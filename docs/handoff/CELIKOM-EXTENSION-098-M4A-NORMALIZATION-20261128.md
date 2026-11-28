# Extension 0.4.98 — canonical M4A upload

28 November 2026. Private owner candidate, customer channel unchanged.

Owner supplied `dope17, 3umph — hennessy (www.lightaudio.ru)(1).m4a`, track 141807399. Original is 4,489,912 bytes, AAC-LC stereo 44.1 kHz, 138.483810 seconds, with a cover and 14 moof/mdat fragments. Both old client preflight and server M4aInspector explicitly rejected fragmented input. This is a container limitation, not another MP3 trailer. 0.4.97's MP3 processing did not fix M4A.

The readable-M4A preflight now delegates unknown layouts to authenticated server processing, with a warning. Known duration mismatches and unreadable files still stop locally. No optimistic acceptance: server rejection remains visible and cannot create a pending result.

M4aNormalizer uses a dedicated minimal static FFmpeg build, from the same pinned source archive as the existing MP3 validator. It copies AAC packets into an ordinary faststart M4A, removes metadata/cover/chapter streams, checks single AAC-LC track and complete sample tables with existing M4aInspector, then completely decodes to a null sink. Standard metadata goes through MOV demuxing/remuxing rather than a growing list of tag names. There is no AAC encoder or network protocol in this binary, no shell, external drefs and absolute paths disabled, bounded allocation/output/stderr/runtime. M4A shares the existing two MP3 admission slots. MP3 binary and its handling remain unchanged.

UploadService now stores the normalized M4A and retains original-source SHA for existing retry semantics. Existing authentication, ownership, declaration, moderation, 30 MiB limit and 1.5-second duration gate remain. No automatic stretching of every uploaded song. Android, Windows, authorization and database schema unchanged.

Local verification of the actual supplied file: normalized to 4,456,209 bytes by the exact minimal binary; strict complete decode passes; original and normalized complete PCM are byte-identical (SHA256 992299d5b5e8369c9f0dd6a9c7c97ec45cb18399481e588025f0692aaf97a07d). No owner audio is committed to Git.

The owner separately requested 2:21 duration. A separate output `hennessy-2m21s.m4a` was prepared by small pitch-preserving tempo adjustment followed by AAC-LC encoding, with stream/container duration exactly 141.000000 seconds. It is NOT represented as lossless; this duration adjustment is separate from lossless automatic upload normalization. The output is saved as an owner download. The original remains untouched.

Regression fixtures are synthetic: ordinary and fragmented AAC; explicit fragment offsets; UTF8/title/comment/lyrics metadata; cover; free/skip/uuid boxes; malformed/truncated files; multiple audio tracks rejected. Every accepted fixture preserves complete PCM locally. PHP normalization matrix, live HTTPS flow, exact private build and owner-delivery evidence are appended only after execution.

## Executed verification and delivery provenance

