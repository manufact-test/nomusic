# CELIKOM Android A1 — START FOR NEXT CHAT
Дата фиксации: 21.11.2026

## Рабочая точка

- Репозиторий: manufact-test/nomusic
- Единственная рабочая ветка: experiment/android-a1-metrica-init-state-observer-arm13-20261112
- Последний известный HEAD перед этим handoff-документом: 4b0351eddf3daead5cc88c4e8a93f6079173b9bd. Этот документ и последующие правки документации — только docs; в начале следующего чата обязательно получить фактический HEAD ветки.
- Не начинать заново, не менять архитектуру, не трогать закрытые маршруты LyEa/LCK1, не пересобирать NAV40/NAV45, не откатывать ранее подтверждённые рабочие участки.

## Что уже известно — не заставлять владельца доказывать повторно

- Проверяется конкретная песня Рамиля «Ау», которую владелец выбирает непосредственно из альбома.
- Историческая запись CELIKOM: альбом 38902809, Yandex track ID 144530503, альтернатива №1, одобрена и активна; MP3, длительность 180872 мс. Ранее файл был сверен с активной записью расширения.
- Владелец подтвердил: Windows-версия и браузерное расширение подменяют эту же песню из этого же альбома. Считай это установленным фактом. Не предлагай искать её через «Мою волну», не проси повторно доказывать соответствие трека и не отправляй владельца собирать скриншоты вместо самостоятельной проверки.
- В этой сессии живой вход в Hostinger/admin/БД не был выполнен: доступного авторизованного браузера/hPanel-коннектора в текущем наборе инструментов не оказалось. Не заявлять, что БД проверена. Если в следующем чате доступен реальный авторизованный браузер — проверить самому; если нет, честно не выдавать историческую запись за live-проверку и продолжать работу по коду/CI.

## Последняя диагностика BETA11

Файл владельца: CELIKOM-A1-Diagnostics-1795254709741.txt.

- OWNER_ENABLED=ONE, PREFETCH_STARTED=ONE.
- ISSUER proxy hook/created/method selected — по одному; handler invoke и args present — FEW.
- При этом ISSUER_TRACKID=NONE, ISSUER_VALUE_TARGET_ALLOWLISTED=NONE, ORIGINAL_CREATOR_KEY_CONFIRMED=NONE, EXACT_BETA_CREATOR=NONE, ORIGINAL_SETTER=NONE; OTHER_NUMERIC=FEW и SCOPE_ABSENT=FEW.
- OWNER_RESOLVE_NOT_APPROVED=ONE, OWNER_RESOLVE_APPROVED=NONE; сетевой ошибки и невалидного JSON нет. SIGNED_MPEG_READY, SIGNED_AUDIO_READY, GRANT_ADMITTED — NONE; DECISION_ALTERNATE, DATASOURCE_ARMED, AUDIO_OPEN, AUDIO_READ — NONE.
- ВАЖНО: BETA11 OWNER_RESOLVE_NOT_APPROVED — агрегатный маркер проверки found + approved + entitled + MIME audio/mpeg. Он не говорит, какой именно флаг не прошёл. Из него нельзя делать вывод, что запись отсутствует, выключена или не одобрена.
- EXACT_PREPARE=ONE, но это не привело к grant/alternate. В Stage B есть TCA_CREATOR_WRAPPER_FLOW_MATCH=ONE, TCA_CREATOR_WRAPPER_ALBUM_LINK=ONE, TCA_CREATOR_FLOW_LATER_SAME_TRACK=ONE и TCA_CREATOR_FLOW_LATER_ALBUM_OBSERVED=ONE.
- При этом NATIVE_MAIN_SOURCE_ENTER=NONE, WRAPPER_MAIN_SOURCE=NONE, WRAPPER_DESCRIPTOR_LINK=NONE, TRACK_DESCRIPTOR_FACTORY_LINK=NONE, TRACK_FACTORY_SOURCE_LINK=NONE, TRACK_SOURCE_OPEN_LINK=NONE, TRACK_SOURCE_READ_LINK=NONE. В renderer hook status NATIVE_PLAYER_SOURCE_SETTER зарегистрирован; TRACK_PLAYER_SOURCE_SCOPE_ENTER/SAME_SCOPE и LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED наблюдались FEW, но полная связка creator Track/Album → конкретный live source → descriptor/factory → новый unopened DataSource не доказана.
- EXO_SOURCE_INSTANCE/OPENED/READ и EXO_READ_POSITIVE имеют MANY, но это не доказывает CELIKOM-подмену. Итоговый статус прямо указан как CELIKOM_REPLACEMENT=NOT_CONNECTED.
- Не путать одно prefetch с разрешённой подменой. Prefetch может происходить из creator-конструктора tCa(String); сам по себе он не подтверждает выбранный publisher track ID или текущий audible source.

