# CELIKOM Android A1 — NAV12 final handoff (14 Nov 2026)

## Repository state

- Repository: `manufact-test/nomusic`
- Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- Source snapshot before this documentation commit: `d397a34cb25561dc65ae22afa4c15781f59a2b00`
- Pre-NAV12 exact rollback: `backup/android-a1-nav12-pre-onboarding-writer-trace-20261114` @ `00f9e4485a2814aa81ed9b089fc40c83e02d96f8`
- Earlier stable source checkpoints: `backup/android-a1-nav9-pre-token-callback-witness-20261114` @ `50fc7ca`; `backup/android-a1-nav10-pre-master-token-crypto-status-20261114` @ `a0410c5`; `backup/android-a1-nav10-postlogin-crypto-witness-before-key-init-20261114` @ `a0a4565`; `backup/android-a1-nav11-key-order-before-native-event-gate-20261114` @ `9c141f5`.

## What the last pass accomplished

### 1. Fresh-install Passport key order — runtime proven, not owner-login proven

The independently signed CELIKOM clone uses the original 2025.10.4 Passport AES master-token path. The vendor's own `v.try()` generates and persists `yandex_am_storage/master_token_key`; the key is cached through `LY7a`. NAV11 invokes this original SDK method in clone MAIN before Passport starts **only when both the clone-owned AccountManager account and key are absent**. It never rotates an existing key or touches an existing account.

