# Extension 0.4.96 — orphaned XMP upload tail

28 November 2026 (owner timezone). Private owner candidate, no customer publication.

Owner supplied `Yung_Trappa_-_Trapflow_3_72038827(1).mp3` after the pre-upload duration error returned for track 53685452. This is different from the one missing ancillary byte repaired in 0.4.94. 0.4.95 retained that earlier correction; no rollback or missing migration was identified.

Actual supplied file: 5,086,189 bytes, SHA256 69e1fd6b4a110e1845e8ccff9b0c0975e387058eadd7b02d8ca23024b7d73697. Leading ID3v2 occupies bytes 0..312892. There are 4,569 complete consecutive MPEG frames at byte range [312893,5082929). After them: 1,804 zero padding bytes, a 1,328-byte orphaned XMP property/closing-tag fragment and an ID3v1 tag. Existing inspection rejects the nonzero tail, so upload never begins. Raw FFmpeg strict decoding also reports a missing header on the non-audio tail; do not describe raw strict decode as successful.

The existing normalizer now recognizes this bounded orphan fragment after complete MPEG frames and at least 32 zero padding bytes, within the existing 4,096-byte tail bound. It validates the ENTIRE printable fragment: a bounded identifier/property continuation, at most four known stRef ID properties, exact RDF/XMP closing sequence and optional known xpacket end marker. Whitespace is normalized before bounded token checks; XML is never executed or parsed with external entities. Arbitrary trailers, extra garbage/scripts/control bytes, changed frame headers, missing closings and over-limit tails remain rejected. No resynchronization through damaged audio or generic dropping of an arbitrary trailer.

Returned prepared Blob already flows through both direct and background upload as fixed in 0.4.94; no upload route or backend change is needed. Output is 4,770,036 bytes, measured 119,353 ms. Every one of its 4,569 MPEG frames is byte-for-byte equal to the original contiguous audio range; preparation is idempotent. Final output passes strict FFmpeg decode. Its complete decoded PCM SHA256 equals the original file's decodable audio: 06138908c11b09a0e767e541fb88cc9259670c6f666d3aa98e126c2c597d7b66. No transcoding or audio removal.

471 extension tests pass. Added orphan-XMP cleanup/idempotence and rejection coverage plus multipart integration proving cleaned bytes are actually sent while the selected source File is unchanged. Both real owner inputs were rechecked: Trapflow accepted with XMP removal; baby-melo-orvi accepted with the previous one-byte ancillary repair. Full ZIP build, production manifest, security and whitespace checks passed.

Retained: 0.4.95 cancellation fences, partial-upload idle detection and persistent failure UI; existing duration tolerance, subscription/auth, moderation and file size limits. No Android, Windows, server authorization, decoder deployment or playback-engine changes. No supplied audio is committed to Git.

Exact private build/spool and owner HTTPS delivery evidence will be appended after independent verification. Do not infer an actual owner-account upload or real Yandex listening acceptance from these tests.

## Verified private owner delivery

- Exact archived extension build source: `0e28cba5221c0f345bb1e3502d186016a614f54b`. All 10 changed blobs were verified against local git hash-object before main advanced.
- Ordinary extension run `46068278275`, job `140738782873`, became assigned to ci01 but did not start any steps during this work. It is NOT claimed as the producer or a passed browser check.
- Delivery therefore used a controlled isolated build through the already authorized administrative workflow, **actual successful build run `46070419007`, job `140745763863`**, wrapper commit `0d847d439a99050eb12f52696388102379c46adb`. The wrapper extracted only required files from the exact archived source above into a private temporary workspace in the existing CI container, then executed build/unpacked, all 471 tests (concurrency 2), ZIP build, manifest validation and security as the existing unprivileged spool owner **UID 1001**. No repository code ran as root. Successful execution used the existing Node 24.22.3 toolcache. The resulting ZIP exactly matched the locally verified size and digest.
- This is explicitly administrative-workflow isolated-build provenance, not a fictional successful ordinary extension workflow. Receipt run_id is the ACTUAL successful build run `46070419007`; source_commit is the actual Git-archived source `0e28cba...`.
- Existing `floki-private-build-spool.mjs --extension-only` staged those exact checked bytes without changing receipt schema, delivery consumer or public channel. Independent root-owned consumer ZIP/spool verification: run `46070646863`, job `140746519238`, SUCCESS.
- Package `celikom-extension-0.4.96.zip`, **2,506,160 bytes**.
- SHA256 `2503ea6f3a2326394dbd3e67859064a051db30125a035f44cff22c35aefc1379`.
- Exact metadata approved in existing owner-only manifest; public_stable remains null.
- Final trusted receipt and full HTTPS verification: administrative run `46070788054`, job `140746963567`, SUCCESS. Both versioned/latest downloads returned anonymous 401 and authorized 200 with matching complete size/hash. Receipt exactly matches version/source/actual build run/attempt/hash.
- Verified private URL: https://celikom.com/downloads/extension/celikom-extension-0.4.96.zip
- Only the exact isolated build directory was removed after publication. Maintenance request reset to harmless no-op in `00048628ffc921127b1641fb77568926b58fe49a`.
- Explicit mirror service invocation again returned 1, but trusted approval matched exactly and existing publisher/HTTPS verification succeeded. No unrelated mirror changes.

### Delivery troubleshooting limits

Earlier 0.4.95 native run `46066362165` ended cancelled. Two exact old-process probes found no matching process and terminated nothing; an idle-unit verification failed before restart, and a same-user listener signal attempt failed. No runner service/container configuration, active worker, CI02 or Chrome setup was changed.

The first isolated-build attempts incorrectly assumed UID 1000, missed the existing Node cache and hit temporary-file limits. Those failed attempts were never approved/staged as a release. Only task-owned failed Node temp folders were cleaned. After deriving actual existing spool UID 1001, the existing Node cache was accessible and all checks passed; the successful build required no shared runtime install. This UID assumption caused avoidable delay and must not be repeated.

No separate native Chromium/Yandex listening acceptance is claimed. The actual supplied cleaned audio did pass strict local FFmpeg decode with unchanged MPEG bytes and matching complete decodable PCM. Owner should reload the updated unpacked extension and retry the original untouched Trapflow MP3.
