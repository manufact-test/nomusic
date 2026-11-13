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

## NAV5 Passport sync repair — native Android 13 results (13 Nov 2026)

Trial commit: `f05122cf01fbbfb1156d858053127a88ac7e2a74`.
Post-result backup: `backup/android-a1-nav5-passport-native75s-pass-20261113` @ `f13fbcaa3b2f3617a0db282d749c5a4ace3b6b8f`.

Both exact commit workflows completed SUCCESS:
- Clone-alone fresh Android 13: `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`; clone installed; native MAIN resumed in 25/25 samples (75 s); no uncaught exception / IllegalState; no fatal dispatch observed. Publisher intentionally absent in this differential.
- Publisher-first paired test: original issuer-verified Yandex 2025.10.4 installed first with all 16 splits and observed stable for 75 s; clone installed second alongside it; both remained installed; clone MAIN resumed in 25/25 samples (75 s). Verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. No uncaught exception / IllegalState and no fatal dispatch observed; no Metrica fatal suppression occurred.
- The clone-only trial and paired trial both ran with `CELIKOM_A1_PASSPORT_SYNC_TRIAL=1`, `CELIKOM_A1_RESOURCE_NAMESPACE_TRIAL=1`. Build output confirms `PASSPORT_SYNC_OWN_RESOURCE_PARITY_OK`; clone APK remained structurally single-APK, embedded original publisher APK byte-identical, original DEX/native payload unchanged, own signer unchanged, and only the three expected outer v1 signing metadata entries regenerated.
- This is strong evidence that the original NAV5 Passport fatal was configuration-related and the exact own-clone sync-authority alignment removed the observed startup crash in this 2025.10.4 / Android 13 test. It is **not** proof of account login, live audio routing, CELIKOM replacement, Play Protect behavior, or production readiness. No account or audio was tested; owner phone was not touched. Stage A remains NO-GO; Stage B remains LOCKED.
- Read-only witness also recorded a nonempty Push fatal guard input, but Push init returned normally; no uncaught fatal dispatch was observed. Do not mislabel this as a Passport crash.

### Private one-time owner-phone diagnostic bundle
- GitHub Actions run: `43496737566`; artifact `14072202508`, `CELIKOM-A1-OnDevice-Diagnostic-20261113` (7-day retention, expires 20 Nov 2026).
- Contains `CELIKOM-A1-Native-ReadOnly-Diagnostic.apk` (71,438,316 bytes) and `README-RU.txt`.
- APK SHA-256: `420aaa31c8a70f6acd8944ab25d693c16dab43caa136092325fef18297b94b07`.
- This is a **temporary diagnostic clone**, not a product/release APK. It contains the issuer-signed Yandex 2025.10.4 source clone plus the scoped read-only diagnostic module; it does not replace audio, create a second player, or perform song substitution.
- Owner test instructions are in the bundled `README-RU.txt`: install alongside the original Yandex (do not remove original), reproduce the four-screen startup path, relaunch after any return to launcher, tap “Сохранить диагностику”, and send the generated TXT. No cable, PC, ADB or USB debugging is required. Remove the previous diagnostic clone before installing this new APK because the test signing key changed. If Play Protect warns, do not disable protection or bypass it; report the warning.
- APK is locally downloaded and verified against the CI SHA-256 at `/mnt/data/celikom-a1-nav5-owner-test/CELIKOM-A1-Native-ReadOnly-Diagnostic.apk`; local README at `/mnt/data/celikom-a1-nav5-owner-test/README-RU.txt`.

Next: owner-phone reproduction and diagnostic TXT. If startup now passes, report that too; do not infer login/audio acceptance from the 75-second CI test. After owner confirmation, proceed to account/login check, then a separately gated audio test; keep Test.50 and production untouched.

## Owner phone 13 Nov 23:33 local — first successful Passport UI, Android AccountManager ownership block

