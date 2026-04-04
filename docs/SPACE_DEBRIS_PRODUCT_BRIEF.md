# Unified Space Debris Intelligence & Collision Prediction System

This is the working design brief for the system in this repository. It is written as a build document, not a textbook note.

## 1. Full System Architecture

### A. Data Sources
- CelesTrak TLE feeds for live catalog updates.
- Space-Track for authenticated orbital records when available.
- Local optical or radar imagery for debris detection and evidence overlays.
- Project artifacts and evaluation outputs for calibration, benchmarking, and reporting.

### B. End-to-End Pipeline
1. Ingest orbital and image data through scheduled pulls or API calls.
2. Parse TLE lines into orbital state fields like inclination, RAAN, eccentricity, and mean motion.
3. Engineer orbital features: altitude, semi-major axis, perigee, apogee, orbital velocity, drag proxy, shell distance, and cyclic angle encodings.
4. Shortlist conjunction candidates with orbital-shell screening before heavy scoring.
5. Run learned models for trajectory prediction and image-based debris detection.
6. Fuse physics-derived priors with AI probabilities into one risk score.
7. Emit alert bands: low, medium, high.
8. Render the current orbital scene and alert queue in the dashboard.
9. Export calibration, benchmark, and readiness artifacts for research or deployment.

### C. Why this structure matters
The first version of this kind of project usually fails because everything is treated as one big ML problem. That does not scale. We split it into screening, prediction, fusion, and presentation because each layer has a different failure mode.
- Screening keeps the pairwise search tractable.
- Prediction keeps temporal structure.
- Fusion keeps the final decision defensible.
- Presentation keeps operators from drowning in raw probabilities.

## 2. Model Explanations

### LSTM / GRU
- Best for trajectory forecasting on orbital sequences when data is limited.
- Useful for short-to-medium horizon propagation.
- Trade-off: weaker long-range dependency modeling and can flatten regime changes.

### Transformer
- Best for long sequence context and repeated orbital patterns.
- Useful when the task needs global attention over time.
- Trade-off: heavier compute and more sensitive to sparse data.

### Random Forest / XGBoost
- Best for strong tabular baselines on engineered orbital features.
- Useful as a calibration anchor when neural predictions look overconfident.
- Trade-off: no true sequence memory.

### CNN / YOLO
- Best for optical or radar imagery when debris signatures are visually separable.
- Useful for detection, localization, and evidence overlays.
- Trade-off: does not solve orbital propagation by itself.

### Practical choice
We do not rely on one model. We use the simplest model that can defend a part of the problem, then combine them. That is more honest operationally and easier to publish.

## 3. Collision Prediction Engine

### Core logic
- Physics gate first: shell proximity, inclination neighborhood, and relative motion narrow the candidate set.
- AI second: learned sequence and classification models rank the remaining candidates.
- Final fusion: the system produces a probability plus a coarse operational band.

### Intuition
The physics stage is the fast filter. It is cheap and stable.
The AI stage is the nuanced scorer. It can learn patterns humans miss.
The final score is a compromise, not a purity contest.

### Risk scoring
- Low: the object is tracked, stable, and not in a dense shell.
- Medium: the object is close enough to deserve attention.
- High: geometry, velocity, and learned risk all point in the same direction.

### Real-world trade-off
We tested the idea of jumping straight to a learned pairwise classifier. It looked neat on paper, but it was too fragile when the catalog had missing or noisy TLE fields. The physics gate fixed that quickly.

## 4. Real-Time System

### Live tracking pipeline
- Scheduled TLE pulls or API-driven ingestion.
- Incremental catalog refresh.
- Event buffer for alerts and state changes.
- Continuous re-scoring on new orbital snapshots.

### Streaming architecture
- Flask today for fast integration with the existing repository.
- Redis or Kafka as the live queue if the system is scaled further.
- Worker pattern for ingestion, screening, and scoring.

### Operational principle
The dashboard should never block on a full catalog recompute if a smaller screened update is enough. That was one of the first scalability lessons.

## 5. 3D Visualization System

### What it shows
- Earth sphere.
- Orbit shells.
- Debris points.
- Risk-colored tracks.
- Alert queue.

