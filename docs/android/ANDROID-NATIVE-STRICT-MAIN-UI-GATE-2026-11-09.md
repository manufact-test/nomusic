# CELIKOM Android — strict native clone MAIN/UI audit, 09.11.2026

## Актуальное продолжение: MAIN EXIT_SELF + согласованный AppMetrica A/B (10.11.2026)

**Новый кодовый HEAD до этого docs-коммита:** `9c117e994c1562c5f820de843fa15e04d58b8e38`.
**Контрольная ветка:** `backup/android-native-exit-self-ab-evidence-20261110`.
Полный отчёт: `docs/android/ANDROID-NATIVE-MAIN-EXIT-AUDIT-2026-11-10.md`.

Строгая диагностика [42704598401](https://github.com/manufact-test/nomusic/actions/runs/42704598401) выявила: MAIN клона действительно стартует (`am_proc_start`), затем исчезает (`am_proc_died`), а Android 11 относит выход именно MAIN к `REASON_EXIT_SELF=1`. Java/ART/DEX crash не подтверждён, `:AppMetrica` остаётся, UI/фокус отсутствуют. Старый парсер причин выхода исправлен и проверен юнит-тестами. Подписанный исходный Яндекс продолжает работать.

Контролируемая правка одного AppMetrica provider string с соблюдением сортировки `string_ids` и согласованным манифестом **не помогла**: [42706194581](https://github.com/manufact-test/nomusic/actions/runs/42706194581) FAIL, тот же `REASON_EXIT_SELF`. Независимый manifest-only A/B [42706195477](https://github.com/manufact-test/nomusic/actions/runs/42706195477) также FAIL. [42705716074](https://github.com/manufact-test/nomusic/actions/runs/42705716074) статически нашёл 7 точек явного завершения в оригинальных DEX, но **не определил реальный вызов**. Причина/условие выхода внутри приложения пока НЕ доказаны. Не утверждать, что виновата подпись, anti-tamper или AppMetrica.

**NO-GO на нативный клон и аудиоподмену.** Не повторять согласованный/несогласованный AppMetrica-эксперимент и не делать произвольных DEX-правок. Следующая работа — только подтверждение точного self-exit источника через разрешённую read-only диагностику в изолированной среде; если для этого нужен обход издательских защит, прекратить эту ветку и рассматривать официальную интеграцию. Ни Play Protect, ни вход в Яндекс, ни decoder не обходить. Test.50/HONOR/остальные платформы не трогали.

---


## Status verdict (important)

**SIDE-BY-SIDE INSTALLATION PASS; MAIN PLAYER / FOREGROUND UI FAIL.**
No usable Android native Yandex clone and no real CELIKOM source swap exists yet.

The last "SIDE_BY_SIDE...INSTALL_LAUNCH_ONLY" SUCCESS seen in
[CI 42695956456](https://github.com/manufact-test/nomusic/actions/runs/42695956456)
was **too weak**: it counted ANY named clone process, including only the
noninteractive `pro.celikom.yandex.nativeclonelab:AppMetrica` helper.
The exact original launcher `ru.yandex.music.main.MainScreenActivity`
runs in the **default main process** (confirmed signed manifest
[CI 42696018566](https://github.com/manufact-test/nomusic/actions/runs/42696018566)).
The clone main `pro.celikom.yandex.nativeclonelab` PID and `ps` process
were absent across four launch snapshots; foreground resumed activity and
window focus did NOT belong to the clone.

**Strict corrected runtime gate** [CI 42696772783](https://github.com/manufact-test/nomusic/actions/runs/42696772783)
deliberately FAILS with stage:
`MAIN_UI_NOT_READY_AUXILIARY_PROCESS_ALONE_INSUFFICIENT`.
This is the accurate verdict, not an unexpected regression.

## Experiment A — legacy fixed-length DEX literal mutation

- Original #170gpr signed Yandex successfully installs and stays running
  on Android 11 x86 Google APIs / ARMv7 translation.
- A separate 5+5 split-APK clone installs, but main classloader reported
  `YMApplication ClassNotFoundException` [CI 42686813136](https://github.com/manufact-test/nomusic/actions/runs/42686813136).
- Signed DEX original-to-clone static A/B [CI 42690904213](https://github.com/manufact-test/nomusic/actions/runs/42690904213)
  **confirmed** that the byte-length-preserving AppMetrica authority
  substitution violated the mandatory `string_ids` lexicographic ordering.
  Merely rewriting SHA-1 / Adler32 did not make the DEX structurally valid.
  The exact AOSP verifier rejects out-of-order string IDs (Android runtime
  documented by AOSP).
- Current clone script now **fails closed** on this invalid DEX ordering.
  This historical altered-DEX build must not be reused or distributed.

## Experiment B — manifest-only, original DEX byte-identical

- New opt-in `CELIKOM_MANIFEST_ONLY_ORIGINAL_DEX=1` preserves ALL original
  six base DEX files verbatim. It is CI-only, isolated, disposable, no
  modified DEX and no APK artifact release.
- [CI 42694224453](https://github.com/manufact-test/nomusic/actions/runs/42694224453):
  original + lab clone coexist in 5+5 installed split APKs; original main
  launcher alive. Prior `YMApplication` exception not observed, but clone
  still not accepted by simple PID check.
- [CI 42695956456](https://github.com/manufact-test/nomusic/actions/runs/42695956456):
  ActivityManager answered `Status: ok` for clone explicit launcher, and
  an `:AppMetrica` helper stayed alive. This was NOT a functioning main UI.
- [CI 42696772783](https://github.com/manufact-test/nomusic/actions/runs/42696772783):
  corrected strict UI gate FAIL, main process absent at all samples and
  clone was NOT resumed or focused. Original publisher main process stayed
  alive. The limited AndroidRuntime:E log classifier did not observe a
  Java exception and the exit-info classifier returned all false;
  **no definitive shutdown reason obtained**.

## Safety/regressions

- Five-split manifest-only structural CI [42697151607](https://github.com/manufact-test/nomusic/actions/runs/42697151607):
  SUCCESS; original DEX untouched, signatures for lab copy independent,
  no duplicate providers. Its PASS is **structural only**.
- Exact FileInfo read-only module's synthetic and Gradle build jobs
  [42697074970](https://github.com/manufact-test/nomusic/actions/runs/42697074970):
  SUCCESS. These are unrelated to real decoder.
- Earlier signed Retrofit evidence remains: `FileInfoApi` and
  `OldFileInfoApi` use `trackId` at parameter 0,
  `codecs` at parameter 1, `quality` at parameter 3.
  Runtime trackID→edition→native decoder not proven.
- **No HONOR update or phone test requested.** No Play Protect bypass,
  no publisher credential access, no security weakening, no vendor APK
  sharing, no original Yandex deletion, no Test.50/production modification.

## Next developer actions — do not repeat old smoke

1. Diagnose **EXACT MAIN process termination** in disposable Android 11
   control without raw user logs. Note the existing exit classifier looks
   for string literal `REASON_CRASH`, but AOSP dump actually reports
   `reason=4 (APP CRASH(EXCEPTION))`, `reason=1 (EXIT_SELF)`, etc.
   A change to that diagnostic parser was attempted but blocked before
   commit; it is NOT implemented. Do not infer "not a crash" from the
   current all-false classifier.
2. Confirm signed/verified clone has a legitimate functional MAIN/UI
   without weakening Android permission or signer protections. If
   publisher package/signature assumptions block independent login,
   treat as an architecture decision, NOT license to bypass.
3. Only after main UI and account boundary are safe, add *read-only*
   FileInfo param0 witness for genuine native decoder linkage.
   Then test single native source pre-prepare and RASKOL/«Дым»/first join/Next.
4. Keep accepted Test.50, official Yandex on HONOR and prior backup branches
   unchanged. Publish no vendor APK.
