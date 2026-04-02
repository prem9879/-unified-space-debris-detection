"""Tests for immutable dataset manifests and key ring policy loading."""

from __future__ import annotations

import json

from PIL import Image

from src.data.dataset_manifest import create_dataset_manifest, load_dataset_manifest
from src.security.secrets_manager import as_role_map, as_rotation_info, get_api_key_ring
from webapp.flask_app import app


def test_create_manifest_with_locked_splits(tmp_path) -> None:
    root = tmp_path / "dataset"
    (root / "debris").mkdir(parents=True, exist_ok=True)
    (root / "non_debris").mkdir(parents=True, exist_ok=True)

    for i in range(3):
        Image.new("RGB", (48, 48), (230, 230, 230)).save(root / "debris" / f"d_{i}.png")
        Image.new("RGB", (48, 48), (40, 40, 40)).save(root / "non_debris" / f"n_{i}.png")

    manifest_path = tmp_path / "manifest_v1.json"
    payload = create_dataset_manifest(
        dataset_root=root,
        manifest_path=manifest_path,
        dataset_name="debris_ops",
        dataset_version="v1",
        split_seed=42,
    )

    assert payload["immutable"] is True
    assert payload["num_files"] == 6
    assert payload["manifest_digest"]
    assert len(payload["splits"]["train"]) == 4
    assert len(payload["splits"]["val"]) == 1
    assert len(payload["splits"]["test"]) == 1

    loaded = load_dataset_manifest(manifest_path)
    assert loaded["manifest_digest"] == payload["manifest_digest"]


def test_key_ring_from_env_json(monkeypatch) -> None:
    keyring = {
        "keys": [
            {"id": "k1", "key": "alpha", "role": "viewer", "status": "active"},
            {"id": "k0", "key": "beta", "role": "analyst", "status": "grace"},
            {"id": "k_old", "key": "retired", "role": "admin", "status": "retired"},
        ],
        "rotation": {"interval_days": 30, "overlap_days": 7},
    }
    monkeypatch.setenv("USDD_API_KEYRING_JSON", json.dumps(keyring))

    ring = get_api_key_ring(force_refresh=True)
    role_map = as_role_map(ring)
    rotation = as_rotation_info(ring)

    assert role_map["alpha"] == "viewer"
    assert role_map["beta"] == "analyst"
    assert "retired" not in role_map
    assert rotation["rotation_interval_days"] == 30
    assert rotation["overlap_days"] == 7


def test_production_profile_disables_legacy_fallback(monkeypatch) -> None:
    monkeypatch.setenv("USDD_SECURITY_PROFILE", "production")
    monkeypatch.setenv("USDD_API_KEYS", '{"legacy":"admin"}')
    monkeypatch.delenv("USDD_API_KEYRING_JSON", raising=False)
    monkeypatch.delenv("USDD_KEYVAULT_URL", raising=False)
    monkeypatch.delenv("USDD_KEYVAULT_SECRET_NAME", raising=False)

    ring = get_api_key_ring(force_refresh=True)
    roles = as_role_map(ring)
    assert roles == {}


def test_calibration_acceptance_gates_present(tmp_path) -> None:
    debris_dir = tmp_path / "debris"
    non_debris_dir = tmp_path / "non_debris"
    debris_dir.mkdir(parents=True, exist_ok=True)
    non_debris_dir.mkdir(parents=True, exist_ok=True)

    from PIL import Image

    for i in range(2):
        Image.new("RGB", (96, 96), (220, 220, 220)).save(debris_dir / f"d_{i}.png")
        Image.new("RGB", (96, 96), (20, 20, 20)).save(non_debris_dir / f"n_{i}.png")

    client = app.test_client()
    res = client.post(
        "/calibration_report",
        data={"dataset_dir": str(tmp_path), "modality": "optical", "max_samples": "4", "bins": "10", "operating_point": "0.5"},
    )
    assert res.status_code == 200
    payload = res.get_json()
    assert isinstance(payload, dict)
    gates = payload.get("acceptance_gates")
    assert isinstance(gates, dict)
    assert "passed" in gates
