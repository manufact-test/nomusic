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

*Заполняется строго по завершённому CI, не по статическим тестам.*
