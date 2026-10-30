# CELIKOM Android — checkpoint: Unified Audio Gate A / observational Gate B — 30.10.2026

> **UPDATE — Gate D seek single-flight / native source continuity (30.10.2026):** latest CI-green code `a560d0051586051979627fc16bc473c394b20501`; [full CI SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41029927026). See new section at the bottom. Original signed 0.3.54 AUDIOFIX and all desktop code unchanged; **no new signed APK**.


**Last fully CI-verified Android code:** `d1034816796d6fc1a421d559304f5c5218317c66` on `feature/android-unified-preparation-seek-gate`.

**CI:** https://github.com/manufact-test/nomusic/actions/runs/41027989995 — SUCCESS: all host regressions, Android API 36 Java compile, D8, source/DEX provenance and unsigned packaging artifact checks. Separate earlier successful runs: [Gate A](https://github.com/manufact-test/nomusic/actions/runs/41027153541) and [read-only Gate B](https://github.com/manufact-test/nomusic/actions/runs/41027778183).

**Scope:** Android phone only. No desktop, extension, Ad Protection, backend, API, auth implementation, catalogue, website, production DB or signing material changed. Only `android/native-companion/**`, `docs/android/**`, and Android-only push trigger in `.github/workflows/android-0348-validation.yml`. Original signed and installed `0.3.54 AUDIOFIX` remains unchanged; **no new APK has been built or signed**, and no device listening is claimed.

## Implemented and checked

- `AudioOwnership` now declares a single common event vocabulary for `PREPARE`, `PREPARE_READY`, `SEEK`, `BUFFERING`, `PAUSE`, `RESUME`, `HANDOVER`, `BOUNDARY`, `ROUTE_LOSS`, `LOGOUT`, `STOP`. The audio command operation epoch is revoked by transitions, separately from the track/decoder source epoch.
- Immutable `AudioOwnership.Ticket`: `sourceKey`, `sourceEpoch`, `operationEpoch`, `accountEpoch`, `replacementId`, `version`, `durationMs`. `dataCurrent` protects staged data; `commandCurrent` additionally gates audible handover callbacks. A seek may retain current-song data but invalidates the prior audio command.
- `AudioOwnership.preparing()` refuses background preparation takeover while replacement is active, aligning or paused. `PREPARE_READY` alone cannot change owner state. Installing a verified source effect **does not automatically grant alignment**; the active playback path is responsible.
- `ReplacementEngine` ties preparations, file acceptance, `onPrepared`, and fade handover to those tickets and revokes handover commands on seek, pause/buffer/resume, boundary, stop or route loss. On account generation change, engine stops and safely restores original audio; old resolves and downloaded files cannot become new-account output.
- New `TestUnifiedAudioTransactions.java` registered in the mandatory host suite: prepare-ready vs seek, pause/buffer/resume, track repeats, ten rapid skips, route loss, stop, wrong edition/version/duration, account change and an actual paused-source prepared decoder. Existing playback/phone HONOR/long-run/clock/stream/exclusive-output regression checks retained, not disabled.
- Read-only Media3 **feasibility instrumentation**: when supported, every ≥2 seconds inspect controller timeline's next media item and whether title/artist/duration are available. At confirmed source boundary, report whether predicted next item matches and lead time. New sanitized `source_next_readonly_observation` and `source_next_readonly_boundary` events contain booleans/counts/timing only; no candidate identifiers or metadata logged. `SourceEventArbiter.LookaheadEvidence` remains observational. **There is no network prefetch, second decoder or new DSP control.** Negative tests check stale prediction, mismatch, same-item repeats and reset/reconnection.
- Android-only CI workflow triggers on the new work branch as well as old Android branch. Signing secrets are never sent to CI.

## Verified checkpoints / rollback

