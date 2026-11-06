# CELIKOM Android Test.51 — forensic transport audit, 2026-11-07

**Status: evidence boundary identified; universal Pause/Seek fix NOT demonstrated; no APK generated.**
This investigation is **documentation-only** on `feature/android-0385-test51-transport-controls-investigation-20261107`. Do not promote to stable, change acoustic joins, or claim an owner-verified fix.

## Exact immutable baseline verified through GitHub

- Golden source commit: `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`; tree `bbdf43d78e04c6dc4562c5b0541049283f9109b0`.
- Golden backup ref `backup/android-test50-exact-source-owner-accepted-20261106` independently resolves to that exact commit and tree.
- Before this report, current investigation branch HEAD `029d809143aa661dd1c039b91554ad35fe36b2f6` was exactly three commits ahead of golden, all changes confined to five documentation files. Android Java, tests, build scripts, test APK metadata and accepted audio transport matched golden.
- Owner-approved signed APK remains `0.3.85-test.50`, `pro.celikom.nativeprobe.test`, code 86135, SHA-256 `aadedff2051cd40e96641cff1be831aa3a6a79c3938c2b849837b3e880b511d1`.
- Stable Android 0.3.92, PC extension, server, auth, Hostinger and backup refs not touched.

## Historical trace: separate the Yandex UI from visible Media3 and native decoder

The owner reports that on certain Yandex source items seeking or pressing Pause can appear delayed for tens of seconds while CELIKOM replacement audio continues. Neither the standalone Android service nor public Media3 exposes a timestamp of the user's finger touching Yandex's UI. A post-publication decoder ACK is **not** UI-to-sound latency.

### Test.31 RASKOL source edition (older trace; not Test.50)

Private source: `CELIKOM-combined-20261104-222444.txt`, third Test.31 run after line 1996; screen recording described in `ANDROID-0385-TEST31-OWNER-REJECTED-FORENSIC-2026-11-04.md`. **Do not commit the raw diagnostic or private video.**

- Source track: `Нас не понимают вообще`, artist `Космонавты, RASKOL`, Yandex album ID `5685525`, catalog track ID `42884423`, duration `232330ms`, ephemeral Media3 alias `64`. A different-album recording is **not yet identified or verified**.
- While the Yandex UI already displayed about `2:11` in the owner's video, a corresponding public Media3 sample at elapsed `112512ms` still reported source position `50943ms`; at `114816ms` it reported `53250ms`. Native seeks during the stale-position interval target what Media3 published, not the Yandex UI's unobservable pending seek.
- At elapsed `116861ms`, a valid source position of `134392ms` reached CELIKOM. `replacement_hot_cached_seek_request` was issued then, the MediaPlayer ACK arrived at `116915ms` (**54ms**), and complete at `116919ms`. A later request at `120982ms` reached ACK in **44ms**.
- No same-item source discontinuity event was logged in the stalled interval. The evidence supports a delay **before** new target publication to the observer, not a 30-second native MediaPlayer seek. It does not prove *why* the source delayed publication or whether Yandex itself was buffering.

### Test.50 «Дым» source edition (the accepted baseline)

Private source: `CELIKOM-combined-20261106-235245.txt`, third/Test.50 run starting line 3665.

- Source: `Дым` by `Лёша Свик`, Yandex album ID `5281614`, catalogue track ID `39949113`, duration `219660ms`, ephemeral alias `77`. Different-album variants remain unverified.
- Actual CELIKOM replacement prepared at `111232ms`, and `replacement_transition_complete` at `111497ms`; it was NOT an original-only false positive. At elapsed `116914ms`, the published target `119179ms` produced `replacement_hot_cached_seek_request` against the verified local cache.
- Native seek ACK at elapsed `116959ms`, reported `callbackElapsedMs=46`; `replacement_hot_cached_seek_complete` at `116964ms` also reports 46ms. At elapsed `118190ms`, source position was `120452ms` with `sourcePlaying=true` and replacement armed/ready.
- There is **no measured UI finger timestamp**, no confirmed 30-second seek stall, and **no user Pause test** on this Test.50 item in this segment. A successful native seek cannot establish whether the original reported defect persists on this or a different album edition.
- No Test.50 RASKOL occurrence confirmed; earlier occurrences in the combined Test.48/Test.49 runs must not be confused with the Test.50 segment.

## Source review: deterministic state/ownership boundaries

