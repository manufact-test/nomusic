# Extension 0.4.98 — canonical M4A upload

28 November 2026. Private owner candidate, customer channel unchanged.

Owner supplied `dope17, 3umph — hennessy (www.lightaudio.ru)(1).m4a`, track 141807399. Original is 4,489,912 bytes, AAC-LC stereo 44.1 kHz, 138.483810 seconds, with a cover and 14 moof/mdat fragments. Both old client preflight and server M4aInspector explicitly rejected fragmented input. This is a container limitation, not another MP3 trailer. 0.4.97's MP3 processing did not fix M4A.

The readable-M4A preflight now delegates unknown layouts to authenticated server processing, with a warning. Known duration mismatches and unreadable files still stop locally. No optimistic acceptance: server rejection remains visible and cannot create a pending result.

M4aNormalizer uses a dedicated minimal static FFmpeg build, from the same pinned source archive as the existing MP3 validator. It copies AAC packets into an ordinary faststart M4A, removes metadata/cover/chapter streams, checks single AAC-LC track and complete sample tables with existing M4aInspector, then completely decodes to a null sink. Standard metadata goes through MOV demuxing/remuxing rather than a growing list of tag names. There is no AAC encoder or network protocol in this binary, no shell, external drefs and absolute paths disabled, bounded allocation/output/stderr/runtime. M4A shares the existing two MP3 admission slots. MP3 binary and its handling remain unchanged.

UploadService now stores the normalized M4A and retains original-source SHA for existing retry semantics. Existing authentication, ownership, declaration, moderation, 30 MiB limit and 1.5-second duration gate remain. No automatic stretching of every uploaded song. Android, Windows, authorization and database schema unchanged.

Local verification of the actual supplied file: normalized to 4,456,209 bytes by the exact minimal binary; strict complete decode passes; original and normalized complete PCM are byte-identical (SHA256 992299d5b5e8369c9f0dd6a9c7c97ec45cb18399481e588025f0692aaf97a07d). No owner audio is committed to Git.

The owner separately requested 2:21 duration. A separate output `hennessy-2m21s.m4a` was prepared by small pitch-preserving tempo adjustment followed by AAC-LC encoding, with stream/container duration exactly 141.000000 seconds. It is NOT represented as lossless; this duration adjustment is separate from lossless automatic upload normalization. The output is saved as an owner download. The original remains untouched.

Regression fixtures are synthetic: ordinary and fragmented AAC; explicit fragment offsets; UTF8/title/comment/lyrics metadata; cover; free/skip/uuid boxes; malformed/truncated files; multiple audio tracks rejected. Every accepted fixture preserves complete PCM locally. PHP normalization matrix, live HTTPS flow, exact private build and owner-delivery evidence are appended only after execution.
