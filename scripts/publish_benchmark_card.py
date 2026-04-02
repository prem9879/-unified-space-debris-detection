"""Publish a locked benchmark card with scientific hardening metadata."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path


def _confidence_interval_wilson(successes: float, n: float, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    phat = successes / n
    denom = 1.0 + (z * z) / n
    center = (phat + (z * z) / (2.0 * n)) / denom
    spread = (z * math.sqrt((phat * (1.0 - phat) / n) + ((z * z) / (4.0 * n * n)))) / denom
    return max(0.0, center - spread), min(1.0, center + spread)


def build_card(manifest_path: Path, benchmark_path: Path, calibration_path: Path, output_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))

    class_balance = manifest.get("class_counts", {})
    split = manifest.get("split_protocol", {})
    digest = manifest.get("manifest_digest", "")

    best_model = None
    best_f1 = -1.0
    for model_name, stats in (benchmark.get("results", {}) or {}).items():
        f1 = float(stats.get("f1", 0.0))
        if f1 > best_f1:
            best_f1 = f1
            best_model = {"name": model_name, **stats}

    metrics = calibration.get("metrics", {})
    cm = metrics.get("confusion_matrix", {})
    tp = float(cm.get("tp", 0.0))
    tn = float(cm.get("tn", 0.0))
    fp = float(cm.get("fp", 0.0))
    fn = float(cm.get("fn", 0.0))
    total = tp + tn + fp + fn

    accuracy = float(metrics.get("accuracy", 0.0))
    low, high = _confidence_interval_wilson(successes=accuracy * max(1.0, total), n=max(1.0, total))

    false_positive_cost = float(fp * float(os.getenv("USDD_FALSE_POSITIVE_COST", "5.0")))
    false_negative_cost = float(fn * float(os.getenv("USDD_FALSE_NEGATIVE_COST", "20.0")))

    card = {
        "dataset": {
            "name": manifest.get("dataset_name"),
            "version": manifest.get("dataset_version"),
            "class_balance": class_balance,
            "split_seed": split.get("seed"),
            "split_digest": digest,
        },
        "benchmark": {
            "best_model": best_model,
            "num_models": len(benchmark.get("results", {}) or {}),
        },
        "calibration": {
            "ece": metrics.get("ece"),
            "brier_score": metrics.get("brier_score"),
            "recall": metrics.get("recall"),
            "false_alarm_rate": (fp / max(1.0, fp + tn)),
            "acceptance_gates": calibration.get("acceptance_gates", {}),
        },
        "confidence_intervals": {
            "accuracy_95ci": [low, high],
        },
        "false_positive_cost_analysis": {
            "false_positives": fp,
            "false_negatives": fn,
            "fp_unit_cost": float(os.getenv("USDD_FALSE_POSITIVE_COST", "5.0")),
            "fn_unit_cost": float(os.getenv("USDD_FALSE_NEGATIVE_COST", "20.0")),
            "estimated_total_cost": false_positive_cost + false_negative_cost,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(card, indent=2), encoding="utf-8")
    return card


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish locked scientific benchmark card")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--benchmark", default="artifacts/image_bench/image_bench_summary.json")
    parser.add_argument("--calibration", default="artifacts/reports/calibration_report_ci.json")
    parser.add_argument("--output", default="artifacts/reports/benchmark_card.json")
    args = parser.parse_args()

    card = build_card(
        manifest_path=Path(args.manifest),
        benchmark_path=Path(args.benchmark),
        calibration_path=Path(args.calibration),
        output_path=Path(args.output),
    )
    print(f"Benchmark card written to {args.output}")
    print(json.dumps(card, indent=2))


if __name__ == "__main__":
    main()
