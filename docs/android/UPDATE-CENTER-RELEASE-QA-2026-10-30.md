> **CURRENT STATUS — 31.10.2026:** stable OTA release **0.3.72 / versionCode 73** has been published and verified. This QA document's 0.3.55 / 0.3.56 / 0.3.57 steps are historical and superseded. The remaining owner action is the real HONOR test: update discovery, Android confirmation, removal from Recents after successful install, manual relaunch, and version 0.3.72 confirmation. See [ANDROID-0372-OTA-RELEASE-RECEIPT-2026-10-31.md](ANDROID-0372-OTA-RELEASE-RECEIPT-2026-10-31.md).

---

# CELIKOM — Gate G baseline, выпуск Update Center и ручная QA · 30.10.2026

> **Состояние:** подписанная 0.3.55 есть, **НЕ проверена пользователем на телефоне**, **НЕ содержит** обновлятора. Этот чеклист — работа для следующего чата, не отметка о завершённой проверке.

## 1. Пин последней Android APK и откат

- Repository: https://github.com/manufact-test/nomusic
- Branch: `feature/android-unified-preparation-seek-gate`. CI-green source checkpoint: `d0317e3d697db202164804a27f18f3e688fe1d05`; full Android GitHub Actions: https://github.com/manufact-test/nomusic/actions/runs/41043617578 — SUCCESS.
- Signed APK: **CELIKOM Android `0.3.55` / versionCode `56`**, package `pro.celikom.nativeprobe`.
- APK SHA256: `ff1c9d0757173796b1068acf52ebdecd8354cfb429dd35c2b7253f3e5596c54a`.
- Native DEX SHA256: `64ee7d70e48dba382effea638c17766052e58bd67ed56e663ff05d18d08b575c`.
- Public signing **certificate** SHA256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
- Library path (persistent user file): `/CELIKOM/Android/Backups/CELIKOM-Android-0.3.55-GATEG-SIGNED-20261030.apk`. Do **not** assume an old `sandbox:/mnt/data/` path is live in a different chat. Locate existing Library file or materialize if byte access required. Verify SHA again.
- Older signed **0.3.54 AUDIOFIX/versionCode 55** was last installed and physically observed (but had audible handover/seek problems): Library `/CELIKOM/Android/Backups/CELIKOM-Android-0354-AUDIOFIX-DIRECT-20261030-B29AF425.apk`. Do not overwrite either.
- User phone: **HONOR NTH-NX9**, Android **13**; Yandex Music **2026.09.5 #167.1gpr** in previous logs. Current versions must be read from new diagnostics rather than presumed unchanged.
- Recovery branches: `backup/android-0355-gateg-signed-ci-green-20261030` (code green), `backup/android-0355-before-update-center-handoff-20261030` (full docs baseline). Prior Gate D/E/F backups remain.

## 2. What Gate G actually changed

Source docs: `docs/android/UNIFIED-AUDIO-GATE-PROGRESS-2026-10-30.md`. Gate A/B were single audio authority / event tickets / observational Media3 lookahead, Gate D/E/F closed seek single-flight, buffering vs manual pause, stale decoder callbacks and account revocation.

Gate G: removed legacy duplicate `warmSeekTransition` flag and moved native warm seek tracking solely to `AudioOwnership.seekInFlight`; moved `handoverPending` clock gate to `AudioOwnership.handoverAwaitingClock`, revoked on source/seek/pause/buffer/route/STOP; `PlaybackUi` now reads owner; manual «Вернуть оригинал» uses `AudioOwnership.Event.RETURN` ticket; decoder `onPrepared` fences old account. Full CI tests **host state/Android API36/D8**, not waveform or Bluetooth acoustic output. The native code is **not a complete pure reducer yet** and future-track lookahead stays read-only; **no speculative next-song prefetch was added**.

There was a false intermediate test failure on Gate F caused by invoking a detached null callback; fixed with saved stale listener. Gate G intermediate compile failure `PlaybackUi.handoverPending` was corrected; full green run then completed. All important details in Gate Progress. Do not ignore real regressions but do not treat corrected intermediate test issues as production bugs.

## 3. Next numbered APK release

Updater is new code, therefore **do not modify or redistribute 0.3.55 as though updater already exists**. Choose `0.3.56 / code 57` for first updater-bearing release. Advance both `release-spec.json` and `AppVersion.java`, negative release tests and any hardcoded version/file naming in CI. **Second signed `0.3.57 / code 58`** for live auto-update demonstration. Keep both in private Library and pinned hashes.

