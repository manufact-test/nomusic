# CELIKOM 0.4.54 — consecutive ID3v2 headers (18 October 2026)

## Source and confirmed failure

Track ID `48591846` (Каменные цветы). Owner supplied the actual 11,118,847-byte
MP3 to the chat privately (do NOT add the audio to GitHub, CI artifacts or
public issues). SHA-256:
`d261b89d81d73de3693e8669a5d93f25a99ccb3cbc89e80a14a1775d28d91cf8`.

Verified locally against the supplied original:
- `ffprobe`: valid MP3, MPEG Layer III v1, 44,100 Hz, stereo, 320 kbit/s;
  277.942857 seconds as estimated by FFmpeg's format-level probe.
- Decoding by `ffmpeg -v error -i <file> -f null -` completed successfully.
- Two consecutive valid ID3v2.4 tags: first at offset 0 with payload 35
  (next header at 45); second at offset 45 with payload 34 (MPEG starts at
  byte 89). First/second TSSE fields describe Lavf encoder versions.
- Frame scan: 10,641 contiguous MPEG-1 Layer III frames covering the entire
  file (9,554 frames of 1,045 bytes, 1,087 of 1,044 bytes; no trailer).
  Frame-derived duration 277,968.98 ms, safely within 1,500 ms of the
  Yandex duration 277,900 ms.
- Existing single-ID3 parser attempts frame parsing at byte 45 and returns
  null because the next bytes start with `ID3` rather than MPEG sync.
  This explains BOTH local “could not read duration” and historical server
  `HTTP 415 invalid_mp3`. Previous APEv2/finfo fixes do not address it.

## Fix and safety properties

Client `mp3DurationMs` and PHP `Mp3Inspector` now iterate over up to four
**consecutive** ID3v2 headers before parsing all MPEG frames. Each header
enforces supported versions 2–4, flags, synchsafe payload size and bounded
total leading metadata (8 MiB); malformed/truncated tags or extra arbitrary
data cannot simply be searched past. Existing strict MPEG frames, duration
and trailing metadata checks remain.

Regression fixtures consist of generated frames/tags only (no copyrighted
audio). They include a two-tag layout with offsets 0/45/89, malformed second
tag and excess tags. Test in isolated MySQL that a double-tagged MP3
enters `pending` moderation rather than publishing directly. The actual user
file remains only in the original chat attachment and local verification.

## Release

Build 0.4.54 after passing CI, then deploy only through guarded Hostinger
pipeline with snapshot, HTTPS/API checks, after-deploy audit and isolated
restore. Preserve all uploaded versions and PR #6. No website/UI changes.
An automated synthetic test is not equivalent to an end-to-end upload of
the user's own MP3 from their Chrome: request a single manual verification
after the client/server updates complete.