Owner files: screenshot `Screenshot_20261113_233335.jpg` and diagnostic `CELIKOM-A1-Diagnostics-1794602027128.txt`. The screenshot shows `authorizeByCookie` failed with Android account ownership denial: `cannot explicitly add accounts of type: com.yandex.passport`. Do **not** publish the user's UID, screenshot diagnostic incident hash, phone/email, cookies, auth tokens or credentials. The owner reports all four introductory screens passed, the Yandex native account page loaded, and they completed the phone/email sign-in UI; the application then displayed this account-registration error. It is **NOT** proof that an Android account/session was saved or audio playback accepted.

Exact uploaded NAV5-like diagnostic (569 lines, `DIAGNOSTIC_BUILD NAV_V5_PASSPORT_FATAL_CAUSE ACTIVE`) corroborates full Passport UI lifecycle: under `PASSPORT_LOG_SECTION`, repeated `VENDOR_ACTIVITY CREATED / STARTED / RESUMED`; **no** `PASSPORT_FATAL_TYPE`, `UNCAUGHT` or `FATAL_DISPATCH`. The old five identical `ILLEGAL_STATE PASSPORT_AUTH` crashes are absent. Android exit-info for Passport is `USER_REQUESTED`, not `JAVA_CRASH`. The new failure is visible in the screenshot rather than the current finite diagnostic-event schema. `METRICA_DETAIL` occurs in one additional main process launch but has no observed fatal dispatch; do not claim it caused the login error.

System root: Android `AccountManager.addAccountExplicitly` checks whether the caller is the **registered authenticator owner** for the account type; it rejects independently signed clones claiming the publisher account type. Verified on the exact 71,438,316-byte prior APK: its embedded `AuthenticationService` service and `res/xml/authenticator.xml` use `@0x7f130919` (resolves to `com.yandex.passport`); `res/xml/passport_sync_adapter.xml` uses the same type. The original Yandex is installed alongside the clone. Thus the clone UID cannot create `com.yandex.passport` accounts while the original authenticator owns them. Also inspected six signed original DEX files: the account-type literal appears in one DEX and has several static uses; changing the XML alone is not guaranteed to fix all runtime consumers.

**Safe isolated repair trial** `ab636424bc6201053fb0d3d3a0585b9ffe0bf1f1`: in the **own-outer** clone resources only, replace the one uniquely anchored `com.yandex.passport` global string resource by independent namespace `pro.celikom.yandex.nativeclonelab.passport`, preserving both authenticator.xml and sync-adapter references and ensuring an authenticator **owned by CELIKOM**. Fail closed on source differences, alias collisions, unexpected strings or ZIP/signature drift. No publisher package/signature/account type impersonation, no access to original Yandex account, no forged login result or exception suppression, no password/token handling. The embedded genuine issuer-signed original APK, DEX and all code unchanged. The previous sync-provider authority fix stays in place. Env gate `CELIKOM_A1_OWN_ACCOUNT_TYPE_TRIAL=1`, together with the previous `CELIKOM_A1_PASSPORT_SYNC_TRIAL=1`, applies **only** to the two disposable ARM13 jobs.

Pre-fix backup: `backup/android-a1-postlogin-system-account-ownership-owner-proof-20261113` @ `95882125cef520c32f210ca3a83df8440cde01e7`.
Two native workflows for the new commit were triggered automatically: clone-only and original-first publisher/clone coexistence; **no PASS claimed until they complete**. Crucially, 75s MAIN stability and Android authentication success are different test gates. Next owner phone test must verify registration after the native Yandex account UI with no exception, then separately that the music interface launches. If the new account still fails, classify direct SDK account-type constant paths rather than expanding permission/signature bypass.

### Follow-up correction: a compiled 2025 Passport account type constant requires a scoped bridge

