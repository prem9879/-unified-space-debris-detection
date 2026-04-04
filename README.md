# Unified Space Debris Intelligence & Collision Prediction System

Unified multi-modal space debris intelligence platform for real-world orbital safety workflows.

This repository started as a debris detector and grew into a collision-intelligence system. The current version is intentionally hybrid: physics does the first-pass filtering, ML does the nuanced ranking, and the UI focuses on operator clarity instead of model hype.

This project combines a research-grade dashboard with a practical training, inference, and orbital-risk pipeline. It helps you ingest TLE and imagery data, engineer physically meaningful orbital features, run live and batch predictions, inspect model evidence, and package release-readiness artifacts for review.

What this is: a serious build for demos, papers, and productization.
What this is not: a toy notebook with a single accuracy score.

## What this project does

- Ingests TLE catalogs from CelesTrak / Space-Track and local imagery folders.
- Engineers orbital features such as altitude, inclination, perigee, apogee, cyclic angles, drag proxy, and shell density.
- Runs a multimodal inference pipeline for debris detection, collision risk, and trajectory reasoning.
- Shows risk surfaces, evidence heatmaps, bounding overlays, and activation views.
- Compares multiple CNN and orbital baselines in a benchmark table.
- Reports calibration metrics like ECE, Brier score, NLL, and reliability bins.
- Supports batch dataset inference and PNG / CSV / JSON exports.
- Provides an RGB analysis panel with histograms and channel statistics.
- Includes personalized operator profiles for balanced, conservative, and exploratory decision styles.
- Exposes a custom multimodal debris model with radar, optical, physics, and orbital encoders.

## Model zoo

The benchmark currently trains and compares these backbones:

1. ResNet18
2. ResNet34
3. DenseNet121
4. EfficientNet B0
5. EfficientNet B1
6. MobileNet V3 Small
7. ShuffleNet V2 X1.0
8. ConvNeXt Tiny

## Main UI features

- Live inference form with optical, radar, and physics inputs
- Operator profile selector that adapts the decision policy and action wording
- Dynamic RGB analysis with selectable view and normalization modes
- Class probability chart and export button
- Batch visual grid with overlay thumbnails
- Model benchmark chart and summary table
- Reliability / calibration report panel
- NASA ODPO public data loader

## How the pipeline works

1. Ingest TLE and image data, then normalize object metadata into one canonical catalog.
2. Engineer orbital features such as altitude, shell distance, inclination risk, and cyclic orbital encodings.
3. Feed time-series and orbital features into sequence models, while CNN and tree baselines handle fast classification and imagery.
4. Compute physics-grounded collision priors and combine them with learned scores.
5. Generate heatmaps, overlays, orbit-shell summaries, and layer activation visuals.
6. Attach a decision basis with uncertainty band, operator profile, and explanation.
7. Convert the raw outputs into a personalized operational verdict and exportable research packet.

## Local setup

```bash
pip install -r requirements.txt
```

Supported runtime for production and CI: `Python 3.11.x`.

### Run the dashboard

```bash
cd webapp
$env:USDD_PORT='7868'
python flask_app.py
```

### Production-style run (WSGI)

```bash
$env:USDD_PORT='7868'
gunicorn --workers 2 --threads 4 --bind 0.0.0.0:$env:USDD_PORT webapp.flask_app:app
```

### Health and readiness probes

- `GET /healthz` - liveness probe (lightweight, no model load required)
- `GET /readyz` - readiness probe (checkpoint + model service init)

### Security controls for external use

Environment flags:

- `USDD_REQUIRE_AUTH=1` enables API-key authentication on non-public endpoints.
- `USDD_API_KEYS` accepts JSON map of key to role, for example:
  `{"viewer-key":"viewer","analyst-key":"analyst","admin-key":"admin"}`
- `USDD_API_KEYRING_JSON` accepts key-ring JSON with active/grace/retired status and rotation metadata.
- `USDD_KEYVAULT_URL` and `USDD_KEYVAULT_SECRET_NAME` enable Azure Key Vault secret loading.
- `USDD_RATE_LIMIT_PER_MIN=180` sets per-identity rate limit window.
- `USDD_AUDIT_LOG_ENABLED=1` enables structured request audit logging.
- `USDD_AUDIT_LOG_PATH=logs/audit.log` controls audit log output path.

