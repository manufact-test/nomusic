# ПЕРВОЕ СООБЩЕНИЕ НОВОМУ ВЕДУЩЕМУ — CELIKOM Android A1 (12.11.2026)

Привет! Ты следующий ведущий CELIKOM Android A1. Продолжай с проверенных результатов этого захода. НЕ начинай с нуля, НЕ меняй утверждённую архитектуру, работай крупными изолированными блоками и всегда делай точные резервы.

**Репозиторий:** `manufact-test/nomusic`.
**Исследовательская ветка:** `experiment/android-a1-2025-sdk-signer-triage-20261112`. В начале проверь актуальный HEAD и точный backup в последнем issue #41.
**Основная A1 заморожена:** `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`. **Не изменять** без owner-accepted native/audio результата.
**Исходный 2025 исследовательский резерв:** `backup/android-a1-owner2025-v1-cleanroom-failed-real-ci-docs-handoff-20261111` @ `fa93f6130523a8645de4044a38dbe0d9742b32e1`.
**Новый точный контроль успешного SIGNER:** `backup/android-a1-2025-owner-sdk35-all16-signed-verified-20261112` @ `fcf6cb1107c53611294b74ef787d40b7234cf342`.

## Обязательно прочитать

1. `docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md` — утверждённое ТЗ, НЕ пересматривать.
2. `docs/android/ANDROID-A1-2025-CONFIG-SPLIT-MINSDK-SIGNER-ROOTCAUSE-20261112.md` — новый проверенный signing-rootcause и реальный ARM runtime.
3. `docs/android/ANDROID-A1-2025-V1-SIGNER-SCRATCH-CLEANROOM-RESULT-20261111.md` — отрицательные прежние пробы, НЕ повторять.
4. `docs/android/ANDROID-A1-ARM13-THREE-CLONE-LAYOUTS-EXIT-SELF-NO-GO-20261111.md` — **другая** проблема 2026.
5. GitHub issue #41 — ОТКРЫТЬ, не закрывать после успешной установки.

## Продукт (решение владельца, не менять)

Один отдельный APK CELIKOM с настоящим нативным интерфейсом Яндекс.Музыки, Яндекс-аккаунтом, библиотекой, плейлистами, Моей волной и штатным единственным плеером/декодером. Наш собственный audio-contract только выбирает разрешённые альтернативные записи на уровне источника. Оригинальный Яндекс остаётся установленным параллельно.

**Никакого** WebView, второго аудиодвижка, подделки подписи издателя, обхода DRM/Passport/Play Protect, LSPatch sigBypassLevel=1/2, переноса модулей конкурента. Патчирование/коммерческое распространение вендорного приложения требует отдельного решения о правах; не обращаться к Яндексу без разрешения владельца.

## Что подтверждено реальным CI 12.11.2026