1. Baseline signed-device code: `8128307d0daf95f3386b85791db5347e3ec56357`; handoff doc ref `9399ccf156561dac094c34ca847518466821f076`.
2. Green initial ownership/data tickets: `5dd36d0c3678f8b78f451484ebd41d89232a0377`; rollback branch `backup/android-unified-gate-a-green-20261030`.
3. Green lookahead evidence, still no prefetch: `b763fd854cce02ddf6f95bb30d2af92743d63341`; rollback `backup/android-unified-gate-b-observation-green-20261030`.
4. Green account-epoch source guard: `d1034816796d6fc1a421d559304f5c5218317c66`; rollback `backup/android-unified-account-gate-green-20261030`. The next documentation-only commit will differ from this code SHA.

## Still NOT resolved / next safe development sequence

1. **Gate A is only partially implemented.** The common event/ticket contract and critical data-to-audio boundary are real and CI-green, but `ReplacementEngine` still has legacy independent `transition`, `generation`, `pausedAt`, `seeking`, `fading` and `handoverPending` flags. `AudioOwnership` has event epochs but NOT a fully pure reducer; do not pretend it is already a complete transaction coordinator. Complete convergence carefully through actual engine tests, with no separate seek or preload audio controller.
2. **Gate B only instrumentation ready; physical observation pending.** Media3 lookahead availability, identifier correctness and lead time for this Yandex Music build on HONOR are *not yet confirmed*. No prefetch should be enabled until reliable observations support it. If not supported, optimize only current-track handover under the same owner.
3. **Gate C blocked.** Future-song prefetch and early start remain disabled. Never infer a next track from a loose queue, and always require fresh actual-track authorized server resolve/identity/edition before playback.
4. **Gate D/E incomplete.** Continue unifying seek completion, buffering, pause, handover and asynchronous callback cancellation under one output lease. `MediaPlayer.onSeekComplete` has no request-specific native callback ID, so ensure old seek callbacks cannot commit a newer transition. More adversarial actual-engine tests for paused/buffered seek, downloader delay, route loss and rapid skips. Do not retune random timeouts to hide races.
5. **No sound quality claims.** Prior 0.3.54 HONOR log had ~1.05–1.72s detection-to-transition-complete (avg ~1.31s) and 26 `audio_command_anomaly` events in the latest 132.389-second run. These are commanded-state traces, not physical/Bluetooth audio; this code checkpoint does not establish improved seamlessness. A future signed release with versionCode >55, original private signer and real HONOR audio/seek test is required before claiming final resolution. Keep signed 0.3.54 AUDIOFIX and old rollback versions intact.

Follow `UNIFIED-AUDIO-OWNERSHIP-PLAN-2026-10-30.md` and the original `HANDOFF-2026-10-30-UNIFIED-AUDIO.md` for background, signing rules and scope. **Never publish private keystore or user diagnostic logs into the public repo.**


## Update 30.10.2026 — Gate D: untagged seek acknowledgements and native source continuity

**Code SHA:** `a560d0051586051979627fc16bc473c394b20501` — [GitHub Actions SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41029927026). Earlier core code without the final diagnostic/architecture check: `0f5bf205bcd76f88684a96ee02055ac40a301225` — [CI SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41029724476). Safe rollback branches `backup/android-unified-seek-original-restored-green-20261030` and **`backup/android-unified-gate-d-seek-singleflight-green-20261030`**. This is a **development checkpoint**, not hardware-validated audio.

### Native single-flight under AudioOwnership

