Привет! Ты принимаешь **CELIKOM Android A1** как ведущий разработчик. Продолжай существующую работу, ничего не начинай с нуля и не меняй согласованную архитектуру.

**GitHub:** `manufact-test/nomusic`

**Единственная рабочая ветка:**  
`experiment/android-a1-metrica-init-state-observer-arm13-20261112`

**Последний CI-green кодовый checkpoint:**  
`a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`

**Точный резерв кода:**  
`backup/android-a1-audio-buffer-identity-ci-green-20261115`  
@ `a9dfbbbcf959da3d5cf265c13a17e8baffcc2c50`

**Резерв финальной передачи с документацией:**  
`backup/android-a1-stage-b-audio-sink-audit-final-handoff-20261115` (указывает на актуальный handoff HEAD).

**Резерв до исправления wide invoke mapping:**  
`backup/android-a1-wide-invoke-map-pre-final-audit-fix-20261115`  
@ `8e121e50712c2f65f0b703e7beeb91688727b764`

**Последнее изменение runtime hooks:** `a655712d210189f3bc611847235de3ed4d985c1a`. В последнем проходе runtime hooks не менялись.

### Обязательно прочитай полностью

1. `docs/android/NEXT-CHAT.md`
2. `docs/android/NEXT-CHAT-ANDROID-A1-TRACK-EXO-CONTINUITY-20261115.md`
3. `docs/android/ANDROID-A1-TRACK-EXO-IDENTITY-HARDENING-20261115.md`
4. `docs/android/ANDROID-A1-TRACK-ALBUM-IDENTITY-20261115.md`
5. `docs/android/ANDROID-A1-SOURCE-OPEN-READ-CLOSE-IDENTITY-20261115.md`
6. `docs/android/ANDROID-A1-NAV17-OWNER-REAL-MUSIC-GREEN-STAGE-B-SOURCE-ADAPTER-20261114.md`

### Текущее состояние — не перепутай этапы

**Stage A пройден на NAV17.** Владелец подтвердил: CELIKOM открывает его настоящий аккаунт Яндекс Музыки, показывает альбомы и Мою волну, играет оригинальные треки. Это owner-reported playback; диагностический TXT сам по себе не верифицирует аудиовыход. Это реальный успех, его нельзя ломать или откатывать.

**Stage B продолжается.** Оригиналы играют, но CELIKOM-версии ещё не подключены и не звучат. Ни одного release APK из этой исследовательской ветки не делаем.

Последний signed-DEX audit [#43712507031](https://github.com/manufact-test/nomusic/actions/runs/43712507031) — SUCCESS, 40/40 тестов. Найден конкретный native audio sink candidate:

- `LbJ2` implements `Lpk0`, имеет типизированные поля `AudioTrack` и `ByteBuffer`.
- `LcLb.O(..., ByteBuffer, ...)` и `Lbd6.O(..., ByteBuffer, ...)` передают тот же ByteBuffer-параметр в `LbJ2.native(ByteBuffer, long, int)`. Для обеих функций параметр находится в v6 и не перезаписывается; wide `long` правильно учитывается как два DEX-регистра.
- `LEF2.j()` вызывает интерфейсный `Lpk0.native(...)`, передавая ByteBuffer, прочитанный из типизированного поля. Реальный runtime dispatch на `LbJ2` не доказан.

Это доказывает статическую передачу ByteBuffer в конкретный аудиовыход, **но не** связь с текущим выбранным Track, Album, edition/generation или тем же item на decoder input. В отчёте остаются `active_selected_item_proven=false` и `same_native_item_to_decoder_proven=false`.

### Следующий большой блок работы

1. Проследи, кто вызывает `LcLb.O` и `Lbd6.O`; отдели текущий playback от очереди, prefetch и download. Не выдавай прямую ссылку на метод за runtime dispatch.
2. Найди конкретного владельца текущего выбранного Track и свяжи его с уже найденным аудиовыходом только через bounded Java object identity.
3. Доказательно установи Album и edition/generation для того же Track. Не считай числовые поля или коллекции семантическим доказательством.
4. Проследи ту же identity до decoder/audio renderer. Только после этого подключай существующий CELIKOM resolve/entitlement contract до decoder input с оригинальным fallback.
5. Работай read-only и fail-closed. Если безопасная цепочка не доказана — не добавляй generic hooks и не придумывай связку.

### Жёсткие ограничения

- Не менять NAV17 working auth, исходный Яндекс и его данные/аккаунт.
- Не менять Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend/API/DB и production.
- Не добавлять второй плеер, MediaPlayer, отдельный decoder/AudioTrack, WebView или смешивание звука.
- Не читать/экспортировать значения приватных Track/Album полей, названия и ID, URL, DataSpec, токены, данные аккаунта или аудиобайты.
- Не подавлять vendor exceptions и не менять поведение vendor methods: каждый оригинальный метод должен выполняться ровно один раз.
- Не просить владельца повторять логин, вводить OTP, устанавливать APK или делать ручную диагностику, пока не определён конкретный необходимый read-only замер.
- Работай крупными самостоятельными блоками, сохраняй точные резервные точки. Не дроби работу на мелкие инструкции и не присылай промежуточные отчёты без необходимости.

**Продолжай самостоятельно.**
