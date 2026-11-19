# CELIKOM Android A1 — передача после дополнительной CFG-проверки, 19.11.2026

## Точка для продолжения

- GitHub `manufact-test/nomusic`.
- **Единственная рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Начинать **с HEAD этой ветки**, не с NAV40/NAV45 commit и не с default branch.
- Точно сохранённый NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391`, signed NAV45 `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8` (27/27 [#44552661805 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44552661805)). Test.50, Windows, все owner подписанные APK/ZIP и оригинальный Yandex production неприкосновенны.
- Читать по порядку: [NEXT-CHAT.md](NEXT-CHAT.md), [ANDROID-A1-POST-NAV45-LIVE-TRACK-ALBUM-SOURCE-CALLBACK-20261119.md](ANDROID-A1-POST-NAV45-LIVE-TRACK-ALBUM-SOURCE-CALLBACK-20261119.md), [ANDROID-A1-TRACKID-BRANCH-CFG-ALL-PATH-NO-GO-20261119.md](ANDROID-A1-TRACKID-BRANCH-CFG-ALL-PATH-NO-GO-20261119.md).

## Что реально сделано

До этой передачи в Android runtime установлен read-only, **не аудиозаменяющий** маршрут:

`original Track + Album → creator-owned tCa TrackWrapper → original source/PeriodID → live SLOT_B renderer same-callback`

Исходные Java ссылки доступны в `StageBAudioEvidence.exactOriginalTrackAlbumForWrapper` и `NativeRendererStreamEvidence.ActiveOriginalTrackObserver` через `ExitCallsiteWitness`. Только уникальные, непротиворечивые ссылки в одном callback, никакого подбора через MediaItem, имена, duration. [JVM #44574303898 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44574303898), [publisher-first ARM13 #44572917325 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44572917325). Это **поздняя** точка в original renderer: она не может выдавать предразрешение на замену original DataSource до prepare.

**Новый единственный целевой заход:** созданы `a1_trackid_cfg_track_alias.py` и `test_a1_trackid_cfg_track_alias.py`; обновлены `a1_private_track_id_api_provenance.py` и workflow. У подписанного Yandex 2025 оригинала семантический API `trackId` есть, но читавшийся в original `LGp0` Track String field receiver **не доказан тем же Track**, что оригинальный формальный параметр через все ветви. Предыдущий скан отвергал DEX switch, новая версия его правильно учитывает: [#44578410987 SUCCESS, 10/10 tests](https://github.com/manufact-test/nomusic/actions/runs/44578410987), `CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN`, `same_formal_track_source_to_trackid_api_candidate_count=0`. **Не утверждать, что ID отсутствует или семантическая точка опровергнута для всех возможных маршрутов.**

## Критически важно

`CELIKOM_REPLACEMENT=NOT_CONNECTED` и `IDENTITY_STATUS=STRUCTURAL_ONLY`. Никакого NAV46 owner APK/ZIP не выпущено, **подмены не слышно**. Сохранять оригинал на неизвестном треке/edition/generation, не допускать двух плееров или mid-play переключения.

**Следующий шаг:** не плодить однотипные read-only CI и owner-диагностики. Использовать **уже существующий** живой исходный Track/Album/source маршрут, но перенести проверку его доказанной идентичности в **раннюю pre-prepare descriptor/source границу**. Нужны точно семантически удостоверенные `trackId+albumId+editionId` и актуальная selection generation; только после этого разрешён fail-closed `NativeReplacementLifecycle`/source admission для approved CELIKOM. Не считать произвольный `long` из `Track.new`, `Track.super():String`, `Album.if():String`, `Ldjv.a()` или blank MediaItem удостоверением трека/редакции. При отсутствии ранней доказанной точки — оставлять original, не выпускать декоративный APK.

Владелец просил **работать, без промежуточных сообщений и бесконечных отчётов**, и в конце отдать один реальный подписанный APK/ZIP только когда появится существенный функциональный шаг. Если его нет — точная причина без ложного «работает».

## Для начала следующего чата

Пользователю отправить готовый текст из текущего чата вместе с актуальным SHA HEAD. Следующий исполнитель обязан проверить HEAD заново: документы могут дописываться поверх последнего исходного коммита, но архитектура и подписанные релизы не должны пересоздаваться.
