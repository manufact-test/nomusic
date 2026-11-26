# W180 update — 0.24.57 owner candidate delivered (26.11.2026)

**The old W177 handoff below is historical.** The fresh 0.24.56 diagnostic was subsequently analyzed in `docs/windows/W178-02456-PLAYBACK-POSTCUTOVER-INVESTIGATION-20261126.md`. The next test package is now available:

- **0.24.57 / P-256 sequence 4**, signed source commit `28587670e9efda35c73eb3a49d9702d2d72b3b8c`.
- Direct owner EXE: `https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.57.exe`.
- SHA-256: `bdba9dc06f5e6315d745cc7c27d83d3e5c22fbc89bdb6f3c3a82c6909ab78e47`.
- Floki data-only stage [45817294570](https://github.com/manufact-test/nomusic/actions/runs/45817294570), attempt 2 SUCCESS.
- Root owner HTTPS SHA receipt [45817998403](https://github.com/manufact-test/nomusic/actions/runs/45817998403) SUCCESS; exact EXE SHA confirmed after root verified both the versioned and owner-latest URLs with authenticated full HTTPS GETs.
- This is **not** owner acceptance. Customer stable remains `approved:null`, baseline 0.24.55/seq2. Do not promote 0.24.57 to customers until the owner personally tests playback and says **«выпускай всем»**.

Owner next action: install 0.24.57, listen to mapped «Ау» track 144530503 and another replacement, test ordinary/unmapped playback and Next/Play/Pause. If replacement is still absent, send fresh diagnostics from 0.24.57. Do not reuse W54 from 0.24.55 or the 0.24.56 diagnostics as if they were the new run.

See [W180 delivery record](./W180-02457-OWNER-DELIVERY-20261126.md) and current [NEXT-CHAT](./NEXT-CHAT.md).

---

# CELIKOM Windows W177 — передача диагностики неисправной 0.24.56 (26.11.2026)

## Статус на момент передачи

**Неисправность НЕ устранена.** Владелец сообщил после получения 0.24.56: «там нихуя не работает» и намерен передать **новую диагностику из установленной 0.24.56 в следующем чате**. В этой переписке нового W54/W55 диагностического файла для 0.24.56 ещё нет. Не утверждать, что подмена заработала, и не выдумывать причину по одному скриншоту. Известная ранее лично принятая рабочая версия до переезда: **0.24.54.0**; 0.24.55 не подменяла музыку, 0.24.56 пока не принята.

Работа только с Windows в `manufact-test/nomusic`, ветка `main`; Forgejo `celadmin/nomusic` — резервное одностороннее зеркало. Последний проверенный перед документированием HEAD `main`: `5fd98c7ef66418f2c9ead345d89b47476dc52746`. HEAD нужно перечитать перед любыми изменениями: Android/extension/инфраструктура параллельно обновляют `main`.

## Что фактически известно о 0.24.56

- Все три метаданные Companion, Update Supervisor, Inno Installer в `main`: **0.24.56**, она единственная текущая Windows-кандидатная версия. Не предлагать старую 0.24.55 для проверки исправления.
- Точная защищённая 0.24.56: `https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.56.exe`; стабильный owner/latest, когда проверена серверная публикация: `https://celikom.com/downloads/windows/CELIKOM-Windows-latest.exe`. Сайт защищён существующим Basic Auth для владельца. **Новый чат обязан проверить server receipt и фактический файл перед выдачей очередной ссылки**, поскольку здесь полный HTTPS GET из внешнего инструмента недоступен.
- Подписанная сборка 0.24.56: GitHub Actions [45653125688](https://github.com/manufact-test/nomusic/actions/runs/45653125688) **SUCCESS**, исходный release commit `3c743332d134618fd4bba39ee826e833f39aa54c`, EXE **85 149 440 байт**, SHA-256 `2ee81ceaf9488cc80b88e312053af1744c0b801a8f8f6e725c40266e5553c15a`. Пакет/манифест подписаны **P-256, sequence=3**; EXE не подписан отдельным Authenticode-сертификатом. Последняя проверенная автоматическая закрытая доставка на Floki [45662617113](https://github.com/manufact-test/nomusic/actions/runs/45662617113) SUCCESS.
- По поздним записям инфраструктурного чата **root owner current был переведён на 0.24.56**, `celikom-windows-signed-owner.timer` был active, а клиентский signed stable **0.24.55/sequence 2** прошёл HTTP200+полный SHA256 `f4c9a7881164ac7a9b5681d9f3568e5cbd3a9915c9e1da7b475caa20d3fb6487`. См. `docs/migration/CELIKOM-ONE-TIME-FLOKI-RELEASE-ACTIVATION-2026-11-25.md`. Начальные разделы старых W175/W176 документов, помечающие серверную активацию «не выполнена», **исторические**, а не текущее состояние. Здесь новый live owner HTTPS не перепроверен.
- `.github/release/windows-customer-stable.json` сейчас содержит `"approved": null`: **0.24.56 НЕ выпущена всем** и автообновление установленных клиентов **НЕ принято реальным old→new тестом**. Нельзя обновлять approval без явного «принимаю / выкатывай всем». 0.24.55 — серверный откат/клиентский принятый подписанный baseline, 0.24.54 — последняя лично проверенная владельцем по музыке до миграции. Различать эти два смысла «рабочей версии».
- API `https://api.celikom.com`; сайт `https://celikom.com`; API app `/srv/celikom/app/staging-20261122`; DB `celikom_cutover_20261124`. Старый Hostinger оставить для совместимости/отката; Android, расширение, UI, gain, VPN, подписки и серверную архитектуру не трогать без доказательств.

## Последняя имеющаяся реальная диагностика (старой 0.24.55, НЕ 0.24.56)

Владелец прислал `CELIKOM WINDOWS OWNER DIAGNOSTICS — W54`, `GeneratedUTC=2026-11-25T16:07:10.8894656+00:00`, `AppVersion=0.24.55.0`, `NativeModuleVersion=0.24.31`, `NativeModuleMatchesApp=true`, `NativeIntegration=ACTIVE`, `BridgeStarted=true`, `Enabled=true`, `SignedIn=true`.

В последних 15 минутах были `GUI_STARTED`, `BRIDGE_STARTED`, `START_ENABLED`, `HOST_LOADED`, `BUNDLE_PRESENT`, `RESOURCE_ATTACHED`, `RENDERER_INJECTED`, `PLAYER_CDP_READY`, `PLAYER_NET_READY`, `NATIVE_STATE_RECEIVED`, `RENDERER_STATE_ON`. Встречался `PLAYER_ENGINE_FAST_PAUSE`, но **не было подтверждения загрузки или звучания подмены текущего трека** (`ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`, `PlayerAudibleEventObserved=false`, `NativeMediaUrlExactMatchObserved=false`, `PlayerNetworkRequestObserved=false`). Появились `STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE` и `STABLE_UPDATE_CHECK_FAILED`; это отдельная линия обновлений, не установленная причина отсутствия подмены. Старые события `SOURCE_ACTIVE_REPLACEMENT` от 21–22 ноября в persistent history **не доказывают** воспроизведение 25 ноября.

В GUI при проигрывании «Ау» 10AGE / Ramil' было «Версия CELIKOM доступна», но реально слышен **оригинал**. Надпись о наличии замены не означает подменённый аудиоисточник.

Живой защищённый API probe [45651443471](https://github.com/manufact-test/nomusic/actions/runs/45651443471) SUCCESS: для двух отдельными временными сессиями проверенных пользователей `resolve?service=yandex&track_id=144530503&audio_formats=mp3,m4a&audio_profile=windows_gain_v1` нашёл `found:true`, вернул корректные signed audio/mpeg grants и HTTP206 Range. Временные сессии удалены. **Это не доказывает**, что DPAPI-токен владельца, точная загрузка grant на его компьютере, native getFileInfo, установка media URL и слышимое воспроизведение работают.

## Последнее исправление, которое 0.24.56 должно проверить

`windows-companion/w23/renderer-entry.mjs`: одна отложенная (после 3,5 секунд) проверка уже загруженного текущего Yandex-трека, только для PLAYING/PAUSED, с положительным авторизованным `adapter.prime(trackId)` и штатным `playerSourceRefresh.request(trackId)` → `reloadEntity("QUALITY_CHANGE")`. Не меняли архитектуру плеера/очередь/позицию/громкость. Тесты `windows-companion/w23/initial-current-source.test.mjs`, [Windows CI 45652096445](https://github.com/manufact-test/nomusic/actions/runs/45652096445) SUCCESS. **Это только проверка сценария в CI, не гарантия реального audio replacement.** Диагностические маркеры: `NATIVE_INITIAL_SOURCE_REVALIDATE`, `NATIVE_INITIAL_SOURCE_RELOAD`, `NATIVE_INITIAL_SOURCE_RELOAD_OK`, `NATIVE_INITIAL_SOURCE_RELOAD_DEFERRED`.

## Что делать в следующем чате

1. В первую очередь **прочитать новую прикреплённую пользователем диагностику именно из 0.24.56** целиком, проверить точную версию, UTC, окно событий, current source / grant / native hook / playback error / обновление. Не требовать повторно инструкций, PowerShell, IDE, CMD, SSH или переустановок до анализа.
2. Разделить три независимых состояния: «сервис знает, что замена существует», «native/getFileInfo реально получил и установил подписанный источник», «в действительности играет наша музыка». Отдельно проанализировать `STABLE_UPDATE_CHECK_FAILED`; не объявлять его причиной audio failure без связи в событиях.
3. Сверить с 0.24.54 функциональным baseline, 0.24.55 миграционной неудачей и W175 точечным патчем. Проверить реальное происхождение запросов, grants, CORS/сетевая доступность, точное подключение в Yandex и логи; не менять VPN/gain/UI/архитектуру наугад. Если требуется — дополнительная **безопасная обезличенная диагностика**, но никаких сырых токенов/audio URL.
4. При установленной причине сделать **минимальный** Windows-only fix в `main`, резервное состояние перед изменением, CI и **следующую уникальную версию строго выше 0.24.56**, новый подписанный манифест sequence >3. Никогда не подменять bytes EXE под прежним номером. Release через уже настроенный GitHub Actions Windows builder → Floki runner data-only signed spool → root publisher → owner сайт; дать только проверенную прямую ссылку с `celikom.com`.
5. Владелец устанавливает поверх текущей и проверяет «Ау», другие замены, Play/Pause/Next, статусы, вход, VPN. **Только после явной приёмки** исправленного EXE обновлять customer approval. После этого отдельно проверить фактическое автоматическое обновление installed old→new, signed feed, safe point, rollback. Hostinger не удалять; платные функции не включать.

## Документация и ссылки

- Текущая Windows точка: `docs/windows/NEXT-CHAT.md` (новая запись W177 должна быть выше устаревшей W176/W175 истории).
- Схема выката/гейтов: `docs/migration/CELIKOM-ONE-TIME-FLOKI-RELEASE-ACTIVATION-2026-11-25.md`.
- Общая инфраструктура: `docs/migration/CELIKOM-NEXT-CHAT-START-2026-11-23.md`, `docs/migration/CELIKOM-FLOKINET-DECISIONS-2026-11-22.md`.
- История сохранения Windows 0.24.54: `docs/windows/W174-MAINLINE-CONSOLIDATION-20261121.md`, `docs/windows/W173-START-UX-AND-OWNER-UPLOAD-AUDIT-20261121.md`.
