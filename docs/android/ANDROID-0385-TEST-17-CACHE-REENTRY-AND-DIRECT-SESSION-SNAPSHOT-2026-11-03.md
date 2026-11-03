# CELIKOM Android Test.17 — repeated-file reuse and permission-free direct session evidence
Date: 2026-11-03. Working branch: `feature/android-0385-test15-permissionless-recovery-20261103`.

## Scope / acceptance state

This is one candidate **derived from owner-accepted Test.15**, not Test.16. Test.15 stays intact at `backup/android-0385-test15-best-owner-20261103` / `6fde1e48179ecb812f1def16067f18bf0d9c3003`. Test.16 has been rejected acoustically and its experimental changes were not ported.

**Goals:** prevent needless repeat downloads when the same next song has a cached full file, preserve a complete file when rapid Next interrupts decoder preparation, and obtain credible read-only evidence about the two Yandex source-state bugs. These address *specific* causes and observability, not volume, fade, polling rates, or unverified PCM alignment.

## Changes

1. **Lookahead reuse after fresh resolve:** after a newly authorized lookahead resolution, if the exact `trackId|replacement_id|version|duration|mime` key already exists in the bounded 8-entry / 96 MiB in-session cache, prime from it without inserting a redundant speculative download into the single serial audio lane. If the file is missing or edition differs, the existing download path remains. Existing account, active candidate, measured-duration and silent decoder gates still apply.
2. **Complete interrupted-file retention:** if a current full-file download completed but a fast source/identity change arrives before decoder validation, retain that complete local file in the *existing private in-session cache* instead of deleting it. Only `track_changed` and `identity_changed` are eligible; failed decoder, auth loss, Stop, service cleanup and partial streams still clear files. Reuse never bypasses a **fresh live server resolve** and measured duration check.
3. **Independent direct Media3 observer:** for the two exact owner-reported track IDs (`39949113`, `42884423`) a bounded, passive second `MediaController` is built from the primary `getConnectedToken()` **only if** it is an authorized same-package `TYPE_SESSION` token. Start is deferred four seconds after the candidate is first observed to avoid competing with the first chord, and comparison is at most every 500 ms for 75 seconds. Every lifecycle exit releases the observer/future. Public Yandex service token names are logged for discovery, but no unknown service is connected. The secondary observer never sends play, pause, seek or other transport commands; it never changes the audio source of truth.
4. **Safety / regression:** host cases for exact cache reentry, changed edition, fast switch before prepare ACK, failed prepare, same-track large/small seek discrepancy, delayed source, pause-state mismatch, unknown/invalid position, other track and duration mismatch. Static guards prohibit transport commands by the observer. Existing HONOR frozen seek/ACK fingerprint remains unchanged.
5. **Isolated delivery:** `0.3.85-test.17/code86102`, package `pro.celikom.nativeprobe.test`; an automated validation-on-push → reusable signed-test-build chain is scoped to this feature branch only. Stable publisher branches and Hostinger OTA remain untouched. The test APK builder retains its original signer and API36/D8/signing checks.

## Explicit limits and unresolved hypotheses

- A second direct controller is **not yet proven** to expose a fresher position or pause. It is a diagnostic experiment only; it cannot yet correct «Дым» or «Нас не понимают вообще». Compare `source_direct_session_comparison` events with visible Yandex UI at specific video frames. If primary/direct positions both stay stale, the public session is likely not publishing the actual UI state.
- `SessionToken.getAllServiceTokens()` is discovery metadata, not evidence another exported endpoint works. No new sensitive permissions, no platform active-sessions enumeration, no Accessibility, no NotificationListener, no capture, no root, no private Yandex APIs.
- No process-persistent cache was added: existing service start removes orphaned `replacement-*.audio` and `buffered-*.audio`. A durable cache would need atomic manifests, account/entitlement scoping, cryptographic integrity, TTL, size/eviction, and explicit logout cleanup. It is not safe to simply stop deleting temporary files; inspect field improvement before expanding.
- The first arbitrary unknown uncached track still requires the complete file; real acoustic PCM phase and codec-edition alignment are not measured. These changes cannot promise a zero-ms first chord.
- Test.15 was owner-accepted; Test.17 is **not owner-acoustically accepted**. Any regression returns to the unchanged Test.15, not Test.16.

## Verification / field test

Required: full native host suite including new cases; unchanged accepted seek fingerprints; Android API36 javac/D8; signed test APK with original certificate; artifact ZIP; stable publishing skipped. Record exact commit, run, artifact, signer and SHA after CI completion. Do not commit personal journals or video.

One owner test: install the separate CELIKOM Test APK, listen through mixed automatic transitions, quick Next and repeated songs/playlist switches; seek and pause both problematic tracks (and an ordinary seek/pause control), with one combined diagnostic/video. Compare against the *same* Test.15 acoustic baseline; track queue/cache events, first audible guard and `source_direct_session_comparison` before claiming progress. Do not test a micro-build for each subchange.

## CI completion / signed receipt (2026-11-03)

- Functional commit: `b24c6d9b527fd5810ba9ef8287c730147acbd3b1` (the exact source the signed APK was built from).
- **Full CI SUCCESS:** https://github.com/manufact-test/nomusic/actions/runs/41688562595 (native-android and isolated build-test-app both success; all stable publish jobs SKIPPED).
- **Signed Test.17 ZIP artifact:** https://github.com/manufact-test/nomusic/actions/runs/41688562595/artifacts/13257301057, id `13257301057`, `CELIKOM-Test-0.3.85-test.17-code-86102`, expires 2026-11-10T17:56Z.
- APK: `CELIKOM-Android-0.3.85-TEST-17-CACHE-DIRECT-SNAPSHOT-SIGNED.apk`; SHA-256 `2f1e0f06314fd37c4b3ed548ba2e3672961969fdaf13404bfb3cae1cc3a796e8`, size 8,800,409 bytes.
- Package `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, version `0.3.85-test.17`, code `86102`. Signer SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` matches original; APK signature v3 verified (v2 not present, v3 is accepted). Separate sandbox and launch icon verified, updater/stable refs absent.
- Host regressions including new cache/session comparisons, frozen seek, Android API36/D8 and build-contract passed. Stable OTA/Hostinger unchanged; no phone listening validation yet. Do not call seek/pause of the two target songs fixed before new owner diagnostics.
