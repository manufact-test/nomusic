# CELIKOM Android A1 — NAV26 owner phone FALSE comparator; NAV27 attach-phase discrimination (18 Nov 2026)

## Authority and scope

Only work in `manufact-test/nomusic` / `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Native original publisher-signed Yandex Music 2025.10.4 is working; pause, seek and Next are not known to be broken. The **only outstanding feature** is CELIKOM alternative-stream substitution. No architectural changes or original vendor audio modifications. Stage B remains `NOT_CONNECTED`. Do not review account/Passport telemetry or commit private owner TXT.

Owner's actual NAV26 TXT: `CELIKOM-A1-Diagnostics-1794990212006.txt`; received and parsed directly. The authoritative current markers are `NAV_V26_EXACT_LMQ8_RENDERER_COMPARATOR_OUTCOME_READONLY;ACTIVE` in both active process and exported summary, not historical rotated lines. Raw file stays private.

## Actual NAV26 phone observations

- All required audio hooks `QUEUE_SCOPE`, `STREAM_ATTACH`, `SAMPLE_READ`, `STREAM_DETACH`, `SECONDARY_CALLER`, `ENGINE_HOLDER_SCOPE`, `RENDERER_TYPE_STATE_ACCESS`, `RENDERER_COMPARATOR` report `REGISTERED`. The optional already-known `BUFFER_EOS_ACCESS=NO_HOOK` is unchanged and is not a playback defect.
- `RENDERER_COMPARATOR_TRUE=NONE`, `RENDERER_COMPARATOR_FALSE=MANY`, `RENDERER_COMPARATOR_UNAVAILABLE=NONE`. This is the raw original `LmQ8.try(Lxh6,k)Z` return preserved exactly, not a proven equality/selection interpretation.
- `ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE=NONE`, `...FALSE=NONE`, `...TRUE_MINUS4=NONE`, `...FALSE_MINUS4=NONE`. The exact same holder/renderer/stream comparator event was NOT re-identified at later started-audio read by NAV26's current in-memory lifetime rules.
- The independent engine-holder/stream proof still works: `ENGINE_HOLDER_SCOPE_ENTER=FEW`, `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW`, `DIFFERENT=NONE`, `UNAVAILABLE=NONE`. `ENGINE_HOLDER_READ_RETURN_MINUS4=MANY`, `MINUS5=FEW`, `MINUS3=MANY`. `ENGINE_HOLDER_RENDERER_TYPE1=MANY`, `ENGINE_HOLDER_TYPE1_STATE2=MANY`, `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4=MANY`; `READ_RETURN_LINK_LOST=NONE`. No claim of audible PCM based on -4 alone.
- `WRAPPER_MAIN_SOURCE`, `TRACK_SOURCE_READ_LINK`, `TRACK_SOURCE_ALBUM_READ_LINK` are still `NONE` despite separate `NATIVE_TRACK_FLOW_EMIT=FEW`, `TRACK_WRAPPER_LINK=FEW`, `EXO_READ_POSITIVE=MANY`. These are separate observational paths, NOT selected Track→renderer identity.
- `IDENTITY_STATUS=STRUCTURAL_ONLY`; `CELIKOM_REPLACEMENT=NOT_CONNECTED`. No source swap or other audio handling in this build.

## Source-backed explanation of the unresolved phase boundary

In `NativeRendererStreamEvidence.onAttach(renderer, stream)` NAV26 removes any old `ComparatorLink` with the same renderer on **every attach**, even if Java holder or stream objects are reused; this prevents stale comparator results from being accidentally promoted across transitions. In `onRendererComparatorResult`, the bounded weak triple is stored **after** the original comparator returns, with renderer's existing attached-stream getter. Correlation only occurs later in `onRendererTypeStateRead` when a current live holder/renderer/stream triple and type=1/state=2 all agree.

Therefore repeated raw FALSE results with zero correlated reads **do not distinguish** comparator-before-attach (followed by invalidation) from comparator for a different holder/renderer, from stream transitions or from prefetch. Static comparator callsites and already-proven TrackWrapper→MediaPeriod→renderer chain need not be repeated. This is a narrow, testable lifetime question, not evidence of broken original playback.

## NAV27 implementation, tests, release gate

Protected NAV26 phone baseline: `backup/android-a1-nav26-phone-false-no-correlation-before-nav27-20261118` @ `2faf55dee641971c4d4e422b9e795942b4047476`. NAV27 changes only the owned observer and tests; marker `NAV_V27_COMPARATOR_ATTACH_PHASE_DISCRIMINATOR_READONLY`.

- At comparator return, classify same-triple existing engine holder, different engine tuple, or no engine link, and separately presence or absence of same already-observed attached stream.
- Immediately **before the old mandatory comparator invalidation at attach**, classify whether the pending comparator result belonged to the newly verified same holder+stream trio, a different stream, a different holder, or unscoped/ambiguous attachment. Even same-trio-before-attach is only a timing witness; it is NOT promoted to active read proof.
- Existing `TRUE/FALSE` bins, attach/detach invalidation, audio-only type1/state2 strict link, original method execution once, original return, original Yandex playback, and `CELIKOM_REPLACEMENT=NOT_CONNECTED` are unchanged. No metadata/IDs/account/content/URLs/audio leave the process; only finite counter bands.
- New bins: `COMPARATOR_AT_CALL_ENGINE_MATCH/ENGINE_OTHER/NO_ENGINE`, `COMPARATOR_AT_CALL_ATTACHED_STREAM/NO_ATTACHED_STREAM`, `COMPARATOR_CLEARED_ATTACH_SAME_TRIO/DIFFERENT_STREAM/DIFFERENT_HOLDER/UNSCOPED`. Interpret as **event-cohort lifetime counters**, not exact per-song trace or current playing track identity.
- Three additional JVM fixtures exercise timing before/after attach, same triple cleared without promotion, different holder/stream and mismatch. JVM run `#44267549038` **SUCCESS** after correcting a fixture that expected ONE for two distinct mismatch events; no production audio change made for that fixture correction.
- NAV27 code commit `e6988bb7bc73fa429d44a9e7ad0941b1ccba10cc`, CI fixture/workflow gates commit `b287492d600c8b01ac32a0401c5e61db2d9b63c1`. ARM13 publisher-first signed owner NAV27 `#44267549027` was **in progress** at this writing. Any failed earlier run is not a release candidate. Do not ask owner to install before signed CI SUCCESS + signer/publisher/hash + verified personal Library upload and readback.

## Next justified decision from NAV27 device evidence

If `COMPARATOR_CLEARED_ATTACH_SAME_TRIO` appears, a genuine before-attach identity observation may explain some lost correlations, but it cannot itself authorize replacement. If comparator is seen at-call on another engine tuple or without matching attachment, investigate current queue selected holder/generation rather than relying on `LmQ8.try` Boolean. After establishing live selected Track and queue generation, connect exactly that Track→Album→edition and renderer before contemplating the CELIKOM entitlement/resolver path.

Keep the previous signed NAV26 APK in personal Library with SHA-256 `1acd57a45dd025e144c4aaedfb43730b819806b1150eedff69274a3ae94d23a6` and all backups. No raw TXT in GitHub.
