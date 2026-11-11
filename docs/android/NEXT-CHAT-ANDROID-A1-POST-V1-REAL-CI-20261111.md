# ПЕРВОЕ СООБЩЕНИЕ ДЛЯ СЛЕДУЮЩЕГО ЧАТА — CELIKOM Android A1

Привет! Ты следующий ведущий разработчик CELIKOM Android A1. Продолжай текущий проект с последнего проверенного состояния. Не начинай с нуля, не меняй архитектуру, не переписывай уже принятые решения и не останавливайся после каждого коммита или очереди GitHub. Работай большими блоками, обязательно сохраняя точные резервные ветки.

**GitHub:** manufact-test/nomusic.
**Замороженная основная ветка Android A1:** experiment/android-native-a1-lspatch-clone-loader0-20261111 @ cc4cb0f93489168db21502f3ef195855ae9fb743. НЕ изменять до верифицированного интеграционного результата.
**Последняя исследовательская ветка:** experiment/android-a1-owner2025-v1-sanitized-signer-lab-20261111. После начала проверь актуальный HEAD. Backup до последнего эксперимента: backup/android-a1-owner2025-v1-clean-before-builder-20261111 @ ff42f3f41f8c458eb5aed182a321f3a922027e70.

**Обязательно прочитай сначала:**
1. docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md — утверждённое владельцем ТЗ.
2. docs/android/ANDROID-A1-2025-V1-SIGNER-SCRATCH-CLEANROOM-RESULT-20261111.md — самый новый реальный отрицательный A/B.
3. docs/android/ANDROID-A1-2025-SIGNER-OFFLINE-FORENSICS-20261111.md — 2025 signer flow/CI/исходники.
4. docs/android/NEXT-CHAT-ANDROID-A1-CHROMASYNC-EXTENDED-HANDOFF-20261111.md — история контролей конкурента/оригинала.
5. GitHub issues #41 OPEN и #42 CLOSED.

**Продукт:** самостоятельный ОДИН APK CELIKOM — в нём настоящая нативная Яндекс.Музыка, штатный интерфейс, аккаунт, библиотека, Моя волна, плейлисты, родной плеер и единый декодер. CELIKOM выбирает вместо определённых треков доступные разрешённые альтернативные аудиозаписи, а не запускает свой плеер. Установленная у владельца официальная Яндекс.Музыка нетронута. Никакого WebView, ручного переключения приложений, двойного звука, собственного UI или удаления оригинального Яндекса.

**Что уже достоверно проверено:**
- Владелец прислал оригинальный XAPK 2025.10.4 #120.1gpr, 45 961 661 bytes, SHA256 8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053; ровно 16 original APK с подлинными подписями Яндекса, [CI 43090872523](https://github.com/manufact-test/nomusic/actions/runs/43090872523) SUCCESS. Находится в GitHub UNPUBLISHED DRAFT release tag a1-yandex-2025-gpr-private-test, release ID 442137464 / asset 736739728. НЕ просить загрузить ещё раз, не публиковать draft/бинарь/ключи.
- Этот ПОДЛИННЫЙ ОРИГИНАЛ 2025 реально установился в native ARM13 и жил 75 секунд: одинаковый MAIN PID 25/25, resumed 25/25 — [CI 43091414430](https://github.com/manufact-test/nomusic/actions/runs/43091414430). Это НЕ наш CELIKOM, не доказательство login/playback.
- Собственная отдельно подписанная копия 2025: сначала Apktool resource error [43092662299](https://github.com/manufact-test/nomusic/actions/runs/43092662299), затем APKEditor rebuild signature verification FAIL [43092999958](https://github.com/manufact-test/nomusic/actions/runs/43092999958), [43093361498](https://github.com/manufact-test/nomusic/actions/runs/43093361498). Ни разу не установилась, до MAIN не дошла.
- В последнем большом заходе добавили read-only ZIP/v1/JAR diagnostics, 17 полностью синтетических тестов (в Python локально 17/17 PASS, также CI прошёл тестовую часть). Реальный [CI 43099023249](https://github.com/manufact-test/nomusic/actions/runs/43099023249) показывает: оригинал 16/16 валиден, rebuilt unsigned contains previous v1 markers, new own-key signature STILL fails apksigner на split 0. [CI 43100028330](https://github.com/manufact-test/nomusic/actions/runs/43100028330) проверил безопасную очистку старых META-INF/v1 подписи из отдельного unsigned lab APK перед own-key signing: 17/17 synthetic tests PASS, original 16/16 PASS, но apksigner снова FAIL на split 0 с теми же категориями. **Это исключает простой вариант «убрали старую подпись — заработало». Не повторять один и тот же эксперимент.**
- Наш separately signed 2026-клон в старой работе УСТАНАВЛИВАЛСЯ, но MAIN уходил в EXIT_SELF(0). Не путай с неинсталлируемым 2025 clone. Проблема доверия/внутренних проверок не решена.
- Конкурент ChromaSync-Clone-3.0.1.apk имеет настоящий нативный интерфейс Яндекса с LSPatch wrapper и его собственным модулем; полный конкурент жил в ARM13 75 s, вложенный re-signed 2025 host без wrapper падал. У конкурента sigBypassLevel=2; нам НЕ разрешено переносить обход, код, бинарь, DRM/Passport tricks. Его эксплуатация не доказана на всём UI/audio.
- Помощник B #42 уже закончил подготовительный source-only audio selection contract, PR #43 главный A уже смержил с улучшениями и [32/32 PASS CI 43018118683](https://github.com/manufact-test/nomusic/actions/runs/43018118683). НЕ мержить снова и не дублировать. Это ещё не подмена звука внутри Яндекс.
- Принятый Android Test.50, Windows, extension, API/backend, сайт и HONOR 50 владельца НЕ меняли.

**Твоя следующая работа:**
1. Проверь актуальные workflow states. Старые [43097031056](https://github.com/manufact-test/nomusic/actions/runs/43097031056) и [43096955087](https://github.com/manufact-test/nomusic/actions/runs/43096955087) ранее висели QUEUED zero jobs; не дублировать их.
2. Изолированно выясни конкретную причину отказа apksigner по 2025 lab split 0, не доверяя голой гипотезе об outdated v1 signing markers. Сначала синтетический APK под нашим ключом и независимая SDK toolchain диагностика, затем только pinned genuine original в disposable CI. НЕ снижать криптографические требования, не подделывать сертификаты, не включать LSPatch signature bypass, не отключать Play Protect и не трогать DRM/авторизацию.
3. При полном 16/16 подписном PASS отдельно запускай на чистом native ARM13 Android13 install/MAIN 75s, потом настоящее UI/login/плейлисты/один декодер/заменённое аудио/Play Protect. Без этого не предлагай пользователю установочный APK и не выдавай синтетические PASS за работающий продукт.
4. Если честный технический путь упирается в требование доверия Яндекса или права модификации/распространения стороннего приложения, это отдельное юридическое/архитектурное решение владельца. Не обходи такие механизмы и не обращайся к Яндексу без разрешения владельца.
5. После реальной звуковой Stage A, принятой владельцем, **обязательно напомни** про утверждённый следующий этап: заменить LSPatch на собственный механизм. До этого Stage B закрыт.

В конце крупного захода: точный резерв, обновлённые docs и комментарий к issue #41, краткий отчёт пользователю только с доказанными результатами.

**Текущее положение: собственного работающего нативного Android CELIKOM нет; Stage A NO-GO, Stage B LOCKED.**