Role model:

- `viewer`: read-only, low-risk endpoints.
- `analyst`: inference and calibration endpoints.
- `admin`: data-loading administrative endpoints.

Open:

```text
http://127.0.0.1:7868
```

### Train the benchmark

```bash
python src/training/train_image_bench.py --data_dir "c:/Users/PREM DIWAN/Desktop/ml/images" --epochs 2 --batch_size 16
```

### Build immutable dataset manifest (real labeled data)

```bash
python scripts/build_dataset_manifest.py --dataset_root "c:/path/to/real_debris_dataset" --dataset_name "debris_ops" --dataset_version "v1" --manifest_path "data/manifests/debris_ops_v1.json" --split_seed 42
```

Then train with locked immutable splits:

```bash
python src/training/train_image_bench.py --data_dir "c:/path/to/real_debris_dataset" --dataset_manifest "data/manifests/debris_ops_v1.json" --epochs 6 --batch_size 16
```

### Run browser UI smoke tests

```bash
npm install
npx playwright install chromium
npm run test:ui
```

### Generate calibration and evaluation artifact reports

```bash
python scripts/generate_ci_reports.py
```

Outputs:

- `artifacts/reports/calibration_report_ci.json`
- `artifacts/reports/eval_report_ci.json`

### Build hard-negative/OOD index

```bash
python scripts/build_hard_negative_index.py --dataset_root "c:/path/to/real_debris_dataset" --output "artifacts/reports/hard_negative_index.json"
```

### Publish locked benchmark card

```bash
python scripts/publish_benchmark_card.py --manifest "data/manifests/debris_ops_v1.json" --benchmark "artifacts/image_bench/image_bench_summary.json" --calibration "artifacts/reports/calibration_report_ci.json" --output "artifacts/reports/benchmark_card.json"
```

### Generate reliability SLO report

```bash
python scripts/generate_slo_report.py
```

### Generate release readiness pack

```bash
python scripts/generate_readiness_pack.py
```

### Production security profile

Set `USDD_SECURITY_PROFILE=production` to disable legacy static key fallback and enforce secret-vault/keyring-only auth material.

## Key API endpoints

- `GET /` - dashboard home
- `POST /predict` - inference from uploaded inputs
- `POST /predict_file` - inference from a local file path
- `POST /predict_dataset` - batch inference on a folder
- `POST /calibration_report` - reliability / calibration metrics
- `GET /model_benchmark` - benchmark summary
- `GET /options` - supported bands, sizes, and layer names

## Project structure

- `src/` - data, preprocessing, training, inference, and evaluation code
- `webapp/` - Flask dashboard, templates, and static assets
- `artifacts/` - saved checkpoints and benchmark summaries
- `data/` - downloaded and generated datasets
- `configs/` - configuration files
- `tests/` - test coverage

## Notes

- The benchmark currently uses synthetic and locally bootstrapped data.
- Calibration and uncertainty reporting are included to support transparent model evaluation.
- The live decision policy can be tuned per operator profile without changing the underlying model.
- For real-world deployment, the next step is a labeled debris dataset and calibrated threshold tuning.

## Research documentation

- Full paper draft scaffold: `PAPER.md`
- Reproducible split policy: `SPLIT_PROTOCOL.md`
- Key rotation policy: `SECURITY_KEY_ROTATION.md`
- Decision support doctrine: `docs/DECISION_SUPPORT_DOCTRINE.md`
- Safety case: `docs/SAFETY_CASE.md`
- Validation report template: `docs/VALIDATION_REPORT_TEMPLATE.md`
- Rollback plan: `docs/ROLLBACK_PLAN.md`
- Security architecture brief: `docs/SECURITY_ARCHITECTURE_BRIEF.md`
- Uptime and incident response: `docs/UPTIME_INCIDENT_RESPONSE.md`
- Procurement dossier checklist: `docs/PROCUREMENT_DOSSIER.md`
- Product and research brief: `docs/SPACE_DEBRIS_PRODUCT_BRIEF.md`
- External blind eval protocol: `external_validation/BLIND_EVAL_PROTOCOL.md`
- Readiness scorecard: `docs/READINESS_SCORECARD.md`

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
