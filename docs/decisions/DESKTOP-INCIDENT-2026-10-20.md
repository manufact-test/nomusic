# Desktop incident, 20 October 2026 — investigation in progress

Owner: desktop Chrome 0.4.58 worked before Android testing; later desktop logout, silent seeks and delayed track transitions. Original 0.4.58 reinstallation did not help. Do not claim Android work was unrelated or that the entire incident is fixed.

## Live read-only evidence

Audit ca7b17a / run 39485698946: deployed backend is 0.4.54-4db00c23cfa148d62837ae0789619a80187357c6. Deployed AuthService/AuthController hashes match repository files after normalizing the fetch tool's extra trailing newline. shared/env mtime 2026-10-13T16:31:57Z. Focus assets 144530503/replacement1 v1 (180872ms, 4345176 bytes), 38436680/replacement3 v2 (268408ms, 6486945 bytes), approved/active, actual sizes match.

Three sessions of one anonymized account: original desktop created Oct13, refreshed Oct20 19:14:19.954797Z, revoked 19:14:20.490136Z; replacement desktop created19:14:31.649105Z, refreshed19:34:28.397851Z, active; other installation created16:47:27.316062Z, refreshed19:10:18.238208Z, active. The desktop revocation closely follows rotation; this supports but does not prove a stale refresh replay. No historical request logs were available in the initial audit. Do not equate temporal proximity with confirmed cause.

## Reproduced bugs and candidate 0.4.59

Unmodified .58 fails regression tests: forced PLAY/SEEK reassigns aligned currentTime; drift ticks repeatedly reassign a still-seeking decoder; delayed auth/me 401 after a completed rotation sends the old refresh token again, reproducing server session revocation. Patch skips aligned/ongoing decoder seek corrections, allows a new explicit seek, does not force a seek on PLAY/rate events, and rereads the current stored session before rotating. Manual Stop/Original and server authorization remain enforced. Active diagnostics now include decoder ready/seeking/buffered/stream state without URLs/tokens.

301 local extension checks pass. Native Chrome delayed-MP3-range regression passed in private package run 39486028350. Complete PHP/MySQL/native browser/lint/security CI 39486034765 passed. The delivered ZIP is byte-identical to the CI package; SHA256 845030134aed9d85319e90aec10e7392812f94b2013684fc6407f8cd266d2050, Library libfile_b86b1d14cfac819192e28bd1c77e3da2. Synthetic bugs are not owner acceptance. The causal chain from today's Android operations to desktop symptoms remains under investigation. Android, backend and audio files are not changed by this candidate. PR6 stays open/unmerged.

Follow-up read-only audit39486028349: only a login at19:14:31 and celikom_started at19:14:33 were recorded in the examined19:10–19:16 auth-event window; no accessible matching request-log entries were found. The historical session revocation reason is still unproven.
