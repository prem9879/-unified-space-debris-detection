"""Generate research-grade collision evaluation report with precision/recall and calibration metrics."""

from __future__ import annotations

import json
import csv
from pathlib import Path
import sys

import numpy as np

from _bootstrap import PROJECT_ROOT  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "production_system" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.collision import CollisionRequest
from app.services.collision_service import CollisionService

REPORT_DIR = ROOT / "artifacts" / "reports"
OUT_PATH = REPORT_DIR / "collision_eval_report.json"
OUT_CSV = REPORT_DIR / "collision_eval_metrics.csv"
OUT_BINS_CSV = REPORT_DIR / "collision_eval_calibration_bins.csv"
OUT_MD = REPORT_DIR / "collision_eval_appendix.md"


def _risk_label_from_physics(closest_km: float, rel_speed: float) -> int:
    score = 100.0 * (0.7 * np.exp(-closest_km / 8.0) + 0.3 * np.clip(rel_speed / 12.0, 0.0, 1.0))
    return int(score >= 45.0)


def _ece(labels: np.ndarray, probs: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(labels)
    if total == 0:
        return 0.0

    value = 0.0
    for idx in range(bins):
        lo, hi = float(edges[idx]), float(edges[idx + 1])
        if idx < bins - 1:
            mask = (probs >= lo) & (probs < hi)
        else:
            mask = (probs >= lo) & (probs <= hi)

        count = int(mask.sum())
        if count == 0:
            continue
        conf = float(np.mean(probs[mask]))
        acc = float(np.mean(labels[mask]))
        value += abs(acc - conf) * (count / total)
    return float(value)


def _binary_metrics(labels: np.ndarray, probs: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    preds = (probs >= threshold).astype(np.int32)
    tp = int(np.sum((preds == 1) & (labels == 1)))
    fp = int(np.sum((preds == 1) & (labels == 0)))
    fn = int(np.sum((preds == 0) & (labels == 1)))

    precision = float(tp / max(1, tp + fp))
    recall = float(tp / max(1, tp + fn))
    f1 = float((2.0 * precision * recall) / max(1e-12, precision + recall))
    brier = float(np.mean((probs - labels) ** 2))
    ece = _ece(labels, probs, bins=10)

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "brier": brier,
        "ece": ece,
        "tp": float(tp),
        "fp": float(fp),
        "fn": float(fn),
    }


def _calibration_bins(labels: np.ndarray, probs: np.ndarray, bins: int = 10) -> list[dict[str, float]]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows: list[dict[str, float]] = []

    for idx in range(bins):
        lo = float(edges[idx])
        hi = float(edges[idx + 1])
        if idx < bins - 1:
            mask = (probs >= lo) & (probs < hi)
        else:
            mask = (probs >= lo) & (probs <= hi)

        count = int(mask.sum())
        if count == 0:
            rows.append(
                {
                    "bin_index": float(idx),
                    "range_lo": lo,
                    "range_hi": hi,
                    "count": 0.0,
                    "mean_confidence": 0.0,
                    "empirical_accuracy": 0.0,
                    "gap": 0.0,
                }
            )
            continue

        conf = float(np.mean(probs[mask]))
        acc = float(np.mean(labels[mask]))
        rows.append(
            {
                "bin_index": float(idx),
                "range_lo": lo,
                "range_hi": hi,
                "count": float(count),
                "mean_confidence": conf,
                "empirical_accuracy": acc,
                "gap": abs(acc - conf),
            }
        )
    return rows


def _write_csv(report: dict[str, object], bins: list[dict[str, float]]) -> None:
    metrics = report.get("collision_metrics", {}) or {}
    metadata = report.get("metadata", {}) or {}

    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerow(["source", metadata.get("source", "")])
        writer.writerow(["samples", metadata.get("samples", "")])
        writer.writerow(["threshold", metadata.get("threshold", "")])
        writer.writerow(["precision", metrics.get("precision", "")])
        writer.writerow(["recall", metrics.get("recall", "")])
        writer.writerow(["f1", metrics.get("f1", "")])
        writer.writerow(["brier", metrics.get("brier", "")])
        writer.writerow(["ece", metrics.get("ece", "")])
        writer.writerow(["risk_score_mean", metrics.get("risk_score_mean", "")])
        writer.writerow(["risk_score_std", metrics.get("risk_score_std", "")])
        writer.writerow(["tp", metrics.get("tp", "")])
        writer.writerow(["fp", metrics.get("fp", "")])
        writer.writerow(["fn", metrics.get("fn", "")])

    with OUT_BINS_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["bin_index", "range_lo", "range_hi", "count", "mean_confidence", "empirical_accuracy", "gap"],
        )
        writer.writeheader()
        for row in bins:
            writer.writerow(row)


