# CELIKOM Android A1 — signed trackId / CFG all-path verification, 19.11.2026

## Входная точка

Единственная ветка `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Работа начата с зафиксированного HEAD `a366bcf58144cb233b244caa8be2c7d0f62b37c4`. Подписанные артефакты NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391`, NAV45 `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8`, Test.50 и Windows **не менялись**.

Сохранённая рабочая точка: [ANDROID-A1-POST-NAV45-LIVE-TRACK-ALBUM-SOURCE-CALLBACK-20261119.md](ANDROID-A1-POST-NAV45-LIVE-TRACK-ALBUM-SOURCE-CALLBACK-20261119.md). В существующем Android observer уже есть точные оригинальные Java-объекты `Track`+`Album`+`source` в одном активном `SLOT_B` / `PlaybackInfo.PeriodID` renderer callback, но это *поздний* callback чтения, а не доказанное раннее pre-prepare переключение звукового источника.

## Один дополнительный целевой заход

Объект: **только подтверждённый в издательски подписанном оригинале 2025.10.4 #120.1gpr** маршрут `FileInfoApi(trackId)`/`DownloadInfoApi(trackId)` → промежуточное String-поле → один его writer → 21 inbound caller, включая `LGp0` оригинального source-track creator. На предыдущем шаге первый обратный проход останавливался на ветвлении: `TRACK_RECEIVER_BRANCH_UNPROVEN`.

Добавлены:

- `android/native-yandex-hooklab/ci/a1_trackid_cfg_track_alias.py` — ограниченный **DEX must-alias CFG**, проверяющий все достижимые ветви, переходы, packed/sparse switch, неизменённый формальный Track-параметр и значения регистров. При try/catch, недопустимой цели, неизвестной записи, неподдержанной конструкции или конфликтующем пути — fail-closed. Поля, значения, ID, сетевые данные и DEX не экспортирует.
- `android/native-yandex-hooklab/ci/test_a1_trackid_cfg_track_alias.py` — **10 независимых синтетических JVM-free/Python проверок**: ветви с подтверждённым и конфликтующим alias, packed/sparse switch, cast, неподдерживаемая форма, ложное поле, недостижимый read.
- `android/native-yandex-hooklab/ci/a1_private_track_id_api_provenance.py` — интеграция только в найденный `LGp0`-caller и вывод **категорий**, а не приватных имён/ID.
- `.github/workflows/android-a1-track-model-id-edition-annotation.yml` — запуск тестов до чтения оригинала, проверка exact pinned 16 publisher-signed splits / 6 DEX; private XAPK удаляется в конце, не выпускается APK.

## Проверенный результат

[GitHub Actions #44578410987 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44578410987); `Ran 10 tests ... OK`, проверка оригинала и удаление входа завершены успешно. Первый промежуточный [#44577716583 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44577716583) показал `CFG_UNSUPPORTED_FLOW` потому, что CFG не обрабатывал DEX switch-data. Это ограничение исправлено и перепроверено **именно на исходном подписанном оригинале**, а не на fake-DEX.

**Итог точного source creator пути:**

```text
exact_creator_track_parameter_present = true
exact_creator_trackid_argument_origin_categories =
  [DIRECT_TRACK_STRING_FIELD, OTHER_OBJECT_FIELD]
exact_creator_branch_aware_receiver_cfg_verdicts =
  [CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN]
same_formal_track_source_to_trackid_api_candidate_count = 0
verdict = PUBLISHER_TRACKID_API_ANNOTATIONS_PRESENT_NOT_SOURCE_PROOF
```

Теперь причина конкретнее: *по всем поддерживаемым путям* исходный регистр-получатель String-поля **не удостоверен** как **тот же формальный оригинальный Track** из `LGp0`; это **не** «алгоритм испугался switch», и **не** доказательство, что trackId отсутствует или что используются точно разные треки. Сочетание `Track.super():String`, `Album.if():String`, `Track.new(...,long,...)`, `Ldjv.a():String` по-прежнему не подтверждает `trackId+albumId+editionId` для активного исходного source и поколения проигрывания.

## Решение и следующий шаг

**Подмену не подключали.** Нельзя взять API `trackId` от неизвестного/другого `Track` и подставить в активный `SLOT_B`; нельзя допускать подмену на уровне уже начатого audio read. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Play/Pause/Seek/Next/MyWave исходного приложения не изменены. **Нового owner-signed APK/ZIP нет** — выпуск диагностики без новой безопасной точки запрещён.

В следующем чате **не повторять** ещё круг пустых MediaItem, String-геттеров, DEX сканов. Следующая реальная задача — найти **раннюю** native descriptor/source pre-prepare точку (до воспроизведения), где `Track` creator, исходный `TrackWrapper` и source являются **тем же** экземпляром/поколением, и семантически верифицировать тройку `trackId+albumId+editionId`. Только после этого применить уже написанный `NativeReplacementLifecycle`/source admission в единственном оригинальном плеере с fail-closed ORIGINAL fallback. Поздний renderer callback может быть дополнительной валидацией, но **не pre-prepare admission**.

Все изменения данного захода ограничены read-only CI-инструментами и документацией; Android runtime/owner APK не изменялись.
