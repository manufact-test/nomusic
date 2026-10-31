# CELIKOM Android 0.3.69 — один режим после трёх приватных HONOR-диагностик

**31.10.2026. Android-only staging. Звук НЕ принят до физической проверки владельца.**

## Что действительно проверялось

Три локальных журнала владельца: `CELIKOM-combined-20261031-191230.txt`,
`CELIKOM-combined-20261031-191549.txt` и
`CELIKOM-combined-20261031-193319.txt`. Это приватные файлы:
**не добавлять их, названия композиций или полный журнал в Git**. Каждый TXT
содержит предыдущие прогоны; сравнение относится только к последнему
`run_start(version=0.3.68)` в соответствующем файле.

| Файл и последний запуск | Фактический выбор | Что можно заключить |
| --- | --- | --- |
| `191230`, строка 2500 | До `elapsed_ms=235372` линейный, затем явно выбран обычный | Один подтверждённый линейный cold join; далее обычные joins. Это НЕ полноценная линейная проверка. |
| `191549`, строка 2615 | Обычный режим | 31 seek ACK, пять ≥200 мс, два ≥500 мс, максимум 656 мс; повторные yield/resume на частичном Range и пять cold 500-мс dips. |
| `193319`, строка 3010 | **Линейный на протяжении последнего прогона** | 8 линейных cold joins, 27 seek ACK; один первичный seek 826 мс с корректировкой 15 мс, остальные ACK 26–74 мс. |

Субъективная оценка владельца: последний **линейный** прогон намного лучше,
большинство начал практически незаметны; несколько подключений ещё слышны;
одна песня с несколькими перемотками пальцем дала рывки. В проблемной песне
было семь decoder seek ACK за **42–58 мс**, без долгого Range; зато после
перемоток возникали короткие Media3 BUFFERING и задержка до проверенного
decoder clock. Следовательно, именно эти рывки нельзя объяснять долгим HTTP
без доказательства. Число join в журнале не равно числу полноценно
прослушанных пользователем песен.

## Объединённая реализация

1. Удалён скрытый long-press переключатель с **«Сохранить диагностику»**,
   диалог и чтение SharedPreferences `celikom-join-lab`. Действует только
   один продуктовый режим; ранее выбранное A/B предпочтение больше не влияет
   на звук. Сама кнопка экспорта диагностики сохранена.
2. Новое присоединение отдельной Android audio session использует прежний
   **комплементарный линейный** handover 160 мс по проверенной ticket/epoch
   дорожке `AudioOwnership.blendSameSong`. Это использует наиболее удачный
   вариант по субъективной HONOR-проверке; **НЕ** equal-power crossfade.
   После финального tick остаётся один слышимый decoder. Проверки Next,
   Stop, pause и stale callbacks сохранены; при реальном повторном
   подключении после долгой паузы действует та же политика.
3. После обычного seek не запускается ещё один 160-мс cold join:
   сохранён быстрый однократный `exclusive_single_turn` только после
   decoder seek ACK, подтверждённого Media3/clock и актуального owner ticket.
   Исходник до этого звучит в полный уровень. Полный файл работает как прежде.
4. При **частичном** файле `BufferedAudio` держит фоновую догрузку на паузе
   через цепочку seek и corrective seek до завершения фактического handover.
   Существующий HTTP Range **не разрывается просто от seek на уже
   закэшированные данные**. Только реальный missing-block `readAt()`
   вытесняет фоновое соединение через watcher, а не decoder thread.
   После действительного handover успешный demand read может запустить
   один worker; реальные Pause, Stop и Next освобождают/закрывают lease.
   Нет нового произвольного таймера/повторного запроса без успешного чтения.

## Границы знания

Две Android-аудиосессии не обладают доказанной sample-phase alignment.
Комплементарные gains сохраняют **сумму команд** при нулевом gain adjustment,
но могут дать частотную интерференцию/изменение тембра на отдельных треках,
Bluetooth и иных выходных маршрутах. Никакого PCM или speaker-output
измерения нет; `phaseVerified:false` и `sourcePcmMeasured:false` остаются
в диагностике. Это осознанный субъективно лучший вариант, а не доказанная
бесшовность и не повод выдавать «звук исправлен».

## Регрессионный минимум перед **одним** APK

- Полный `tests/run_engine.py`: natural song → реальный manual Media3 Next →
  cached/partial scrubs → natural successor → scrubs; короткий BUFFERING
  после seek ACK, 2792/933/17ms, pause/resume, BT, Stop, Next на долгом seek,
  stale owner leases, неправильная редакция и source tail.
- `addon/TestBufferedAudio`: настоящий заблокированный background Range,
  четыре смены позиции, один yield/один resume после handover, точные байты,
  ETag/Content-Range/cancel и гонка успешного foreground read до `finally`.
- `TestHonor066JoinLab` (историческое имя): **один** policy, midpoint 50/50,
  отмена Next/пауза и новая проверка долгого pause/re-attach.
