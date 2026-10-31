# Android 0.3.66/code67 — one installable candidate for HONOR A/B testing

**2026-10-31. Experimental candidate, not acoustically accepted.** Keep this document with `AUDIT-2026-10-31-0365-CONTINUITY-STAGING.md`, `AUDIO-CAPTURE-FEASIBILITY-2026-10-31.md`, and `REGRESSION-GATES-2026-10-29.md`.

## Why a signed candidate is necessary

The user cannot physically validate uninstalled code. Staging-only fake tests and SDK36/D8 do not tell us whether Yandex/MediaPlayer/DynamicsProcessing and HONOR Bluetooth introduce audible clicks or phase beats. One signed APK through the existing in-app updater is required to compare real sound. It is a test candidate, not a claim that both original audio complaints are solved.

## What the one candidate contains

- The previously staged **real Media3 Next → cached seeks → natural successor → seeks** replay and `ReplacementEngine.seek()` ownership correction. Fast cached seeks no longer knowingly command both streams silent while the decoder catches up; partial HTTP seeks no longer repeat the entire cold dip. Pause/route/Stop/stale-account guards remain.
- A *diagnostic-only* cold-join A/B selector, restricted by `NativeApi.fullDiagnostics()` to verified administrators. It uses a long-press on the existing **«Сохранить диагностику»** control, adding **no new normal-user buttons**. Mode A (default) retains 0.3.65's 500ms non-overlap dip for a reliable baseline and immediate fallback. Mode B tests complementary **linear** (not equal-power) gains with the exact existing 0.3.62 **160ms comparison window**, after the current decoder clock and ownership tickets are validated. This is a controlled gain-law experiment rather than another arbitrary duration tweak. It does **not** measure PCM phase and **may** still be audible as a comb-filter wave.
- The selected mode is pinned to the start of each cold handover. A switch during a handover affects only the next attachment; a seek, manual Next, pause, route loss or Stop invalidates the old output lease. Admin grants are checked before selecting and playing the lab mode; ordinary users remain on the old exclusive join.
- The `AudioOwnership.blendSameSong()` law is changed from equal-power (which boosts identical copies by about +3dB) to a complementary linear law for correlated copies. The actual final audio level still follows the replacement edition's `gain_db`, and source PCM/sample phase is **not known**.
- **No** `RECORD_AUDIO`, `MediaProjection`, permissions, new public UI, backend/catalog/site, updater implementation or desktop changes. Package name and signing certificate must remain identical. Version name `0.3.66`, versionCode `67`.

## Mandatory phone procedure AFTER signed APK is verified and published

1. In installed CELIKOM 0.3.65, use the existing **«Проверить обновление»** button to install signed 0.3.66/code67 without uninstalling or resetting data. Check version display.
2. First test the *default baseline* with real Yandex playing: naturally occurring next song, manual Next, six finger scrubs, natural successor, six scrubs, pause/resume, Bluetooth loss/reconnect. It should preserve the previous 0.3.65 500ms join but remove the seek-specific gaps/repeated partial dips.
3. On the admin account, **long-press «Сохранить диагностику»**. Choose **«Линейный переход (эксперимент)»** in the verified admin dialog and apply. On a *new song attachment*, repeat the same scenario at approximately the same volume and route. The experiment avoids the programmed 500ms zero-gain valley but is **not guaranteed** to eliminate interference. If worse, use the same long-press and revert to **«0.3.65: без наложения (контроль)»** without another APK.
4. Save a single combined admin log after the run. Look for `admin_join_mode_selected`, `replacement_correlated_lab_start`, `replacement_transition_complete` join mode, `audio_command_anomaly`, seek callbacks and Media3 event boundaries. **Commands cannot prove speaker audibility.** Describe objectively whether any pop, 500ms fall/rise, timbre wave or seek lag remains; if an external acoustic recording is available it can independently document a real output artifact.
5. Test Stop, unsupported song, Bluetooth and pause again in both modes. Do not mark 0.3.66 accepted until actual HONOR listening and incident diagnostics agree.

## Pre-release gates and publication control

Host tests must include `TestHonor066JoinLab` (linear midpoint, exactly-once ownership, baseline unchanged, mid-join Next and pause) and the existing **71-assertion real Media3 sequence**. `check_audio_architecture.py` permits the overlap only when explicitly pinned to `owner.experimentalCorrelatedJoin()`, and still rejects unauthorized decoder gain. The pure signal-level test models the *worst case* of phase cancellation; it is not a device test.

Run Android SDK36/D8, source-to-DEX provenance, full regression matrix, release contract, original signer continuity, APK SHA256 and live updater manifest/URL checks. The staging branch **must not publish**. The original `feature/android-unified-preparation-seek-gate` **automatically publishes** any higher-version native commit after successful CI when the configured automation is enabled: inspect the exact diff and CI before updating it. A failed build or unsigned package must never be presented as an installable update.

**Acceptance status stays RED until HONOR.** A successful A/B experiment may justify a future safe default or reveal that precise original PCM capture is essential; do not reinterpret a 160ms lab crossfade as a mathematically proven phase-aligned merge.
