"""Flask visual app for Unified Space Debris Detection."""

from __future__ import annotations

import json
import base64
import hashlib
import hmac
import os
import time
from functools import wraps
from io import BytesIO
from pathlib import Path
import sys
from threading import Lock
from typing import TypedDict, cast

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from flask import Flask, g, jsonify, render_template, request, send_from_directory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.dataset_catalog import curated_sources  # noqa: E402
from src.data.local_dataset_loader import (  # noqa: E402
    build_dataset_inventory,
    discover_modality_paths,
    image_file_to_base64,
)
from src.data.nasa_odpo_loader import load_public_nasa_odpo_data  # noqa: E402
from src.inference.service import PreprocessOptions, UnifiedInferenceService  # noqa: E402
from src.security.secrets_manager import as_role_map, as_rotation_info, get_api_key_ring  # noqa: E402

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

CHECKPOINT = ROOT / "artifacts" / "checkpoints" / "unified_latest.pt"
REPORT = ROOT / "artifacts" / "eval_report.json"
DEFAULT_IMAGES_DIR = Path(r"c:\Users\PREM DIWAN\Desktop\ml\images")
FRONTEND_DIST = ROOT / "production_system" / "frontend" / "dist"
IMAGE_BENCH_SUMMARY = ROOT / "artifacts" / "image_bench" / "image_bench_summary.json"

service: UnifiedInferenceService | None = None
service_cache: dict[str, UnifiedInferenceService] = {}
_RATE_LIMIT_STATE: dict[str, object] = {"window_start": 0.0, "buckets": {}}
_RATE_LIMIT_LOCK = Lock()
_ABUSE_STATE: dict[str, object] = {"invalid": {}, "locked_until": {}, "window_start": 0.0, "request_counts": {}}
_AUDIT_STATE: dict[str, object] = {"last_sig": "", "last_prune_ts": 0.0}


class OrbitalObject(TypedDict):
    norad_cat_id: int
    name: str
    altitude_km: float
    inclination_deg: float
    relative_velocity_km_s: float
    collision_density: float
    shell: str


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _load_api_key_map() -> tuple[dict[str, str], dict[str, object]]:
    key_ring = get_api_key_ring()
    return as_role_map(key_ring), as_rotation_info(key_ring)


def _security_config() -> dict[str, object]:
    api_keys, rotation = _load_api_key_map()
    role_rate_limits_raw = os.getenv(
        "USDD_ROLE_RATE_LIMITS_JSON",
        '{"anonymous":30,"viewer":90,"analyst":180,"admin":240}',
    )
    try:
        role_rate_limits = json.loads(role_rate_limits_raw)
    except json.JSONDecodeError:
        role_rate_limits = {"anonymous": 30, "viewer": 90, "analyst": 180, "admin": 240}

    return {
        "security_profile": os.getenv("USDD_SECURITY_PROFILE", "standard").strip().lower() or "standard",
        "auth_required": _env_flag("USDD_REQUIRE_AUTH", False),
        "api_keys": api_keys,
        "rotation": rotation,
        "rate_limit_per_min": max(10, int(os.getenv("USDD_RATE_LIMIT_PER_MIN", "180"))),
        "role_rate_limits": role_rate_limits,
        "invalid_key_lockout_threshold": max(3, int(os.getenv("USDD_INVALID_KEY_LOCKOUT_THRESHOLD", "5"))),
        "invalid_key_lockout_seconds": max(60, int(os.getenv("USDD_INVALID_KEY_LOCKOUT_SECONDS", "600"))),
        "anomaly_threshold_per_min": max(100, int(os.getenv("USDD_ANOMALY_THRESHOLD_PER_MIN", "500"))),
        "audit_log_enabled": _env_flag("USDD_AUDIT_LOG_ENABLED", True),
        "audit_log_path": os.getenv("USDD_AUDIT_LOG_PATH", str(ROOT / "logs" / "audit.log")),
        "audit_signing_key": os.getenv("USDD_AUDIT_SIGNING_KEY", "").strip(),
        "audit_retention_days": max(1, int(os.getenv("USDD_AUDIT_RETENTION_DAYS", "30"))),
    }


def _get_client_identity() -> str:
    api_key = request.headers.get("X-API-Key", "").strip()
    if api_key:
        return f"key:{api_key[:6]}"
    forwarded_for = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded_for:
        return f"ip:{forwarded_for.split(',')[0].strip()}"
    return f"ip:{request.remote_addr or 'unknown'}"


def _check_rate_limit(limit_per_min: int, identity: str) -> tuple[bool, int]:
    now = time.time()
    with _RATE_LIMIT_LOCK:
        window_start = float(_RATE_LIMIT_STATE["window_start"])
        buckets = cast(dict[str, int], _RATE_LIMIT_STATE["buckets"])
        if now - window_start >= 60.0:
            _RATE_LIMIT_STATE["window_start"] = now
            buckets = {}
            _RATE_LIMIT_STATE["buckets"] = buckets

        current = int(buckets.get(identity, 0)) + 1
        buckets[identity] = current
        remaining = max(0, limit_per_min - current)
        return current <= limit_per_min, remaining


def _role_rate_limit_per_min(cfg: dict[str, object], role: str | None) -> int:
    role_name = (role or "anonymous").strip().lower()
    rate_map = cfg.get("role_rate_limits", {}) or {}
    role_limit = int(rate_map.get(role_name, cfg.get("rate_limit_per_min", 180)))
    return max(10, role_limit)


def _abuse_window_tick() -> None:
    now = time.time()
    window_start = float(_ABUSE_STATE.get("window_start", 0.0))
    if now - window_start >= 60.0:
        _ABUSE_STATE["window_start"] = now
        _ABUSE_STATE["request_counts"] = {}


def _register_invalid_key_attempt(identity: str, cfg: dict[str, object]) -> tuple[bool, int]:
    now = time.time()
    invalid = cast(dict[str, int], _ABUSE_STATE["invalid"])
    locked_until = cast(dict[str, int], _ABUSE_STATE["locked_until"])
    current = int(invalid.get(identity, 0)) + 1
    invalid[identity] = current
    if current >= int(cfg["invalid_key_lockout_threshold"]):
        until = int(now + int(cfg["invalid_key_lockout_seconds"]))
        locked_until[identity] = until
        return True, until
    return False, 0


def _is_locked(identity: str) -> tuple[bool, int]:
    now = int(time.time())
    locked_until = cast(dict[str, int], _ABUSE_STATE["locked_until"])
    until = int(locked_until.get(identity, 0))
    return until > now, until


def _register_request_and_anomaly(identity: str, cfg: dict[str, object]) -> bool:
    _abuse_window_tick()
    request_counts = cast(dict[str, int], _ABUSE_STATE["request_counts"])
    current = int(request_counts.get(identity, 0)) + 1
    request_counts[identity] = current
    return current > int(cfg["anomaly_threshold_per_min"])


def _sign_audit_payload(payload: dict[str, object], signing_key: str) -> tuple[str, str]:
    prev_sig = str(_AUDIT_STATE.get("last_sig", ""))
    base = json.dumps({"entry": payload, "prev_sig": prev_sig}, sort_keys=True).encode("utf-8")
    if signing_key:
        sig = hmac.new(signing_key.encode("utf-8"), base, hashlib.sha256).hexdigest()
    else:
        sig = hashlib.sha256(base).hexdigest()
    _AUDIT_STATE["last_sig"] = sig
    return sig, prev_sig


