# External Blind Evaluation Protocol

## Purpose

Independent third-party validation package for blind performance assessment.

## Package Contents

- immutable dataset manifest and split digest
- benchmark card (`artifacts/reports/benchmark_card.json`)
- model checkpoint hash metadata
- prediction submission template (`external_validation/submission_template.csv`)

## Blind Procedure

1. Third party owns test labels and does not share them.
2. Participant receives only blind test IDs and inputs.
3. Participant submits predictions using fixed schema.
4. Third party computes final metrics and confidence intervals.
5. Results are signed and published with dataset digest and model version.

## Required Metrics

- accuracy + 95% CI
- precision, recall, F1
- false alarm rate
- calibration ECE and Brier score
- cost-weighted false positive/false negative impact

## Integrity Constraints

- no test-set threshold tuning
- no post-hoc relabeling
- all submissions tied to commit hash and manifest digest
