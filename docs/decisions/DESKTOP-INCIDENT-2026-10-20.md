# Desktop incident, 20 October 2026 — investigation in progress

Owner: desktop Chrome 0.4.58 worked before Android testing; later desktop logout, silent seeks and delayed track transitions. Original 0.4.58 reinstallation did not help. Do not claim Android work was unrelated or that the entire incident is fixed.

## Live read-only evidence

Audit ca7b17a / run 39485698946: deployed backend is 0.4.54-4db00c23cfa148d62837ae0789619a80187357c6. Deployed AuthService/AuthController hashes match repository files after normalizing the fetch tool's extra trailing newline. shared/env mtime 2026-10-13T16:31:57Z. Focus assets 144530503/replacement1 v1 (180872ms, 4345176 bytes), 38436680/replacement3 v2 (268408ms, 6486945 bytes), approved/active, actual sizes match.

Three sessions of one anonymized account: original desktop created Oct13, refreshed Oct20 19:14:19.954797Z, revoked 19:14:20.490136Z; replacement desktop created19:14:31.649105Z, refreshed19:34:28.397851Z, active; other installation created16:47:27.316062Z, refreshed19:10:18.238208Z, active. The desktop revocation closely follows rotation; this supports but does not prove a stale refresh replay. No historical request logs were available in the initial audit. Do not equate temporal proximity with confirmed cause.

## Reproduced bugs and candidate 0.4.59

Unmodified .58 fails regression tests: forced PLAY/SEEK reassigns aligned currentTime; drift ticks repeatedly reassign a still-seeking decoder; delayed auth/me 401 after a completed rotation sends the old refresh token again, reproducing server session revocation. Patch skips aligned/ongoing decoder seek corrections, allows a new explicit seek, does not force a seek on PLAY/rate events, and rereads the current stored session before rotating. Manual Stop/Original and server authorization remain enforced. Active diagnostics now include decoder ready/seeking/buffered/stream state without URLs/tokens.

301 local extension checks pass. Native Chrome delayed-MP3-range regression passed in private package run 39486028350. Complete PHP/MySQL/native browser/lint/security CI 39486034765 passed. The delivered ZIP is byte-identical to the CI package; SHA256 845030134aed9d85319e90aec10e7392812f94b2013684fc6407f8cd266d2050, Library libfile_b86b1d14cfac819192e28bd1c77e3da2. Synthetic bugs are not owner acceptance. The causal chain from today's Android operations to desktop symptoms remains under investigation. Android, backend and audio files are not changed by this candidate. PR6 stays open/unmerged.

Follow-up read-only audit39486028349: only a login at19:14:31 and celikom_started at19:14:33 were recorded in the examined19:10–19:16 auth-event window; no accessible matching request-log entries were found. The historical session revocation reason is still unproven.

## Follow-up: owner rejects 0.4.59; source-only comparison

Original Yandex with CELIKOM stopped has only very brief ordinary stalls; long dropouts occur with replacement. Do not attribute the full failure to VPN or Yandex. A full live comparison in read-only run39487263627 rebuilt historical backend4db00c23: all115 packaged files match, no mismatches. This does not establish why the incident began during Android testing.

Owner's .59 trace proves PREPARING aborted twice on the same-track SEEK/readystate1 (19:50:05.342Z and07.254Z); a third attempt activated09.879Z after initial prepare02.002Z. A unit reproduction on unchanged .59 destroys the existing player and clears the operation. Candidate .60 preserves a bound preparation through temporary readyState1 and separates loading from guarded activation. It resumes only from a fresh eligible source; Stop, changed identity/media and old asynchronous completions remain fenced. Three targeted unit regressions and actual Chromium delayed-MP3/controller repeated-seek replay added. 304 extension tests PASS; actual Chromium delayed download/controller/seek replay PASS in private run39488675297; complete PHP/MySQL/browser/lint/security CI39488682900 PASS. Direct install archive run39488927148 PASS: manifest at ZIP root, downloaded artifact files exactly match pinned source2fd587c package. Owner acceptance of .60 and full incident resolution remain pending. No Android/backend/audio writes. Do not call the entire incident fixed or infer the historical session revocation cause from timing alone.
