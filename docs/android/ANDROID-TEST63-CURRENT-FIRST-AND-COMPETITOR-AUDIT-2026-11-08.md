# CELIKOM Android Test.63 — current-song first; third-party method audit (2026-11-08)

## Experiment boundaries
- Based on **signed Test.62 exact compiled source** `6cc77df3a9fcc632c36975dc9fb68ffd853c5b36`.
- Isolated branch `feature/android-0385-test63-current-first-preload-20261108`, no changes to stable 0.3.92, immutable Test.50 baseline `5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1`, stable OTA, remote backend, DSP, gain, volume/fade/decoder seek or credentials.
- Test.63 only reorders current `albumProbe.publishCurrent();replacement.update(current)` before `sampleLookahead(c,item)` in `ProbeService.sample`; direct regression assertion added. Most of the existing priority protection in `ReplacementEngine.prefetchLookahead` already guarded `preparing&&!ready`, but speculative lookahead could be dispatched before current engine update in the same sampling cycle.
- Real Test.62 diagnostic `CELIKOM-combined-20261108-142613.txt`: at 66 ms next-song `replacement_lookahead_prefetch_start(106618982)` while current `123250095` resolved 200 ms and cold started 201 ms. Current transfer was thus concurrent with future-song download; Test.63 ensures the **current engine update is scheduled first**, but cannot guarantee prevention of all concurrency because asynchronous callbacks and background threads remain.
- Test.62 phone startup Media3 28 ms **one sample** (not evidence Test.62 retries improved). Live catalogue HTTP200 133 rows. 15 completion events, 14 prepares and 4 brief source-buffer episodes in newest segment. RASKOL 42884423 replacement joined at 82639 ms, but player UI pause/seek defect not proven fixed. Previous 39949113 «Дым» experienced long source buffering; original Yandex process is sole owner of underlying source buffer; no safe bypass without privileged access or player modification.

## Competitor investigation and limits
- `Hazzz895/FckCensor` uses application SDK bridge for player replacement by authoritative Track ID; not an external Android Media3 observer (e.g. `src/api/main-api.ts` `buildPlayerReplacement(trackId)`).
- `S4YN3X/FkCensor` patches desktop app ASAR, `assets/inject.js` intercepts player requests and supplies replacement URL by Track ID, so it receives private player internals unavailable to our official unmodified Android app.
- `mrvokintos/YandexMusicMod` is a desktop client fork; `ym-liberty.ts` replaces `getLocalFileDownloadInfo(trackId)` internally.
- `gagayhhad-tech/ym-liberty-android` runs own dual Web Audio elements `playerA`/`playerB` and preloads next in `app.js`. Good **general current-first/preload state machine** reference, not compatible with official-app media transport ownership.
- `aeviww/yandex-music-client` is a standalone desktop Tauri/JS HTML audio player, warm `Audio` element, not an official Android app connector.
- Do not copy injection / alternate app / WebAudio control or assume these reveal official Yandex Android UI state to another app. Public Media3 source position can be estimated from old callbacks; RASKOL pause/seek may be unobservable. Without root/Accessibility/Notification Listener, reliable UI source transport events may be fundamentally unavailable. Keep original audible and avoid speculative auto-seeks or forced controller reconnects.

## Acceptance criteria
- CI full native tests and D8 + signed separate APK: build run must be independently verified; passed CI **does not verify phone**.
- On HONOR: check startup, repeated normal next transitions, catalogue 133+ and examples of current-song join with no regression (current vs speculative prefetch). RASKOL pause/seek and «Дым» BUFFERING are **open problems**. Do not announce as fixed.
- Next safe research task: verify if any publicly exposed Yandex Android media session output delivers *fresh authoritative* pause/seek state without restricted privileges. If not, clearly communicate architecture limitation rather than keep experimenting with timer-based controller recovery.

## Signed build verified
- CI [42477357165](https://github.com/manufact-test/nomusic/actions/runs/42477357165) native host regression, D8 and APK signing PASS. Exact built source `c542b8275d2bbab200968b16dc6f0910ee6c443b` (doc commit after this).
- Separate signed test APK `CELIKOM-Android-0.3.85-TEST-63-CURRENT-FIRST-PRELOAD-SIGNED.apk`, version `0.3.85-test.63`, code `86149`, SHA-256 `75c3e18d12aee0378f954eb5f579a65afc0e094466712b2683a5b27990c81c9d`, verified original signing cert; signature v3 PASS. Artifact `CELIKOM-Test-0.3.85-test.63-code-86149`, GitHub artifact id `13615869214`.
- Phone audio/perceived speed not yet accepted; do not promote. RASKOL transport/«Дым» buffering remain OPEN.

