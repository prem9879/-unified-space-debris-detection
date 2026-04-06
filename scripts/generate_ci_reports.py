"""Generate calibration and evaluation report artifacts for CI publishing."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader

from _bootstrap import PROJECT_ROOT  # noqa: F401
from src.data.synthetic_dataset import SyntheticDebrisDataset
from src.evaluation.classification_metrics import compute_classification_metrics
from src.evaluation.collision_metrics import compute_auc_roc, compute_brier, compute_ece
from src.evaluation.detection_metrics import compute_auc, tpr_at_fpr
from src.evaluation.orbit_metrics import position_rmse
from src.inference.service import UnifiedInferenceService
from webapp.flask_app import app


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "artifacts" / "reports"
CHECKPOINT = ROOT / "artifacts" / "checkpoints" / "unified_latest.pt"


def _build_tiny_labeled_dataset(root: Path) -> Path:
    debris_dir = root / "debris"
    non_debris_dir = root / "non_debris"
    debris_dir.mkdir(parents=True, exist_ok=True)
    non_debris_dir.mkdir(parents=True, exist_ok=True)

    for i in range(4):
        Image.new("RGB", (96, 96), (220, 220, 220)).save(debris_dir / f"debris_{i}.png")
        Image.new("RGB", (96, 96), (20, 20, 20)).save(non_debris_dir / f"non_debris_{i}.png")

    return root


def generate_calibration_report() -> dict:
    dataset_root = _build_tiny_labeled_dataset(REPORT_DIR / "ci_calibration_dataset")
    client = app.test_client()
    res = client.post(
        "/calibration_report",
        data={
            "dataset_dir": str(dataset_root),
            "modality": "optical",
            "max_samples": "8",
            "bins": "10",
        },
    )
    payload = res.get_json() if res.is_json else {"error": "non-json response"}
    if res.status_code != 200:
        raise RuntimeError(f"calibration_report failed: status={res.status_code} payload={payload}")
    return payload


def generate_eval_report(num_samples: int = 64, batch_size: int = 16) -> dict:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    svc = UnifiedInferenceService(CHECKPOINT, device=device, allow_demo_mode=True)
    model = svc.model
    model.eval()

    ds = SyntheticDebrisDataset(size=num_samples, num_classes=svc.num_classes)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0)

    y_detect_true, y_detect_prob = [], []
    y_cls_true, y_cls_pred = [], []
    y_collision_true, y_collision_prob = [], []
    orbit_true, orbit_pred = [], []

    with torch.no_grad():
        for batch in loader:
            radar = batch["radar"].to(device)
            optical = batch["optical"].to(device)
            physics = batch["physics"].to(device)
            outputs = model(radar, optical, physics)

            detect_prob = torch.sigmoid(outputs["detect_logits"]).cpu().numpy()
            collision_prob = torch.sigmoid(outputs["collision_logits"]).cpu().numpy()
            cls_pred = outputs["class_logits"].argmax(dim=-1).cpu().numpy()

            y_detect_prob.extend(detect_prob.tolist())
            y_detect_true.extend(batch["detect"].cpu().numpy().astype(int).tolist())
            y_collision_prob.extend(collision_prob.tolist())
            y_collision_true.extend(batch["collision"].cpu().numpy().astype(int).tolist())
            y_cls_pred.extend(cls_pred.tolist())
            y_cls_true.extend(batch["class"].cpu().numpy().astype(int).tolist())
            orbit_pred.extend(outputs["orbit_pred"].cpu().numpy().tolist())
            orbit_true.extend(batch["orbit"].cpu().numpy().tolist())

    orbit_true_np = np.array(orbit_true, dtype=np.float32)
    orbit_pred_np = np.array(orbit_pred, dtype=np.float32)

    return {
        "detection_auc": float(compute_auc(y_detect_true, y_detect_prob)),
        "detection_tpr_at_1e-5": float(tpr_at_fpr(y_detect_true, y_detect_prob, target_fpr=1e-5)),
        "classification": {
            k: (v.tolist() if hasattr(v, "tolist") else float(v))
            for k, v in compute_classification_metrics(y_cls_true, y_cls_pred).items()
        },
        "orbit_position_rmse": float(position_rmse(orbit_true_np, orbit_pred_np)),
        "collision_auc": float(compute_auc_roc(y_collision_true, y_collision_prob)),
        "collision_brier": float(compute_brier(y_collision_true, y_collision_prob)),
        "collision_ece": float(compute_ece(y_collision_true, y_collision_prob)),
        "metadata": {
            "source": "ci_synthetic_eval",
            "num_samples": int(num_samples),
            "batch_size": int(batch_size),
        },
    }


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    calibration = generate_calibration_report()
    evaluation = generate_eval_report()

    cal_path = REPORT_DIR / "calibration_report_ci.json"
    eval_path = REPORT_DIR / "eval_report_ci.json"
    cal_path.write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    eval_path.write_text(json.dumps(evaluation, indent=2), encoding="utf-8")

    print(f"Wrote {cal_path}")
    print(f"Wrote {eval_path}")


if __name__ == "__main__":
    main()
