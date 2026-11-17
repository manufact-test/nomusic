# CELIKOM Android A1 — NAV21 owner real-phone TXT analysis (17 November 2026)

**Current evidence, replaces previous "await NAV21 TXT" instruction.** The owner supplied private `CELIKOM-A1-Diagnostics-1794944332422.txt`. This document records only privacy-bounded conclusions; **do not commit/upload raw phone TXT or user data**. The export itself has an old NAV20 marker in rotated local history, but the NEW active build marker appears twice as `NAV_V21_QUEUE_SCOPED_READ_RETURN_READONLY` (including the explicit exported marker). Treat the final NAV21 in-memory counters as authoritative, not the old rotated lines.

## Exact current phone comparison

| Evidence category | NAV20 owner phone | NAV21 owner phone |
|---|---|---|
| Four 2025-native hooks | REGISTERED | REGISTERED |
| QUEUE_SCOPE_ENTER | MANY | **NONE** |
| QUEUED_HOLDER_ATTACHED | ONE | **NONE** |
| ATTACHED_STREAM_READ_MATCH (strong) | FEW | **NONE** |
| UNSCOPED_ATTACH | FEW | FEW |
| UNSCOPED_ATTACHED_STREAM_READ_MATCH | MANY | MANY |
| ATTACHED_STREAM_READ_DIFFERENT / UNSCOPED_ATTACHED_STREAM_READ_DIFFERENT | NONE / NONE | NONE / NONE |
| STREAM_ALIASED_READ_RETURN_MINUS4 | MANY (strong+weak aggregated) | MANY (weak only) |
| STREAM_ALIASED_READ_RETURN_MINUS5 | FEW (strong+weak aggregated) | FEW (weak only) |
| STREAM_ALIASED_READ_RETURN_MINUS3 | FEW (strong+weak aggregated) | ONE (weak only) |
| QUEUE_SCOPED_READ_RETURN_MINUS4/MINUS5/MINUS3/OTHER | unavailable in NAV20 | **NONE / NONE / NONE / NONE** |
| UNSCOPED_READ_RETURN_MINUS4/MINUS5/MINUS3/OTHER | unavailable in NAV20 | **MANY / FEW / ONE / NONE** |
| READ_RETURN_LINK_LOST | NONE | NONE |
| Renderer identity status | STRUCTURAL_ONLY | STRUCTURAL_ONLY |
| Stage B | NOT_CONNECTED | NOT_CONNECTED |
| METRICA_EXCEPTION_SUMMARY (current MAIN-process category) | MUSIC_APP / FEW | **MUSIC_APP / MANY** |

NAV21 additionally reports `RENDERER_DETACHED=FEW`, `EXO_OPEN_OK=MANY`, `EXO_READ_POSITIVE=MANY`, `EXO_IO_FAILURE=NONE`. The observed renderer+stream aliases and original `b.g()` returns are real **weak/unscoped read evidence**. No queue-holder-scoped attachment was observed in THIS phone process. Neither `-4` (which may represent EOS), positive Exo source reads, nor object aliasing identifies the actively audible track/album/edition or downstream PCM output. No replacement sound is present.

## What it means, and what it does NOT mean

NAV21 did **not** demonstrate the desired strict queue-scoped successful return. The missing prerequisite is `QUEUE_SCOPE_ENTER`, not an observed strong read returning the wrong code: **the scope hook was registered but no invocation entered its counter** in this session. No mismatches or stale return links explain this. NAV20 did observe the scope at least once, so NAV21's phone trace follows a different observed route or timing; whether this is a real behavioral regression is **unknown**. The NAV20→NAV21 GitHub code delta adds result categorization, counters, tests, build marker and release workflow. It does **not change the native queue scope/attach/read/detach interceptors or `chain.proceed()` call route**. Therefore do not attribute the absent scope to NAV21 code without controlled reproduction.

`METRICA_EXCEPTION_SUMMARY=MANY` comes from the current in-memory `musicMetricaExceptions` counter (greater than eight observed MUSIC_APP exception-constructor events in current MAIN process), not merely old rotated `METRICA_EXCEPTION` log rows. Compare with NAV20 FEW, but do not equate exception construction to fatal Java crash: supplied NAV21 TXT has no confirmed `JAVA_CRASH` event, while exit history shows USER_REQUESTED/older OTHER. Investigate if owner also reports playback failure, repeated reopening or other symptoms. The owner provided the TXT without a separate reliable listening/Next/seek/My Wave account, so none can be claimed.

## Decision: NO new owner APK on this evidence alone

1. **Keep existing signed NAV21 installed**, no uninstall/data clear. A controlled same-build test is the next least-invasive proof gate: play an original song, use Next on a second song, pause/seek, optionally My Wave, then export a NEW TXT while the same MAIN process is alive; owner notes if original sound played, silent/frozen, or app restarted. Read `QUEUE_SCOPE_ENTER`, `QUEUED_HOLDER_ATTACHED`, strict returns, and fresh `METRICA_EXCEPTION_SUMMARY` together.
2. If `QUEUE_SCOPE_ENTER` remains NONE despite a confirmed queue transition, only then prepare a **narrow read-only exact-2025.10.4 hook path discriminator**: identify whether renderer attachment came through `LmQ8.catch` queue scope or an alternative native `b.super` path; observe only finite status categories and same-reference structural links, never objects/IDs/buffers/URLs. Need careful source audit and tests; alternate call path is a hypothesis, not an established NAV21 phone fact.
3. Any code change needs a new exact pre-change backup, isolated Java model CI, Android13 native/signer checks, and real-phone diagnostic-only APK **exclusively in verified personal ChatGPT Library**. Do not release unsolicited APK, modify original 2025 Yandex/vendor playback, activate Stage B, or touch Test.50, Windows, extension, server or unrelated 2026 HookSpec.

## Protected state

Repo `manufact-test/nomusic`; sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. NAV21 signed APK remains the verified Library item `/CELIKOM/Android/Native/CELIKOM-A1-NAV21-Queue-Scoped-ReadResult-ReadOnly-20261117.apk`, SHA256 `581077a18ea8310d12b0e8049e10fe6d25089ed3043cb8340e0e304b2d0d10ce`; compiled code commit `def5f4ff420ec3b285ee1853009882a8f991ec1f`; native CI #44140575566 SUCCESS, JVM #44140534551 SUCCESS. Final prior docs checkpoint `50228f81039e9443500eeaf4efbd0383708835cf` and backup `backup/android-a1-nav21-final-await-owner-txt-handoff-20261117` preserved. This analysis is documentation-only; no APK was produced or delivered.
