# CELIKOM Android 0.3.61 — cold-join forensic checkpoint (31 October 2026)

Status: **source/log investigation only; no audio runtime change and no new APK**. Scope: Android branch `feature/android-unified-preparation-seek-gate`. Preserve the immutable partially accepted 0.3.61/code62 HONOR baseline and existing admin-only unreleased offline incident journal.

## Evidence and method

Investigated the owner's private combined 0.3.61 diagnostic held outside GitHub (three separate app runs: 02:13:50, 02:46:21 and 02:54:43, +03:00). Parsed each `run_start` separately, aligned confirmed `replacement_source_boundary` with its first subsequent `replacement_transition_complete` **before the next boundary**, and classified cache reuse and failures separately. Do not place the raw private diagnostic, track titles, account details or raw identity keys in this repository.

Among confirmed new-song boundaries:
- **21 fresh-stream successful joins**: source boundary → first exclusive replacement command **523–1073 ms**, median **733 ms**.
- For the same 21 boundaries: boundary → successful backend `replacement_resolve` **62–240 ms**, median **133 ms**; boundary → `replacement_stream_ready` **311–712 ms**, median **458 ms**; stream-ready → decoder prepared **27–63 ms**, median **37 ms**; prepared → handover **118–332 ms**, median **274 ms**.
- One additional successful next-song boundary reused previously cached audio: **261 ms** total, showing that on-demand stream acquisition is a material part of fresh joins.
- Three late boundaries in the second run did not complete an audio handover before the next boundary or the diagnostic ended. Two `resolve` attempts reported `timeout`; one intervening resolve returned after slow `config` (**2489 ms**) and `resolve` (**1036 ms**) HTTP operations, but the source moved on before audio was joined. One `replacement_stream_failure(IOException)` was also recorded in that run, duration around **9604 ms**. These are genuine intermittent request failures, not proof of the failing network hop.
- The 28 observed read-only next-item candidates across these runs had `metadataComplete=false` and `prefetchStarted=false`. The present source cannot safely authorize a particular next replacement merely from those incomplete candidates.

All figures are **software event/command intervals**, not acoustic measurements. `hardwareOutputMeasured=false` and Bluetooth/device pipeline latency can differ. In particular, source audio is deliberately retained during resolve/stream/prepare/seek and transferred only after alignment. It is therefore plausible to hear the original for a fraction of a second at a cold boundary; these data do not prove any unobserved physical overlap or silence. The Yandex Music smooth-transition setting is not recorded in this diagnostic; do not classify specific runs as ON or OFF retrospectively.

## Code trace (unchanged)

- `ReplacementEngine.sourceBoundary` cancels the prior identity and restores source before new verification.
- `ReplacementEngine.update` calls `NativeApi.resolve` for the newly verified identity; `NativeApi.checkedConfig` can add a config request after a 15-second validation window; successful resolve then enters `stream`.
- `BufferedAudio.initializeForPlayback` must obtain a validated initial range before `MediaPlayer.prepareAsync`.
- First alignment and exclusive ownership transfer are gated by `AudioOwnership` and a confirmed advancing decoder clock.
- The current `SourceEventArbiter`/read-only next-item signal does **not** provide a verified next track identity in the observed runs. Do not add an independent predictive playback controller or authorize unknown audio.

**Conclusion:** Healthy cold joins in the captured sample are generally around 0.5–1.1 seconds in the command trace. The dominant variable time is on-demand stream acquisition plus conservative clock/ownership handover, with independent intermittent network outliers. There is currently no proven single Android defect whose removal can safely guarantee seamless zero-delay joins. A cache hit is demonstrably faster, but an unverified future identity must not drive prefetch. Optimizing the clock gate blindly risks the accepted pause/seek behavior.

## Exact next evidence needed before an audio fix

1. On installed 0.3.61, set Yandex Music **«Плавные переходы между треками» OFF** and leave it OFF for the whole test. Keep the existing app connected and play 3–5 songs that have a CELIKOM replacement; let at least three finish naturally.
2. When the original is heard too long before replacement, record the approximate phone-local time and whether Wi-Fi/mobile, VPN and Bluetooth were in use. Distinguish natural boundary, manual Next, pause/resume and seek; do not infer a human seek from `userSeek=true`.
3. Export the **full owner-only combined audio diagnostic** while connected, as close to the event as practicable. The not-yet-released anonymous incident journal cannot replace this audio-timing trace. If network is down and the full diagnostic is unavailable/empty, report that diagnostic blind spot and retain any offline journal after its future release.
4. Reconstruct the precise failing chain (identity, config/resolve, stream, prepare, seek, ownership) and identify a measurable deviation from the healthy joins above. Build a deterministic failing host regression for that observed chain **before** a minimal Android-only code change.
5. Full regression gates: pause/resume, manual seeks, Next, natural end and expected tail, reconnect/VPN, route changes, cancellation, 15 virtual hours / 300 transitions, signed DEX provenance. No APK publication until one tested release bundles the audio fix and admin-only offline journal. Physical HONOR audio acceptance must remain separate from passing CI.

Related: [authoritative 31 October handoff](HANDOFF-2026-10-31-AFTER-0361-INCIDENT-AUDIO.md), [HONOR 0.3.61 QA](AUDIO-0361-HONOR-POSITIVE-QA-AND-TAIL-2026-10-31.md), [offline incident journal](ANDROID-INCIDENT-JOURNAL-CHECKPOINT-2026-10-31.md).
