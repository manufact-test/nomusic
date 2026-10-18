# CELIKOM website v5.12 — verified Au source, private restored excerpt, deployment gate

**Date:** 2026-10-18. **Branch:** `feature/api-range`. **LIVE CLOSED HOSTINGER SITE:** still v5.10 (FAQ). The entire A/B player is **not** deployed as usable until two genuine audio sources exist. No public launch.

## Major correction to v5.11

The MP3 uploaded by the owner named `10AGE, Ramil - Ау.mp3` is **exactly the active CELIKOM replacement audio**, NOT an independently obtained current Yandex Music audio. This was verified on Hostinger by a read-only MySQL query and filesystem SHA-256:

- Yandex service track ID `144530503`, title `Ау`, artist `10AGE, Ramil'`, target duration 180872 ms.
- Active replacement ID `1`, version `1`, approved, only mapping for this track.
- File byte size `4345176`; SHA-256 `5dfdfaa97ee6f1168964a1a49a101bebb20bd5dca7147c41c1d2df366a2a00d8`.
- The owner's uploaded MP3 has **exactly the same hash/bytes**. The site's previous temporary label `Au-bez-CELIKOM...` is **wrong**: it actually contains the **«С CELIKOM»** content. Do NOT ship it as `service.mp3`.
- Existing private staging on the extension Hostinger contains the same MP3; there is no alternate inactive version in the audio database (only one mapping). Reference [read-only GitHub Actions run 39149309411](https://github.com/manufact-test/nomusic/actions/runs/39149309411).

## Actually prepared on website Hostinger

An isolated `00:43–00:54` excerpt **«С CELIKOM»** has been generated from a verified read-only stream of the library source by GitHub Actions, and copied *only* to:

`/home/u235811320/domains/lemonchiffon-narwhal-791953.hostingersite.com/celikom-private/demo-audio/clips/restored.mp3`

The original extension audio, its DB, paths and extension configurations were NEVER modified. The private excerpt hash is `d14e926aa506ec8ad3112cd73c516e935be1dca612e83dc46bca8c0f5a8342b5`, around 11.05 sec. Hostinger returns HTTP 401 without credentials; [run 39149625932 PASS](https://github.com/manufact-test/nomusic/actions/runs/39149625932). This file is not a publicly accessible download. The local user-facing `CELIKOM-with-00-43-00-54.mp3` is a correctly labeled independent 11s clip, but its digest can differ from the runner's FFmpeg 6.1 encoder output.

## Genuine «Без CELIKOM» current Yandex audio: source blocker verified

The required **current Yandex stream** is the authorized playback for track `144530503` (previously observed stream hostname `strm-ams28.strm.yandex.net`, duration 180.953s), but a full user-authorized file or a playable 00:43–00:54 segment was **not provided or stored**. The current alternative is NOT in CELIKOM's DB or staging directory. Existing test only checked playback/replace in the Yandex app, not captured current audio.

Official Apple previews of two related releases are only 29.95s long and after audio waveform alignment against the owner's 3min MP3 start at 0.03s and 119.98s, so NEITHER covers target 00:43–00:54 (high correlation to current stored recording: 0.77 and 0.88). [Audio correlation run 39149029637 PASS](https://github.com/manufact-test/nomusic/actions/runs/39149029637). A public anonymous Yandex request from the US GitHub runner returned HTTP 451 metadata and 403 download-info, [probe run 39149224901](https://github.com/manufact-test/nomusic/actions/runs/39149224901). No login token, subscription, bypass or file from the service is accessible to the present tools. **Do not invent «Без» by duplicating/restyling the replacement, or labeling the same audio as two different versions.**

## Player code / safety

The JavaScript, PHP post-render, CSS and staging-only streaming route are committed in `website/` on the working branch. Chromium with independently generated synthetic test tones validates Play/Pause, progress, pause-safe switching, seeking, and synchronization at 1440px/390px ([run 39147057713 PASS](https://github.com/manufact-test/nomusic/actions/runs/39147057713)); no fabricated tones are served to users. `CmsV10OwnerMotion.php` now guards availability with the exact verified SHA-256 of the private restored clip plus a distinct source-file hash. Therefore two equal sources cannot activate the compare player.

**Next required dependency:** obtain current Yandex Music version for track `144530503` as an authorized full audio file or timestamp-aligned audio capture, NOT manually cropped; our automation will create the 11s isolated clip. No reason to ask user to crop. Once true `service.mp3` source exists, stage privately, verify duration and content, deploy PHP/CSS/JS plus dedicated player asset with backup/rollback, inspect protected HTTP Range, run authenticated Chromium Play/Pause/seek/swaps, then request owner's desktop approval before responsive review.

**Absolute exclusions:** no edits to `extension/`, `server/`, `android/`; no rewriting library source, SQL mappings or hashes, no merging PR #6, no changing approved v10 layout/header/artwork or production release disabled gate. Last installed website version v5.10.

## Staging cutover guard prepared, but intentionally rejected incomplete media

[Audio v5.12 staging workflow](https://github.com/manufact-test/nomusic/blob/feature/api-range/.github/workflows/celikom-v512-audio-deploy.yml) enforces private presence of **two distinct** verified clips before touching PHP/JS/CSS, then offers private backup/rollback, two authenticated HTTP Range tests, and real Chromium (desktop/mobile) Play/Pause/seek/swap checks using [OwnerV10LiveSoundBrowserTest.py](../../../website/tests/OwnerV10LiveSoundBrowserTest.py). First gated run [39150146984](https://github.com/manufact-test/nomusic/actions/runs/39150146984) correctly refused execution with code 12 `BLOCKED_MISSING_GENUINE_YANDEX_ORIGINAL; nothing installed`. The output is an **expected incomplete-input gate**, NOT evidence of broken staging or a completed A/B player. No site files changed. Approved staging v5.10 remains active; original private restored 11s clip remains safely staged.

The hard stop will remain until the actual Yandex-stream `service.mp3` is available. Do not fake it or copy `restored.mp3` into that slot.
