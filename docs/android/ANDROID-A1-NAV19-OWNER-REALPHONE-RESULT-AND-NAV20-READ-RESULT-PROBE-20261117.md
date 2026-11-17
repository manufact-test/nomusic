# CELIKOM A1 — NAV19 real-phone owner diagnostic: renderer stream identity, not audio output (17 Nov 2026)

This is the **latest observed owner phone TXT** for the Android A1 read-only renderer track. User supplied private `CELIKOM-A1-Diagnostics-1794936007461.txt`. DO NOT commit the raw TXT or private song/account data into GitHub.

## What the handset actually proved

- Four exact 2025.10.4 renderer hooks installed: `QUEUE_SCOPE`, `STREAM_ATTACH`, `SAMPLE_READ`, `STREAM_DETACH` each `REGISTERED`. Thus the absent queue event is **not** a hook-registration failure.
- `QUEUE_SCOPE_ENTER=NONE` and `QUEUED_HOLDER_ATTACHED=NONE` despite `UNSCOPED_ATTACH=FEW`. The signed static `mQ8.catch → b.package` route is still a static fact, but no runtime entry into that queue hook was observed.
- `UNSCOPED_ATTACHED_STREAM_READ_MATCH=MANY`, `...DIFFERENT=NONE`, `READ_NO_MATCHED_ATTACHMENT=NONE`, `RENDERER_DETACHED=FEW`. This is a real owner-device **Java object reference equality between attached renderer stream and a renderer read-method entry**. IMPORTANT: NAV19's `b.g` observer fires *before* `chain.proceed()`, so it does NOT even prove the method produced a buffer. Further, this might not be the selected *audible* renderer or a currently heard song.
- `EXO_OPEN_OK=MANY`, `EXO_READ_POSITIVE=MANY`, `EXO_IO_FAILURE=NONE` (coarse bins) on separate Exo source evidence. No continuity to exact track+album+edition or audible decoder proven.
- `AUDIO_STAGE_B_STATUS;CELIKOM_REPLACEMENT=NOT_CONNECTED` by design. NO audio substitution / grant / output proof. **Stage A NAV17 owner accepted PASS; Stage B NO-GO.**
- The log has **455** identical `METRICA_EXCEPTION;origin=MUSIC_APP;error=EXC_OTHER` lines and two `LOG_TRIMMED=KEEP_LAST_32KB` records. The startup `DIAGNOSTIC_BUILD` line was trimmed, but the NAV19-only `AUDIO_NATIVE_RENDERER_HOOK_STATUS`/unscoped summary is present. This demonstrates diagnostic log spam; the data does NOT prove 455 uncaught crashes. `PREVIOUS_PROCESS_EXIT=OTHER` events for MAIN/OTHER_CLONE include recent entries; no `JAVA_CRASH` category in this TXT. A runtime owner assessment of audio/seek/Next/My Wave was not supplied with this upload.

## Bounded next code probe, no architectural change

**Protected pre-change backup:** `backup/android-a1-nav19-owner-realrenderer-reads-before-nav20-20261117` (exact source before the following changes). Single permitted branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

NAV20 **read-only** source changes (not an audio replacement):
1. `NativeRendererStreamEvidence.java`: add `onReadReturn(renderer, attachedStream, originalResult)` categories `STREAM_ALIASED_READ_RETURN_MINUS4 / MINUS5 / MINUS3 / OTHER`, plus `READ_RETURN_LINK_LOST`. A return is counted only while the same weak renderer→stream link survives the call. Even minus4 can be EOS; not audible confirmation.
2. `ExitCallsiteWitness.java`: original `b.g` calls `chain.proceed()` exactly once, unmodified; samples only the pre-existing bounded first few reads per attach and records their untouched integer return after the call. Adds an unconditional **export-time build marker**, because circular logs can trim startup.
3. Limit duplicate `METRICA_EXCEPTION` lines from `MUSIC_APP` to first 8 and include owner-export `METRICA_EXCEPTION_SUMMARY` coarse `NONE/FEW/MANY` status. This does **not** suppress/replace/modify exceptions, and leaves original AppMetrica behavior intact.
4. JVM model regression tests for original return outcomes, detached/stale streams and no invented queue proof. Exact source/CI checks updated to NAV20; original native ARM13 signer/75s/publisher-first gates retained.
5. No server, Windows, browser, Test.50, NAV17/NAV18/NAV19 signing key/data/architecture modifications. **Original tested Yandex 2025.10.4**; do not reuse 2026.10.3 HookSpec.

## Results and next acceptance gate

- JVM CI **#44136882616 SUCCESS** for NAV20 renderer-return model and source invariants.
- NAV20 owner signed one-shot export CI **#44137030390** initiated; at documentation creation **not yet owner-accepted**. Do NOT claim new APK ready or publish before SUCCESS + signer verification + Library upload/verification.
- The next meaningful live evidence is whether `b.g` returns `-4/-5/-3` with still-matched attached renderer stream, NOT whether a CELIKOM track is audible. Continue to observe before any source substitution. Unscoped attached-read match is a useful runtime improvement, but does not cure absent queue hook.
