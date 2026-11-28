# Extension 0.4.97 — standard MP3 metadata processing

28 November 2026, owner timezone. Private owner candidate; no customer publication.

The owner's Fountainebleu MP3 (track 130919915) failed local inspection because it ends with a valid Lyrics3v2 tag followed by ID3v1. Earlier claims of comprehensive metadata support were incorrect. This is a standard tag, not damaged coded audio and not a filename-specific case.

## Processing contract

Client and server now use matching bounded metadata walkers after the contiguous validated MPEG interval. Recognized trailers: ID3v1, enhanced TAG+, legacy UTF8-inflated ID3v1, APEv1/v2 (optional v2 header), Lyrics3v1/v2, and trailing ID3v2 including v2.4 footer. Multiple tags and bounded outer/inter-tag padding are handled in either ordering. Existing leading/interleaved ID3 and duplicate Info cleanup, bounded orphan-XMP cleanup and proven single missing ancillary-slot repair are retained. Server now independently supports those prior XMP/ancillary cases too.

Limits remain explicit: at most 16 trailer tags, 8 MiB per leading/trailing metadata stage, 1 MiB individual APE, 128 APE items or Lyrics3v2 fields, 5,120-byte Lyrics3v1 bound and 4,096 total padding bytes. Declared sizes, field framing and marker boundaries are checked. Unknown arbitrary trailers, malformed sizes, excessive tags/padding, internal frame gaps and missing coded audio remain rejected. No generic frame resynchronization, arbitrary junk stripping, XML execution or transcoding.

If a readable MP3 cannot be measured by the client, the form shows a warning and sends its original bytes for authoritative server processing instead of declaring the file unreadable before submission. Unreadable files and invalid M4A still stop locally; known duration mismatch still blocks. The authenticated server still must normalize, independently inspect duration, perform complete strict decoding and enforce 1.5-second duration tolerance before creating a pending submission. Moderation, rights declaration, limits, authorization, decoder binary and decoder-slot count are unchanged.

## Local evidence

509 extension tests passed, including a 35-case shared client/server fixture matrix, multipart byte preservation for Lyrics3, unknown MP3 reaching a simulated server rejection (never accepted/pending), unreadable/M4A blocking and all prior cancellation/retained-error regressions. Production ZIP build, manifest, security and whitespace checks passed. Shared synthetic fixtures contain no supplied owner audio.

All three untouched owner files were prepared and fully decoded with strict FFmpeg. Their entire decoded PCM equals the original decodable PCM byte-for-byte:

| Input | Original bytes | Prepared bytes | Duration ms | PCM SHA256 |
| --- | ---: | ---: | ---: | --- |
| Fountainebleu - 9mice, Kai Angel.mp3 | 5385722 | 5350921 | 133773 | b44c7e983e58bcc2cfd991b468afd4a167cdb5b2967343819178b1dbe0e97cdb |
| Yung_Trappa_-_Trapflow_3_72038827(1).mp3 | 5086189 | 4770036 | 119353 | 06138908c11b09a0e767e541fb88cc9259670c6f666d3aa98e126c2c597d7b66 |
| baby-melo-orvi_(ru.livemuz.com).mp3 | 5710365 | 5710366 | 142759 | 39993db0c62c906f952a2d5830a3cc7a07651d9fbcab14c8ee195d5d5341aa62 |

Fountainebleu original SHA256: 0d24a343887d2691e5af3506561460b628bec3d966c9db2e52f68d0cb97d93d9. Its prefix contains ID3v2, Info, ID3v2, duplicate Info; EOF contains the 44-byte Lyrics3v2 block `LYRICSBEGININD0000210LYR00000000029LYRICS200` and ID3v1. First Info and every actual coded frame are preserved. No owner audio is committed.

Executed remote PHP parity, deployment and private owner-delivery evidence follows below. Local tests do not constitute owner-account upload or Yandex listening acceptance. Playback implementation, Android, Windows, server authorization and database schema are outside this change.

## Executed server and build verification

