# CELIKOM Blur — передача для следующей партии 200 (будущая 800), 08.11.2026

## Подтверждённый результат
- Предыдущие replacement **518–717**: **200/200 approved/active** после одобрения владельцем; независимый [postapproval audit PASS](https://github.com/manufact-test/nomusic/actions/runs/42510930997), каталог, resolve, HEAD 200, Range 206 — без ошибок.
- Новые replacement **718–917**: **200/200 новых pending, 0 auto-approved/active**, реальный [4×50 production import PASS](https://github.com/manufact-test/nomusic/actions/runs/42511351984), [независимый production audit PASS (повтор после импорта)](https://github.com/manufact-test/nomusic/actions/runs/42511392076). Все 200 MP3 проверены и скрыты от активного каталога/API.
- Текущая рабочая ветка: `feature/blur-batch600-20261108`, не merge в main. Фиксированная партия: `tools/blur-batch600/fixed-plan600.json`, объём **1 223 634 198 байт**, replacement IDs **718–917**.
- Накопительный CSV `docs/research/BLUR-REJECTED-CUMULATIVE.csv`: **50** уникальных технических отказов, из них 15 новых в текущей партии.
- Полный отчёт: [BLUR-BATCH600-2026-11-08.md](BLUR-BATCH600-2026-11-08.md).

## Следующие действия
1. Пользователь вручную модерирует новую партию **718–917** по 50, не утверждать права автоматически. После одобрения провести отдельную read-only live проверку с `tools/blur-batch600/check-current200-after-approval.php`: approved/active, каталог/resolve, HEAD и Range и фактические байты. Скрипт подготовлен, пока не запускался.
2. **Только после команды владельца на следующие 200** создать ещё одну isolated feature-ветку **от текущей**. Не трогать main, другие Android/Windows/extension ветки и серверную админку.
3. Использовать проверенные `tools/blur-batch600/` и pinned FckCensorData commit `10187b7af56f311fe141a3c9b75483798bf0f589`; обновить candidate manifest, исключив все **50** отклонённых источников и live-дубли из `tracks`, `track_replacements`, `track_requests`, `bulk_moderation_tombstones`, а также artist+title совпадения.
4. До записи проверить MP3: size, blob Git SHA1, MIME, Mp3Inspector, ffprobe duration; временные ошибки отдельно от технических. Подобрать **ровно 200 технически валидных новых** и **зафиксировать их в новом immutable fixed-plan**, не использовать прежний.
5. Проверить свободное место и активный release. Проводить четыре последовательных 50 через приватное хранилище и pending, проверить каждую живой БД+файлами, затем полный независимый read-only аудит всех 200. Никаких auto-approve, auto-active, автоотметки прав.
6. Результат сообщать по подтверждённым цифрам, URI GitHub Actions и новым отказам. Не путать корректное аудио с подтверждением оригинальной длительности Яндекс.Музыки или юридическими правами.

Примечание: при импорте текущей партии первая **независимая** проверка стартовала **до завершения** записи и обнаружила отсутствие ещё не загруженных файлов; её повтор **после импорта** завершился SUCCESS. Для следующих партий postcheck запускать **только после SUCCESS** импортного workflow, чтобы избежать ложного раннего FAIL.
