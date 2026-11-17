Привет! Принимай **CELIKOM Android A1** как ведущий разработчик. Продолжай только с сохранённой точки. Не начинай с нуля и архитектуру не меняй.

**GitHub:** `manufact-test/nomusic`
**Единственная рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
**Последний проверенный read-only static code:** `24c37a59d454cc5ec0b69f9e548fbe3349108673`
**Точный зелёный backup:** `backup/android-a1-exact-source-to-lo96-mediaperiod-ci-green-20261117`
**Последний runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a`. После него hooks/APK не менялись.
**Главный новый CI #3:** SUCCESS, https://github.com/manufact-test/nomusic/actions/runs/44077450137
**Предшествующий playlist/source-holder CI #5:** SUCCESS, https://github.com/manufact-test/nomusic/actions/runs/44076441146
**Предшествующий exact TrackWrapper→Player CI #1:** SUCCESS, https://github.com/manufact-test/nomusic/actions/runs/44070976535

### Прочитай только актуальные документы

1. `docs/android/NEXT-CHAT.md` — **единственный авторитетный текущий статус**.
2. `docs/android/ANDROID-A1-EXACT-SOURCE-MEDIAPERIOD-IDENTITY-20261117.md` — последняя подтверждённая MediaPeriod identity.
3. `docs/android/ANDROID-A1-EXOPLAYER-PLAYLIST-HOLDER-IDENTITY-20261117.md` — Player playlist/internal holder.
4. `docs/android/ANDROID-A1-EXACT-SOURCE-PLAYER-HANDOFF-20261117.md` — начало точной цепочки.

`docs/android/README.md` — индекс. Старые handoff и архивы не читать без точной причины.

### Зафиксированные факты

- **Stage A / NAV17 PASS**, владелец подтвердил нативный вход в Яндекс, интерфейс, альбомы, Мою волну, оригинальную музыку.
- **Stage B NO-GO**: замена звука CELIKOM не подключена и не подтверждена на слух, текущий активный MediaPeriod/decoder не определён.
- Точный подписанный **NAV17 original: Yandex Music 2025.10.4 #120.1gpr**; embedded `assets/lspatch/origin.apk` SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Пинованный XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053` — 16 issuer-signed splits / 6 DEX.
- 2026.10.3 #170gpr — отдельный ARM13 original, 2026.09.5 #167gpr — старая версия с телефона. **Не переносить обфусцированные имена между версиями.**

### ВАЖНО: новый доказанный исходный source→MediaPeriod маршрут

Три независимые read-only signed-CI доказали **статически по точным Java object references**:

`LcA9.extends(...LtCa TrackWrapper...)` → уникальный `LiLb` MediaSource с `LOf6` MediaItem → **тот же LiLb** в `LA14.e(LSl6;J)` → native `ExoPlayer.e` → concrete `ExoPlayer.d.e` → `Collections.singletonList(source)` → `d.T0(List)` → `d.A0(List)` → `List.get` **того же source** → `i$c(LSl6;Z)` → `Lp96(LSl6;Z)` → `LuIb(LSl6)` → **точный field store исходного LSl6** в LuIb.

Новое важнейшее звено: `Lp96.transient(LSl6$b;LrH2;J)Lo96` читает **тот же самый точный DEX-field reference** LuIb, а не поле похожего типа; записывает исходный source на один `Lo96` MediaPeriod объект, и **оба возврата** (2/2) возвращают **именно его**. Это `static_same_source_to_returned_MediaPeriod_proven=true` по CI #44077450137. CFG branch-sensitive, один Lo96 allocation/constructor, exact field identity.

**Не преувеличивать:** это *не* доказательство, что именно этот Lo96 MediaPeriod уже играет в текущем ExoPlayer. Он может быть queued/prefetch. Текущий Track+album+edition+duration+generation, активный period→decoder и фактическая подмена **не доказаны**.

### Следующий этап

**Не начинать ещё одну массовую трассировку.** Ищи только точную связь **runtime current selected Player/item/generation → active Lo96 MediaPeriod → native decoder** на уже доказанной цепочке. Только после подтверждения текущего звучащего источника имеет смысл независимый CELIKOM approved/entitled exact grant и подмена в оригинальном нативном плеере с исходным fallback. Не принимать `open/read`, factory или сам `MediaPeriod` constructor за active audio proof.

Закрыты: `LfT2` (final data-only, не continuation), `LXk6`, direct `LiLb.for()` getter caller census, старые generic List/ByteBuffer/Player сканы. Восстановленные `RAa.invokeSuspend` и Media3 факты — в `docs/android/ANDROID-A1-YANDEX-MEDIA3-RESEARCH-RECOVERED-20261116.md`; не повторять.

**Ограничения:** Android A1 only. NAV17, Test.50, Windows, extension, backend, production и оригинальный Яндекс не трогать. Не менять runtime hooks/APK без обоснованного следующего runtime witness; не добавлять второй Player/decoder/AudioTrack. Не читать и не экспортировать приватные значения Track/Album, IDs, URLs, DataSpec, токены, аккаунт, аудиобайты. Работай большими блоками, сохраняй резервы. Stage B только после реальной проверки владельцем.
