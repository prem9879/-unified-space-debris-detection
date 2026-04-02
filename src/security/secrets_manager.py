"""Secrets manager integration for API keys with rotation-aware key rings."""

from __future__ import annotations

import json
import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KeyEntry:
    key: str
    role: str
    kid: str
    status: str


@dataclass(frozen=True)
class KeyPolicy:
    rotation_interval_days: int
    overlap_days: int
    fetched_at_epoch: int
    source: str


@dataclass(frozen=True)
class KeyRing:
    entries: list[KeyEntry]
    policy: KeyPolicy


_CACHE: dict[str, Any] = {"expires_at": 0.0, "key_ring": None, "env_sig": ""}


def _security_profile() -> str:
    return os.getenv("USDD_SECURITY_PROFILE", "standard").strip().lower() or "standard"


def _env_signature() -> str:
    parts = [
        os.getenv("USDD_API_KEYRING_JSON", ""),
        os.getenv("USDD_KEYVAULT_URL", ""),
        os.getenv("USDD_KEYVAULT_SECRET_NAME", ""),
        os.getenv("USDD_API_KEYS", ""),
        os.getenv("USDD_API_KEY", ""),
    ]
    payload = "|".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parse_key_ring_payload(raw_payload: str, source: str) -> KeyRing:
    payload = json.loads(raw_payload)
    if not isinstance(payload, dict):
        raise ValueError("Key ring payload must be a JSON object")

    raw_keys = payload.get("keys", [])
    if not isinstance(raw_keys, list) or not raw_keys:
        raise ValueError("Key ring payload must include non-empty 'keys' list")

    entries: list[KeyEntry] = []
    for idx, item in enumerate(raw_keys):
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", "")).strip()
        role = str(item.get("role", "viewer")).strip().lower() or "viewer"
        kid = str(item.get("id", f"key-{idx + 1}")).strip() or f"key-{idx + 1}"
        status = str(item.get("status", "active")).strip().lower() or "active"
        if key:
            entries.append(KeyEntry(key=key, role=role, kid=kid, status=status))

    if not entries:
        raise ValueError("No valid keys found in key ring payload")

    rotation = (
        payload.get("rotation", {})
        if isinstance(payload.get("rotation", {}), dict)
        else {}
    )
    interval_days = int(rotation.get("interval_days", 30))
    overlap_days = int(rotation.get("overlap_days", 7))

    return KeyRing(
        entries=entries,
        policy=KeyPolicy(
            rotation_interval_days=max(7, interval_days),
            overlap_days=max(1, overlap_days),
            fetched_at_epoch=int(time.time()),
            source=source,
        ),
    )


def _load_from_env_json() -> KeyRing | None:
    raw = os.getenv("USDD_API_KEYRING_JSON", "").strip()
    if not raw:
        return None
    return _parse_key_ring_payload(raw, source="env_json")


def _load_from_azure_key_vault() -> KeyRing | None:
    vault_url = os.getenv("USDD_KEYVAULT_URL", "").strip()
    secret_name = os.getenv("USDD_KEYVAULT_SECRET_NAME", "").strip()
    if not vault_url or not secret_name:
        return None

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
    except Exception:
        return None

    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    client = SecretClient(vault_url=vault_url, credential=credential)
    secret = client.get_secret(secret_name)
    return _parse_key_ring_payload(secret.value, source="azure_key_vault")


def _load_legacy_env_mapping() -> KeyRing | None:
    raw_json = os.getenv("USDD_API_KEYS", "").strip()
    if raw_json:
        parsed = json.loads(raw_json)
        if isinstance(parsed, dict) and parsed:
            entries = [
                KeyEntry(
                    key=str(k),
                    role=str(v).strip().lower() or "viewer",
                    kid=f"legacy-{i + 1}",
                    status="active",
                )
                for i, (k, v) in enumerate(parsed.items())
                if str(k).strip()
            ]
            if entries:
                return KeyRing(
                    entries=entries,
                    policy=KeyPolicy(
                        rotation_interval_days=30,
                        overlap_days=7,
                        fetched_at_epoch=int(time.time()),
                        source="legacy_env_map",
                    ),
                )

    one_key = os.getenv("USDD_API_KEY", "").strip()
    if one_key:
        return KeyRing(
            entries=[
                KeyEntry(
                    key=one_key, role="admin", kid="legacy-single", status="active"
                )
            ],
            policy=KeyPolicy(
                rotation_interval_days=30,
                overlap_days=7,
                fetched_at_epoch=int(time.time()),
                source="legacy_env_single",
            ),
        )
    return None


def get_api_key_ring(force_refresh: bool = False) -> KeyRing:
    ttl_seconds = max(30, int(os.getenv("USDD_KEYRING_CACHE_SECONDS", "300")))
    now = time.time()
    env_sig = _env_signature()
    if _CACHE.get("env_sig") != env_sig:
        force_refresh = True

    if (
        not force_refresh
        and _CACHE["key_ring"] is not None
        and now < float(_CACHE["expires_at"])
    ):
        return _CACHE["key_ring"]

    profile = _security_profile()
    loaders = [_load_from_env_json, _load_from_azure_key_vault]
    if profile != "production":
        loaders.append(_load_legacy_env_mapping)

    for loader in loaders:
        try:
            key_ring = loader()
        except Exception:
            key_ring = None
        if key_ring is not None:
            _CACHE["key_ring"] = key_ring
            _CACHE["expires_at"] = now + ttl_seconds
            _CACHE["env_sig"] = env_sig
            return key_ring

    fallback = KeyRing(
        entries=[],
        policy=KeyPolicy(
            rotation_interval_days=30,
            overlap_days=7,
            fetched_at_epoch=int(time.time()),
            source="production_no_fallback" if profile == "production" else "none",
        ),
    )
    _CACHE["key_ring"] = fallback
    _CACHE["expires_at"] = now + ttl_seconds
    _CACHE["env_sig"] = env_sig
    return fallback


def as_role_map(key_ring: KeyRing) -> dict[str, str]:
    return {
        entry.key: entry.role
        for entry in key_ring.entries
        if entry.status in {"active", "grace"}
    }


def as_rotation_info(key_ring: KeyRing) -> dict[str, Any]:
    return {
        "source": key_ring.policy.source,
        "fetched_at_epoch": key_ring.policy.fetched_at_epoch,
        "rotation_interval_days": key_ring.policy.rotation_interval_days,
        "overlap_days": key_ring.policy.overlap_days,
        "active_key_ids": [
            entry.kid for entry in key_ring.entries if entry.status == "active"
        ],
        "grace_key_ids": [
            entry.kid for entry in key_ring.entries if entry.status == "grace"
        ],
    }
