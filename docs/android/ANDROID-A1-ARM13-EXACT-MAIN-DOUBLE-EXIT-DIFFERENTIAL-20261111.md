# CELIKOM Android A1 — exact-MAIN double-exit A/B on native ARM Android13 (11.11.2026)

**Status:** genuine ARM13 native Yandex clone still **NO-GO**. This document records **newly verified lifecycle and error evidence**, not a working APK, audio source swap, identity-bypass recipe, or determination of internal publisher cause.

## Evidence and source

- Working branch: `experiment/android-native-a1-lspatch-clone-loader0-20261111`
- Diagnostic source as tested: `ebe93ec17a67a757fb571342efa9140ae111b304`
- [Latest real ARM13 CI 43001123875](https://github.com/manufact-test/nomusic/actions/runs/43001123875) (**FAILURE by expected clone runtime gate**), native Linux ARM64 + real Android13 ARMv7 Redroid; signed original #170gpr with five immutable splits.
- **44/44 regression and structure tests PASS** (17 startup observer, 17 crash/exit classifier, 6 zero-loader, 4 merge). Guest boots; three ephemeral lab-signed clone arrangements each install/launch. The CI's final nonzero status is the intentionally strict live MAIN gate, not a test compilation error.
- Earlier matching different-format read-only A/B: [43000335583](https://github.com/manufact-test/nomusic/actions/runs/43000335583). The last accepted signed-original control remains [42991987794](https://github.com/manufact-test/nomusic/actions/runs/42991987794). No production artifacts produced.

## Actual new differential

| Scenario | Exact MAIN EventLog lifecycle | MAIN logs, fixed safe classifications | Outcome |
| --- | --- | --- | --- |
| Five lab-signed clone splits, no loader | `am_proc_start → am_proc_died → am_proc_start → am_proc_died` | `ILLEGAL_STATE` (matching `IllegalStateException`) on E/F; generic `OTHER_THROWABLE`; no AndroidRuntime fatal/stack frames | `EXIT_SELF`, status zero; MAIN not alive |
| One lab-signed merged clone APK, no loader | Same four exact MAIN events | Same scoped `ILLEGAL_STATE` marker | `EXIT_SELF`, status zero; MAIN not alive |
| One separately signed merged clone APK, LSPatch0, zero modules | Same four exact MAIN events | Same scoped `ILLEGAL_STATE` marker | `EXIT_SELF`, status zero; MAIN not alive |
| Unmodified publisher-signed original five splits | **One** exact `am_proc_start`, no `am_proc_died` | E/F logs include `ILLEGAL_ARGUMENT` and generic `OTHER_THROWABLE`, but **no `ILLEGAL_STATE` observed** in the bounded sample | MAIN alive and Activity resumed after observation |

Each clone has two `ApplicationExitInfo` exact MAIN records. The process *launch/death* cycles are independently corroborated by AOSP EventLog, after excluding `:AppMetrica` and other helpers. This does **not** prove the second launch mechanism (automatic service restart vs explicit app start) or the cause of either exit. Activity-specific `am_resume_activity` event tags were not observed, but `dumpsys activity` did briefly observe resumed Activity for clones; do not interpret absent event tags as "no Activity".

No `AndroidRuntime FATAL EXCEPTION`, Android EventLog `am_crash`/system `am_kill` or scoped native signal was observed in these buffers. These absences do **not** establish that no internal error occurred. `IllegalStateException` is an **associated diagnostic marker, NOT a verified causal throw or integrity check**. No exception stack frames were present for subsystem attribution; issuer signing vs package identity remain jointly different and not isolated.

## Two analyzer bugs eliminated

1. Android `logcat -b events -v brief` emits `I/am_proc_start( 123): [..]`, while the initial observer accepted only `am_proc_start:`. Fixed brief-header parsing with regression tests.
2. Earlier string-matching process lifecycle events counted a `:AppMetrica` helper as MAIN if the *hosting component* field contained the exact app package. AOSP's published [EventLogTags](https://android.googlesource.com/platform/prebuilts/fullsdk/sources/+/refs/heads/main/android-35/com/android/server/am/EventLogTags.java) says `am_proc_start` process name is array **field 3**, and `am_proc_died` / `am_kill` / `am_crash` process name is **field 2** (zero-indexed); the observer now checks those exact positions, never merely any package occurrence. `am_anr` has a package, not a process name, so it is conservatively excluded from MAIN attribution.
3. The comparison now classifies working publisher-signed ORIGINAL main log with the same fixed-vocabulary parser (using exact live PID on a newly cleared private main buffer) as the failed clone (using **fresh** exact MAIN ApplicationExitInfo PID). Raw PIDs/stack/log/error texts/tokens are never printed.

## Engineering verdict and next single evidence-bearing gate

- This proves **two recorded main start/death cycles per cold-launch probe in all three clones**, whereas the signed original has a single surviving MAIN process. The actionable differential is **main-specific `ILLEGAL_STATE`** coincident with `EXIT_SELF(0)`; neither is tied to a confirmed source line.
- One bounded potential further read-only gate is **privately correlate the two distinct EventLog MAIN PIDs with the two fresh exit-info MAIN records and per-PID exception categories** to determine whether both cycles independently log `ILLEGAL_STATE` before exiting. Emit only bounded booleans/counts. If both cycles match but have no causal stack, stop claiming incremental proof from more identical CI trials.
- No further ABI, ZIP, NativeBridge, LSPatch0 layout carousel; no signature/Passport/DRM bypass or security weakening. The owner explicitly forbids unsolicited Yandex contact. Do not send messages on their behalf.
- Stage A is **NO-GO** until true independently installable native Yandex UI and same-decoder licensed audio swap work, Play Protect ON/stock side-by-side and owner audible validation pass. No user APK; no Stage B. Original owner HONOR 50, accepted Test.50, Windows W61, extension, production untouched.

## Backups

- Before original-control differential: `backup/android-a1-before-original-control-error-differential-20261111` @ `b3c5f897e2f58a3b3b661743c054f9cfc24741fc`
- Before brief-format parser: `backup/android-a1-before-logcat-brief-event-parser-20261111` @ `941dbfc9b9777ff39e0abe77dbf9ab93958b069e`
- Before exact AOSP field scoping: `backup/android-a1-before-aosp-events-exact-process-scoping-20261111` @ `afe6c4efa03ad01ae4f759ddc7bd318e848c1900`

Related: [Approved master](CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md), [handoff](ANDROID-A1-NEXT-CHAT-FINAL-HANDOFF-20261111.md), [blocker issue #41](https://github.com/manufact-test/nomusic/issues/41).

## 11 November 2026 — exact **per-PID** correlation verified (subsequent controlled run)

**[CI 43001833178](https://github.com/manufact-test/nomusic/actions/runs/43001833178)**, code `4d79ef03e70845d6d7be6c3cada6fb8d4f058f9b`, passed **47/47** startup/classifier/loader/merge tests (20+17+6+4); Redroid Android13 native ARM boot PASS; strict native clone runtime gate **FAILURE as expected**, not a unit error.

New method `classify_main_cycle_correlation` privately joins `ApplicationExitInfo` exact fresh MAIN process PIDs with structured AOSP `am_proc_start/am_proc_died` PIDs and PID-scoped logcat `IllegalStateException`. Only boolean/count categories leave CI; no raw PID, stack, class string or credentials.

**Across EACH of the 3 independent clone layouts**, exactly **2 different fresh exact-MAIN exit PIDs** have all of:
1. `EXIT_SELF` and exit status 0;
2. a matching `am_proc_start` and `am_proc_died` in native Android EventLog (helper processes excluded by AOSP structured process-name field);
3. an E/F-scoped `IllegalStateException` marker in that PID's main log.

That is 6 individually correlated clone MAIN lifecycles, not merely six lines mentioning a package name. The same publisher-signed original MAIN remains alive after a single `am_proc_start` without an `am_proc_died` or `ILLEGAL_STATE` marker in the bounded window; it has a different `ILLEGAL_ARGUMENT` logging marker. **These are associations; no stack/specific instruction or intentional publisher security check has been proved.** Repeating the same three layouts or only adding more identical PID counters no longer improves causal understanding. A new next step must expose materially new, legitimate evidence.

No Android APK delivered, no owner HONOR touched, no signature/Passport/DRM bypass, no communication to Yandex. User-approved Stage A remains NO-GO and Stage B remains locked.

---

