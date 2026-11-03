# CELIKOM Android — передача после Test.7: код готов, APK ещё не доставлена (2026-11-03)

## Неотложный итог для следующего чата

**СНАЧАЛА ДОСТАВИТЬ готовую подписанную APK Test.7 владельцу через ChatGPT Library, отдельным файлом .apk, без ZIP.** Не делать новый коммит/пересборку, пока нет новых диагностик или конкретной ошибки сборки. Не писать владельцу инструкции по смене прав, которые в веб-ChatGPT недоступны. Не предлагать ему снова тестировать, пока нет рабочей прямой ссылки на APK.

Владелец только что сообщил: он не смог скачать GitHub Actions artifact; несколько попыток ассистента отправить ссылку на ZIP вместо APK привели к раздражению. **Test.7 ни разу не установлена и не проверена на HONOR по подтверждению владельца.** Считать акустическую оценку Test.7 **NOT TESTED**; сам факт SUCCESS CI не доказывает слышимую бесшовность.

Функциональный SHA **`a365dc1da36a9ee960100c40409d677778070e3f`**; ветка `feature/android-0385-intro-join-investigation-20261102`; приложение `pro.celikom.nativeprobe.test`, label `CELIKOM Test`, `0.3.85-test.7`, versionCode **86092**. GitHub Actions [run #41603059001](https://github.com/manufact-test/nomusic/actions/runs/41603059001) **SUCCESS**, artifact ID **13215970098**, artifact label `CELIKOM-Test-0.3.85-test.7-code-86092`. Внутри ZIP отдельные signed APK, verification.json, receipt.json. **НЕ устанавливать ZIP**; извлечь именно подписанную APK.

Проверки:
- Signed APK SHA256 из runner receipt: **`de9d14050be56de8d7f837973a070c704b75cb23bd381886ac0cbee20e80b5be`**.
- ZIP SHA256: `50afbe026bfc7980ef5d6df76b92b64f51199c5fa4a536e3ad2166552748544a`.
- Signing certificate SHA256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`; `signer_matches_original=true`, separate package, no OTA updater or stable publishing.
- CI: complete native host suite incl. `TestYandexSessionSafety`, unchanged golden seek baseline, Android API36, D8, stable publisher SKIPPED.
- GitHub connector `github_download_workflow_artifact` with repository `manufact-test/nomusic` and artifact ID `13215970098` returns a temporary file reference/ZIP; this is **not a Library APK**.
- Earlier session filesystem had existing Test.5/6 APKs, but not Test.7. Later execution sessions explicitly returned sandbox **read-only** and `curl --output ...` failed with code23; escalation not permitted. The previous assistant incorrectly told the owner to change `Workspace Write`; **web ChatGPT has no per-chat local sandbox selector**, and new chat isn't guaranteed to receive write permission. Do not improvise a fake Library link, wrong APK, or unsupported user settings. If environment can write, download/extract, verify exact SHA/certificate, use official Library skill/create_library_file, then send **direct Library APK link**.

## Что Test.7 действительно меняет

1. **Главная задача: задержки вступлений.** Read-only Media3 timeline next-track lookahead polling ускорен с 2000 до 500мс и обновляется сразу после `onTimelineChanged`. Условия: уникальная identity, 2 стабильных fallback samples, fresh resolve/auth и `MIN_LEAD_MS=3000`. Не обещать идеальный случай rapid Next без времени на сетевую загрузку.
2. **Двойной звук после Yandex audio session renewal.** На HONOR Android13/API33 ранее Yandex ID менялся с74313 на75561, а старый mute effect оставался на74313. Теперь при suspected same-package session mismatch CELIKOM fail-closed прекращает replacement и возвращает оригинал; unverified broadcast **не даёт права** автоматически перепривязать новую session. В обычных сменах песен автоматическое воспроизведение замены сохраняется. Если реальная session меняется, может потребоваться ручное повторное включение (бесшовного rebind ещё нет).
3. **Редкий seek после разблокировки**: два неподтверждённых случая за неделю (ползунок движется, звук не перематывается; Next восстанавливает). В capture 32 seek requests и 32 ACK, воспроизведения бага нет. Test.7 добавлена только пассивная диагностика `deviceInteractive`. **ИСПРАВЛЕНИЕМ это не считать**, frozen accepted HONOR seek logic не менять без воспроизведения.

## По какой диагностике работали

`CELIKOM-combined-20261103-111640.txt`: Test.6 latest owner run 1547 events, 11 boundaries, latency мс gen2..12 = `389, 189, 139, 377, 2196, 103, 289, 239, 262, 201, 127`. Самый тяжёлый rapid Next trackID48591644: prefetch lead 178мс, network ready ~1875мс после source boundary, join +2196мс. Другие треки намного лучше; Test.6 пользователю субъективно заметно лучше Test.4, некоторые интро незаметны. `CELIKOM-combined-20261103-110350.txt` показывает double-audio stale session после длительного background, и отдельный ~23-секундный identity album wait. См. `ANDROID-0385-TEST-7-CONSOLIDATED-OWNER-ISSUES-2026-11-03.md` + `ANDROID-0385-TEST-6-STALE-YANDEX-SESSION-DOUBLE-AUDIO-2026-11-03.md` для подробного анализа.

## Все оставшиеся проблемы и приоритеты

- **P0:** звуковое вступление/переключения, особенно «тяжёлые» песни и быстрый Next: Test.7 ещё не проверена на реальном устройстве, стратегия prefetch может требовать дальнейшей архитектурной работы.
- **P0 safety:** не допускать двух аудио при смене Yandex session; Test.7 содержит conservative fail-closed guard, на HONOR ещё не проверен.
- **P1:** редкий seek UI после блокировки/разблокировки — причина не установлена, только диагностика.
- **P1:** эпизодическое прекращение replacement в середине песни после background; Test.5/6 recovery есть, долгий owner retest ещё нужен.
- **P1:** отдельные долгое ожидание album identity (~23с) и неуспешное подключение — не давать замену по неоднозначной metadata, установить причину, не списывать на audioSession.
- Не выпускать раздельные тестовые APK ради мелкой диагностики/косметики. Владелец требует **один следующий общий пакет** со всеми реальными исправлениями и минимальные ясные сообщения.

## Строгий freeze оригинала

Стабильный оригинал CELIKOM **0.3.85/code86** package `pro.celikom.nativeprobe`, SHA **`053b7d59beb53db5f30b942feba35e51a1ab256a`**. Backups `backup/android-0385-honor-seek-accepted-20261102` и `backup/android-0385-honor-seek-accepted-recovery-20261102` сохраняются без изменений. Не менять `stable.json`, Hostinger, оригинальную OTA, frozen accepted seek/Pause/Resume, PR #37; stable и Test нельзя одновременно направлять на одну Yandex session. Yandex `Плавный переход` OFF.

## Порядок действий следующему чату

1. Проверить, не появилась ли **правильная Test.7 APK** в Library; если появилась — сверить SHA, дать прямую ссылку. Если нет — получить исходный artifact `13215970098`, извлечь именно APK, сверить подпись/hash и загрузить в Library; не перекомпилировать.
2. Отдать владельцу **одну короткую ссылку на APK**. Ни GitHub Actions ZIP, ни длинные отчёты он не просит. Не заявлять `готово` до фактической доступности файла.
3. Дождаться **одного совместного полевого теста**: обычные песни + тяжёлые rapid Next + background/screen off/on + отсутствие double audio и mid-song dropout; seek проверять по ходу естественного прослушивания, не переписывать пока.
4. Разобрать новый owner combined log и акустическое мнение, только тогда решать дальнейший **один общий экспериментальный выпуск**.
5. После следующих изменений обновить этот документ и начало `docs/android/NEXT-CHAT.md`, всегда указывать functional SHA отдельно от docs-only HEAD.

**Коммуникация:** коротко, по существу, не гонять владельца по ненужным настройкам/повторным тестам; пользователь просит прежде всего рабочий APK для установки.
