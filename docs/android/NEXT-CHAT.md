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
- CI: clone-only differential `46146347294` PASS, но это не product/acoustic pass. Publisher-first ARM13 `46146347357` и observer JVM `46146347367` ещё выполняются.

## Что выяснили по оригинальному Яндексу

Read-only анализ подписанного Yandex 2025, CI run `46144076359`: **PASS**.

- Точный `DataSource.open`: 18 прямых вызывающих методов.
- Точный `DataSource.read`: 23 прямых вызывающих метода.
- Ни один из них и ни один найденный upstream-метод не подтвердился как ExoPlayer Loadable.
- Связь этих вызовов с `Lo96` / `MediaPeriod` не доказана. Активный renderer/source link статически не установлен.
- Отдельно найден статический путь `Lp96` → `Lo96` → `Lwh6` / `Lup1` → native holder. Это только структура оригинального кода, не доказательство, что именно этот period активен на телефоне.
- Анализатор исправлен: повторные callsite больше не считаются отдельными рёбрами. Получено 856 289 уникальных связей; 6 regression tests PASS.

## Следующий шаг

Проверить результаты CI после observer-патча `80f42ed`:
- `HOLDER_OTHER_WH6_AT_READ` и `HOLDER_OTHER_LO96_AT_READ` должны учитывать внутренний объект `wh6` из `up1`.
- `HOLDER_OTHER_SELECT_SAME_AT_READ` и `HOLDER_OTHER_ATTACH_SAME_AT_READ` подтверждают, что это тот же объект, который выбрали и подключили.
- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS` + `PERIOD_ADAPTER_STARTED_NON_EOS_SOURCE_MATCH` подтверждают связь этого period с тем же DataSource и renderer stream.
- Renderer → decoder пока не доказано. После подтверждения этой связки искать только этот последний переход.

Не возвращаться к MP3/AAC, не повторять NAV51–NAV54 и не экспортировать APK ради счётчиков. Аудиомеханизм NAV54 не менять.

## Не трогать

`main`, Windows, сервер, каталог, авторизацию, OTA и второй плеер. Работать только в указанной Android experiment-ветке.

Исторические BETA-документы — архив. Для продолжения читать сначала только этот файл; к архиву обращаться лишь при конкретной необходимости.
