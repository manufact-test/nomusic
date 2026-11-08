# CELIKOM Android Test.65 — 08.11.2026

## Симптом и причина
В присланной HONOR 50 диагностике `CELIKOM-combined-20261108-161941.txt` (3 запусках Test.61, Test.62, Test.64) Test.64 показал каталог 133 одобренных песен, однако у «Малая, пой», «Пряный ром», «ИСКАЛА» публичный endpoint альбомов Яндекс.Музыки вернул HTTP 451, а актуального уникального Track ID не нашлось. Движок переходил от `waiting_for_album_response` к `no_unique_candidate`, но `AppPresentation` всегда показывал «Определяем песню», пока `identified=false`. Старый текст шторки игнорировал исход определения.

## Изолированная правка
Ветка: `feature/android-0385-test65-identification-status-recovery-20261108`, validated source commit `28c4b96e373fb838afa62e4b546d38e0e34668de`. В `ReplacementEngine` сохранена причина определения; `PlaybackUi` передаёт terminal/pending c проверкой текущего source key, учитывает уже кешированную 451; `AppPresentation` и `NotificationState` различают «Определяем», «Яндекс ограничил данные альбома», «не удалось однозначно определить» и отдельно **после действительного серверного `resolve found=false`** — «Для этой песни нет замены». В шторке показывается заголовок из текущей Media3 песни даже без Track ID, но кнопка «Предложить песню» не предлагается без надёжно определённого ID. При смене песни причина определения сбрасывается.

Это не делает 451 доказательством отсутствия версии CELIKOM; не даёт информации «на модерации» без серверного обращения по конкретному Track ID. Способы обхода ограничения Яндекса не добавлялись. Аудиодвижок, seek, pause, buffer, prefetch, авторизация, серверная API, стабильный Android, Test.50, OTA и desktop не менялись.

## Проверено
- Host CI & D8: PASS, [workflow run 42485946874](https://github.com/manufact-test/nomusic/actions/runs/42485946874); `TestIdentificationStatus`: 16/16 PASS на pending, 451, unidentified, ambiguity, паузу, found=false, playing, disconnect.
- Подписанная APK: `CELIKOM-Android-0.3.85-TEST-65-IDENTITY-STATUS-SIGNED.apk`, package `pro.celikom.nativeprobe.test`, version `0.3.85-test.65`, code 86151.
- SHA-256: `b44fe798bd755fb6938bb3ac3443ed1557958b048fd1f38d22369653fb32ef93`; original certificate matched, Android v3 signature verified; stable publication disabled.
- Library: `/CELIKOM/Android/Test` ([APK](https://chatgpt.com/library?file_id=libfile_38daafa7c59c8191a681925774d7590f&account_id=personal)), verification JSON and immutable build receipt in same folder.
- GitHub artifact: [#13619641701](https://github.com/manufact-test/nomusic/actions/runs/42485946874/artifacts/13619641701).

## Следующая проверка на телефоне
На HONOR проверить три ранее зависших песни («Малая, пой», «Пряный ром», «ИСКАЛА»): шторка должна завершать определение и не утверждать, что версии точно нет. Отдельно проверить известную отсутствующую песню (сервер `found=false`), имеющуюся песню и заголовок шторки, переход к следующему треку и тест RASKOL/Dym. Данные на модерации без ID не доказаны. Ни RASKOL-управление, ни Dym-BUFFERING, ни общее акустическое качество не объявлять исправленными до нового устройства.
