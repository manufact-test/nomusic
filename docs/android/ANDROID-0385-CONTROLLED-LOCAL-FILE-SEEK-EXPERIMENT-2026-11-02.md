# CELIKOM Android 0.3.85 — controlled full-local-file experiment (2026-11-02)

## Status and safeguards

- Source: `release/android-0.3.84-stable` at `c53cc467eaa6682e006e78d470bc1db5d19e43e2`.
- Experiment branch: `feature/android-0385-local-file-seek-controlled-20261102`.
- Test identity only: `0.3.85`, versionCode `86`. Physical HONOR acoustic acceptance is **NOT** established.
- Protected backups `backup/android-0384-before-local-seek-experiment-20261102`, `backup/android-0382-stable-listening-baseline-20261101`, and `backup/android-0378-original-before-cached-join-20261101` are untouched.
- No Android updater, backend, website, browser extension, database, catalogue, or account changes.

## Independent evidence review

The 0.3.84 owner journal is described in `ANDROID-0384-OWNER-RETEST-LOCAL-FILE-SEEK-PLAN-2026-11-02.md`. The raw phone text/video were not present in this repository checkout; do not claim an independent frame-by-frame reconstruction of unavailable attachments. The reported 25 ALIGNMENT callbacks include six >=250ms and only two explicit `replacement_stream_seek_data_wait` events. The four other slow callbacks **cannot** be attributed to HTTP by subtraction: MediaPlayer seeking, codec, scheduling, and source read instrumentation remain possible. Five joins used `stream`; ~1–2-second post-boundary completion intervals include lookup, prepare, clock gate, and handover commands, not necessarily speaker silence.

Earlier local-file cache-hit tests show that eliminating remote reads alone is insufficient for gapless sound: during Android 0.3.65, cached seek ACKs of 44–58ms still coexisted with command-level silence of ~136–147ms. The 0.3.79 local-file decoder-motion gate also lengthened one recorded join from ~267ms to ~651ms. This experiment explicitly does **not** restore that rejected policy or retune crossfades, seek correction thresholds, Pause, or Next.

Android references:

- [MediaPlayer](https://developer.android.com/reference/android/media/MediaPlayer): `seekTo` completion is asynchronous; `getTimestamp()` describes a media-time/system-time correlation, not the original Yandex PCM or observed speaker waveform.
- [MediaDataSource](https://developer.android.com/reference/android/media/MediaDataSource): `readAt(position,...)` may need an uncached byte range. In CELIKOM's `BufferedAudio`, a cache miss fetches the missing range over HTTPS.
- [MediaTimestamp](https://developer.android.com/reference/android/media/MediaTimestamp): a decoder transport timestamp cannot independently prove waveform phase alignment between separately owned output sessions.

## Exactly one playback data-path change

After **every new authorized live resolve**, a cache miss now invokes the existing `downloadFull`/`NativeApi.download` path instead of `NativeApi.stream`. This is the only product behavior changed in `ReplacementEngine`.

- Full file is downloaded automatically to `getCacheDir()` using the existing `AudioTransfer` implementation (30 MiB file ceiling, authenticated signed URL, transport generation/account lease, HTTPS response and identity safeguards). The experiment adds a 20-second download validity budget; on failure, the original remains audible and existing bounded retry rules apply.
- Once ready, the **existing** `acceptAudio()` creates a `MediaPlayer` with `setDataSource(file.getAbsolutePath())`. The existing local-file prewarm, source effect, seek, fade, Pause, Next, and decoder lifecycle are unchanged. The user never manually downloads a song.
- `recentAudio` can retain up to three validated files / 60 MiB within the foreground session, with fresh resolve on reuse. Normal Stop deletes the cache. Android may retain temporary cache files after process death until reclamation; this experiment does not claim instantaneous crash cleanup.
- Test-only constructor allows the deterministic host suite to run the frozen streaming baseline against the experimental local path; **the installed app has one hardcoded full-file behavior**, no A/B UI or additional app mode.
- Instrumentation emits `replacement_full_file_experiment_start`; existing `replacement_download`, `replacement_prepared`, `replacement_seek_ack`, `replacement_output_clock_sample`, and `replacement_transition_complete` are retained. `audioSourceKind=full_download_file` must appear, and no `replacement_stream_seek_data_wait` should arise for local seeks.

## Falsifiable expectations and limitations

1. **Expected:** once a fully downloaded file is prepared, a finger seek must not wait for a remote `MediaDataSource.readAt`/HTTP range; seek still waits for the Android decoder.
2. **Not promised:** first replacement note/Next cannot start before the full download, and local decoder prewarm can itself introduce delay. Some songs may remain on original if a slow connection exceeds 20 seconds.
3. **Not promised:** no acoustic dip/repetition. Original-source PCM/hardware output is still unobserved, and same song versions may differ by encoding/offset.
4. **Decision rule:** if local seeks remain slow in ACK or sound, investigate decoder/ownership timings rather than switching back and forth between numerous timer patches. If they become reliably faster but intros become worse, a separate *future* experiment may evaluate streaming start plus background full-file preparation. Do not conflate it with this A/B.

## Verification matrix

- `TestFullFileSeekExperiment`: new authorized full-file selection, absent streaming source, local decoder, initial handover, finger seek, pause/resume, manual Next, Stop/deletion, deadline, and stale callback deletion.
- Existing `TestStreamingEngine` and its slow-range/stale seek gates run with the test-only legacy stream selection to guard the frozen baseline. `TestCachedAudioRollback`, `TestHonor068SupersededAlignmentSeek`, all owner-state/clock and long-run tests still run.
- Local host `run_engine.py` and `check_release_contract.py`: PASS. Local SDK 36 unavailable, so Android API 36 compilation, D8, real APK provenance/signature verification, and publishing checks **must** be green in CI before owner installation.
- Only after a verified signed OTA candidate exists: ask for **one short HONOR test**, using the existing five familiar songs, specifically comparing seek delay versus longer intro/Next wait. No repeated diagnostic demands before hearing the result.

## OTA routing caveat

The installed CELIKOM updater reads **only the Hostinger `stable.json`**. A private GitHub Actions artifact or an isolated PR does not appear behind **Проверить обновление**. Delivering this test through the owner's requested in-app button therefore requires a versionCode 86 signed publish to that same channel. Treat it as an **experiment distributed via the stable transport**, not acoustic approval or a claim that 0.3.85 is stable. Do not modify the updater itself; verify and record the manifest and immutable APK receipt if and only if the build passes all gates.
