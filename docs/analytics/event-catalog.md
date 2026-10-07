# Analytics event catalog

Version: `analytics.v1-draft`  
Status: schema contract; collection is not enabled in Stage 1.

All production events require a server-generated `event_id`, UTC `occurred_at`, pseudonymous `account_id`, `schema_version` and `source`. Event ingestion is idempotent. Raw email, IP, audio filenames, track titles and payment credentials are forbidden event properties.

| Event | Source of truth | Required properties | Purpose |
|---|---|---|---|
| `account_registered` | Account service | `account_id`, `channel` | New-user cohort |
| `session_started` | Server session | `account_id`, `client`, `client_version` | Active/returning users |
| `trial_started` | Entitlement ledger | `account_id`, `trial_ends_at` | Trial funnel |
| `subscription_started` | Billing ledger | `account_id`, `subscription_id`, `price_type`, `amount_minor`, `currency` | First paid conversion |
| `subscription_renewed` | Billing ledger | `account_id`, `subscription_id`, `amount_minor`, `currency` | Renewed paid users |
| `subscription_cancelled` | Billing ledger | `account_id`, `subscription_id`, `effective_at`, `reason_code` | Pending churn |
| `subscription_expired` | Entitlement ledger | `account_id`, `subscription_id` | Real churn |
| `promo_redeemed` | Promo ledger | `account_id`, `promo_id`, `discount_type` | Discount attribution |
| `referral_qualified` | Referral ledger | `referrer_id`, `referred_account_id`, `qualification_version` | Referral reward |
| `track_upload_completed` | Upload service | `account_id`, `upload_id`, `duration_bucket` | Library adoption |
| `replacement_started` | Client + server validation | `account_id`, `service`, `mapping_id`, `client_version` | Playback adoption |
| `replacement_restored` | Client | `account_id`, `reason_code`, `client_version` | Fail-open health |

Client events are telemetry, never billing truth. Revenue, paid conversion, renewal, discount and churn are calculated from billing/entitlement ledgers. Retention periods and deletion behaviour must be approved before collection is enabled.