- `check_audio_architecture.py`: не осталось admin A/B selector, cold 500ms
  valley, несанкционированных аудиокоманд или phase-verified утверждения.
- Stage GitHub SDK36/D8 и release-contract — только непубликующий workflow.
  Никаких приватных логов/песен в коммитах.

**Staging gate подтверждён:** code/doc HEAD
[`be15a870b0c2a43290365adfe1fbf54985a4dec9`](https://github.com/manufact-test/nomusic/commit/be15a870b0c2a43290365adfe1fbf54985a4dec9),
[GitHub Actions 41221793450](https://github.com/manufact-test/nomusic/actions/runs/41221793450)
— Android SDK36/D8 **SUCCESS**, `publish-stable` **SKIPPED**.
Локальные JVM ownership/Media3/BT/pause/Next regressions **PASS**,
standalone `TestBufferedAudio` **4139 PASS**, release contract **29 PASS**.
Это build evidence, не физическое аудиоизмерение.

Первый production release gate
[`41221973695`](https://github.com/manufact-test/nomusic/actions/runs/41221973695)
остановился **до подписи/публикации**: быстрый decoder demand успевал
завершиться раньше, чем асинхронный watcher вызывал `disconnect()`,
а `TestBufferedAudio` ошибочно требовал готовый счётчик без ожидания.
Самостоятельный `TestBufferedAudio` четырежды подряд прошёл после
исправления теста: он теперь `await`-ждёт ровно один disconnect и
проверяет, что он случился **не на decoder thread**. Аудиодвижок, gain law,
versionCode и механизм обновлений при этом не менялись. Перед выпуском
требуется повторный полный staging CI.

Подписывать/публиковать исключительно при зелёном CI через существующий
производственный release/update workflow с исходным сертификатом. Версия
кандидата `0.3.69`, code `70`; после live publish проверить подпись,
DEX provenance, номер, SHA256, GET и существующую кнопку
«Проверить обновление». Окончательная приёмка — только на HONOR пользователя,
**один единый режим, одна диагностика**, без новых A/B APK.

## Итог: один подписанный 0.3.69/code70, опубликован

- Повторный непубликующий staging на
  [`a87f912a4d8bef1c92aaa6353ce3cb74ef519081`](https://github.com/manufact-test/nomusic/commit/a87f912a4d8bef1c92aaa6353ce3cb74ef519081):
  [SDK36/D8 CI 41222325576](https://github.com/manufact-test/nomusic/actions/runs/41222325576)
  **SUCCESS**, `publish-stable` **SKIPPED**.
- Единственный **успешный подписанный выпуск**:
  production commit
  [`a30f949b10a72f62977e70cba30767b7c382a249`](https://github.com/manufact-test/nomusic/commit/a30f949b10a72f62977e70cba30767b7c382a249),
  [GitHub SDK36/D8 + sign/publish 41222465012](https://github.com/manufact-test/nomusic/actions/runs/41222465012)
  **SUCCESS**; все `native-android` и `publish-stable / publish` steps завершены.
- Подлинная подпись v2/v3, оригинальный signer SHA256
  `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`;
  точные DEX из CI provenance, assets неизменны. Release verifier сообщил
  `PASS: same signing identity; APK v2/v3 signature; alignment; version/API;
  approved manifest boundary and unchanged catalogue assets; exact compiled addon DEX`.
- **Живой manifest:** `https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json`,
  `versionName=0.3.69`, `versionCode=70`, `packageName=pro.celikom.nativeprobe`.
- **Живой immutable APK:**
  `https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/70-f03e73d37e957d08acdf105371eb7fb7f7f91876d56fee5603cbb0927ed46d20.apk`.
  HTTP HEAD **200**, content type
  `application/vnd.android.package-archive`, размер **8 738 889 байт**.
  Независимый полный HTTP GET в `sha256sum` (exit 0) совпал с manifest:
  **`f03e73d37e957d08acdf105371eb7fb7f7f91876d56fee5603cbb0927ed46d20`**.
- Кнопка **«Проверить обновление»** использует тот же существующий live
  manifest и теперь должна предложить установку code70 поверх 0.3.68/code69.
  **Физическое подтверждение установки/акустики на HONOR ещё принадлежит
  владельцу**; APK не именовать «звук принят».

Теперь нужен **один** пользовательский прогон:
естественная песня → реальный manual Next в Яндексе → 5–6 finger seeks →
естественная следующая песня → ещё 5–6 seek, плюс пауза/возобновление,
Bluetooth, Stop, полностью/частично загруженный файл и Next во время
долгого seek. Без A/B выбора; сохранить только обычную диагностику, если
будет слышимый дефект. Особенно отметить два разных события: слышное
подключение в некоторых песнях и короткий seek-glitch на проблемной песне
при быстрых Media3 BUFFERING/clock transitions.
