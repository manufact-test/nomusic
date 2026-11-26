# W187 — W173 0.24.54 login failure after rollback; restore Floki API compatibility without changing audio baseline

Date: 26 November 2026

## Current owner result

The owner installed the exact historical W173 **CELIKOM Windows 0.24.54** package recovered from artifact `14703029534` (run `44894407351`). The application opens and displays version 0.24.54, but signing in fails with the generic UI message:

`Не удалось выполнить действие. Проверь интернет и повтори.`

Screenshot supplied 26.11.2026. There is no successful login and no new playback test. Therefore **the rollback has NOT restored a working product**. Do not describe 0.24.54 as currently working on the owner's machine merely because this was the last personally accepted source baseline.

## Correction to W186 — the previous rollback instruction was wrong for the migrated service

W186 instructed the owner to uninstall CELIKOM and select **«Также удалить сохранённые данные входа»**. If that step was followed, the uninstaller removed `%LOCALAPPDATA%\CELIKOM\Windows\session.dpapi`, forcing W173 0.24.54 to create a blank session.

That historical build has the old Hostinger origin as its default:

- `windows-companion/w15/Celikom.Companion/MainWindow.cs` at W174: `DefaultApiOrigin = "https://darkred-camel-588676.hostingersite.com"`.
- `windows-companion/w15/Celikom.Companion/CelikomApi.cs` at W174: a new blank `SessionStore` has an empty Origin; there is no constructor migration to Floki.
- W174 password-reset and config fallbacks also point to the old Hostinger origin.

Thus the prescribed data wipe likely sent the new login attempt to the legacy Hostinger API rather than the migrated Floki API at `https://api.celikom.com`. This is the leading explanation, **not yet a proven request-level diagnosis**: the screenshot does not expose the selected origin, HTTP status, response body or transport exception.

The W186 Hostinger monitor run `45759107905` only checked GET health/config (200) and anonymous resolve (401). It did **not** verify owner login, POST `/api/v1/auth/login`, the owner account, or an authenticated grant. A green health check is not evidence that login works.

The generic UI error is not diagnostic. W174 `MainWindow.LoginAsync` catches broad exceptions and collapses them into the same message; it does not show the actual origin, status code or transport category. Do not infer that the owner's password is wrong.

## Verified reference implementation already exists on current main

Current main contains the narrowly scoped Floki origin migration that was added after W174:

- `CelikomApi.ProductionOrigin = "https://api.celikom.com"`.
- `LegacyProductionOrigin` is the exact former Hostinger authority.
- `MigrateProductionOrigin(SecretRecord)` changes only that exact legacy origin to Floki. It leaves unrelated custom/test origins untouched.
- The constructor migrates and persists the encrypted DPAPI session while preserving installation ID, email, access token, refresh token and bridge token.
- `MainWindow.DefaultApiOrigin` uses `CelikomApi.ProductionOrigin`.
- Password-reset, reset-password and config fallbacks use `ProductionOrigin`.

Current main's `Celikom.Companion.Tests/Program.cs` contains migration contracts around lines 1855–1876: exact legacy mapping, preservation of tokens/account/device, persistence, idempotence, and rejection of unrelated/lookalike origins.

The `LoginAsync` request contract in W174 and current main remains the same: POST `/api/v1/auth/login` with email, password and installation_id; it expects access_token, refresh_token and user.email. The Floki server's `AuthController` exposes this same POST route. Do not rewrite the authentication protocol without new evidence.

Existing Floki read-only audit `45813153575` documented health/config 200, admin login page 200, and anonymous auth/me and resolve 401. It used no credentials. It does not prove a successful owner login.

## Correct recovery target

**Keep the W174 audio/runtime baseline; backport only the API-origin compatibility.**

Recovery branch already created:

- Branch: `recovery/windows-w174-02454-known-good-20261126`
- Exact base commit: `aa713b99824f20abbe7c239bf06e356cf3f7f367`
- This is the W174 canonical promotion of the owner-accepted W173 0.24.54 code.
- Do not use current main as the source baseline for the audio/runtime candidate.

The following W174 audio integration blobs are the protected known-good baseline and must remain byte-identical during the API compatibility repair:

