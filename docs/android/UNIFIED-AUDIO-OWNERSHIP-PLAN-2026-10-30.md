# CELIKOM Android — единый владелец аудио: технический план (2026-10-30)

**Status: PLAN / NOT IMPLEMENTED.** Подписанный 0.3.54 AUDIOFIX уже существует, но изменение архитектуры из этого документа ещё не реализовано и НЕ отправлялось на устройство. Ни одна новая APK в рамках этого checkpoint не выпускалась.

**Scope strictly Android phone only.** Repository `manufact-test/nomusic`; development branch `feature/android-unified-preparation-seek-gate` based on green code SHA `8128307d0daf95f3386b85791db5347e3ec56357`. Keep `feature/android-0348-audio-ownership-stabilization` (PR #22, DRAFT), `feature/api-range` (desktop), production backend/catalogue/website/CMS, Ad Protection and keys unchanged.

## Почему выбран этот путь — предупреждение владельца

Уже была негативная серия исправлений, когда подготовка следующего трека и перемотка/пауза внедрялись частями и противоречили друг другу. В 0.3.52 появились `AudioOwnership`, `ClockSupervisor`, `SourceEventArbiter`, но `ReplacementEngine` до сих пор содержит свои `generation`, `transition`, `pausedAt`, `seeking`, `fading`, `handoverPending`, `warmSeekTransition` и асинхронные callback'и, меняющие состояние в разных местах. Формальный шлюз для команд MediaPlayer полезен, но сам по себе не обеспечивает единую транзакционную координацию подготовки и seek. **Нельзя** делать независимые подсистемы "next song fast" и "seek stabilizer". Это снова создаст гонки.

### Актуальные факты по HONOR, НЕ обещания

Diagnostic: `CELIKOM-combined-20261030-105118.txt` (private upload; user report combines THREE runs). 
- 0.3.53 run 00:28:35 +03; 0.3.54 initial run 01:14:46 +03; **последний установленный 0.3.54 AUDIOFIX run 10:49:05 +03** on HONOR NTH-NX9 / Android 13 / Yandex Music 2026.09.5 #167.1gpr. Do not mix events from different runs.
- Last run duration 132389 ms; 28 `replacement_transition_complete`, 19 `replacement_source_buffer_resumed`, 26 `replacement_source_buffer`, 7 `replacement_outgoing_candidate`, 0 old `replacement_outgoing_reset`, 26 `audio_command_anomaly`, 0 `replacement_duration_mismatch`, 3 `replacement_bounded_tail_accepted`.
- Startup track handover roughly 1.05–1.72 s in measured examples (mean ~1.31 s). This is time from detection to completed handover, **not measured continuous acoustic silence**. Backend resolve, stream buffering, decoder prepare/seek and exclusive source→replacement rise all contribute. Previously 100ms source fade + 200ms replacement fade prevents overlap, but cannot eliminate late onset.
- At user seeks, decoder may take hundreds of milliseconds; transient native `STATE_BUFFERING` with `playWhenReady=true` is not user pause. The AUDIOFIX gate improved handling but commanded-silence episodes remain. Logs report AUDIO COMMANDS, not direct hardware/Bluetooth waveform measurements.
- 0.3.54 accepts verified measured tail differences up to 1500ms; do not loosen identity/duration guard blindly.

## One authority: required invariants

1. ONLY `AudioOwnership` authorizes *audible* output and MediaPlayer start/seek/pause/volume + Yandex-session `DynamicsProcessing` gain; never a second controller for upcoming track or seek.
2. `ProbeService` + `SourceEventArbiter` classify Media3 events, do not themselves emit new audio. A confirmed boundary cancels all old track work. Stale callback: no output side effects.
3. Every staged preparation/seek/handover has immutable ticket `{source key, source alias/album/track, source generation, playback epoch, user/account generation, expected replacement id/version/duration}`. Out-of-date ticket -> discard. Account logout, Stop, session change, route loss revoke tickets.
4. **Data-only prefetch** may read bounded metadata/files. It is not allowed to create/start a second audible decoder, mutate original gain, change AudioOwnership state from REPLACEMENT/ALIGNING/PAUSED, or seek active decoder. A prepared future file is *not* authorization to play; each track needs fresh backend resolve/entitlement and observed real source identity.
5. `SEEK` always invalidates pending alignment/handover of the old position; `BOUNDARY` always overrides SEEK and stale prefetch. Pause/buffering are distinct events. An unrelated network prefetch cannot change current audio state.
6. Exclusivity: before any positive replacement volume original input gain is -100dB; before original restored, secondary is zero or released. Never reintroduce two audible sessions to "crossfade".
7. Limit memory, downloads, repeated lookups, decoder restarts, seek retries and timer callbacks. Fail open: safe original audio if uncertain; no silent failures.
8. No claim of perfect first-frame or Bluetooth quality without a real on-device listening test.

## Implementation gates, one cohesive system

**Gate A — contract before speed:** consolidate event transition ownership: pure typed event/reducer/transition decisions for `PREPARE_READY`, `SEEK`, `BUFFERING`, `PAUSE`, `RESUME`, `BOUNDARY`, `ROUTE_LOSS`, `LOGOUT/STOP`; generation/epoch invalidates prior work. Apply only inside Android. Enforce forbidden `AudioOwnership.preparing()` calls while REPLACEMENT/ALIGNING/PAUSED. Add tests first. Current status: NOT STARTED. No patch claimed.

**Gate B — feasibility, observational only:** assess read-only Media3 lookahead. Determine if Yandex controller reliably reveals the next source's mediaId and title/artist/album/duration before real transition, with enough lead time. Log only sanitized timing, no account/media secrets. If not reliable, DO NOT speculate using queue indexes or synthesize identities; fall back to optimizing the current-track handover.

**Gate C — data-only bounded prefetch (IF Gate B works):** one immutable future ticket; fetch only validated bytes/descriptor, no MediaPlayer or DSP; per-track fresh authorization on actual transition. Cancel/evict on seek, skip, logout, identity change, user Stop. Prepared data consumed atomically through the same owner when the actual song begins.

**Gate D — seek and commit under same owner:** handle seek/buffering/decoder advance as transitions of the same state machine. Suppress duplicate/replayed source events, cancel stale fade/seek callbacks and prevent re-entry into START when a decoder is already current. Do not just increase arbitrary milliseconds.

**Gate E — adversarial regressions:** PREPARE_READY+SEEK; PREPARE_READY+PAUSE/RESUME; BUFFERING vs user pause; PREPARE_READY+BOUNDARY; stale async callback after STOP/logout; 10 rapid skips, Bluetooth route loss, large drift/stream stall, same-track repeat, malicious wrong-edition, original+replacement gain NEVER positive together. Replay the observed HONOR logs and validate source identity, generation, state and command counts. All host / Android API36 D8 / static architecture gates pass. Only then version bump, source-matched DEX, original certificate and signed APK.

## Current implementation paths / source of truth

- `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/ReplacementEngine.java`: high-level state and async callbacks, the source of current conflicts.
- Same directory: `AudioOwnership.java` (exclusive audio authority), `ClockSupervisor.java` (drift), `SourceEventArbiter.java` and `SourceTransitionGate.java` (Media3 events), `PlaybackSource.java` (play intent/buffering), `ProbeService.java` (Media3 listener/polling), `NativeApi.java` (authorized API and stream), `BufferedAudio.java`, `StreamingAudio.java`.
- `android/native-companion/tests/run_engine.py`, `check_audio_architecture.py`, `TestAudioCommandGateway.java`, `TestEngine.java`, `TestAudioOwnershipRegression.java`, `TestStreamingEngine.java`, `TestHandoverClock.java`, `TestRealFailures.java`, `TestCarRecovery.java`, `TestSourceEventArbiter.java`, `TestPhoneReplay.java`, `TestAudioLifecycle.java`, `TestLongRun.java`, `TestResumeClock.java`.
- Current Android CI: `.github/workflows/android-0348-validation.yml`; green https://github.com/manufact-test/nomusic/actions/runs/41019895272 at base `8128307d0daf95f3386b85791db5347e3ec56357`. **No new CI success is implied by docs-only commits on new branch**; configure/trigger appropriately after code changes.
- `android/native-companion/release-spec.json`: 0.3.54, versionCode 55, package `pro.celikom.nativeprobe`. Signing cert fingerprint `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- Build: `build_release.py`, `verify_release.py`, `build-inputs.json`; JDK17, SDK API36, build tools 36, Apktool2.11.1, pinned dependencies/base APK 0.3.22; original PRIVATE keystore outside Git. Match compiled DEX to the exact tested GitHub SHA; never confuse simulated host tests with hardware output.
- Signing key and passwords must NEVER enter GitHub, committed docs, public CI, comments or APK release archives.

## Release and rollback

Existing **SIGNED 0.3.54 AUDIOFIX** is an ON-DEVICE TEST CANDIDATE and uses versionCode 55 (same nominal version as previous 0.3.54, but updated bytecode). User's installation confirmed by 10:49 log. Its APK SHA256 from release evidence: `b29af425b630816b6b7161700c130b9a3824a4a82f229d206939bfcb00a153b7`. Library private file: `/CELIKOM/Android/Backups/CELIKOM-Android-0354-AUDIOFIX-DIRECT-20261030-B29AF425.apk`; previous 0.3.54/0.3.53/0.3.52/0.3.51 also under `/CELIKOM/Android/Backups/`. Do not overwrite backups or uninstall user's app.

Private signing environment, provided earlier by owner: `/mnt/data/CELIKOM-Original-Android-Signing-RECOVERED-20261029(1).zip` (keystore + signing.json) — may NOT exist in a new runtime; retrieve from authorized private files only, do NOT invent paths or expose contents. CI never receives key.

**No new APK in this handoff.** New numbered release requires tests, original signature, matching CI DEX, source code vs APK check and device listening. User has repeatedly encountered red download failures from ChatGPT sandbox links; verify actual file delivery and offer one direct Library APK (not ZIP) without promising UI delivery is guaranteed.
