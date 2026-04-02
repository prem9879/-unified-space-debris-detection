"""
Ablation Study Runner: Multi-modal and missing modality evaluation
"""
import torch


def run_ablation(models: dict, dataloaders: dict):
    """
    Evaluate all modality combinations and missing modality robustness.
    """
    results = {}
    device = "cuda" if torch.cuda.is_available() else "cpu"

    for name, model in models.items():
        model = model.to(device)
        model.eval()
        all_probs = []
        all_targets = []

        with torch.no_grad():
            for batch in dataloaders["val"]:
                radar = batch["radar"].to(device)
                optical = batch["optical"].to(device)
                physics = batch["physics"].to(device)

                if "no_radar" in name:
                    radar = torch.zeros_like(radar)
                if "no_optical" in name:
                    optical = torch.zeros_like(optical)
                if "no_physics" in name:
                    physics = torch.zeros_like(physics)

                out = model(radar, optical, physics)
                all_probs.extend(torch.sigmoid(out["detect_logits"]).cpu().tolist())
                all_targets.extend(batch["detect"].tolist())

        preds = [1 if p >= 0.5 else 0 for p in all_probs]
        correct = sum(int(p == t) for p, t in zip(preds, all_targets))
        results[name] = {"detection_accuracy": correct / max(1, len(all_targets))}

    return results
