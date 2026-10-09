# CELIKOM Stage 9 — guarded user auth rollout

**10 October 2026.** Development branch `feature/api-range`, release `0.4.5-43bf308f1514881dbe996e7e08650d6e74214cdf`. PR #6 OPEN, Issue #7 OPEN. Stage 8 accepted, no Stage 10 work.

## Implemented boundaries

- Customer identity is not admin identity: `server/src/Auth/*` and `users/user_devices/user_sessions` are isolated from `admins/admin_sessions`. All user auth endpoints are under `/api/v1/auth/` and default 404 while `FEATURE_USER_AUTH=0`.
- `register`, `login`, `refresh`, `logout`, `me`, `sessions`, `sessions/revoke`, `activate`. Customer passwords via PHP strong password KDF; 256-bit CSPRNG opaque tokens, SHA-256 hashes only in MySQL, 15-minute access sessions and 30-day rolling refresh. Previous-token reuse revokes affected session; repeated login throttled per email hash and IP hash; session access denied for disabled/restricted users.
- Chrome 0.4.5 generates v4 `installation_id`, stored independently of musical-service identity. Refresh/access credentials are in extension-origin IndexedDB controlled by background service worker (never page/content scripts), separate from existing private owner API access. Settings/player, owner upload and original 0.4.4 extension remain compatible.
- Admin overview uses actual account creation, first activation and distinct authenticated `celikom_started` events; returning users require earlier authenticated start. Anonymous installations are not fingerprint-merged.

## Automated evidence

| Gate | Evidence | Status |
|---|---|---|
| Server + client CI against disposable MySQL/Chrome fixtures | [CI](https://github.com/manufact-test/nomusic/actions/runs/38001081205) | PASS |
| Private Chrome 0.4.5 ZIP + SHA-256 | [Chrome package](https://github.com/manufact-test/nomusic/actions/runs/38000772154) | PASS |
| Pre-deploy snapshot: 16 tables and 5 audio objects | [Snapshot](https://github.com/manufact-test/nomusic/actions/runs/38000819463) | PASS |
| Pre-deploy restore in disposable DB, isolated file recovery | [Restore](https://github.com/manufact-test/nomusic/actions/runs/38000923973) | PASS |
| Immutable CI-gated deploy | [Hostinger deploy](https://github.com/manufact-test/nomusic/actions/runs/38001076778) | PASS |
| Live read-only audit after migration; approved and pending retained | [Audit](https://github.com/manufact-test/nomusic/actions/runs/38001265857) | PASS |
| Post-deploy private backup: 21 tables and 5 audio objects | [Snapshot](https://github.com/manufact-test/nomusic/actions/runs/38001376977) | PASS |
| Post-deploy SQL and files isolated restore | [Restore](https://github.com/manufact-test/nomusic/actions/runs/38001474957) | PASS |

Server runtime: PHP 8.3 HTTPS; target `https://darkred-camel-588676.hostingersite.com`. Owner-only upload token and all existing private flags preserved. `FEATURE_USER_AUTH` defaults OFF. Never place credentials, customer email lists or token values in public source, artifacts, GH logs or reports.

## Protected invariants

- Yandex Track `144530503`: Replacement #1 **approved and active**; original file hash and duration remain unchanged.
- Track `38436680`: Replacement #3 **pending**, no admin decision.
- Track `799133075`: Replacement #2 synthetic **pending**, no admin decision.
- Public `FEATURE_UPLOADS` stays OFF; private owner upload state unchanged. Existing owner Chrome extension 0.4.4 is not overwritten.
- No merge of PR #6. Issue #7 and unresolved two-independent-Chrome-profile Stage 6.7 gate remain open.

## Next controlled test (Stage 9 only)

1. Review live auth threat model, especially unverified email ownership and account recovery before opening registration to public traffic. Do not enable auth solely because the migration is present.
2. Enable `FEATURE_USER_AUTH=1` through a separate approved, reversible Hostinger private-env operation only after gate; preserve every other flag and backup private `shared/env`.
3. With a dedicated closed-test Chrome 0.4.5 installation, test register/login, refresh after expiry, logout and session revoke for two independent browser profiles. Do not replace the owner's existing working extension.
4. Review email/login UX and status-change audit event handling before **formally accepting** Stage 9.
5. If auth activation fails, revert only the new private auth flag, avoid destructive MySQL rollback. 004 is additive and old code ignores the new tables. The previous 0.4.4 server release is still available for code-only rollback. Retain 21-table snapshot for full restoration if required.

**Not Stage 9:** Trial/EntitlementService, recurring billing, public uploads, and the required separate public song suggestion button belong to Stage 10 or later. Specifically `Предложить песню` uses automatically detected exact Track ID and does NOT request MP3 or rights declaration; Stage 8 admin queue already exists.