def _prune_audit_log_if_due(cfg: dict[str, object]) -> None:
    now = time.time()
    last_prune = float(_AUDIT_STATE.get("last_prune_ts", 0.0))
    if now - last_prune < 3600:
        return
    _AUDIT_STATE["last_prune_ts"] = now

    audit_path = Path(str(cfg["audit_log_path"]))
    if not audit_path.exists():
        return
    cutoff = int(now - int(cfg["audit_retention_days"]) * 86400)

    kept: list[str] = []
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            if int(row.get("ts", 0)) >= cutoff:
                kept.append(json.dumps(row))
        except Exception:
            continue

    audit_path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")


def _build_calibration_acceptance(metrics: dict[str, object], operating_point: float) -> dict[str, object]:
    ece_threshold = float(os.getenv("USDD_ECE_THRESHOLD", "0.10"))
    false_alarm_threshold = float(os.getenv("USDD_FALSE_ALARM_THRESHOLD", "0.08"))
    min_recall = float(os.getenv("USDD_MIN_RECALL", "0.85"))

    cm = metrics.get("confusion_matrix", {}) or {}
    fp = float(cm.get("fp", 0.0))
    tn = float(cm.get("tn", 0.0))
    false_alarm_rate = fp / max(1.0, fp + tn)

    ece = float(metrics.get("ece", 0.0))
    recall = float(metrics.get("recall", 0.0))
    checks = {
        "ece_ok": ece <= ece_threshold,
        "false_alarm_ok": false_alarm_rate <= false_alarm_threshold,
        "recall_ok": recall >= min_recall,
    }
    return {
        "operating_point": float(operating_point),
        "thresholds": {
            "ece_max": ece_threshold,
            "false_alarm_max": false_alarm_threshold,
            "recall_min": min_recall,
        },
        "observed": {
            "ece": ece,
            "false_alarm_rate": false_alarm_rate,
            "recall": recall,
        },
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def _resolve_caller_role(cfg: dict[str, object]) -> tuple[str | None, str]:
    api_key = request.headers.get("X-API-Key", "").strip()
    role = str((cfg["api_keys"] or {}).get(api_key, "")).strip().lower() or None
    return role, api_key


def _role_rank(role: str | None) -> int:
    order = {"viewer": 1, "analyst": 2, "admin": 3}
    return order.get((role or "").strip().lower(), 0)


def require_role(min_role: str):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            cfg = _security_config()
            role, _ = _resolve_caller_role(cfg)
            if cfg["auth_required"] and _role_rank(role) < _role_rank(min_role):
                return jsonify({"error": f"role '{min_role}' required"}), 403
            return fn(*args, **kwargs)

        return wrapped

    return decorator


@app.before_request
def enforce_runtime_security_controls():
    cfg = _security_config()
    role, api_key = _resolve_caller_role(cfg)
    g.auth_role = role or "anonymous"
    g.identity = _get_client_identity()
    g.request_start = time.time()

    locked, until = _is_locked(g.identity)
    if locked:
        return jsonify({"error": "identity temporarily locked", "locked_until_epoch": until}), 423

    open_paths = {
        "/",
        "/healthz",
        "/readyz",
        "/options",
        "/app",
        "/mission_status",
        "/legacy-api/mission_status",
        "/legacy-api/readyz",
        "/legacy-api/options",
    }
    if request.path.startswith("/static") or request.path.startswith("/app") or request.path.startswith("/assets") or request.path in open_paths:
        return None

    if bool(cfg["auth_required"]):
        if not api_key:
            return jsonify({"error": "missing X-API-Key header"}), 401
        if role is None:
            should_lock, lock_until = _register_invalid_key_attempt(g.identity, cfg)
            if should_lock:
                return jsonify({"error": "invalid API key; identity locked", "locked_until_epoch": lock_until}), 423
            return jsonify({"error": "invalid API key"}), 401

    if _register_request_and_anomaly(g.identity, cfg):
        return jsonify({"error": "anomalous request rate detected", "retry_in_seconds": 60}), 429

    allowed, remaining = _check_rate_limit(_role_rate_limit_per_min(cfg, role), g.identity)
    g.rate_limit_remaining = remaining
    if not allowed:
        return jsonify({"error": "rate limit exceeded", "retry_in_seconds": 60}), 429

    return None


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if hasattr(g, "rate_limit_remaining"):
        response.headers["X-RateLimit-Remaining"] = str(int(g.rate_limit_remaining))

    cfg = _security_config()
    if bool(cfg["audit_log_enabled"]):
        try:
            latency_ms = None
            if hasattr(g, "request_start"):
                latency_ms = int((time.time() - float(g.request_start)) * 1000)
            audit_entry = {
                "ts": int(time.time()),
                "method": request.method,
                "path": request.path,
                "status": int(response.status_code),
                "ip": request.remote_addr,
                "identity": getattr(g, "identity", "unknown"),
                "role": getattr(g, "auth_role", "anonymous"),
                "latency_ms": latency_ms,
                "ua": request.headers.get("User-Agent", ""),
                "security_profile": cfg.get("security_profile", "standard"),
            }
            sig, prev_sig = _sign_audit_payload(audit_entry, str(cfg.get("audit_signing_key", "")))
            audit_entry["sig"] = sig
            audit_entry["prev_sig"] = prev_sig
            audit_path = Path(str(cfg["audit_log_path"]))
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            with audit_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(audit_entry) + "\n")
            _prune_audit_log_if_due(cfg)
        except Exception:
            # Audit logging must never break API responses.
            pass
    return response


