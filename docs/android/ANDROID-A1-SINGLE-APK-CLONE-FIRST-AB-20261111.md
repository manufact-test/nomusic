# CELIKOM Android A1 — единый APK: контроль «клон один» против «клон рядом с Яндексом» (11.11.2026)

**База:** `feature/android-parallel-clone-single-apk-merge-20261111` @ `969a3043af3292cf4cd8a56490ff4baea17ed389`. **Резерв:** `backup/android-parallel-single-apk-before-clone-first-ab-20261111`.

Предыдущий реальный Android 11 CI [42912195579](https://github.com/manufact-test/nomusic/actions/runs/42912195579) подтвердил: 5-split оригинал + 1 merged отдельно подписанный native clone одновременно устанавливаются и содержат совпадающие 6 DEX/3 native libs. Но клон MAIN завершается с EXIT_SELF(0) ещё до Activity, `java.lang.IllegalStateException` в scoped MAIN log. Это блокер живого интерфейса и будущей подмены; повторять произвольные перепаковки нельзя.

**Новый изолированный A/B** на одноразовом Google APIs Android 11 x86/ARMv7 CI-эмуляторе:
- A: установить **только** merged отдельный lab clone, убедиться, что оригинального `ru.yandex.music` ещё нет, прямо запустить MainScreenActivity и проверить **основной** процесс, Activity resume и window focus. Не принимать AppMetrica за успешный результат. Выдать только истинные булевы признаки, не raw logs/экран/секреты.
- B: установить оригинальные 5 publisher-signed частей, убедиться в их нормальном запуске и текущем состоянии; **не переустанавливая клон**, проверить тот же родной UI клона рядом с оригиналом и точное 5+1 PackageManager. Original Yandex по-прежнему не изменён.
- Если A FAIL и B FAIL: блокер не является *только* конфликтом одновременных установок, а относится к независимому клону/интеграции; без уверенного безопасного решения на основной HONOR APK не отправлять.
- Если A PASS, B FAIL: искать конкретный package/permission/provider конфликт совместного присутствия, не обходить подписи и Passport.
- Если A PASS, B PASS: это только native MAIN/UI gate; отдельно ещё проверить логин, Play Protect ON и настоящую замену одного аудиодвижка, и только потом owner trial.

Тест ничего не ставит на HONOR, не входит в аккаунт, не меняет безопасность Android, не создаёт публичный модифицированный Яндекс APK. **Не выдавать A/B API/CI-результат за слышимую замену**. Финальный эталон LSPatch пока отсутствует; обязательное самостоятельное напоминание про Stage B действует при его принятии владельцем.


## Verified outcome — GitHub Actions 42913442978

[Actual isolated emulator run](https://github.com/manufact-test/nomusic/actions/runs/42913442978), commit `47e4593d4143d6f0cde5cfd2ea2f3b39c920d55c`, workflow **FAIL** intentionally on strict MAIN/UI proof.

**A: clone ALONE with NO `ru.yandex.music` installed:**
- exact merged 1 APK installation PASS: `clone_standalone_package_manager_pass=true`;
- `clone_standalone_main_activity_and_focus_pass=false`;
- `standalone_main_pid_alive=false`, `standalone_auxiliary_only=true`;
- Activity not resumed; window not focused. No login or audio.

**B: Install original AFTER A, without reinstalling clone:**
- original publisher signed 5 splits installed and original process booted normally;
- `SIDE_BY_SIDE_5_ORIGINAL_AND_1_CLONE_PASS`;
- clone MAIN still dies `EXIT_SELF(0)`, no resumed/focused Activity, helper alone alive;
- main PID `java.lang.IllegalStateException` in sanitized E/F log class, no stack or proven causal condition;
- all merged 6 DEX and 3 native .so byte SHA parity preserved, independently lab signed, signature bypass disabled.

### Causal interpretation

**Confirmed:** coexistence with an installed original is **NOT a necessary condition** for this startup failure. Clone fails without it. This narrows blocker to *independent modified-package host startup / package-identity or resource/permission/auth initialization*, but does not establish which branch, nor prove publisher integrity check.

**Do not proceed to owner HONOR install.** No functional native Yandex UI was demonstrated in disposable environment. Do not disable Play Protect, spoof signer/Passport, bypass DRM or install main-package modified Yandex. Avoid repeating another variant of 5-split/one-APK merge without independent evidence. Next meaningful evidence requires inspectable comparator native clone (e.g. owner-provided ChromaSync binary, no redistribution or copied code) or safe first-party integration/host startup trace with approved research access.

CI binaries/trace/temporary key deleted. No external APK artifacts, login data or owner phone changes. One-APK **installability** proved only on Android 11 translated emulator; Android 13 native ABI / Play Protect still unverified.

**When and only when owner actually accepts a stable audible LSPatch single-player build, proactively remind owner Stage B (independent non-LSPatch injection).**
