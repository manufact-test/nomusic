# Extension 0.4.94 — automatic preparation of the owner's MP3

27 November 2026. Private owner candidate only, no customer publication.

Owner reported the pre-upload duration error for track 132599807 and supplied `baby-melo-orvi_(ru.livemuz.com).mp3`. Screenshot alone was insufficient; analysis uses the actual original file, 5,710,365 bytes, SHA256 ea242a328ed666c6cfcccedd43875afd9370f11ab6b55cd813b0162fd941610b. Do not commit that audio to Git.

0.4.93 inspectMp3 rejects it reproducibly. After 5,464 complete MPEG frames, the final MPEG-1 Layer III frame has padding bit 1 and declares 1,045 bytes, while 1,044 bytes remain. Its side information proves the coded audio fits within present main data/reservoir, followed by unused ancillary bytes (the original ends in 501 bytes of 0xaa). It is a missing terminal ancillary byte, not an ID3 cleanup regression. Both original and repaired files decode successfully with FFmpeg strict error flags.

Correction is deliberately limited: only the final unprotected MPEG-1 padded frame, only exactly one missing byte, at least two prior audio frames, unchanged rate/version, complete side information, nonzero coded length and all coded bits present. Append a zero ancillary byte. Missing coded audio, two or more missing bytes, internal gaps, format switches, unpadded/CRC-protected cases remain rejected. No frame resynchronization, arbitrary junk skipping or transcoding.

The popup previously measured inspectMp3 output through mp3DurationMs but discarded prepared bytes and uploaded the original Blob. It now keeps the prepared Blob from the same validated file and sends it through both direct multipart and IndexedDB/offscreen upload. Original filename is retained; source File is not modified. M4A path is unchanged. Backend normalizer/decoder, authorization, upload limits, duration tolerance, moderation, Android and Windows are not changed.

The actual owner file becomes 5,710,366 bytes and measures 142,759 ms; inspection is idempotent. Independently decoding original and prepared bytes yields exactly the same complete PCM SHA256: 39993db0c62c906f952a2d5830a3cc7a07651d9fbcab14c8ee195d5d5341aa62. No sound was removed or reencoded.

462 extension tests pass. New tests cover exact preserved prefix and one-byte repair, idempotence, rejection of missing coded bits/two-byte truncation/CRC/unpadded/wrong-rate/internal damage, and actual prepared bytes passed through direct multipart and background staging. Full ZIP build, production manifest, security and whitespace checks pass. Existing playback changes from 0.4.93 are retained without additional playback engine edits.

Independent verification against deployed PHP normalizer/decoder and exact owner download receipt will be appended after successful execution. Use the existing private spool, trusted consumer and celikom.com owner delivery; no Actions download links or customer publication. Do not claim a real owner-account upload of the supplied song unless it was actually performed.

## Verified deployed upload path and private delivery

- Exact source `81447bfef49a2492675ff0574a0eaa986ed79282`, private Floki extension run `46059173025`, attempt 1. All 462 tests, build, security, checksum and private staging passed.
- Independent root-owned spool/ZIP verification and deployed ordinary-account HTTPS contribution flow: administrative run `46059336433`, job `140709502646`, SUCCESS.
- The live check reused the previously proven isolated QA flow, with generated tone audio normalized by the new extension inspector. A 7,335,180-byte multipart was accepted HTTP 202/pending and retried idempotently. Separate song proposal, linked upload progress, pending ownership, CORS and non-public pending media checks passed. Its own synthetic account, records and media were cleaned. No owner song was submitted and no user's data was modified.
- Filename `celikom-extension-0.4.94.zip`, **2,505,077 bytes**.
- SHA256 `e381d4c4274c768b888ab279d6523c666944f6d34aba581e70cdc92e22d09e09`.
- Existing owner-only approval manifest updated with exact verified metadata; public_stable remains null.
- Trusted owner consumer publication and full download verification: administrative run `46059437431`, job `140709837619`, SUCCESS. Trusted receipt matches version/source/run/attempt/size/hash. Both versioned and latest HTTPS downloads: anonymous 401, authorized 200 with matching complete size and digest.
- Explicit mirror service start again returned 1; trusted consumer independently read the exact new approval and successfully published/verified it. No unrelated mirroring repairs.
- Verified owner URL: https://celikom.com/downloads/extension/celikom-extension-0.4.94.zip
- Maintenance reset to harmless no-op in `ef873950c22fc3cb23194755f51362bad7096ad7`.