Offline owner-owned APK DEX inspection proved that the `com.yandex.passport` string is also present as a compile-time static String value in the original signed Passport classes, not just in the account-authenticator and sync-adapter XML resources. Several `Account(String, String)` constructor callsites in the Passport SDK read that same static value. **A resource-only remap is therefore insufficient and must NOT be sent to the owner as an account-login fix.** The isolated resource-only experiment is `ab636424bc6201053fb0d3d3a0585b9ffe0bf1f1`, which can establish static APK/native safety but cannot validate a real authenticated session. Keep this causal limit explicit.

Provisional clone-owned compatibility bridge added at `4b5b13471c1b74093dc098f626589e38b9b981ef`; NAV6 marker update at `5e7598ba6766dc9cb232632ff180176ec8284fa2`:
- Only inside the cloned CELIKOM MAIN and `:passport` processes, hook the standard `android.accounts.Account(String name, String type)` constructor and change the **type argument only when exactly** `com.yandex.passport` to the **independent clone-owned type** `pro.celikom.yandex.nativeclonelab.passport`. Do not inspect/log/change the account name, password, cookies or tokens; pass the new argument through the actual original Android constructor.
- When the same two clone processes call standard `AccountManager.getAccountsByType(String)` for the publisher type, query **only the clone-owned type** instead. Do not read or transfer publisher original Yandex accounts.
- The real Android `AccountManager.addAccountExplicitly` and signature/owner authorization checks execute unmodified. No fake result, no signature spoof, no native/issuer DEX modification, no interception of network credentials; all unrelated hooks stay read-only.
- The own-outer resource patch registers exactly the same own type in the cloned `AuthenticationService` metadata and sync-adapter, so Android is meant to treat CELIKOM as the real authenticator owner of only that clone-specific account type.
- Finite diagnostics `ACCOUNT_BRIDGE / CONSTRUCTOR|QUERY / OWN_TYPE` and `ACCOUNT_BRIDGE / REGISTERED / BOTH|CTOR_ONLY|QUERY_ONLY|NO_HOOK`. UI button `Диагностика NAV6`, marker `NAV_V6_OWN_ACCOUNT_TYPE`.
- An actual owner account-login flow, session, and media player still have **NOT** been tested with this NAV6 variant. Android13 75-second CI startup remains a necessary but **insufficient** gate. Only give an APK after the exact NAV6 paired+alone native jobs pass. If Passport still fails, do not assert authorization success or extend into vendor permission/signature spoof; inspect scoped type consumer before next build.

If owner can complete login, verify the Yandex Music main interface appears; no need to repeat login merely for extra diagnostics. If error returns, export bounded NAV6 TXT + a screenshot of the error (with account personal details hidden), and re-evaluate. Stage A NO-GO until owner testing; audio and B42 remain locked.

### NAV6 real native tests COMPLETE, owner test APK verified — 13 Nov 2026

