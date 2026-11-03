# Desktop intro preparation experiment 0.4.68

Owner authorized an isolated desktop experiment on 2026-11-03, retaining 0.4.67 for rollback. Android is owned by another chat. No Android, server, auth, entitlement, upload, or live deployment changes in this experiment.

## Frozen reference

- Accepted desktop 0.4.67 source: `78a1072c212fa3c8f1256b3524c353a5883eabcc`.
- GitHub archive branch: `archive/desktop-0.4.67-20261103`.
- ZIP: `celikom-extension-0.4.67.zip`, SHA-256 `fe2611012a1387eba81ffd35e21b00408e7502ce76c8b051df52da026d1d48e1`.
- Persisted owner archive: `libfile_6c56eea92ebc8191b3066091ca272d0a`.
- Experiment branch: `feature/desktop-068-intro-start-20261103`; do not advance `feature/api-range` or deploy the server.

## Evidence and limits

Diagnostics 20261103-180941: track 125724528 (тело) PREPARING 18:08:48.636Z to ACTIVE 18:08:49.823Z; original native play at 18:08:48.629Z. Preparation 1187 ms. Replacement still muted, paused, readyState 0 when native position was 512 ms. By the next retained snapshot native/replacement positions were 1390/1348 ms. The log does not contain captured audio and cannot prove exactly which phoneme was lost.

Diagnostics 20261103-182003: five retained preparation intervals 317, 479, 364, 304, 306 ms. Detailed trace covers only three complete recent joins. For all three the original clock advances while replacement is still loading and muted. Successful API responses do not measure signed audio body duration or native decoder latency. These are controller activation times, not measured acoustic latency.

## Narrow changes

1. Warm a validated track at HAVE_METADATA only when paused, not seeking, and position <=250 ms. Keep all identity, confidence, duration, rights and generation checks. No guard request at metadata-only readiness. Activation still requires the existing playable readiness and bridge guard checks. Mid-song buffering/seeks preserve original admission rules.
2. MP3 MSE initial Range is 64 KiB, followed by contiguous 512 KiB chunks. No dropped bytes, no transcoding, no changed sample rate, no tiny steady-state chunks. Existing status, MIME, range, size, timeout, retry and abort checks retained. Large ID3 blocks continue loading until the decoder has data. M4A native path unchanged.
3. Diagnostics retain twelve successful join timings (track ID, preparation/resolve/load milliseconds, native position at activation). No signed URLs, credentials or audio contents. Not a measurement of audible output.
4. Version only: 0.4.68. No master pause/resume overrides, forced rewind, clock offsets, changed sync thresholds or new UI.

## Validation and owner check

Unit regressions include metadata warmup without early guard, paused activation, Stop fencing late decoder completion, invalid metadata rejection, bounded history, contiguous MSE ranges, transient HTTP retries, revoked URL handling, timeout recovery and unchanged seek behavior. Dedicated isolated GitHub workflow additionally runs existing actual Chrome synthetic MP3/M4A playback, buffering, seeking, pause and restoration scenarios. Its outcome must be checked before delivery.

This experiment reduces work on the startup path; zero lost opening audio is NOT established. Large metadata, network delays or a track only identified after playback can still cause a late join. No claim of fixed Yandex outages.

Owner check in one session: repeat тело and several Next transitions, one pause/resume and one seek; export diagnostics once after the session. Compare first words and startupHistory against reference. No per-song diagnostic collection required.

Rollback: stop playback, replace unpacked files with the preserved 0.4.67 ZIP, reload the existing extension in chrome://extensions, refresh the Yandex tab, then start. Keep the existing extension installation and account data.
