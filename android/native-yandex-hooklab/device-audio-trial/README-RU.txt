CELIKOM Android A1 — Ramil' «Ау», BETA9 (HONOR 50 / Android 13)
21.11.2026. Исправляем подтверждённый BETA8 разрыв: FileInfoApi отдаёт нужный оригинальный trackId, но запрос выполняется на другом потоке, где нет исходной Track-рамки.
BETA9 сохраняет этот ID ненадолго (30 секунд) и привязывает только при точном совпадении оригинального ключа tCa(String), оригинальных Track/Album/Wrapper и настоящего setter плеера Яндекса. Не подменяет API/логин; без подтверждения совпадений играет оригинал.

1. Установить APK поверх BETA8. НЕ удалять приложение и НЕ очищать данные.
2. Запустить CELIKOM/Yandex. Доступ к CELIKOM включается автоматически, кнопки BETA отдельно нет.
3. Проверить 10AGE, Ramil' — «Ау», ID 144530503: https://music.yandex.ru/album/38902809/track/144530503
4. Послушать 00:43–00:54. Пока не проверять паузу/перемотку/радио.
5. Если оригинал, нажать «CELIKOM: … · TXT» вверху справа и прислать файл.

Для диагностики BETA9: ISSUER_ASYNC_ID_OBSERVED, ISSUER_ASYNC_CREATOR_BOUND, ISSUER_ASYNC_CREATOR_STALE, ISSUER_TRACKID, EXACT_BETA_CREATOR, ORIGINAL_SETTER, PREFETCH_STARTED, SIGNED_MPEG_READY, OWNER_RESOLVE_REQUEST, GRANT_ADMITTED, EXACT_PREPARE, DATASOURCE_ARMED, AUDIO_OPEN, AUDIO_READ.
Зелёная CI проверяет установку и запуск Android 13, НЕ доказывает звучание подмены.