def _pil_to_data_uri(image: Image.Image, max_size: int = 224) -> str:
    img = image.convert("RGB").copy()
    img.thumbnail((max_size, max_size))
    buff = BytesIO()
    img.save(buff, format="PNG")
    encoded = base64.b64encode(buff.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _build_rgb_analysis(image: Image.Image) -> dict[str, object]:
    """Analyze RGB channels with histograms and statistics."""
    rgb = image.convert("RGB")
    arr = np.asarray(rgb, dtype=np.uint8)
    
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    
    # Compute histograms (256 bins)
    r_hist = np.histogram(r, bins=256, range=(0, 256))[0]
    g_hist = np.histogram(g, bins=256, range=(0, 256))[0]
    b_hist = np.histogram(b, bins=256, range=(0, 256))[0]
    
    # Normalize to 0-1
    r_hist = (r_hist / (r_hist.max() + 1e-6)).tolist()
    g_hist = (g_hist / (g_hist.max() + 1e-6)).tolist()
    b_hist = (b_hist / (b_hist.max() + 1e-6)).tolist()
    
    # Statistics
    stats = {
        "r_mean": float(r.mean()), "r_std": float(r.std()),
        "g_mean": float(g.mean()), "g_std": float(g.std()),
        "b_mean": float(b.mean()), "b_std": float(b.std()),
        "luminance": float((0.299*r.astype(float) + 0.587*g.astype(float) + 0.114*b.astype(float)).mean()),
    }
    
    return {
        "r_histogram": r_hist,
        "g_histogram": g_hist,
        "b_histogram": b_hist,
        "stats": stats,
    }


def _build_evidence_visuals(image: Image.Image, max_size: int = 224) -> dict[str, object]:
    rgb = image.convert("RGB")
    arr = np.asarray(rgb, dtype=np.float32) / 255.0
    gray = arr.mean(axis=2)
    gray = (gray - gray.min()) / (gray.max() - gray.min() + 1e-6)

    # Advanced pseudo-color heatmap with better color mapping
    heat_rgb = np.stack([gray, 0.35 * gray, 1.0 - gray], axis=2)
    heat_img = Image.fromarray(np.clip(heat_rgb * 255.0, 0, 255).astype(np.uint8))

    p95 = float(np.quantile(gray, 0.95))
    threshold = max(0.55, p95)
    mask = gray >= threshold

    bbox = None
    bbox_area_ratio = 0.0
    overlay = rgb.copy()
    draw = ImageDraw.Draw(overlay)
    ys, xs = np.where(mask)
    if xs.size > 0 and ys.size > 0:
        x1, x2 = int(xs.min()), int(xs.max())
        y1, y2 = int(ys.min()), int(ys.max())
        bbox = [x1, y1, x2, y2]
        img_area = float(max(1, gray.shape[0] * gray.shape[1]))
        bbox_area = float(max(0, (x2 - x1 + 1) * (y2 - y1 + 1)))
        bbox_area_ratio = min(1.0, bbox_area / img_area)
        draw.rectangle([x1, y1, x2, y2], outline=(255, 90, 90), width=3)

    return {
        "heatmap_visual": _pil_to_data_uri(heat_img, max_size=max_size),
        "bbox_overlay_visual": _pil_to_data_uri(overlay, max_size=max_size),
        "bbox": bbox,
        "bbox_area_ratio": bbox_area_ratio,
        "hot_pixel_ratio": float(mask.mean()),
    }


def _build_decision_basis(
    detect_probability: float,
    collision_probability: float,
    class_probabilities: list[float] | None,
    evidence: dict[str, object] | None,
    inference_source: str | None = None,
) -> dict[str, object]:
    threshold = 0.5
    low_cutoff = 0.45
    high_cutoff = 0.55
    margin = float(detect_probability - threshold)
    abs_margin = abs(margin)

    if detect_probability >= high_cutoff:
        label = "debris"
    elif detect_probability <= low_cutoff:
        label = "non_debris"
    else:
        label = "uncertain"

    if abs_margin < 0.03:
        confidence_band = "very_low"
    elif abs_margin < 0.08:
        confidence_band = "low"
    elif abs_margin < 0.2:
        confidence_band = "medium"
    else:
        confidence_band = "high"
    hot_pixel_ratio = float((evidence or {}).get("hot_pixel_ratio", 0.0))
    bbox_area_ratio = float((evidence or {}).get("bbox_area_ratio", 0.0))
    probs = class_probabilities or []
    ranked = sorted((float(probability), index) for index, probability in enumerate(probs))
    top_class_probability = float(ranked[-1][0]) if ranked else float(detect_probability)
    second_class_probability = float(ranked[-2][0]) if len(ranked) > 1 else 0.0
    top_class_index = int(ranked[-1][1]) if ranked else -1
    class_gap = float(top_class_probability - second_class_probability)
    entropy = 0.0
    if probs:
        probabilities = np.asarray(probs, dtype=np.float64)
        probabilities = np.clip(probabilities, 1e-12, 1.0)
        entropy = float(-np.sum(probabilities * np.log(probabilities)))

    source = inference_source or "trained model"
    reason = (
        f"{source} predicts {label.replace('_', ' ')} because detect_probability={detect_probability:.4f} "
        f"around threshold={threshold:.2f} (band [{low_cutoff:.2f}, {high_cutoff:.2f}]). "
        f"Margin={margin:+.4f}, confidence_band={confidence_band}, "
        f"top_class_index={top_class_index}, top_class_probability={top_class_probability:.4f}, "
        f"class_gap={class_gap:.4f}, entropy={entropy:.4f}, collision_probability={collision_probability:.4f}, "
        f"hot_pixel_ratio={hot_pixel_ratio:.4f}, bbox_area_ratio={bbox_area_ratio:.4f}."
    )

    return {
        "threshold": threshold,
        "low_cutoff": low_cutoff,
        "high_cutoff": high_cutoff,
        "predicted_label": label,
        "margin_from_threshold": margin,
        "confidence_band": confidence_band,
        "top_class_probability": top_class_probability,
        "top_class_index": top_class_index,
        "class_gap": class_gap,
        "entropy": entropy,
        "collision_probability": float(collision_probability),
        "hot_pixel_ratio": hot_pixel_ratio,
        "bbox_area_ratio": bbox_area_ratio,
        "inference_source": source,
        "reason": reason,
    }


def _build_operational_summary(decision_basis: dict[str, object]) -> dict[str, object]:
    profile = str(decision_basis.get("operator_profile", "balanced"))
    label = str(decision_basis.get("predicted_label", "uncertain"))
    confidence_band = str(decision_basis.get("confidence_band", "low"))
    inference_source = str(decision_basis.get("inference_source", "trained model"))
    collision_probability = float(decision_basis.get("collision_probability", 0.0))
    margin = abs(float(decision_basis.get("margin_from_threshold", 0.0)))
    bbox_area_ratio = float(decision_basis.get("bbox_area_ratio", 0.0))
    hot_pixel_ratio = float(decision_basis.get("hot_pixel_ratio", 0.0))
    class_gap = float(decision_basis.get("class_gap", 0.0))
    entropy = float(decision_basis.get("entropy", 0.0))

    profile_settings = {
        "conservative": {
            "bias": 0.18,
            "tone": "Cautious",
            "suffix": "Prefer manual verification before final action.",
            "review_floor": 0.35,
        },
        "balanced": {
            "bias": 0.0,
            "tone": "Balanced",
            "suffix": "Use the model output as the default operational guide.",
            "review_floor": 0.5,
        },
        "exploratory": {
            "bias": -0.12,
            "tone": "Exploratory",
            "suffix": "Gather another frame or secondary source before escalation.",
            "review_floor": 0.62,
        },
    }.get(profile, {
        "bias": 0.0,
        "tone": "Balanced",
        "suffix": "Use the model output as the default operational guide.",
        "review_floor": 0.5,
    })
    bias = float(profile_settings["bias"])
    review_floor = float(profile_settings["review_floor"])

    adjusted_collision = max(0.0, min(1.0, collision_probability + bias))

    if label == "uncertain":
        priority = "manual_review"
        action = "Collect another image or increase sensor coverage before acting."
    elif label == "debris":
        if adjusted_collision >= 0.7:
            priority = "urgent"
            action = "Escalate immediately for conjunction screening and orbit review."
        elif adjusted_collision >= review_floor:
            priority = "high"
            action = "Review trajectory and confirm with additional measurements."
        else:
            priority = "medium"
            action = "Track as debris candidate and keep monitoring."
    else:
        if adjusted_collision >= 0.55:
            priority = "medium"
            action = "Non-debris appearance, but collision score warrants a follow-up check."
        else:
            priority = "low"
            action = "Treat as non-debris and archive for reference."

    quality_score = max(
        0.0,
        min(
            1.0,
            (1.0 - margin) * 0.35
            + (1.0 - min(1.0, hot_pixel_ratio + bbox_area_ratio)) * 0.2
            + (1.0 - min(1.0, adjusted_collision)) * 0.25
            + min(1.0, class_gap) * 0.1
            + max(0.0, 1.5 - entropy) * 0.1,
        ),
    )

    return {
        "operator_profile": profile,
        "operator_tone": profile_settings["tone"],
        "priority": priority,
        "action": f"{action} {profile_settings['suffix']}",
        "quality_score": float(quality_score),
        "confidence_band": confidence_band,
        "summary": f"{profile_settings['tone']} mode: {label.replace('_', ' ').title()} with {confidence_band} confidence. {action}",
        "evidence_note": (
            f"Inference source: {inference_source}. Class gap={class_gap:.4f}, entropy={entropy:.4f}, "
            f"hot pixels={hot_pixel_ratio:.4f}, bbox area={bbox_area_ratio:.4f}."
        ),
        "signals": {
            "collision_probability": collision_probability,
            "adjusted_collision_probability": adjusted_collision,
            "margin_from_threshold": margin,
            "bbox_area_ratio": bbox_area_ratio,
            "hot_pixel_ratio": hot_pixel_ratio,
            "class_gap": class_gap,
            "entropy": entropy,
        },
    }


def _infer_ground_truth_label(path: Path) -> int | None:
    tokens = [p.lower() for p in path.parts]
    joined = "/".join(tokens)
    if "non_debris" in joined or "nondebris" in joined or "non-debris" in joined:
        return 0
    if "debris" in joined:
        return 1
    return None


def _compute_binary_calibration(samples: list[tuple[float, int]], bins: int = 10) -> dict[str, object]:
    if not samples:
        return {
            "num_samples": 0,
            "ece": 0.0,
            "mce": 0.0,
            "brier_score": 0.0,
            "nll": 0.0,
            "accuracy": 0.0,
            "balanced_accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "confusion_matrix": {"tp": 0, "tn": 0, "fp": 0, "fn": 0},
            "bins": [],
        }

    probs = np.array([s[0] for s in samples], dtype=np.float64)
    labels = np.array([s[1] for s in samples], dtype=np.int64)
    eps = 1e-12
    probs_clipped = np.clip(probs, eps, 1.0 - eps)
    preds = (probs >= 0.5).astype(np.int64)

    tp = int(np.sum((preds == 1) & (labels == 1)))
    tn = int(np.sum((preds == 0) & (labels == 0)))
    fp = int(np.sum((preds == 1) & (labels == 0)))
    fn = int(np.sum((preds == 0) & (labels == 1)))

    accuracy = float(np.mean(preds == labels))
    precision = float(tp / max(1, tp + fp))
    recall = float(tp / max(1, tp + fn))
    f1 = float((2.0 * precision * recall) / max(1e-12, precision + recall))
    tpr = float(tp / max(1, tp + fn))
    tnr = float(tn / max(1, tn + fp))
    balanced_accuracy = 0.5 * (tpr + tnr)

    brier_score = float(np.mean((probs - labels) ** 2))
    nll = float(-np.mean(labels * np.log(probs_clipped) + (1 - labels) * np.log(1 - probs_clipped)))

    edges = np.linspace(0.0, 1.0, bins + 1)
    bin_rows: list[dict[str, object]] = []
    ece = 0.0
    mce = 0.0
    n = len(samples)

    for i in range(bins):
        lo = float(edges[i])
        hi = float(edges[i + 1])
        if i < bins - 1:
            mask = (probs >= lo) & (probs < hi)
        else:
            mask = (probs >= lo) & (probs <= hi)

        count = int(np.sum(mask))
        if count == 0:
            bin_rows.append(
                {
                    "bin_index": i,
                    "range": [lo, hi],
                    "count": 0,
                    "avg_confidence": 0.0,
                    "empirical_accuracy": 0.0,
                    "gap": 0.0,
                }
            )
            continue

        avg_conf = float(np.mean(probs[mask]))
        emp_acc = float(np.mean(labels[mask]))
        gap = abs(emp_acc - avg_conf)
        weight = count / n
        ece += gap * weight
        mce = max(mce, gap)

        bin_rows.append(
            {
                "bin_index": i,
                "range": [lo, hi],
                "count": count,
                "avg_confidence": avg_conf,
                "empirical_accuracy": emp_acc,
                "gap": float(gap),
            }
        )

    return {
        "num_samples": int(n),
        "ece": float(ece),
        "mce": float(mce),
        "brier_score": brier_score,
        "nll": nll,
        "accuracy": accuracy,
        "balanced_accuracy": float(balanced_accuracy),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "bins": bin_rows,
    }


def _resolve_model_checkpoint_map() -> dict[str, Path]:
    mapping = {"unified_latest": CHECKPOINT}
    payload = _load_json_if_exists(IMAGE_BENCH_SUMMARY)
    for model_name, stats in (payload.get("results", {}) or {}).items():
        checkpoint_raw = str((stats or {}).get("checkpoint", "")).strip()
        if not checkpoint_raw:
            continue
        checkpoint_path = Path(checkpoint_raw)
        if not checkpoint_path.is_absolute():
            checkpoint_path = ROOT / checkpoint_path
        mapping[str(model_name).strip().lower()] = checkpoint_path
    return mapping


def _load_service(model_name: str | None = None) -> UnifiedInferenceService:
    global service
    key = (model_name or "unified_latest").strip().lower() or "unified_latest"

    if key == "unified_latest":
        if service is None:
            service = UnifiedInferenceService(CHECKPOINT, allow_demo_mode=True)
        return service

    if key in service_cache:
        return service_cache[key]

    model_map = _resolve_model_checkpoint_map()
    checkpoint = model_map.get(key)
    if checkpoint is None:
        raise ValueError(f"Unknown model_name '{key}'. Use /options to see available model choices.")

    loaded = UnifiedInferenceService(checkpoint, allow_demo_mode=True)
    service_cache[key] = loaded
    return loaded


def _load_json_if_exists(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _risk_band(score: float) -> str:
    if score >= 0.7:
        return "HIGH"
    if score >= 0.35:
        return "MEDIUM"
    return "LOW"


def _build_orbital_brief() -> dict[str, object]:
    eval_report = _load_json_if_exists(REPORT)
    benchmark_report = _load_json_if_exists(ROOT / "artifacts" / "image_bench" / "image_bench_summary.json")

    architecture = [
        {
            "step": "1. Ingest",
            "title": "Real-time orbital intake",
            "detail": "Pull TLEs from CelesTrak / Space-Track, then attach provenance, epoch, and shell metadata.",
        },
        {
            "step": "2. Preprocess",
            "title": "Orbital feature extraction",
            "detail": "Convert raw TLE rows into altitude, semi-major axis, drag proxy, cyclic angles, and orbit-shell cues.",
        },
        {
            "step": "3. Predict",
            "title": "Multi-model reasoning",
            "detail": "Use LSTM / GRU for trajectories, Transformer for long-horizon sequences, and XGBoost as a stable baseline.",
        },
        {
            "step": "4. Fuse",
            "title": "Physics + AI collision engine",
            "detail": "Screen by orbital proximity first, then fuse learned risk with relative velocity and conjunction geometry.",
        },
        {
            "step": "5. Visualize",
            "title": "3D orbital deck",
            "detail": "Render Earth, orbit shells, debris points, and alerts with WebGL / Three.js style motion.",
        },
    ]

    model_stack = [
        {
            "name": "LSTM / GRU",
            "use": "Trajectory forecasting",
            "why": "Good at orbital time sequences with limited data, cheap to train, easy to explain.",
            "tradeoff": "Struggles with long-range dependencies and regime changes.",
        },
        {
            "name": "Transformer",
            "use": "Long-horizon sequence modeling",
            "why": "Captures repeated orbital patterns and global context better than a plain recurrent net.",
            "tradeoff": "Heavier compute and more sensitive to sparse datasets.",
        },
        {
            "name": "XGBoost / Random Forest",
            "use": "Fast baseline classifier",
            "why": "Strong on tabular orbital features and useful when the neural stack is not confident.",
            "tradeoff": "No real sequence understanding.",
        },
        {
            "name": "CNN / YOLO",
            "use": "Image-based debris detection",
            "why": "Useful when optical or radar imagery is available for object localization.",
            "tradeoff": "Does not solve orbital propagation by itself.",
        },
    ]

    deployment_stack = {
        "backend": "Flask today, FastAPI-ready if the system needs async endpoints and stricter schema contracts.",
        "frontend": "Server-rendered Flask UI now, with a clean migration path to React / Next.js for richer mission views.",
        "database": "PostgreSQL for catalog and audit data, Redis for live queues and cached orbit snapshots.",
        "cloud": "AWS or GCP depending on the team; GPU workers for inference, CPU workers for ingestion, and object storage for artifacts.",
        "api": [
            "/healthz",
            "/readyz",
            "/options",
            "/predict",
            "/predict_dataset",
            "/calibration_report",
            "/orbital_brief",
            "/orbital_scene",
        ],
    }

    sample_objects: list[OrbitalObject] = [
        {"norad_cat_id": 25544, "name": "ISS", "altitude_km": 408.0, "inclination_deg": 51.6, "relative_velocity_km_s": 7.66, "collision_density": 0.18, "shell": "LEO"},
        {"norad_cat_id": 43013, "name": "DEBRIS-A", "altitude_km": 612.0, "inclination_deg": 97.4, "relative_velocity_km_s": 10.8, "collision_density": 0.41, "shell": "LEO"},
        {"norad_cat_id": 39120, "name": "DEBRIS-B", "altitude_km": 799.0, "inclination_deg": 98.0, "relative_velocity_km_s": 11.2, "collision_density": 0.58, "shell": "LEO"},
        {"norad_cat_id": 40294, "name": "DEBRIS-C", "altitude_km": 2020.0, "inclination_deg": 63.4, "relative_velocity_km_s": 8.2, "collision_density": 0.27, "shell": "MEO"},
        {"norad_cat_id": 45678, "name": "DEBRIS-D", "altitude_km": 35786.0, "inclination_deg": 0.2, "relative_velocity_km_s": 3.1, "collision_density": 0.19, "shell": "GEO"},
        {"norad_cat_id": 49812, "name": "DEBRIS-E", "altitude_km": 1180.0, "inclination_deg": 71.0, "relative_velocity_km_s": 9.7, "collision_density": 0.63, "shell": "LEO"},
    ]

    scene_objects: list[dict[str, object]] = []
    collision_alerts: list[dict[str, object]] = []
    for index, obj in enumerate(sample_objects):
        base_risk = 0.38 * obj["collision_density"] + 0.25 * (obj["relative_velocity_km_s"] / 12.0) + 0.22 * (obj["inclination_deg"] / 180.0)
        shell_bonus = 0.18 if obj["shell"] == "LEO" else (0.10 if obj["shell"] == "MEO" else 0.06)
        risk_score = max(0.0, min(1.0, base_risk + shell_bonus))
        band = _risk_band(risk_score)
        record = {
            **obj,
            "risk_score": round(risk_score, 3),
            "risk_band": band,
            "size": 0.55 if obj["shell"] == "LEO" else 0.42 if obj["shell"] == "MEO" else 0.33,
            "color": "#35d1ff" if band == "LOW" else "#fbbf24" if band == "MEDIUM" else "#ff5d5d",
            "orbit_phase": round((index + 1) / len(sample_objects), 3),
        }
        scene_objects.append(record)
        if band != "LOW":
            collision_alerts.append(
                {
                    "object": obj["name"],
                    "norad_cat_id": obj["norad_cat_id"],
                    "risk_band": band,
                    "risk_score": round(risk_score, 3),
                    "recommended_action": "Track closely" if band == "MEDIUM" else "Escalate conjunction review",
                }
            )

    collision_alerts = sorted(collision_alerts, key=lambda item: float(item["risk_score"]), reverse=True)

    research_edges = {
        "unique_contribution": "A physics-gated, multimodal collision intelligence stack that mixes orbital screening, learned sequence models, and explainable risk bands.",
        "paper_titles": [
            "Unified Space Debris Intelligence for Physics-Gated Collision Prediction",
            "Multimodal Orbital Risk Fusion for Real-Time Space Safety",
            "From TLE Streams to Conjunction Alerts: A Research-Grade Operational Pipeline",
        ],
        "metrics": ["AUC-ROC", "PR-AUC", "ECE", "Brier score", "lead time to alert", "false alert rate", "orbit RMSE"],
        "comparison": [
            "Pure SGP4 propagation: fast but not decision-aware.",
            "Pure deep learning: flexible but brittle under sparse orbital data.",
            "This system: hybrid, auditable, and usable in operations.",
        ],
    }

    if not eval_report:
        eval_report = {"status": "unavailable", "note": "No evaluation artifact found yet."}

    return {
        "architecture": architecture,
        "model_stack": model_stack,
        "collision_engine": {
            "mode": "physics-first + AI fusion",
            "thresholds": {"low": 0.35, "medium": 0.7, "high": 1.0},
            "reasoning": [
                "We shortlist by orbital shell and inclination before scoring, because full pairwise search does not scale.",
                "Relative velocity matters, but only after proximity and shell context have already reduced the candidate set.",
                "The final risk band is intentionally conservative; false confidence is worse than a missed visual flourish.",
            ],
        },
        "realtime": {
            "ingest": "APIs / webhooks / scheduled TLE pulls",
            "stream": "Redis or Kafka for live score updates",
            "updates": "Continuous re-scoring on new catalog snapshots and sensor fusion events",
        },
        "visualization": {
            "scene": scene_objects,
            "alerts": collision_alerts[:4],
            "shells": [
                {"name": "LEO", "radius": 1.35, "color": "#35d1ff"},
                {"name": "MEO", "radius": 2.1, "color": "#7dd3fc"},
                {"name": "GEO", "radius": 2.85, "color": "#a5b4fc"},
            ],
        },
        "deployment": deployment_stack,
        "research": research_edges,
        "metrics_snapshot": {
            "benchmark": benchmark_report.get("num_samples", 0) if benchmark_report else 0,
            "eval": eval_report,
        },
    }


@app.get("/")
def home():
    report = {}
    layers = []
    default_dataset_root = str(DEFAULT_IMAGES_DIR if DEFAULT_IMAGES_DIR.exists() else (ROOT / "data"))
    if REPORT.exists():
        report = json.loads(REPORT.read_text(encoding="utf-8"))
    if CHECKPOINT.exists():
        try:
            layers = _load_service().list_layers()
        except Exception:
            layers = []
    return render_template(
        "index.html",
        report=report,
        checkpoint_exists=CHECKPOINT.exists(),
        layers=layers,
        default_dataset_root=default_dataset_root,
    )


@app.get("/app")
def mission_unified_app():
    if not FRONTEND_DIST.exists():
        return jsonify({"error": f"Frontend bundle not found at {FRONTEND_DIST}. Run: cd production_system/frontend ; npm run build"}), 503
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.get("/app/<path:asset_path>")
def mission_unified_app_paths(asset_path: str):
    if not FRONTEND_DIST.exists():
        return jsonify({"error": f"Frontend bundle not found at {FRONTEND_DIST}. Run: cd production_system/frontend ; npm run build"}), 503

    file_path = FRONTEND_DIST / asset_path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(FRONTEND_DIST, asset_path)
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.get("/assets/<path:asset_path>")
def mission_unified_assets(asset_path: str):
    if not FRONTEND_DIST.exists():
        return jsonify({"error": f"Frontend bundle not found at {FRONTEND_DIST}. Run: cd production_system/frontend ; npm run build"}), 503
    return send_from_directory(FRONTEND_DIST / "assets", asset_path)


@app.get("/options")
@app.get("/legacy-api/options")
def options():
    layers = []
    if CHECKPOINT.exists():
        try:
            layers = _load_service().list_layers()
        except Exception:
            layers = []
    model_choices = sorted(_resolve_model_checkpoint_map().keys())
    return jsonify(
        {
            "layers": layers,
            "bands": ["rgb", "r", "g", "b", "rg", "rb", "gb"],
            "normalize_modes": ["unit", "zscore", "none"],
            "image_sizes": [64, 96, 128, 160, 224],
            "dataset_sources": curated_sources(),
            "model_choices": model_choices,
        }
    )


@app.get("/healthz")
def healthz():
    # Liveness probe: lightweight response, does not require model initialization.
    cfg = _security_config()
    return jsonify(
        {
            "status": "ok",
            "service": "unified-space-debris-detection",
            "auth_required": bool(cfg["auth_required"]),
            "rate_limit_per_min": int(cfg["rate_limit_per_min"]),
            "key_source": str(cfg.get("rotation", {}).get("source", "unknown")),
        }
    )


@app.get("/readyz")
@app.get("/legacy-api/readyz")
def readyz():
    # Readiness probe: validates checkpoint and model service initialization.
    checkpoint_exists = CHECKPOINT.exists()
    if not checkpoint_exists:
        return jsonify({"status": "not_ready", "reason": "checkpoint_missing", "checkpoint": str(CHECKPOINT)}), 503

    try:
        svc = _load_service()
    except Exception as exc:
        return jsonify({"status": "not_ready", "reason": "service_init_failed", "error": str(exc)}), 503

    return jsonify(
        {
            "status": "ready",
            "checkpoint_exists": CHECKPOINT.exists(),
            "demo_mode": bool(getattr(svc, "demo_mode", False)),
        }
    )


@app.get("/whoami")
def whoami():
    return jsonify(
        {
            "role": getattr(g, "auth_role", "anonymous"),
            "identity": getattr(g, "identity", "unknown"),
        }
    )


@app.get("/security_policy")
@require_role("admin")
def security_policy():
    cfg = _security_config()
    rotation = cfg.get("rotation", {})
    return jsonify(
        {
            "auth_required": bool(cfg["auth_required"]),
            "rate_limit_per_min": int(cfg["rate_limit_per_min"]),
            "role_rate_limits": cfg.get("role_rate_limits", {}),
            "invalid_key_lockout_threshold": int(cfg["invalid_key_lockout_threshold"]),
            "invalid_key_lockout_seconds": int(cfg["invalid_key_lockout_seconds"]),
            "anomaly_threshold_per_min": int(cfg["anomaly_threshold_per_min"]),
            "key_rotation": rotation,
            "audit_log_enabled": bool(cfg["audit_log_enabled"]),
            "audit_log_path": str(cfg["audit_log_path"]),
            "audit_retention_days": int(cfg["audit_retention_days"]),
        }
    )


@app.get("/dataset_inventory")
@app.get("/legacy-api/dataset_inventory")
def dataset_inventory():
    folder = request.args.get("folder", "").strip()
    if not folder:
        return jsonify({"error": "folder is required"}), 400
    limit = int(request.args.get("limit", "500"))
    items = build_dataset_inventory(folder, limit=limit)
    return jsonify({"folder": folder, "count": len(items), "items": items})


@app.get("/mission_status")
@app.get("/legacy-api/mission_status")
def mission_status():
    folder = request.args.get("folder", "").strip()
    if not folder:
        folder = str(DEFAULT_IMAGES_DIR if DEFAULT_IMAGES_DIR.exists() else (ROOT / "data"))

    checkpoint_exists = CHECKPOINT.exists()
    service_ready = False
    service_error = ""
    if checkpoint_exists:
        try:
            _load_service()
            service_ready = True
        except Exception as exc:
            service_error = str(exc)

    benchmark_path = ROOT / "artifacts" / "image_bench" / "image_bench_summary.json"
    benchmark_payload = _load_json_if_exists(benchmark_path)
    benchmark_models = []
    for model_name, stats in (benchmark_payload.get("results", {}) or {}).items():
        benchmark_models.append(
            {
                "model": model_name,
                "accuracy": stats.get("accuracy", 0.0),
                "precision": stats.get("precision", 0.0),
                "recall": stats.get("recall", 0.0),
                "f1": stats.get("f1", 0.0),
                "test_loss": stats.get("test_loss", 0.0),
                "checkpoint": stats.get("checkpoint", ""),
            }
        )

    try:
        brief = _build_orbital_brief()
        orbital_ok = True
        orbital_error = ""
    except Exception as exc:
        brief = {}
        orbital_ok = False
        orbital_error = str(exc)

    try:
        inventory_items = build_dataset_inventory(folder, limit=1)
        dataset_state = {
            "state": "ready",
            "detail": f"{len(inventory_items)}+ files discoverable",
            "folder": folder,
        }
    except Exception as exc:
        dataset_state = {
            "state": "warning",
            "detail": str(exc),
            "folder": folder,
        }

    model_choices = sorted(_resolve_model_checkpoint_map().keys())
    layers: list[str] = []
    if checkpoint_exists:
        try:
            layers = _load_service().list_layers()
        except Exception:
            layers = []

    return jsonify(
        {
            "readyz": {
                "status": "ready" if service_ready else "not_ready",
                "checkpoint_exists": checkpoint_exists,
                "error": service_error,
            },
            "benchmark": {
                "state": "ready" if len(benchmark_models) > 0 else "warning",
                "models": benchmark_models,
                "num_models": len(benchmark_models),
            },
            "orbital": {
                "state": "ready" if orbital_ok else "warning",
                "alerts": (brief.get("visualization", {}) or {}).get("alerts", []),
                "brief": brief,
                "error": orbital_error,
            },
            "dataset": dataset_state,
            "options": {
                "layers": layers,
                "model_choices": model_choices,
                "bands": ["rgb", "r", "g", "b", "rg", "rb", "gb"],
                "normalize_modes": ["unit", "zscore", "none"],
                "image_sizes": [64, 96, 128, 160, 224],
                "dataset_sources": curated_sources(),
            },
        }
    )


@app.get("/gallery_inventory")
def gallery_inventory():
    folder = request.args.get("folder", "").strip()
    if not folder:
        folder = str(ROOT / "data")
    limit = int(request.args.get("limit", "120"))
    items = build_dataset_inventory(folder, limit=limit)
    for item in items:
        path = Path(item["path"])
        item["thumb"] = image_file_to_base64(path, max_size=180)
    return jsonify({"folder": folder, "count": len(items), "items": items})


@app.get("/preview_image")
def preview_image():
    path = request.args.get("path", "").strip()
    if not path:
        return jsonify({"error": "path is required"}), 400
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return jsonify({"error": f"image not found: {path}"}), 404
    return jsonify({"path": path, "image": image_file_to_base64(file_path)})


@app.post("/predict")
@app.post("/legacy-api/predict")
@require_role("analyst")
def predict():
    model_name = request.form.get("model_name", "unified_latest").strip().lower() or "unified_latest"
    try:
        svc = _load_service(model_name)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    optical_image = None
    radar_image = None

    if "optical" in request.files and request.files["optical"].filename:
        optical_image = Image.open(request.files["optical"].stream)

    if "radar" in request.files and request.files["radar"].filename:
        radar_image = Image.open(request.files["radar"].stream)

    physics_raw = request.form.get("physics", "")
    image_size = int(request.form.get("image_size", "64"))
    optical_band = request.form.get("optical_band", "rgb")
    normalize_mode = request.form.get("normalize_mode", "unit")
    camera_threshold = float(request.form.get("camera_threshold", "0.0"))
    operator_profile = request.form.get("operator_profile", "balanced").strip().lower() or "balanced"
    layer_name = request.form.get("layer_name", "").strip() or None

    options = PreprocessOptions(
        image_size=image_size,
        optical_band=optical_band,
        normalize_mode=normalize_mode,
        camera_threshold=max(0.0, min(1.0, camera_threshold)),
    )

    physics_vector = None
    if physics_raw.strip():
        try:
            physics_vector = np.array([float(v.strip()) for v in physics_raw.split(",") if v.strip()], dtype=np.float32)
        except ValueError:
            return jsonify({"error": "Physics vector must be numeric comma-separated values."}), 400

    inputs, visuals = svc.prepare_inputs_with_visuals(
        optical_image=optical_image,
        radar_image=radar_image,
        physics_vector=physics_vector,
        options=options,
    )
    result, activation_visual = svc.predict_with_layer(inputs, layer_name=layer_name)
    
    evidence = None
    rgb_analysis = None
    if optical_image is not None:
        evidence = _build_evidence_visuals(optical_image)
        rgb_analysis = _build_rgb_analysis(optical_image)
    elif radar_image is not None:
        evidence = _build_evidence_visuals(radar_image)
        rgb_analysis = _build_rgb_analysis(radar_image)

    decision_basis = _build_decision_basis(
        detect_probability=result.detect_probability,
        collision_probability=result.collision_probability,
        class_probabilities=result.class_probabilities,
        evidence=evidence,
        inference_source=result.inference_source,
    )
    decision_basis["operator_profile"] = operator_profile
    decision_basis["inference_source"] = result.inference_source
    operational_summary = _build_operational_summary(decision_basis)

    return jsonify(
        {
            "requested_model": model_name,
            "operator_profile": operator_profile,
            "detect_probability": result.detect_probability,
            "collision_probability": result.collision_probability,
            "predicted_class": result.predicted_class,
            "class_probabilities": result.class_probabilities,
            "orbit_vector": result.orbit_vector,
            "snr_prediction": result.snr_prediction,
            "inference_source": result.inference_source,
            "preprocessed_visuals": visuals,
            "activation_visual": activation_visual,
            "evidence_visuals": evidence,
            "rgb_analysis": rgb_analysis,
            "decision_basis": decision_basis,
            "operational_summary": operational_summary,
        }
    )


@app.post("/predict_dataset")
@app.post("/legacy-api/predict_dataset")
@require_role("analyst")
def predict_dataset():
    model_name = request.form.get("model_name", "unified_latest").strip().lower() or "unified_latest"
    try:
        svc = _load_service(model_name)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    dataset_dir = request.form.get("dataset_dir", "").strip()
    if not dataset_dir:
        return jsonify({"error": "dataset_dir is required."}), 400

    modality = request.form.get("modality", "optical")
    max_samples = int(request.form.get("max_samples", "12"))
    image_size = int(request.form.get("image_size", "64"))
    optical_band = request.form.get("optical_band", "rgb")
    normalize_mode = request.form.get("normalize_mode", "unit")
    camera_threshold = float(request.form.get("camera_threshold", "0.0"))
    operator_profile = request.form.get("operator_profile", "balanced").strip().lower() or "balanced"

    options = PreprocessOptions(
        image_size=image_size,
        optical_band=optical_band,
        normalize_mode=normalize_mode,
        camera_threshold=max(0.0, min(1.0, camera_threshold)),
    )

    discovered = discover_modality_paths(dataset_dir)
    paths = discovered.get(modality, []) if modality in {"optical", "radar"} else discovered["all"]
    if not paths:
        return jsonify({"error": f"No images found for modality '{modality}' in {dataset_dir}"}), 400

    selected = paths[: max(1, max_samples)]
    rows = []
    detect_vals = []
    collision_vals = []

    for path in selected:
        image = Image.open(path).convert("RGB")
        inputs = svc.prepare_inputs(
            optical_image=image if modality != "radar" else None,
            radar_image=image if modality == "radar" else None,
            physics_vector=None,
            options=options,
        )
        result = svc.predict(inputs)
        evidence = _build_evidence_visuals(image, max_size=160)
        detect_vals.append(result.detect_probability)
        collision_vals.append(result.collision_probability)
        decision_basis = _build_decision_basis(
            detect_probability=result.detect_probability,
            collision_probability=result.collision_probability,
            class_probabilities=result.class_probabilities,
            evidence=evidence,
            inference_source=result.inference_source,
        )
        decision_basis["operator_profile"] = operator_profile
        decision_basis["inference_source"] = result.inference_source
        operational_summary = _build_operational_summary(decision_basis)

        rows.append(
            {
                "file": str(path),
                "file_name": path.name,
                "detect_probability": result.detect_probability,
                "collision_probability": result.collision_probability,
                "predicted_class": result.predicted_class,
                "predicted_class_name": f"class_{result.predicted_class}",
                "detect_label": decision_basis["predicted_label"],
                "thumb": image_file_to_base64(path, max_size=160),
                "bbox_overlay_thumb": evidence["bbox_overlay_visual"],
                "heatmap_thumb": evidence["heatmap_visual"],
                "bbox": evidence["bbox"],
                "inference_source": result.inference_source,
                "decision_basis": decision_basis,
                "operational_summary": operational_summary,
            }
        )

    return jsonify(
        {
            "requested_model": model_name,
            "dataset_dir": dataset_dir,
            "modality": modality,
            "operator_profile": operator_profile,
            "num_images": len(paths),
            "processed": len(selected),
            "avg_detect_probability": float(np.mean(detect_vals)),
            "avg_collision_probability": float(np.mean(collision_vals)),
            "max_detect_probability": float(np.max(detect_vals)),
            "min_detect_probability": float(np.min(detect_vals)),
            "samples": rows,
        }
    )


@app.get("/model_benchmark")
@app.get("/legacy-api/model_benchmark")
def model_benchmark():
    summary_path = ROOT / "artifacts" / "image_bench" / "image_bench_summary.json"
    if not summary_path.exists():
        return jsonify({"error": "Model benchmark summary not found. Run train_image_bench.py first."}), 404

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    table = []
    for model_name, stats in payload.get("results", {}).items():
        table.append(
            {
                "model": model_name,
                "accuracy": stats.get("accuracy", 0.0),
                "precision": stats.get("precision", 0.0),
                "recall": stats.get("recall", 0.0),
                "f1": stats.get("f1", 0.0),
                "test_loss": stats.get("test_loss", 0.0),
                "checkpoint": stats.get("checkpoint", ""),
            }
        )

    return jsonify(
        {
            "data_root": payload.get("data_root"),
            "classes": payload.get("classes", []),
            "num_samples": payload.get("num_samples", 0),
            "splits": payload.get("splits", {}),
            "models": table,
        }
    )


@app.post("/calibration_report")
@app.post("/legacy-api/calibration_report")
@require_role("analyst")
def calibration_report():
    model_name = request.form.get("model_name", "unified_latest").strip().lower() or "unified_latest"
    try:
        svc = _load_service(model_name)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    dataset_dir = request.form.get("dataset_dir", "").strip()
    if not dataset_dir:
        return jsonify({"error": "dataset_dir is required."}), 400

    modality = request.form.get("modality", "optical")
    max_samples = int(request.form.get("max_samples", "200"))
    bins = int(request.form.get("bins", "10"))
    image_size = int(request.form.get("image_size", "64"))
    optical_band = request.form.get("optical_band", "rgb")
    normalize_mode = request.form.get("normalize_mode", "unit")
    camera_threshold = float(request.form.get("camera_threshold", "0.0"))
    operating_point = float(request.form.get("operating_point", "0.5"))

    bins = max(5, min(25, bins))

    options = PreprocessOptions(
        image_size=image_size,
        optical_band=optical_band,
        normalize_mode=normalize_mode,
        camera_threshold=max(0.0, min(1.0, camera_threshold)),
    )

    discovered = discover_modality_paths(dataset_dir)
    paths = discovered.get(modality, []) if modality in {"optical", "radar"} else discovered["all"]
    if not paths:
        return jsonify({"error": f"No images found for modality '{modality}' in {dataset_dir}"}), 400

    selected = paths[: max(1, max_samples)]
    labeled_samples: list[tuple[float, int]] = []
    skipped_unlabeled = 0

    for path in selected:
        gt = _infer_ground_truth_label(path)
        if gt is None:
            skipped_unlabeled += 1
            continue

        image = Image.open(path).convert("RGB")
        inputs = svc.prepare_inputs(
            optical_image=image if modality != "radar" else None,
            radar_image=image if modality == "radar" else None,
            physics_vector=None,
            options=options,
        )
        result = svc.predict(inputs)
        labeled_samples.append((float(result.detect_probability), int(gt)))

    metrics = _compute_binary_calibration(labeled_samples, bins=bins)
    acceptance = _build_calibration_acceptance(metrics, operating_point=operating_point)
    return jsonify(
        {
            "requested_model": model_name,
            "dataset_dir": dataset_dir,
            "modality": modality,
            "requested_max_samples": max_samples,
            "total_discovered": len(paths),
            "evaluated": len(labeled_samples),
            "skipped_unlabeled": skipped_unlabeled,
            "bins": bins,
            "metrics": metrics,
            "acceptance_gates": acceptance,
        }
    )


@app.post("/predict_file")
@app.post("/legacy-api/predict_file")
@require_role("analyst")
def predict_file():
    model_name = request.form.get("model_name", "unified_latest").strip().lower() or "unified_latest"
    try:
        svc = _load_service(model_name)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    file_path = request.form.get("file_path", "").strip()
    if not file_path:
        return jsonify({"error": "file_path is required."}), 400

    modality = request.form.get("modality", "optical")
    image_size = int(request.form.get("image_size", "64"))
    optical_band = request.form.get("optical_band", "rgb")
    normalize_mode = request.form.get("normalize_mode", "unit")
    camera_threshold = float(request.form.get("camera_threshold", "0.0"))
    operator_profile = request.form.get("operator_profile", "balanced").strip().lower() or "balanced"
    layer_name = request.form.get("layer_name", "").strip() or None

    options = PreprocessOptions(
        image_size=image_size,
        optical_band=optical_band,
        normalize_mode=normalize_mode,
        camera_threshold=max(0.0, min(1.0, camera_threshold)),
    )

    image_path = Path(file_path)
    if not image_path.exists() or not image_path.is_file():
        return jsonify({"error": f"image not found: {file_path}"}), 404

    image = Image.open(image_path)
    inputs, visuals = svc.prepare_inputs_with_visuals(
        optical_image=image if modality != "radar" else None,
        radar_image=image if modality == "radar" else None,
        physics_vector=None,
        options=options,
    )
    result, activation_visual = svc.predict_with_layer(inputs, layer_name=layer_name)
    evidence = _build_evidence_visuals(image)
    rgb_analysis = _build_rgb_analysis(image)
    decision_basis = _build_decision_basis(
        detect_probability=result.detect_probability,
        collision_probability=result.collision_probability,
        class_probabilities=result.class_probabilities,
        evidence=evidence,
        inference_source=result.inference_source,
    )
    decision_basis["operator_profile"] = operator_profile
    decision_basis["inference_source"] = result.inference_source
    operational_summary = _build_operational_summary(decision_basis)

    return jsonify(
        {
            "requested_model": model_name,
            "operator_profile": operator_profile,
            "file_path": file_path,
            "modality": modality,
            "detect_probability": result.detect_probability,
            "collision_probability": result.collision_probability,
            "predicted_class": result.predicted_class,
            "class_probabilities": result.class_probabilities,
            "orbit_vector": result.orbit_vector,
            "snr_prediction": result.snr_prediction,
            "inference_source": result.inference_source,
            "preprocessed_visuals": visuals,
            "activation_visual": activation_visual,
            "evidence_visuals": evidence,
            "rgb_analysis": rgb_analysis,
            "decision_basis": decision_basis,
            "operational_summary": operational_summary,
        }
    )


@app.post("/load_nasa_public_data")
@require_role("admin")
def load_nasa_public_data():
    output_root = ROOT / "data"
    result = load_public_nasa_odpo_data(output_root)
    return jsonify(result)


@app.post("/load_all_public_data")
@app.post("/legacy-api/load_all_public_data")
@require_role("admin")
def load_all_public_data():
    output_root = ROOT / "data"
    nasa_result = load_public_nasa_odpo_data(output_root)
    gallery_root = output_root
    inventory = build_dataset_inventory(gallery_root, limit=500)
    return jsonify(
        {
            "status": "loaded",
            "nasa": nasa_result,
            "gallery_count": len(inventory),
            "gallery_root": str(gallery_root),
            "message": "Public ODPO files loaded and local gallery inventory refreshed.",
        }
    )


@app.get("/preview_nasa_solarflux")
@app.get("/legacy-api/preview_nasa_solarflux")
def preview_nasa_solarflux():
    csv_path = ROOT / "data" / "processed" / "nasa_odpo" / "solarflux_table_12172025.csv"
    if not csv_path.exists():
        return jsonify({"error": f"Parsed solar flux CSV not found at {csv_path}. Run /load_nasa_public_data first."}), 404

    df = pd.read_csv(csv_path)
    # Keep payload small for browser by returning summary and first rows.
    head = df.head(20).fillna("").to_dict(orient="records")
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    summary = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "numeric_columns": numeric_cols,
    }
    return jsonify({"summary": summary, "head": head})


@app.get("/orbital_brief")
@app.get("/legacy-api/orbital_brief")
def orbital_brief():
    return jsonify(_build_orbital_brief())


@app.get("/orbital_scene")
def orbital_scene():
    brief = _build_orbital_brief()
    return jsonify(
        {
            "timestamp": float(time.time()),
            "scene": brief.get("visualization", {}).get("scene", []),
            "shells": brief.get("visualization", {}).get("shells", []),
            "alerts": brief.get("visualization", {}).get("alerts", []),
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("USDD_PORT", "7860"))
    app.run(host="127.0.0.1", port=port, debug=False)
