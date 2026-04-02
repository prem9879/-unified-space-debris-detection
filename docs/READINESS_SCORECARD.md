# Readiness Scorecard

This repository is organized around a target state of 9/10 across product, research, and operational dimensions.

## Evidence bundle

- immutable dataset manifest: `data/manifests/*.json`
- hard-negative index: `artifacts/reports/hard_negative_index.json`
- benchmark card: `artifacts/reports/benchmark_card.json`
- calibration report: `artifacts/reports/calibration_report_ci.json`
- SLO report: `artifacts/reports/slo_report.json`
- security policy: `artifacts/reports/security_policy.json`
- release readiness pack: `artifacts/reports/readiness_pack.json`

## Target scores

- scientific credibility: 9.0
- engineering reliability: 9.0
- security and governance readiness: 9.0
- deployment and operations maturity: 9.0
- product UX and demo impact: 9.0
- talent/recruitability signal: 9.0
- government/ministry adoption readiness: 9.0

## Passing conditions

1. Blind external evaluation exists and is reproducible.
2. Calibration gates pass at the policy operating point.
3. Reliability SLOs are within threshold.
4. Production profile uses managed identity or Key Vault only.
5. Rollback and incident response plans are documented.