Strict native Android13 reports confirmed `master_key_init_runtime_status=ORIGINAL_KEY_PERSISTED` in BOTH:
- [#43574754576 — clone alone](https://github.com/manufact-test/nomusic/actions/runs/43574754576), SUCCESS
- [#43574754550 — original publisher installed first, then CELIKOM](https://github.com/manufact-test/nomusic/actions/runs/43574754550), SUCCESS

This proves the vendor's own key-generation method persisted the key on fresh Android13 in both layouts. It does **not** prove an OTP login, token retrieval, userInfo, screen transition or audio.

**Important for NAV9:** the owner device already has a clone-owned account. The fresh-install preinitializer therefore deliberately does not run for that state; if the key is absent it emits `ACCOUNT_EXISTS_NO_KEY_UNCHANGED`. Do not force-create or rotate a key against an existing encrypted account. The current NAV9 user data has not been modified.

### 2. Read-only post-login receipt chain

The clone-only module observes the real vendor path without manufacturing success:
- `MASTER_TOKEN_READ`: clone-owned `AccountManager.getPassword` result category only.
- `MASTER_TOKEN_DECRYPT`: real vendor decrypt result exception presence only.
- `POSTLOGIN_PUBLISH`: original `ZX5.if(WS3)`, including exact `REAL_USERINFO_SUCCESS` type only.
- `POSTLOGIN_CONSUME`: original `hT3.try(Bundle,String)` receives `EntryScreenCloseLoginKey`.
- `POSTLOGIN_MAIN_ROUTE`: original `YS3.if(lw4,boolean)` invocation and return/throw.

No password, account identifier, token, Bundle payload or userInfo fields are recorded. No result, preference, onboarding state or Activity launch is synthesized.

### 3. Final NAV12 onboarding writer investigation

NAV9 owner diagnostics show `ONBOARDING_PREF / ENTRY_ACTIVITY / UNSET` four times, including after the clone-owned account is visible. That is a fact, but not proof that this preference is the root cause. Exact original DEX inspection already established that `f67` is in the app upgrade/initialization family, not a proven Passport success callback.

The final source pass adds a read-only observer restricted to the clone's exact `Yandex_Music` SharedPreferences instance:
`ContextImpl.getSharedPreferences("Yandex_Music")` → `SharedPreferencesImpl.edit()` → `EditorImpl.putBoolean("onboarding", value)` → actual `commit()` or `apply()`.

It logs only the boolean, a sanitized first non-framework caller class/method and the real commit/apply result. It does not write the preference. Editor tracking was corrected so commit/apply is reported only when that editor actually received `putBoolean("onboarding", ...)`, not for unrelated edits to the same preference file.

A private, read-only exact-2025 DEX scanner was added:
- `android/native-yandex-hooklab/ci/a1_private_onboarding_contract.py`
- `android/native-yandex-hooklab/ci/test_a1_private_onboarding_contract.py`

It inventories methods containing the exact `onboarding` literal and preference API calls from the pinned signed 2025.10.4 base APK. It prints method identifiers/API names only, never DEX bytes, tokens, account data or credentials.

The native Android13 acceptance parser now also requires `ONBOARDING_WRITER_HOOK / ANDROID / REGISTERED`. Idle native CI can prove hook registration, but cannot prove that a real login invokes a writer.

## CI status at handoff

Previously confirmed:
- [#43574754576](https://github.com/manufact-test/nomusic/actions/runs/43574754576) — SUCCESS, `ORIGINAL_KEY_PERSISTED`.
- [#43574754550](https://github.com/manufact-test/nomusic/actions/runs/43574754550) — SUCCESS, `ORIGINAL_KEY_PERSISTED`.

Latest NAV12 checks were still running when this handoff was written; re-check the exact run pages before accepting anything:
- [#43576640113](https://github.com/manufact-test/nomusic/actions/runs/43576640113) — onboarding DEX scan step SUCCESS; paired native 75-second step still running.
- [#43577067135](https://github.com/manufact-test/nomusic/actions/runs/43577067135) — clone-alone run with runtime onboarding-hook gate.
- [#43577136676](https://github.com/manufact-test/nomusic/actions/runs/43577136676) — latest paired run from the final test-source correction.

Some intermediate runs failed only because source-contract tests assumed a reflection declaration was on one line while Java formatting split it across lines. Those test assertions were corrected in `c700ae1` and `e353f72`; re-check the latest run rather than treating the earlier assertion failure as a native or product failure. The static onboarding scan output from #43576640113 should be read from its completed job log; it was not yet available at handoff time.

### Exact onboarding DEX inventory result

The read-only scan completed in [#43576640113](https://github.com/manufact-test/nomusic/actions/runs/43576640113): **8 methods** contained the `onboarding` literal, **2 reader candidates**, **5 writer candidates**, and **0 undecodable methods skipped**. It identified:
- Reader candidates: `Lru/yandex/music/main/MainScreenActivity;->onCreate` (`contains/getBoolean`) and `LUc1$b;->emit` (`contains/getLong/setValue`).
- Writer candidates: `LVj1;->transient` (`clear/setValue`), `LUc1$b;->emit` (`contains/getLong/setValue`), `Lf67;->if` (`putBoolean/apply`), `Lru/yandex/music/profile/ProfileActivity$b;->emit` and `ProfileActivity$c;->emit` (`putBoolean/apply`).

These are **same-method literal/API co-occurrence candidates**, not a proven runtime call chain or proof that every candidate writes this specific key. Prior exact DEX callsite work places `f67` in app upgrade/initialization, not the demonstrated Passport success callback; profile writers are not evidence of login completion. The NAV12 runtime observer is the next discriminator.

The same #43576640113 paired Android13 run completed **SUCCESS** with `master_key_init_runtime_status=ORIGINAL_KEY_PERSISTED` and verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. This source predates the new onboarding-writer registration gate, so it proves paired idle startup/key persistence only.

## What remains unresolved

The NAV9 owner report confirms:
- `ACCOUNT_ADD / CLONE_OWN / ADDED` and `ACCOUNT_STATE / CLONE_OWN / ONE`.
- Passport activities called `setResult(OK)`; this is not proof Android delivered a result to Entry.
- Four `ONBOARDING_PREF / UNSET` observations.
- No observed new Main screen and no observed process crash.

It does **not** establish whether `getPassword` returned a master token, whether decrypt succeeded, whether Music produced `Success(userInfo)`, whether FragmentManager delivered the close-login event, or whether `LYS3` ran.

## Release and owner-device safety

- NAV8 and NAV9 have different outer signing certificates; each research CI run currently creates a disposable signer.
- Do not produce or install another owner APK until a dedicated persistent A1 signing identity is provisioned and verified. Do not reuse the Test.50 production signing key without explicit owner approval.
- No APK was exported in this pass.
- Do not ask the owner to repeat OTP, reinstall, clear data, use ADB/cable, remove original Yandex, or change onboarding.
- Keep the embedded publisher-signed APK, original Yandex installation, Test.50 and all production paths untouched.

## Next developer's exact order

1. Read this file, `NEXT-CHAT-ANDROID-A1-LEAD-20261113.md`, `ANDROID-A1-POSTLOGIN-RECEIPT-WITNESS-AND-SIGNER-GATE-20261114.md`, and `ANDROID-A1-NAV9-SIGNED-2025-POSTLOGIN-CONTRACT-20261114.md`.
2. Verify current branch HEAD and inspect latest Actions runs #43576640113, #43577067135, #43577136676. Read the private DEX onboarding scan output once its job has completed.
3. Confirm `ONBOARDING_WRITER_HOOK=REGISTERED` on both native Android13 configurations. If not registered, fix hook compatibility first; do not issue an APK.
4. Interpret the static writer candidates. Do not set `onboarding` manually. If the runtime writer is absent during a future genuine login, continue along token/decrypt/Success(userInfo)/FragmentManager/native route receipts.
5. Resolve dedicated persistent A1 signing before any owner delivery. Only then consider one bounded owner test that preserves existing app data and avoids repeated authentication.

**Stage A: NO-GO. Stage B: LOCKED.** The fresh-install key write is technically proven; the owner's post-login loop is not fixed or owner-verified.