Independent native playback gate did not run: its Chrome/tool preparation step failed on `getaddrinfo ENOTFOUND github.com`. Do not mark it passed or infer listening acceptance. No extra Chrome repair work was attempted. The supplied original and prepared MP3 did independently pass local strict FFmpeg decoding with identical PCM; actual deployed PHP upload/normalizer/decoder passed the synthetic HTTPS test above.

Owner should update the existing unpacked extension and retry the same untouched original MP3. Its on-screen duration still must match the pinned original track within the existing 1.5-second tolerance; that rule is not relaxed.

## Subsequent owner diagnostic — unresolved transport/cancel/UI findings

Input `Вставленный текст(20261127-202937).txt`, 0.4.94. Owner asked to investigate rare slow upload, cancellation/retry errors and disappearing error text. This section records evidence, not a new fix or release.

- Attempt 2ec18523, track 128750389, 3,756,408-byte source: initial 98,304/114,688-byte progress, then slow partial transfer to 491,520 bytes (13%). Cancelled at 65.384 s. Its terminal diagnostic falls back to 10% and sent=0 because the worker records a decile counter rather than actual final progress. New attempt bce744e7 on same track/source completed HTTP 202 in 1.68 s.
- Attempt 0849c933, track 115444644, 3,063,827-byte source: 114,688 bytes / 3%, then no progress for about 29.7 s, network_error / HTTP status 0 at 30.216 s. New attempt c0d206a3 completed HTTP 202 in 1.596 s. Backend rejection/MP3 decoder error is not reported for the failed transmission.
- Other recent uploads completed in roughly 1.6–2.5 seconds. Historical 503 errors on 26 November are the already repaired executable-permission incident and must not be relabeled as this failure.
- Read-only administrative audit 46064319037, job 140725839354, SUCCESS: filtered deployed application log confirms successful bce744e7 (202, 552 ms) and c0d206a3 (202, 453 ms). No application upload record matched failed/cancelled prefixes in scanned tails. This bounded audit did not establish a particular VPN/TLS/HTTP2/server-network cause; no network configuration was changed.

Confirmed code issues in current upload wrapper:
1. Offscreen watchdog returns as soon as any first byte is reported; it never detects a later idle partial transfer. Absolute 120 s XHR timeout remains. The direct path has the same first-progress-only watchdog limitation.
2. Fresh popup suppresses terminal saved status when backgroundUploadMode is false, and opening resets the panel. Journal persists the failure, but error text cannot be recovered in the UI after closure. Existing server-authoritative pending/approved precedence must be retained when fixing this.
3. Reproduced cancellation race in actual built offscreen worker via VM (no real HTTP): hold config fetch pending, begin succeeds, cancel before xhr exists returns ok, immediate begin returns upload_busy, resolve config, and the old cancelled operation still starts one HTTP request. execute lacks cancellation fences after preparation awaits. Do not infer that this preparation race caused the owner's already-in-flight 3% stall; it independently explains a real possible cancel/retry/continued-upload inconsistency and requires regression coverage.
4. Cancellation acknowledgment is not a completion barrier; late old status must not overwrite a newer attempt when implementing retry/fencing. Do not automatically replay a POST or risk duplicate submissions.

No production extension source changed for this investigation; owner candidate remains 0.4.94. Outstanding work: progress-idle watchdog and accurate terminal bytes, real cancellation through preparation and cleanup, recoverable last-failure UI with current server state taking precedence, and targeted race/slow-transfer tests. No evidence yet establishes the underlying intermittent transport cause. Maintenance audit request returned to safe no-op.
