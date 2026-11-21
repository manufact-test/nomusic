# Automatic lossless MP3 upload cleanup — desktop 0.4.78

## Scope

New upload preflight and shared backend staging only. Desktop playback is the accepted 0.4.77 implementation; the only core.ts delta is VERSION. Android and Windows sources, public audio delivery, Range, existing stored assets, moderation, access, payments and rate limits are unchanged. No database migration.

Backend cleaning applies to every client using POST /api/v1/uploads. Older clients can still reject repairable files in their own preflight; other client maintainers should align their parser, without weakening the independent server check. M4A remains on the existing M4aInspector path; this change targets the MP3 metadata failures actually reproduced.

## Pipeline

1. Existing authentication, declaration, request/file and original-size limits.
2. Strict bounded normalization into a private temporary file. Remove leading ID3v2 blocks, additional empty Info/Xing metadata frames before audio, validated APEv2/ID3v1 tails and bounded zero padding. A downloader's UTF-8 inflated ID3v1 tail is accepted only if its decoded field character count is exactly the original 124 characters, with no extra control bytes.
3. Preserve the first Info/Xing frame byte-for-byte, including encoder delay/padding data. Copy every actual audio frame unchanged. Never resynchronize past an invalid audio frame or remove tags appearing inside actual audio.
4. Existing server Mp3Inspector independently measures the normalized file. A private, network-disabled MP3-only FFmpeg decoder reads the entire audio to a null sink with xerror/err_detect=explode. Failed decoding is invalid_mp3. No audio is reencoded. Validation infrastructure failures return an error, never success.
5. Existing 1.5 second duration comparison, staging and transaction. Only after successful storage/DB completion is the response pending/202. Canonical digest drives new deduplication; original digest is also recognized for retries of pre-cleanup submissions/assets.
6. Temporary file is unlinked in finally on success, duplicate and all errors. Existing assets are never rewritten.

The browser parser implements the same structural normalization rules for duration preflight but uploads the original File. This preserves the existing staging/request identity and lets the server perform authoritative cleanup for every client. Local preflight cannot detect all damaged Huffman payloads; the server decoder does.

## Decoder build

Pinned official FFmpeg release/7.1 source commit 2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99, retrieved through the official FFmpeg GitHub repository. Build recipe: .github/scripts/upload-cleanup/build-decoder.sh. Minimal static musl binary: MP3 demuxer, mp3float decoder, file protocol, null muxer and PCM sink only; no network, GPL or external codec libraries enabled. LGPL license and exact source archive travel with the private server binary. Reproducible source/configuration is kept; binary checksum is verified, not claimed bit-reproducible across toolchains.

No shell invocation from PHP: proc_open receives a fixed argv array. Input has a strict 30 MiB bound. Two nonblocking process slots, one decoder thread, 15 second deadline, bounded stderr. Overload/unavailable/timeout fails closed as a retryable server failure. No FFmpeg diagnostics, private paths or contents are returned to clients.

## Verification

- Four retained original user problem MP3s: Heronwater / Bla-bla-bla; Sqftyboy, WHITEKIDD / Odinoko; Yupi, boogshi / STVOL; Виталя [Джа] / По хуй молодой. JS normalization outputs match the manually repaired files, decoded PCM SHA-256 and ffprobe duration exactly match each original. No user audio is committed to GitHub or uploaded to public CI.
- 371 extension tests, including new normalization fixtures, pass locally.
- Disposable synthetic sine fixtures cover MPEG1/2, 44.1/48/22.05 kHz. JS and PHP output bytes and decoded PCM are compared; valid frame headers with corrupted payload must pass structural preflight but fail full decoding.
- PHP upload SQL tests cover canonical asset digest/size, same-content metadata variants, legacy raw-digest retries, duplicate prevention and temporary-file cleanup.
- Native Chrome popup test selects a repairable file through File/DataTransfer, blocks truncation, recovers after selecting the valid file again, and checks no unintended upload or rights confirmation.
- Release workflow runs independent tests before a surgical deployment; exact old UploadService/Mp3Inspector digests guard against overwriting concurrent work. Candidate clones the actual current release and changes only UploadService plus new private normalizer/decoder/tools. No full checkout deployment.
- Hosting smoke exercises the actual HTTPS/FPM process, both valid cleanup and broken-payload rejection, before/after activation. One random, nonce-protected synthetic-only QA script is removed in finally. No account/admin sessions or catalog records are created by the hosting smoke.

