"""Emit a sanitized security policy artifact for release readiness packaging."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from webapp.flask_app import _security_config


def main() -> None:
    out_path = Path("artifacts/reports/security_policy.json")
    cfg = _security_config()
    policy = {
        "security_profile": cfg.get("security_profile"),
        "auth_required": bool(cfg.get("auth_required", False)),
        "rate_limit_per_min": int(cfg.get("rate_limit_per_min", 0)),
        "role_rate_limits": cfg.get("role_rate_limits", {}),
        "invalid_key_lockout_threshold": int(cfg.get("invalid_key_lockout_threshold", 0)),
        "invalid_key_lockout_seconds": int(cfg.get("invalid_key_lockout_seconds", 0)),
        "anomaly_threshold_per_min": int(cfg.get("anomaly_threshold_per_min", 0)),
        "audit_log_enabled": bool(cfg.get("audit_log_enabled", False)),
        "audit_retention_days": int(cfg.get("audit_retention_days", 0)),
        "key_rotation_source": cfg.get("rotation", {}).get("source", "unknown"),
        "managed_identity_only": cfg.get("security_profile") == "production",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")
    print(json.dumps(policy, indent=2))


if __name__ == "__main__":
    main()