def _write_markdown(report: dict[str, object], bins: list[dict[str, float]]) -> None:
    metrics = report.get("collision_metrics", {}) or {}
    metadata = report.get("metadata", {}) or {}

    lines = [
        "# Collision Evaluation Appendix",
        "",
        "## Experimental Setup",
        "",
        f"- Source: {metadata.get('source', '')}",
        f"- Samples: {metadata.get('samples', '')}",
        f"- Decision Threshold: {metadata.get('threshold', '')}",
        "",
        "## Core Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Precision | {float(metrics.get('precision', 0.0)):.6f} |",
        f"| Recall | {float(metrics.get('recall', 0.0)):.6f} |",
        f"| F1 | {float(metrics.get('f1', 0.0)):.6f} |",
        f"| Brier | {float(metrics.get('brier', 0.0)):.6f} |",
        f"| ECE | {float(metrics.get('ece', 0.0)):.6f} |",
        f"| Mean Risk Score | {float(metrics.get('risk_score_mean', 0.0)):.6f} |",
        f"| Risk Score Std | {float(metrics.get('risk_score_std', 0.0)):.6f} |",
        f"| TP | {int(metrics.get('tp', 0))} |",
        f"| FP | {int(metrics.get('fp', 0))} |",
        f"| FN | {int(metrics.get('fn', 0))} |",
        "",
        "## Calibration Bins",
        "",
        "| Bin | Range | Count | Mean Confidence | Empirical Accuracy | Gap |",
        "|---:|---|---:|---:|---:|---:|",
    ]

    for row in bins:
        lines.append(
            f"| {int(row['bin_index'])} | [{row['range_lo']:.2f}, {row['range_hi']:.2f}] | {int(row['count'])} | {row['mean_confidence']:.4f} | {row['empirical_accuracy']:.4f} | {row['gap']:.4f} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(samples: int = 200) -> dict[str, object]:
    rng = np.random.default_rng(77)
    service = CollisionService()

    y_true: list[int] = []
    y_prob: list[float] = []
    risk_scores: list[float] = []

    for idx in range(samples):
        pa = np.array([7000.0, rng.uniform(-60, 60), rng.uniform(-40, 40)], dtype=np.float64)
        va = np.array([rng.uniform(-0.02, 0.02), 7.58 + rng.uniform(-0.1, 0.1), rng.uniform(-0.03, 0.03)], dtype=np.float64)
        pb = pa + np.array([rng.uniform(0.1, 6.0), rng.uniform(-3.5, 3.5), rng.uniform(-2.0, 2.0)], dtype=np.float64)
        vb = va + np.array([rng.uniform(-0.05, 0.05), rng.uniform(-0.12, 0.12), rng.uniform(-0.05, 0.05)], dtype=np.float64)

        gt_rel_speed = float(np.linalg.norm(vb - va))
        gt_closest_proxy = float(np.linalg.norm(pb - pa))
        gt = _risk_label_from_physics(gt_closest_proxy, gt_rel_speed)

        history_a = [
            {"t_s": 0.0, "x_km": float(pa[0]), "y_km": float(pa[1]), "z_km": float(pa[2])},
            {"t_s": 60.0, "x_km": float(pa[0] + va[0] * 60), "y_km": float(pa[1] + va[1] * 60), "z_km": float(pa[2] + va[2] * 60)},
            {"t_s": 120.0, "x_km": float(pa[0] + va[0] * 120), "y_km": float(pa[1] + va[1] * 120), "z_km": float(pa[2] + va[2] * 120)},
        ]
        history_b = [
            {"t_s": 0.0, "x_km": float(pb[0]), "y_km": float(pb[1]), "z_km": float(pb[2])},
            {"t_s": 60.0, "x_km": float(pb[0] + vb[0] * 60), "y_km": float(pb[1] + vb[1] * 60), "z_km": float(pb[2] + vb[2] * 60)},
            {"t_s": 120.0, "x_km": float(pb[0] + vb[0] * 120), "y_km": float(pb[1] + vb[1] * 120), "z_km": float(pb[2] + vb[2] * 120)},
        ]

        response = service.assess(
            CollisionRequest(
                object_a=f"SAT-{idx:04d}",
                object_b=f"DEBRIS-{idx:04d}",
                position_a_km=pa.tolist(),
                velocity_a_km_s=va.tolist(),
                position_b_km=pb.tolist(),
                velocity_b_km_s=vb.tolist(),
                ai_forecast_horizon_s=3600,
                ai_risk_weight=0.4,
                history_a=history_a,
                history_b=history_b,
            )
        )

        y_true.append(gt)
        y_prob.append(float(response.collision_probability))
        risk_scores.append(float(response.risk_score))

    labels = np.array(y_true, dtype=np.float64)
    probs = np.array(y_prob, dtype=np.float64)
    metrics = _binary_metrics(labels, probs)
    bins = _calibration_bins(labels, probs, bins=10)

    return {
        "metadata": {
            "source": "synthetic_conjunction_benchmark",
            "samples": samples,
            "threshold": 0.5,
        },
        "collision_metrics": {
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "brier": metrics["brier"],
            "ece": metrics["ece"],
            "risk_score_mean": float(np.mean(risk_scores)),
            "risk_score_std": float(np.std(risk_scores)),
            "tp": int(metrics["tp"]),
            "fp": int(metrics["fp"]),
            "fn": int(metrics["fn"]),
        },
        "calibration_bins": bins,
    }


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report(samples=220)
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    bins = list(report.get("calibration_bins", []))
    _write_csv(report, bins)
    _write_markdown(report, bins)
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_BINS_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
