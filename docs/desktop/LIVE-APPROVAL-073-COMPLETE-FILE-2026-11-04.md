# Desktop 0.4.73 — complete-file adoption of a newly approved MP3

## Owner request

After 0.4.70 fixed opening words, live approval failed. 0.4.71 then caused a reported closure of the entire Brave window. A conservative 0.4.72 rollback was prepared but NOT sent to the owner; owner explicitly requested continuing until the live-approval mechanism is fixed, rather than sending rollback for another test.

0.4.71 remains WITHDRAWN. 0.4.70 is an accepted INTRO reference only. 0.4.68 remains the older accepted fallback. Do not claim the exact cause of Brave closure is proven without its process/crash evidence; the controlled Node failure explains the old retry loop, not a whole-process crash.

## Implementation

The changed route is restricted to a known negative mapping becoming available on the same track at a position over 250 ms. Initial positive lookup, guarded intro, normal streaming and ordinary active seeks retain their previous paths.

For a newly approved mid-song MP3, use the existing bounded, signed native-file downloader (already used for M4A/WAV). Fetch the complete unchanged MP3 through validated 206 ranges, max 30 MiB, one continuation at a time, 30-second transport budget. Reuse still requires a real signed first range and matching strong ETag/version key. No unsigned URL, persistent file, transcoding, server edits or account bypass.

Create a native Blob audio source only after all bytes pass range/type/size checks. This path does NOT create MediaSource and cannot seek an incomplete SourceBuffer. Original remains audible during the entire download; a stale admission transition is ended before native-file preparation, without reserving a long mute.

Only the complete native file can enter `prepareCompleteJoin`: it rejects any MediaSource. Complete a muted seek, read a fresh, operation-owned native snapshot, and align within 80 ms (at most 3 completed seeks / 2500 ms). Fresh final native position must remain within 100 ms before acquiring original guard. Do not force another initial seek after activation. Changed track/source, Stop, Original, expiry and access loss keep the existing cancellation fences.

No change to successful MAIN intro hold, adapter, sync engine, guard, backend or Android. New preparation diagnostics identify complete-file mode without URLs or credentials.

## Automated validation

New checks cover bounded signed MP3 download, content preservation, revoked access, complete-file alignment, stale ownership, user seek and rejection of MediaSource alignment. Controller checks verify original guard is acquired after fresh alignment and guarded intro does not use this route.

Browser fixture starts a real original at 42 seconds, first resolves unavailable, simulates approval, holds native-file continuation for 1800 ms, and requires the original to keep playing unmuted. After release, the real controller must adopt a complete native MP3 with one decoder/first download, no restore loop, aligned output and effective pause. Full existing opening-word hold, native MP3/M4A, delayed seek, volume/mute and original restoration scenarios remain enabled.

Dedicated workflow installs official Brave release using https://brave.com/linux/ apt instructions, then requires actual Chrome AND actual Brave native audio fixtures. Explicit browser override must not silently fall back to Chrome. A browser closing during a CDP request fails the test rather than hanging. A separate Windows job installs the official standalone Brave installer, verifies its Authenticode publisher, and requires the same real-media tests. Both run in isolated temporary browser profiles; cleanup may terminate only the child process tree created by this script. This still does not reproduce the owner's exact profile/GPU/crash report; record actual outcomes before claiming success.

## Delivery

Isolated branch: `feature/desktop-073-complete-file-live-join-20261104`. No stable branch update or server deployment. Version 0.4.73 only after tests pass; owner acceptance pending.

## Verified delivery

- Extension functional commit: `b081a2fa6c97c8a0373da6598fe08276eb757245`; final verification harness commit: `7b9c0656db9a78dd6d37af25c0c470129143c45a`.
- Workflow `41791574411`: both jobs SUCCESS. Linux job `126445927178` passed 360 Node regressions, actual Chrome 156.0.8078.47, actual Brave 156.1.98.63, lint, manifest validation and configured ZIP build. Windows job `126445927586` passed the real Brave complete-file live-approval, ordinary media, seeking, restoration and bounded intro fixtures.
- Earlier Brave harness invocations remained running; the final harness adds bounded RPC, stage reporting and owned child-process-tree cleanup. No audio assertions were skipped. Do not interpret an earlier incomplete harness as a reproduced owner browser crash.
- Configured ZIP `celikom-extension-0.4.73.zip`: 2,489,476 bytes; SHA-256 `d6689e9d1e7157572e64622864d8c84ec98ec80f286e4aec4cf6fa31bee1a5b8`.
- Persisted deliverable: `libfile_a4ccee7d8e4481919e0d5bac02be72ab`.
- Accepted 0.4.70 MAIN intro, adapter, sync and guard files remain byte-identical. Rollback 0.4.72 was not sent for owner testing; send only 0.4.73 as the new mechanism candidate.
- Owner acceptance PENDING. The exact whole-Brave closure was NOT reproduced and its cause is NOT proven. The changed route avoids unbuffered MSE mid-song seeking and passed all three actual browser/OS checks, but this is not a guarantee for every profile/GPU/network combination.