- Android `MediaPlayer.OnSeekCompleteListener` provides no request ID. The actual engine previously distinguished a warm alignment seek from normal seek by mutable `warmSeekTransition` flags; pause/route/seek could clear them while an old seek still operated on the same decoder. A late callback could then incorrectly be treated as a newer alignment completion.
- `AudioOwnership.issueSeek` now registers at most **one in-flight native seek** per decoder and records kind `ALIGNMENT` or `WARM` with `operationEpoch` and submission time **before** issuing `MediaPlayer.seekTo`; this handles synchronous and asynchronous completion. `acceptSeekCompletion` consumes that pending request exactly once. New native seeks cannot overlap a pending callback; `retireDecoder` and `stopped` clear the flight.
- Source seek during warm handover revokes the previous fade/output decision, silences/pauses the decoder and restores original gain. No new seek is issued until the old callback has been acknowledged or the decoder's bounded seek budget expires. The acknowledged old warm callback **cannot authorize playing**, but triggers a fresh seek to the live current source position where appropriate.
- A paused alignment callback may report a useful final decoder position even though its output epoch was revoked. It may be reused **as position data only**, under source/identity match and strict live-position tolerance; an invalid/replayed output command is never re-granted. The accepted 0.3.54 short pause and 5ms alignment regression was preserved.
- Deadline/expiry is bounded; unacknowledged old warm seek eventually follows existing stream/local-file fail-open fallback. No new decoder or speculative preloader.

### Keep original audio audible while the secondary seek is waiting

- Previously, a seek from already-audible replacement often left the Yandex native input at `-100dB` after secondary gain was set to zero. The Android network decoder could then spend hundreds or thousands of milliseconds seeking, producing **commanded silence**.
- `AudioOwnership.sourceGainDuringAlignment()` now restores the verified Yandex original gain to **0dB only after the replacement decoder is commanded silent and paused**, while retaining the *same* attached `DynamicsProcessing` effect. No new effect attach/release cycle is needed for this transition. `originalMix=1`; a successful alignment re-enters the existing break-before-make original fade, exclusive grant, then replacement fade.
- A manual stop/return during a pending seek stops directly to original; it may not launch an audible replacement return-animation through a seek. `replacement_sync.originalStillMuted` logs the true commanded gain state, not merely whether an effect instance is attached. Architecture check requires the new gain path to remain inside `AudioOwnership`.

### Release-blocking tests added/updated

- `TestUnifiedAudioTransactions.java` includes an actual streaming decoder with **pending warm seek + new explicit user seek**; old completion cannot perform the new seek or revive the old fade, and exactly one new native seek follows acknowledgement.
- Another actual streaming replay covers **pending warm seek + pause/resume + changed live position**, with no overlapping seeks or premature output.
- Owner test verifies repeated completions are ignored, output epochs are invalidated across pause, and the second seek starts only after the first completes.
- Another real-engine test checks the **same verified source effect remains attached** while the original is restored and secondary decoder seeks silently, plus manual return during seek cannot raise secondary audio.
- Old `TestEngine` expectation that the original stay muted during seek was deliberately replaced with the safer invariant (gain restored, replacement zero). Existing HONOR, car/Bluetooth, long-run, source arbitration, streaming, security, compilation, DEX and packaging negative tests all pass. Tests are *simulation/host evidence*, not actual sound waveform measurements.

### Important limits / next steps

1. This advances Gate D but **does not complete the full pure event reducer**. Old `ReplacementEngine` flags and some asynchronous lifecycle paths remain. Complete convergence only with adversarial tests and one audio owner; do NOT create a separate next-track preloader or competing seek controller.
2. Single-flight prevents overlapping seeks but Android callbacks still have no native request ID; a pathological duplicate callback arriving only after a later seek has begun cannot be fully distinguished without hardware observation. Continue fail-open and positional validation; never claim a mathematical guarantee of every OEM callback behavior.
3. Lookahead remains **read-only observation**, not verified on HONOR. Gate C future-song prefetch and speculative audio remain **disabled**. No fresh resolve/entitlement or edition checks were relaxed.
4. Prior user-recorded 0.3.54 mean detection-to-handover ~1.31s and 26 command-anomaly observations are **historical baseline**, not measurements of this code. Real acoustic/Bluetooth startup and seek behavior still require an eventual properly signed versionCode >55 and HONOR physical listening + sanitized log. **No APK or new user test requested at this checkpoint.**
5. Original owner signing ZIP and private user logs remain outside the public repository and CI. Installed signed `0.3.54 AUDIOFIX`, `feature/android-0348-audio-ownership-stabilization`, desktop `feature/api-range` and draft PR #22 are unchanged.
