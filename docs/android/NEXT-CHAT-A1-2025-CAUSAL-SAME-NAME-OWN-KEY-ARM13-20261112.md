> **ПОСЛЕДНИЙ НОВЫЙ ФАКТ — НЕ ПОВТОРЯТЬ SIGNER 16/16 И INSTALL 16/16.** [ARM13 CI 43118196605](https://github.com/manufact-test/nomusic/actions/runs/43118196605): своё подписание всех 16 genuine 2025 split под исходным именем `ru.yandex.music` PASS, установка PASS, Native MAIN строго FAIL, `java_top_exception_enum=ILLEGAL_STATE`, `java_fatal_thread_enum=MAIN_UI`, `java_top_stack_family=YANDEX_APP`, `java_exception_security_markers=["SIGNATURE"]` — **слово signature обнаружено в тексте первого IllegalStateException**. Это пока не полный root cause, но намного сильнее общей категории `APPLICATION_STATE`. [Точный root-cause отчёт](ANDROID-A1-2025-JAVA-SIGNATURE-MAIN-ROOTCAUSE-20261112.md); code/classifier — `android/native-yandex-hooklab/clone_main_crash_buffer.py`, синтетический CI **28/28 PASS** [43118152206](https://github.com/manufact-test/nomusic/actions/runs/43118152206). **Технический прогресс есть, пользовательского APK нет, Stage A NO-GO**. Владелец запретил предлагать обращения к Яндексу; не продолжать эту тему.

> **РЕШЕНИЕ ВЛАДЕЛЬЦА 12.11 — ОБЯЗАТЕЛЬНО.** Повторно не предлагать писать Яндексу, запрашивать разрешение/лицензию или превращать это в условие следующего этапа. Владелец уже много раз отказал; вместо этого продолжать техническую разработку и проверяемую диагностику по утверждённому ТЗ. Не выдавать недоказанную сборку за рабочую.

> **НОВОЕ ПОСЛЕ 23/23 ПРОВЕРОК:** отдельная изолированная ветка `experiment/android-a1-2025-privatelog-java-rootcause-20261112` реализует read-only классификацию первичного Java исключения и семейства стека `AndroidRuntime` по точному MAIN PID (скрывает имена классов/пути/личные данные). [Синтетический CI 43114504196](https://github.com/manufact-test/nomusic/actions/runs/43114504196) **23/23 PASS**. Категории ещё **НЕ измерены на новом нативном ARM13 CI**, нельзя утверждать, что runtime исправлен. Последний реальный факт: [native CI 43112641177](https://github.com/manufact-test/nomusic/actions/runs/43112641177), подписывание/установка 16/16 PASS, startup ILLEGAL_STATE FAIL. Двигаться к настоящему корню падения, не начинать с подписывания заново.

# ПЕРЕДАЧА СЛЕДУЮЩЕМУ ВЕДУЩЕМУ CELIKOM Android A1 — 12.11.2026

Привет! Ты новый ведущий Android A1. **Не начинай с нуля, утверждённую архитектуру не меняй и уже проверенные варианты не повторяй.** Сначала проверь актуальные HEAD/резервы. Работай самостоятельными большими блоками; всё новое — в своей отдельной исследовательской ветке, без изменений замороженной основной A1 до подтверждённого native/audio результата.

**Репозиторий:** `manufact-test/nomusic`.
**Текущая исходная исследовательская ветка:** `experiment/android-a1-2025-causal-startup-controls-20261112` (проверь актуальный HEAD и резерв по issue #41).
**ЗАМОРОЖЕНА основная A1:** `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`.
**Signing/installation checkpoint:** `backup/android-a1-2025-owner-sdk35-all16-signed-verified-20261112` @ `fcf6cb1107c53611294b74ef787d40b7234cf342`.
**Предыдущий подтверждённый Java-crash резерв:** `backup/android-a1-2025-sign16-install16-java-state-nogo-final-20261112` @ `1d54bc86115ec48acee03a49cd810912cbb73b92`.
**Финальный резерв нового каузального исследования:** см. обновлённый issue #41, одноимённую новую backup ветку.

## Что обязательно прочитать

1. `docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md` — утверждённое полное ТЗ, **не пересматривать**.
2. `docs/android/ANDROID-A1-2025-CONFIG-SPLIT-MINSDK-SIGNER-ROOTCAUSE-20261112.md` — уже решённые signing/installation blockers.
3. `docs/android/ANDROID-A1-2025-SAME-PACKAGE-OWN-SIGNER-ARM13-CAUSAL-20261112.md` — **главный новый результат**, отчёт по причинному A/B.
4. `docs/android/ANDROID-A1-PUBLISHER-SUPPORTED-INTEGRATION-OPTIONS-20261111.md` — законные варианты/вопросы правообладателю, не отправлять без разрешения владельца.
5. GitHub issue **#41 OPEN**. Issue #42/PR #43 audio contract уже завершён и интегрирован в frozen main; 32/32 PASS, повторно не делать.

## Продукт, который утверждён владельцем

Один **отдельный CELIKOM APK** с настоящей нативной Яндекс.Музыкой внутри: штатные экраны, Yandex login, библиотека, Моя волна, плейлисты, родной единственный плеер/декодер. CELIKOM выбирает разрешённый альтернативный audio source внутри штатного декодера. Официальный Яндекс остаётся на телефоне отдельно.

**Запрещено** WebView, свой плеер/двойное воспроизведение, signature spoof, bypass publisher app integrity, LSPatch sigBypassLevel 1/2, Passport/DRM/Play Protect обходы и заимствование модулей конкурентов.

## Что достоверно сделано (НЕ перепроверять без новой причины)

- У владельца уже загружен настоящий 2025.10.4 #120.1gpr XAPK в GitHub **unpublished draft release** `a1-yandex-2025-gpr-private-test` (release 442137464, asset 736739728), 45 961 661 bytes SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`. Не просить заново, **не публиковать** original/release, не записывать сторонние APK/ключи в GitHub source или Actions artifacts.
- Издательский оригинал: 16/16 crypto signatures PASS и **75 s native Android13 MAIN PASS** [CI 43091414430](https://github.com/manufact-test/nomusic/actions/runs/43091414430).
- **Независимая подпись 2025 FIXED**: config splits без собственного minSdk проверяются с minSdk=24 из издательского оригинального base; [CI 43105227726](https://github.com/manufact-test/nomusic/actions/runs/43105227726) 16/16 independent signer PASS. На чистом ARM64+ARMv7 Android13 16/16 уже **установлены**, `am start` accepted [CI 43105679694](https://github.com/manufact-test/nomusic/actions/runs/43105679694). **Дальше Java crash: `APPLICATION_STATE`**, а не ошибка установки или `EXIT_SELF(0)` старой версии 2026. [CI 43106889245](https://github.com/manufact-test/nomusic/actions/runs/43106889245).
- **НОВЫЙ КАУЗАЛЬНЫЙ КОНТРОЛЬ:** полностью исключили смену package name и APKEditor/ARSCLib rebuild: на чистом ARM Android 13 исходный *неизменённый* package `ru.yandex.music`, те же original manifest/resources/DEX/so (без ресурсной пересборки), **своё отдельное временное подписание**, 16/16 signed/verified/install PASS — но MAIN всё равно **FAIL**, `JAVA_CRASH`/ `APPLICATION_STATE` и точнее `ILLEGAL_STATE` [CI 43112641177](https://github.com/manufact-test/nomusic/actions/runs/43112641177). 20/20 синтетических тестов PID-scoped/secret redaction PASS. ZIP подписи при own-key подписывании закономерно отличаются, поэтому строгая причина **сертификат vs ZIP metadata** не установлена. Не объявляй доказанным «Java проверяет сертификат»; это только вероятность в рамках отличий от работающего issuer original.
- Этот causal control выполнили **без vendor signature spoof, без защиты/авторизации/DRM bypass, без LSPatch и чужих модулей**, исключительно на disposable guest и в виде нераспространяемого lab output. Пользовательский готовый APK по-прежнему **отсутствует**.

## Следующий правильный ход

Технически стало ясно, что **ни переименование, ни APKEditor не являются необходимой причиной java startup crash**. Следующий ход должен **сначала** проверить, есть ли **документированная/официальная, разрешённая правообладателем** схема встраивания полного нативного интерфейса под собственной подписью, а не раз за разом менять ZIP/подпись, или проводить security self-check bypass. В публичных документах такого стороннего full-native SDK пока не найдено; поддержка партнёрского закрытого SDK неизвестна. Если законный способ требует письменных прав или доверия издателя, **зафиксируй как внешний blocker и доложи владельцу конкретное решение**, не обходи механизмы защиты. **Не пиши правообладателю** без отдельного разрешения владельца.

Только после успешного **законного** native host/UI с гарантированной совместимостью — нормальная авторизация, библиотека, MyWave, одно воспроизведение, реализация уже готового source-selector на согласованной нативной точке, реальные pause/seek/next/screen-off/BT и акустическая приёмка владельцем. Не выдавай пользователю APK до прохождения Stage A.

После **реального** звукового принятия Stage A отдельно напомнить владельцу про **Stage B — заменить временный LSPatch собственным механизмом**. До тех пор Stage B LOCKED.

**Нетронуты:** frozen A1, Android Test.50, Windows, расширение, сервер/API, админка, production и HONOR владельца. Release draft остаётся неопубликованным.

**Вывод:** Stage A **NO-GO**, issue #41 остаётся **OPEN**. Следующий разработчик не должен тратить время на очередное пересоздание уже устанавливающихся 16 APK; теперь вопрос в доверии/совместимости исходного нативного приложения и правомерном способе встраивания.