## Уже найденная ошибка форматов и внесённая правка

- extension/src/api/api-client.ts запрашивает audio_formats=mp3,m4a.
- Android BETA11 запрашивал только audio_formats=mp3 и принимал только audio/mpeg, хотя NativeGrantContract и NativeExoAlternateByteRoute уже поддерживали audio/mp4.
- В NativeOwnerControlPlane на ветке исправлен запрос на mp3,m4a; общий gate допускает только approved + entitled и audio/mpeg/audio/mp4; Range-проверка различает MP3 ID3/frame и ISO-BMFF ftyp; certified-source и limited-beta используют общий форматный gate; добавлены отдельные privacy-safe причины отказа (not found, approval flag, entitlement, unsupported MIME, MPEG/MP4, signed audio ready).
- Добавлен regression test на соответствие Android контракту расширения; добавлен отдельный тест NativeGrantContract на audio/mp4.
- Не объявлять это доказанной причиной отказа именно «Ау»: историческая запись указывает на MP3 180872 мс. Это подтверждённая ошибка parity клиентов, но она не объясняет автоматически текущий отказ для MP3. Следующий шаг — выяснить, какой именно publisher track ID реально дошёл до resolve и что именно вернул сервер.

## CI на момент передачи

- Workflow 44893907029 — JVM issuer-proxy contract SUCCESS; ARM13 job дошёл до No-suppression native ARM13 publisher-first side-by-side 75s test и ещё выполняется на последней проверке.
- Workflow 44893887129 — clone-alone differential ARM13 SUCCESS. Это отдельная проверка, не product acceptance.
- Workflow 44893887112 — exact triple-identity pure-Java model tests SUCCESS.
- Workflow 44893567368 — прежний publisher-first ARM13 75s workflow SUCCESS.
- APK для владельца пока не экспортирован из последнего изменения и на телефон не установлен. Успешный CI не равен доказанной подмене/акустическому результату.

## Что делать дальше — строго по стратегии

1. Сначала проверить завершение workflow 44893907029. Не запускать параллельно дублирующую сборку, пока эта не закончилась.
2. Проверить живую запись/resolve самостоятельно, если доступна авторизованная админка: альбом 38902809, publisher track ID 144530503, активная одобренная альтернатива №1, MIME/файл/длительность; отдельно сравнить фактический track_id, который Android отправляет в resolve, с ID, который использует расширение для этой песни. Не просить владельца присылать скриншоты, если доступ можно проверить самому.
3. Главный технический узел — почему в BETA11 не появляется ISSUER_TRACKID/ORIGINAL_CREATOR_KEY_CONFIRMED/ORIGINAL_SETTER для реального трека и почему creator Track+Album не доходит до точного source setter/descriptor/factory. Идти от уже имеющихся точек: issuer proxy → exact Track/Album creator → original Player source setter → descriptor/factory → тот же unopened DataSource. Не исследовать десятки соседних классов без доказательства, что текущий вызов проходит через них.
4. После точечного изменения — один конкретный regression test + нужный CI. Не делать серию APK с одними новыми счётчиками. Новый APK владельцу — только когда есть конкретная правка, которую действительно нужно проверить на его телефоне; дать прямую ссылку на GitHub artifact/Library, не требовать ADB, кабель, PowerShell или IDE.
5. Критерий успеха — не зелёный CI и не наличие grant само по себе: точный выбранный оригинальный Track/Album/source → валидный CELIKOM grant → DECISION_ALTERNATE → DATASOURCE_ARMED → AUDIO_OPEN/READ, а затем подтверждение владельцем, что из альбома звучит наша версия.
6. Не менять сервер/оригинальный Яндекс и не ослаблять подписи, ID, album/source identity или fail-closed проверки ради зелёного статуса.

