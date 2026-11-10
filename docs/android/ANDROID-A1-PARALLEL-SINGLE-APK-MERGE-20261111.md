# CELIKOM A1: one APK clone structural/runtime experiment — 11.11.2026

Goal: replace five side-by-side **research** clone splits with one independently signed APK while the publisher-signed original five splits stay intact. This does not create an audio replacement yet and does NOT authorize sideload distribution.

Research branch: feature/android-parallel-clone-single-apk-merge-20261111, based on 80a07d20247c37af64cef98442745fefe0d32685. Safe rollback: backup/android-parallel-clone-main-exit-illegalstate-20261111.

Previous translated Android 11 CI: original app running; 5+5 split original/clone installation PASS; cloned main `EXIT_SELF(0)` before UI; `java.lang.IllegalStateException` in main PID error logs, not proven causal. Approved A1 still requires a *single native player* and original Yandex on owner HONOR unchanged.

New variant uses pinned already downloaded REAndroid APKEditor 1.4.9 merge command to combine ONLY the separate clone's five verified independent-signer split APKs. It performs zipalign, re-signs with SAME throwaway clone research key, checks independent clone package, exact version and no split ID, full original clone DEX/native library byte-by-byte SHA parity, and on isolated Android emulator installs original 5 + merged clone **1**. Native MAIN/Activity/foreground remains a hard FAIL if absent. No credentials, no payment, no Play Protect disable, no fake Yandex signature, no LSPatch signature spoof.

All binaries remain ephemeral in GitHub Actions temporary directory. A successful 5+1 **installation** does not imply native UI, account, audio, single-player source swap or Play Protect ON phone approval. If a real MAIN/UI still fails with merged one-APK, DO NOT repeat guessed packaging fixes or claim release readiness. HONOR 50 read-only preflight exists separately, actual owner install only after independent package, permissions and native UI pass.

Mandatory: once LSPatch sound swap works and owner approves preserved exact backup, proactively remind about independent Stage B injection adapter instead of LSPatch.


## Проверенный результат GitHub Actions 42912195579 (11.11.2026)

[Полный CI-прогон](https://github.com/manufact-test/nomusic/actions/runs/42912195579): **workflow FAILURE** по осознанно строгому тесту запуска MAIN/UI. Это НЕ ошибка объединения APK.

- Четыре pure-JVM unit merge contract-теста и остальные проверки логов/диагностики: **SUCCESS**.
- Фактический APKEditor merge пяти отдельно подписанных research-clone splits: **PASS**. Итог: **один merged APK**, правильный независимый package name `pro.celikom.yandex.nativeclonelab`, подписан лабораторным, отличным от Yandex сертификатом.
- Подтверждено сохранение SHA256-содержимого 6 DEX + 3 нативных библиотек по сравнению с пятью входными split-клонами; исходный издательский Яндекс не переподписывался и не изменялся.
- **Действительный PackageManager на Android 11**: одновременно установлены publisher-signed original **5 частей** и lab clone **1 APK**; `SIDE_BY_SIDE_5_ORIGINAL_AND_1_CLONE_PASS`.
- **СТОП**: после Activity start клона MAIN кратко стартует и сам завершается `REASON_EXIT_SELF, status=0`; только `:AppMetrica` живой, foreground Activity отсутствует. MAIN-PID error-class `java.lang.IllegalStateException`; причинность не доказана, Java FATAL и trace не доступны. `MAIN_UI_NOT_READY_AUXILIARY_PROCESS_ALONE_INSUFFICIENT` — честный конечный verdict, **не рабочий клиент**.
- Нет LSPatch внутри merged clone, нет аудиоподмены, нет авторизации/подписки, нет телефоно- или Play Protect-теста. Экспериментальные сборки уничтожены в CI, **устанавливаемый релизный APK не изготовлен и не доставлен**.
- Важная граница: повторная упаковка/слияние не исправляет источник `EXIT_SELF(0)`, поэтому не запускать по кругу одинаковые CI. Нужны законные подтверждения причины запуска / технический путь, не требующий нарушать оригинальные защиты.
