> **АРХИВ. НЕ ИСПОЛЬЗОВАТЬ КАК СТАРТОВОЕ СООБЩЕНИЕ.** Этот handoff от 16.11.2026 полностью superseded документом [NEXT-CHAT-START-MESSAGE-20261118.md](NEXT-CHAT-START-MESSAGE-20261118.md) и каноническим [NEXT-CHAT.md](NEXT-CHAT.md). Оставлен только для исторического аудита.

Привет! Принимай **CELIKOM Android A1** как ведущий разработчик. Продолжай **строго с сохранённой точки**. Архитектуру и нативный плеер не менять. Не переключайся на Windows или расширение.

**GitHub:** `manufact-test/nomusic`
**Единственная рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
**Последний CI-green read-only код:** `762088f55114553bacb96b324530ee241ce72dcd`
**Точный backup:** `backup/android-a1-exoplayer-engine-period-holder-ci-green-20261117`
**Перед последним заходом:** `backup/android-a1-pre-period-activation-last-pass-20261117` @ `a07c5dbb174f714e9d750d7ebff8fc54e60221fe`
**Последний runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a` — после него hooks/APK НЕ менялись.
**Главные последние CI:** [native period holder #3 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44093915839); [native Exo engine #2 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44094591928).

### Сначала прочитай — строго по порядку

1. `docs/android/NEXT-CHAT.md` — **единственный текущий канонический статус**.
2. `docs/android/ANDROID-A1-EXOPLAYER-ENGINE-PERIOD-HOLDER-20261117.md` — **последний точный результат**, вызовы Exo engine и нативный holder.
3. `docs/android/ANDROID-A1-EXACT-SOURCE-MEDIAPERIOD-IDENTITY-20261117.md` — доказанная цепь исходного source → Lo96 MediaPeriod.
4. `docs/android/ANDROID-A1-EXOPLAYER-PLAYLIST-HOLDER-IDENTITY-20261117.md` — исходный source сохраняется в Player/плейлисте.

`docs/android/README.md` — индекс. Старые handoff/архивы не подменяют текущий статус.

### Оригинал и статус

- **Stage A / NAV17 PASS** по подтверждению владельца: Яндекс внутри APK, вход, UI/альбомы/Моя волна и оригинальный звук работают.
- **Stage B NO-GO:** CELIKOM audio replacement ещё **НЕ подключён**, не слышен и не доказан на активном декодере. APK для проверки Stage B не собирать без нового обоснованного runtime evidence.
- В NAV17 установлен подписанный **Yandex Music 2025.10.4 #120.1gpr**. `assets/lspatch/origin.apk` SHA `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`; исходный подписанный XAPK SHA `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 16 splits / 6 DEX. **2026.10.3 #170gpr** — отдельный ARM13 original, **2026.09.5 #167gpr** — старая версия телефона; их классы НЕ смешивать.

### Что реально доказано (точные signed-DEX Java object identities)

`LcA9(...LtCa TrackWrapper...) → LiLb(MediaSource) → LA14.e(LSl6;J) → native ExoPlayer.d.e → singletonList(source) → d.T0 → d.A0 → i$c → Lp96 → LuIb → Lo96 MediaPeriod`.

Уже проверено, что это **тот же source-object**, а не совпадение типов. `LuIb` хранит source в точно проверенном поле; `Lp96.transient` берёт **тот же** source и помещает в уникальный `Lo96`, возвращаемый в 2/2 ветках. CI #44077450137 SUCCESS.

**Последний большой заход:**
- `Lxh6.<init>(...ExoPlayer/i...)` получает `Lp96` из точно подтверждённого `i$c`, вызывает `Lp96.transient` (PC 96), использует тот же `Lo96` как ключ `IdentityHashMap` (PC 102) и передаёт тот же период в `Lup1.<init>(Lwh6;ZJJ)` (PC 132). `Lup1` сохраняет параметр периода на `this`. CI #44093915839 SUCCESS.
- **Единственный прямой вызов** указанного конструктора `Lxh6` находится в `Landroidx/media3/exoplayer/e.break()V` (PC 275), внутри которого `Lxh6` создаётся на PC 240. Код обращается к `Landroidx/media3/exoplayer/h` и полям типа `Lxh6` (очередь периодов). CI #44094591928 SUCCESS.
- Это **доказанная статическая цепь source → period → native engine holder**, но **не** текущий звучащий период. Обфусцированное `break` — только имя метода, не основание считать его текущим playback event.

### Следующий конкретный блок

От **точной** пары `Lxh6/Lup1/Lo96` в `ExoPlayer/e` + `ExoPlayer/h` выяснить, **какой holder сейчас выбран и читает звук**, а какой лишь загружается/стоит в очереди/предзагружается. Нужны гарантированные **same-object active Player/queue generation → Lo96 → decoder**, плюс selected Track/album/edition/duration на том же owner. До этого **не подключать CELIKOM bytes и не объявлять Stage B успешным**. Если понадобится runtime-observer, сначала вывести узкую безопасную точку, создать backup, доказать отсутствие вмешательства в нативный плеер; нельзя ставить хуки «наугад».

**Запрещено переоткрывать** `LfT2` (data-only), `LXk6`, прямой `LiLb.for()` getter, старые global `List/Object/MediaItem/ByteBuffer/Player/renderer` сканы, Exo factory/open/read и уже закрытые constructor/holder/period routes. Не читать/экспортировать IDs, Track/Album названия, URL/DataSpec, private field values, токены и аудио. Ни второго Player/decoder/AudioTrack, ни правок оригинального Яндекса, NAV17, Test.50, Windows, extension, backend/production.

Работай большими блоками, **без промежуточных отчётов**, сохраняй зелёные бэкапы, обновляй канонический `NEXT-CHAT.md` после нового результата. Stage B менять на PASS только после фактического ручного прослушивания владельцем.
