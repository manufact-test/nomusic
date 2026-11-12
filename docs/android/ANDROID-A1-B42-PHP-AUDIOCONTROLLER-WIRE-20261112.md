# CELIKOM Android A1 — B42 PHP AudioController ↔ source contract, 12 ноября 2026

**Статус: проверена реальная совместимость транспортного кода, но native host недоступен. Stage A NO-GO; Stage B LOCKED.**

## Выполнено

- Независимая ветка: `experiment/android-a1-b42-audio-controller-wire-20261112`. Ни одна принятая ветка не перезаписана.
- Создан собственный PHP test fixture `android/native-audio-contract/actual-audio-controller-fixture.php`. Он исполняет **реальные, неизменённые** `server/src/Http/AudioController.php`, `Http/Response.php`, `Http/ByteRange.php`, `Application/AudioTokenService.php` на синтетических байтах в памяти. Нет production DB, хранения, пользовательских файлов, сетевых запросов или реального Яндекса.
- `android/native-audio-contract/actual-audio-controller-compat.test.mjs` проверяет точные HTTP headers и реальные SHA256 тела для HEAD 200, GET 200, GET 206 с `If-Range`, GET open-ended 206, EOF clipping, 416, ETag mismatch → 200 и 403 для неверного HMAC / неподтверждённой сессии. Подлинный серверный код вызывается PHP CLI из Node tests.
- Реальный JS source contract дополнительно запрещает принимать GET 206 с MIME, отличным от проверенного HEAD. HEAD witness теперь связывает `size+etag+mimeType`, а GET 206 должен иметь точно тот же `Content-Type`. Это предотвращает передачу чужой MIME-репрезентации в один нативный декодер. Добавлен отдельный регрессионный тест нарушения MIME.
- Сохранены ранее исправленные требования точного `trackId+albumId+editionId`, URL с `sid`, корректного SHA/ETag, отсутствия 206 truncation и отсутствия network resolve при неполной identity.
- GitHub Actions Node 22 + PHP CLI: **45/45 PASS**, [run 43183941538](https://github.com/manufact-test/nomusic/actions/runs/43183941538). Это проверка **своего** сетевого контракта, не fake native runtime.

## Ограничение теста

Для воспроизводимости успешный серверный transport использует **только собственный тестовый HMAC v1 без session ID**, а session HMAC v2 проверяется на отказ при отсутствии серверного `AudioAccessService`. Это **НЕ доказывает** успешный реальный entitlement/user-session flow. Нельзя использовать результаты теста как доказательство готового пользовательского аудиопотока. `ResolveService` пока не отдаёт authoritative album/edition attestation; Android adapter не должен фабриковать её из названия трека.

Главный блокер issue #41 остаётся без изменений: оригинальные 16 publisher-signed APK работают, независимо подписанная копия устанавливается, но MAIN падает с `IllegalStateException/SIGNATURE`. Запрещено пытаться обходить signing/Passport/DRM/Play Protect. Штатный public MediaBrowserService отвергает наш independently signed client на native Android13. **Нет проверенного in-process host со штатным единым декодером и настоящими Yandex native UI**. Живую подмену и звуковую приёмку владельцем не проводили; пользовательской APK нет.

Не изменялись frozen A1 @ `cc4cb0f93489168db21502f3ef195855ae9fb743`, Test.50, Windows, Chrome extension, PHP/backend production, HONOR 50, оригинальный установленный Яндекс, draft release с исходными APK.

**При последующем разрешении host blocker:** использовать готовый B42 выбор до native decoder `prepare`, не запускать второй плеер; проверить авторизацию, Мою волну, pause/seek/Next/Stop, реальный entitled v2 signed URL, Range и живой звук. Только после акустического принятия Stage A владельцем отдельно начать Stage B.
