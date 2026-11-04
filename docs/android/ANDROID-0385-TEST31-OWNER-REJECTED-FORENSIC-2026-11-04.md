# CELIKOM Test.31 — HONOR owner rejection, fresh video and combined-run forensic (2026-11-04)

## Verdict and exact session boundary

**OWNER VERDICT: Test.31 REJECTED for acoustic quality.** The owner reports continued audible «пшик», unequal first joins, spontaneous restoration of the original after CELIKOM connected, and additional delayed reattachment. **Do not call CI success an acoustic success, create a Test.31 accepted backup, or ask the owner for more of the same diagnostics.**

The private `CELIKOM-combined-20261104-222444.txt` contains historical Test.29 runs starting at lines 4 and 1302. **The fresh Test.31 run begins exactly at line 1996** (`run_start` version `0.3.85-test.31`, HONOR NTH-NX9 Android 13, 2026-11-04 22:21:42 +03:00). Only lines 1996–3425 form this field verdict. Corresponding video `SVID_20261104_222200_1.mp4` has 149.16 s internal audio and video; it begins a little after app run start. Keep these private files outside Git.

## Demonstrated distinct failure classes (do not collapse into one fade/timing knob)

### A. New-track first handover actually runs a 160ms commanded blend — but is still audible

* **16 `replacement_unified_join_start`** and **16 `replacement_join_transport_summary`** events in the fresh run. The app now commands the 160ms complementary mix; the `audio_command_anomaly` reports 16 `overlap_commands` explicitly classified `expected_same_song_blend`.
* Hence restoring the **commanded** 50/50 midpoint did not fix the owner-observed «пшик». The current tests prove only *gain commands*, not synchronized hardware output, equal PCM masters, or Bluetooth/rendered sample continuity. Do not assert the original song and replacement have sample-level phase agreement; do not keep changing 32/48/160ms by intuition.

### B. Four other post-seek grants bypass that blend entirely

* At elapsed **20,478; 67,180; 112,236; 177,266 ms**, `replacement_transition_complete` reports `joinMode=exclusive_single_turn`, `rampMs=0` after source-position/seek sequences. These are **not** the sixteen first cold joins, but can create another abrupt audible replacement after a seek or transient BUFFERING pause.
* E.g. at 67,013ms a hot cached seek is requested, at 67,078ms Media3 reports a transient non-playing/buffering state, at 67,099ms the cached seek ACK arrives, after which a redundant ordinary correction and an instantaneous grant occur at 67,180ms. Test.30's hot-seek code does not eliminate every re-grant path.

### C. Incomplete streaming data is promoted to audible ownership, then starves

* **«Толер»** source boundary 134,335ms → first blend completes 141,583ms: **7.248 seconds**. At 136,969ms the sparse source was declared ready with only **131,072 bytes** cached. Alignment `seekTo` waits include ~2.4s and ~1.55s. At 143,656ms — **2.073 seconds after granting the replacement** — `replacement_buffer_wait` restores the original, with only **475,114 cached bytes**. The video shows the track during this period. This proves a CELIKOM continuity failure after output handover.
* **«Метамир»** source boundary 151,363ms → blend completes 163,139ms: **11.776 seconds**. Stream ready 157,287ms after the source started, with multiple foreground demand range fetches, waits and corrections. At 161,301ms, before the eventual first grant, streaming enters `replacement_buffer_wait`. At the video notification curtain near its end, CELIKOM displays **«Подготавливаем версию CELIKOM...»** while Yandex's Metamir is already playing.
* Compare local/prewarmed tracks **«тело»** boundary 50,948ms → complete 51,468ms (**0.520s**) and **«Три слова»** 58,945ms → 59,425ms (**0.480s**). This is why songs with apparently similar identity diverge: their **buffer readiness/source cache state** is not the same. It is not evidence that the MP3 titles themselves cause the problem.
* The current sparse source starts after a small number of validated 128KiB blocks; the first join has no tested contiguous *future playback runway*. `BufferedAudio` can therefore block inside a decoder read after ownership has switched. `holdPrefetchForSeek()` may suppress speculative fill during clock-gated handover; owner must inspect this in a dedicated streaming-state redesign.

