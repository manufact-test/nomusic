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
