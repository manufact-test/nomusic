CELIKOM Android A1 — NAV44. Read-only сравнение MediaItem текущего оригинального Timeline Window и MediaItem того же активного источника, который связан с PlaybackInfo PeriodID и SLOT_B.

Установить поверх NAV43. Не удалять приложение и не очищать данные. Официальную Яндекс.Музыку не изменять.
Проверить несколько обычных треков и Мою волну; Next, паузу, перемотку и повтор того же трека.
Сохранить TXT диагностикой CELIKOM, прислать файл.

NAV44 сначала требует NAV43 positive SAME_CALLBACK и неизменный SLOT_B. Затем проверяет только равенство Java-ссылок MediaItem текущего окна Timeline и исходного source — никаких названий песен, личных идентификаторов, URI, байтов PCM или содержимого буферов.
Контрольные строки: PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_SAME_REF / DIFFERENT / UNAVAILABLE / SLOT_CHANGED.
Маркер NAV_V44_CURRENT_MEDIAITEM_SOURCE_READONLY.
BUFFER_EOS_ACCESS=NO_HOOK. Это только read-only structural identity, не подтверждает редакцию, текущий PCM или работу подмены.
CELIKOM_REPLACEMENT=NOT_CONNECTED; IDENTITY_STATUS=STRUCTURAL_ONLY.
NAV40 и резервная ветка не изменены.

После проверки отправить именно TXT с пометкой NAV_V44_CURRENT_MEDIAITEM_SOURCE_READONLY. Не делать вывод о подмене только по совпадению MediaItem.
