# CELIKOM Android A1 — NEXT CHAT

Репозиторий: `manufact-test/nomusic`
Ветка: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Текущее состояние
- На Honor 50 последняя проверенная владельцем версия — BETA36 NAV56. Слышимой подмены нет.
- BETA37 NAV57 собрана, подписана постоянным owner signer и прошла CI. На Honor 50 ещё НЕ установлена/не проверена.
- BETA37 owner-only Draft Release: https://github.com/manufact-test/nomusic/releases/tag/untagged-95a8a3a809bcfa9ef254
- APK: `CELIKOM-A1-RAMIL-AU-BETA37-HONOR50-20261128.apk`
- SHA-256: `fad002a6b73fa04c728565eb97af20578712ab1ab4000dd92807d6dc76c4c866`
- Размер: 71,606,252 bytes. Подпись проверена; install mode — UPDATE_EXISTING.

## Что уже установлено
- BETA36 диагностика: `CELIKOM-A1-Diagnostics-1795880627662.txt`.
- First-open: кандидат принят; deferred arm принят; `DATASOURCE_ARMED=ONE`.
- Альтернативный DataSource открывался и отдавал байты: `AUDIO_OPEN=ONE`, `AUDIO_READ=MANY`.
- BETA36 не связала этот read с текущим MediaPeriod: `LIVE_PERIOD_SOURCE_LOOKUP_CALL=NONE`.
- Renderer read наблюдался при state != 2; `ENGINE_HOLDER_TYPE1_STATE2=NONE`. Старый код прекращал source lookup до чтения текущего PeriodID/MediaPeriod.
- NAV55 подтвердил прямой `Lo96` MediaPeriod в select/attach/read. Holder-аудит не повторять.
- NAV56 сохраняет exact first-open DataSource после очистки creator history. Этот путь не переделывать.

## BETA37 NAV57 — что изменено
- Source lookup запускается и на renderer read при state != STATE_STARTED.
- Сверяются текущий SLOT_B, тот же holder, точный PeriodID (UID + оба индекса) и source identity.
- Добавлены отдельные pre-start counters и регрессионные тесты на совпадающий/чужой SLOT_B и точный текущий PeriodID.
- Проверка read-only. Она не доказывает decoder/PCM или слышимую подмену.
- STATE_STARTED/decoder evidence остаётся отдельным строгим условием.
- MP3/AAC override и audio route не менялись. Не повторять BETA32 codec override без нового доказательства.

## Результат BETA37 CI
Run `46163744419`: https://github.com/manufact-test/nomusic/actions/runs/46163744419
- JVM contract — PASS.
- ARM13 publisher-first side-by-side — PASS.
- Оригинальный publisher установлен первым (16 splits), запущен стабильно 75 секунд (25/25).
- Clone установлен рядом; native main стабилен 75 секунд (25/25).
- Fatal suppression не применялся; owner signer проверен.
- Draft Release и APK созданы, SHA-256 проверен.
- Владелец/телефон не затрагивались; audio/account test не выполнялся.
- Итоговый verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. Это технический gate, не доказательство подмены.

## Следующий шаг
1. Дать владельцу ссылку на BETA37 Draft Release выше; установить APK поверх BETA36 на Honor 50.
2. Не удалять CELIKOM, не очищать данные/кеш; проверить, что CELIKOM включён.
3. В оригинальном Яндекс Музыке открыть Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, сегмент 00:43–00:54.
4. Проверить, запускается ли трек без ошибки и слышна ли подменённая музыка.
5. Обычным коротким нажатием CELIKOM сохранить TXT и прислать его для анализа.

В диагностике проверить:
- `A1_TRACKID_BETA37_NAV57_PRESTART_PERIOD_SOURCE_LINK_20261128`
- `LIVE_QUEUE_SLOT_B_TYPE1_NOT2_READ_MATCH`
- `LIVE_QUEUE_SLOT_B_TYPE1_NOT2_PERIOD_ID_SAME`
- `LIVE_PERIOD_SOURCE_LOOKUP_CALL` / `LIVE_PERIOD_SOURCE_LOOKUP_RESOLVED`
- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS` (либо `..._EOS_UNKNOWN`)
- `ENGINE_HOLDER_TYPE1_STATE_NOT2` и `ENGINE_HOLDER_TYPE1_STATE2`

Если альтернативный read связан с точным текущим MediaPeriod — переходить к decoder/format. Если нет — исправлять только конкретное несовпадение source identity/PeriodID. Не повторять NAV55/NAV56, MP3/AAC override, не запускать CI и не собирать новую версию без конкретной причины из диагностики. Не трогать main и Windows.
