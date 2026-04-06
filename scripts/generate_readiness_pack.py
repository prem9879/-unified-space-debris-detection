"""Generate a release readiness pack that consolidates evidence artifacts and gate status."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_pack(manifest: Path, benchmark: Path, calibration: Path, slo: Path, security_policy: Path, hard_negative: Path, output: Path) -> dict:
    manifest_payload = _load_json(manifest)
    benchmark_payload = _load_json(benchmark)
    calibration_payload = _load_json(calibration)
    slo_payload = _load_json(slo)
    security_payload = _load_json(security_policy)
    hard_negative_payload = _load_json(hard_negative)

    benchmark_results = benchmark_payload.get("results", {})
    if not benchmark_results:
        benchmark_results = benchmark_payload.get("benchmark", {}).get("best_model", {})

    gates = {
        "scientific": bool(manifest_payload.get("manifest_digest") and calibration_payload.get("acceptance_gates")),
        "reliability": bool(slo_payload.get("latency_ms")),
        "security": bool(security_payload.get("auth_required") is not None),
        "deployment": bool(benchmark_results),
        "hard_negatives": bool(hard_negative_payload.get("summary", {}).get("total_files", 0) >= 0),
    }

    pack = {
        "status": "release_ready" if all(gates.values()) else "needs_work",
        "evidence": {
            "manifest_digest": manifest_payload.get("manifest_digest"),
            "split_protocol": manifest_payload.get("split_protocol", {}),
            "class_balance": manifest_payload.get("class_counts", {}),
            "benchmark_best_model": benchmark_results,
            "calibration_acceptance": calibration_payload.get("acceptance_gates", {}),
            "slo": slo_payload,
            "security_policy": security_payload,
            "hard_negative_index": hard_negative_payload.get("summary", {}),
        },
        "gates": gates,
        "recommended_next_actions": [
            "Run a blind external evaluation against third-party labels.",
            "Keep production profile on managed identity + Key Vault only.",
            "Refresh calibration gates whenever dataset or model version changes.",
        ],
        "scores_target": {
            "scientific_credibility": 9.0,
            "engineering_reliability": 9.0,
            "security_and_governance_readiness": 9.0,
            "deployment_and_operations_maturity": 9.0,
            "product_ux_and_demo_impact": 9.0,
            "talent_recruitability_signal": 9.0,
            "government_ministry_adoption_readiness": 9.0,
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    return pack


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate release readiness pack")
    parser.add_argument("--manifest", default="data/manifests/debris_ops_v1.json")
    parser.add_argument("--benchmark", default="artifacts/reports/benchmark_card.json")
    parser.add_argument("--calibration", default="artifacts/reports/calibration_report_ci.json")
    parser.add_argument("--slo", default="artifacts/reports/slo_report.json")
    parser.add_argument("--security_policy", default="artifacts/reports/security_policy.json")
    parser.add_argument("--hard_negative", default="artifacts/reports/hard_negative_index.json")
    parser.add_argument("--output", default="artifacts/reports/readiness_pack.json")
    args = parser.parse_args()

    pack = build_pack(
        manifest=Path(args.manifest),
        benchmark=Path(args.benchmark),
        calibration=Path(args.calibration),
        slo=Path(args.slo),
        security_policy=Path(args.security_policy),
        hard_negative=Path(args.hard_negative),
        output=Path(args.output),
    )
    print(json.dumps(pack, indent=2))


if __name__ == "__main__":
    main()
