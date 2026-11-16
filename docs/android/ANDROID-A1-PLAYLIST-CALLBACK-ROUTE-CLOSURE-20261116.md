# CELIKOM Android A1 — playlist callback route closure

**Дата:** 16 ноября 2026  
**Репозиторий:** `manufact-test/nomusic`  
**Рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**Code checkpoint:** `c0cf9896916cca9b13299cdb3fde7a78ffbe4da1`  
**CI #213:** [SUCCESS, 127/127 тестов](https://github.com/manufact-test/nomusic/actions/runs/43871788563)  
**Точный резерв:** `backup/android-a1-playlist-callback-route-closed-ci-green-20261116` @ `c0cf9896916cca9b13299cdb3fde7a78ffbe4da1`  
**Последний runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`. Runtime hooks после него не менялись.

Read-only статический анализ точного issuer-signed Yandex Music 2025 XAPK, шесть DEX. APK и оригинальное приложение не менялись; сборки, установки и релиза не было. Значения полей, Track/Album IDs, URL/DataSpec, токены, аккаунт и аудиобайты не читались.

## 1. Закрываемый маршрут

Точный метод:

`LXk6.if(LsO7;LXi6$e;Ljava/util/List;)V`

Ранее внутри его тела было доказано:

- `List.size()` вызывается на List-параметре.
- `List.get(I)Ljava/lang/Object;` вызывается на том же List-параметре.
- Результат `List.get` проходит cast к `LOf6;` (MediaItem).
- Тот же объектный результат передаётся в `LsO7.Z(ILOf6;)V`.
- Внутренняя цепочка `List.get → MediaItem → Player holder setter` доказана на уровне метода.

Но это ещё не доказывает, что данный метод вызывается для реального активного Player и что его List содержит MediaItem, построенный из текущего Track.

## 2. Прямые вызовы и MethodHandle

В CI #213 выполнен ограниченный поиск точной ссылки на этот метод во всех шести подписанных DEX:

| Проверка | Результат |
|---|---:|
| Прямые DEX `invoke-*` callsites на `LXk6.if(...)` | 0 |
| MethodHandle, ссылающиеся на точный метод | 0 |
| Call-site items, содержащие такие MethodHandle | 0 |
| `invoke-custom` sites для этих call-sites | 0 |

Следовательно, обычного прямого вызова и ссылки через MethodHandle/`invoke-custom` не найдено.

## 3. Найденный интерфейсный маршрут

`LXk6;` реализует интерфейсный контракт:

`LLl6$c;.if(LsO7;LXi6$e;Ljava/util/List;)V`

У интерфейса найдено шесть concrete implementers:

- `LPk6;`
- `LVk6;`
- `LXk6;`
- `Ldl6;`
- `Leg3;`
- `Lwg3;`

То есть `LXk6;` не является единственной реализацией. Статическое разрешение interface dispatch именно в `LXk6;` отсутствует.

Найден один прямой callsite интерфейсного контракта:

`LKl6;.run()V` → `LLl6$c;.if(...)`

В этом caller доказаны только типизированные источники аргументов:

- `LsO7;` берётся из поля объекта типа `Lek6;`;
- `LXi6$e;` берётся из поля `LKl6;`;
- `Ljava/util/List;` берётся из поля `LKl6;`;
- receiver интерфейса `LLl6$c;` тоже берётся из поля `LKl6;`.

Identity List-поля передаётся в interface call как аргумент. Но кто и каким объектом заполняет это поле, из каких элементов построен List и содержит ли он TrackWrapper/Track-derived MediaItem — не доказано. Поскольку concrete runtime receiver среди шести реализаций не установлен, этот callsite нельзя связать с телом `LXk6.if(...)`.

## 4. Проверка альтернативного Track-bearing Player mutator caller

В существующем ограниченном Player caller census:

- `native_track_related_callers`: 52 строки, результат не усечён;
- `player_setter_or_getter_callsite_count`: 9;
- `track_bearing_player_mutator_callers`: одна строка — `LXk6.if(...)` → `LsO7.Z(ILOf6;)V`.

Но `LXk6.if(...)` принимает Player holder и List, а не Track/TrackWrapper; у самого `LXk6;` не обнаружено Track-, TrackWrapper- или Album-typed instance fields. Поэтому это не Track-bearing caller.

**Точный Track-bearing caller Player mutator в проверенном bounded census не найден.** Не подменять этот отрицательный результат предположением, что List точно не содержит Track-derived items: состав List просто не доказан.

## 5. Решение по маршруту

Маршрут `LXk6.if(...)` закрыт как **непригодный для доказательства связи TrackWrapper → active Player item**:

- прямых вызовов нет;
- MethodHandle/`invoke-custom` ссылок нет;
- interface dispatch неоднозначен между шестью concrete implementers;
- List прослежен только до поля `LKl6;`, а не до его построителя/элементов;
- связи List elements с TrackWrapper/Track нет;
- связь текущего MediaItem с decoder/audio sink остаётся недоказанной.

Это не утверждение, что List гарантированно не содержит Track-derived MediaItem. Это утверждение, что данный маршрут не даёт требуемого доказательства. Повторять его census и расширять глобальную List/Object трассировку не нужно.

## 6. Следующий узкий маршрут

Продолжать не с `LXk6.if(...)`, а с уже доказанной source-side цепочки:

`TrackWrapper → URI → MediaItem → LiLb holder`

Найти только прямые callers точного MediaItem-returning getter/constructor handoff для `LiLb;` и проверить, передаётся ли тот же MediaItem в один из уже известных Player mutators `LsO7/LBs4/LfH7`.

- Если точный caller и same-object handoff находятся — проследить только этот объект до `LfH7.E()LOf6;` current getter.
- Если прямого caller или identity edge нет — закрыть и этот source-side holder маршрут без расширения общего поиска.
- Не искать заново Player ancestry, competitors, все Media3 methods, все List/Object callers или renderer ByteBuffer writers.

## 7. Продуктовые gates и ограничения

- Stage A / NAV17: PASS по подтверждению владельца.
- Stage B: NOT CONNECTED / NO-GO.
- `active_selected_item_proven=false`.
- `same_native_item_to_decoder_proven=false`.
- `same_track_album_edition_generation_owner_proven=false`.
- `codec_output_object_to_audio_sink_proven=false`.

Не менять архитектуру, runtime hooks, vendor behavior, APK или оригинальное приложение. Не добавлять второй Player/decoder/AudioTrack. Не трогать NAV17, Test.50, frozen A1/LSPatch, Windows, browser extension, backend/API/DB или production. Не читать приватные значения, Track/Album IDs, названия, URL/DataSpec, токены, данные аккаунта или audio bytes. Ручная проверка владельца сейчас не требуется.

## 8. CI

- CI #204: SUCCESS, 122/122 — внутренний `List.get → MediaItem → LsO7.Z` handoff.
- CI #205: SUCCESS — точный direct-call census и MethodHandle/`invoke-custom` census.
- CI #213: SUCCESS, 127/127 — interface callback contract, implementer set и caller argument provenance. Все проверки read-only; шесть DEX.