- Exact source commit: `c3057ec8cd6f39d56591fe05b5a8f1f3420a6f8b`. All 17 changed blobs were independently checked against local git hash-object before advancing fresh main; unrelated concurrent Windows/Android changes were preserved.
- PHP lint and all **35 shared JS/PHP parity cases** passed as www-data in an isolated temporary directory with no database access: administrative run `46075556808`, job `140762327200`.
- Backend deployment replaced only `src/Application/Mp3Normalizer.php` and added `Mp3Metadata.php` under the existing application. Exact old normalizer SHA256 was required before replacement; ownership/mode preserved, source backups retained privately, PHP lint checked, helper installed before its consumer. No auth/config/schema/decoder/slot changes.
- First live probe run `46125511056` failed because the test incorrectly expected HTTP 422; the existing API returns **415** for these validation errors. The deployment automatically rolled back and its synthetic records were removed. No application change to the HTTP contract was needed. The corrected probe asserts the established 415 status and precise error code.
- Successful deployment, complete real HTTPS contribution flow and isolated build: administrative run **`46125600649`**, job **`140919386403`**, wrapper `7a9ce8509c5a453f7429140074e58de2cc71a1c2`. A fresh synthetic ordinary verified account with trial used the existing API: CORS; proposal and idempotent retry; duration mismatch rejected; invalid MP3 rejected; **7,335,352-byte raw tagged MP3 upload accepted as pending**; same-attempt retry returned the same replacement; linked proposal progress; pending audio not public or streamable. The uploaded fixture included Lyrics3v2 and ID3v1; server cleaned it independently. Only this probe's account/records/media/rate counters were removed afterward.
- The same successful administrative run built the exact Git-archived source as existing spool owner UID **1001** in a new private directory inside ci01, using its existing Node 24.22.3 cache. All **509 tests**, ZIP build, production manifest and security passed. No repository code executed as root; no runner/Chrome/container configuration changed. This is actual administrative-workflow isolated-build provenance, not a claimed successful normal/native CI check.
- Built ZIP: `celikom-extension-0.4.97.zip`, **2,507,737 bytes**, SHA256 **79d2f37b73d38802a0fe38ea538185049628eb74968045b88d52e885ddadd429**. It exactly matches the locally checked build.
- Existing private spool producer staged that actual build run and source. Independent trusted consumer checked receipt, ZIP content/manifest and full hash: run **`46125751763`**, job **`140919846476`**, SUCCESS. Only then was exact metadata appended to the existing owner-only approvals; public_stable remains null.
- Installed backend SHA256: `Mp3Metadata.php` = `599e16953d56778e0b64abfe276e7a0a3dec6d8842fc4008791c7e4c16789ce9`; `Mp3Normalizer.php` = `bc1a23d808dfb7be5318e743149b5e3c96647e867cf5f80853b711a7a2185954`.

Final owner HTTPS receipt and post-publication cleanup have been verified as recorded below. Do not infer real Yandex listening acceptance or an upload from the owner's account.


## Verified private owner delivery

Final trusted consumer verification: administrative run **46125819467**, job **140920061309**, SUCCESS. Live backend hashes match the checked source; versioned and latest owner downloads returned anonymous 401 and authorized 200 with matching complete byte count/SHA256. Current-owner receipt exactly matches 0.4.97, source c3057ec8..., actual successful build run 46125600649, attempt 1 and owner-only channel. Both independent spool validation and HTTPS checks used the existing root-owned consumer with ownership/mode checks, without exposing credentials.

Verified URL: https://celikom.com/downloads/extension/celikom-extension-0.4.97.zip

Only the exact isolated `.work-extension97-owner.1CL11SSS` directory was removed after success, as UID 1001. Temporary backend probe files and only this probe's synthetic contribution data were cleaned. Source backups remain private for rollback. The final maintenance request is reset to a harmless no-op when this handoff is saved. The mirror sync service again returned 1 due existing unrelated mirror state; exact trusted approvals, publication and full HTTPS verification succeeded. No shared mirror/runner/Chrome repairs were attempted.

Owner update: replace contents of the existing unpacked-extension directory with 0.4.97, reload the installed extension, then refresh Yandex Music once. Retry the untouched original Fountainebleu MP3; do not pre-clean/re-encode it manually. Server normalization is already deployed. The public customer channel was not updated.
