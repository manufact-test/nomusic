# CELIKOM Android A1 — NAV23 owner real-phone engine holder match (18 Nov 2026)

**Private evidence:** user-supplied `CELIKOM-A1-Diagnostics-1794952135309.txt` received and analyzed directly in conversation. **Do not copy, commit, or upload the raw TXT**. Local-file rotation contains historical NAV22 records. The current, explicitly exported `DIAGNOSTIC_BUILD=NAV_V23_EXACT_ENGINE_HOLDER_STREAM_ARRAY_READONLY;ACTIVE` and the last compact in-process counter block are authoritative.

## Device facts from NAV23 (not claims of audible track identity)

- All **six** exact-2025 original clone-native hooks REGISTERED: `QUEUE_SCOPE`, `STREAM_ATTACH`, `SAMPLE_READ`, `STREAM_DETACH`, `SECONDARY_CALLER`, **`ENGINE_HOLDER_SCOPE`**.
- `ENGINE_HOLDER_SCOPE_ENTER=MANY`; **`ENGINE_HOLDER_STREAM_ARRAY_MATCH=MANY`**, `DIFFERENT=NONE`, `UNAVAILABLE=NONE`. Crucially, at real renderer attach, the same exact Java `LR29` stream reference is a member of the original native `Lxh6` media-period holder's **`[LR29` stream array** while original `e.catch → k.super → b.package` frames are jointly active.
- **`ENGINE_HOLDER_READ_RETURN_MINUS4=MANY`, `MINUS5=FEW`, `MINUS3=MANY`, `OTHER=NONE`**. These are original untouched `b.g` return codes on the same renderer+stream while the independently matched holder/stream link is still present. They are not byte/PCM or audible evidence; `-4` can be EOS.
- `SECONDARY_CALLER_ENTER=MANY`, `SECONDARY_CALLER_STREAM_MATCH=MANY`, `UNSCOPED_ATTACH_SECONDARY_MATCH=MANY`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH=MANY`, `READ_RETURN_LINK_LOST=NONE`, no differing or unmatched reference category.
- The **older helper** `QUEUE_SCOPE_ENTER=NONE`, `QUEUED_HOLDER_ATTACHED=NONE`, strong `QUEUE_SCOPED_READ_RETURN_*=NONE`. This is not a NAV23 regression: the alternate engine-holder path is demonstrably active and working as observed; previous NAV21/22 also mostly lacked this specific queue-scope callback.
- `IDENTITY_STATUS=STRUCTURAL_ONLY`, `AUDIO_STAGE_B_STATUS:CELIKOM_REPLACEMENT=NOT_CONNECTED`. No CELIKOM audio substitution and no proof of *current audible selected* track, edition, album, rights or decoded audio.
- `EXO_FACTORY_CREATED/EXO_OPEN_OK/EXO_READ_POSITIVE=MANY`, `EXO_IO_FAILURE=NONE`. These are separately scoped Exo source observations, **not same-trace track→holder equality**.
- `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/MANY` is only observed exception constructor events; no owner-reported playback issue or confirmed Java crash accompanying this file. Rotated previous process exits are not current crash proof. Owner has previously confirmed ordinary Yandex playback, Next, pause, seek working.

## Exact proven result / next bounded investigation

**NAV23 closes runtime `e.catch(Lxh6 holder) → holder.[LR29 contains same stream → k.super/b.package attaches → b.g reads/returns`** by in-process Java object reference equality. This is stronger than NAV22's caller-only match.

**The remaining gate is identifying which native `Lxh6` holder is actually selected for the currently heard track, and whether linked renderer is an audio decoder rather than video/prefetch.** Do a bounded signed original 2025.10.4 *static* callsite audit first: find exact callers/arguments into `e.catch(Lxh6;IZJ)V` and relationship to engine active holder field `h.SLOT_B`; distinguish playback activation from preparation, and seek/Next transitions. Avoid repeated generic scans, sound handling or metadata reads. Only if signed proof yields an exact new runtime observation boundary should a privacy-bounded passive NAV24 hook be considered. No new APK solely from today's log; no modifications to original Yandex, Test.50, Windows, browser, backend or current CELIKOM service.

**Protected code**: `backup/android-a1-nav23-owner-signed-library-verified-final-20261118` @ `3c2146092e29e58d32415e3a43a2c431e896bc60`, signed APK source `b53af8291c38ac9e7141a186bb48ab682eb30e25`, CI native #44180557905 SUCCESS, JVM #44180395176 SUCCESS; Library signed owner NAV23 APK SHA-256 `376d3212a3802cf40e905eb434699d6999202086129eb9affc0c66bd4f8ea6a8`. NAV23 remains installed; no new owner test requested yet.

## Additional exact signed 2025 static proof after NAV23 phone success

Auditor `android/native-yandex-hooklab/ci/secondary_renderer_attach_caller_owner_exact.py` on the pinned publisher-signed original XAPK (16 original splits, six DEX) independently establishes **three exact direct invocations of `e.catch(Lxh6;IZJ)V`**:
- `e.break()V` PC **510** — holder input exists but is **not strictly traced to queue SLOT_B** by the current exact proof. Do **not** generalize to this path.
- `e.break()V` PC **1183** — strict `h.SLOT_B Lxh6` field read at PC **1051**.
- `e.class([ZJ)V` PC **51** — strict same DEX `h.SLOT_B Lxh6` field read at PC **2**.

**Final bounded branch-sensitive CFG, domination + alias verifier: #44185115155 SUCCESS, source commit `2fd5b5d8ee6fef997079c92966eac30a21467b6c`.** For `e.break 1051→1183` and `e.class 2→51`:
- Same *exact field ID* as independently proved `e.break PC547` `h.SLOT_B`, not only a matching `Lxh6` type;
- source read dominates target invocation (no bypass path found);
- **1/1 reaching CFG state** has the same source object in the `e.catch` holder argument;
- no unmodeled instructions in bounded region;
- still **static only**, no proof that this is the currently audible audio decoder or track/album/edition.

This dovetails with NAV23's real-phone same-holder array membership and renderer return observations but **does not establish live queue slot B equality at the moment of sound output**. `e.class` may participate in stream reset/reconfiguration; `e.break` PC510 may be an alternate path. Existing selected-track/album Stage B counters `WRAPPER_MAIN_SOURCE` and `TRACK_SOURCE_READ_LINK` remain `NONE`. No native APK, app behavior, music files or server was changed by this scan. Continue with exact 2025 audio-only renderer `getTrackType()/started` and live selected-holder discriminator only after verifying signature/field origin in bounded signed research, without metadata or audio contents capture.

**Static safety checkpoint:** `2fd5b5d8ee6fef997079c92966eac30a21467b6c` (followed by documentation-only changes), isolated source scan #44185115155 SUCCESS. NAV23 owner APK and signed release backup unchanged.
