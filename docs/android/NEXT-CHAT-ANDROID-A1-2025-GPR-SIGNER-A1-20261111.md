> **11.11.2026 IMPORTANT: NEW real negative 2025 signing A/B completed.** Read [NEXT-CHAT-ANDROID-A1-POST-V1-REAL-CI-20261111.md](NEXT-CHAT-ANDROID-A1-POST-V1-REAL-CI-20261111.md) FIRST and [actual failed cleanroom A/B](ANDROID-A1-2025-V1-SIGNER-SCRATCH-CLEANROOM-RESULT-20261111.md). 17 synthetic tests PASS; issuer original 16/16 PASS; independent 2025 clone **still signature verifier FAIL BEFORE install** in [CI 43100028330](https://github.com/manufact-test/nomusic/actions/runs/43100028330). Removing old v1 META-INF scratch entries did **not** solve. Stage A NO-GO. Main A1 and Test.50 unchanged. Older status paragraphs below are historical; this is the current status.

# ПЕРВОЕ СООБЩЕНИЕ ДЛЯ СЛЕДУЮЩЕГО ЧАТА — CELIKOM Android A1 (11.11.2026)

Привет! Ты новый **ведущий разработчик CELIKOM Android A1**. Продолжай текущую работу, **не начинай с нуля** и не переделывай утверждённую архитектуру. Работай крупными самостоятельными заходами: исследование → код → настоящий тест → резерв → документация. Не останавливайся после каждого коммита или поставленного в очередь CI и не проси пользователя повторно делать уже сделанное. Объективно разделяй проверенный факт, гипотезу и ожидание runner.

**Repo:** manufact-test/nomusic (публичный; черновик GitHub Release не считать публичным артефактом и не публиковать).

**Замороженная основная A1-ветка:** experiment/android-native-a1-lspatch-clone-loader0-20261111 @ cc4cb0f93489168db21502f3ef195855ae9fb743. НЕ менять до доказанного интеграционного PASS.

**Последняя исследовательская ветка:** experiment/android-a1-owner2025-signer-offline-lab-20261111. В ней подготовлен точный отчёт по упаковке/подписи и offline-диагностике. Перед своими изменениями проверь актуальный HEAD и сохрани точную backup-ветку; не ломай текущую. Pre-work backup предыдущего захода: backup/android-a1-owner2025-signer-analysis-before-offline-lab-20261111 @ 6985e518cfdfa765267e64df13031d3b1eb9d769. Дополнительные бэкапы и SHA смотри в конце отчёта/issue #41.

**Обязательно прочитай:**
1. docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md — утверждённое владельцем ТЗ; главный приоритет.
2. docs/android/ANDROID-A1-2025-SIGNER-OFFLINE-FORENSICS-20261111.md — текущий отчёт, работы и тесты.
3. docs/android/ANDROID-A1-2025-GPR-LAB-SIGNER-ROOTCAUSE-20261111.md — предыдущий этап, строгий базовый диагноз.
4. docs/android/NEXT-CHAT-ANDROID-A1-CHROMASYNC-EXTENDED-HANDOFF-20261111.md — контрольная история конкурента, настоящая ARM13 A/B и все ограничения.
5. GitHub issue #41 (открыт), issue #42 (ЗАКРЫТ, аудиоконтракт уже интегрирован).

**Что за продукт:** человек устанавливает ОДИН отдельный CELIKOM APK; внутри работает настоящая нативная Яндекс.Музыка с привычными функциями, поиском, библиотекой, авторизацией, Моей волной, плейлистами и штатным плеером. Наш код только подбирает доступную разрешённую альтернативную аудиозапись для того ЖЕ штатного декодера; если нет версии, звучит оригинал. Официальный Яндекс на телефоне остаётся нетронутым. Не создавать WebView, свой плеер, второе воспроизведение, отдельное переключение треков, эмуляцию GUI.

**Что уже доказали, не повторяй бессмысленно:**
- Владелец уже загрузил **настоящий, подписанный издателем** XAPK Яндекс.Музыки 2025.10.4 #120.1gpr, 45 961 661 bytes, 16 split APKs, SHA256 8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053; все подписи 16/16 валидны, [CI 43090872523](https://github.com/manufact-test/nomusic/actions/runs/43090872523). **Не проси снова загружать**. Оригинал находится в UNPUBLISHED GitHub draft release tag a1-yandex-2025-gpr-private-test, ID 442137464, asset ID 736739728. Никогда не публикуй draft/файл/секреты, не включай бинарь в git/actions artifacts.
- Этот ПОДЛИННЫЙ ОРИГИНАЛ 2025 реально запускается в чистом ARM13: 16/16 splts installed, native MAIN 75s same PID 25/25, resumed 25/25, [CI 43091414430](https://github.com/manufact-test/nomusic/actions/runs/43091414430). Это **не** запуск нашего клона и **не** proof UI/auth/audio.
- СВОЯ независимая 2025 lab-signed копия: [CI 43092662299](https://github.com/manufact-test/nomusic/actions/runs/43092662299) failed Apktool resources; [43092999958](https://github.com/manufact-test/nomusic/actions/runs/43092999958) и [43093361498](https://github.com/manufact-test/nomusic/actions/runs/43093361498) rebuilt with APKEditor but strict apksigner verify failed BEFORE installation. Причина не установлена. Никакого рабочего собственного CELIKOM APK ещё нет.
- Наш 2026 separately-signed clone в 3 layout проходит установку, но MAIN вызывает EXIT_SELF(0). Это другая, более поздняя проблема; не смешивай с 2025 packaging.
- Конкурент ChromaSync 3.0.1 полный стабилен на ARM13 75s, а его вложенный модифицированный origin.apk без wrapper падает. Конкурент использует LSPatch и sigBypassLevel=2. Его код, патч и обходы НЕ переносить. Самостоятельную подпись издателя подделать нельзя.
- Помощник B (#42) уже закончил подготовительный аудиоконтракт, PR #43 **уже смержен главным A** в основную A1; исправления и 32/32 node tests PASS [CI 43018118683](https://github.com/manufact-test/nomusic/actions/runs/43018118683). **Не дублировать B и не мержить заново.** Это только source contract, реальной подмены в Яндексе ещё нет.
- Test.50 — принятый неизменяемый эталон старого Android; основной Windows, расширение, API, админка, сайт, владельческий HONOR 50 не трогали.

**Что сделано в последнем заходе:**
- Изолированный fail-closed инструмент android/native-yandex-hooklab/ci/lab_signer_signal_gate.py — ZIP CRC, split structural integrity, old v1 META-INF marker counts, duplicate/unsafe entries и категории apksigner ошибок. Никаких raw APK/data/secrets в logs.
- 10 синтетических независимых unit tests в ci/test_lab_signer_signal_gate.py; 10/10 локально PASS на Python (не выдавай это за CI SUCCESS).
- В ci/owner_2025_gpr_lab_clone_no_bypass_arm13.py добавлена проверка unsigned/signed ZIP каждого split до криптографического gate; ошибочную подпись не пропускает.
- Workflow .github/workflows/android-a1-owner2025-signing-integrity-lab.yml для source-only signer диагностики, НЕ устанавливает Android APK, сохраняет в секрете архив.
- Новая [CI 43099023249](https://github.com/manufact-test/nomusic/actions/runs/43099023249) на момент передачи оставалась QUEUED zero jobs. Предыдущие [43097031056](https://github.com/manufact-test/nomusic/actions/runs/43097031056) и [43096955087](https://github.com/manufact-test/nomusic/actions/runs/43096955087) также queued zero jobs. Это **не** неудачный кодовый тест и **не** PASS. Перед новым запуском проверь, разблокировался ли GitHub Actions, не плодить идентичные job.

**Твой следующий большой блок (без дробления):**
1. Проверить 3 run выше и существующие CI logs. Если jobs всё ещё =0: проверить проблему планирования Actions/квоты/ограничений доступными разрешёнными способами; не придумывать «починил», не запускать бесконечные дубли.
2. По конкретному zip_probe и SDK failure category локализовать ошибку переподписи 2025 клона. Прежние v1 META-INF могут быть лишь гипотезой. Любое исправление протестировать на синтетическом APK, затем в отдельном ephemeral CI, сохранив original publisher-signed 16/16 input gate и ОБЯЗАТЕЛЬНЫЙ apksigner pass для каждого lab split. Не обходить системные/издательские проверки и не подменять сертификаты.
3. Только после полноценной собственной 16/16 проверки подписи — native ARM13 install + MAIN stable 75s с независимым package ID. Лишь потом UI/auth/плейлисты/штатный decoder hook и аудиоподмена. Не обещать пользователю APK, пока не будет доказательств.
4. Если техническое решение начинает требовать вмешательства в издательское доверие/DRM/Play Protect или изменение/распространение клиента Яндекса без нужных прав — стоп по этому направлению и согласовать законный вариант с владельцем; никаких тайных обходов. Не связываться с Яндексом без согласия владельца.
5. После реального успешного звукового Stage A и принятия владельцем — **обязательно отдельно напомнить** о следующей согласованной задаче: заменить LSPatch собственным механизмом, не до этого.

**В конце захода:** сохранить точную backup ветку, обновить этот handoff и основной исследовательский отчёт, прокомментировать issue #41 с фактами/ссылками, написать пользователю коротко: что фактически удалось, что заблокировано, что проверять. Не объявлять Stage A PASS по одной зелёной synthetic CI.

**Текущий статус: Stage A = NO-GO, Stage B = LOCKED, собственного устанавливаемого рабочего CELIKOM с нативной Яндекс.Музыкой ещё нет.**
