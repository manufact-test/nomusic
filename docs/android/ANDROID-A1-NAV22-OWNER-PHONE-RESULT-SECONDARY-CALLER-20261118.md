# CELIKOM Android A1 — NAV22 real phone confirmation (18 Nov 2026)

**Evidence:** private owner TXT `CELIKOM-A1-Diagnostics-1794950075073.txt` uploaded in conversation. Never commit its raw bytes or identifiers. The old `NAV_V21_...` marker in the rotated local-log history is **historical only**. NAV22 is proved active by the new live `NAV_V22_EXACT_SECONDARY_ATTACH_CALLER_READONLY` marker and latest in-memory exported summaries. No playback bugs were reported; user previously confirmed original Yandex's normal operation (Next, pause, seek, playback), and the only requested product functionality remains CELIKOM substitution.

## Grounded in current MAIN-process NAV22 summary

- All five 2025 native witness hooks `QUEUE_SCOPE`, `STREAM_ATTACH`, `SAMPLE_READ`, `STREAM_DETACH`, `SECONDARY_CALLER`: **REGISTERED**.
- `QUEUE_SCOPE_ENTER=NONE`, `QUEUED_HOLDER_ATTACHED=NONE`, strong scoped read-return buckets **all NONE**.
- **`SECONDARY_CALLER_ENTER=MANY`, `SECONDARY_CALLER_STREAM_MATCH=MANY`, `UNSCOPED_ATTACH_SECONDARY_MATCH=MANY`**. This is the first real-device proof that the exact `androidx.media3.exoplayer.b.super(LlQ8;[LSr4;LR29;ZZJJLSl6$b;)V` path drives a same-Java-reference stream into the native renderer attach.
- `SECONDARY_CALLER_STREAM_DIFFERENT=NONE`, `UNSCOPED_ATTACH_SECONDARY_DIFFERENT=NONE`, `UNSCOPED_ATTACH_OUTSIDE_SECONDARY=NONE`, `STREAM_REATTACH_TRANSITION=NONE`. No observed stream conflict or outside-secondary attach in this sampled process.
- `UNSCOPED_ATTACHED_STREAM_READ_MATCH=MANY`, `UNSCOPED_ATTACHED_STREAM_READ_DIFFERENT=NONE`, `READ_NO_MATCHED_ATTACHMENT=NONE`, `READ_RETURN_LINK_LOST=NONE`. Linked renderer then invokes original `b.g` on the same attached stream, preserving the live alias route.
- `UNSCOPED_READ_RETURN_MINUS4=MANY`, `MINUS5=MANY`, `MINUS3=MANY`, `OTHER=NONE` after original method returns. These are the known Exo-style result codes, **not evidence of audible track contents** without checking buffer flags and the actual audio output. Counts are finite coarse categories, not exact calls.
- `RENDERER_DETACHED=MANY`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. Separately `EXO_FACTORY_CREATED/EXO_OPEN_OK/EXO_READ_POSITIVE=MANY`, `EXO_IO_FAILURE=NONE`.
- `CELIKOM_REPLACEMENT=NOT_CONNECTED`, as designed. `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/MANY` is exception-constructor observation, **not** a reliable crash report. Android exit history has older/USER_REQUESTED categories, not current proof of a playback failure.

**Proved route:** exact 2025 `b.super` secondary caller → `b.package` attaches the **same** `LR29` object → original `b.g` reads that attachment with same renderer/stream identity. This is **stronger** than NAV21's unscoped observations: we now know the caller source. **Not proved:** the exact currently selected audio track/album/edition, distinction from prefetched media/video renderer, connection to decoded audible output, CELIKOM replacement route. Do not enable Stage B yet.

## Next evidence-based technical work

Perform a narrow **signed 2025.10.4 private static DEX audit** of `b.super` and its real direct callers/argument propagation, before adding another runtime hook. This can establish what drives the confirmed active secondary path. Remain source/identity-only; do not inspect audio, account data or user IDs, and do not change published Yandex, Test.50, Windows, extension, server, Android app architecture, or working audio controls. If static scan identifies a meaningful bridge to a currently selected media item/period, design minimal read-only linkage plus JVM test, owner signing and Library delivery; never infer it from code shape alone.

**Protected snapshot:** `backup/android-a1-nav22-owner-signed-library-verified-final-20261117` points to documentation-era NAV22 (signed code commit `50078f012a57b7fc13060c3205f2757b4a2894a7`, native CI #44174172281 SUCCESS, JVM #44174039648 SUCCESS). Owner-signed NAV22 APK remains in personal Library with SHA-256 `06e7dd168f82db2052d8421a050c5d2bf22f12ff250918d4bd943e7b1cdebf86`. No new app binary produced by the phone TXT analysis itself.


## Confirmed next static source boundary (18 Nov, signed CI)

Signed isolated six-DEX scanner `secondary_renderer_attach_caller_owner_exact.py`, with pinned original XAPK SHA/signatures and failed-closed tests, completed **CI #44179047340 SUCCESS** and detailed holder inspection **CI #44179471641 SUCCESS**. The earlier scan for only `b.super`-declared invokes returned 0 correctly: caller invokes through exact renderer interface `k.super`. Including the interface produced **exactly two real invoke sites** from `Landroidx/media3/exoplayer/e;.catch(Lxh6;IZJ)V` at PC **131 and 144**.

Inside this exact engine method, `Lxh6;` holder is the *actual method argument* (input register 19). It reads a typed `Lxh6;.[LR29;` stream-array field at PC **67**, accesses the array at PC **69**, reads a `Lxh6;.Lyh6;` period-reference at PC **73**, and obtains `Lyh6;.LSl6$b;` at PC **101**. These are source-language-free exact DEX method/field types, not a claim that the current audio track is known. The two downstream `k.super` invocations share full descriptor `(LlQ8;[LSr4;LR29;ZZJJLSl6$b;)V`. The inherited `b.super` then calls `b.package` at PC 27. NAV22 handset confirms this latter attach → renderer read works.

**Next bounded NAV23 witness idea:** observe `e.catch` holder lifetime and, specifically at existing `b.super` attachment, compare the original stream reference against this holder's exact typed `[LR29` elements **by Java reference equality only**, and retain separate counters for engine-holder linked reads. The per-holder array match is the gate; mere nested method timing cannot count as proven holder-to-stream identity. Preserve legacy `QUEUE_SCOPE` and `UNSCOPED` counters separately. Do not confuse this with an actual selected audible track or enable Stage B yet.
