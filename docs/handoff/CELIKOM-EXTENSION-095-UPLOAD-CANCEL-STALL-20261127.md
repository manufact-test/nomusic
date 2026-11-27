# Extension 0.4.95 — stalled upload, real cancellation and retained failure

27 November 2026. Private owner candidate only.

Owner explicitly authorized fixing findings from `Вставленный текст(20261127-202937).txt` after the prior analysis recorded them in the 0.4.94 handoff. Two real incidents: track 128750389 crawled to 13% and was cancelled at 65 s, then uploaded in 1.68 s; track 115444644 stopped at 3% and failed network_error/status 0 at 30.2 s, then uploaded in 1.596 s. Read-only audit 46064319037 confirmed successful retry application statuses 202/552 ms and 202/453 ms. Exact intermittent transport cause remains unproven; no VPN, TLS, HTTP2 or server changes are justified by that log.

## Corrections

- Offscreen and direct transfer watchdogs now observe actual increases in sent bytes for the whole request body. A 15-second idle warning preserves existing progress; a partial transfer with no byte progress for 30 seconds stops as stalled. Before first bytes the existing 45-second admission bound remains. Continuing byte progress resets the deadline even if its percentage is unchanged. Once request body is sent, normal server response timeout applies independently; no false stall abort during server processing. POST is never automatically replayed.
- Each offscreen transfer owns its cancellation signal and XHR. Cancellation races pending configuration fetch/JSON, staged-file read and connecting status; checks fence the send. A cancelled preparation cannot later POST. Cancellation acknowledgment waits for cleanup, and an immediate explicit new begin waits for the cancelled operation to finish. Final status is published after staged-file cleanup so the UI cannot enable retry before old staging is removed. Late preparation/config/old progress callbacks cannot activate or overwrite a newer operation. Duplicate delivery of an already active same-ID command acknowledges existing work without starting another POST.
- Terminal progress retains exact percentage and bytes rather than a decile/zero. Waiting preserves partial progress. Cancelling direct fallback is journaled as cancelled.
- Explicitly reopening the upload form recovers the saved failed/cancelled attempt for that track (bounded to 24 hours), with failure category and attempt code. Background polling does not forcibly reopen a closed panel or restore historical success. Fresh server pending/approved status remains authoritative and wins over a historical failure; user-selected new files are protected. No credentials, filename or file content are added to diagnostic storage.

468 extension tests pass, including new pending-config/file cancel races, cleanup barrier, immediate explicit retry, partial-transfer idle cutoff, byte-progress heartbeat despite unchanged percent, independent server wait, command-delivery idempotence and recoverable failure UI with server-state precedence. Existing 0.4.94 MP3 preparation and ordinary/background prepared Blob regressions pass. Full ZIP build, manifest, security and whitespace checks are required for delivery.

Scope: extension upload worker, popup, tests, version and documentation. Playback engine behavior, MP3 normalization/decoder, backend authentication, Android and Windows are unchanged. No customer publication. Do not present the unknown underlying network condition as fixed; the reproduced extension failures and their handling are corrected.

Exact private spool and HTTPS delivery evidence will be appended after independent verification through the existing owner channel. Native browser/listening gate is separate and must not be claimed passed if unavailable or failed.

## Verified private owner delivery

- Upload correction source: `01401c064554904e5c676231655e1ef667a29d8d`. Exact build source `6684c937e56b6a8dc6fb8dffcddab99f19c88a9a`; Floki extension run `46066362165`, attempt 1.
- Initial extension run 46066259828 was assigned to ci02 without any started steps. Existing trigger file requested the next available runner once; ci01 ran the exact build. No runner or Chrome infrastructure repair.
- Server tests: 468 passed. ZIP build, manifest, security, checksum and private staging passed. All 11 changed source/document blobs were independently matched to the locally tested git hash-object before main was advanced.
- Independent root-owned consumer spool/ZIP validation: administrative run `46066449872`, job `140732804128`, SUCCESS.
- Filename `celikom-extension-0.4.95.zip`, **2,505,631 bytes**.
- SHA256 `ef0ddd9f1e0cfc5e2649ad360c2ae82b8ec8af815249e28150e68f412be05a40`.
- Approved exact metadata in existing owner-only manifest; public_stable remains null.
- Final trusted receipt, publication and versioned/latest complete HTTPS download verification: administrative run `46066560798`, job `140733173799`, SUCCESS. Anonymous 401 / authorized 200; full size/digest and exact version/source/run/attempt receipt matched.
- Mirror service invocation returned 1 again; exact trusted approval was independently matched and existing consumer publication/HTTPS verification succeeded. No unrelated branch/mirror changes.
- Verified private download: https://celikom.com/downloads/extension/celikom-extension-0.4.95.zip
- Maintenance request reset to harmless no-op in `e2f8d81b64455478fbb2ad195f3b47322974c69d`.

At final owner-download verification, the separate native Chromium media gate was still `in_progress`; it is not counted as passed or real owner listening acceptance. Private delivery follows the owner's previously authorized separation from prolonged headless work. The current task changes upload handling only; native/playback engines were not changed.

Owner should update the existing unpacked extension, then try normal upload, Cancel followed by retry, and closing/reopening the popup after a failed attempt. Save diagnostics if slow transmission recurs. A genuinely interrupted connection can still produce a visible failed upload; no unsupported claim is made that the underlying network condition has disappeared. Existing 0.4.94 prepared MP3 behavior remains covered.