### D. RASKOL seek UI vs available Media3 state is discrepant in this run

* On the video, Yandex's `Нас не понимают вообще` (Космонавты, RASKOL id `42884423`) shows **~2:11** while the around-corresponding CELIKOM public Media3 / own output is still around **50s**. At 111,740ms CELIKOM issues an alignment native seek to **50,146ms** — the only target it currently knows. Later at 116,861ms it receives the ~134,392ms position and a cached native hot seek ACK completes in **54ms**; another at 120,982ms completes in **43ms**.
* This is **not** proof that UI-to-audible finger response is 43–54ms. The visible slider and the public Media3 snapshot differ before that; event observability requires separate investigation. Do not claim merely speeding up `MediaPlayer.seekTo` fixes this gap.
* **«Дым» is not present in this fresh Test.31 session**; its repeated historically reported lag remains unresolved, and no new claim about its behavior should be drawn from this particular file.

## Architecture-directed next work (one combined experiment only after tests)

1. **One-per-track owner transfer contract:** separation of preparation vs audible grant; avoid repeated instantaneous `exclusive_single_turn` after a seek or transient BUFFERING. A seek that genuinely needs source-audible fallback must return through an intentional guarded audio entry, not an unchecked immediate source-to-decoder flip. Cached hot seek already audible should remain in place with no re-entry.
2. **Verified playable runway before sparse-source audible grant:** the current number of cached bytes alone is insufficient; verify *contiguous bytes ahead of the decoder play cursor*, ensure foreground demand/prefetch can fill it, impose a finite readiness policy, and keep original audible while unready. Preserve quick joins for fully cached/primed tracks; do not blindly change every song to a long full-file download. Prevent source→replacement→source flapping when buffered data cannot sustain playback.
3. **Acoustic validation beyond command logs:** a test can prove `original=1-mix` and `replacement=mix`, but not phase/mixing fidelity between independently clocked audio sessions. Use the supplied screen-recorded internal audio as forensic evidence with careful recording-time alignment, and test actual join sound transitions on device before any owner-acceptance claim. The recording is not necessarily Bluetooth acoustic PCM.
4. **RASKOL/«Дым» position source:** isolate UI→Media3 publication delay from actual decoder seeks, using permissible available inputs. No new sensitive Android permission, second controller or source capture should be silently added in the release route.
5. **Do not repeat former failed adjustments:** speculative 512KiB batching, non-overlap 32/48ms split fade, only changing milliseconds, and test-only audio flags that differ from production.

## Immutable pins and scope

* Test.31 original signed source `8f3bce6bb049d66ae1e30316ab4365bbd7c9f66b`, [CI SUCCESS #41891216645](https://github.com/manufact-test/nomusic/actions/runs/41891216645), original signed Library APK `libfile_a4aa619bae1c819187d651fb9900ad05`, SHA256 `124f45abad77cd70664f557161736fa76ac997b9c3f118f350665a9a2f326522`, test code `86116`. **CI passed; owner acoustic verdict rejected.**
* Test.23 **owner-accepted** backup `backup/android-0385-test23-owner-accepted-20261104`, SHA `251b6facc8739557ff962365da012d502ed3bac8`, original signed Library APK `libfile_301d98360e9c8191b8e05594f402d265`, APK SHA256 `c24260ee009381226c11e465b8a5482423af7811de589c64b3b8eb982483de6a` — untouched.
* Test.28 **owner-selected interim** backup `backup/android-0385-test28-owner-selected-20261104`, SHA `904ba52d5afbb5e77f4ee36e40d321d568896460`, original signed Library APK `libfile_dbc76474748481918f72b91a9eaea383`, APK SHA256 `973ee8565170d333c2ad7a8319f66c099c4afc2388228d3833562ffde7361b12` — untouched.
* Stable CELIKOM `pro.celikom.nativeprobe`, code86, Hostinger OTA not changed. Lower Test versionCode installation may require uninstalling only `pro.celikom.nativeprobe.test` or a newly signed recovery build at a higher code. A rebuilt APK is not an original byte-identical artifact.