## Status

Deployed successfully on 2026-11-21 at 10:31 Minsk (07:31 UTC).

- Code/release commit: 823c0613c2122d201165ae45952598b60c935c4b.
- Workflow 44880432304: inspection, pinned decoder, verification and deployment all succeeded. Verify job 136774379166; deployment job 136774800576.
- Active server release: upload-cleanup-823c0613c212. Backup: /home/u235811320/domains/darkred-camel-588676.hostingersite.com/celikom/backups/upload-cleanup-823c0613c212/. Its previous-release file identifies the exact prior release, and UploadService.php/public-index.php preserve the replaced file and launcher metadata.
- Exact-delta assertion passed. Both candidate and active HTTPS/FPM probes accepted the repairable synthetic MP3, checked exact cleaned bytes and rejected broken payloads. Public /api/v1/config remained healthy; shared env and public launcher content hashes stayed unchanged. Random QA endpoint was removed by finally.
- 371 extension tests, native Chrome File/DataTransfer UI, PHP/JS PCM comparisons, MySQL canonical/legacy retries, temp-file cleanup, security and package validation all passed. Source playback delta asserted VERSION only.
- Delivered ZIP: 2,491,316 bytes. SHA-256 67873c1085b0926a5f40531d17b06d444cbe0b5124442f2cdfa49245794bb56c. CI artifact 14697433285 was downloaded and its contained ZIP compared byte-for-byte with the delivered local package.
- Library ZIP libfile_a081342241dc819193a14eff8a34a577; checksum libfile_4cd03b082e0c81919713771bada95551. PR 62 remains unmerged for review; deployed backend is an exact upload-only patch of the actual active release, not this branch's entire server tree.

Owner confirmation using their own installed 0.4.78 upload remains pending; do not claim every possible malformed MP3 is supported. This implementation covers the known bounded metadata patterns and refuses unknown damage rather than guessing. Existing Android/Windows client-side preflight is outside this change.

Do not re-run a successful deployment blindly: original-source digest guards intentionally reject a second installation. For rollback, first require that current still resolves to this release; atomically restore the path recorded in backup/previous-release and restore public index mtime. Never roll back over a later release from another chat. No DB or audio-asset rollback is required because this deployment performs neither migrations nor catalog writes. Future server rollouts must preserve these three classes and private tools or merge this upload delta first; deploying a historical complete server checkout would discard the feature.

Stable baseline: fix/desktop-wave-metadata-20261118 @ d12cdcdaf96b95710b93e783898fe59488f27dff (owner accepted 0.4.77). Branch: feature/upload-auto-cleanup-20261121. Backend old UploadService SHA-256 dd4ec0501fb88b06e5aaf8d423fe83581fc7321207138cb0cdcad3128ab95c7b; old Mp3Inspector 0485502c2488a1125bd4b5d898133f68f7fb870914626d9659b330ee9f122a25.


## Post-install owner upload check (2026-11-21)

Owner installed 0.4.78 and uploaded several real songs. Read-only workflow 44883847547 inspected all five new replacement records after activation. All five are pending, each has one submission, matching physical size/SHA-256, compatible measured duration, canonical already-normalized MP3 bytes and successful full decoding of the stored object. Active release remains upload-cleanup-823c0613c212. Moderation/catalog/account data were not modified.

The report is CMS-encrypted before being attached to Actions; titles, asset identifiers and hashes are not printed in public CI logs. No user audio is copied out of hosting. Exact original metadata cleanup per upload cannot be reconstructed: current schema retains the canonical asset/submission digest, not original tags, raw bytes or a per-upload removed-byte counter. Do not infer that a particular song required repair merely because the stored file is clean. This verifies ingestion/storage/decodability, not musical correctness of the replacement or every possible future input.


## Subsequent admin-only restoration

On 2026-11-21, release admin-bulk-restore-067968ce4eae cloned the active upload-cleanup release and restored six Admin files only. The upload pipeline/normalizer/private decoder are preserved byte-for-byte by its exact-delta assertion. All five owner songs were already approved before that restoration and were not remoderated. See docs/admin/ADMIN-BULK-RESTORE-20261121.md for the missing bulk/search recovery and shared snapshot deployment warning.
