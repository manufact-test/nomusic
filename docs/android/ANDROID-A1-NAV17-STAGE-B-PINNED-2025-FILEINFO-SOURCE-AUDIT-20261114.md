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
