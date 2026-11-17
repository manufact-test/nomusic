# CELIKOM Android A1 — NAV20 actual owner-phone diagnostics and bounded NAV21 queue-scoped read-result probe (17 November 2026)

This report supersedes the previous **await NAV20 owner TXT** state. Owner supplied private `CELIKOM-A1-Diagnostics-1794937292351.txt`; do not upload the TXT or its contents to GitHub.

## What actually happened on the owner handset (NAV20)

- Two exported build markers confirm `NAV_V20_RENDERER_READ_RESULT_READONLY;ACTIVE`, including the new explicit export marker. All four installed renderer hooks (QUEUE_SCOPE, STREAM_ATTACH, SAMPLE_READ, STREAM_DETACH) report `REGISTERED`.
- **Critical improvement over NAV19:** `QUEUE_SCOPE_ENTER=MANY` (NAV19 NONE); `QUEUED_HOLDER_ATTACHED=ONE` (NAV19 NONE), `ATTACHED_STREAM_READ_MATCH=FEW` (NAV19 NONE). An actual *queue-holder scoped same-renderer stream link* was witnessed at read-method entry. No `ATTACHED_STREAM_READ_DIFFERENT` or `READ_NO_MATCHED_ATTACHMENT` observed.
- Weak/unscoped connections still occur: `UNSCOPED_ATTACH=FEW`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH=MANY`, `UNSCOPED_ATTACHED_STREAM_READ_DIFFERENT=NONE`, `RENDERER_DETACHED=FEW`. A weak alias must not be promoted to queue-scoped proof.
- Across both strict and weak cohorts **combined**, original `b.g(iA9,RF2,int)` returned `-4=MANY`, `-5=FEW`, `-3=FEW`, `OTHER=NONE`, `READ_RETURN_LINK_LOST=NONE`. These are **actual untouched return ints after the original read method completed**, and no recorded reference mismatches. `-4` is Exo buffer result including possible EOS and does NOT by itself prove actual sample bytes, decoder/AudioTrack output, the currently audible renderer or a specific selected song/edition.
- Other Exo activity includes `EXO_OPEN_OK=MANY`, `EXO_READ_POSITIVE=MANY`, `EXO_IO_FAILURE=NONE`. **No strict object link from current selected track/album/edition to audible renderer yet.**
- **Stage B substitution is STILL NO-GO:** `AUDIO_STAGE_B_STATUS;CELIKOM_REPLACEMENT=NOT_CONNECTED`. Stage A NAV17 (original Yandex audio/login/UI) previously owner-accepted; we did not change playback architecture.
- `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/FEW` for current NAV20 process, but existing retained log still has many old MUSIC_APP exception-constructor entries and `LOG_TRIMMED`. This is persistent prior log history, not proof that NAV20 continued to log hundreds in its new process. Process exit categories OTHER/USER_REQUESTED appeared, no explicit JAVA_CRASH line in this TXT; no new crash cause established.

## NAV21 bounded diagnostic-only patch (same sole working branch)

Owner's NAV20 evidence proves `-4=MANY` **in combined strong+weak return categories**. It cannot show how many successful read returns came from the single strict `QUEUED_HOLDER_ATTACHED` stream. That is the precise unresolved gate.

Pre-code exact branch backup: `backup/android-a1-nav20-owner-strong-read-before-nav21-20261117`. On `experiment/android-a1-metrica-init-state-observer-arm13-20261112`:

1. `NativeRendererStreamEvidence.java`: retain NAV20 aggregate `STREAM_ALIASED_READ_RETURN_*` and add isolated `QUEUE_SCOPED_READ_RETURN_MINUS4/MINUS5/MINUS3/OTHER` vs `UNSCOPED_READ_RETURN_MINUS4/MINUS5/MINUS3/OTHER`. Queue-scoped category only when the *same renderer+stream+non-null queue holder weak reference* still exists at post-`chain.proceed()` callback; unscoped link can never count for strong. Original read result is not modified.
2. Regression tests reject stale strong links after detach or same-renderer unscoped reattachment; confirm strong, weak and aggregate counts each remain independently consistent.
3. `ExitCallsiteWitness.java` diagnostic marker `NAV_V21_QUEUE_SCOPED_READ_RETURN_READONLY` only. Original native queue/attach/read/detach hooks and single `chain.proceed()` unchanged; no sound/metadata buffers, tokens, IDs, URLs or track names are read or emitted.
4. Exact JVM checks and full publisher-first native ARM13 + matched owner certificate signed export reused, with new one-shot NAV21 workflow. Java model checks green **#44140534551 SUCCESS**. Signed owner export run **#44140575566** started, but not claimed delivered until CI + APK verified in user's ChatGPT Library.

**Next evidence gate:** if `QUEUE_SCOPED_READ_RETURN_MINUS4` is nonzero, this establishes a strict queue-holder-attached stream whose original `b.g` returned -4 in owner playback. Still not proof of audible samples, selected edition or CELIKOM replacement. If NONE, follow precise cause: strict link only captured early reads with -3/-5, or return occurred after an unscoped reattachment. Next changes, if any, require actual NAV21 owner data before adding output hooks or modifying player behavior.

**Safety:** No new player, backend, Windows, extension, Test.50 or original publisher changes; no user app install/uninstall/data clear by automation. Never use 2026.10.3 obfuscated HookSpec for the original embedded Yandex 2025.10.4. NAV17–NAV20 owner-installed builds remain protected in Library.