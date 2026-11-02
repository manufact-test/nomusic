# CELIKOM Test.6 — owner retest / диагностика 2026-11-03

## Итог пользователя

Владелец HONOR подтверждает значительное улучшение вступлений в Test.6: многие треки звучат идеально, некоторые «тяжёлые» всё ещё заметно проваливаются. Mid-song отвал в короткой сессии не повторился, на следующий день планируется длительная проверка. Акустически решение ещё не принято.

## Источник

ZIP «Сытый пёс(2).zip»: CELIKOM-combined-20261103-001100.txt и SVID_20261103_000900_1.mp4. Combined содержит три накопленных run — Test.2, Test.4 и **Test.6**; не считать их как один запуск. Новый Test.6 начинается 2026-11-03 00:08:51 +03, HONOR/Android 13, 1084 событий. APK подтверждена как `0.3.85-test.6` / code86091 / `pro.celikom.nativeprobe.test`; functional SHA `3c22a03f364a019ac545efb4e132ad3f5fc12c21`. Сырые данные/видео не коммитить.

## Цифры

- 13 `replacement_source_boundary`, 14 `replacement_lookahead_prefetch_start` и 14 ready, 12 silent-prime start/ready, 10 prime adopted; 1 early discarded (`not_ready_or_live_key_mismatch`). **Не обнаружено зависания promoted-current PREPARING** как в Test.4.
- Медиана boundary → cold-join **211 мс** в Test.6; обычные 10 быстрых joins Test.4 имели медиану **440.5 мс** (тогда ещё два экстремальных 2060 и 5172 мс).
- На 10 общих catalog trackIDs **8 из 10 ускорились**. Таблица мс Test.4 → Test.6:

| trackID | Test.4 | Test.6 |
| --- | ---: | ---: |
| 48591644 | 501 | 577 |
| 40371622 | 492 | 167 |
| 89285816 | 321 | 904 |
| 50163052 | 424 | 1990 |
| 1944605 | 437 | 184 |
| 48592143 | 478 | 268 |
| 42601865 | 2060 | 157 |
| 42498648 | 610 | 152 |
| 27317260 | 362 | 192 |
| 108484219 | 444 | 211 |

### Две оставшиеся длинные задержки

1. track 89285816: boundary at elapsed **70.266 с**, идентификация next и готовый silent decoder имелись заблаговременно (lead ~12.2 с). После boundary fresh current server resolve появился только на **71.050 с** — ожидание backend ~0.75–0.78 с; join 71.170 с (**+904 мс**). Предел не в decoder/pre-download. **Не обходить fresh server authorization/identity check** ради ускорения.
2. track 50163052: boundary at **73.928 с** после быстрого Next; prefetch стартовал ~72.501 с (lead ~1.43 с), полный файл готов лишь в 75.457 с (**+1.53 с ПОСЛЕ boundary**); join 75.918 с (**+1990 мс**). Время скачивания полного файла ~2.95 с; silent decoder не может прогреться до появления файла. Проверить safe longer lookahead при коротких сериях Next без отмены current promoted prefetch.
3. track 48591644: prefetched file ready лишь через +78 мс после boundary, join +577 мс, также без раннего prime.

Остальные переходы в Test.6: 583, 331, 147, 577, 167, 904, 1990, 184, 268, 157, 152, 192, 211 мс (source gen2..14).

## Mid-song и видео

Recovery at elapsed12.045 с (`drift_unstable`, drift ~952 мс): защитный откат к исходному звуку; другие recovery at 33.075 с `source_end`, at 68.637 с `replacement_end`. Не доказан бесконечный mid-song dropout, но это **не подтверждает** долгосрочную стабильность. Видеозапись ~112 с содержит mono mixed AAC и тихие окна (напр., 58.13–61.26 с при -35dB); без изолированных Yandex/replacement PCM и точного offset невозможно приписать тишину одному приложению или контенту. Timestamp команд ≠ слышимое начало PCM.

## Что делать дальше

**Главный приоритет — начало песен.** Найти безопасную оптимизацию свежего backend current resolve и способ заблаговременного downloading при быстром Next; сверить с исходным кодом. Никаких speculative обходов точной идентификации, авторизации, current-handoff lease, AudioOwnership, принятой seek/Pause/Resume. Если конкретной безопасной правки пока нет, оставить Test.6 как проверенный owner checkpoint; не выпускать диагностические или косметические APK отдельно. При реальном фиксе объединить изменения в одной Test APK >86091 с полным regression suite, неизменным seek baseline, API36/D8, CI, оригинальной подписью, SHA/verification/receipt и Library.

## Неприкосновенное и доставка

Test.6 functional SHA `3c22a03f364a019ac545efb4e132ad3f5fc12c21`; [successful CI #41523894044](https://github.com/manufact-test/nomusic/actions/runs/41523894044); [signed APK](https://chatgpt.com/library?file_id=libfile_085b58b278f48191a17c48818dba3bde&account_id=personal), [verification](https://chatgpt.com/library?file_id=libfile_937665882e708191a5dc483f46f36dcc&account_id=personal), [receipt](https://chatgpt.com/library?file_id=libfile_bba341cab64081918847ecd9f7190c96&account_id=personal). Signed APK SHA256 `74d9b0369d31f84657fc951b7bb6a5c9396c62c30815e5faae222cd1b2de5e21`.

Stable 0.3.85/code86 package `pro.celikom.nativeprobe` / functional SHA `053b7d59beb53db5f30b942feba35e51a1ab256a`; обе accepted seek backup ветки, `stable.json`, Hostinger, stable publisher не менять, PR #37 не объединять. Smooth Transition в Яндекс Музыке OFF; два CELIKOM не запускать одновременно против одной audio session. Последний docs HEAD отдельно от functional SHA; перед дальнейшей записью проверить текущий HEAD.
