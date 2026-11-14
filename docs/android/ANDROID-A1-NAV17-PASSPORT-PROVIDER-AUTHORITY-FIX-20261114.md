# CELIKOM Android A1 NAV17 — cloned Passport provider authority contract repair (14 Nov 2026)

## Owner's latest real diagnostic: NAV16

File: `CELIKOM-A1-Diagnostics-1794684080709.txt`, 992 lines, 68,018 bytes. Export is truncated (`LOG_TRIMMED KEEP_LAST_32KB`), includes earlier NAV15 lines (build marker line 53) and then the **NAV16** block (marker line 172). Main section:
- line 449 original `LOGIN_PIPELINE_SOURCE ENTRY PASSPORT_LOGIN_RESULT`
- line 455 clone account exists `ACCOUNT_STATE CLONE_OWN ONE`
- line 457 `LOGIN_TOKEN_OUTCOME ENTRY WRAPPED_FAILURE`
- line 458 `LOGIN_TOKEN_ERROR_KIND ENTRY PASSPORT_API_UPPER_A`; no emitted `LOGIN_TOKEN_CAUSE_KIND`
- line 461 original `LOGIN_PIPELINE_RESULT AFTER_TOKEN_REQUEST NO_USERINFO_RESULT`; line 462 flow `NO_USERINFO_RESULT`.
The selected account is present, Passport-side account was ADDED, master-token reads PRESENT / decrypt NO_EXCEPTION in subprocess logs. Real Music UserInfo, native Main and audio remain unproven.

**What exception A means:** verified exact original publisher 2025 DEX `com.yandex.passport.api.exception.A` extends PassportException, has constructors accepting either String or Throwable. It is an SDK generic wrapper; the enum alone does NOT prove network/signature/token/scope failure. There is no immediate cause in owner NAV16 log.

## New direct verified defect in the clone build

Analyzed exact owner-distributed NAV16 APK (and unchanged embedded original vendor APK) read-only. Original signed issuer manifest declares:
- `com.yandex.passport.internal.provider.InternalProvider` authority `com.yandex.passport.internal.provider.ru.yandex.music`
- `com.yandex.passport.internal.authsdk.AuthSdkProvider` authority `com.yandex.passport.authsdk.provider.ru.yandex.music`
- `com.yandex.passport.internal.sso.SsoContentProvider` authority `com.yandex.passport.internal.sso.ru.yandex.music`

NAV16 outer CELIKOM manifest instead had all three renamed to unrelated `pro.celikom.yandex.nativeclonelab.provider.<hash>` addresses, specifically InternalProvider `pro.celikom.yandex.nativeclonelab.provider.7337716868ec5ddd`, authsdk `...provider.a47a4f0d44e617c5`, SSO `...provider.af52aa711ffde2b8`. The hashes equal SHA256(original authority)[:16].

Original signed Yandex SDK `com.yandex.passport.internal.impl.U.<init>` creates its provider URI from `Context.getPackageName()` through `com.yandex.passport.internal.util.u.if`, whose effective rule is `content://com.yandex.passport.internal.provider.<runtime app package>`. The original `com.yandex.passport.internal.methods.requester.h.if` uses Android `ContentResolver.acquireUnstableContentProviderClient(uri)`, and a null result from that provider request can produce Passport exception `A(String)` without a nested cause. Android docs say null is returned if no provider matches the authority. Therefore the original SDK-generated URI for CELIKOM `com.yandex.passport.internal.provider.pro.celikom.yandex.nativeclonelab` could **not resolve** to the actual NAV16 provider, despite successful Passport UI account add.

**This mismatch is independently verified in the distributed APK and source, not speculation.** Its causal contribution to the owner's exact A exception is strongly plausible but still requires owner real-device confirmation; do not claim successful login until proven.

## Fix in the existing architecture, one working branch

Repository `manufact-test/nomusic`. Unique Android working branch remains `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; no new active branches. Exact pre-change protected backup:
`backup/android-a1-nav16-original-passport-provider-authority-mismatch-pre-fix-20261114` @ `137587ad7aaac44e98fb9fdacd834a6ae46eec75`.

- `b370fcf68add78da359fd9ff544f4b49094d8330`: in existing `android/native-yandex-hooklab/ci/owner_2025_lspatch2_namespaced_clone_arm13.py`, fix only **clone-owned** manifest authorities for these 3 known Passport components by the precise original SDK dynamic rule `<original prefix> + DEST`. The fix accepts and checks only original, prior hash and already-correct own value, fails closed on unexpected authority, preserves SYNC resource reference and keeps random hash for all other providers (AppMetrica included). On BASE require exactly three named Passport provider components; no signed vendor bytecode/assets or issuer app edits, no borrowed accounts, no synthetic login or bypass of Android account ownership. Their new authorities remain globally unique to clone package.
- `6aa4bf22d4b22453d4b96abc2ed903526a4fbe7d` + `f7c7d4f2b54eb24d9d1c0238bb9961915f0d16e5`: update ONLY diagnostic build label to `NAV_V17_PASSPORT_PROVIDER_AUTHORITY_FIX` and source tests.
- `7536d7fe18cf4af7d2d10f0bb40fdfcf51222889`: existing CI-executed `test_metrica_manifest_preserved_detail_control.py` asserts all 3 SDK-compatible clone authorities, correct hash-to-own repair, other-provider independence and fail-closed drift rejection.

## Acceptance, build and owner action

At document creation, triggered source CI is still running; **do not claim it passed**. Require exact clone-only + paired Android13 native GREEN, original nested vendor/source unchanged, signing-owner cert continuity before exporting one NAV17 owner APK using existing assistant-driven GitHub Actions workflow. No asking user to click GitHub Actions. Verify final APK three manifest provider authorities, one unchanged original embedded APK, module NAV17 marker, permanent signer `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` independently after export.

For owner: attempt **in-place install over NAV16**, no uninstall/data wipe, original Yandex untouched. Normal app launch/use; do not force OTP solely to generate telemetry; if flow happens and genuine `USERINFO_READY` + Music native Main appears, check music playback and navigation next. Export one TXT. If error persists, inspect new NAV17 type and continue from actual evidence without spoofing tokens. Stage A NO-GO / Stage B LOCKED until real owner Music entry and audio proven.
