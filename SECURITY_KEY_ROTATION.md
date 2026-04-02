# API Key Rotation Policy

This project supports API key rotation using key rings loaded from environment or Azure Key Vault.

## Key Ring Schema

Provide JSON payload in `USDD_API_KEYRING_JSON` or in the Azure Key Vault secret configured by:

- `USDD_KEYVAULT_URL`
- `USDD_KEYVAULT_SECRET_NAME`

Example payload:

```json
{
  "keys": [
    {"id": "k-2026-04", "key": "viewer_key_value", "role": "viewer", "status": "active"},
    {"id": "k-2026-03", "key": "old_analyst_key", "role": "analyst", "status": "grace"}
  ],
  "rotation": {
    "interval_days": 30,
    "overlap_days": 7
  }
}
```

## Status Semantics

- `active`: primary keys accepted.
- `grace`: temporary overlap keys accepted during rotation windows.
- `retired`: rejected keys.

## Rotation Procedure

1. Create a new key and add it as `active`.
2. Mark previous key as `grace` for overlap period.
3. Redeploy/reload services and distribute new key.
4. Remove grace key after overlap period by marking it `retired` or deleting it.
5. Verify with admin endpoint `GET /security_policy`.

## Operational Recommendations

- Rotate keys at least every 30 days.
- Keep overlap period short (for example 7 days).
- Use Azure Managed Identity + Key Vault in production.
- Never hardcode key values in source files.
- Store audit logs securely and monitor auth failures.
