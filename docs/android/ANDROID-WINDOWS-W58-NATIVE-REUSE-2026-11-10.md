# CELIKOM Android — reuse of the OWNER-VERIFIED Windows W58 source path

Date: 10 November 2026. Android-only experimental source. Windows 0.24.7, Test.50, HONOR and production remain untouched.

## Actual owner evidence and Windows code examined

- Windows 0.24.7 has **owner-confirmed audible approved audio**, working native Play, Pause, Seek, playlist Next, previous track, and MyWave (including unknown upcoming tracks). This is a **Windows** acceptance, not Android evidence.
- Windows W58 source analysis confirms **Stop disables new CELIKOM lookups and invalidates pending responses**, but it cannot replace an **already delivered signed URL / buffered native Yandex media source**. User heard the already-running replacement after Stop, consistent with these semantics. No independent after-Stop *fresh non-prefetched* track test was in the provided Windows log: do not assume new OFF-state mapping continues.
- Source reviewed: `windows-companion/w15/source-controller.mjs` and `windows-companion/w22/native-resource-adapter.mjs` at Windows W58 branch `experiment/windows-companion-integration-20261108` SHA `2338c2109ad55beb583397cfbf7161726d678777`.
- W58 report: https://github.com/manufact-test/nomusic/blob/2338c2109ad55beb583397cfbf7161726d678777/docs/windows/W58-OWNER-0247-CONTROLS-PASS-STOP-LIFECYCLE-20261110.md
- Windows protected W56 signed URL via an **Electron-specific** trailing `celikom_native_query_guard`; this change is NOT validated for Android and is NOT ported.

## Actual Android implementation from those lessons

1. `android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeGrantContract.java` — strict **structural** validation of CELIKOM's approved audio source before possible native admission: exact decimal Track ID, approved+entitled, HTTPS trusted origin, canonical replacement resource path, lower-hex token, signed expiry matching grant, optional canonical SID, no duplicate or extra query parameters, 5s–30min remaining grant TTL, known audio MIME. Rejects unknown query params and Windows URL padding. The **server remains the sole authority** to check actual HMAC/session/entitlement; no token/URI is logged or persisted by this validator.
2. `android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativeReplacementLifecycle.java` — switchable, epoch-fenced **pure-Java source admission** coordination using existing `NativePrePrepareAdmission` and `NativeSourceGate`. OFF cancels *decision eligibility* for outstanding work; old completions cannot map the next track. Next/radio/re-enable create distinct generations. It does **not** cancel actual network transport yet (no transport wired), and neither calls native play/pause/seek nor manipulates an already buffered player source.
3. Exact source admission requires trusted current **trackId+edition+generation** both in FileInfo and in the real native decoder's pre-prepare descriptor. Those sources have NOT been established/connected in Android. `NativeReplacementLifecycle` is a tested integration contract, **not an active live audio hook**. It's not wired to `NativeHookEntry` because the real decoder boundary is not proven.
4. `NativeGrantContractTest` and `NativeReplacementLifecycleTest`: fail-closed tests for malformed second-`?` URL (desktop 403 root cause), corrupted SID, unknown parameters, unauthorized grants, timeouts, Start/Stop after prepare, 5000 Next/radio races, late old responses and no double commit.

**[CI run #42802150192 SUCCESS 2/2](https://github.com/manufact-test/nomusic/actions/runs/42802150192)**. Exact tested code SHA `e2a3c7c9577ea0a44966d1859296d77e0bae40d7` on `experiment/android-native-yandex-fileinfo-hooklab-20261109`. Test was synthetic Java + actual standalone Android module compile; **not real native Yandex injection/playback**. Frozen test backup branch: `backup/android-w58-grant-stop-next-ci-green-20261110`. Pre-transfer backup: `backup/android-before-windows-w58-lifecycle-transfer-20261110`.

## Product implications / next real blocker

Windows proved the catalog+entitlement+Range origin and one native *desktop* source adapter can work end-to-end with secure signed media; it cannot prove Android's FileInfo and decoder accept same source representation. Real Android request → converter → active decoder identity still must be witnessed on separate authorized native ARM Android host. Without it, don't ship APK or claim audio success.

**Stop behavior to preserve:** When CELIKOM turns off, future *new* native source selection should use Yandex original. Already created current media source may finish playing its mapped source: not a hidden ongoing hook. Never fake instant revert by forcing native Next/Seek/Reload without a separately verified non-destructive implementation.

Windows W58 tests/prod 0.24.7 and owner HONOR untouched; Test.50 exact accepted baseline remains immutable. No paywalled ChromaSync, Yandex outreach, Play Protect bypass, token extraction, or server HMAC relaxation.
