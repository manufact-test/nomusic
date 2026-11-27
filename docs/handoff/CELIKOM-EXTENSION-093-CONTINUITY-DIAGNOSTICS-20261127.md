# Extension 0.4.93 — continuous drift correction and retained interruption diagnostics

27 November 2026. Private owner candidate; no customer release or listening acceptance.

The owner now authorized the previously deferred VPN interruption and diagnostic expansion together with subsequent dropouts. Latest input `Вставленный текст(20261127-112826).txt` still identifies extension/bridge 0.4.91. It does not test the already delivered 0.4.92 transport correction. Preserve that correction in this candidate.

The latest trace contains a routine decoder seek during running playback (track 78608850, around six seconds, replacement readyState drops to 1 while native continues). The existing synchronizer seeks once drift exceeds 350 ms. A decoder seek can interrupt the current audio even when the file is buffered. This is a concrete avoidable interruption mechanism; the log alone does not prove the exact duration or acoustic cause of every reported gap. Most retained restores in that input coincide with natural song endings; do not label all of them VPN failures or silence.

For an already playing, ready real replacement, ordinary drift between 350 and 1200 ms now uses bounded 4% speed correction relative to the user's selected speed. Correction ends within 80 ms. Explicit seeks, large mismatches and synthetic looping assets retain decoder repositioning. Pause, buffering, pending seeks and initial alignment cannot enter rate correction. Default browser pitch preservation is retained. No extra original-audio mute or tail holding was introduced.

Diagnostics now keep a bounded isolated-world timeline (180 entries, stable samples at most once per five seconds, state changes recorded immediately), 24 interruption contexts with the preceding 20 entries and decoder/stream state, and 48 startup/restore records. Replacement diagnostics include 64 media events (waiting, stalled, seeking, seeked, playing, pause, ended, error), rate and buffering. Interruption context is captured before decoder disposal and remains available after changing songs. Ordinary track transitions, natural endings, controls and interruption candidates are classified separately. Browser online/offline and available connection-change hints are recorded; these are not proof of a specific VPN toggle.

History scope is the current document and is explicitly marked in export; reload history is not persisted. No URLs, credentials, tokens or audio are added to the timeline. It is generated in the isolated controller and only exported on diagnostics request; the MAIN bridge's existing 48-entry live snapshot remains unchanged to avoid making normal playback messages larger.

0.4.92 exact-range transport retries, manual Stop/Original, subscription/access boundaries, binding fences, expiry handling, upload/proposal flow and private release policy are retained. Android, Windows and server authorization are outside this change.

Validation and exact private delivery evidence will be appended after checks and publication through the established owner-only pipeline. Work cannot independently install/listen to this unpacked extension in the cloud browser as already documented; do not represent automated tests as real listening acceptance.

## Local validation

457 extension tests passed, including new regression coverage for a running half-second drift, rate correction convergence without any decoder seek, selected playback speed, stop/pause/buffering boundaries, explicit/new seeks, retained pre-teardown context, bounded sampling and normal track-change classification. Running the eight focused seek tests against the unchanged 0.4.92 synchronizer produces five failures (including the added correction instrumentation); the current implementation passes them. Full ZIP build, production manifest validation, security gate and diff whitespace checks passed. Real Yandex listening remains unverified.
