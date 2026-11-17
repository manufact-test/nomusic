Привет! Принимай **CELIKOM Android A1** как ведущий разработчик. Продолжай только с сохранённой точки, архитектуру не менять.

**GitHub:** `manufact-test/nomusic`
**Рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
**Последний зелёный статический код:** `a9408608562b3d70a51f8d01c8be17aa4a73589b` — доказанный exact source→Player same-object CFG, 17 Nov. LfT2 checkpoint `e6bf9b6933d17d503b4f3b1d4f7d460df4b52f6a` и последний hook-change отдельно сохранены.
**Backup:** `backup/android-a1-lca9-wrapper-mediasource-player-identity-ci-green-20261117`.
**Pre-audit backup:** `backup/android-a1-pre-direct-mediasource-contract-audit-20261117` @ `a142f5fe48f92d68727f4c9873a4a6cfda56b156`.
**Pre-documentation backup:** `backup/android-a1-before-yandex-media3-research-handoff-20261116` @ `a324963b84876a88513bc1d208a42519489c397f`
**Последний runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a` — hooks не менялись.
**CI #12 (LfT2):** SUCCESS, https://github.com/manufact-test/nomusic/actions/runs/43909098407
**CI #1 (exact TrackWrapper → LiLb → ExoPlayer):** SUCCESS, https://github.com/manufact-test/nomusic/actions/runs/44070976535 — branch-sensitive 55 path states / 2 branches; 4/4 tests, точный signed 2025 XAPK. Предыдущий named direct MediaSource CI #2 SUCCESS — https://github.com/manufact-test/nomusic/actions/runs/44049682525.

### Прочитай только актуальные документы
1. `docs/android/NEXT-CHAT.md` — единственный текущий статус.
2. `docs/android/ANDROID-A1-EXACT-SOURCE-PLAYER-HANDOFF-20261117.md` — **новый конкретный успешный source→Player маршрут**, CI green.
3. `docs/android/ANDROID-A1-LFT2-EXACT-CLASS-CLOSURE-20261116.md` — закрытый маршрут LfT2.
4. `docs/android/ANDROID-A1-YANDEX-MEDIA3-RESEARCH-RECOVERED-20261116.md` — RAa/Media3 справка. Не читать архивы.

`docs/android/README.md` — индекс. Старые handoff и архивы не читай при старте.

### Что доказано
- Наш **проверенный владельцем NAV17 CELIKOM APK** (SHA `8d7c1570367360c12ba11f3972fa72477aca4dcc33f30dce78b381aee939b20d`) содержит `assets/lspatch/origin.apk` SHA `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` = подписанный Yandex **2025.10.4 #120.1gpr**. Это подтверждение фактического NAV17 original, а не выбор будущего production target.
- Подлинный XAPK SHA `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 16 подписанных splits / 6 DEX; base SHA совпадает с NAV17 origin.
- **2026.10.3 #170gpr** — отдельный подтверждённый ARM13 original control/structural clone research. **2026.09.5 #167gpr** — старая версия с телефона; не путать с NAV17 binary.
- Цепочка `LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>` сохраняет тот же TrackWrapper.
- **LfT2 закрыт:** CI #12 доказывает, что это final class extends Object, поля `LdA9;/LtCa;/LgA9;`, только constructor/equals/hashCode/toString, **нет invokeSuspend и другого continuation**. Все непосредственные чтения `LtCa;` ведут только в equals/hashCode/toString, не в source/Player. Не повторять LfT2.
- `LiLb`, `LXk6` и отдельный ByteBuffer sink census ранее закрыты.
- Stage A/NAV17 **PASS** (родная музыка Яндекса играет), Stage B **NO-GO** (CELIKOM replacement audio не связан с активным decoder).

### Что ещё нашли в сохранённом исследовании Яндекса (важно)

**Не потеряй эту зацепку:** `docs/android/ANDROID-A1-YANDEX-MEDIA3-RESEARCH-RECOVERED-20261116.md`. Это индекс предыдущих исследований и официальной справки Android, а не новое исследование.

