# Extension 0.4.97 — standard MP3 metadata processing

28 November 2026, owner timezone. Private owner candidate; no customer publication.

The owner's Fountainebleu MP3 (track 130919915) failed local inspection because it ends with a valid Lyrics3v2 tag followed by ID3v1. Earlier claims of comprehensive metadata support were incorrect. This is a standard tag, not damaged coded audio and not a filename-specific case.

## Processing contract

Client and server now use matching bounded metadata walkers after the contiguous validated MPEG interval. Recognized trailers: ID3v1, enhanced TAG+, legacy UTF8-inflated ID3v1, APEv1/v2 (optional v2 header), Lyrics3v1/v2, and trailing ID3v2 including v2.4 footer. Multiple tags and bounded outer/inter-tag padding are handled in either ordering. Existing leading/interleaved ID3 and duplicate Info cleanup, bounded orphan-XMP cleanup and proven single missing ancillary-slot repair are retained. Server now independently supports those prior XMP/ancillary cases too.

Limits remain explicit: at most 16 trailer tags, 8 MiB total metadata, 1 MiB individual APE, 128 APE items or Lyrics3v2 fields, 5,120-byte Lyrics3v1 bound and 4,096 total padding bytes. Declared sizes, field framing and marker boundaries are checked. Unknown arbitrary trailers, malformed sizes, excessive tags/padding, internal frame gaps and missing coded audio remain rejected. No generic frame resynchronization, arbitrary junk stripping, XML execution or transcoding.

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

Actual remote PHP parity, deployment and private owner-delivery evidence must be appended after successful execution. Local tests do not constitute owner-account upload or Yandex listening acceptance. Playback implementation, Android, Windows, server authorization and database schema are outside this change.
