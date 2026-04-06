"""Build a versioned immutable manifest for a labeled debris dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

from _bootstrap import PROJECT_ROOT  # noqa: F401
from src.data.dataset_manifest import create_dataset_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Create immutable dataset manifest with locked splits")
    parser.add_argument("--dataset_root", required=True, type=str)
    parser.add_argument("--dataset_name", default="real_labeled_debris", type=str)
    parser.add_argument("--dataset_version", default="v1", type=str)
    parser.add_argument("--manifest_path", default="data/manifests/debris_manifest_v1.json", type=str)
    parser.add_argument("--split_seed", default=42, type=int)
    parser.add_argument("--train_ratio", default=0.7, type=float)
    parser.add_argument("--val_ratio", default=0.15, type=float)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    manifest = create_dataset_manifest(
        dataset_root=Path(args.dataset_root),
        manifest_path=Path(args.manifest_path),
        dataset_name=args.dataset_name,
        dataset_version=args.dataset_version,
        split_seed=args.split_seed,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        immutable=True,
        overwrite=bool(args.overwrite),
    )

    print("Manifest created:")
    print(f"  path: {args.manifest_path}")
    print(f"  dataset: {manifest['dataset_name']} ({manifest['dataset_version']})")
    print(f"  files: {manifest['num_files']}")
    print(f"  digest: {manifest['manifest_digest']}")


if __name__ == "__main__":
    main()
