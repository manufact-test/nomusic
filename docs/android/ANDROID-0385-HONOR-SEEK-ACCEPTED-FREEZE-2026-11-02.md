# CELIKOM Android 0.3.85 — HONOR owner accepts seeking; freeze this audio baseline (2026-11-02)

## Owner listening verdict — IMPORTANT

On HONOR NTH-NX9 / Android 13 the owner installed 0.3.85 / versionCode 86 through the existing Android update flow. His immediate listening report was unusually clear and positive:

- Ordinary finger seeking, and seeking after Next: **NO audible lag observed**, across the tested songs.
- The beginning/new-song replacement join is **much better** than before, and sometimes imperceptible. It is not perfect and varies by song; the owner has **not** acoustically accepted all intros.
- Do not replace the working full-local-file seek path, modify the seek/ACK pipeline, or revert to network-backed sparse `MediaDataSource` as a speculative intro fix.
- This is a real-user acoustic verdict, not a calibrated waveform/PCM measurement. Preserve both facts, without overclaiming perfection.

## Independent analysis of owner's new combined journal

Private input: `CELIKOM-combined-20261102-101047.txt` (2,897 lines; contains 0.3.83, 0.3.84, and 0.3.85). The raw diagnostic must not be committed. The last run starts at line 1,959 and contains 939 events; it lacks a closing `run_end` event, so it is a partial journal. Compare distributions as **separate listening sessions**, not identical paired trials.

| Field | 0.3.84 (previous) | 0.3.85 (new) |
|---|---:|---:|
| Source-path `replacement_seek_ack` | stream (34/34) | full_download_file (41/41) |
| ALIGNMENT seek ACKs | 25 | 36 |
| ALIGNMENT median | 73 ms | **41 ms** |
| ALIGNMENT maximum | 751 ms | **86 ms** |
| ALIGNMENT >=250 ms | 6 | **0** |
| `replacement_stream_seek_data_wait` | 2 | **0** |
| WARM ACKs / max | 9 / 64 ms | 5 / 91 ms |
| Confirmed user-position jumps within the same item (>1 s) | 18 in prior owner review | **30** |

The new 0.3.85 run includes 38 source discontinuities: 30 actual position jumps within the same item and eight index-changing transitions. `userSeek=true` on index changes does not by itself prove a physical Next tap. All 41 replacement seek acknowledgements had `rangeWaitObserved=false`, `staleOperation=false`. The full 36 ALIGNMENT callback distribution is 15–86 ms; the median is 41 ms.

Eight replacements were automatically fully downloaded into the temporary app-private cache, each followed by a `full_download_file` join. Download durations were 1,255–4,592 ms (1.3–4.6 seconds); these timings and decoder preparation **still matter at the start of songs**, even when the original is audible. Seven local-decoder prewarm-motion events took 132–219 ms. Eight `audio_command_anomaly` records are exclusively `expected_same_song_blend` with zero recorded commanded-silence duration; they are normal commanded overlapping volume during the complementary join, not proof of acoustic overlap. Four recoveries were ordinary `source_end`/`replacement_end`. There were **zero full-download failures** and no explicit stream wait events.

This evidence strongly supports that replacing network-backed streaming seeks with a local full file removed the previous network-bound seek long tail on this device. It does **not** prove the actual speaker PCM phase or eliminate other possible failures on different networks/devices.

## Exact preserved source

- Signed/published 0.3.85 functional source: merge commit **`053b7d59beb53db5f30b942feba35e51a1ab256a`**.
- NEW DO-NOT-EDIT backup: **`backup/android-0385-honor-seek-accepted-20261102`**, created from that exact functional source SHA.
- Older backups remain intact: `backup/android-0384-before-local-seek-experiment-20261102` (`d434d442aeed7a84f17126da48c6a08b752c825d`), `backup/android-0382-stable-listening-baseline-20261101` (`2e03aca1dad0f89b3d71f871270e09f8bb9f143f`), `backup/android-0378-original-before-cached-join-20261101` (`bf011dcf1a70c504883a8e5e742e0b038f41d9b0`).
- Keep the live OTA manifest at 0.3.85 / versionCode 86, APK SHA256 `e23c962d969129c5b839ed3676e36d6a337342e2761bde852e2048bbf1bda88a`. Do **not** publish another version for this documentation/test checkpoint.

## Technical prevention against repeating old regressions

1. A new required regression `tests/check_0385_seek_baseline.py` pins exact SHA-256 fingerprints of the accepted production seek-submission method, its asynchronous ACK completion method, and the `prepare()` full-local-file selection block. It also asserts that the production constructor still selects `fullFileExperiment=true` by default.
2. `TestFullFileSeekExperiment` additionally verifies that the **real production constructor** enables full-local-file playback, not merely a test-only constructor override. It already exercises first attachment, seek, Pause, Next, timeout, cancellation, and cache cleanup.
3. The host suite runs both the accepted local path and the legacy streamed baseline only in test injection. This preserves diagnostics/regressions without reinstating streaming on the installed app.
4. All future Android work should branch from a safe current commit while leaving the frozen backup ref unchanged. Treat a change to these seek fingerprints as a **deliberate owner-approval gate**, not a test that can be silently deleted or updated to make CI green.
5. This guard intentionally does not freeze unrelated UI/backend code or all cold-join investigation. It is a tripwire and rollback point, not a claim that GitHub refs are cryptographically immutable or that all acoustic regressions are theoretically impossible.

## What to do next (not now)

Focus ONLY on occasional imperfect beginnings/Next attachment after the owner has enjoyed and confirmed this baseline. First correlate a short **single problematic intro** captured with actual audible sound against a contemporaneous diagnostic, if the owner elects to supply it; Android's internal screen recorder may omit protected playback, in which case an external microphone recording can be more trustworthy. Do not demand another exhaustive scrubbing test. Separate full-file download time, local muted prewarm, decoder clock gate, and 160ms complementary join. Explore a streaming-start/background-local hybrid only on a separate nonpublishing branch with explicit proof and the golden seek behavior preserved. No blind timing tweaks.

**Acceptance status:** 0.3.85 accepted by owner as the new **seeking-listening baseline**. Intro/Next acoustic polish remains open. No new APK was created for the freeze.
