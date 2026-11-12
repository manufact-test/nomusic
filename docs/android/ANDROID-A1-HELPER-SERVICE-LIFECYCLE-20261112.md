# CELIKOM Android A1 — независимый service lifecycle helper B (12.11.2026)

**Issue:** [#45](https://github.com/manufact-test/nomusic/issues/45). Только собственная ветка `experiment/android-a1-helper-service-lifecycle-arm13-20261112`. **Stage A NO-GO / Stage B LOCKED до доказанного native 25/25.**

## Конкретная гипотеза

Четыре успешных `Context.startService` из предшествующего native #43276748729 не доказывают, что отдельный AppMetrica service process действительно был создан, получил жизненный цикл и остался жив до обращения Push SDK. Предшествующий `dumpsys` был только **после** 75-секундного окна. Важно найти **первое** отличие stock/clone, а не объявить отсутствие service record после краша его причиной.

## Новый фактический контроль

- `android/a1-service-lifecycle-helper/probe.py` **только на disposable ARM64/ARMv7 Android13** запускает неизменённый существующий original-first проверяющий код A, с единственной Python-подстановкой проверки имени **своей изолированной ветки**. Не модифицирует A-файлы на диске.
- Сравнивает base APK бинарные `AndroidManifest.xml` через локальный AAPT: число service и AppMetrica-кандидатов, namespace их `android:process`, экспорт и `enabled`, совпадение классов *только в оперативной памяти*.
- Во время каждого 75-секундного наблюдения собирает асинхронные `ps -A` и `dumpsys activity services <package>` для фактически живых MAIN/AUX PID, service record и привязки `app=ProcessRecord`/Bindings.
- После каждого окна считывает системный AOSP `logcat -b events` (перед stock и clone стартом буфер сбрасывается). Ищет только компоненты выбранного пакета и фиксированные типы `am_proc_start`, `am_create_service`, `am_bind_service`, `am_service_bound`, `am_destroy_service`, `am_proc_died` и restart. Фиксирует первые 48 событий в конечном словаре, **без имён оригинальных классов, PID, исходных строк/ключей**.
- `am_create_service` означает факт запроса AMS на создание ServiceRecord; **сам по себе не доказывает успешный Java `Service.onCreate()`**. Связанный ProcessRecord/события bind/service args повышают уверенность, но без instrumentation callback-onCreate нельзя объявить его прямым свидетельством. Отрицательные события без доступного лога не доказывают отсутствие.
- `android/a1-service-lifecycle-helper/test_probe.py`: синтетические регрессии распознавания manifest, PID, ServiceRecord и изоляции stock-vs-clone. Готовый no-suppression native CI — `.github/workflows/android-a1-helper-service-lifecycle.yml`, не общий workflow A.

## Ограничения и критерий

Оригинальная issuer-signed Яндекс.Музыка устанавливается **первой** (16 splits). CELIKOM собирается как отдельный ONE-APK и устанавливается рядом. Одинаковая реальная ARM13 проверка 75 сек / 25 MAIN-замеров без подавления исключения. Исходные SDK, Push и код владельца не патчим; бинарники, ключи, private Java и APK не публикуем. Предлагаем config fix только после доказанного причинного несовпадения, иначе честное NO-GO.

## Результаты реального ARM13

## Подтверждённый ARM13 no-suppression результат — native #43286779150

- **CI:** https://github.com/manufact-test/nomusic/actions/runs/43286779150
- **Точный tested source:** `84b1418fee96050277aecd4d977438715923c23d` (документ перед этим native запуском не изменяет исполняемый код). Все 4 synthetic helper cases PASS, SDK 35 и собственный read-only LSPatch-модуль собраны, приватный issuer XAPK верифицирован, Android13 ARM64+ARMv7 реально загрузился; оригинал установлен первым, клон рядом.
- **Итог job:** CI **FAIL по настоящему product gate** — CELIKOM MAIN не прошёл 25/25. Не выдавать диагностическое исследование за зелёный APK.

| Факт | Publisher original | ONE-APK CELIKOM clone |
|---|---|---|
| Base manifest service | 32 | 32 |
| AppMetrica-classified services | 3 | 3 |
| AppMetrica service class names | совпадают с клоном (только in-memory) | совпадают с оригиналом |
| Metrica process declaration | 2 DEFAULT, 1 PRIVATE | 2 DEFAULT, 1 PRIVATE |
| service exported | 3 false | 3 false |
| Metrica auxiliary process `am_proc_start` | 1 | 1 |
| Metrica auxiliary process `am_proc_bound` | 1 | 1 |
| sample: Metrica aux PID ever live | YES | YES |
| sample: Metrica ServiceRecord present | YES | YES |
| sample: ServiceRecord attached `app=ProcessRecord` | YES | YES |
| sample: ServiceRecord binding entry | YES | YES |
| foreground MAIN 75s/25 | **25/25 PASS** | **1/25 FAIL** |
| after-window metrica service candidate | YES | NO |
| after-window Metrica aux process | YES | YES |

**Важная причинная поправка:** пропавшая после краша `ServiceRecord` у клона **не означает, что сервисный процесс не стартовал**. В live-сэмплах фиксируются его запуск/привязка, физический PID, запись сервиса и прикреплённый `ProcessRecord` у обоих приложений. Следовательно гипотеза **«клон вообще не регистрирует AppMetrica service / нет service process / startService ничего не создал»** опровергнута. Нельзя исправлять ошибку добавлением сервиса в manifest вслепую.

**Первое достоверно измеренное расхождение:** после запуска Metrica auxiliary clone наблюдается серия `am_proc_died_APP_OTHER` (3), а у оригинала таких событий не было; нативный текущий отчет подтверждает **3 MAIN JAVA_CRASH** клона, прямой `Push.impl` `DETAIL_NOT_INITIALIZED`, `PUSH_LEGACY.init` 3 ENTER / 3 THROW, ноль suppressed. До смерти MAIN на host-уровне сервис/aux доступны у обоих. Это **последствие сбоя MAIN**, не доказанная исходная service-ошибка.

**Ограничение:** Android eventlog на этом guest выдал `am_proc_start/bound/died`, но **не выдал `am_create_service/am_bind_service/am_service_args` ни для stock, ни для clone**. Записи `dumpsys` свидетельствуют о созданном системном ServiceRecord и привязанном процессe, но не являются прямыми callback-свидетелями `Service.onCreate`, `onStartCommand`, `onBind`, а также состояния *внутреннего* AppMetrica readiness. Раннюю race/reset внутри SDK нельзя объявить полностью исключённой. Узкий дальнейший путь для A — его независимая точка Push fatal-state; **повторять manifest/aux PID регистрацию и post-crash missing-service гипотезу не нужно**.

**Минимальная причинная правка:** отсутствует, так как manifest/process registration нет доказанного дефекта. Не менять vendor SDK, порядок активации, SDK boolean predicates, service component или fatal handlers без нового доказательства. В PR только read-only B-owned instrumentation, tests, собственный CI и этот отчёт.

**Безопасность:** оригинальные APK/XAPK/DEX, ключи и private generated Java не опубликованы, runner очистил файлы; владелец не тронут; Test.50 и frozen A1 неизменны. **Stage A NO-GO / Stage B LOCKED**.

