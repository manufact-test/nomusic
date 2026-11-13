> **LATEST — 13 Nov NAV5 is ready for owner retest; NAV4 already proved the failing process.** NAV4 owner TXT shows four `JAVA_CRASH` exits of the cloned `:passport` process in five minutes. Each Passport session records uncaught `IllegalStateException` → `FATAL_DISPATCH / NOT_METRICA` → self-kill. The exact cause and throwing method were not exposed by NAV4; do not infer Firebase, signature, account or provider cause.

> NAV5 APK `CELIKOM-A1-NAV5-Passport-Fatal-20261113.apk`, 71,438,316 bytes, SHA-256 `d0d0d52f44f5a62cfcbcf8e34ed6d0b239dae31117ba8c6a5876e3303801af37`, is saved in Library at `/CELIKOM/CELIKOM-A1-NAV5-Passport-Fatal-20261113.apk`. Exact source `0851e384101e2bc21a16043350e1cfed24b0d97d`; paired ARM13 #43488933870 and standalone #43488933817 both SUCCESS 25/25. These are startup-only checks, not Passport/login/audio acceptance. The owner will provide NAV5 video and TXT in the next chat; read those first and do not request another NAV4 run, USB, ADB or credentials.

Current lead handoff: `NEXT-CHAT-ANDROID-A1-LEAD-20261113.md`. NAV4 exact reserve: `backup/android-a1-nav4-real-passport-illegalstate-owner-proof-20261113` @ `fed35ede4acdbf2ea9e9c9c0405fa517aa4d1e53`.

---
# CELIKOM Android A1 — owner-device onboarding exit triage (13 Nov 2026)

## Current observed result

- Device: owner's existing HONOR 50 / Android 13.
- Diagnostic APK: `CELIKOM-A1-Native-ReadOnly-Diagnostic.apk`, package `pro.celikom.yandex.nativeclonelab`, Yandex Music 2025.10.4 clone.
- Installation succeeded; Google Play Protect raised no block or warning. App is installed separately beside original Yandex.
- First launch waited approximately 15–20 seconds, then displayed Yandex My Wave/personal recommendations and introductory navigation screens.
- At the fourth of four intro indicators/pages, owner pressed the next arrow. Loading began, then the app closed to Android launcher.
- Owner cannot reach login, track playback, pause/seek/Next, or any audio path. This is the entire report; no further steps were completed.
- The owner uses their existing Yandex account on this same phone if/when the clone reaches authentication. No separate test account is available or required.

## Correct interpretation of prior CI

