# CELIKOM Android A1 — точный источник 2025, Stage B (14.11.2026)

## Факт: проверен оригинальный установленный владельцем NAV17
`CELIKOM-A1-NAV17-PassportProviderFix-20261114.apk`, SHA256 `8d7c1570367360c12ba11f3972fa72477aca4dcc33f30dce78b381aee939b20d`.
Внутренний `assets/lspatch/origin.apk`, SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` — точно тот зафиксированный исходный Яндекс 2025.10.4. Ни один APK не изменён в ходе аудита.

## Точный статический DEX-аудит, НЕ воспроизведение
- Есть два прямых наследника `android.media.MediaDataSource`: первый читает данные из `ByteBuffer`, второй через собственный `DataInputStream`. Единственный прямой вызов `MediaExtractor.setDataSource(MediaDataSource)` конструирует первый источник с `ByteBuffer`. Нельзя приравнивать этот путь к нативному воспроизведению музыки.
- Приложение содержит AndroidX Media3 / ExoPlayer, включая Yandex `CrossfadingExoPlayerImpl`; присутствует идентификатор Media3 1.6.1. Прежний DEX-аудит не находил **необфусцированные** имена публичных DataSource API, что НЕ означает отсутствие Media3.
- Retrofit `get-file-info`: `com.yandex.music.shared.player.content.remote.fileinfo.FileInfoApi`, аргументы `trackId, codecs, transports, quality, ts, sign, measuredNetworkSpeedKbps, estimatedNetworkSpeedKbps, network, device`. Ответ: `GetFileInfoDto.downloadInfo` с `FileInfoDto` (URL/urls, key, codec, quality, transport, bitrate, gain).
- Retrofit `tracks/{trackId}/download-info`: `DownloadInfoApi`, параметры `trackId, direct, preview, formatFlags`, ответ `DownloadInfoDto` (link, codec, container, bitrate, gain).
- Важно: `get-file-info` **не содержит albumId или editionId**. Нельзя брать только trackId оттуда и подменять: текущие album + edition + duration должны быть подтверждены отдельно из **именно выбранного нативного элемента очереди** до prepare. Поле `key` и транспорт тоже запрещают слепо менять URL на MP3.

## Реальное изменение в экспериментальной ветке
На клоне в MAIN добавлены два узких read-only observer точных DTO getter-методов из подписанного 2025 DEX: `GetFileInfoDto.if()` и `DownloadInfoDto.case()`. Они не читают и не сохраняют сами ответы или ссылки. На ручном экспорте TXT выдаются только конечные категории `FILEINFO_DTO` / `DOWNLOADINFO_DTO`, а также сводка фактических `readAt` и `MediaExtractor`, без логирования горячего аудиопотока на диск. Пока эти счётчики не проверены на владельце: наличие вызова getter не равно факту аудио в декодере.

## Далее, с запретом на ложные подмены
1. Подтвердить путь, реально задействованный при музыке владельца; отдельно доказать связь конкретного source object с текущей песней, а не фоновым prefetch.
2. Получить достоверную связку `trackId + albumId + editionId + durationMs + generation` из текущего нативного player item и проверить тот же идентификатор до декодера.
3. Подключить **отдельную авторизованную сессию CELIKOM**, approved/entitled, точную версию, подписанный URL, срок, MIME/Range/HEAD. Не использовать токены Яндекса как токены CELIKOM. У экспериментального PHP поля album/edition могут быть NULL и ещё не развёрнуты в production.
4. Менять источник только при всех доказательствах, в том же плеере; неправильная версия, невозможность декодирования, stale Next/MyWave или любая ошибка → ORIGINAL. Не трогать NAV17, Яндекс Passport, Windows/main и Test.50.
5. Только после реальной подмены + CI ARM13 выдавать новый подписанный APK владельцу. До реальной проверки замены никаких заявлений о готовности.

**Статус:** появился исполняемый диагностический слой Stage B, но аудиоподмена ещё НЕ ПОДКЛЮЧЕНА.


## 14 Nov — точный downstream Exo source path (новая работа)

После проверки оригинального подписанного `classes4.dex` установлена последовательность классов (СТАТИЧЕСКАЯ, НЕ доказательство реального воспроизведения):
- `GetFileInfoDto` → `FileInfoDto` преобразуется через obfuscated mapping в внутреннюю file-info model.
- `com.yandex.music.shared.player.download2/o` делает собственный media download descriptor с `android.net.Uri` + альтернативами, сроками и форматом.
- `com.yandex.music.shared.player.download2.exo.c.for` использует этот descriptor при создании Exo `RetryingBalancingDataSource` factory; `RetryingBalancingDataSource` имеет точные методы `if(DataSpec)` (open) и `read(byte[],int,int)`. Это точный собственный Exo HTTP audio-source путь оригинала; он может обслуживать **prefetch/offline**, поэтому факт вызова сам по себе всё ещё не доказывает именно текущий трек и звук.
- Добавлены clone-MAIN-only read-only hooks на точно установленные factory/open/read с оригинальным `chain.proceed()` ОДИН раз, неизменёнными аргументами/результатом и исходными исключениями. Диагностика экспорта TXT показывает только ограниченные категории: `EXO_FACTORY_CREATED`, `EXO_OPEN_OK`, `EXO_READ_POSITIVE`, `EXO_SOURCE_END`, `EXO_IO_FAILURE`; **никаких** URL, MIME headers, треков, байтов или source objects. Горячий `read` не пишет в TXT/logcat; только сбрасывает анонимные насыщаемые счётчики в памяти.

**Сейчас это лишь подтверждённая статически точная граница и динамический read-only witness.** До подмены всё ещё нужно найти достоверный native selected-track album+edition+duration и увязать ровно тот Exo source instance с текущим decoder, отдельной CELIKOM-сессией и проверенным правом/версией. Не подменять `QAa` или `DataSpec` на основании одного `trackId`.

## 14 Nov — existing CELIKOM session transport and owner Test.50 scope

Read the *existing* Android CELIKOM client instead of reimplementing its server or reusing the old audio engine:
- `android/native-companion/addon/src/pro/celikom/nativeprobe/identitydiag/NativeApi.java` already implements **independent CELIKOM** login, refresh-token rotation, `GET /api/v1/config`, and authenticated `GET /api/v1/resolve?audio_formats=mp3,m4a&service=yandex&track_id=<id>`. It guards account generation, foreground resolve lane, redirects, request size, timeouts and cancellations. `SecureSession.java` stores the independent CELIKOM session using Android Keystore. **Copy/adapt this authentication/HTTP logic into the native clone only after an authorized CELIKOM login path is wired. Never mix Yandex Passport tokens or reuse another Android package's session.**
- The older Test.50 `ReplacementEngine.java` uses **its own `MediaPlayer` and foreground-service mixing**. This MUST NOT be transplanted into A1. The one-native-player architecture forbids a second decoder/clock; the Exo source factory hook is the intended in-process integration surface.
- Existing `server/src/Application/ResolveService.php` only returns approved/entitled exact album/edition when those server-side rows are attested; currently experimental nullable `album_id` and `edition_id` fields may be NULL and are **not production deployed**. The old Test.50 `ApiContract.audio` validates signed HTTPS source but does NOT attest album+edition. Stage B must reuse the stricter B42/NativeTrackIdentityGate triple and actual native owner-source-object continuity, not simply port Test.50 track-only resolution.
- Original pinned DEX has a track-id-only wrapper `LtCa` with one String. At least one constructor call (from `LGp0.new`) derives this wrapper from native `ru.yandex.music.data.audio.o` track model; another path appends `_sm` for smart preview. The resulting Exo descriptor may therefore represent **different playback/prefetch variants**, and the `LtCa` string alone cannot certify album+edition. The pinned model `ru.yandex.music.data.audio.o` has an `Album` field and duration-like fields, but no live player->source attestation yet. Do not guess field meaning or derive an edition from filename/title.

**Active next code block:** correlate the actually selected native player item (track ID + explicit album/edition + duration + queue generation) to the exact source object supplied to `com.yandex.music.shared.player.download2.exo.c.for`, then join authenticated CELIKOM resolve/HEAD/Range before source construction. If either identity or session is unknown, return the original Exo factory result unchanged. No new owner APK until this works and both ARM13 gates are green.

## 14 Nov — exact native descriptor object continuity (read-only, clone MAIN)

Static signed-2025 DEX confirms `com.yandex.music.shared.player.download2.o.while(LQBa,Lf6a,Ln26):LQAa` constructs the native Exo source descriptor. The pinned `com.yandex.music.shared.player.download2.exo.c.for(LdA9,LQAa,Lmu3,LgA9):LOr2$a` receives such a descriptor, but whether it is for **the audible current song rather than prefetch** remains unproven.

The current scoped hook adds: (a) exact read-only returned-object witness at `download2/o.while`; (b) **same Java reference identity** (`==`, never vendor `hashCode/equals/toString`) against the descriptor passed into Exo factory; (c) a maximum of 16 weak references, no persistent references to account/track/URL/media; (d) bounded `EXO_DESCRIPTOR_BUILT` and `EXO_SAME_DESCRIPTOR` categories exported only on explicit diagnostic save; and (e) a registered/NO_HOOK status in the CI parser. One unchanged original call per intercepted method; NO audio swapping, no rights bypass and no downloader/publisher mutation.

This proves object continuity **only if runtime counters become nonzero**, never by static code or CI startup-only checks. Next blocker still current queue track+album+edition+duration and authorized CELIKOM grant on that exact descriptor before decoder. No owner APK yet.

## 14 Nov — Exo factory → source INSTANCE → open/read native witness

Exact signed-2025 source instance factory `com.yandex.music.shared.player.download2.exo.RetryingBalancingDataSource$b.for():LCC2;` constructs a `RetryingBalancingDataSource`. A new clone-only read-only hook observes this one factory result without altering the object. `StageBAudioEvidence` keeps at most 16 **weak Java object references** and correlates the exact same instance (`==`) to actual `RetryingBalancingDataSource.if(LUC2;)` (open) and positive `read(byte[],int,int)` calls, with a maximum of **16 initial nonzero reads** checked; no object scans on every later byte read and no media bytes captured. Export categories: `EXO_SOURCE_INSTANCE`, `EXO_INSTANCE_OPENED`, `EXO_INSTANCE_READ`. The hook registration marker is `AUDIO_EXO_SOURCE_INSTANCE_HOOK` and the CI parser explicitly distinguishes REGISTERED/NO_HOOK/NOT_SEEN. Original caller and exceptions always forwarded unchanged.

**Boundary of proof:** when owner-authenticated playback yields these counters, they establish actual factory→open/read source **instance continuity**, not yet current selected track/album/edition or decoder audio, and not proof of a CELIKOM replacement. Uncertain identity/entitlement always ORIGINAL. Owner NAV17 baseline remains untouched. 

## 14 Nov — fixed real compile gap in Java Stage B admission/lifecycle models

The original `NativePrePrepareAdmission` and `NativeReplacementLifecycle` still used old two-field track+edition APIs while `NativeTrackIdentityGate` / `NativeSourceGate` demanded exact **track+album+edition**. This was a compile-time blocker hidden by separate tests. These two models now carry the **three-field identity** across begin, FileInfo and decoder pre-prepare; their existing tests were upgraded and new wrong/absent album negative cases enforce ORIGINAL. ARM13 paired + standalone workflows now compile all five relevant pure-Java classes via `javac --release 17` and run both model stress suites before touching publisher resources, avoiding falsely interpreting uncompiled model PASS as native replacement. Still MODEL-ONLY, no swap, no live Yandex playback.
