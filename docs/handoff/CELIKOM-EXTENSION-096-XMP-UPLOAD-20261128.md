# Extension 0.4.96 — orphaned XMP upload tail

28 November 2026 (owner timezone). Private owner candidate, no customer publication.

Owner supplied `Yung_Trappa_-_Trapflow_3_72038827(1).mp3` after the pre-upload duration error returned for track 53685452. This is different from the one missing ancillary byte repaired in 0.4.94. 0.4.95 retained that earlier correction; no rollback or missing migration was identified.

Actual supplied file: 5,086,189 bytes, SHA256 69e1fd6b4a110e1845e8ccff9b0c0975e387058eadd7b02d8ca23024b7d73697. Leading ID3v2 occupies bytes 0..312892. There are 4,569 complete consecutive MPEG frames at byte range [312893,5082929). After them: 1,804 zero padding bytes, a 1,328-byte orphaned XMP property/closing-tag fragment and an ID3v1 tag. Existing inspection rejects the nonzero tail, so upload never begins. Raw FFmpeg strict decoding also reports a missing header on the non-audio tail; do not describe raw strict decode as successful.

The existing normalizer now recognizes this bounded orphan fragment after complete MPEG frames and at least 32 zero padding bytes, within the existing 4,096-byte tail bound. It validates the ENTIRE printable fragment: a bounded identifier/property continuation, at most four known stRef ID properties, exact RDF/XMP closing sequence and optional known xpacket end marker. Whitespace is normalized before bounded token checks; XML is never executed or parsed with external entities. Arbitrary trailers, extra garbage/scripts/control bytes, changed frame headers, missing closings and over-limit tails remain rejected. No resynchronization through damaged audio or generic dropping of an arbitrary trailer.

Returned prepared Blob already flows through both direct and background upload as fixed in 0.4.94; no upload route or backend change is needed. Output is 4,770,036 bytes, measured 119,353 ms. Every one of its 4,569 MPEG frames is byte-for-byte equal to the original contiguous audio range; preparation is idempotent. Final output passes strict FFmpeg decode. Its complete decoded PCM SHA256 equals the original file's decodable audio: 06138908c11b09a0e767e541fb88cc9259670c6f666d3aa98e126c2c597d7b66. No transcoding or audio removal.

471 extension tests pass. Added orphan-XMP cleanup/idempotence and rejection coverage plus multipart integration proving cleaned bytes are actually sent while the selected source File is unchanged. Both real owner inputs were rechecked: Trapflow accepted with XMP removal; baby-melo-orvi accepted with the previous one-byte ancillary repair. Full ZIP build, production manifest, security and whitespace checks passed.

Retained: 0.4.95 cancellation fences, partial-upload idle detection and persistent failure UI; existing duration tolerance, subscription/auth, moderation and file size limits. No Android, Windows, server authorization, decoder deployment or playback-engine changes. No supplied audio is committed to Git.

Exact private build/spool and owner HTTPS delivery evidence will be appended after independent verification. Do not infer an actual owner-account upload or real Yandex listening acceptance from these tests.
