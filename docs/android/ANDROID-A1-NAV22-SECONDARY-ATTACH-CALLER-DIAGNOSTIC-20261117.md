# CELIKOM Android A1 — NAV22 exact second renderer-attach caller (17 Nov 2026)

## Owner reality: original Yandex is fully working

The user explicitly confirms the currently installed NAV21 original native Yandex Music works like an ordinary Yandex installation: playback, seek, pause and other controls are normal; **the only missing product function is CELIKOM replacement music**. Never turn the NAV21 diagnostic counter differences into a claim about playback bugs, silence, crashes or seek regressions. This is a source-link discovery task, NOT a bug fix.

## Phone evidence and why a second read-only hook

Private NAV21 owner phone TXT is analyzed in [real-phone NAV21 report](ANDROID-A1-NAV21-OWNER-REALPHONE-TXT-RESULT-20261117.md). NAV21 all four native hooks REGISTERED; `QUEUE_SCOPE_ENTER=NONE`, `QUEUED_HOLDER_ATTACHED=NONE`, strong scoped read-return categories NONE. `UNSCOPED_READ_RETURN_MINUS4=MANY`, -5 FEW, -3 ONE, no mismatched stream links. NAV20 had queue scope MANY and at least one strongly attached stream. Both are only runtime structure evidence; do not promote `-4` to acoustic proof. Stage B still NOT_CONNECTED.

Signed-original 2025.10.4 exact six-DEX static proof in [attached-stream route](ANDROID-A1-CONCRETE-RENDERER-ATTACHED-STREAM-20261117.md) lists **two direct callers** of the same `k.package([LSr4;LR29;JJLSl6$b;)V`: already-observed `LmQ8.catch(k,xh6,RFa,LLL2)I` and `androidx.media3.exoplayer.b.super(LlQ8;[LSr4;LR29;ZZJJLSl6$b;)V`. The second has its own exact method identity, not the obfuscation from an unrelated 2026 Yandex package.

NAV22 adds **only one passive additional native interception** at `b.super`, inside the existing own-clone-scoped, exact `versionCode=24025542` native 2025 hook installer. An ephemeral thread-local `CallerFrame` observes same renderer object + stream parameter reference while the original method executes once and unchanged. In the existing `b.package` post-call observer, separate finite counters show whether a weak/unscoped attach was inside the secondary method and matched the same stream, was different, or occurred outside the secondary method when its hook was active. No added getters, no new players, no sound/bytes capture, no metadata, no server, no original Yandex modifications. The previous four hook/counter behaviors remain untouched.

### New private diagnostic-only categories

- `AUDIO_NATIVE_RENDERER_HOOK_STATUS;origin=SECONDARY_CALLER;error=REGISTERED/NO_HOOK/NOT_SEEN`.
- `SECONDARY_CALLER_ENTER`: bounded entry count for exact method (NOT necessarily sound).
- `SECONDARY_CALLER_STREAM_MATCH` and `SECONDARY_CALLER_STREAM_DIFFERENT`: same renderer/stream Java references vs mismatch at underlying attach.
- `UNSCOPED_ATTACH_SECONDARY_MATCH`, `UNSCOPED_ATTACH_SECONDARY_DIFFERENT`: weak attach while the secondary caller was active; never equivalent to queue-holder proof.
- `UNSCOPED_ATTACH_OUTSIDE_SECONDARY`: weak attach without secondary active, counted only if its hook was positively REGISTERED; **not proof of a third caller**.

Legacy queue-scoped/weak `b.g` read-return counters remain unchanged. `IDENTITY_STATUS` cannot become audible PASS merely because this alternate callsite is found. If a nested frame exits out of order, fail-closed invalidation prevents a spurious identity claim.

## Changes and verification

Single working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Pre-change exact backup `backup/android-a1-nav21-owner-accepted-original-before-nav22-caller-witness-20261117` @ `c728f2e8c069ac2d360aa28fedc45af9e5164379`. NAV21 signed Library APK untouched. Five Java regression cases cover weak secondary path, coexistence with valid queue scope, hook-active-only outside counter, mismatched stream rejection, and caller-frame unwind. JVM observer CI #44174039648 SUCCESS; independent earlier #44173881716 SUCCESS. New one-time private ARM13 owner export workflow `.github/workflows/android-a1-nav22-exact-second-attach-caller-diagnostic-export-once.yml` at source HEAD `50078f012a57b7fc13060c3205f2757b4a2894a7`, run #44174172281 in progress at document creation; **do not claim signed APK/Library until this finishes successfully and actual bytes verified**.

## Test and gates

Only if native/signer CI succeeds, export signed APK over NAV21; the user needs only to listen normally for a few songs and export TXT, with no alleged pause/seek bugs to reproduce. Assess whether the weak renderer attach is attached through `b.super` or outside it and then identify next concrete native linkage to the actually selected audible source. This diagnostic is not the CELIKOM substitution; keep Stage B NO-GO. Preserve all previous binary backups, same owner signing certificate and original embedded publisher-signed Yandex.
