"""Index out-of-distribution and hard-negative image sets for scientific hardening."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT  # noqa: F401
from src.data.local_dataset_loader import IMAGE_EXTENSIONS


CATEGORIES = ["cloud_noise", "sensor_artifacts", "star_streak_confusion"]


def _scan_images(root: Path) -> list[str]:
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    return [str(p.resolve()) for p in sorted(files)]


def build_index(dataset_root: Path, output: Path) -> dict:
    payload = {
        "dataset_root": str(dataset_root.resolve()),
        "hard_negative_sets": {},
        "summary": {"total_files": 0, "categories_present": 0},
    }

    for cat in CATEGORIES:
        cat_root = dataset_root / cat
        files = _scan_images(cat_root) if cat_root.exists() else []
        payload["hard_negative_sets"][cat] = {
            "path": str(cat_root.resolve()),
            "count": len(files),
            "files": files,
        }

    total = sum(v["count"] for v in payload["hard_negative_sets"].values())
    present = sum(1 for v in payload["hard_negative_sets"].values() if v["count"] > 0)
    payload["summary"] = {"total_files": total, "categories_present": present}

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Build OOD/hard-negative dataset index")
    parser.add_argument("--dataset_root", required=True)
    parser.add_argument("--output", default="artifacts/reports/hard_negative_index.json")
    args = parser.parse_args()

    payload = build_index(Path(args.dataset_root), Path(args.output))
    print(f"Wrote hard-negative index: {args.output}")
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
