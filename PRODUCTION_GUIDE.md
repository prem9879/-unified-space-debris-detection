# Space Debris Detection Production Guide

**Status:** Production ready
**Live:** [http://127.0.0.1:7868](http://127.0.0.1:7868)

## Overview

This workspace provides a space debris detection dashboard with the following capabilities:

- Dynamic RGB channel analysis with histograms and statistics
- Live evidence visualization with heatmaps and bounding-box overlays
- Multi-modal inference across optical, radar, and physics inputs
- Batch processing with PNG, CSV, and JSON export
- Benchmark comparison across 8 pretrained models
- Local-first execution with a Chart.js fallback renderer

## Dashboard Sections

### Hero

The top of the page provides quick access to loading data and opening the dataset explorer.

### Accuracy Strip

A compact summary shows the best benchmark model, best accuracy, best F1 score, and benchmark sample count.

### AI Pipeline

The pipeline explanation covers these steps:

1. Data ingestion from NASA and local files
2. Preprocessing with resizing, normalization, and thresholding
3. Feature extraction using CNN backbones
4. Multi-task prediction for detect, classify, collision, and orbit
5. Visual evidence generation with activations, heatmaps, and overlays
6. Benchmark comparison across trained models

### Live Inference

The live form supports:

- Image size selection
- Optical band selection
- Normalization mode selection
- Camera threshold adjustment
- Optional layer inspection
- Optional optical, radar, and physics inputs

### RGB Analysis

The RGB panel shows:

- Red, green, and blue histograms
- Mean and standard deviation for each channel
- Luminance values
- A combined RGB chart

### Batch Processing

Batch inference supports:

- Local folder scanning
- Modality filtering
- Sample limits
- Risk plot generation
- Visual grid export

### Research Insights

The insight panel displays:

- Debris confidence
- Collision risk
- Prediction uncertainty
- Evidence intensity

### Operational Verdict

The operational verdict summarizes the model output in operator-friendly language and adapts the tone using the selected operator profile.

## Starting the App

```bash
cd c:/Users/PREM DIWAN/Desktop/ml/unified-space-debris-detection
$env:USDD_PORT='7868'
python webapp/flask_app.py
```

Open the dashboard at [http://127.0.0.1:7868](http://127.0.0.1:7868).

## Common Usage

### Single Prediction

1. Choose image size, band, normalization, and operator profile.
2. Upload an optical or radar image.
3. Add a physics vector if needed.
4. Run prediction and review the summary, charts, and overlays.

### Batch Prediction

1. Enter a dataset folder path.
2. Choose modality and sample limit.
3. Run the batch.
4. Export the results if needed.

### Dataset Explorer

1. Enter a folder path.
2. Scan the folder.
3. Select an image.
4. Run inference on that selected file.

## Benchmarking

Retrain the benchmark models with:

```bash
python src/training/train_image_bench.py \
  --data_dir "c:/Users/PREM DIWAN/Desktop/ml/images" \
  --epochs 10 \
  --batch_size 16
```

The summary is saved to `artifacts/image_bench/image_bench_summary.json`.

## Preprocessing Notes

- Use RGB for natural images
- Use R or RB for infrared-like sensor behavior
- Start with camera threshold values between 0.1 and 0.4 for real imagery
- Use smaller image sizes for faster batch runs

## Troubleshooting

- If the dashboard does not start, run `python main_train.py` to create a checkpoint.
- If RGB analysis is blank, make sure an image was uploaded before prediction.
- If batch processing is slow, reduce the max sample count.
- If the Chart.js CDN is blocked, the page falls back to the local canvas renderer.

## Notes

- The dashboard is designed to work offline after the initial page load.
- The core model is a custom multimodal network, while the benchmark section compares pretrained backbones.
- Operator profiles change the operational tone and action wording without changing the underlying model weights.