- Официальный Media3/ExoPlayer предоставляет **прямые** `setMediaSource/addMediaSource/setMediaSources` с объектом `MediaSource`. Искать исключительно через `MediaItem` — неправильно; конкретный путь официального Яндекса этим **не доказан**.
- В подписанной версии Яндекса 2025.10.4 существует **реальный** `RAa.invokeSuspend`: CI #43696198020 SUCCESS подтвердил повторный вызов `download2.o.for` с **тем же объектом continuation** и с явно `null` аргументом TrackWrapper. В раннем исследовании были уже реализованы read-only weak-reference checks восстановления identity через этот же RAa. Это не `LfT2`, который закрыт. Повторять старое исследование RAa/Fp0 без нового факта не нужно.
- В цепочке `download2.o.while → exo.c.for → RetryingBalancingDataSource → open/read/close` уже существуют статическая проверка и read-only lifecycle свидетели. Они **не** отличают реально выбранный звучащий трек от prefetch/offline; Stage B остаётся NO-GO.
- Справка Яндекса про VPN/сеть объясняет потенциальные остановки звука, но **не** раскрывает внутреннюю архитектуру приложения. Сторонние клиенты YaMuLite/yt-dlp не переносить как доказательство.
- **Новая точная проверка 17.11:** 11 известных Player owners на подписанном NAV17 Yandex 2025 XAPK; в шести DEX **0** методов Player с точным необфусцированным типом MediaSource в параметрах, **0** их прямых callsite, точный class MediaSource не определён. Это закрывает ТОЛЬКО named/direct API гипотезу, но **не** обфусцированные/косвенные MediaSource/Player маршруты. Не возобновлять mass scan.
- Изменения 17.11 только в **новом статическом Python-аудите, его 3 unit tests, CI и документах**; никаких runtime-hook/APK/оригинального Яндекса.

### Новый доказанный результат 17 ноября
Не возвращайся к старому поиску: signed CI #44070976535 доказал **один и тот же** `LiLb` MediaSource instance от конструктора до реального native Player source setter:
- `LcA9.extends(...LtCa...)` получает TrackWrapper и передаёт тот же Java-объект в `Lbq0.this` (PC 14).
- Уникальный `LiLb` создан и получает `LOf6` MediaItem в конструктор (PC 97).
- **Этот же LiLb**, не просто такой же тип, передаётся в `LA14.e(LSl6;J)` (PC 112), затем `LA14.e` перенаправляет тот же source объект в `ExoPlayer.e`.
- Статическая цепь MediaSource: `LiLb → LWT1 → LdC0 implements LSl6`. Параллельно `LiLb$a.invokeSuspend` присоединяет `LIr8` child MediaSource через `LWT1.strictfp`, что тоже доказано отдельным CI.
- Всё это **static exact same-object source→Player proof**, но **не** current audible playback: нет отдельного подтверждения активного Player receiver/item, album/edition/duration/generation, MediaPeriod/decoder и звука CELIKOM. Stage B **NO-GO**.

### Следующий блок
Продолжай ТОЛЬКО с конкретной проверенной `LcA9.extends → LA14.e → ExoPlayer.e` цепочки. Найди строгий same-object мост к current selected Player и активному MediaPeriod/decoder, отличая очередь/prefetch, с track+album+edition+duration+generation. Не повторяй `LiLb` constructor/getter census, LfT2, LXk6, широкий List/ByteBuffer/Player scan, RAa/Media3 базовые исследования и новый exact source CFG — всё это уже закрыто/зафиксировано. Не менять runtime hooks или APK без оправданного отдельного runtime measurement и разрешения на QA.

Ограничения: Android A1 only, без изменений APK, оригинального Яндекса, архитектуры и runtime hooks. Второй Player/decoder/AudioTrack запрещён. Не читать/экспортировать Track IDs, названия, URL, DataSpec, токены, account data, private fields, audio bytes. NAV17/Test.50/frozen branches/Windows/extension/backend/API/DB/production не трогать. Никаких больших CI-логов. Работать крупными блоками, сохранять backup, Stage B остаётся NO-GO до реального доказательства и ручной проверки.