| File | W174 blob SHA |
|---|---|
| `windows-companion/w23/renderer-entry.mjs` | `203b098914d549bc8d21b682b62df6486025cefa` |
| `windows-companion/w22/native-resource-adapter.mjs` | `e3bfdc3ed579709c342c3ae87e2e83510e35826e` |
| `windows-companion/w60/current-source-refresh.mjs` | `a5814bee52a8698ab79f9f4861f1b1451d85ee09` |

Do not bring in W182/W183/W185/W186 audio-hook or player-source changes. The accepted W174 discovery path must be preserved exactly.

## Work order for the next chat

1. Read this document, `docs/windows/NEXT-CHAT.md`, W186 and W174 before editing.
2. Verify branch `recovery/windows-w174-02454-known-good-20261126` still points to the exact W174 base and inspect its current status. Keep `main` and customer stable untouched.
3. On that recovery branch, make a **minimal API-only backport** from current main:
   - add the exact `ProductionOrigin`, `LegacyProductionOrigin` and `MigrateProductionOrigin` implementation;
   - migrate/persist only the exact old Hostinger origin in the constructor, without losing the existing account/device tokens;
   - change the blank-session default in `MainWindow.cs` to Floki;
   - change password-reset/reset-password/config empty-origin fallbacks to Floki;
   - port the exact migration tests from current main, adapted to the W174 test file.
4. Add privacy-safe login diagnostics. Record only an allowlisted target class (Floki vs legacy/custom) and outcome class (transport failure, timeout, HTTP status/error category, invalid JSON, success). Never log email, password, Authorization, access/refresh/bridge tokens, request/response bodies, or full URLs. Keep the existing generic UI copy if necessary, but make the diagnostic useful.
5. Verify the Floki endpoint with no owner credentials: health/config, anonymous auth/me (expected 401), and a safe route/method-shape check for auth/login. Do not send the owner's password from CI, tools, scripts, or chat. Do not attempt repeated production login requests.
6. Run W15 .NET contracts, including the exact origin-migration tests; W20 installer checks; W21/W22/W23/W24 regressions; renderer/native tests; and the Windows Floki cross-build. Confirm the three protected audio blobs above are unchanged from W174.
7. Package one owner-only candidate from the recovery branch using the current verified delivery/signing path. Determine the next version/sequence from the live release metadata; do not guess. Verify exact EXE/ZIP hashes and owner HTTPS receipt.
8. Owner test sequence, once the candidate is delivered:
   - install in place over 0.24.54; do not uninstall and do not clear DPAPI;
   - confirm login reaches the CELIKOM account page on Floki;
   - then test the known mapped track 144530503 («Ау») and confirm actual substituted sound;
   - separately test an unmapped/original track, Next and Play/Pause.
9. If login succeeds but audio replacement still fails, treat that as a separate W174 playback regression and request fresh diagnostics from the candidate. Do not mix an auth failure with an audio-hook failure.

## Hard stop / owner data protection

- **Do not ask the owner to uninstall again or delete `session.dpapi`.**
- Do not ask for, copy, inspect or place the owner's password/tokens in repository files, workflow inputs, Actions logs or chat.
- Do not alter live Floki/Hostinger server code, database, mail, account, trial, subscription, catalog, grants or feature flags in this task.
- Do not change Android or browser extension.
- Do not publish customer stable, promote auto-update, or mass-release this owner candidate.
- Do not change W174 audio code while solving API origin/login.
- Do not call the rollback successful until the owner confirms both login and actual audible replacement.

## Honest current status

- Exact historical W173 0.24.54 artifact: recovered and SHA-256 verified.
- 0.24.54 application launch: owner screenshot confirms.
- 0.24.54 login: **FAILED in owner test**; precise endpoint/reason not yet confirmed.
- 0.24.54 audio replacement after rollback: **NOT TESTED**.
- Recovery branch: created at exact W174 commit.
- Runtime code changes in this W187 documentation update: **none**.
- Next deliverable: owner-only recovery candidate = W174 audio baseline + minimal Floki API-origin migration + safe login diagnostics.
