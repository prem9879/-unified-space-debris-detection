"""
Main evaluation script for UnifiedDebrisNet
Runs all metrics and generates plots for the trained model.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.synthetic_dataset import SyntheticDebrisDataset  # noqa: E402
from src.inference.service import UnifiedInferenceService  # noqa: E402
from src.evaluation.classification_metrics import compute_classification_metrics  # noqa: E402
from src.evaluation.collision_metrics import compute_auc_roc, compute_brier, compute_ece  # noqa: E402
from src.evaluation.detection_metrics import compute_auc, tpr_at_fpr  # noqa: E402
from src.evaluation.orbit_metrics import position_rmse  # noqa: E402

def main():
    parser = argparse.ArgumentParser(description="Evaluate UnifiedDebrisNet")
    parser.add_argument("--checkpoint", type=str, default="artifacts/checkpoints/unified_latest.pt")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--num_samples", type=int, default=128)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    ckpt_path = Path(args.checkpoint)
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found at {ckpt_path}. Run main_train.py first.")

    inference_service = UnifiedInferenceService(ckpt_path, device=device, allow_demo_mode=False)
    model = inference_service.model
    model.eval()
    num_classes = inference_service.num_classes

    test_ds = SyntheticDebrisDataset(size=args.num_samples, num_classes=num_classes)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    y_detect_true, y_detect_prob = [], []
    y_cls_true, y_cls_pred = [], []
    y_collision_true, y_collision_prob = [], []
    orbit_true, orbit_pred = [], []

    with torch.no_grad():
        for batch in test_loader:
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

    report = {
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
    }

    out_path = Path("artifacts/eval_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    print(f"Saved evaluation report to: {out_path}")

if __name__ == "__main__":
    main()
