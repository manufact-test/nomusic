# CELIKOM Android A1 — new lead handoff after AppMetrica read-only native ARM13 controls, 12.11.2026

## Read first
- `docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md`.
- `docs/android/ANDROID-A1-2025-DISTINCT-ONEAPK-NATIVE-75S-LAB-LEAD-HANDOFF-20261112.md` and prior `docs/android/NEXT-CHAT-ANDROID-A1-2025-METRICA-LAB75S-20261112.md` (restored here from doc-only HEAD `9de7a2f50ddba92476cffcf3e69e83ff9c5e035c`).
- **Most recent truth:** `docs/android/ANDROID-A1-METRICA-INIT-STATE-OBSERVER-20261112.md`.
- GitHub issues #41 and #42, source-only audio contract `android/native-audio-contract/source-contract.mjs` merged by lead and already tested, **NOT live Android audio**.

## Repository state, do not restart
- Experimental branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112` (the latest HEAD contains this handoff; consult GitHub for final exact SHA).
- Last exact SOURCE tested in actual native ARM13: `66a36f2fa0f7fab718582f8c98efbc7bfb37f61c`, immutable backup `backup/android-a1-metrica-readonly-v2-actual-arm13-nogo-source-20261112`.
- Pre-work immutable source `5891ee655061d2049d1e0b9fa7a83927f3b563d2`, backup `backup/android-a1-2025-distinct-oneapk-native-75s-metrica-lab-pass-20261112` (LAB ONLY, fatal suppressed).
- Accepted Test.50 `backup/android-test50-exact-source-owner-accepted-20261108`; frozen A1 `cc4cb0f93489168db21502f3ef195855ae9fb743`, DO NOT CHANGE.

## Proven real outcomes
- Previous LAB-ONLY two 75s green runs #43217132456 and #43217178231: original and single clone coinstalled, but one precise AppMetrica `IllegalStateException` fatal in Android kill handler was intentionally suppressed. Not product-ready.
- First no-suppression actual ARM13 [#43222681617](https://github.com/manufact-test/nomusic/actions/runs/43222681617) **FAIL**: original 16/16 stock 75s/25 PASS; one clone installed alongside but MAIN 1/25. MODERN `AppMetrica.activate` ENTER=3 RETURN=3 THROW=0 during Application.onCreate; Context CLONE, classloader MATCH; direct SDK `NOT_INITIALIZED` fatal; suppression 0.
- Second no-suppression actual ARM13 [#43224344294](https://github.com/manufact-test/nomusic/actions/runs/43224344294) **FAIL** same outcome, with extra observer: public AppMetrica `getReporter` 14/14 RETURNS, `getDeviceId` 1/1, `reportEvent` 1/1. No public API throw. Internal `AppMetricaFacade` state hook did NOT register (probable obfuscation). Fatal still SDK `DETAIL_NOT_INITIALIZED` `DIRECT_IDENTITY`.

## Next precise technical move
Find the **actual** reporter/async internal SDK callsite throwing the initialized-state exception after public activate returned; study SDK lifecycle and provider/service/process binding differential, ideally a safe bound-enum in-memory probe on the same disposable clone. Current code's own scoped observer and parser infrastructure is reusable; no user accounts/private messages/raw vendor stack or API keys in public logs.

Do NOT simply call activate again, delete AppMetrica manifest components, suppress fatal, rewrite Passport/DRM, fabricate an audio engine or mark ready. A successful independent ONE APK native 75s 25/25 **without** suppression remains mandatory before sound/seek/pause/Next/MyWave/B42 integration. Stage A NO-GO / Stage B LOCKED.

## Security and workflow
- Keep publisher-signed XAPK and own lab APK/signing keys in ephemeral GitHub runner only, **no uploaded artifacts**. Existing CI uses pinned SHA-256 ARM64 aapt2 and exact publisher private input verification.
- Preserve original signed publisher install FIRST then clone ONE-APK second in same genuine native ARM13 guest.
- Before edits create exact backup; save docs and issue #41 with accurate failure status. Do not merge into frozen A1, release or Test.50.

## Third experimental result — required update
Actual [ARM13 #43226144866](https://github.com/manufact-test/nomusic/actions/runs/43226144866), source `15b1c10338b25fdf0f41b7667cf67e160abc3fe0`: native original 25/25 PASS, independent clone 1/25 and direct SDK `NOT_INITIALIZED` fatal, suppression zero. Real reporter implementation hooks **registered** and saw 8 session operations + 2 reportEvent all RETURN and zero THROW. Public activation 3/3 returns. Error is therefore outside these synchronous APIs, likely downstream async SDK process (not yet proved). **Do not** infer Android native ready. Backups: `backup/android-a1-metrica-readonly-reporter-native-nogo-source-20261112`.

**Current follow-up:** classify actual SDK async work lifecycle/fatal callsite and service/provider/process identity safely on disposable ARM13, then make only a causal fix and rerun unsuppressed original+clone 75s/25. Do not merge or ship until PASS.

## Newer fifth ARM13 data — 12 Nov 2026
[#43230162000](https://github.com/manufact-test/nomusic/actions/runs/43230162000) at exact `e46da1f3c5199347b0cf8aa2b90bd3d47935821a`: original native **25/25 PASS**, independent clone **1/25, JAVA_CRASH**, zero suppression. Same Throwable originates in `com.yandex.metrica.*` code, but contains a *modern AppMetrica* initialization-message marker. Modern public class/activate exists and returns 3/3. Legacy public YandexMetrica class/signature not successfully resolved by observer (no legacy activation). Therefore DO NOT add legacy SDK activate or share the same analytics key. The `com.yandex.metrica` family can be internal legacy-package implementation/dependency; it does not prove separate public SDK.
Backup: `backup/android-a1-metrica-modern-only-public-legacy-internal-nogo-20261112`.
**Next**: classify exact failing SDK component/worker/service init and compare clone with stock under privacy-bounded native ARM13, then try only a cause-proven fix. Product A NO-GO / B LOCKED.