Build: `android/native-companion/build_release.py` with pinned 0.3.22 APK, SDK36, build-tools 36, Apktool 2.11.1, JDK17, dependencies pinned by `build-inputs.json`. Original private signing material is outside repository, no key in GitHub/CI/files served from website. `verify_release.py` requires original signer, source/DEX proof, package/manifest/archive invariants; updater permissions/receiver/path changes need narrow audited build/verifier modifications and negative tests. Never overwrite installed previous APK or use unsigned package as testing deliverable.

## 4. New Update Center regression checklist (automated)

- Direct URL `/download/android` returns correct latest *stable* signed APK every time, including HEAD/GET, MIME and attachment, HTTPS, no login prompt/manual page, works in HONOR browser. Changing current release keeps same URL and changes bytes/version.
- Validator rejects non-integer/same/older versionCode, wrong package, wrong signer, invalid SHA/size, malformed manifest, untrusted redirect, HTTP URL, unsupported SDK, partial/truncated/corrupt APK and mismatched changelog data. Caller should not hit APK bytes for ineligible version.
- Download can be cancelled and resumed/retried safely; wrong checksum never launches installer; no temp APK is exposed to other apps.
- OS installer invoked only after trust checks; user action/unknown source permissions handled and cancellation leaves existing app running. Verified actually installed higher version only after relaunch.
- Foreground music service/audio callbacks don't change for update notifications or download. Separate channel and `POST_NOTIFICATIONS` permission denial works; in-app alert still works without notifications.
- Prevent repeated notifications of the same version, stale callbacks after Activity exit, duplicate parallel downloads, race between remote publish and previous downloader, network offline and low storage.
- Versioned immutable APK storage and atomic pointer. Rollback must not publish lower versionCode to users who already installed a higher one; they retain their valid installed app and only wait for next higher code.
- Existing `tests/run_engine.py`, `check_audio_architecture.py`, signed release verification, CI and site tests remain green. No desktop, extension, ads, music API, catalogue or unrelated website CSS/FAQ changes.

## 5. HONOR manual acceptance

**Before actual test:** current signed 0.3.55 (if user chooses to test) has NO updater/notification. First eligible test candidate is newly signed 0.3.56/code57 after implementation, so don't tell user to expect old 0.3.55 to notify.

### Stage A: first install from *one link*
1. Open the one handed-over working HTTPS URL on HONOR. It immediately saves APK, no intermediary webpage, not a GitHub artifact; verify versionCode 57.
2. Install **over existing** 0.3.54/0.3.55, without uninstall or app data wipe; verify signer's continuity and that login, source connection and existing media session still work.
3. Open update UI, grant notifications if desired, check "Обновлений нет" when on current manifest; check deny permission fallback, installed version shown correctly.
4. Run 10+ real track transitions, abrupt skips, large seek forward/back, user pause/resume, Yandex buffering, app/background return, wired/Bluetooth headphone disconnect and reconnect, Wi-Fi/mobile switch. Log *heard silence/clicks/overlap*, not just event counters. Keep original untouched if decoder cannot align.
5. Export actual device diagnostics, sanitize account tokens, give to developer for correlation. Distinguish previous run's 0.3.54 logs from this newer 0.3.56.

### Stage B: true end-to-end update
1. Build **new**, signed and hosted 0.3.57/code58; verify SHA and signer before publishing manifest for correct test channel. Same *user-facing one link* now downloads newer APK when promoted.
2. With 0.3.56 still installed, click **Проверить обновления** to make immediate detection deterministic (periodic background notification can be delayed by Android/OEM). Verify visible in-app banner/changelog; with notification permission, background task eventually emits a separate normal system notification in the shade. Do not promise exact delivery seconds.
3. Tap "Скачать и установить"; verify progress, download size/SHA, Android install prompt/unknown sources, tap **Установить**; confirm app version actually becomes 0.3.57/code58 without data loss.
4. Repeat check: no more prompt, no infinite download. Confirm browsing *one link* gets 0.3.57 (no URL change).
5. Negative on-device: offline, incomplete APK download, deny notifications, cancel OS install, interruptions, low storage if safely simulatable; verify old version remains usable and Yandex audio not affected.
6. Owner signs off only after both update chain and audio quality are evaluated. Save binaries and rollback branch before next changes.

## 6. Manual-test release gate

Until actual deployment and signer verification, **do not give a made-up direct URL**. Until phone validation, **do not claim either audio seamlessness or update notifications proved**. If hosting deployment requires one login/credential not available through connected integrations, next chat can prepare code and one precise owner action, but must not claim production release was performed.