- Code **`5e7598ba6766dc9cb232632ff180176ec8284fa2`**, own clone account resource + scoped real Android Account constructor/query namespace bridge, real framework ownership enforcement unmodified.
- Fresh standalone ARM13 Android13 [run 43505060731](https://github.com/manufact-test/nomusic/actions/runs/43505060731) **SUCCESS**: clone MAIN 25/25 samples / 75 seconds, `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`, own-account resource parity confirmed.
- Publisher-first paired [run 43505060927](https://github.com/manufact-test/nomusic/actions/runs/43505060927) **SUCCESS**: publisher stable 25/25, clone stable 25/25, both installed, `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, own-account resource parity confirmed. No audio or account login was tested in CI.
- Private one-time artifact **14076166766** `CELIKOM-A1-OnDevice-Diagnostic-20261113` at https://github.com/manufact-test/nomusic/actions/runs/43505060927/artifacts/14076166766 (7-day retention). APK source member `CELIKOM-A1-Native-ReadOnly-Diagnostic.apk`, **71,438,316 bytes**, SHA-256 **`6d4750682a95286874d77ca60368c596e9819ae9e78e705f0603f623b3c43cfa`**.
- Independently downloaded and verified exact APK digest, zip CRC, manifest package `pro.celikom.yandex.nativeclonelab`, account authenticator.xml and sync-adapter XML **same resource ID 0x7f130919**, resulting unique own resource value `pro.celikom.yandex.nativeclonelab.passport` (old `com.yandex.passport` no longer in the outer string pool), exact `NAV_V6_OWN_ACCOUNT_TYPE` module marker. Embedded signed publisher origin in NAV6 is SHA-256 **identical** to earlier NAV5 origin. No signed publisher original was altered or re-signed.
- Local verified owner APK: `/mnt/data/celikom-a1-nav6-owner-test/CELIKOM-A1-NAV6-Own-Account-20261113.apk`; instructions `/mnt/data/celikom-a1-nav6-owner-test/README-RU.txt`. These are current-turn paths only; future chats must not invent sandbox links without path verification.
- Owner next action: remove **ONLY** old CELIKOM diagnostic clone because disposable signer changes each build. Preserve installed original Yandex Music. Install NAV6 APK, verify `Диагностика NAV6`, proceed native intro and real Yandex Passport login once. **If login completes and native music interface launches**, report this; then test playback separately. If a new error appears, capture screenshot **without private credentials** and export bounded NAV6 diagnostic TXT. Do not turn off security protections or request ADB/USB/cables/passwords.
- The currently proven gate is native co-install/startup only. Real Android account registration/login, Yandex Music player, MediaDataSource replacement and B42 routing **not yet proven**. Stage A **NO-GO**, Stage B **LOCKED**.

## Owner regression NAV6 — 13 Nov 2026, exact static cause, and NAV7 fix trial

Owner new file `CELIKOM-A1-Diagnostics-1794604260123.txt` (489 event lines) and report: four intro pages advance, then CELIKOM returns to Android launcher instead of opening the real Yandex Passport sign-in. This is a **regression from NAV5**, which reached Passport login and later showed the Android account owner error. Do not mark NAV6 accepted.

The exact TXT has the expected `DIAGNOSTIC_BUILD / NAV_V6_OWN_ACCOUNT_TYPE / ACTIVE` marker, 2 main launches with multiple `EXPLICIT_OWN_ENTRY` plus one `EXPLICIT_OWN_PASSPORT` target, and the cloned `:passport` starts, runs its application, creates/resumes two vendor activities and then disappears. Android exit-info reports `PASSPORT / OTHER`, **not** `JAVA_CRASH`. No `PASSPORT_FATAL_*` or `ACCOUNT_BRIDGE` markers appear. The absence of `ACCOUNT_BRIDGE` cannot by itself prove installation failure because a registration emitted before the diagnostic file/context was initialized could be lost; NAV7 emits the registration **after** diagnostics prepare and installs at `Application.attach`.

**Exact original issuer-signed 2025.10.4 DEX validator inspection** (local, never publish binary or raw source) identified the regression root in the Passport configuration validator: when account type is not exactly `com.yandex.passport`, the SDK requires `accountType.startsWith("com.yandex.passport")`. It records `IllegalStateException` otherwise. NAV6 owned account type `pro.celikom.yandex.nativeclonelab.passport` violates that SDK contract. Other genuine Passport DEX routines also use that same prefix in account-type handling. NAV6 CI 25/25 only exercised MAIN idle, **not** this Passport path, so the previous green CI never proved phone onboarding success.

**NAV7 targeted fix** code commit `92ee935cbdc093cf587314615e78ec81ae1fa4f8`:
- Change the clone-owned AuthenticatorService + SyncAdapter account type to the strictly distinct string **`com.yandex.passport.pro.celikom.yandex.nativeclonelab`**, which satisfies the genuine SDK's checked prefix while **not being** the official original `com.yandex.passport` account type. Android's real authenticator ownership and signature checks remain enforced. Never forge or read original Yandex accounts.
- Keep existing safe Passport SyncProvider clone authority fix and separate correct own resource ID references. Keep all signed nested publisher APK/DEX untouched.
- Use this same independent prefixed type in two **scoped** own-process bridge methods forwarding to the real `android.accounts.Account` constructor and `AccountManager.getAccountsByType`; do not bypass `addAccountExplicitly` or forge return codes.
- Add earliest registration during `Application.attach` (including separate `:passport`) and explicit post-diagnostic `Application.onCreate` registration marker. New build marker `NAV_V7_PASSPORT_ACCOUNT_PREFIX` and `Диагностика NAV7`.
- Synthetic account-type tests require `startsWith('com.yandex.passport')`, **not equal** publisher account type, and **not** the `.wl` debug-only prefix.
- Two native ARM13 jobs run automatically from this exact commit; **do not claim success or release an APK until they complete**. They do not test live Yandex login. Stage A NO-GO / B LOCKED.

Regression reserve: `backup/android-a1-nav6-owner-regression-before-bridge-attach-fix-20261113` @ `00c4641f5ed388422817ff20bde1ef5314deeb22`. Existing previous proven NAV5 artifact and backups are untouched. Main production, official Yandex, Test.50, Windows, backend untouched. If NAV7 is exported after CI, upload its verified bytes **FIRST to Library `/CELIKOM/`**, verify the Library entry and display it through a Library file citation/card; **never give the user a sandbox download link** (explicit owner requirement).

### NAV7 native gates SUCCESS + verified owner Library delivery (13 Nov 2026)

Exact owner code: `92ee935cbdc093cf587314615e78ec81ae1fa4f8`.
- Clone-alone native ARM13 GitHub Actions run `43509552355`: SUCCESS, clone MAIN 25/25 foreground observations across 75s, `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`.
- Publisher-first side-by-side native ARM13 run `43509552388`: SUCCESS, original publisher and clone remain installed together, clone 25/25, `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- Exact owner APK artifact `14078526243` (run `43509552388`, seven-day retention). APK `71,438,316` bytes, SHA-256 `583df0afb70e08057cae579df78aa2cccdd5dc53bbafdd818c1e3ba278548d17`. Artifact ZIP verified independently, ZIP CRC checks PASS, APK SHA matches native build report. Manifest package is `pro.celikom.yandex.nativeclonelab`.
- Parsed exact final `resources.arsc`: `com.yandex.passport.pro.celikom.yandex.nativeclonelab` occurs **exactly once**, `com.yandex.passport.sync.pro.celikom.yandex.nativeclonelab` occurs once, stock `com.yandex.passport` resource value absent, and prior NAV6 incompatible `pro.celikom.yandex.nativeclonelab.passport` value absent. Embedded original signed Yandex APK `assets/lspatch/origin.apk` is SHA-identical to NAV6, so original vendor source was not altered.
- Exact own module contains `NAV_V7_PASSPORT_ACCOUNT_PREFIX` marker. Diagnostic UI button `Диагностика NAV7`.
- **Uploaded first to the user's personal persistent Library**, then Library entry and 71,438,316-byte size verified by `files__list`: `/CELIKOM/CELIKOM-A1-NAV7-Passport-Account-20261113.apk` with instructions `/CELIKOM/NAV7-Инструкция-проверки-входа-20261113.txt`. Shared with user only as **Library file cards/links**, not sandbox.
- New NAV7 owner phone test still PENDING: does native Passport login appear after four intros? If yes, test sign-in and Android account ownership once; if no, submit NAV7 diagnostic TXT. Only after real sign-in and normal Yandex Music screen proceed to playback and then B42. No owner login/audio/product accepted by CI. Stage A **NO-GO**, Stage B **LOCKED**.

## 14 Nov 00:42 (+03) — owner NAV7 reaches ID code but loops to four-screen onboarding; NAV8 read-only triage

Owner symptom (one bounded account sign-in flow): NAV7 shows the four intro screens, the Yandex account sign-in screen, and accepts a one-time code entered via the Yandex ID app. The previous `authorizeByCookie cannot explicitly add accounts...` dialog **does not appear**. Instead a loading screen occurs and app returns to the four original intro screens. After repeating intros, the account is remembered in the sign-in UI, but selecting it repeats the same cycle. **This is not successful persistent session/login and is not a working music UI.**

Exact NAV7 TXT uploaded `CELIKOM-A1-Diagnostics-1794606106566.txt` (445 event lines). Marker `NAV_V7_PASSPORT_ACCOUNT_PREFIX` is correct. Both clone MAIN and `:passport` report `ACCOUNT_BRIDGE / REGISTERED / BOTH`. MAIN records **two** `EXPLICIT_OWN_PASSPORT` targets with `ACTIVITY_START_RESULT RETURN`. The Passport process reports multiple vendor activities progressing CREATED/STARTED/RESUMED then PAUSED/STOPPED/DESTROYED_FINISHING; no `PASSPORT_FATAL_*`, uncaught exception, Process kill, fatal dispatch, or JAVA_CRASH. Android exit snapshot `PREVIOUS_EXIT_INFO NONE`. **Zero** `ACCOUNT_BRIDGE CONSTRUCTOR` or `ACCOUNT_BRIDGE QUERY` events were logged, but those prior hooks only reported exact *publisher-type remaps* and not already-own-type objects, so absence does **not** prove the SDK skipped Android AccountManager operations.

Read-only static original Yandex 2025.10.4 classes5.dex inspection isolates `com.yandex.passport.internal.core.accounts.p#if`: builds an `android.accounts.Account` from the SDK's configured account type, calls real `AccountManager.addAccountExplicitly(Account, String, Bundle)`, records the real boolean result, and separately uses `getAccountsByType` and `getAuthenticatorTypes`. It also maintains private local account row state. These are **candidate loss/restore boundaries**, not an established failure site. There is also a possible external Yandex ID activity-result/navigation handoff; no exact cause yet.

NAV8 source diagnostic-only change `17430e30c56930169f66d749d031817c77bce342` keeps the NAV7 owned account type `com.yandex.passport.pro.celikom.yandex.nativeclonelab`, signed original Yandex bytes and all existing account-bridge functional behavior unchanged. Adds bounded categorical events in only clone MAIN and :passport:
- `ACCOUNT_BRIDGE REGISTERED BOTH_PLUS_ADD_OBS` if real Android add hook armed
- `ACCOUNT_ADD / CLONE_OWN|PUBLISHER_TYPE|PASSPORT_OTHER|OTHER_TYPE / ADDED|NOT_ADDED|DENIED|THREW`, forwarding the **actual original** Android method and result, no fake success
- `ACCOUNT_QUERY / type family / ZERO|ONE|MULTIPLE|DENIED|THREW` (array length only)
- `ACCOUNT_STATE / CLONE_OWN / ZERO|ONE|MULTIPLE|DENIED|UNAVAILABLE` on bounded Activity resumes; `ACCOUNT_OWNER OWN_PRESENT|OWN_ABSENT / PUBLISHER_PRESENT|PUBLISHER_ABSENT` by Android AuthenticatorDescription type and package equality only
- `ACCOUNT_CTOR` records type family only for non-remapped constructor; `ACCOUNT_BRIDGE CONSTRUCTOR STOCK_TO_OWN` for the original remap
- `ACTIVITY_RESULT` result OK/CANCELED/OTHER without reading Intent extras plus Passport-process ACTIVITY_START / ACTIVITY_FINISH and finite category markers
- `NAV_V8_ACCOUNT_COMMIT_LOOP_WITNESS` exact diagnostic marker and `Диагностика NAV8` UI.
- No account names, phone/email, passwords, OTPs, tokens, cookies, Intent data/URLs, raw exceptions, or private rows are logged. No authorizations bypassed, and the original publisher and Test.50/Windows/backend/production untouched.

Native Android13 standalone and publisher-first paired workflows were started for NAV8 diagnostic; only CI success can authorize **one** owner APK export, not claim login success. User expects APK delivery **in Library `/CELIKOM/`** and a Library file card/link, NEVER a sandbox link. Do not ask owner to repeat a failed sign-in loop multiple times: **one** traversal, then TXT if still cycles. If after accepting Yandex ID code the main music screen actually appears, stop investigating and record real owner result.

### NAV8 completed native gates, exact artifact and verified Library delivery — 14 Nov 2026

- Final diagnostic source code `dd58c2eb484e5fd64b63c6973c41b69f3e16523c`. Separate account-add/query/ctor/registry event caps ensure early lifecycle calls **cannot** consume the decisive `ACCOUNT_ADD` budget after user enters an OTP. Both public `Activity.setResult` overloads are observed. Marker `NAV_V8_ACCOUNT_COMMIT_LOOP_WITNESS`; button `Диагностика NAV8`.
- Clone-alone native ARM Android13 run **43514767582 SUCCESS**, clone MAIN foreground 25/25, `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`.
- Original publisher-first native ARM Android13 run **43514767757 SUCCESS**, original publisher stable 25/25 before own clone, both installed, clone MAIN foreground 25/25, verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`. No actual Yandex account, OTP, login, song playback or audio replacement tested by CI.
- Private one-time GitHub artifact **14080697408** from paired run (7-day retention). APK 71,438,316 bytes; SHA-256 **`592c9c93dbf41a44503982989e1088de80da5f7bf78161fa2f04613f7df6da73`**. Artifact ZIP and APK CRC verified locally, SHA-256 matches exact workflow report, embedded diagnostic module contains NAV8 build marker and ACCOUNT_ADD observer; embedded untouched signed 2025.10.4 Yandex `assets/lspatch/origin.apk` SHA **`1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`** matches NAV7.
- User-requested personal Library upload completed FIRST, exact paths verified using `files__list`: `/CELIKOM/CELIKOM-A1-NAV8-Account-Loop-Diagnostics-20261114.apk` 71438316 bytes; `/CELIKOM/NAV8-Инструкция-проверки-цикла-входа-20261114.txt`. Only Library cards were offered, **no sandbox links**. Exact Library IDs: APK `libfile_fb32c37216608191adacb93eb850c349`, README `libfile_3da1b1bd1ac48191bd44f232a08a9772`.
- Exact current owner TEST still PENDING. User uninstalls **only** previous disposable NAV7 clone, keeps official Yandex, installs NAV8, follows one bounded sign-in if needed, stops after first repeat, exports TXT via NAV8 button. Must never request/capture account names, passwords, code, tokens, video of credentials or ADB.
- Root-cause decision after TXT: `ACCOUNT_OWNER OWN_ABSENT` -> own Android authenticator registration; `ACCOUNT_ADD PUBLISHER_TYPE/DENIED` -> stock-type call escaped bridge; `ACCOUNT_ADD CLONE_OWN/ADDED` + `ACCOUNT_STATE ZERO` -> persisted visibility / account restore; `ACCOUNT_STATE ONE` but UI loops -> Passport-to-main result/routing or local session state. **Do not claim any of these diagnoses before actual owner TXT evidence.**
- Protect prior working progress: NAV7 backup `backup/android-a1-nav7-owner-login-loop-diagnostic-20261114` @ `2fcb3b8d102e8d60b907648a580dc5f87f27747d`; first NAV8 intermediate `backup/android-a1-nav8-pre-per-operation-event-budgets-20261114` @ `17430e30c56930169f66d749d031817c77bce342`. Stage A NO-GO, Stage B LOCKED.
