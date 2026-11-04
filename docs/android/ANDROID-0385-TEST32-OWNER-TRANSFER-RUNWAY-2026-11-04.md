# CELIKOM Android Test.32 — single owner transfer and verified sparse runway (2026-11-04)

## Status and scope

Test.32 is one isolated owner-device experiment, not an owner-accepted acoustic release. It starts from documentation HEAD `c53935141ef20338a4b88a0ee0c1a9a62fc9e351` (Test.31 signed functional SHA `8f3bce6bb049d66ae1e30316ab4365bbd7c9f66b`). The exact Test.32 functional source SHA and CI artifact are recorded below after validation; do not substitute a subsequent docs commit for the signed-source SHA.

Branch: `feature/android-0385-test32-audio-owner-runway-20261104`. Separate package `pro.celikom.nativeprobe.test`, name `CELIKOM Test`, version `0.3.85-test.32`, code `86117` (> Test.31 code86116). Stable package `pro.celikom.nativeprobe` 0.3.85/code86 is not built, signed, published or updated by this test workflow. No manifest permission or account/Track ID change. No PC, Hostinger or OTA edits.

## Repaired defects

1. **Sparse startup was not a readiness proof.** The previous 128KiB initial block authorized `MediaPlayer` preparation, while scattered future cache blocks could be incorrectly treated as enough audio. `BufferedAudio` now provides a position-aware, contiguous, fully validated *future* byte runway gate (12 seconds projected from actual file size and source duration, minimum 512KiB and capped at 1MiB except near end). A complete file qualifies immediately. The original stays at full gain and the decoder is muted until both real advancement/clock agreement and this runway gate pass. Total cached bytes alone never qualify. The VBR byte/time estimate is conservative, **not a decoder-clock or acoustic PCM measurement**.
2. **Transport self-starvation during handover.** Native foreground seek still gets priority; when the seek has reached handover, the previous `fade()`-level prefetch hold is released, and serialized background Range prefetch continues while original sound remains audible. Foreground decoder reads continue to preempt speculative traffic. The old speculative 512KiB batching remains disabled.
3. **Zero-millisecond source→replacement after BUFFERING/seek.** The `update()` branch previously called `grantReplacement()` + `applyVolume(1)` when the decoder happened to be playing and no fade was pending. Now if original gain is nonzero, it must enter the same ticketed, bounded clock-gated transition. Already exclusively owned replacement and owner-approved audible cached hot seeks remain in-place. Cold and post-seek coherent joins share the current complementary 160ms command envelope, with no changed gain-law coefficient or unproven phase assumption.
4. **Underbuffered stream re-grants.** A sparse decoder that *already acquired audible ownership* and then fails the existing real-stall recovery gate is retired, the original is restored, and the next fresh resolve uses the full-file fallback instead of returning to the same starved decoder. Before first ownership, a stall retains the prepared player and original sound while data is awaited. A 12-second maximum startup runway wait chooses full-file retry, not premature audible ownership. Account/track/callback tickets still fence the handover.

## Engineering limitations and why they matter

The existing permissionless architecture has **two independently clocked Android audio streams**: original Yandex Music processed by its verified session effect and CELIKOM `MediaPlayer`. A 160ms command-level complementary fade does not prove sample-accurate phase or remove every possible audible «пшик». Host checks cannot certify Bluetooth hardware output. Yandex UI may publish a finger seek later than Media3; this work intentionally does not claim to recover missing Yandex events or modify the frozen source/seek callback transport.

Full-file retry is intentionally safer than repeatedly stealing audio from a sparse stream; on slow connections this can mean the original plays longer before a replacement becomes available. We expect this to trade aggressive early connects for consistent audible ownership; the actual HONOR result remains unverified.

## Regression and delivery checklist

* `TestStreamRunway`: scattered cache, partial head, contiguous head/middle, complete file.
* `Test32AudioOwner`: 128KiB-equivalent preparation stays source audible, verified runway then one join; post-grant starvation retires sparse stream and chooses full-file recovery; previously 0ms regrant now enters clock-gated fade.
* Full `tests/run_engine.py`, including accepted cached seek and `check_0385_seek_baseline.py`; static source authority; lookahead and background observer gates.
* GitHub Actions Android SDK36/D8, reusable isolated signing job and artifact inspection; signing certificate SHA256 must be `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`. Verify package/versionCode, v2/v3 signature, original assets and OTA absence before handing over an APK.
* One real HONOR listening run only after signed CI: ordinary sequential songs, seek, pause/resume, poor network if convenient. No repeated videos required. Owner verdict remains pending.

## Pinned rollback (hands off)

* Test.23 owner-accepted: `backup/android-0385-test23-owner-accepted-20261104` → `251b6facc8739557ff962365da012d502ed3bac8` (original signed APK `libfile_301d98360e9c8191b8e05594f402d265`).
* Test.28 owner-selected: `backup/android-0385-test28-owner-selected-20261104` → `904ba52d5afbb5e77f4ee36e40d321d568896460` (original signed APK `libfile_dbc76474748481918f72b91a9eaea383`).
* Test.31 owner-rejected: `8f3bce6bb049d66ae1e30316ab4365bbd7c9f66b`; signed APK `libfile_a4aa619bae1c819187d651fb9900ad05`.

Installing Test.32 over Test.31 keeps test app data due the same package, same original signer and higher code. Installing an older code normally requires a separately signed higher-version restore or removing **only** the test package, with its app data loss. Never uninstall the stable original.

## CI provenance (fill from GitHub after build)

* Test.32 functional source SHA: PENDING.
* Validation + signing run URL and result: PENDING.
* Signed artifact and SHA256: PENDING.
* APK original-signature/manifest inspection: PENDING.
* Owner HONOR acoustic acceptance: **PENDING, NOT VERIFIED**.
