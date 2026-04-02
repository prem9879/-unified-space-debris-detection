# Security Architecture Brief

## Identity and secrets

- managed identity preferred in production profile
- key ring from Azure Key Vault or env-json
- no static fallback in production security profile

## Access control

- role model: viewer, analyst, admin
- role-based rate limits
- invalid-key lockout and anomaly throttling

## Audit

- signed append-only JSON lines
- retention pruning policy
- weekly role policy review report
