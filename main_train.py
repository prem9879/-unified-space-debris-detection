"""
Main training script for UnifiedDebrisNet
Trains the full multi-modal model end-to-end.
"""
import argparse
import json
from pathlib import Path
import sys

import torch
from torch.utils.data import DataLoader, random_split
import yaml

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.synthetic_dataset import SyntheticDebrisDataset  # noqa: E402
from src.models.unified_debris_net import UnifiedDebrisNet  # noqa: E402
from src.training.trainer import Trainer  # noqa: E402
from src.losses.multitask_loss import MultiTaskLoss  # noqa: E402
from src.losses.physics_loss import PhysicsRadarLoss  # noqa: E402
from src.losses.sgp4_loss import SGP4ResidualLoss  # noqa: E402
from src.losses.calibration_loss import ECELoss  # noqa: E402


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_dataloaders(batch_size: int, num_classes: int) -> dict:
    dataset = SyntheticDebrisDataset(size=256, num_classes=num_classes)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])
    return {
        "train": DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0),
        "val": DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0),
    }

def main():
    parser = argparse.ArgumentParser(description="Train UnifiedDebrisNet")
    parser.add_argument("--config", type=str, default="configs/unified.yaml")
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=None)
    parser.add_argument("--num_classes", type=int, default=4)
    args = parser.parse_args()

    config = load_config(Path(args.config))
    batch_size = args.batch_size or int(config.get("batch_size", 16))
    epochs = args.epochs or int(config.get("epochs", 5))
    lr = args.lr or float(config.get("learning_rate", 1e-3))
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = UnifiedDebrisNet(num_classes=args.num_classes)
    dataloaders = build_dataloaders(batch_size=batch_size, num_classes=args.num_classes)

    multitask_loss = MultiTaskLoss()
    physics_loss = PhysicsRadarLoss(pt=1.5e6, g=10**(49.7/10), lamb=0.225, l=1.0, k_b=1.38e-23, t=290, b=5e3, nf=2.0)
    sgp4_loss = SGP4ResidualLoss()
    ece_loss = ECELoss()

    optimizer = torch.optim.AdamW(
        list(model.parameters()) + list(multitask_loss.parameters()),
        lr=lr,
        weight_decay=float(config.get("weight_decay", 1e-4)),
    )

    trainer = Trainer(
        model=model,
        dataloaders=dataloaders,
        optimizer=optimizer,
        loss_fn=multitask_loss,
        aux_losses={"physics": physics_loss, "sgp4": sgp4_loss, "ece": ece_loss},
        device=device,
    )
    history = trainer.fit(epochs=epochs)

    out_dir = Path("artifacts")
    ckpt_dir = out_dir / "checkpoints"
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = {
        "model_state": model.state_dict(),
        "num_classes": args.num_classes,
        "config": config,
    }
    torch.save(checkpoint, ckpt_dir / "unified_latest.pt")

    with (out_dir / "train_history.json").open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print(f"Training complete. Checkpoint: {ckpt_dir / 'unified_latest.pt'}")

if __name__ == "__main__":
    main()
