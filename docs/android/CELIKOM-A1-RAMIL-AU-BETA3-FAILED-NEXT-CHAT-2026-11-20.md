# CELIKOM Android A1 — BETA3 не работает: конкретная передача (20 ноября 2026)

## Фиксированная точка

- Repo: `manufact-test/nomusic`
- Только ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- HEAD до этой передачи: `1566bdc8f959cce95b9afd3968872a1bd7ba5823`; HEAD самой документации смотреть в GitHub.
- Последняя проверенная владельцем APK: `CELIKOM-A1-RAMIL-AU-BETA3-HONOR50-20261120.apk`, исходный CI [#44753682381](https://github.com/manufact-test/nomusic/actions/runs/44753682381) SUCCESS. **Живой акустический результат: FAIL, всегда звучит цензурный оригинал.** Это не релиз, не подтверждённое воспроизведение альтернативы.
- Новый TXT с HONOR 50 / Android 13: `CELIKOM-A1-Diagnostics-1795187145828.txt` (приложен пользователем к чату 20.11.2026, не выкладывать в публичный репозиторий). Тест: 10AGE / Ramil' — «Ау», предполагаемый publisher trackId `144530503`; тестовый участок ~00:43–00:54. Нельзя считать publisher ID **доказанным для конкретного запуска**, потому что issuer callback не сработал.
- Оригинальные Yandex app, Windows, Test.50, NAV40/NAV45 и backend не менять. Один ExoPlayer Яндекса, не делать второй плеер/второй вход в Яндекс.

## Реальная диагностика — не интерпретировать в пользу успеха

Новый маркер `DIAGNOSTIC_BETA_BUILD=A1_TRACKID_BETA_RAMIL_AU_20261120` **ACTIVE** — верная версия BETA3. Старый `DIAGNOSTIC_BUILD=NAV_V45_CURRENT_MEDIAITEM_LOGICAL_ID_READONLY` остаётся как baseline. Статический `CELIKOM_REPLACEMENT=NOT_CONNECTED` — legacy strict triple status, не заменяет актуальных beta counters.

**Актуальные beta counters:**

| Этап | Из TXT | Смысл |
| --- | --- | --- |
| `OWNER_ENABLED` | `ONE` | Владелец вошёл в отдельный CELIKOM и нажал BETA, доступ подтверждён |
| `ISSUER_TRACKID` | `NONE` | Нет события exact original Retrofit trackId по разрешённому ID |
| `EXACT_BETA_CREATOR` | `NONE` | Нет связки original publisher Track ↔ tCa wrapper и issuer ID |
| `ORIGINAL_SETTER` | `NONE` | Не привязана успешная смена original Player source к разрешённому треку |
| `PREFETCH_STARTED`, `SIGNED_MPEG_READY` | `NONE`, `NONE` | Не было prefetch альтернативы |
| `OWNER_RESOLVE_REQUEST`, `GRANT_ADMITTED` | `NONE`, `NONE` | CELIKOM resolve/grant вообще не запрашивался для источника |
| `EXACT_PREPARE` | `FEW` | Реальный original MediaPeriod.prepare засвидетельствован |
| `DECISION_ALTERNATE`, `DATASOURCE_ARMED`, `AUDIO_OPEN`, `AUDIO_READ` | всё `NONE` | В ExoPlayer ни разу не использовались альтернативные байты |

**Коррелирующие Stage B:** `FILEINFO_DTO=FEW`; `EXO_DESCRIPTOR_BUILT=FEW`; `EXO_FACTORY_CREATED=FEW`; `EXO_SOURCE_INSTANCE=MANY`; `EXO_OPEN_OK=MANY`; `EXO_READ_POSITIVE=MANY`; `EXO_IO_FAILURE=NONE` — оригинальное аудио работает. `NATIVE_TRACK_FLOW_EMIT=ONE`; `NATIVE_TRACK_SOURCE_REQUEST=ONE`; `TRACK_WRAPPER_LINK=ONE`; `TCA_CREATOR_OWNER_ENTER=FEW`; `TCA_CREATOR_WRAPPER_CONSTRUCTED=FEW`; однако `NATIVE_MAIN_SOURCE_ENTER=NONE`, `WRAPPER_MAIN_SOURCE=NONE`, `WRAPPER_DESCRIPTOR_LINK=NONE`, `TRACK_DESCRIPTOR_FACTORY_LINK=NONE`, `TRACK_FACTORY_SOURCE_LINK=NONE`. Механизм не связал оригинальный source и реально читаемый Exo DataSource, несмотря на реальное чтение оригинального звука.

В TXT есть `LOG_TRIMMED`; прошлые строковые события регистрации могли быть обрезаны. Вышеперечисленные экспортные счетчики снимаются из памяти по нажатию «Диагностика», поэтому для этих категорий `NONE` достоверен в рамках наблюдаемого процесса. `METRICA_EXCEPTION_SUMMARY=MANY`, но это **не доказывает**, что именно AppMetrica блокирует аудио; не уводить работу туда.

## Приоритетный пул задач — выполнять по порядку

**P0 — первый ненулевой issuer ID, без фальшивой личности.** На живом clone `ISSUER_TRACKID=NONE`, поэтому открыть `ExitCallsiteWitness.installPublisherTrackIdProxyWitness()` / `hookConcretePublisherTrackIdProxy()` и `StageBAudioEvidence.onPublisherAnnotatedTrackId()`. Проверить, когда реально создаётся Retrofit proxy, что конкретный `InvocationHandler.invoke` вызывается на active track и что выбран `@Query("trackId")`. Возможен промах: proxy создан до установки hook или использован cached request, обрезан контекст вызова, неверный allowed trackId, нерелевантный путь FileInfoApi. Не объявлять какую-либо гипотезу доказанной. При необходимости добавить **только обезличенные и ограниченные по частоте** события: REGISTERED/PROXY_SEEN/ISSUER_ID_PRESENT/ALLOWLIST_MATCH/Gp0_SCOPE_MATCH; без самого trackId/токенов/URI/аккаунта в экспорте. Проверить фактическое соответствие проигранного «Ау» publisher ID `144530503`; не угадывать.

**P1 — вторая недостающая source chain, не распространять publisher bytes по наитию.** Разобраться с `NATIVE_MAIN_SOURCE_ENTER=NONE` и `WRAPPER_DESCRIPTOR_LINK=NONE`. Код: `ExitCallsiteWitness.installNativeTrackSourceContinuityWitness()` (оригинальная `download2.o.for(... tCa ...)`) и `installExactNativeExoSourceWitness()` (descriptor→factory→DataSource), `StageBAudioEvidence.enterNativeMainSourceRequest()` / `onNativeExoDescriptorBuiltForCurrentWrapper()`; проверить регистрацию методов и реальный runtime путь. Может быть другой coroutine callsite либо нужная установка до жизненного цикла. Требовать exact Java object reference, successful original Player setter/generation, untouched/unopened Exo DataSource. Нет данных — продолжать original audio.

**P2 — при появлении P0+P1 использовать существующую signed owner beta, без второго плеера.** `NativeOwnerControlPlane.warmFromPublisherTrackId()` → `requestForTrackIdBeta()` → `NativeEarlySourceLifecycleBridge` → `NativeExoAlternateByteRoute`. Существующие условия approved+entitled, signed HTTPS, MIME MPEG, Range/206, bounded original pre-prepare, generation invalidation и Next/Stop сохранять. Не сканировать снова все DEX, не переключаться на PCM/Metrica без ясного нового факта. Факт успеха только `AUDIO_READ` не `NONE` + **слышно альтернативу владельцу**.

**P3 — нормальный UX; пользователь прямо отверг отдельную BETA-кнопку, отдельную форму и плавающую диагностику.** Яндекс-логин внутри клона уже есть, но backend CELIKOM использует **отдельную** серверную сессию, email/password и `auth/activate`. Они не являются автоматически общей учёткой. Сейчас `NativeOwnerControlPlane.hasSession()` читает Android Keystore encrypted refresh token; `start()` проверяет entitlement. Реализовать после исправления P0/P1 тихий автоматический `start()` при уже существующей сессии CELIKOM, а не требовать нажимать BETA при каждом процессе; первоначальная авторизация CELIKOM всё ещё нужна только если нет законной связанной сессии. Перенести первоначальный CELIKOM login в штатный экран CELIKOM (или добавить законное account-linking позже), а не выдавать Yandex пароль за CELIKOM credential. Скрыть плавающие `CELIKOM BETA` и `Диагностика NAV9` из пользовательского музыкального экрана; экспорт диагностики оставить только в настройках/режиме разработчика. Не убирать серверные права доступа и контроль одобрения.

**P4 — один повторный акустический тест после доказанного движения P0/P1.** Тот же 10AGE/Ramil' «Ау», publisher ID `144530503`, 00:43–00:54. Один signed APK/Library для HONOR 50 Android 13, не выдавать серию неизменённых APK. Сначала слышим оригинал vs альтернативу; затем Pause, Seek, Next и MyWave. TXT только если нужно. CI/JVM PASS — **не** звуковой PASS.

## Правила продолжения

1. **Не начинать архитектуру заново.** Не перебирать legacy NAV40/NAV45, Test.50, Windows, backend; этот проход нужен для первого звучащего alternative inside original Yandex ExoPlayer.
2. Два рабочих препятствия подтверждены пользователем и диагностиками: отсутствующий issuer ID в beta и отсутствующий native main-source → Exo chain. Остальное после них.
3. Длинные блоки реальной работы без промежуточных микрорепортов. Проверки через GitHub CI. Изменения атомарно в этой же ветке. Успех звука не объявлять без теста владельца.
4. До выпуска новой версии проверить, что появился реальный маршрут от издательского Track/ID до оригинального DataSource. Не выпускать ради зеленого CI или косметики.
5. Документировать законченные этапы в этом файле и `CELIKOM-A1-LIVE-AUDIO-NEXT-CHAT-2026-11-20.md`, передать новый HEAD следующему чату.