- Подлинный XAPK Яндекс 2025.10.4 #120.1gpr, SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 45 961 661 bytes, **16/16 подлинных publisher-signed APK**. В НЕОПУБЛИКОВАННОМ GitHub draft release `a1-yandex-2025-gpr-private-test` (release ID 442137464, asset ID 736739728). Не просить файл снова, не публиковать draft, не загружать APK/ключи в коммиты или Actions artifacts. Подлинный оригинал ARM13 MAIN 75s PASS: [CI 43091414430](https://github.com/manufact-test/nomusic/actions/runs/43091414430).
- **ПРЕЖНЯЯ ПРОБЛЕМА ПОДПИСЫВАНИЯ 2025 РЕШЕНА**: first split index0 — named config split без собственных `uses-sdk`; `apksigner verify` без minSDK ошибочно охватывал старые API и отклонял JAR/v1. ПОДЛИННЫЙ base.apk имеет `minSdkVersion=24`. Подписываем все splits для 24, именованные конфигурационные verify с `--min-sdk-version 24`, base обычным strict verifier. Не ослабляем подпись. [CI 43105227726](https://github.com/manufact-test/nomusic/actions/runs/43105227726) **SUCCESS: 16/16 own-key independent signature PASS**, [CI 43105590847](https://github.com/manufact-test/nomusic/actions/runs/43105590847) SUCCESS повтор. Официальный SDK35 синтетические apk на API21/28 + tamper rejection PASS; 15+7 тестов PASS. DEX/so byte-preserved, 7 provider authorities rewritten, separate own-key signer. Удаление старого META-INF в прошлом НЕ решало проблему, НЕ повторять.
- **НОВЫЙ РЕАЛЬНЫЙ ARM13 ЭКСПЕРИМЕНТ**: [CI 43105679694](https://github.com/manufact-test/nomusic/actions/runs/43105679694) — disposable ARM64 + ARMv7 Android13 Redroid, publisher original 16/16 и own-sign 16/16 PASS, **все 16 независимо подписанных cloned APK УСТАНОВИЛИСЬ**, Android `am start` принял нативный MainScreenActivity. Далее **Java MAIN CRASH**, 75sec same-PID & resumed gates FALSE; точный `ApplicationExitInfo latest_main_exit_reason=JAVA_CRASH, status=ZERO`. CI строго **FAIL / Stage A NO-GO**. Android UI/login/Play Protect/audio и владелец HONOR не проверялись. Это НЕ прежний 2026 `EXIT_SELF(0)`, причины не смешивать.
- Audio selection контракт помощника issue #42/PR #43 **уже интегрирован** в замороженную A1, 32/32 tests PASS. НЕ делать заново и НЕ мержить повторно.

## Новая работа — приоритет

1. **НЕТ необходимости повторно чинить 2025-подписи или установку** — 16/16 обеих уже PASS на настоящем ARM13.
2. В **отдельном исследовательском CI/ветке** провести безобходную read-only **классификацию Java MAIN CRASH** на disposable ARM13: собрать AndroidRuntime crash-buffer + `ApplicationExitInfo`, строго scope по точному MAIN PID и использовать уже существующий безопасный `android/native-yandex-hooklab/clone_main_crash_buffer.py`. Он возвращает фиксированные категории (`APPLICATION_STATE`, `RESOURCE`, `CLASS_RESOLUTION`, `PERMISSION`, etc), без раскрытия Java stack, классов и чужих данных. Не добавлять raw логов/приватных данных в публичный репозиторий. Не переигрывать заведомо тот же тест без новой диагностической метрики.
3. После получения категории и в отсутствие DRM/issuer/Passport self-check — точечно искать законную причину, исправить **лишь проверенный** упаковочный/manifest/resource дефект, затем реальный native 75s. Если упираемся в vendor trust, разрешение правообладателя, integrity-check — **STOP / NO-GO**; предложить владельцу официальные варианты, не обходить.
4. Только после стабильного native MAIN — UI screenshots/навигация/обычная авторизация, библиотека, Моя волна, одно штатное воспроизведение, интеграция существующего audio-contract, пауза/seek/Next и реальное акустическое подтверждение владельцем.
5. Владелец должен отдельно принять Stage A по **реальному звуку**, после чего обязательно напомнить про Stage B: замена LSPatch своим механизмом. До этого Stage B LOCKED.

**Нельзя трогать** frozen A1, Android Test.50, Windows, расширение, сервер/админку/production, штатное приложение и HONOR владельца. Бинарей для установки пользователю нет, Stage A — **NO-GO**, issue #41 оставить OPEN.

**Рабочие файлы:**
- `android/native-yandex-hooklab/ci/owner_2025_gpr_lab_clone_no_bypass_arm13.py` — 16 signer + install/main strict gates;
- `android/native-yandex-hooklab/ci/official_sdk_signer_control.py` — официальная SDK синтетика;
- `android/native-yandex-hooklab/ci/lab_signer_signal_gate.py` и `test_lab_signer_signal_gate.py` — безопасные категории;
- `.github/workflows/android-a1-2025-official-sdk-signer-triage.yml`;
- `.github/workflows/android-a1-2025-own-clone-native-arm13-75s.yml`.

Не размножать старые queued 0 jobs [43097031056](https://github.com/manufact-test/nomusic/actions/runs/43097031056) и [43096955087](https://github.com/manufact-test/nomusic/actions/runs/43096955087); сначала проверить их статус.

В конце каждого следующего большого захода — **точный backup, обновить docs, issue #41, написать короткий проверенный отчёт**.

## Результат дополнительной безопасной категории Java crash (12.11)

[CI 43106889245](https://github.com/manufact-test/nomusic/actions/runs/43106889245) — ещё один настоящий ARM Android13 запуск именно собственной копии 2025. Подпись 16/16 + установка 16/16 остались PASS. Нативный MAIN **снова FAIL**. PID-scoped private `logcat -b crash` + `ApplicationExitInfo` классифицирован существующим `clone_main_crash_buffer.py`: **`fatal_category=APPLICATION_STATE`**, `android_runtime_fatal_main_seen=true`, `crash_main_pid_evidence_available=true`, `crash_buffer_main_pid_lines_seen=true`; `native_link_error_seen=false`, `native_main_signal=NOT_OBSERVED`, `application_component_factory_failure=false`, `application_create_failure=false`, `activity_launch_failure=false`, `lspatch_bootstrap_mentioned=false`. Raw Java stack/PID/app byte contents в логи и артефакты не попали. Это **не** доказательство проверки подписи или DRM, а безопасное сужение до Java-state исключения. НЕЛЬЗЯ делать обходы или снимать проверку приложения; следующий шаг — анализ документированных/собственных configuration/manifest metadata при полном соблюдении vendor-trust ограничений либо эскалация о правах.

**Не повторять** тождественную ARM сборку ради получения той же `APPLICATION_STATE` категории; нужна новая разрешённая, каузально разделяющая гипотеза и тест. До этого — Stage A NO-GO.