### Interaction design
- Rotate and zoom the scene.
- Click an object to inspect risk.
- Use glow and shell separation so the scene reads cleanly.

### Implementation note
A Three.js layer is the right design target. The current repo also keeps a safe fallback path so the UI does not become unusable if a browser blocks the WebGL path.

## 6. UI / UX Structure

### Visual direction
- Dark space background.
- Cyan and blue glow accents.
- High-contrast alert states.
- Glass-like cards with depth.

### Screens
1. Dashboard
- Status cards, live feed, operational summary.

2. 3D visualization
- Orbit shells, Earth, debris, and object labels.

3. Collision alert panel
- High-risk objects, recommended action, and risk band.

4. Analytics page
- Benchmarks, calibration, and model comparison.

### Component breakdown
- Mission hero.
- Architecture timeline.
- Model stack panel.
- Deployment stack panel.
- Collision alert rail.
- Three.js orbital scene.
- Benchmark and calibration charts.

### Micro-interactions
- Hover lift on cards.
- Slow orbital motion in the 3D deck.
- Smooth panel switching.
- Soft glow changes on risk bands.

### Typography
- `Space Grotesk` for headings.
- `Source Sans 3` for body text.
- The point is not novelty for its own sake. The type choices are there to keep the interface sharp without becoming theatrical.

## 7. Deployment Architecture

### Backend
- Flask in the current repo.
- FastAPI is the natural next step if async endpoints or stricter schema contracts become necessary.

### Frontend
- Flask-rendered dashboard now.
- React / Next.js is the clean path for a richer startup-grade product.

### Database
- PostgreSQL for orbital catalog, audit, and operational records.
- Redis for live queues and cached snapshots.
- MongoDB only if the team prefers document-first experimentation.

### Cloud
- AWS or GCP both work.
- GPU workers handle inference.
- CPU workers handle ingestion and alert routing.
- Object storage keeps artifacts and scene snapshots.

### API structure
- `/healthz`
- `/readyz`
- `/options`
- `/predict`
- `/predict_dataset`
- `/calibration_report`
- `/orbital_brief`
- `/orbital_scene`

## 8. Research Paper Edge

### Unique contribution
A physics-gated multimodal collision intelligence system that combines orbital screening, learned sequence modeling, and explainable risk bands in one pipeline.

### Paper title ideas
- Unified Space Debris Intelligence for Physics-Gated Collision Prediction
- Multimodal Orbital Risk Fusion for Real-Time Space Safety
- From TLE Streams to Conjunction Alerts: A Research-Grade Operational Pipeline

### Evaluation metrics
- AUC-ROC
- PR-AUC
- ECE
- Brier score
- Orbit RMSE
- Alert lead time
- False alert rate
- Calibration stability

### Comparison baseline
- Pure SGP4 or physics-only propagation: fast but not decision-aware.
- Pure deep learning: flexible but brittle.
- This system: hybrid, auditable, and deployable.

## 9. What Makes This Project Unique
- It does not force ML to do physics' job.
- It does not force physics to do the operator's job.
- It gives each layer a precise role.
- It packages the result as a usable product, not only a model.
- It is easier to explain in a paper, easier to demo in a hackathon, and easier to defend in front of an investor or university panel.

## 10. Suggestions to Push It Beyond 10/10
1. Add a real Three.js client with object picking and orbit trails.
2. Plug in a streaming broker like Kafka or Redis Streams.
3. Store orbital catalogs and alerts in PostgreSQL with historical diffs.
4. Build a calibration explorer for threshold tuning by orbit shell.
5. Add a sensor-fusion ingestion page for radar and optical observations.
6. Add a lock-step evaluation harness for TLE drift, false alerts, and lead-time metrics.
7. Add a FastAPI service layer for external clients and startup integrations.

## 11. Honest Engineering Notes
- A flashy model stack alone is not enough. If the pairwise search explodes, the demo dies.
- A beautiful 3D view is not enough if the risk score cannot be justified.
- A clean dashboard is not enough if the catalog update path is not stable.
- The practical win is the combination of screening, modeling, and clear operator UX.

This repo now reflects that direction.
