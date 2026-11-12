> **НОВОЕ ПОДТВЕРЖДЕНИЕ 12.11.2026 / СЛЕДУЮЩИЙ ЧАТ:** эксперимент `experiment/android-a1-public-browser-foreground-causal-20261112`; точный backup `backup/android-a1-2025-public-browser-foreground-final-20261112`. В [актуальном разделе исследования](ANDROID-A1-2025-NATIVE-BRIDGE-REAL-IPC-20261112.md#контроль-3--убедились-что-отказ-не-вызван-потерей-фокуса-яндексом) и [реальном ARM13 CI](https://github.com/manufact-test/nomusic/actions/runs/43179463992): publisher native Yandex Activity **RESUMED до попытки IPC**, собственный независимый CELIKOM Service вызывает `MediaBrowser.connect()`, **CONNECTION_REJECTED**; 16/16 оригинальных signed APK проверены/установлены, никаких модификаций/обходов. Следовательно, причина прежнего отказа НЕ только в потере фокуса. Этот публичный IPC путь без принципиально новой интеграционной поверхности **не продолжать**. Нет native host/source swap. **Stage A NO-GO, Stage B LOCKED**, не обещать APK. Обе immutable ветки старой передачи сохранены; новую проверять по refs.

# CELIKOM Android A1 — передача после native IPC экспериментов 12.11.2026

Новый ведущий, продолжай CELIKOM A1. Утверждённое ТЗ `docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md` неизменно. **Работать крупными блоками, без пустых отчётов, не создавать заново существующие решения.**

- Репозиторий: `manufact-test/nomusic`.
- Последняя **экспериментальная** ветка: `experiment/android-a1-2025-native-bridge-manifest-witness-20261112`; точный backup: `backup/android-a1-2025-native-bridge-manifest-and-live-ipc-final-20261112`. **Обязательно сравни обе HEAD ссылки перед новым заходом.**
- Замороженная принятая главная A1: `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743` — не трогать. Эталон Test.50 также не трогать.
- Исходный 2025 XAPK уже лежит в **неопубликованном** draft release `a1-yandex-2025-gpr-private-test` (release 442137464, asset 736739728). Не просить повторно, не публиковать сторонние APK и ключи.
- Сначала прочитай `docs/android/ANDROID-A1-2025-NATIVE-BRIDGE-REAL-IPC-20261112.md`, `docs/android/ANDROID-A1-FINAL-20261112-SIGNATURE-TRUST-AND-B42-BOUNDARY.md`, `docs/android/ANDROID-A1-PARALLEL-AUDIO-CONTRACT-20261111.md`, и issue **#41 (OPEN)**.

## Новое доказательство (НЕ рабочая APK)

1. **Реальный издательски подписанный 2025 AndroidManifest, 16/16 signature PASS**: 138 Activity, 11 exported+enabled, **0** разрешений на external cross-UID activity embedding; один declared exported MediaBrowserService. CI https://github.com/manufact-test/nomusic/actions/runs/43177629249.
2. **Реальный ARM Android13**: неизменённый издательский Яндекс 16/16 работает, собственный отдельно подписанный diagnostic Android app устанавливается и запускается; система находит один service, но `MediaBrowser.connect()` возвращает **`CONNECTION_REJECTED`**, нет root или session token; никаких playback/source commands не посылалось. CI https://github.com/manufact-test/nomusic/actions/runs/43178136217.
3. Это **не доказательство**, что браузер всегда отвергает при других состояниях пользователя. Но в чистом госте без аккаунта **нет разрешённого source interface**, и MediaBrowser сам не предоставляет `replaceAudioSourceBeforePrepare`.
4. Ранее независимо подписанный same-package Яндекс 2025 **16/16 sign/install PASS, MAIN Java IllegalStateException/SIGNATURE FAIL** при побайтово неизменённых 8661 entries, собственном valid SourceStamp, grants 30/30 requested и 15/15 granted. Не повторять signer/ZIP/permissions/SourceStamp без новой независимой идеи.
5. Подготовленный свой source-choice contract B42 **34/34 PASS**, но **не** проверен в активном декодере. Album/edition attestations у PHP отсутствуют для части сценариев; backend не менять без отдельного решения.

## Точная задача дальше

Продолжать только если найден **новый реально проверяемый, не обходящий защиту** способ независимого собственно native host со штатной UI и одним родным декодером и точкой source-before-prepare. Проверь его на настоящем signed original и только после этого интегрируй B42; не создай ещё одну синтетическую модель. Если такого host нет, честно сохраняй **Stage A NO-GO / Stage B LOCKED**, не выдавай diagnostic APK владельцу. **Никаких WebView, второго плеера, credential/DRM/signature/Play Protect обходов или кода конкурента.** Тему обращения к Яндексу владелец окончательно закрыл — не возвращаться.

Не трогать HONOR, оригинальный установленный Яндекс, Windows, расширение, Test.50, API/backend, production. **После реально акустически принятого владельцем Stage A** обязательно отдельно напомнить о Stage B: замене LSPatch собственным механизмом.
