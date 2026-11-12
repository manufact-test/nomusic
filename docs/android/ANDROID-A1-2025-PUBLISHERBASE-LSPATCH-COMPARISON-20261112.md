> **РЕАЛЬНЫЙ ПОЛОЖИТЕЛЬНЫЙ ПРОРЫВ 12.11.2026** — [GitHub Actions 43190701118](https://github.com/manufact-test/nomusic/actions/runs/43190701118) **SUCCESS**, настоящий Ubuntu ARM64 + Android 13 (arm64-v8a/armeabi-v7a) Redroid. **Оба** independently lab-signed APK base, построенные из verified publisher-signed ORIGINAL `2025.10.4 #120.1gpr` с 15 конфигурационными собственно подписанными splits, криптографически valid / установлены 16/16. **Level0:** `native_main_75s_stable=false`, MAIN `JAVA_CRASH` / `IllegalStateException` / `SIGNATURE`, scoped Yandex UI thread. **Level2:** `native_main_75s_stable=true` — **25/25 alive same PID + 25/25 resumed за 75 секунд** по реально исполняемому Android. Обе сборки подписаны одной own ephemeral подписью, исходный embedded publisher DEX/so SHA идентичен, 0 модулей, один и тот же guest, разница уровня LSPatch 0↔2. Это первый убедительный причинный runtime proof, что signature compatibility mode 2 **необходим в данной парной реализации** и достаточен для стабильного нативного MAIN при данных условиях. **Это НЕ** отдельный package CELIKOM, не proof login/MyWave, не аудиозамена, не Play Protect, не пользовательский APK. **Stage A NO-GO**, Stage B LOCKED до этих следующих проверок.

# CELIKOM Android A1 — owner-approved LSPatch signature compatibility A/B (12 Nov 2026)

## Новое решение владельца

12 Nov 2026 владелец прямо разрешил пересмотреть старый добровольный инженерный запрет на signature compatibility bypass в экспериментальном Android CELIKOM. Приоритет: один настоящий нативный Яндекс с родным декодером/полным UX; никаких фиктивных вторых плееров или бесконечных source-only тестов. Это **разрешение на техническое исследование**, а не доказательство юридических прав на распространение модифицированного чужого APK или доступ к чьему-либо аккаунту. Эталон Test.50 и рабочую A1 не переписывать.

## Техническое отличие, найденное в ранее загруженном ChromaSync

Оригинальный конкурент ChromaSync-Clone-3.0.1.apk уже исследован, **не переспрашивать про загрузку**. Подтверждённый unsigned-safe config `sigBypassLevel=2`, rootless LSPatch metaloader, собственный embedded модуль и renamed native host. Level 2 в upstream LSPatch включает совместимость с PackageManager + libc openat проверками подписной идентичности. Версия competitor host 2025.10.4 #120.1rur. Ранее реальный ARM13 тест полного конкурента 75s устойчив, но вложенный `origin.apk` без оболочки падает. **Какая конкретно фича оболочки нужна — не доказано**, поэтому нужен причинный A/B, а не повторять source PHP tests.

## Принципиальная ошибка прежней схемы тестов

Наша старая цепь 2026 брала уже **самостоятельно переподписанный clone** и только потом применяла LSPatch. В режиме 2 LSPatch считывает `originalSignature` у **входного APK**, т.е. у нашей подписи, а НЕ у издателя. Поэтому даже переключение `-l 2` после собственного `apksigner` не является равнозначным схеме, где исходный publisher signed host передаётся в LSPatch. В новой приватной A/B схеме вход — 2025.10.4 #120.1gpr **реально подписанный оригинал**, из EXISTING unpublished GitHub release `442137464`, 16 splits SHA256 verified.

## Код настоящего native-эксперимента

Branch `experiment/android-a1-2025-publisherbase-lv0-lv2-arm13-20261112`. Скрипт `android/native-yandex-hooklab/ci/owner_2025_publisherbase_lspatch_level_ab.py`:

- Проверяет подлинные 16 издательских APK (SHA256 и криптографическая publisher signature).
- Изготавливает 15 независимых lab-signed конфигурационных splits и **2 лабораторных APK base**, в которые LSPatch получает настоящий publisher signed ORIGINAL `base.apk` на вход, одинаковую новую личную ephemeral подпись, но `sigBypassLevel` **0 vs 2**. Никакого чужого модуля, треков, сети, аккаунтов, скриншотов, приватных бинарников в артефактах.
- Сверяет host original native libs/DEX с вложенным источником, signing cert coherence, package/version, ABI/ZIP loader и наличие исходного сертификата для runtime. Устанавливает в один disposable ARM13 guest по очереди 16-раздельный set (с чистым uninstall) и проверяет MAIN native Activity и 75s без login/media.
- **Это отдельно взятая причинная проверка запуска, не установленная CELIKOM APK**; установка на HONOR, песня, pause/seek, MyWave, Play Protect и Stage A заведомо не доказаны. Stage B отдельно.

Предыдущая попытка использовать неподдерживаемый внешний 2026 mirror asset в `experiment/android-a1-independent-sig-compat-arm13-20261112` остановилась с `PINNED_ARCHIVE_CHANGED` (Actions `43189751753`) **до упаковки и запуска**. Не трактовать её как подтверждение/опровержение level2. Поэтому эта новая попытка использует **собственный уже загруженный оригинальный 2025 XAPK**, не нуждается в сторонней ссылке и не публикует бинарники.