- `ProbeService.java`: read-only official Yandex Media3 `MediaController`; listener `onPositionDiscontinuity` forwards a current-item, current-position `SEEK` via `Media3SourceRouter`. Polls current source snapshot around every 250ms and calls `ReplacementEngine.update()`. A service cannot observe Yandex UI touch or a hidden uncommitted seek target.
- `SourceEventArbiter.java`, `SourceTransitionGate.java`: intentionally reject stale or different-track callbacks and only forward a seek event when the live current position matches the event within 2000ms. **No historical evidence** in the examined Test.31/Test.50 files shows a suppressed valid seek (`source_seek_event_ignored`) for these cases; do not relax generation/identity safety without proof.
- `ReplacementEngine.java`: the `update(s)` path immediately invokes `pauseSource()` when an authenticated, current PlaybackSource reports genuine not-playing state; `pauseSource()` silences and pauses the secondary decoder synchronously before delayed source-gain restoration. Known `STATE_BUFFERING + playWhenReady` is intentionally distinguished from deliberate user Pause; a 300ms short-buffer hold exists, **not** a 30-second pause timer. Source position jumps are converted into hot cached seek or owned silent alignment seek; verified cached seeks require valid effect, identity and local data.
- `AudioOwnership.java`: one owner, verified audio effect and account/track epoch. Decoder seek completion is single-flight; stale callbacks cannot grant output. `seek()` and `completeSeek()` are protected by `tests/check_0385_seek_baseline.py` SHA-256 regression contracts and are untouched.
- `BufferedAudio.java`: HTTP Range starvation may delay a **native** seek once issued, but **cannot account** for the RASKOL interval where no correct target was yet visible. Avoid speculative changes to Range sizes or prefetch.
- `ProbeService.connectLegacyPosition()` and `LegacySourcePositionPolicy` already attempt an independent passive platform MediaBrowser snapshot with strict title/artist/duration/playing agreement. No `source_seek_platform_recovered` appears in examined Test.50 log; do not assume this supplies the UI position.
- A short-lived second Media3 controller was explored in earlier Test.40 work; failure can quarantine working playback and it is not an accepted universal transport source. `AudioManager.AudioPlaybackCallback` counts active media devices but does not authorize decoding another app's source position or exact Pause intent.
- `SourceStateWatchdog` may reconnect after a quiet `STATE_BUFFERING` snapshot; **no** `source_controller_refresh` was found in examined Test.31/Test.50 logs. This is not a demonstrated cause and is **not** modified.

## What remains unknown; one focused owner test rather than speculative patches

1. With the exact same album and source item, compare official Yandex with CELIKOM **OFF** and **ON**; separately test a known-good track. Record whether Yandex's own original audio/UI Pause and Seek immediately respond when CELIKOM is OFF.
2. On an affected item with replacement actually active, capture one short **screen recording** containing a visible Pause press and finger seek, together with the existing combined diagnostic. Prefer RASKOL album `5685525` and «Дым» album `5281614` plus one affected **different album** variant; record the real track/album IDs via existing diagnostics rather than title-only matching. No new broad permissions/root/modified Yandex required.
3. Correlate (a) visible gesture timestamp and Yandex UI, (b) Media3 `getPlayWhenReady/isPlaying/STATE_BUFFERING` and `onPositionDiscontinuity` publication, (c) CELIKOM `replacement_pause` / `replacement_seek_request`, (d) decoder ACK and audible output.
4. **If** a real Pause is already visible in the public Media3 snapshot but CELIKOM keeps audibly playing beyond a tick, or a correct new position appears but no seek is issued, that demonstrates a fixable CELIKOM state/command defect. Implement a narrowly scoped Test.51 code fix and regression on this branch.
5. **If** Yandex itself fails to publish Pause/Seek or delays committing it until source buffering ends, no permissionless standalone companion can accurately infer an unseen target from the UI. Do not add a hidden transport controller, Accessibility/NotificationListener, injected APK, speculative audio restart or per-track exception. Report upstream product/API limitation instead.

## Test/build gate (not falsely declared PASS)

- **Static code audit complete** for controller, source arbiter, snapshot, ownership, pause, buffering, cached/range seek and historical reports.
- **No Java source, audio, tests, signing or CI workflow has been changed**. Therefore no new host/CI run or Test.51 signed APK exists. Test.50 is still the sole owner-accepted audio candidate.
- When a causal fix is demonstrated, add a deterministic regression for the observed command/state trace; require existing complete `run_engine.py`, `run_addon_host.py`, frozen seek SHA tests, Android API 36 compile/D8, isolated package and signing verification, Test.50 lookahead/deferred-next, Next/shuffle, route/pause, original fallback, source-effect retention, no stable publish. Update CI branch allowlists and the signed-build test branch gate **only for the Test.51 branch** at that time, leaving Test.50 production and backups untouched.
- CI alone never proves real HONOR acoustic acceptance or prompt response of Yandex's app UI.