Workflow [#43450303301](https://github.com/manufact-test/nomusic/actions/runs/43450303301) passed original-first co-install and 25/25 idle MAIN foreground samples over 75 seconds. The test calls `am start` for `MainScreenActivity` and checks PID/resumed activity. It does **not** automate or verify the four intro pages, the next arrow, authentication, track selection, audio, controls, or MediaDataSource calls.

Thus:
- APK packaging/signing/install and original+clone side-by-side are verified.
- Idle main-screen survival is verified in CI.
- Owner-device onboarding navigation is **FAILED**.
- Actual audio path and playback are **NOT TESTED**.
- The APK is not ready for audio testing or release. No root cause is yet proven.

## Replacement on-device diagnostic APK — READY

The replacement build is available after successful Android 13 ARM13 validation.

- Workflow [#43461955113](https://github.com/manufact-test/nomusic/actions/runs/43461955113) **SUCCESS**: original publisher installed first and remained stable 25/25 for 75 seconds; CELIKOM clone installed alongside it and remained stable 25/25; no Metrica fatal suppression observed.
- Separate clone-only control [#43461955329](https://github.com/manufact-test/nomusic/actions/runs/43461955329) **SUCCESS**, clone 25/25.
- Artifact ID `14057522148`, name `CELIKOM-A1-OnDevice-Diagnostic-20261113`, 7-day retention.
- APK `CELIKOM-A1-Native-ReadOnly-Diagnostic.apk`, package `pro.celikom.yandex.nativeclonelab`, Yandex Music 2025.10.4, size 71,430,124 bytes, SHA-256 `9fe9c0139564ead9b499e059065006e4097e833db7c06e7d453fd45f1d75cfe4`.
- The module stores finite CELIKOM diagnostic events in the clone's private files directory, reads Android 13 historical process-exit reason categories on next launch, and adds a small in-window `Сохранить диагностику` button. On tap, it copies the TXT to `Downloads/CELIKOM A1` using MediaStore. No storage permission, USB, PC, ADB or BAT is needed.
- The build and paired startup gate passed. **The button's actual tap/export flow has not yet been exercised on the owner's handset**; owner confirmation is still required. No onboarding tap-through, authentication, playback, readAt calls, or audio substitution was tested. This APK remains diagnostic-only, not a release.

### One owner action

1. Uninstall only the previous diagnostic clone installed from the earlier CELIKOM test APK. Its temporary signing key is different, so Android cannot update it in place. **Do not uninstall the original Yandex Music app** (`ru.yandex.music`).
2. Install the new APK.
3. Repeat the already-described four intro pages and final arrow until it returns to the Android launcher.
4. Reopen the CELIKOM clone. Tap `Сохранить диагностику`.
5. Attach the TXT from `Downloads/CELIKOM A1` to this ChatGPT conversation.

No extra Yandex account is needed; use the existing account only if/when the clone reaches sign-in. Do not send credentials, SMS codes, tokens, screenshots of account pages, or general logs.

If the button is absent or saving fails, do not reinstall or clear data. Tell us exactly what happened and send a screenshot of the app screen without personal information.

## Engineering next steps

1. Inspect the returned finite event report and Android exit reason category.
2. If it proves a Java fatal, explicit exit/kill, native crash, or ANR, trace that exact cause and reproduce the same intro navigation in disposable ARM13 CI.
3. If the app simply finishes an Activity without a process exit, add a narrowly scoped lifecycle witness.
4. Fix only the CELIKOM clone; keep original Yandex, Test.50, Windows, production and the A1 architecture untouched.
5. Re-run the four intro pages, then verify login. Only after that return to actual MediaDataSource/MediaExtractor playback observation and B42 integration.

No second player. No architecture change. Do not claim audio or full app acceptance from idle 25/25 startup tests.


## Owner on-device TXT received — targeted navigation follow-up

The owner uploaded `CELIKOM-A1-Diagnostics-1794587810900.txt` (300 lines). It includes exactly one `PREVIOUS_EXIT_INFO=NONE` and one `APP_LIFECYCLE APPLICATION ENTER/RETURN`; successful AppMetrica activate, service, Push provider return and resource path OUTER_OWN; no `FATAL_DISPATCH`, `UNCAUGHT`, `SYSTEM_EXIT`, `RUNTIME_EXIT` or `PROCESS_KILL`. Last line is `DIAGNOSTIC_EXPORT DOWNLOADS REQUESTED`. This establishes the private on-device file export path works and provides **no observed Java/process fatal**. It does not prove that the onboarding action was captured or successful; no Activity navigation witness existed in this build. The single app init is consistent with an Activity/task finish while process survives, but is NOT conclusive.

Implementation follow-up: narrowed diagnostic instrumentation to log bounded clone-only `ACTIVITY_PHASE` (CREATED/STARTED/RESUMED/PAUSED/STOPPED/DESTROYED_FINISHING/DESTROYED_OTHER), exact framework `ACTIVITY_FINISH` categories, and `ACTIVITY_START` with finite Intent action/destination categories. Never record screen names (except general MAIN vs VENDOR vs OTHER), URLs, arguments, auth data or raw class names. All original method calls proceed unchanged. No B42/audio changes. Run paired native ARM13 and standalone validation again before offering another diagnostic APK.


## 13 Nov — navigation witness APK fully built and exported (CI PASS)
- Initial owner phone TXT `CELIKOM-A1-Diagnostics-1794587810900.txt` (300 finite events) had exactly one application initialization and PREVIOUS_EXIT_INFO NONE. No FATAL_DISPATCH, SYSTEM_EXIT, RUNTIME_EXIT or PROCESS_KILL. It confirms on-device export worked, not that onboarding succeeded. The cause of the exit to launcher is still **unproven**.
- New experimental code `3863feba1dbc4cc6a509f2c18f936fcb43e57755` adds **read-only clone-only** Activity lifecycle and finish/start Intent-category hooks (no URL, raw screen name, intent extras, account values or audio data; original calls forwarded once). Includes prior one-tap Diagnostics → Downloads exporter.
- Paired Android13 ARM13 [#43465459512](https://github.com/manufact-test/nomusic/actions/runs/43465459512) **SUCCESS**: original stable 25/25, clone stable 25/25, both installed, no Metrica suppression; readAt and MediaExtractor registration remains true. Standalone [#43465459488](https://github.com/manufact-test/nomusic/actions/runs/43465459488) **SUCCESS**, clone 25/25. These automated tests still do not tap through onboarding or validate login/audio, nor do they confirm a real phone's navigation callback categories.
- Exported private artifact `14057738468` (`CELIKOM-A1-OnDevice-Diagnostic-20261113`, 7 days). Exact APK archive member `CELIKOM-A1-Native-ReadOnly-Diagnostic.apk`: size 71,434,220 bytes; SHA-256 `7e470aa7903fbf2c923ab7634e7b694a1fb8a3ad130751289ddd640a3046b363`. User-facing extracted direct filename `CELIKOM-A1-Onboarding-Navigation-Diagnostic.apk` contains **these exact same APK bytes**. Package remains `pro.celikom.yandex.nativeclonelab`.
- Owner next step: remove **only** previous CELIKOM diagnostic clone (each CI build has a fresh temporary signer, in-place updates not possible); never remove original `ru.yandex.music`. Install new APK; reproduce 4 intro pages/final arrow; reopen clone and tap `Сохранить диагностику`; send TXT from Downloads/CELIKOM A1. No USB/PC/BAT; no additional account. If launcher exit does not reproduce, report that too; do not claim fixed without confirmation.
- After receipt, discriminate `ACTIVITY_PHASE` (PAUSED/STOPPED/DESTROYED_FINISHING), `ACTIVITY_FINISH`, `ACTIVITY_START` events versus system-process fatal markers. Target the observed closure, no broad architecture rebuild. Test.50, Windows, production and publisher original untouched.

## 13 Nov — second real HONOR 50 phone evidence: video + navigation TXT

Owner provided a ~54 s screen recording and `CELIKOM-A1-Diagnostics-1794589772625.txt` (327 events). The video shows clone startup with a black loading screen/spinner for roughly 15–20 s, Yandex 2025.10.4's four intro pages, then the final arrow leading to another loading spinner and the Android launcher. Owner opens Android recents immediately after: the CELIKOM task is **not present**. Tapping CELIKOM again starts the spinner/intro afresh. The separate stock Yandex application is not affected.

The diagnostic confirms the critical first attempt in strict event order:
- #78 `ACTIVITY_PHASE MAIN_ACTIVITY CREATED`, #80–81 `ACTIVITY_START NONE OWN`, #82 `ACTIVITY_FINISH MAIN_ACTIVITY FINISH`; #102–113 vendor intro Activity CREATED/STARTED/RESUMED. This is the observed initial launch chain.
- #298 `ACTIVITY_START NONE OWN` is emitted at the final-onboarding transition. #301–306: vendor Activity PAUSED → STOPPED → SAVE_STATE → **DESTROYED_FINISHING**.
- There is **no Activity CREATED callback for the target of #298** before #306. The next #307 MAIN_ACTIVITY CREATED followed by #311 VENDOR_ACTIVITY CREATED is consistent with the explicit second user-initiated app launch visible in the recording, not proof that the first transition succeeded.
- No `ACTIVITY_FINISH VENDOR_ACTIVITY` was observed for #306, although `isFinishing()` was true; this is not enough to claim an app-initiated `finish()` call, since system/task-finish paths can also set that state.
- Exactly one `APP_LIFECYCLE APPLICATION ENTER/RETURN` at #3/#20; `PREVIOUS_EXIT_INFO ANDROID NONE` at #1; no `FATAL_DISPATCH`, `SYSTEM_EXIT`, `RUNTIME_EXIT`, or `PROCESS_KILL` was recorded. The recorder does not prove process death; the phone demonstrably lost the foreground Activity/task.
- The start observer currently emits *before* `chain.proceed()`, so `ACTIVITY_START NONE OWN` proves an attempted own-package Intent, **not** successful start or a valid/resolvable destination.

**Current technical priority:** determine why the final intro Intent to the CELIKOM package produces no observable target Activity before the vendor intro finishes. Inspect the target component against the merged, installed 2025.10.4 clone manifest, including explicit class, package, alias, Activity resolution, and launch flags. If that static comparison cannot settle it, narrowly instrument the exact clone-only `startActivity` outcome/throw category and `finishAndRemoveTask`/task-finish path, logging bounded categories only. Do not add a broad network/identity/audio probe or bypass the genuine onboarding flow. Compare with untouched publisher behavior where possible. Preserve all original arguments, returns and exceptions.

The 15–20 s slow spinner is a **second issue**. Investigate it after resolving onboarding navigation, rather than guessing at Firebase or B42. No audio, login, B42 integration, live server, Windows, Test.50, or stock package was changed or accepted. This is owner-device failure evidence; 25/25 idle CI remains valid only for idle startup.

Snapshot before further changes: `backup/android-a1-owner-video-activity-transition-evidence-20261113` at `25bd6321a3d7f850041f6ea64168ab7285de2f48`.

### Follow-up structural check and narrow read-only code (13 Nov)
- Inspected `AndroidManifest.xml` directly inside the exact owner navigation APK from private artifact #14057738468 (no vendor modification). It declares 132 activities and 6 activity-alias entries; **all activity and alias class names are fully qualified**, not relative names accidentally retargeted by changing the manifest package. This specifically excludes the simple relative-class-rebasing hypothesis; it does **not** prove the destination selected by onboarding exists or starts correctly.
- New read-only clone-only Java witness commit `e9cdd607e668304aa97371399464104242aca601`: hook common startActivity overloads and `finishAndRemoveTask`, emit bounded `ACTIVITY_TARGET` categories for explicit component registered/missing in own installed manifest plus task-clear flag family, and `ACTIVITY_START_RESULT` normal return vs whitelisted ActivityNotFound/Security/IllegalArgument/other failure. All original Activity method arguments, returns and thrown exceptions are preserved, no raw target name/URL/extras or login data collected. Source edit is **not** proof of runtime stability.
- Both native CI workflows started for this code change: paired `43471511290`, standalone `43471511289`. Verify their final verdict before offering any APK. The previous known-good 25/25 diagnostic artifact #14057738468 remains intact in the user's Library. No duplicate-owner test is needed until a new verified binary is actually available.

### 13 Nov — new exact diagnostic APK passed both ARM13 gates and uploaded to owner Library
- Read-only source `e9cdd607e668304aa97371399464104242aca601`.
- Publisher-first paired ARM13 [#43471511290](https://github.com/manufact-test/nomusic/actions/runs/43471511290): SUCCESS; standalone clone-only [#43471511289](https://github.com/manufact-test/nomusic/actions/runs/43471511289): SUCCESS. Both reached native device steps and finished with no failure. These checks still do **not** automate the real onboarding arrows or test audio.
- Private artifact ID `14060878514` is the output of the *paired* gate. Exact member `CELIKOM-A1-Native-ReadOnly-Diagnostic.apk`: 71,434,220 bytes; SHA-256 `14453c8b3dd075a67d23de69bbf24d17938c2d400f22505d9462b03d5f8d73e1`. Owner-facing same bytes named `CELIKOM-A1-Navigation-Target-Outcome-20261113.apk`.
- Owner Library confirmed at `/CELIKOM/CELIKOM-A1-Navigation-Target-Outcome-20261113.apk`; previous validated APK untouched. No original Yandex or production writes.
- Owner install/test (one bounded attempt only): remove only the earlier **diagnostic CELIKOM clone** because CI ephemeral signatures differ, keep original Yandex; install this new diagnostic APK; advance four intro pages to final arrow; if launcher exit recurs, reopen and save TXT once. Required witness events: `ACTIVITY_TARGET`, `ACTIVITY_START_RESULT`, `ACTIVITY_FINISH` / `ACTIVITY_PHASE` around the third own-package Intent. If login unexpectedly opens, report success instead of attempting unrelated configuration; only later proceed to a permitted playback test.

## 13 Nov — second phone attempt at ~20:35, intro resumes then task exits

Owner provided real device `SVID_20261113_203508_1.mp4` (~52.7 seconds) and `CELIKOM-A1-Diagnostics-1794591360307.txt` (~340 event lines), reportedly from the NAV target/outcome build. Video: startup loading spinner ~15–20 s, intro cards, final attempted transition to spinner and launcher; reentering clone again shows the intro (not signed-in/player). Owner reports an additional repeat of the four intro cards before eventual exit. Preserve owner report as stated.

Source-backed new event ordering:
- #79 MAIN_ACTIVITY CREATED; #80–82 own start/start, FINISH MAIN. #101–112 vendor intro CREATED/STARTED/RESUMED.
- #296 `ACTIVITY_START NONE OWN`, followed by #299 `ACTIVITY_PHASE VENDOR_ACTIVITY PAUSED`, **#302 VENDOR_ACTIVITY RESUMED**: attempted navigation falls back into the old intro Activity while its task is still open.
- #311 `ACTIVITY_START NONE OWN` again, followed by #314–319 vendor PAUSED/STOPPED/SAVE_STATE/**DESTROYED_FINISHING**; the first subsequent MAIN_ACTIVITY CREATED is #320. That is consistent with a further (manual) launcher tap after the task leaves recents. Exactly one APP_LIFECYCLE entry #3 indicates these events may share an Android process, but is not process-death proof. The video supports the user's report that the visible task closes to home; no signed-in player appears.
- **Critical diagnostic gap:** the newest provided TXT contains **zero** `ACTIVITY_TARGET` and **zero** `ACTIVITY_START_RESULT` records, despite those being compiled into the GitHub paired artifact #14060878514 / SHA-256 `14453c8b3dd075a67d23de69bbf24d17938c2d400f22505d9462b03d5f8d73e1`. Local byte inspection of the exact user-provided APK confirms nested `assets/lspatch/modules/pro.celikom.a1exitwitness.apk` classes2.dex contains both markers. The key question is **which runtime observer build is actually executing on the phone**, not whether the GitHub code contains the strings. Do NOT claim this proves an Android crash, successful route, or old installed APK.
- The APK bundle signatures of the previous and new diagnostic builds are different. A regular update over the prior diagnostic should be rejected by Android; preserve owner data/security and do not assume which APK was successfully installed from filename alone.
- A targeted `NAV_V3_OWNER_PHONE` runtime identity marker was added at Application diagnostics activation (first persisted session events) plus a visible `Диагностика NAV3` button label. A simple unconditional `NAV_V3_START` emission was added immediately after existing Activity-start logging, *before* any PackageManager access; this ensures the next report can definitively show whether the new observer loaded. The exact own vs implicit resolve check now returns finite `IMPLICIT_UNRESOLVED`/`IMPLICIT_OWN_RESOLVED`/etc. The observer never changes intents, returns or errors.
- New source commits `a162101630f1fa7c3fe3ff26ede56ac453e427c7`, `74000cea099f56115c9bb1ad2c1d4b754e057b6f`; pre-change protective backup `backup/android-a1-onboarding-v3-before-owner-2035-witness-20261113` @ `f267e38f90fb09e8a9704a345b9a1a12b685d45f`.
- Correct priority remains only onboarding's specific non-resolving/returning own-package navigation and owner-visible 15–20 s startup delay. Do not reinterpret native 25/25 idle success as login success, and do not alter B42, Firebase-stable reserve, original Yandex, Test.50, Windows or live server. New user test may follow only after actual CI success and verified artifact export, not before.

### Safeguard refinement before NAV3 CI acceptance

The NAV3 test instrumentation must not perform synchronous package-manager lookup on the hot `startActivity` path; that extra IPC could itself influence navigation timing and contaminate the failure under investigation. Source commit `6f30c08148252316f8038e2a9739226826b4144a` replaces the earlier `PackageManager.getActivityInfo()/resolveActivity()` queries entirely with a passive in-memory `Intent.getComponent()/getPackage()/getFlags()` shape classification. The `ACTIVITY_TARGET` event now means target **shape** (explicit own main/vendor/other vs implicit package scope), **not resolved existence**. The local start-outcome marker and exception-category observer remain read-only and should not change arguments, results or exceptions.

This supersedes the earlier plan to resolve targets synchronously within an Activity-start interceptor. If static declaration/absence is needed, check the exact clone manifest in separate CI code after capturing a target-class category, not on the owner handset in the hook. A visible `Диагностика NAV3` button and persisted `DIAGNOSTIC_BUILD NAV_V3_OWNER_PHONE ACTIVE` are the definitive runtime-build markers. Both relevant CI runs for exact new source (paired #43475960711, standalone #43475960685) started; do not call them PASS before their final success.

### NAV3 owner-phone artifact — exact verified, 13 Nov 2026

- Latest NAV3 read-only observer code: `6f30c08148252316f8038e2a9739226826b4144a`; includes stable `DIAGNOSTIC_BUILD/NAV_V3_OWNER_PHONE/ACTIVE` event persisted at Application diagnostics start, a visible `Диагностика NAV3` button, unconditional `NAV_V3_START` emitted immediately after any existing Activity-start event, simple already-in-memory Intent target shape, and start method return/error categories. **No PackageManager IPC** in the Activity-start hook and no authentication or audio behavior changes.
- Exact native clone-only ARM13 workflow [#43475960685](https://github.com/manufact-test/nomusic/actions/runs/43475960685): **SUCCESS**. Exact paired publisher-first ARM13 [#43475960711](https://github.com/manufact-test/nomusic/actions/runs/43475960711): **SUCCESS**. Both are still idle 25/25 gates, *not* proof that actual owner onboarding works.
- Private GitHub artifact #14063028168, nested exact `CELIKOM-A1-Native-ReadOnly-Diagnostic.apk`, size **71,434,220 bytes**, SHA-256 **`d8f846b0316088efc903acbbff2a85198153b6f675bfd539f268b1bf83468add`**. Verified archive and nested classes2.dex locally: NAV_V3_OWNER_PHONE, NAV_V3_START, DIAGNOSTIC_BUILD, ACTIVITY_START_RESULT, ACTIVITY_TARGET and visible Диагностика NAV3 strings are present in the actual packaged module.
- Extracted same APK into personal Library `/CELIKOM/CELIKOM-A1-NAV3-Diagnostics-20261113.apk` and verified listing. Prior diagnostic APK remains preserved.
- Owner: uninstall **only** previous diagnostic clone due temporary signer; do not uninstall the original Yandex. Install NAV3, confirm that the top-right button explicitly reads `Диагностика NAV3` before interpreting any log, reproduce the final four-screen transition once, reopen, tap this button and return TXT. If the button label lacks NAV3, do not confuse previous APK logs with new observer results. **This build is diagnostic, not a fix or release.**
- Known failure: real phone's earlier #296 start -> vendor PAUSED/RESUMED then #311 start -> vendor PAUSED/STOPPED/DESTROYED_FINISHING; second opening may be user tapping app again. No signed-in player/audio tested. Baseline startup success protected at `backup/android-a1-firebase-namespace-success-witness-20261113`; pre-NAV3 owner evidence snapshot at `backup/android-a1-onboarding-v3-before-owner-2035-witness-20261113`.

## 13 Nov — NAV3 owner phone log + on-device video, and identified Passport observability hole

Owner submitted `SVID_20261113_211508_1.mp4` (53 seconds) and `CELIKOM-A1-Diagnostics-1794593760351.txt` (363 events), from actual NAV3 diagnostic. Video shows diagnostic button NAV3 visible, long initial startup spinner, promo onboarding, arrow -> spinner -> launcher, reopen -> intro from beginning. No auth/music. TXT #3 has `DIAGNOSTIC_BUILD/NAV_V3_OWNER_PHONE/ACTIVE`: **the correct NAV3 observer definitely ran**, unlike the ambiguity of prior phone TXT.

Exact NAV3 event chain:
- #80 MAIN CREATED; #81–96 four *nested/intercepted* Android start observers report `EXPLICIT_OWN_VENDOR`, `OTHER_OR_NONE`, `ACTIVITY_START_RESULT RETURN` (do not interpret four re-entrant hook messages as necessarily four distinct starts). #97 MAIN FINISH, #118–128 VENDOR CREATED/STARTED/RESUMED; #131 MAIN DESTROYED_FINISHING.
- #269 VENDOR PAUSED then #270 VENDOR RESUMED (intro stays).
- #317–320 one later `EXPLICIT_OWN_VENDOR` start, flags `OTHER_OR_NONE`, returns normally. #323–328 VENDOR PAUSED/STOPPED/SAVE_STATE/DESTROYED_FINISHING. No observed destination CREATED before the subsequent #329 MAIN CREATED (the user's manual reopen after launcher exit), and #330–353 starts new VENDOR intro again.
- Android `PREVIOUS_EXIT_INFO NONE` at #1, no Java fatal/kill in captured **main process**. Return from startActivity is only an accepted request, NOT proof of destination Activity execution or absence of crash in another process.

New static exact-binary finding: parsed the signed user-facing diagnostic APK `/CELIKOM/CELIKOM-A1-NAV3-Diagnostics-20261113.apk` AndroidManifest.xml and resources.arsc directly. **132 declared Activities**. **39 Yandex Passport Activities** (including `LoginRouterActivity`, `DomikActivity`, and `AuthSdkActivity`) declare android:process reference `0x7f130a32` which resolves to `@string/passport_process_name = ':passport'`; this starts the separate clone process `pro.celikom.yandex.nativeclonelab:passport`. Three Plus-Pay Activities use another process reference `@string/pay_sdk_process_name`. Main observer `arm()` and `emit()` were guarded to `Application.getProcessName() == pro.celikom.yandex.nativeclonelab`, so **they could not observe Passport-process Activity or fatal events**, even if that subprocess started and crashed. This is an evidence gap, not proof that the final target is actually Passport or that it crashed.

Action: new opt-in clone-only passive NAV4 observer `bf93e5d94eb8466a27f2b743f332132bf990763c` only in the working experimental branch. Main startup/Firebase/architecture untouched. Detailed finite targets: `EXPLICIT_OWN_WIZARD`, `EXPLICIT_OWN_ENTRY`, `EXPLICIT_OWN_PASSPORT`, and other music/vendor groups rather than one ambiguous EXPLICIT_OWN_VENDOR. Passport process gets only separate Activity lifecycle + uncaught/exit read-only hooks and a separate private bounded diagnostic file; the owner one-tap export appends it to the main report. No target classes/URLs/credentials/messages logged, no overlay on Passport screens. Main process also queries Android ApplicationExitInfo on tap/export (not on navigation) and labels main vs :passport, recent vs older. UI marker is `Диагностика NAV4`, TXT identity `NAV_V4_PASSPORT_WITNESS`. Do not claim success/ready before both CI runs pass. CI started paired #43482403120 and standalone #43482403689. Exact prior working-tree backup `backup/android-a1-nav3-owner-runtime-before-passport-observer-20261113` @ `7b6d9f3bbadc2d6341cadbc8441d7cb304f126b3`.

Native 25/25 idle test does **not** tap onboarding or enter :passport; owner acceptance still required. No original app modification, no authorization bypass, no B42/audio changes, no prod/Windows/Test.50/Firebase baseline changes. Priority is recover stable login flow first, then actual native audio.

### 13 Nov — NAV4 clone Passport observer, both native ARM13 gates SUCCESS, owner APK available

- Verified code commit `a41d3d2099a818f4a25d71c119c713f85c17f35b`; the original `installOwnedResourceRouteTrial()` and `installExactRunModeWitness()` ordering is preserved for every clone process, including Passport. Observations remain read-only. Main process and separate `pro.celikom.yandex.nativeclonelab:passport` both use *same application package*; the Passport observer has its own bounded private log and no UI overlay. The main on-device download exporter merges it, and performs an Android 13 exit-reason snapshot on user tap. The target classifier distinguishes WIZARD / ENTRY / PASSPORT / MUSIC_OTHER without logging target class names, URLs or data.
- Paired publisher-first native ARM13 workflow [#43482793846](https://github.com/manufact-test/nomusic/actions/runs/43482793846) **SUCCESS**, original 25/25 and clone 25/25. Clone-only native ARM13 [#43482793526](https://github.com/manufact-test/nomusic/actions/runs/43482793526) **SUCCESS**, clone 25/25. Both test only idle MAIN foreground; **Passport onboarding itself is NOT tested or fixed.**
- Fresh paired private artifact **#14066561673**. Exact signed owner APK `CELIKOM-A1-NAV4-Passport-Witness-20261113.apk`: **71,434,220 bytes**, **SHA-256 `ec8b5add1c3505b731c0608c9954f06b08b131d87f132f50a5c95b644c7085e7`**. Verified exact zip member and nested LSPatch module DEX markers `NAV_V4_PASSPORT_WITNESS`, `PASSPORT_PROCESS`, `EXPLICIT_OWN_PASSPORT`, `EXIT_PROCESS_FAMILY`, `DIAGNOSTIC_EXIT_SNAPSHOT`, and the visible Russian button `Диагностика NAV4`.
- Uploaded and verified in user's Library: `/CELIKOM/CELIKOM-A1-NAV4-Passport-Witness-20261113.apk`.
- Next owner step: uninstall **only** old disposable NAV3 CELIKOM clone because CI temporary signatures differ; keep original Yandex installed, install NAV4 APK, confirm top-right `Диагностика NAV4`. Repeat one onboarding transition; if task closes, reopen clone and tap button **once**, send TXT from Downloads/CELIKOM A1. No USB, ADB, PC, password, account details or another video required. If login opens successfully, this is welcome but needs a separate logged-in/playback acceptance before any audio claim.
- Protected original known-good Firebase backup `backup/android-a1-firebase-namespace-success-witness-20261113` untouched; additional pre-change reserve `backup/android-a1-nav3-owner-runtime-before-passport-observer-20261113` at `7b6d9f3bbadc2d6341cadbc8441d7cb304f126b3`. No changes to Test.50, original Yandex, production, Windows or native B42 audio; no product release.

## 13 Nov — NAV4 owner phone: definitive Passport subprocess crash

Owner files: SVID_20261113_215824_1.mp4 (55.49s) and CELIKOM-A1-Diagnostics-1794596358589.txt (407 event records). The correct NAV4 running on the phone is proven by event #3 DIAGNOSTIC_BUILD/NAV_V4_PASSPORT_WITNESS/ACTIVE. The video confirms intro -> auth loading -> Android launcher -> fresh intro after a second launch.

Root-cause boundary established:
- #285-288 and #303-306: the vendor intro explicitly attempts to open EXPLICIT_OWN_PASSPORT in the clone package; Android startActivity returns normally, not proof the Activity became usable.
- #349-362 at owner export: Android ApplicationExitInfo records FOUR JAVA_CRASH exits belonging to pro.celikom.yandex.nativeclonelab:passport, all within five minutes. These are not MAIN process crashes.
- #364-407: the private Passport log proves FOUR repeated process sessions. Each has PASSPORT_PROCESS/APPLICATION_READY and APP_LIFECYCLE ENTER/RETURN, an uncaught IllegalStateException on another thread, FATAL_DISPATCH/NOT_METRICA and PROCESS_KILL/KILL_TARGET_SELF. Several sessions create a vendor Activity. This is conclusive that :passport actually crashes; prior main-only logs could not capture it.
- The exception message/cause and stack site remain UNKNOWN: NAV4 intentionally stores no message or stack. Do not speculate that signing, providers, Firebase or credentials are the root cause, and do not bypass authentication or app-signature protections.

For a single bounded next diagnosis, experimental NAV5 source 0851e384101e2bc21a16043350e1cfed24b0d97d adds fatal-only Passport exception/cause categories, fixed lexical message hints and max ten SHA-256 class#method frame fingerprints per cause level. The file does NOT store message text, class/method names, credentials, tokens or URLs; the original fatal execution is untouched. UI marker Диагностика NAV5; persisted DIAGNOSTIC_BUILD/NAV_V5_PASSPORT_FATAL_CAUSE. Resolve fingerprints against the exact 2025.10.4 embedded original DEX in a private environment, not by guessing from generic errors. This is diagnostic only and requires both ARM13 CI gates before owner use.

Safety reserve before NAV5: backup/android-a1-nav4-real-passport-illegalstate-owner-proof-20261113 @ fed35ede4acdbf2ea9e9c9c0405fa517aa4d1e53. Firebase known-good, original Yandex, B42, Test.50, Windows and production remain unchanged. Native ARM13 idle 25/25 is still not an onboarding/login/music acceptance test.

### NAV5 exact CI verification and private APK export — 13 Nov

- Source code 0851e384101e2bc21a16043350e1cfed24b0d97d adds fatal-only Passport message hint categories, cause-family categories, 10 SHA-256 code-symbol fingerprints per Throwable/cause (no raw messages, class names, account data, URLs or tokens); UI Диагностика NAV5 and diagnostic identity NAV_V5_PASSPORT_FATAL_CAUSE. This does not alter throwable handling or any Passport login logic.
- Native Android13 paired publisher-first workflow #43488933870: SUCCESS, publisher 25/25 and CELIKOM clone 25/25 idle startup. Clone-only #43488933817: SUCCESS, 25/25 idle startup. No onboarding navigation, authorization, playback or audio substitution accepted by these tests.
- Exact paired artifact #14069052056. Downloaded ZIP passed CRC. Extracted user APK name CELIKOM-A1-NAV5-Passport-Fatal-20261113.apk, 71,438,316 bytes, SHA-256 d0d0d52f44f5a62cfcbcf8e34ed6d0b239dae31117ba8c6a5876e3303801af37. Nested LSPatch observer APK verified to contain NAV_V5_PASSPORT_FATAL_CAUSE and PASSPORT_FATAL_TYPE/HINT/FRAME markers.
- Uploaded and independently verified exact APK in Library at /CELIKOM/CELIKOM-A1-NAV5-Passport-Fatal-20261113.apk. Prior NAV4 APK and pre-NAV5 full snapshot remain intact.
- Owner next: uninstall only previous diagnostic NAV4 clone (ephemeral signing key differs), keep original Yandex installed. Install NAV5, verify top button Диагностика NAV5, repeat last intro arrow ONCE, then after exit reopen and tap button; send the single TXT. No new video, cable, ADB or credential. If sign-in succeeds, preserve and report instead of repeated recreation. The next step is matching short SHA-256 stack fingerprints against exact preserved 2025.10.4 original DEX, which was locally validated with the LoginRouterActivity#onCreate fingerprint 5F37181A47977002 -> classes5.dex. Find and fix only the actual cause, without changing Yandex account checks.

### NAV5 fingerprint resolver — verified against the exact embedded original

The fingerprint algorithm in `ExitCallsiteWitness` hashes the Android runtime symbol string `StackTraceElement.getClassName() + "#" + getMethodName()` as UTF-8, then emits the first 8 SHA-256 bytes as 16 uppercase hex characters. Runtime class names use dotted Java notation; do not hash the DEX descriptor form with `/` and `;`.

Independent local verification was performed against the actual `assets/lspatch/origin.apk` extracted from the exact NAV5 APK above. That embedded original is Yandex Music 2025.10.4 and contains six DEX files (`classes.dex` through `classes6.dex`). The known symbol `com.yandex.passport.internal.ui.router.LoginRouterActivity#onCreate` hashes to `5F37181A47977002` and was found in `classes5.dex`. This verifies the resolver algorithm and exact DEX provenance; it does **not** identify this method as the crash cause.

On receipt of the owner's NAV5 TXT, resolve every `PASSPORT_FATAL_FRAME` token privately against all six DEX method tables, preserving cause depth and frame order. Prefer a tiny local resolver over emitting raw publisher class/method names into GitHub Actions logs. Distinguish a matched frame from a proven throwing frame: stack order and exception/cause relationship matter.

## NAV5 owner-phone exact fatal result — 13 Nov 22:25 local

Source: owner video `SVID_20261113_222512_1.mp4` (58.17 sec) and owner TXT `CELIKOM-A1-Diagnostics-1794597969944.txt` (506 lines); NAV5 marker `NAV_V5_PASSPORT_FATAL_CAUSE / ACTIVE` was present. After the four native intro cards, an explicit own Passport launch returned; the separate `:passport` process crashed. The video shows a return to the launcher and repeated intro on re-open. This is not Firebase/Push and not an idle-main startup failure.

The merged Passport log contains **five** uncaught `ILLEGAL_STATE` crashes, each `PASSPORT_AUTH`, same ordered three fingerprints:
- `D0_F0_PASSPORT / SYM_BA2F2F8F515934E8`
- `D0_F1_PASSPORT / SYM_0B7BA9643E8EF47C`
- `D0_F2_JAVA / SYM_9B2283F471456A56`
No `CAUSE_1` was captured. Android exit-info snapshot showed four recent `JAVA_CRASH` entries for Passport. The five log entries and four exit-info entries are independent windows, not conflicting crash totals.

Locally matched every frame across the **six exact embedded original 2025.10.4 DEX files** (317,558 method references). Both Passport frames matched uniquely in `classes5.dex`; the Java frame resolves to the normal `Thread.run` (two DEX references). The previously verified control fingerprint `5F37181A47977002` also matched once. No raw vendor method/class names or error strings were exported to public CI. The top frame creates an `IllegalStateException` in the Passport configuration validator and stores it in a fatal error list; a later initialization step throws the first list member. Thus the top stack frame is the exception **construction** site, not a bare DEX `throw` instruction.

The exact already-built NAV5 owned-outer `resources.arsc` has the Passport sync prefix but an authority ending in **the original** `ru.yandex.music` package, while the installed clone is `pro.celikom.yandex.nativeclonelab`. The current 2025.10.4 validator requires `prefix + current applicationId`. The static account type is already the expected production type and `android:allowBackup=false`, excluding the other initial fatal-list checks. The clone also rewrote the original SyncProvider manifest resource-reference authority into an unrelated generated literal while the sync-adapter XML still points to that original resource ID. These **configuration mismatches** explain the owner-observed `PASSPORT_AUTH` fatal; they are not an authorization/signature bypass.

**Narrow repair trial** commit `f05122cf01fbbfb1156d858053127a88ac7e2a74`:
- Preserve the SyncProvider's original manifest **resource reference** in the disposable own clone, so it resolves the same authority as the sync-adapter XML.
- Rebuild **one uniquely anchored string in clone-outer** `resources.arsc` to use the CELIKOM package, maintaining every other global string, table entry, inner original publisher APK, DEX, native library and resource-table package namespace.
- Independently re-sign with the same ephemeral **own** signer, verify exact three top-level v1 signing metadata differences only, zip parity, own signer equality and native library alignment. No vendor code, Passport return values, account secrets or original Yandex APK are changed.
- Separate tests run in paired original-first ARM13 and standalone clone-only workflows on this commit. **No native result or owner login success is claimed until the exact workflows finish and the owner tests the new APK.** Do not create or offer an unverified APK.

Saved protective exact pre-fix snapshot: `backup/android-a1-nav5-owner-passport-crash-proof-pre-fix-20261113` @ `ab8537253fdd9e361c630a92caeee78472d3fea9`. Previous owner handoff backup also remains untouched. Stage A still NO-GO; Stage B LOCKED. Test.50, Windows, production, backend and official Yandex untouched.
