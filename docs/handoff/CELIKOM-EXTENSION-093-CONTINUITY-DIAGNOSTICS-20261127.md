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

The initial remote commit a83c2717a5ed042cc728d1552c0256fe9c966cca contained an output-transfer truncation marker inside replacement-player.ts, despite the local source/tests being intact. Its build correctly failed before private staging. Commit eb70ee35d1be68b5dd5842d4fe6821c68ee487d0 restores the full file. Every changed blob was independently compared with git hash-object of the locally tested source; the only mismatch was that transferred file, and its repaired remote blob now matches too. No broken package was approved or delivered. Future tool-mediated file transfers must be chunked and blob-verified, not accepted merely because JSON parsing succeeds.

## Verified private delivery

- Exact corrected build source: `eb70ee35d1be68b5dd5842d4fe6821c68ee487d0`; Floki run `45992977800`, attempt 1.
- Server tests: 457 passed. Build, security, checksum and private spool steps passed.
- The independent native Chromium media gate remains **failed**, specifically `actual MP3 MSE plays` in `scripts/test-audio-gain-browser.mjs`. M4A fixture was reached before it. This is not a green browser/audio result, and its cause is not established by this release. The user previously authorized private candidate delivery without endlessly repairing the headless environment. Do not claim all acoustic defects fixed or customer acceptance.
- Independent trusted root-owned spool/ZIP verification: administrative run `45993126623`, SUCCESS.
- Filename: `celikom-extension-0.4.93.zip`; size **2,504,603 bytes**.
- SHA-256: `c97ec42c4317a33fc7cd390443a72feacf12c6f17efc6393db8d532e5bfb1de8`.
- Exact metadata approved in the existing owner-only manifest; public_stable remains null.
- Final publication, trusted receipt and full HTTPS verification: administrative run `45993261733`, SUCCESS. Existing trusted consumer verified versioned/latest anonymous 401 and authorized 200, full size and digest. Current owner receipt exactly matches version/source/run/attempt/hash.
- Explicit mirror service start returned 1 again, but the independently loaded trusted approval exactly matched the intended 0.4.93 approval and existing owner consumer publication/HTTPS verification succeeded. No unrelated mirror or branch repair.
- Verified private download: https://celikom.com/downloads/extension/celikom-extension-0.4.93.zip
- Maintenance request reset to harmless no-op in `5b69fbfb77b3fb1e30809b577ac0468c24db4e44`.

Owner installation: replace contents of the existing unpacked folder, reload that extension, reload the Yandex tab, and confirm 0.4.93 in the next diagnostic. Listen through initial Start, mid-song reload/adoption, pause/resume, seek, track changes while VPN connects and steady playback. Export diagnostics promptly after a gap, before reloading: retained context survives song changes but not document reload. No Android/Windows/server-auth changes and no customer release.
