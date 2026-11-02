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

