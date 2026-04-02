# Dataset Split Protocol

This repository uses a deterministic train/validation/test split protocol for all benchmark and reportable runs.

## Objectives

- Reproducibility across machines and CI runs.
- Transparent comparability between model backbones.
- Strict separation of train/validation/test samples.

## Protocol Definition

- Split method: seeded random permutation over sample indices.
- Ratios: train 70%, validation 15%, test 15%.
- Default split seed: 42.
- Split generator implementation: `build_reproducible_split_indices` in `src/training/train_image_bench.py`.

## Rules

1. Use a single split seed for all models in one experiment.
2. Do not tune hyperparameters on the test split.
3. Select checkpoints based only on validation metrics.
4. Report test metrics only after model and threshold choices are frozen.
5. Persist seed and split protocol metadata in summary artifacts.

## Required Report Metadata

Every experiment report should include:

- dataset root path or dataset version identifier,
- split method,
- split ratios,
- seed value,
- class list,
- split counts,
- model list,
- training epochs and batch size,
- preprocessing settings.

## Example Run

```bash
python src/training/train_image_bench.py --data_dir "c:/Users/PREM DIWAN/Desktop/ml/images" --epochs 6 --batch_size 16 --image_size 224 --split_seed 42
```

## Reproducibility Check

- Running the same command twice with the same seed must produce identical split indices.
- Changing only the seed must produce different split indices while preserving split counts.
