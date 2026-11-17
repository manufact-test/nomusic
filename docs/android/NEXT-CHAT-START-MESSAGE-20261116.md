Привет! Принимай **CELIKOM Android A1** как ведущий разработчик. Продолжай только с сохранённой точки, архитектуру не менять.

**GitHub:** `manufact-test/nomusic`
**Рабочая ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
**Последний зелёный статический код:** `433191c0b6e5f2a2eabef8589aa01c02f326e3b1` (direct MediaSource audit, 17 Nov). Прежний LfT2 checkpoint `e6bf9b6933d17d503b4f3b1d4f7d460df4b52f6a` не изменён.
**Backup:** `backup/android-a1-direct-mediasource-contract-ci-green-20261117`.
**Pre-audit backup:** `backup/android-a1-pre-direct-mediasource-contract-audit-20261117` @ `a142f5fe48f92d68727f4c9873a4a6cfda56b156`.
**Pre-documentation backup:** `backup/android-a1-before-yandex-media3-research-handoff-20261116` @ `a324963b84876a88513bc1d208a42519489c397f`
**Последний runtime-hook change:** `a655712d210189f3bc611847235de3ed4d985c1a` — hooks не менялись.
**CI #12 (LfT2):** SUCCESS, https://github.com/manufact-test/nomusic/actions/runs/43909098407
**CI #2 (direct MediaSource):** SUCCESS, https://github.com/manufact-test/nomusic/actions/runs/44049682525 — 3/3 tests, точный signed 2025 XAPK.

### Прочитай только три документа
1. `docs/android/NEXT-CHAT.md` — единственный текущий статус.
2. `docs/android/ANDROID-A1-LFT2-EXACT-CLASS-CLOSURE-20261116.md` — закрытый маршрут LfT2.
3. `docs/android/ANDROID-A1-YANDEX-MEDIA3-RESEARCH-RECOVERED-20261116.md` — восстановленные RAa/Media3 факты и новый ограниченный MediaSource отрицательный результат.

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

### Следующий блок
Не начинай новую глобальную трассировку. По уже проверенной 2025 NAV17 базе ищи только **новое узкое, доказуемое** selected-Track → ACTIVE (не prefetch) native source/decoder same-object ребро. Предыдущие Exo factory→open/read witnesses доказывают продолжение source instance, **но не selected track identity**. Любой кандидат — сначала точная class/method identity; только потом bounded trace. Учитывать возможности MediaSource API, но НЕ считать его необфусцированное имя присутствующим в signed Yandex. Не запускать очередной глобальный поиск. Кандидат должен появиться из точного подтверждённого source-side или selected Player owner маршрута.

Ограничения: Android A1 only, без изменений APK, оригинального Яндекса, архитектуры и runtime hooks. Второй Player/decoder/AudioTrack запрещён. Не читать/экспортировать Track IDs, названия, URL, DataSpec, токены, account data, private fields, audio bytes. NAV17/Test.50/frozen branches/Windows/extension/backend/API/DB/production не трогать. Никаких больших CI-логов. Работать крупными блоками, сохранять backup, Stage B остаётся NO-GO до реального доказательства и ручной проверки.
