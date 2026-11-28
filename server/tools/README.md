# MP3 validation runtime

The upload path normalizes bounded MP3 metadata and then decodes the complete stream before it is accepted. The runtime executable is a server-side, x86-64 static FFmpeg CLI; it is not included in the browser extension or exposed through a public download route.

## Pinned validator

- Version: FFmpeg 7.1.5
- Upstream: `FFmpeg/FFmpeg`, commit `2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99` (17 Nov 2026)
- Binary SHA-256: `d9c6e49ef3246c77a112a0832a44a179f28fd0f0b147bd10572b2b79ab2d2939`
- ELF build ID: `2647d62ab8ddbeae4081b71ee3a973a3425f858c`
- Build configuration: `--disable-everything --disable-autodetect --disable-network --disable-doc --disable-debug --disable-x86asm --disable-shared --enable-static --extra-ldflags=-static --enable-ffmpeg --disable-ffplay --disable-ffprobe --enable-decoder=mp3float --enable-demuxer=mp3 --enable-protocol=file --enable-muxer=null --enable-encoder=pcm_s16le --enable-filter=anull,aresample --enable-swresample`
- No GPL components are enabled. FFmpeg's applicable license is LGPL 2.1 or later; the full license is in `LICENSE.LGPLv2.1`.

The matching upstream source archive is retained privately on FlokiNET at:

`/srv/celikom-releases/private/runtime-tools/ffmpeg-7.1.5-2f5e4b9521db2ae309e5c2dd6e409fab27e1ad99.tar.gz`

Expected source archive size: 15,948,344 bytes. SHA-256: `82ce458e07914714c28028caed59326d1ac1b97fdf800201934162cc9434ff69`. The source archive is intentionally not copied into each application package; keep the private source copy and this checksum through handover. `build-mp3-validator.sh` verifies it before rebuilding.

## Runtime permissions on FlokiNET

PHP-FPM runs as `www-data`. The directory must remain non-writable by that user while the two pre-created lock files are group-writable:

- `tools/`: `root:www-data`, mode `0750`
- `tools/mp3-validator`: `root:www-data`, mode `0750`
- `tools/decode-slot-0.lock` and `tools/decode-slot-1.lock`: `root:www-data`, mode `0660`
- `tools/LICENSE.LGPLv2.1`: `root:www-data`, mode `0640`

Do not make the tools directory group-writable. The validator opens only the two existing lock files, invokes a fixed argument array with no shell, limits decoding to one thread and 15 seconds, and allows only the local file protocol. The build package prepares executable/lock modes; the deploy step must set the ownership/group above after extraction.

## M4A container normalization (0.4.98)

`m4a-normalizer` is a separate static build from the same pinned FFmpeg source
commit/archive as the MP3 validator. Build with `bash build-m4a-normalizer.sh
/path/to/ffmpeg-source.tar.gz`; archive SHA256 is verified by the script.
Only MOV demuxing, AAC decoding/parser, packet-copy IPOD muxing, a null sink
and file protocol are enabled. No network and no AAC encoder/transcoding.
Checksum: `m4a-normalizer.sha256`. The MP3 validator is unchanged.

Authenticated M4A uploads are canonicalized with packet copy and metadata/cover
removal, structurally inspected as single-track AAC-LC, then completely decoded
to a null sink. Fragmented/ordinary M4A and ordinary container metadata use
the same demux/remux path; metadata names are not individually whitelisted.
External track references and absolute aliases are disabled explicitly.
Both processes share the existing two MP3 admission lock slots and have
15-second time limits, bounded stderr/allocation/output, no shell/network.

References: https://ffmpeg.org/ffmpeg-formats.html (MOV demuxer, IPOD/MOV muxer).
