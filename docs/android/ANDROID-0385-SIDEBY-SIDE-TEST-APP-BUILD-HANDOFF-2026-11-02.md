# CELIKOM Android 0.3.85 — side-by-side test app build handoff (2026-11-02)

**Owner decision:** build the cold-join experiment as a genuinely separate Android application installed alongside stable CELIKOM 0.3.85. Do not create an in-place update APK.

## Goal

Deliver one signed, installable **CELIKOM Test** APK so the owner can keep the currently installed stable **CELIKOM 0.3.85 / code 86** untouched and compare the new cold/new-track handover.

- Stable app remains installed as-is.
- Test app appears as a second launcher entry with label **CELIKOM Test**.
- Test app has its own Android application sandbox, app files, cache, SharedPreferences and local login state.
- Installing or uninstalling the test app must not replace or remove stable CELIKOM.
- The test app contains the exclusive prewarmed cold-join experiment from PR #37. Yandex Music crossfade stays OFF for the first listening check.
- The owner will stop/close stable CELIKOM before starting the test app. Do not run both CELIKOM engines simultaneously against the same Yandex playback session.

## 2026-11-02 — separate signed test APK built and verified

The owner supplied `CELIKOM-0.3.22-install(1).apk`. Its SHA-256 was independently computed as `170b1883e292570d28a3b5c619cf000eaccd9d11ee85ca6f6c08f7b50e5f72c9`, exactly matching the pinned baseline. Apktool 2.11.1 successfully decoded it; a local structural smoke build confirmed the test package, label, versionCode/versionName, dedicated vector icon, test authorities and Android API 36 resource compilation.

Implemented on this branch:
- `android/native-companion/test-app-spec.json`
- `android/native-companion/build_test_release.py`
- `android/native-companion/verify_test_release.py`
- `android/native-companion/tests/check_test_app_build_contract.py`
- `.github/workflows/android-0385-test-app-build.yml` — **workflow_dispatch only**, exact-branch guard, explicit confirmation checkbox, no push/PR/workflow_run trigger.

The manual workflow uses the existing repository secrets `CELIKOM_HOSTINGER_SSH_KEY`, `CELIKOM_HOSTINGER_KNOWN_HOSTS`, `CELIKOM_ANDROID_SIGNING_P12_B64`, and `CELIKOM_ANDROID_SIGNING_JSON_B64`. It retrieves the pinned baseline by read-only SCP, validates the exact SHA, and signs only in the ephemeral GitHub runner. It uploads only the test APK plus verification JSON and receipt; it has no Hostinger write, stable publisher, or stable manifest step.

**Signature detail:** the pinned original base APK verifies with APK Signature Scheme v3 (not v2). The final test APK verifier checks the original base's v3 signature and certificate, then requires the newly signed APK to verify with v3 and the same original certificate. The v2 result is recorded truthfully if present; the repository's standard apksigner invocation may produce v3 without v2. Do not require v2 on either APK.

The builder runs the unchanged full native host suite and unchanged `check_0385_seek_baseline.py`, compiles against Android API 36, runs D8, removes all three updater Java sources from the test DEX, removes the updater construction from `RecorderActivity`, changes the visible update panel to the static disabled notice, and verifies no updater classes/references, stable manifest URL, install permission, or updater components remain.

