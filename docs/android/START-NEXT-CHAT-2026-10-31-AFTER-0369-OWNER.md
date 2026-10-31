# Новый чат: CELIKOM Android 0.3.69 — продолжение после удачной контрольной версии HONOR

Привет! Ты продолжаешь разработку **строго CELIKOM Android**, repo [manufact-test/nomusic](https://github.com/manufact-test/nomusic). Предыдущий чат закончил unified single-mode Android 0.3.69, получил первую настоящую физическую диагностику HONOR, заморозил и описал контрольную точку. Твоя цель — исправить оставшиеся **слышимые cold/resume joins**, сохранив всё удачное, и отдельно доработать Android UX после системной установки обновления.

## Обязательно перед кодом

1. [`ANDROID-0369-HONOR-OWNER-LISTENING-CHECKPOINT-2026-10-31.md`](ANDROID-0369-HONOR-OWNER-LISTENING-CHECKPOINT-2026-10-31.md) — полный разбор новой приватной 0.3.69-диагностики (только последний run, 33 seek ACK 21–95 мс, 10 unified joins), subjective owner QA, ограничения telemetry.
2. [`ANDROID-0369-ONE-MODE-HONOR-TRIAGE-2026-10-31.md`](ANDROID-0369-ONE-MODE-HONOR-TRIAGE-2026-10-31.md) — почему выбрали single-mode linear и как устранили прежние буферные лаги.
3. [`AUDIO-CAPTURE-FEASIBILITY-2026-10-31.md`](AUDIO-CAPTURE-FEASIBILITY-2026-10-31.md) — ограничения акустической/PCM-фазовой проверки в Android.
4. [`REGRESSION-GATES-2026-10-29.md`](REGRESSION-GATES-2026-10-29.md), [`NEXT-CHAT.md`](NEXT-CHAT.md), предыдущие 0.3.67/0.3.68 акты.

## Неприкосновенная контрольная точка

- **Последняя подписанная и установленная на HONOR:** Android **0.3.69/versionCode70**.
- **Production код подписанного APK:** `a30f949b10a72f62977e70cba30767b7c382a249`; branch `feature/android-unified-preparation-seek-gate`.
- **НОВЫЙ backup:** `backup/android-0369-honor-listening-control-20261031` указывает на тот же неизменённый SHA. Старые backup refs не передвигать.
- GitHub production [SDK36/D8, sign and stable publish 41222465012 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/41222465012); APK SHA256 `f03e73d37e957d08acdf105371eb7fb7f7f91876d56fee5603cbb0927ed46d20`; старый signer, v2/v3 signature, DEX, stable available. Не выпускать 0.3.70 лишь ради документов.
- Staging branch `feature/android-honor065-continuity-staging` используется для следующей безопасной работы; проверять текущий HEAD.
- Единственный режим: complementary **linear 160ms** для нового трека/длинного resume, **exclusive single-turn** на seek, demand-first HTTP Range с удержанием/возобновлением фоновой догрузки. Старый admin A/B selector полностью удалён из `RecorderActivity`/`ProbeService`, «Сохранить диагностику» только экспортирует журнал. **Не возвращай две тестируемые версии и не проси повторить два прогона.**

## Что фактически услышал владелец в последнем HONOR прогоне

- Значительно лучше всех старых версий. Finger seeks и обычная пауза — в основном без подлагиваний, ручной Yandex Next у одного трека — идеальное начало.
- При отдельном холодном соединении слышно краткое снижение громкости примерно до 70%, затем обратно; при некоторых других — короткий повтор слога/ноты на слух 0.3–0.5 с, без изменения громкости; после длинной паузы один раз был подобный повтор, повторно не воспроизводился.
- Никакого полного «обрыва и пшика», как в прежних версиях. Звук всё ещё **НЕ принят**. Особое внимание не к seek latency, а к временному/фазовому расхождению источника и replacement при соединении.
- HONOR latest run 0.3.69: 7 media aliases, 6 boundaries, **33 replacement_seek_complete 21–95 мс**, 25 buffer/resumed, 10 prefetch yield/resume, **10 linear joins**, 10 expected overlap_commands; в joins `phaseVerified:false`, `sourcePcmMeasured:false`. Clock drift при примерах ≈134–200 мс. Разные исходы на слух при похожем coarse drift. Media3 field `manualNextButtonObserved:false` даже при manual Next, не принимай ложный вывод. Wi-Fi verified; BT/cellular/Stop не проверены на телефоне.
- Не своди разговор к «всё зелёное значит звук починили»: логи не меряют фазу и реальную громкость.

## Задачи

1. **В первую очередь** исследуй механизм cold transition: что именно вызывает слышимый dip либо микро-повтор при одновременной игре двух сессий. Сравни на хорошем и плохих join точку входа, decoder advancement, residual drift, DSP/volume commands; отдельный кейс — reattach после 35.7-секундной паузы с `resume_aligned driftMs=132 seekSkipped=true`. Не угадывай длительность кроссфейда и не возвращай equal-power (ранее он создавал +3dB/интерференцию на коррелированных записях). При необходимости добавить безопасную наблюдаемость и воспроизводимый тест.
2. Не ломать успешно работающие fingerprint/tickets, partial/full buffer, finger scrubs, real Media3 Next, Bluetooth, pause/resume, Stop, long-seek owner fencing, network worker rearm, релизный сертификат. Вся работа **только Android native companion**, без компа, backend, сайта, каталога, auth.
3. **Отдельная небольшая задача Android updater UX:** пользователь нажимает «Проверить обновление», скачивает APK, системный installer предлагает «Обновить»; после согласия приложение исчезает с экрана, **но остаётся как неоткрытая карточка в Recents**. Пользователь согласен на два решения: либо после успешно подтверждённой установки убрать CELIKOM task card и закрыть полностью (он потом сам запустит), либо автоматически открыть обновлённое приложение. Выбери надёжное UX по ограничениям Android и проверь на HONOR. Не закрывай task до завершения системного подтверждения; не меняй stable channel, APK URLs, систему подписи/публикации и auth.
4. Сначала инженерная диагностика и регрессионные тесты + **непубликующий** staging CI SDK36/D8. Новый подписанный APK только когда решение обосновано и regressions PASS, через существующий подписывающий pipeline. При публикации одна версия, проверь signer, DEX, version, SHA256, stable manifest и кнопку обновления; на слух принимает только владелец HONOR.

Не загружай приватные owner TXT, имена песен или пользовательские сведения в GitHub. При необходимости для анализа владелец сможет передать один релевантный журнал — **не возвращай A/B двух режимов**.

Начни с проверки фактических heads, документов и кода. Не делай хаотичные правки.
