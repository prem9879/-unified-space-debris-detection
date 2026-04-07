"""Train multiple image backbones on a local debris dataset with strong preprocessing."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import torch
from torch import nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.debris_image_data import ensure_dataset_bootstrap  # noqa: E402
from src.data.dataset_manifest import load_dataset_manifest  # noqa: E402
from src.training.model_zoo import (  # noqa: E402
    available_image_backbones,
    build_image_backbone,
)


def _build_model(name: str, num_classes: int) -> nn.Module:
    return build_image_backbone(name, num_classes=num_classes, pretrained=True)


def _metrics(y_true: list[int], y_pred: list[int]) -> dict:
    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    return {
        "accuracy": float(acc),
        "precision": float(p),
        "recall": float(r),
        "f1": float(f1),
    }


def _run_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: str,
    train: bool,
) -> tuple[float, dict]:
    if train:
        model.train()
    else:
        model.eval()

    losses: list[float] = []
    y_true: list[int] = []
    y_pred: list[int] = []

    context = torch.enable_grad() if train else torch.no_grad()
    with context:
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)

            if train:
                optimizer.zero_grad(set_to_none=True)

            logits = model(x)
            loss = criterion(logits, y)

            if train:
                loss.backward()
                optimizer.step()

            losses.append(loss.item())
            pred = torch.argmax(logits, dim=1)
            y_true.extend(y.cpu().tolist())
            y_pred.extend(pred.cpu().tolist())

    avg_loss = float(sum(losses) / max(1, len(losses)))
    return avg_loss, _metrics(y_true, y_pred)


def build_reproducible_split_indices(
    num_samples: int,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    seed: int = 42,
) -> dict[str, list[int]]:
    if num_samples < 3:
        raise ValueError("num_samples must be >= 3 to produce train/val/test splits")
    if train_ratio <= 0 or val_ratio <= 0 or train_ratio + val_ratio >= 1.0:
        raise ValueError(
            "train_ratio and val_ratio must be positive and sum to less than 1"
        )

    n_train = int(train_ratio * num_samples)
    n_val = int(val_ratio * num_samples)
    n_test = num_samples - n_train - n_val
    if n_train < 1 or n_val < 1 or n_test < 1:
        raise ValueError(
            "split resulted in an empty partition; adjust ratios or sample count"
        )

    generator = torch.Generator().manual_seed(seed)
    perm = torch.randperm(num_samples, generator=generator).tolist()
    return {
        "train": perm[:n_train],
        "val": perm[n_train : n_train + n_val],
        "test": perm[n_train + n_val :],
    }


def train_image_bench(
    data_dir: str | Path,
    output_dir: str | Path,
    model_names: list[str],
    epochs: int,
    batch_size: int,
    image_size: int,
    images_per_class: int = 320,
    split_seed: int = 42,
    dataset_manifest: str | None = None,
) -> dict:
    data_root = Path(data_dir)
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    bootstrap = ensure_dataset_bootstrap(
        data_root, images_per_class=max(64, int(images_per_class)), image_size=image_size
    )

    train_tf = transforms.Compose(
        [
            transforms.RandomResizedCrop(
                image_size, scale=(0.72, 1.0), ratio=(0.85, 1.15)
            ),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.15),
            transforms.RandomRotation(16),
            transforms.RandomAutocontrast(p=0.4),
            transforms.ColorJitter(
                brightness=0.28, contrast=0.24, saturation=0.15, hue=0.02
            ),
            transforms.RandomGrayscale(p=0.08),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            transforms.RandomErasing(p=0.12, scale=(0.02, 0.08), ratio=(0.3, 3.0)),
        ]
    )
    eval_tf = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    reference_dataset = datasets.ImageFolder(str(data_root), transform=None)
    if len(reference_dataset.classes) < 2:
        raise RuntimeError("Need at least 2 class folders for classification training.")

    n = len(reference_dataset)
    split_protocol = {
        "method": "seeded_random_permutation",
        "train_ratio": 0.7,
        "val_ratio": 0.15,
        "test_ratio": 0.15,
        "seed": split_seed,
    }

    if dataset_manifest:
        manifest = load_dataset_manifest(dataset_manifest)
        rel_to_index: dict[str, int] = {}
        for idx, sample in enumerate(reference_dataset.samples):
            sample_path = Path(sample[0]).resolve()
            rel = str(sample_path.relative_to(data_root.resolve())).replace("\\", "/")
            rel_to_index[rel] = idx

        def _indices(split_name: str) -> list[int]:
            rel_paths = manifest.get("splits", {}).get(split_name, [])
            indices = [rel_to_index[p] for p in rel_paths if p in rel_to_index]
            if not indices:
                raise ValueError(
                    f"No usable indices for split '{split_name}' from manifest"
                )
            return indices

        train_idx = _indices("train")
        val_idx = _indices("val")
        test_idx = _indices("test")
        split_protocol = {
            "method": "immutable_manifest",
            "manifest_path": str(dataset_manifest),
            "manifest_dataset_name": manifest.get("dataset_name"),
            "manifest_dataset_version": manifest.get("dataset_version"),
            "manifest_digest": manifest.get("manifest_digest"),
            "seed": manifest.get("split_protocol", {}).get("seed"),
        }
    else:
        split = build_reproducible_split_indices(
            num_samples=n, train_ratio=0.7, val_ratio=0.15, seed=split_seed
        )
        train_idx = split["train"]
        val_idx = split["val"]
        test_idx = split["test"]

    n_train = len(train_idx)
    n_val = len(val_idx)
    n_test = len(test_idx)

    train_ds = Subset(
        datasets.ImageFolder(str(data_root), transform=train_tf), train_idx
    )
    val_ds = Subset(datasets.ImageFolder(str(data_root), transform=eval_tf), val_idx)
    test_ds = Subset(datasets.ImageFolder(str(data_root), transform=eval_tf), test_idx)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(
        test_ds, batch_size=batch_size, shuffle=False, num_workers=0
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    class_counts = [0] * len(reference_dataset.classes)
    for idx in train_idx:
        _, target = reference_dataset.samples[idx]
        class_counts[target] += 1
    class_weights = torch.tensor(
        [max(1.0, sum(class_counts) / max(1, count)) for count in class_counts],
        dtype=torch.float32,
        device=device,
    )
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.05)

    results: dict[str, dict] = {}

    for model_name in model_names:
        model = _build_model(model_name, num_classes=len(reference_dataset.classes)).to(
            device
        )
        optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4, weight_decay=2e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=max(1, epochs)
        )

        best_state = None
        best_val_f1 = -1.0
        history: list[dict] = []

        for epoch in range(1, epochs + 1):
            train_loss, train_m = _run_epoch(
                model, train_loader, optimizer, criterion, device, train=True
            )
            val_loss, val_m = _run_epoch(
                model, val_loader, optimizer, criterion, device, train=False
            )
            scheduler.step()

            row = {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "train_accuracy": train_m["accuracy"],
                "train_f1": train_m["f1"],
                "val_accuracy": val_m["accuracy"],
                "val_f1": val_m["f1"],
            }
            history.append(row)
            print(
                f"[{model_name}] epoch {epoch}/{epochs} train_f1={train_m['f1']:.4f} val_f1={val_m['f1']:.4f}"
            )

            if val_m["f1"] > best_val_f1:
                best_val_f1 = val_m["f1"]
                best_state = {
                    k: v.detach().cpu() for k, v in model.state_dict().items()
                }

        if best_state is not None:
            model.load_state_dict(best_state)

        test_loss, test_m = _run_epoch(
            model, test_loader, optimizer, criterion, device, train=False
        )

        ckpt = {
            "model_name": model_name,
            "classes": reference_dataset.classes,
            "num_classes": len(reference_dataset.classes),
            "image_size": image_size,
            "state_dict": model.state_dict(),
            "model_state": model.state_dict(),
            "metrics": test_m,
        }
        ckpt_path = output_root / f"{model_name}_best.pt"
        torch.save(ckpt, ckpt_path)

        results[model_name] = {
            "test_loss": test_loss,
            **test_m,
            "checkpoint": str(ckpt_path),
            "history": history,
        }

    summary = {
        "bootstrap": bootstrap,
        "data_root": str(data_root),
        "classes": reference_dataset.classes,
        "num_samples": len(reference_dataset),
        "split_protocol": split_protocol,
        "splits": {"train": n_train, "val": n_val, "test": n_test},
        "results": results,
    }

    with (output_root / "image_bench_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with (output_root / "image_bench_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "model",
                "accuracy",
                "precision",
                "recall",
                "f1",
                "test_loss",
                "checkpoint",
            ],
        )
        writer.writeheader()
        for model_name, stats in results.items():
            writer.writerow(
                {
                    "model": model_name,
                    "accuracy": stats["accuracy"],
                    "precision": stats["precision"],
                    "recall": stats["recall"],
                    "f1": stats["f1"],
                    "test_loss": stats["test_loss"],
                    "checkpoint": stats["checkpoint"],
                }
            )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train multiple image models on debris dataset"
    )
    parser.add_argument(
        "--data_dir", type=str, default=r"c:\Users\PREM DIWAN\Desktop\ml\images"
    )
    parser.add_argument("--output_dir", type=str, default="artifacts/image_bench")
    parser.add_argument(
        "--models", type=str, default=",".join(available_image_backbones())
    )
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--image_size", type=int, default=224)
    parser.add_argument("--images_per_class", type=int, default=320)
    parser.add_argument("--split_seed", type=int, default=42)
    parser.add_argument("--dataset_manifest", type=str, default="")
    args = parser.parse_args()

    model_names = [m.strip() for m in args.models.split(",") if m.strip()]
    summary = train_image_bench(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        model_names=model_names,
        epochs=args.epochs,
        batch_size=args.batch_size,
        image_size=args.image_size,
        images_per_class=args.images_per_class,
        split_seed=args.split_seed,
        dataset_manifest=args.dataset_manifest.strip() or None,
    )

    print("Image benchmark complete.")
    for model_name, stats in summary["results"].items():
        print(f"{model_name}: acc={stats['accuracy']:.4f} f1={stats['f1']:.4f}")


if __name__ == "__main__":
    main()