Initial manual build attempt [#41440747159](https://github.com/manufact-test/nomusic/actions/runs/41440747159) correctly fetched the base APK and signing secrets but stopped in the Android addon host gate because `run_addon_host.py` ignored the builder's `CELIKOM_ANDROID_DEPS` path and looked for `annotation.jar` under the source checkout. Fixed the runner to resolve its pinned dependencies from `CELIKOM_ANDROID_DEPS` (with the original local default preserved); no test assertions, audio code or seek implementation changed. Added a static contract assertion for this path.

After the fix, validation run [#41440905435](https://github.com/manufact-test/nomusic/actions/runs/41440905435) passed on exact packaging source commit `ef634ba7a91bf247873a5c1bd4e96a6d5985135e`: full native host suite, cold-join experiment, unchanged seek golden guard, Android API 36, D8, test-app packaging contract and offline toolchain staging. All stable publisher jobs were skipped. Its `celikom-android-offline-kit` artifact is available for 2 days and is selected by the manual workflow for this source commit.

GitHub requires a `workflow_dispatch` workflow file to exist on the default branch. Therefore the same manual-only workflow file is also registered on `main` by workflow-only commit `b836793d0e70eca708cd3673c615f19b0c6075b3`. That commit adds only `.github/workflows/android-0385-test-app-build.yml`; it does not merge PR #37 or change Android source, stable release metadata, publisher or OTA. The workflow page is [here](https://github.com/manufact-test/nomusic/actions/workflows/android-0385-test-app-build.yml).

**FINAL SIGNED TEST APK BUILT AND AUTOMATED — SUCCESS.** The validated PR run [#41457212661](https://github.com/manufact-test/nomusic/actions/runs/41457212661) completed successfully. It ran `native-android` first, then automatically invoked reusable job `build-celikom-test / build-test-app` via `needs: native-android`. No manual Run workflow action or confirmation checkbox is required. The automatic call is restricted to pull requests whose head is the same-repository branch `feature/android-0385-intro-join-investigation-20261102`; it only starts after the full native validation job succeeds.

- Source commit: `32a4afa7c381758502bf47d7b3facd200e74842a`.
- Signed APK artifact: [`CELIKOM-Test-0.3.85-test-code-86085`](https://github.com/manufact-test/nomusic/actions/runs/41457212661) (artifact ID `13148340328`).
- APK filename in artifact: `CELIKOM-Android-0.3.85-TEST-SIGNED.apk`.
- APK SHA-256: `bf1fc8b39a08b3c1f5f5b2d1483f0fe0fb013bbd7041671867dea77e2b5e4bee`.
- Library copy: `/CELIKOM/Android/Test/CELIKOM-Test-0.3.85-test.apk`; receipt and verification JSON are stored beside it.

**Verified APK identity:** package `pro.celikom.nativeprobe.test`; launcher label `CELIKOM Test`; version `0.3.85-test` / code `86085`; separate Android sandbox, icon and authorities. The original signing certificate matches (SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`); APK Signature Scheme v3 verified. The verifier explicitly confirms the launcher activity label.

**Isolation and tests:** OTA updater absent; stable manifest reference absent; `REQUEST_INSTALL_PACKAGES` absent; no stable publisher or stable OTA changes; Hostinger was read-only for fetching the pinned base APK. The receipt confirms `stable_published=false`, `stable_ota_touched=false`, and `hostinger_write_performed=false`. Full native host suite, cold-join exclusive experiment, unchanged `check_0385_seek_baseline.py`, Android API 36 and D8 all passed. Stable publisher jobs were skipped.

The first manually built APK from run #41442357959 is superseded and must not be installed. Use only the corrected artifact above. The final APK has not yet been acoustically accepted on a physical HONOR phone (`physical_phone_playback_verified=false`, `acoustic_acceptance=false`). The remaining owner check is one short listening check with Yandex Crossfade OFF; do not repeat accepted seek/Pause/Resume tests. Stable CELIKOM 0.3.85/code86, stable release contract, stable OTA endpoint and backup branches remain untouched. PR #37 remains open and unmerged.

# CELIKOM Android — контрольная тестовая сборка после первого запуска (2026-11-02)

## Важное разделение контрольных точек

Здесь существуют ДВЕ РАЗНЫЕ версии, и их нельзя смешивать:

1. **Оригинал / стабильный эталон:** CELIKOM Android 0.3.85, versionCode 86, package `pro.celikom.nativeprobe`, функциональный source commit `053b7d59beb53db5f30b942feba35e51a1ab256a`. Это принятый пользователем эталон перемотки. Резервные ветки `backup/android-0385-honor-seek-accepted-20261102` и `backup/android-0385-honor-seek-accepted-recovery-20261102` указывают на этот точный SHA. **Не менять, не перемещать, не удалять.**
2. **Контрольная тестовая сборка:** отдельное приложение CELIKOM Test, versionName `0.3.85-test`, versionCode `86085`, package `pro.celikom.nativeprobe.test`. Это не оригинал и не новая стабильная версия. Это установленная рядом экспериментальная сборка для проверки холодного перехода между песнями и дальнейшей диагностики интерфейса входа.

Не называть тестовую сборку «новым оригиналом». Не заменять ею стабильную и не менять stable OTA.

## Точная тестовая контрольная точка

- Repository: `manufact-test/nomusic`.
- Work branch: `feature/android-0385-intro-join-investigation-20261102`.
- APK source commit: `32a4afa7c381758502bf47d7b3facd200e74842a`.
- Отдельная резервная ветка контрольной тестовой сборки: `backup/android-0385-test-first-owner-check-20261102`.
- Эта ветка создана от точного APK source commit `32a4afa7c381758502bf47d7b3facd200e74842a`. Она фиксирует полное дерево исходников, из которого собрана APK, включая cold-join эксперимент и test packaging. Она не является оригиналом стабильной версии.
- GitHub currently reports backup refs as not branch-protected; не force-push/delete/repoint. Ветка является сохранённой контрольной точкой, но не криптографически immutable.
- APK artifact: Actions run [#41457212661](https://github.com/manufact-test/nomusic/actions/runs/41457212661), artifact ID `13148340328`, artifact name `CELIKOM-Test-0.3.85-test-code-86085`.
- APK filename in artifact: `CELIKOM-Android-0.3.85-TEST-SIGNED.apk`.
- SHA-256: `bf1fc8b39a08b3c1f5f5b2d1483f0fe0fb013bbd7041671867dea77e2b5e4bee`.
- ChatGPT Library copy: `/CELIKOM/Android/Test/CELIKOM-Test-0.3.85-test.apk`. Receipt and verification JSON находятся рядом.
- Package `pro.celikom.nativeprobe.test`; launcher label `CELIKOM Test`; отдельные sandbox, icon, authorities; оригинальный signing certificate совпадает (SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`); APK Signature Scheme v3 verified.
- Test OTA полностью отключён: нет UpdateCenter construction, stable manifest, UpdateCheckJob, UpdateInstallReceiver, REQUEST_INSTALL_PACKAGES. Не может обновить стабильное приложение.
- Build CI: full native host suite, cold-join exclusive experiment, unchanged `check_0385_seek_baseline.py`, Android API 36 и D8 — PASS. Это не является акустическим подтверждением на телефоне.
- PR #37 remains OPEN/unmerged. Stable publisher не запускался; `stable.json`, stable release contract, stable APK и Hostinger не затронуты.

## Первый запуск на телефоне — новый UI-дефект

Пользователь установил/запустил CELIKOM Test. В процессе ввода собственной почты и пароля обнаружен дефект:

**Текст, вводимый в поля email и password, отображается белым на белом фоне, поэтому пользователь не видит вводимые символы.**

Это пользовательское наблюдение, не установленная причина. Пока не делать предположений о виновном компоненте/теме/Android WebView. Пользователь подготовил **две диагностики** и передаст их следующему чату сразу после этого handoff. Следующий разработчик должен:

1. Сначала принять и изучить обе диагностики целиком; извлечь сведения об экране входа, версиях, логах, окружении и воспроизведении.
2. Найти реальную реализацию формы входа и стили полей в соответствующих Android/UI ресурсах или WebView/CSS (по фактической архитектуре проекта).
3. Определить конкретную причину белого текста на белом фоне: цвет текста, фон поля, hint, состояние фокуса, password transformation, тему/appearance, injected CSS или иной реально подтверждённый фактор.
4. Исправить только видимость текста в полях email/password и связанные состояния ввода. Сохранить читаемый hint/placeholder, cursor, selection, autofill и password masking; проверить светлую/тёмную тему, если приложение действительно поддерживает обе.
5. Не менять логику авторизации, backend/API, аудио, перемотку, Pause/Resume/Next, cold-join experiment и updater. Не менять стабильный пакет.
6. Добавить воспроизводимую проверку UI/контракт/тест, затем полный Android regression suite, неизменный seek guard, Android API 36 и D8.
7. После проверки собрать следующую **отдельную CELIKOM Test APK** с тем же test package `pro.celikom.nativeprobe.test`, оригинальной подписью и OTA-disabled конфигурацией; увеличить test versionCode относительно 86085 (не трогая stable versionCode 86). Новую APK отдавать только после успешной проверки.
8. Сохранить текущую контрольную тестовую сборку (этот backup ref и APK SHA) для отката. Не перезаписывать её.

## Аудио-границы, остающиеся обязательными

- Перемотка 0.3.85/code86 принята владельцем на HONOR для проверенных сценариев, включая перемотку после Next. Не просить повторять тесты перемотки, Pause, Resume.
- Проблема начала/перехода между песнями остаётся отдельным экспериментом. Тестовая APK содержит exclusive cold/new-track handover для предварительно подготовленного локального полного файла после существующего clock gate.
- Первое короткое прослушивание на HONOR с выключенной настройкой Яндекс Музыки **«Плавный переход»** ещё не подтверждено в этой передаче. Не заявлять акустическую приёмку, пока пользователь не сообщил результат.
- Не запускать одновременно CELIKOM и CELIKOM Test против одной сессии Яндекс Музыки: перед проверкой закрыть стабильное приложение.
- Не повторять перемотку «на всякий случай». После UI-дефекта приоритет следующего чата — анализ двух новых диагностик и исправление видимости ввода.

## Автоматическая сборка

Тестовая сборка автоматически запускается в рамках валидации PR #37 после успешного `native-android` job. Пользователю не нужно каждый раз вручную нажимать Run workflow. Сборка только для same-repository branch `feature/android-0385-intro-join-investigation-20261102`, отдельный test package, без stable publishing. При последующих правках обновлять только тестовую сборку; stable publishing path не трогать.


## Exact source checkpoint

- Repository: `manufact-test/nomusic`
- Work branch: `feature/android-0385-intro-join-investigation-20261102`
- Packaging source commit: `32a4afa7c381758502bf47d7b3facd200e74842a`; validation + automatic signed test APK run [#41457212661](https://github.com/manufact-test/nomusic/actions/runs/41457212661) is green for this exact SHA. The reusable test workflow is called automatically by `android-0348-validation.yml` after `native-android` succeeds; no manual dispatch. Audio experiment implementation remains the PR #37 code; packaging changes are isolated from seek/playback logic.
- Draft experiment PR: [#37](https://github.com/manufact-test/nomusic/pull/37), open and unmerged.
- Experiment CI: [#41419113128](https://github.com/manufact-test/nomusic/actions/runs/41419113128), PASS (32 cold-join checks, full native host suite, accepted seek guard, Android API 36 and D8).
- Accepted 0.3.85 seek source: `053b7d59beb53db5f30b942feba35e51a1ab256a`.
- Stable release: 0.3.85 / versionCode 86 / package `pro.celikom.nativeprobe`.
- Stable signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.

## Required test application identity

Use a distinct Android package/application ID, proposed:

`pro.celikom.nativeprobe.test`

Use:
- Android application label: `CELIKOM Test`
- Test versionName: `0.3.85-test`
- Test versionCode: `86085` (or another explicitly test-only integer, recorded in the receipt; increment it for future upgrades of this same test package)
- The **same original signing key/certificate** as stable CELIKOM, SHA-256 above.
- A test-specific APK filename such as `CELIKOM-Android-0.3.85-TEST-COLD-JOIN-SIGNED.apk`.

The distinct package ID is the key to side-by-side installation and Android's separate app sandbox. A separate APK filename or version number alone is NOT sufficient. The package must be verified from the final signed APK with `aapt dump badging` / package inspection before delivery.

Do not relocate the Java class namespace. The existing Java classes may remain under `pro.celikom.nativeprobe...`; Android application ID and Java namespace are separate concepts in this reconstructed APK.

## Manifest identity collisions to audit and isolate

The pinned base manifest currently declares:
- package: `pro.celikom.nativeprobe`
- signature permission and uses-permission: `pro.celikom.nativeprobe.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`
- FileProvider authority: `pro.celikom.nativeprobe.package-export`
- AndroidX Startup authority: `pro.celikom.nativeprobe.androidx-startup`

For the test APK, change the manifest package to the test application ID and give every app-unique permission/authority a test-specific value, e.g.:
- `pro.celikom.nativeprobe.test.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`
- `pro.celikom.nativeprobe.test.package-export`
- `pro.celikom.nativeprobe.test.androidx-startup`

Audit any hard-coded FileProvider authority in base smali and Java before changing the manifest authority; patch only the identity-sensitive string(s) that actually need to match. Do not globally replace `pro.celikom.nativeprobe` throughout DEX/smali: that is also the Java class namespace and component class names, which should remain valid.

## Disable the stable OTA updater in the test app

This is mandatory. The stable updater is tied to the stable package and manifest:

- `UpdateCenter.MANIFEST` points to `/updates/android/stable.json`.
- `UpdateCenter.parse()` accepts only packageName `pro.celikom.nativeprobe`.
- `RecorderActivity.java` currently constructs `new UpdateCenter(this, updatesPanel)` at line 54; its constructor schedules a job and immediately checks the stable manifest.
- `build_release.py` currently adds `REQUEST_INSTALL_PACKAGES`, `UpdateCheckJob`, and `UpdateInstallReceiver` to the stable manifest.

For the test application:
1. Do not instantiate `UpdateCenter`; show a static note such as **«Тестовая сборка · автоматические обновления отключены»** instead.
2. Do not schedule `UpdateCheckJob`.
3. Do not add `REQUEST_INSTALL_PACKAGES`, `UpdateCheckJob`, or `UpdateInstallReceiver` to the test manifest.
4. The test app must never fetch the stable manifest, download the stable APK, or offer an install action.
5. Keep the stable updater source and behavior unchanged for the stable package.

The existing `android-auto-publish-hostinger.yml` `test_only` path is **not suitable as-is**: it still builds the package from stable `release-spec.json` (`pro.celikom.nativeprobe`) and would install over the current app. Do not use that path without a separate package-aware test builder and verifier.

## Build implementation requirements

Implement a dedicated, clearly separated test packaging mode on the work branch. Prefer a dedicated `test-app-spec.json` plus `build_test_release.py` / `verify_test_release.py`, or a strictly isolated explicit test mode in shared packaging code. Do not weaken the stable release contract.

The current stable build pipeline has important assumptions:
- `release-spec.json` pins stable package `pro.celikom.nativeprobe`, version 0.3.85/code86 and signer.
- `release_contract.py` validates that stable identity.
- `build_release.py` reconstructs the pinned base APK, compiles the Java addon, patches manifest/version, adds stable updater components, signs with the original key and calls `verify_release.py`.
- `verify_release.py` explicitly requires the stable package, label, manifest structure and updater components.

Therefore:
- Do not change stable `release-spec.json` package/version/code/signer.
- Do not weaken `release_contract.py` or `verify_release.py` to accept a second identity.
- Add test-specific build metadata and test-specific verification that prove the test package ID, test label/version, unique authorities/permission, absence of updater UI/jobs/receiver/install permission, correct DEX, v2/v3 signature and exact original signer.
- Preserve the pinned base APK SHA and dependency checks.
- Compile the current experimental source from the work branch; do not substitute an older DEX or stable 0.3.85 DEX.
- Keep the seek golden guard `android/native-companion/tests/check_0385_seek_baseline.py` unchanged and passing.
- Verify that stable and test APKs have different package IDs but the expected same signing certificate.
- Verify final APK archive/manifest and calculate SHA-256.

## Build and delivery channel

Create a dedicated manually dispatched GitHub Actions workflow restricted to this work branch (or another equally auditable nonpublishing build route). Reuse the repository's original signing secrets only inside the signed build job. Upload the signed test APK and a JSON build receipt as a GitHub Actions artifact with a practical retention period (e.g. 7 days).

**Do not:**
- run the stable publisher;
- call the Hostinger stable publish path;
- upload the test APK to the stable release directory;
- edit `/updates/android/stable.json`;
- edit the production update manifest or OTA endpoints;
- use the existing same-package `test_only` artifact as the side-by-side deliverable;
- merge PR #37 or publish stable.

The artifact must be installable and signed. An unsigned inspection APK is not an owner test build.

## Required verification before delivery

1. Existing full native host suite passes, including the 32 cold-join experiment checks.
2. `check_0385_seek_baseline.py` passes unchanged.
3. Android API 36 compile and D8 pass.
4. Test APK package is exactly `pro.celikom.nativeprobe.test`; stable package remains `pro.celikom.nativeprobe`.
5. App label is `CELIKOM Test`; test versionName/code are the declared test values.
6. All package-specific manifest authorities and signature permissions are unique; no provider authority collision remains.
7. Test APK has no update UI/constructor, no scheduled update job, no updater receiver, no `REQUEST_INSTALL_PACKAGES`, and no stable-manifest request.
8. Original base APK's v3 signature verifies; final test APK's v3 signature verifies and matches stable certificate SHA-256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`.
9. Stable APK and stable release metadata are byte-for-byte untouched; the manual build may perform only the pinned baseline's read-only SCP fetch. No Hostinger write, stable.json read/write, or publisher is allowed.
10. Produce a receipt with source commit, package, label, versionName/code, signer SHA-256, APK SHA-256, file size, CI run URL, and `stable_published: false`.

## Owner's one device check after delivery

The owner installs the test APK normally. Android should show two apps:
- **CELIKOM** — existing stable 0.3.85, untouched.
- **CELIKOM Test** — experimental cold-join build.

No uninstall or replacement of stable CELIKOM is required. Before testing, stop/close stable CELIKOM; then open CELIKOM Test and sign in if its separate local state requires it. Keep Yandex Music crossfade OFF. Listen to one or two representative new-track starts only. Do not repeat the accepted seek test unless a regression is actually heard.

A successful build/CI is not acoustic acceptance. After the owner's listening verdict, decide whether the experiment is useful. Only then consider a later stable integration/release as a separate, explicitly approved task.
