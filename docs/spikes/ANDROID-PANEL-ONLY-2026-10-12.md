# Android0.3.4: панель без NotificationListener

После повторной блокировки0.3.3 владелец отклонил USB/отключение защиты/Google appeal и просил продолжить работу с приложением. Полный companion не объявляется исправленным.

Full flavor сохраняет стандартное MediaSession наблюдение. PanelOnly flavor реально удаляет MusicListener из merged manifest: не запрашивает уведомления, не получает metadata/state/queue и не вызывает privileged getActiveSessions. Read-only интерфейс эквалайзера и receiver остаются. Яндекс сохраняет собственный UI/master player. Никаких WebView/root/accessibility/перехватов. AudioEffect panel caller и временный session диагностируются, broadcast extras остаются claims. Подмена звука пока отсутствует.

Системный ACTION_SEND принимает штатную ссылку на Яндекс-трек и сохраняет только track_id/time/source=user_shared_link/current_track_verifiedfalse. Это точный ID ссылки, не automatic identification текущей песни, не синхронизация playback. Query/credentials и текст SHARE не сохраняются. Старые media/queue сведения при обновлении в panelOnly не экспортируются, чтобы не выдавать их за актуальные.

Поставка: тот же package pro.celikom.nativeprobe, versionCode5, постоянный private diagnostic key0.3.3. Это ограниченная диагностическая сборка, не новый финальный клиент. Режимы отличаются реальным функционалом и manifest, имя/ключ не меняются ради сокрытия разрешений. Google Play Protect решение о0.3.4 заранее неизвестно. Нужна установка с включённой защитой и повторный вызов панели с Honor50. Автоматическое определение Track ID/sync/replacement остаются открыты.
