# Unified Multi-Modal Space Debris Detection

## Abstract

This work presents a decision-support platform for space debris screening that combines optical imagery, radar-like representations, and compact physics vectors in a unified inference pipeline. The current release prioritizes reproducibility, calibration visibility, and operator-facing explainability over autonomous mission-critical control. We provide a benchmark workflow across multiple image backbones, deterministic split protocol metadata, API-level security controls, and a production-ready web service baseline. Results and deployment guidance are intended for research labs, university teams, and pre-operational evaluation workflows.

## 1. Introduction

Space-domain awareness workflows require robust debris classification signals while preserving uncertainty visibility and operator judgment. Many model demos optimize only top-line accuracy and omit calibration, traceability, and reproducibility controls. This repository addresses those gaps by pairing model outputs with explicit confidence-band decisions, operational summaries, and reproducible evaluation artifacts.

## 2. Problem Statement

Given multi-source observations, estimate:

- debris likelihood,
- collision-risk proxy,
- class probabilities,
- operationally interpretable recommendation text.

The system is positioned as a decision-support layer, not an autonomous flight-safety authority.

## 3. Data

### 3.1 Current data status

- Synthetic and bootstrapped image data for development and benchmarking.
- Optional ingestion of publicly available NASA ODPO tables for exploratory analysis.

### 3.2 Ground-truth requirements for operational transition

For production-grade claims, replace synthetic-first evaluation with curated, labeled orbital debris datasets and maintain immutable train/validation/test protocols.

## 4. Methods

### 4.1 Model and inference

- Multi-modal inference service with image preprocessing controls.
- Operator profile adaptation (`conservative`, `balanced`, `exploratory`).
- Decision-basis generation including margin, confidence band, and evidence ratios.

### 4.2 Image benchmark model zoo

The benchmark compares several CNN backbones (e.g., ResNet, DenseNet, EfficientNet, MobileNet, ShuffleNet, ConvNeXt) under one unified training/evaluation harness.

### 4.3 Calibration and reliability

The API computes ECE, MCE, Brier score, and reliability bins for binary debris detection, along with confusion statistics and balanced accuracy.

## 5. Reproducibility Protocol

This project enforces deterministic split generation through a seeded permutation strategy:

- ratios: 70/15/15 (train/val/test),
- split seed persisted in benchmark summary,
- validation-only model selection,
- test-once final reporting.

Reference: `SPLIT_PROTOCOL.md` and `build_reproducible_split_indices` in `src/training/train_image_bench.py`.

## 6. System and API Architecture

### 6.1 Service runtime

- Flask application serving dashboard + JSON endpoints.
- Gunicorn production process model.
- Docker packaging with healthcheck.

### 6.2 Operational endpoints

- `/healthz`: liveness probe.
- `/readyz`: readiness probe.
- `/predict`, `/predict_file`, `/predict_dataset`: inference paths.
- `/calibration_report`: reliability evaluation.

### 6.3 Security and governance controls

- API-key auth toggle (`USDD_REQUIRE_AUTH`).
- Role levels (`viewer`, `analyst`, `admin`).
- Per-identity rate limiting.
- Structured audit logging.

## 7. Experimental Design

### 7.1 Baseline training settings

- optimizer: AdamW,
- criterion: weighted cross entropy with label smoothing,
- augmentation: crop/flip/rotation/color jitter,
- scheduler: cosine annealing,
- deterministic split seed.

### 7.2 Reporting requirements

Each result table should include:

- dataset root/version,
- class distribution,
- split seed,
- split counts,
- model hyperparameters,
- preprocessing parameters,
- checkpoint identifier.

## 8. Results

Populate this section using `artifacts/image_bench/image_bench_summary.json` and corresponding CSV summaries.

Suggested table schema:

| Model | Accuracy | Precision | Recall | F1 | Test Loss |
| --- | ---: | ---: | ---: | ---: | ---: |
| ResNet18 | TODO | TODO | TODO | TODO | TODO |
| DenseNet121 | TODO | TODO | TODO | TODO | TODO |

## 9. Error Analysis

Document qualitative and quantitative errors:

- false positive cases by modality,
- false negative cases by low-SNR conditions,
- calibration drift by confidence bin,
- operator profile sensitivity analysis.

## 10. Limitations

- Synthetic/bootstrapped data may not represent mission operational distributions.
- Collision output is a proxy estimate, not a certified conjunction risk pipeline.
- Current controls improve reliability but do not provide formal SLA guarantees.

## 11. Deployment and MLOps Notes

- Runtime target: Python 3.11.
- Containerized serving path is available.
- Health/readiness probes are present.
- Additional production work: identity federation, secrets management, model registry governance, drift monitoring.

## 12. Ethical and Safety Position

This system should be treated as a human-in-the-loop research assistant. Operational decisions affecting mission-critical conjunction handling must include independent verification and established flight safety procedures.

## 13. Reproducibility Checklist

- [ ] Exact commit hash captured
- [ ] Runtime version captured (Python 3.11.x)
- [ ] Dependency lock captured
- [ ] Split seed recorded
- [ ] Train/val/test counts recorded
- [ ] Checkpoint hash recorded
- [ ] All metrics exported to JSON and CSV

## 14. Citation

Add BibTeX and repository citation details once publication metadata is finalized.
