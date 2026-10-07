# CELIKOM POC 001 Test Plan

## Автоматические проверки

| Проверка | Ожидаемый результат | Статус |
| --- | --- | --- |
| URL parser | Извлекает только цифровой exact Track ID | Выполняется `npm test` |
| Candidate ranking | Выбирает сильный ID и отклоняет неоднозначность | Выполняется `npm test` |
| Drift decision | Корректирует только после заданного порога | Выполняется `npm test` |
| Master time projection | Продвигает playing snapshot и сохраняет paused snapshot | Выполняется `npm test` |
| Replacement time | Безопасно ограничивает позицию длиной test asset | Выполняется `npm test` |
| Settings sanitization | Не принимает неверный ID и ограничивает threshold | Выполняется `npm test` |
| Yandex state matching | По реальным metadata выбирает ID `1944599` | Выполняется `npm test` |
| Artwork normalization | Сводит `%%`, `50x50` и `100x100` к одному ключу | Выполняется `npm test` |
| Duplicate fail-closed | Не выбирает неразличимые ID | Выполняется `npm test` |
| Master media ranking | Отклоняет пустой рекламный video и предпочитает playing audio | Выполняется `npm test` |
| Yandex ad stream | Отклоняет наблюдавшийся короткий video stream `strm.yandex.ru` | Выполняется `npm test` |
| Manual bypass | Действует только для точного текущего Track ID | Выполняется `npm test` |
| Manifest integrity | Все объявленные файлы существуют | Выполняется `npm run validate` |
| Script syntax | Все extension JS проходят `node --check` | Выполняется `npm run validate` |
| Remote code | В package нет `eval` и `new Function` | Выполняется `npm run validate` |
| Audio ceiling | Synthetic asset существует и меньше 40 MB | Выполняется `npm run validate` |
| Fixture HTTP smoke | HTML и synthetic original audio доступны локально | Выполняется `npm run fixture:smoke` |

## Локальный fixture

1. Выполнить `npm run fixture`.
2. Загрузить `spikes/player-poc` как unpacked extension.
3. Открыть `http://localhost:4173/album/1/track/424242`.
4. Запустить original player.
5. В popup нажать `Использовать текущий ID`, затем `Сохранить`.
6. Перезапустить трек. Низкий original tone должен смениться высоким replacement tone.
7. Проверить pause, resume, seek вперёд, seek назад, next track и замену player node.
8. Проверить `Вернуть оригинал` и `Alt+Shift+R`.

## Реальный веб плеер

| Сценарий | Ожидаемый результат | Факт | Статус |
| --- | --- | --- | --- |
| Track ID на landing/main | Exact ID и metadata корректны | Подтверждены `156177669` и `155194611`, confidence 240–260 | Пройден |
| Запуск replacement | Original guarded, synthetic audio слышен | Два трека успешно заменены, `REPLACEMENT_ACTIVE`, `guardActive=true` | Пройден |
| Ручной restore в v0.0.3 | Replacement не запускается повторно | Через следующий state снова происходил `PREPARING → REPLACEMENT_ACTIVE` | Найден blocker; исправлен в v0.0.4 |
| Ручной restore в v0.0.4 | Replacement не запускается повторно | `manual bypass` переводит controller в `IDLE`, guard снят; повторный запуск происходит только после явного изменения settings | Пройден |
| Прямо открытый трек | Exact ID и metadata корректны | Подтверждено в итоговом ручном регрессе 07.10.2026 | Пройден |
| Трек из альбома | Exact ID соответствует playing track | Подтверждено в итоговом ручном регрессе 07.10.2026 | Пройден |
| Трек из playlist | Exact ID соответствует playing track | Подтверждено в итоговом ручном регрессе 07.10.2026 | Пройден |
| Трек из search | Exact ID соответствует playing track | Подтверждено в итоговом ручном регрессе 07.10.2026 | Пройден |
| Play pause resume | Replacement следует без double audio | В paused snapshot replacement остаётся активным, guard сохранён, master `paused=true` | Пройден |
| Seek вперёд и назад | Позиция корректируется | После намеренных крупных seek correction итоговый drift стабилизировался на `13 ms` | Пройден |
| Next previous | Старый replacement остановлен | Зафиксировано `RESTORING · track-changed` → `IDLE · original restored` | Пройден |
| Автопереход queue | Новый Track ID определяется | Track ID менялся между `38077230` и `37889209`, stale replacement не оставался активным | Пройден |
| SPA navigation | Состояние не теряется | На artist/SPA странице bridge оставался ready/healthy, Track ID и metadata обновлялись | Пройден |
| Page refresh | Extension инициализируется повторно | Повторные `MAIN-world bridge ready` без stuck guard и double audio | Пройден |
| Extension установлен при открытой вкладке | Popup сам внедряет controller, без ручного refresh | Controller/bridge восстановились без ручной перезагрузки player state | Пройден |
| Быстрая смена 20 раз | Нет stuck mute и двух replacement | Пользовательский итоговый регресс: слышимых сбоев, stuck mute и double audio нет | Пройден |
| Отключение extension | Original возвращается не позднее 12 s в видимой вкладке | Итоговый ручной регресс: original восстановлен, `guardActive=false` в IDLE | Пройден |
| Возврат из фоновой вкладки | Bridge переподключается без ложного emergency restore | Bridge повторно готов и healthy; ложная активная подмена не осталась | Пройден |
| Ошибка test asset | Немедленный fail-open | Локальный fixture/validation и error path подтверждают restore; отсутствие asset не оставляет guard | Пройден в PoC scope |
| Autoplay rejection | Original остаётся слышимым | На реальном player replacement стартует после пользовательского play; rejection обрабатывается fail-open | Пройден в PoC scope |

## Итог gate

Этап 0 закрыт 7 октября 2026 года. Финальные diagnostics подтвердили exact Track ID `38077230` и `37889209` с confidence 240–260, корректный выбор master audio, отклонение известного рекламного video, ручной bypass, restore при смене трека, здоровый bridge и стабильный итоговый drift `13 ms`. Блокирующих дефектов не обнаружено.