- Exact source commit **4a10d2a70b3f97dc1ecc48624fa716b29200a7af**. All 15 text blobs and the executable binary blob/mode were verified against local git hashes before fresh main advanced. Other chats' Android/Windows commits were preserved.
- Dedicated static tool: SHA256 **c0f2d9b74c0f1f4e19605d45dbaf3e31e75411a53da4f1ceb172c1e2e0b86d63**, 3,805,992 bytes; Git blob 39123c9b511625fc2b2fb7598863bb7a33991512. Pinned source commit 2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99, source archive SHA256 82ce458e07914714c28028caed59326d1ac1b97fdf800201934162cc9434ff69. Rebuild script, checksum and existing LGPL license retained in server/tools. No change to mp3-validator.
- Isolated www-data PHP lint and all **11 normalization scenarios** passed using that exact binary: administrative run **46133604797**, job **140943941539**. Expected output hashes/durations match the independently exercised local binary; valid fixtures preserve PCM locally; invalid/truncated/multiple-audio fixtures are rejected. No database used in this matrix.
- Successful backend deployment, real HTTPS contribution verification and exact isolated extension build: administrative run **46133855457**, job **140944709887**, wrapper **2e9eeeafa5ac73cc82d0284b1513bd5f100b2a8c**. Deployment guards old UploadService and M4aInspector hashes; installs only the separate tool, M4aNormalizer.php and UploadService.php, preserving existing ownership/modes with private source backups. Lint checked before install, automatic rollback on failed HTTP probe. No permissions/config/auth/schema/slot changes.
- A fresh synthetic ordinary verified account/trial exercised existing CORS, proposal and idempotent retry, **raw fragmented 18,121-byte M4A multipart upload to pending**, same-attempt upload retry, linked proposal progress and pending-not-public/streamable boundaries. Incorrect duration and malformed M4A both returned the existing HTTP 415 with the precise expected error. Probe-owned synthetic account/rows/media/rate counters and temporary files were cleaned. This is not an upload from the owner's account.
- Existing private container ci01, spool owner UID **1001**, isolated directory and existing Node 24.22.3 were used to build the exact Git-archived source. All **510 extension tests**, production ZIP, manifest and security passed. No repository code executed as root; no Chrome/runner configuration changed. Provenance is the actual successful administrative isolated build, not a claimed native-browser CI success.
- ZIP **celikom-extension-0.4.98.zip**, **2,507,773 bytes**, SHA256 **76d190f9af494afb1634c873d1e734dd0a5944a64a326f32715d89e03daaa63d**, exactly matches local build.
- Existing private spool producer staged that actual source/build run. Independent root-owned consumer validated the receipt, ZIP and full digest: run **46134063451**, job **140945337687**, SUCCESS. Only then was exact metadata added to owner-only approvals; public_stable remains null.
- Installed runtime hashes: M4aNormalizer.php **6e183fa340db660f4c5fd9137eb850549a2490872a3f34bbbf44fcf995a4e623**; UploadService.php **27ff9aa9614bc7ee7815779dcc4851ed1aa1c736fe6084ccc9e46bf60d85e5b6**; tool hash above.
- Owner's separate 2:21 output: **4,779,626 bytes**, SHA256 **abc0db0aae3723cce8ced11d7eeb50959d4770a68cf85d4f146c030a59724841**. Stream/container duration 141.000000 seconds, client structural media duration 141,023 ms including AAC priming, within the unchanged compatibility tolerance. Complete strict minimal-tool decode passes. Saved as an independent owner file; never committed.

Final protected HTTPS verification and own-directory cleanup are recorded below. Real Yandex listening acceptance is not inferred.

## Verified owner download

Final trusted consumer and live backend-hash verification: administrative run **46134145981**, job **140945585914**, SUCCESS. Versioned/latest downloads returned anonymous 401 and authorized 200 with full matching size/SHA256. Exact current-owner receipt matches version 0.4.98, source 4a10d2a7..., actual successful build run 46133855457, attempt 1, owner-only channel and https_verified=true. Existing root-owned consumer was independently checked for trusted ownership/mode; credentials were not printed.

Verified package: https://celikom.com/downloads/extension/celikom-extension-0.4.98.zip

Only the exact `.work-extension98-owner.WvbFPx60` build directory was removed afterward, as UID 1001. Backend source backups remain private for rollback; all probe temporary files and synthetic records were cleaned. Shared runner/container/Chrome and unrelated mirror state were not repaired or changed. Mirror sync again returned 1 while exact trusted approval and final publication/HTTPS verification succeeded. The owned maintenance request is reset to a harmless no-op with this handoff; another chat's request must never be overwritten.

Owner should replace existing unpacked extension files, reload the extension and refresh Yandex Music once. For track 141807399 upload the separately supplied **hennessy-2m21s.m4a**. The untouched original remains 2:18.48 and will correctly fail the unchanged duration gate against 2:21. Automatic server container normalization does not stretch songs. Customer channel was not updated; previous MP3/playback fixes remain included.