## Как работать с владельцем

- Идти прямо к результату, крупными осмысленными шагами. Не присылать мелкие регулярные отчёты и не останавливаться после каждой найденной строки.
- Не уходить в бесконечный реверсинг и не начинать боковые исследования. Каждый следующий шаг должен устранять конкретный блокер на пути к работающей мобильной подмене.
- Не спрашивать то, что уже известно из истории и диагностики. Владелец тестирует на одном телефоне; любые действия на телефоне — только если без них нельзя подтвердить реальный результат.
- Если нужна проверка владельцем, дать одну короткую инструкцию и дождаться результата. До фактической проверки не говорить «готово».
- Приоритет — работающая мобильная версия CELIKOM, не новые исследовательские документы и не косметические улучшения диагностики.


---

## 2026-11-21 follow-up — late creator Flow + original source continuity

Current branch HEAD: `75b33733a2e8106823b1dcb4d7b3ac68298c9881`.

### BETA11 diagnosis

The last owner diagnostic showed:
- Publisher proxy interception worked, but no allowlisted publisher ID was bound to the selected creator Track.
- The exact creator Track+Album wrapper was observed; the same Track entered Flow later.
- The original setter/Track ID candidate path was one-shot: it evaluated before that later Flow event and was never retried.
- `OWNER_RESOLVE_REQUEST=NONE`, while `PREFETCH_STARTED=ONE` and `OWNER_RESOLVE_NOT_APPROVED=ONE`. The rejected call was speculative prefetch; the source-bound resolve for the selected original setter never ran.
- Exo descriptor/factory/DataSource objects were created and used, but Track→descriptor→factory→DataSource lineage counters remained zero. `download2.o.for` and its continuation route were not observed.

### Changes now on the working branch

1. `NativeRendererStreamEvidence` retains the exact successful original Player setter lineage and rechecks the publisher ID after the same creator Track enters Flow.
2. `NativeEarlySourceLifecycleBridge` accepts that late candidate only for the same setter generation, dispatches the source-bound resolve once, and rejects conflicting IDs or any candidate arriving after prepare.
3. The existing pre-prepare grace now waits briefly for an explicitly proven allowlisted creator Track whose same-Track Flow event is pending, then waits for its grant. It does not wait for arbitrary tracks.
4. `StageBAudioEvidence` now carries the exact TrackWrapper through the real `cA9.extends` Player selection call and through the exact original MediaPeriod prepare, recovered only when the period's source field is the same object as the successful Player source setter. This gives existing descriptor/factory/DataSource hooks the correct wrapper scope without falsely marking `download2.o.for` as entered.
5. Regression coverage now checks late Flow promotion, rejection after prepare, bounded pre-prepare waiting, selected-wrapper descriptor/factory continuity, and exact MediaPeriod-source→Player-wrapper identity.

### Verification

- JVM regression workflow: SUCCESS on HEAD `75b33733a2e8106823b1dcb4d7b3ac68298c9881`. Test output: `RAMIL_AU_ORIGINAL_TRACK_ONLY_BETA_LINEAGE_PASS`.
- ARM13 workflow `44897905526`: running on code commit `65bc7a613762cef00fe9cbcff7c7949ea6af67de`; scoped-module build had started. Await final conclusion before declaring ARM13 green.
- Clone-alone differential workflow `44897905524`: running; not product acceptance.
- No owner-phone APK was exported. The workflow was not dispatched with the APK export input.
- Live admin was not accessed: no authorized hosting/admin browser connector was available in this session. Backend route and client contracts were inspected in the repository.

### Next action

Check the final result of ARM13 workflow `44897905526`. If green, prepare ONE functional owner-phone build only for this code change and test the same Ramil' «Ау» selection. The decisive result is now whether `ORIGINAL_SETTER` and source-bound `OWNER_RESOLVE_REQUEST` appear, the server approves the exact selected Track ID, and the same original wrapper reaches descriptor→factory→fresh DataSource before its first open. Do not repeat NAV40/NAV45 or reopen adjacent class investigations.
