# CELIKOM Android A1 — актуальное состояние

Дата: 2026-11-28  
Репозиторий: `manufact-test/nomusic`  
Рабочая ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
Код BETA34: `a513e1045bc5fdd76beb06e697399c9b48c6e351`

## Что уже проверено

- **BETA32 MP3 override — НЕ РАБОТАЕТ.** Request-only подмена ломала воспроизведение. Не возвращать и не повторять без новой доказанной причины.
- **BETA34 NAV54 — работает до чтения альтернативных байтов:** `FIRST_OPEN_CANDIDATE_ACCEPTED=ONE`, `DATASOURCE_ARMED=ONE`, `AUDIO_OPEN=ONE`, `AUDIO_READ=MANY`. NAV54 сохраняем.
- **BETA34 на Honor 50 — слышимой подмены НЕТ.** `CELIKOM_REPLACEMENT=NOT_CONNECTED`; чтение альтернативного источника в текущем renderer period не подтверждено; `ENGINE_HOLDER_READ_RETURN_MINUS3=MANY`, `ENGINE_HOLDER_TYPE1_STATE2=NONE`.
- Счётчики собраны по процессу. Не приписывать AAC/MPEG или отдельные чтения конкретной песне без связи по объектам.
- **Патч observer `80f42ed`**: при renderer read из `up1` извлекается внутренний `wh6`; его identity сверяется с объектами select и attach. Альтернативный DataSource read и renderer stream теперь атрибутируются только при совпадении обеих ссылок. Аудиомеханизм NAV54 не менялся.
- Добавлены JVM positive/negative tests для wrapped `wh6`.
- CI: clone-only differential `46146347294` PASS, но не product/acoustic pass. Publisher-first ARM13 `46146347357` PASS: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO` — музыка не запускалась, renderer counters не получены.
- Observer JVM `46147441043` PASS: wrapped-wh6 positive/negative identity tests passed.
- Предыдущий ARM13 run подтвердил `PERSISTENT_OWNER_SIGNER` и `UPDATE_EXISTING`; fresh install не требуется.
- Первый BETA35 export run `46147938426` остановился на упаковке из-за оставшегося пути BETA34. Исправлено в `517905c`; корректный run `46148935304` выполняется. APK ещё не выдана.

## Что выяснили по оригинальному Яндексу

Read-only анализ подписанного Yandex 2025, CI run `46144076359`: **PASS**.

- Точный `DataSource.open`: 18 прямых вызывающих методов.
- Точный `DataSource.read`: 23 прямых вызывающих метода.
- Ни один из них и ни один найденный upstream-метод не подтвердился как ExoPlayer Loadable.
- Связь этих вызовов с `Lo96` / `MediaPeriod` не доказана. Активный renderer/source link статически не установлен.
- Отдельно найден статический путь `Lp96` → `Lo96` → `Lwh6` / `Lup1` → native holder. Это только структура оригинального кода, не доказательство, что именно этот period активен на телефоне.
- Анализатор исправлен: повторные callsite больше не считаются отдельными рёбрами. Получено 856 289 уникальных связей; 6 regression tests PASS.

## Следующий шаг

JVM-проверка патча `80f42ed` пройдена. Для runtime proof нужен запуск реального трека на телефоне с этой версией observer:
- `HOLDER_OTHER_WH6_AT_READ` — внутренний объект `wh6` из `up1` действительно виден при read.
- `HOLDER_OTHER_LO96_AT_READ` вместе с `HOLDER_OTHER_SELECT_SAME_AT_READ` и `HOLDER_OTHER_ATTACH_SAME_AT_READ` подтверждает, что выбранный/подключённый объект имеет точный класс `o96` и это та же ссылка.
- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS` + `PERIOD_ADAPTER_STARTED_NON_EOS_SOURCE_MATCH` подтверждают связь с DataSource альтернативных байтов и renderer stream.
- Renderer → decoder пока не доказано. После подтверждения предыдущих связей искать только этот последний переход.

BETA35 NAV55 — целевая owner-test сборка с исправленной связью `up1 → wh6 → select/attach → DataSource/renderer`, а не сборка ради новых счётчиков. Дождаться `46148935304` и проверить draft asset. На телефоне устанавливать как UPDATE_EXISTING, не удалять существующий clone и не трогать оригинальный Яндекс. Затем один реальный трек и diagnostics. Это ещё не доказательство слышимой подмены; Renderer → decoder остаётся открытым. NAV54 audio route не менять.

## Не трогать

`main`, Windows, сервер, каталог, авторизацию, OTA и второй плеер. Работать только в указанной Android experiment-ветке.

Исторические BETA-документы — архив. Для продолжения читать сначала только этот файл; к архиву обращаться лишь при конкретной необходимости.
