# CELIKOM Android A1 — actual ARM13 ART trace, capacity limit and inconclusive exception (11 Nov 2026)

**Product Stage A: NO-GO.** This is the exact diagnostic continuation after [the true ARM13 double-exit evidence](ANDROID-A1-ARM13-EXACT-MAIN-DOUBLE-EXIT-DIFFERENTIAL-20261111.md), not an APK handoff, audio test, publisher protection bypass or causal root-cause proof.

## Important observed differential

A real ARM64 GitHub-hosted, Android13 ARMv7 Redroid guest loaded an **independently signed lab clone** with `android:profileable android:shell=true` in the **compiled** APK. The original five publisher-signed Yandex Music splits stayed unmodified and their MAIN remained alive and Activity resumed, while all clone layouts still exited MAIN with `EXIT_SELF(0)`.

- [CI 43005865574](https://github.com/manufact-test/nomusic/actions/runs/43005865574): 69 diagnostic/contract tests passed; compiled lab APK really had shell profiling enabled, but stopping ART **after** clone exit produced a **zero-byte** trace. The original MAIN remained alive.
- [CI 43006425478](https://github.com/manufact-test/nomusic/actions/runs/43006425478): **70 diagnostic/contract tests passed**. Stopping ART **while lab clone MAIN was still alive** produced a valid, private **599,184-record** ART method trace. `YMApplication.onCreate` and default uncaught-handler installation were observed, but the trace stopped before MAIN death; absence of `System.exit` / `Runtime.exit` / `killProcess` in the retained records proves nothing about later execution.
- [CI 43007210075](https://github.com/manufact-test/nomusic/actions/runs/43007210075): **73 diagnostic/contract tests passed**. A separate early ART trace again had exactly **599,184 records**. `YMApplication.attachBaseContext` was entered and returned on MAIN. A `java.lang.IllegalStateException` constructor appeared **once in a non-MAIN thread**, with immediate caller categorized `ANDROID_RUNTIME`. There was no corresponding constructor observed on MAIN. `YMApplication.onCreate` was not present in this bounded capture, which does **not** prove the method was skipped.
- [CI 43010485075](https://github.com/manufact-test/nomusic/actions/runs/43010485075): **75 tests passed**. Delaying profiler stop until a **second separately observed live/resumed MAIN sample** again gave a **zero-byte trace**. The profiler had been stopped while MAIN was observed alive, but a nonempty trace was not guaranteed. The clone still self-exited; original survived.
- [CI 43011106033](https://github.com/manufact-test/nomusic/actions/runs/43011106033) is the follow-up exact-overflow-header/8-MiB-capacity regression run; do not claim its result until complete.

Every overall native CI above is **FAILURE due to strict clone MAIN gate**; individual tests passing or valid ART profiling does NOT change product NO-GO.

## Critical ART buffer saturation discovery

Both independent valid ART captures reported exactly `599184` trace records. For Android ART format v3 (14 bytes per record), `599184 × 14 + 32 = 8,388,608` bytes = **8 MiB**. Android [public Debug API documentation](https://developer.android.com/reference/android/os/Debug) confirms the **default 8 MB trace buffer**. The [AOSP ART trace implementation](https://android.googlesource.com/platform/art/+/c968f45f41f9ca409c967e5495d28a049eebf14d/runtime/trace.cc) records the explicit `data-file-overflow=true|false` text header field. [AOSP ART trace buffer behavior](https://android.googlesource.com/platform/art/+/f65b1c4e254b3fcd262ed6f26420d4d13b127709/runtime/trace.h): once the **non-streaming** buffer fills, **following events are ignored**; it does **not** necessarily preserve the final moments of the process.

Therefore, a 599,184-record capture can be a **saturated early prefix**, not a full call history or death stack. Claims that `onCreate`/exit calls never occurred, or that the single observed background `IllegalStateException` constructor **caused** `EXIT_SELF`, are unsupported. The previously observed Android `logcat` E/F `IllegalStateException` markers and exact process start/death correlations remain independently established, but no method or subsystem has been identified as the reason for MAIN self-exit.

The updated `observe_native_startup_trace.py` (source `2faebf0818c2b31536ebdd171337b2f17ba138d7`) checks the **explicit** `data-file-overflow` header and conservative 8-MiB capacity heuristic. It exposes only bounded booleans/enums and class-family groups. The positive method observations remain informative; the absence of a method from an overflowed or partially observed trace is **non-evidence**.

## Engineering decision and guardrails

Avoid rerunning identical five-split / merged / LSPatch0 clones with a default 8-MiB non-streaming method trace and treating omitted events as new proof. A possible **single different and bounded** next test is the standard Android `am start --start-profiler ... --sampling INTERVAL` mode, to reduce record volume and assess later high-level startup phases; this has weaker causal resolution and must not claim an exact method call from a sampled stack. If that also fails, record the diagnostic limit and seek a genuinely new source of safe evidence rather than infinite CI retries.

Only the separately signed **owned, disposable lab clone** is profileable. Publisher-signed original was not profiled or modified. No account, password, Yandex tokens, DRM, signature impersonation, security disabling, Play Protect modification, root, user HONOR device interaction, production or Test.50/Windows changes. No APK distributed or suitable for user testing. No publisher outreach (owner explicitly declined it). Stage B (custom patcher) locked until Stage A works audibly and is owner accepted.

## Exact source / backup

- Research branch: `experiment/android-a1-arm13-shell-profiler-no-bypass-20261111`
- Safe original prior to ART investigation: `backup/android-a1-true-arm13-merged-timeline-pre-art-profile-20261111` @ `df5037fb2cbbc74e440dae5d88964960f0589ddb`
- Working captured ART before added onCreate/constructor watch: `backup/android-a1-arm13-art-599k-records-before-exception-stage-20261111` @ `c2e81771d2af67e2110625d2e989ed6d9c863fa3`
- Before later timing probe: `backup/android-a1-art-oncreate-exception-staging-evidence-20261111` @ `a7f44901e4fb214d5644e2dc664553bc4b3113e7`
- After later timing probe: `backup/android-a1-art-second-alive-zero-trace-20261111` @ `cbc7834a038743c67b32aa0e929f6cd0fbed1369`

Canonical master: [CELIKOM Android native clone TZ](CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md), [handoff](ANDROID-A1-NEXT-CHAT-FINAL-HANDOFF-20261111.md), [open issue 41](https://github.com/manufact-test/nomusic/issues/41).
