# CELIKOM Android — owner rejects Test.17; functional rollback to Test.15
Дата: 2026-11-03. **СТАТУС: Test.17 отклонена владельцем после первого HONOR прогона.**

## Решение владельца

Test.17 (`0.3.85-test.17/code86102`) вызвала резкое субъективное ухудшение: первая подключившаяся песня сильно лагала; начало и перемотка на ряде песен хуже Test.15, часть обычных пауз игнорировалась. Владелец также сообщил, что после сворачивания UI / закрытия экранов кнопка паузы в Яндекс Музыке останавливала оригинал, а звучание CELIKOM могло продолжаться. **Никаких дальнейших прослушиваний Test.17; не распространять эту сборку и не брать её за базу.** Это окончательный вердикт опыта, не статистическое доказательство одной причины.

## Откат, выполненный в GitHub

- Рабочая ветка: `feature/android-0385-test15-permissionless-recovery-20261103`.
- Коммит отката: `1b26a0afc1d1d0a5177cced54b9e7bd0d7929f14` (`revert(android): restore exact Test.15 functional tree after owner rejects Test.17 [skip ci]`).
- **Проверка GitHub compare:** между текущей веткой и неизменной резервной Test.15 `backup/android-0385-test15-best-owner-20261103` SHA `6fde1e48179ecb812f1def16067f18bf0d9c3003` теперь различаются **только docs/android/**; ни одного изменённого `.java`, теста, тестового spec, workflow, manifest или другого функционального файла. Ранее добавленные Test.17 observer/policy и их host tests удалены из текущего дерева; прежняя cache логика и CI спецификация Test.15 восстановлены точно.
- Исторические коммиты Test.17 сохранены только для forensic review, **не являются активным кодом**. Не переписывать историю и не сливать их в новую ветку.
- Стабильная `CELIKOM 0.3.85/code86`, Hostinger OTA/`stable.json`, сохранённые backup refs, golden seek/ACK, PR #37 не изменены. Новый APK при откате **не собран**: возвращаемся к уже подписанной и подтверждённой Test.15.
- Эталон: `0.3.85-test.15/code86100`, functional SHA `4838ccee4aa4628dce68437ebbf00d4dfc30ce27`, [CI success #41674369584](https://github.com/manufact-test/nomusic/actions/runs/41674369584), [signed Test.15 ZIP artifact 13248949184](https://github.com/manufact-test/nomusic/actions/runs/41674369584/artifacts/13248949184), expires 2026-11-10. Для установки Test.15 поверх установленной Test.17 Android обычно потребует сначала **удалить только CELIKOM Test** (86102→86100 downgrade); оригинальное CELIKOM не удалять. Удаление тестовой версии стирает её локальное состояние, поэтому диагностику владелец уже отдельно передал.

## Приватная HONOR диагностика Test.17

- `CELIKOM-combined-20261103-210209.txt` — 5,688 строк; актуальный `run_start` Test.17 на **строке 4337** в 2026-11-03 21:00:08 +03:00; старые сегменты в начале файла относятся к Test.15 и Test.16, их нельзя смешивать.
- `SVID_20261103_210017_1.mp4` — 96.8с, вертикальная запись 590×1280. Видео и полный combined журнал не коммитить: история прослушивания приватна.
- Актуальный сегмент содержит 43 `replacement_seek_request`, 43 `replacement_seek_ack`, 42 `replacement_transition_complete`, 27 `replacement_source_buffer` с `replacement_source_buffer_resumed`, 13 `replacement_download`, четыре eviction по `entry_limit`. Событий `replacement_lookahead_cache_reused` и `replacement_interrupted_file_retained` **0**: новые cache branches не проявили пользы в этом прогоне. Нельзя по этому журналу утверждать, что именно они вызвали акустический провал.
- Первая текущая песня: полный файл скачивался ~2,423мс, `replacement_prepared` на 2,711мс, `replacement_transition_complete` около 3,103мс после начала run. Это фактический поздний холодный старт и согласуется с жалобой на слышимое начало, хотя не доказывает причину всех лагов.
- Secondary direct Media3: `source_direct_session_connect` для `trackId=42884423` на 60,871мс; уже на 60,880мс `source_direct_session_unavailable reason=connect_failed exceptionType=ExecutionException`. **Ни одного `source_direct_session_comparison`** — direct TYPE_SESSION гипотеза на этом HONOR так и не дала альтернативную позицию. Нельзя выдавать её за исправление «Нас не понимают вообще» или «Дым».
- Видео содержит эпизоды, где в Yandex UI показана пауза, при этом near-time диагностические снимки Media3 могут оставаться `controllerPlaying=true` и `playerIsPlaying=true`. Временное сопоставление видео и лога приближённое; требуется аккуратная трассировка реальной паузы и авторитетного состояния, не выдумывать root cause. Исходный пользовательский слуховой вердикт при этом однозначный.
- Многочисленные `source_buffer` около пользовательских скачков позиции требуют отдельного исследования; не превращать частоту событий в неподтверждённый виновник Test.17.

## Дальнейший план без микросборок

1. Любое новое исследование вести только от **точной Test.15 functional base**, а не от Test.16/Test.17. Сохранить 70% акустически удачных переходов Test.15.
2. До новых изменений составить из сравнительных логов Test.15/17 независимые сценарии «пауза на обычной песне», «пауза из Android media controls при свёрнутой CELIKOM», «перемотка и резкое начало». Не переобучать decision-maker на часто недостоверных source events.
3. Сохранять разрешения mass-market без Accessibility, NotificationListener, MediaProjection, MEDIA_CONTENT_CONTROL, root или скрытых API. Ранее rejected legacy Browser и direct token не считать работающими.
4. Для первых аккордов думать над подтверждённой готовностью cached/local full-file и границами PCM/edition; при полностью холодной неизвестной песне нельзя гарантировать мгновенное скачивание. Не менять произвольно таймеры, gain, audio owner и frozen accepted seek/ACK.
5. Не строить очередной APK сейчас. Сначала обоснованные regressions/architecture plan; затем один большой безопасный пакет и полный CI с отдельной подписанной Test APK, не stable OTA. Любую заметную акустическую регрессию снова откатывать к Test.15.
