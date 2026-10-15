# OpenBao API secret integration

Source authority: [Codestra-OpenBao](https://github.com/appolon1908-hue/Codestra-OpenBao).
The machine-readable contract is `openbao-secret-consumer.v1.json`.
This change prepares file-based credential consumption; runtime binding is unverified.

For each admitted process, render its bundle in Codestra-OpenBao using
`scripts/render_application_secrets.py`. The default selection contains required
startup bindings; add `--include SETTING_NAME` only for an enabled integration.
Run the agent as the same non-root UID/GID as its consumer. Use private directories
on a memory-backed volume and read-only mounts in the application container.
The agent writes mode 0400, with no backup copy or token sink. Consumers accept
0400 or 0600 private regular files owned by the runtime user; links, directories,
pipes, empty/oversized/invalid files and conflicting inline credentials are rejected.
Remove the matching inline environment setting when supplying its `_FILE` setting.
A configured file failing to load stops configuration; it never falls back to an
inline value. Local development without a file retains existing configuration behavior.

The agent reads KV-v2 records with a string `payload` field. The logical namespace
below maps to `/v1/codestra/data/<environment>/...` in the private native API.
No provider credentials belong in browser variables, images, Git or logs.
OpenBao bootstrap/unseal keys and user/customer records are outside this contract.

Settings are loaded at process startup. After Agent renders a rotated value,
restart the affected consumer under the rollout supervisor, verify provider access,
and revoke the old credential only after successful cutover. Static KV refresh is
not provider-key rotation. A reader observing a new file does not prove that an
already-running SDK client has reloaded it. Never dump settings or error `.errors()`
payloads; Pydantic error formatting and secret-field repr are redacted here, but
application-specific diagnostic serialization still requires care.

## moneybee-api

Logical prefix: `codestra/<environment>/moneybee/api/runtime/`.

| Setting | File reference | Startup required |
| --- | --- | --- |
| `DATABASE_URL` | `DATABASE_URL_FILE` | Yes |
| `REDIS_URL` | `REDIS_URL_FILE` | Yes |
| `CODESTRA_MIDDLEWARE_CLIENT_SECRET` | `CODESTRA_MIDDLEWARE_CLIENT_SECRET_FILE` | When integration requires it |
| `CODESTRA_MIDDLEWARE_WEBHOOK_SECRET` | `CODESTRA_MIDDLEWARE_WEBHOOK_SECRET_FILE` | When integration requires it |
| `PROVIDER_WEBHOOK_SECRETS_JSON` | `PROVIDER_WEBHOOK_SECRETS_JSON_FILE` | When integration requires it |
| `FIELD_ENCRYPTION_KEYS_JSON` | `FIELD_ENCRYPTION_KEYS_JSON_FILE` | When integration requires it |
| `PLAID_SECRET` | `PLAID_SECRET_FILE` | When integration requires it |
| `CRM_API_KEY` | `CRM_API_KEY_FILE` | When integration requires it |
| `ODOO_API_KEY` | `ODOO_API_KEY_FILE` | When integration requires it |
| `KYB_API_KEY` | `KYB_API_KEY_FILE` | When integration requires it |
| `MIDDESK_API_KEY` | `MIDDESK_API_KEY_FILE` | When integration requires it |
| `MIDDESK_WEBHOOK_SECRET` | `MIDDESK_WEBHOOK_SECRET_FILE` | When integration requires it |
| `CREDIT_API_KEY` | `CREDIT_API_KEY_FILE` | When integration requires it |
| `EXPERIAN_CLIENT_SECRET` | `EXPERIAN_CLIENT_SECRET_FILE` | When integration requires it |
| `LENDER_API_KEY` | `LENDER_API_KEY_FILE` | When integration requires it |
| `SENDGRID_API_KEY` | `SENDGRID_API_KEY_FILE` | When integration requires it |
| `TWILIO_AUTH_TOKEN` | `TWILIO_AUTH_TOKEN_FILE` | When integration requires it |
| `OBJECT_STORAGE_ACCESS_KEY` | `OBJECT_STORAGE_ACCESS_KEY_FILE` | When integration requires it |
| `OBJECT_STORAGE_SECRET_KEY` | `OBJECT_STORAGE_SECRET_KEY_FILE` | When integration requires it |
| `STRIPE_SECRET_KEY` | `STRIPE_SECRET_KEY_FILE` | When integration requires it |
| `STRIPE_WEBHOOK_SECRET` | `STRIPE_WEBHOOK_SECRET_FILE` | When integration requires it |
| `PAYPAL_CLIENT_SECRET` | `PAYPAL_CLIENT_SECRET_FILE` | When integration requires it |

DocuSign access tokens are ephemeral OAuth credentials. They are not added to durable KV storage; token refresh must be integrated separately.
