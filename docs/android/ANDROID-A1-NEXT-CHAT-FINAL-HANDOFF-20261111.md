> **11.11.2026 AFTER ART/sampling investigation — DO NOT REPEAT BLINDLY:** [complete true ARM13 ART research and 8-MiB overflow analysis](ANDROID-A1-ARM13-ART-TRACE-CAPACITY-AND-NONCAUSAL-EXCEPTION-20261111.md). [Method ART CI 43007210075](https://github.com/manufact-test/nomusic/actions/runs/43007210075) had 73 passing tests and a real 599,184-record trace showing `YMApplication.attachBaseContext` entered+returned on MAIN and one background `IllegalStateException` constructor with immediate Android runtime caller, but **no proven relationship to exit**. Exactly 599,184 v3 × 14 bytes plus 32-byte ART header saturates **default 8 MiB**; ART explicitly reports `data-file-overflow`, and non-streaming ART stops recording subsequent events when full — missing later `onCreate/System.exit` is **not evidence of absence**. [Overflow test CI 43011106033](https://github.com/manufact-test/nomusic/actions/runs/43011106033) 77 tests PASS, [owned sampled-stack CI 43011741044](https://github.com/manufact-test/nomusic/actions/runs/43011741044) 79 tests PASS; both still clone MAIN `EXIT_SELF(0)`, sampled trace zero bytes, unchanged signed original alive. User APK **NO-GO**. Source and backup: canonical A1 branch (read-only documentation changes only), `backup/android-a1-before-art-trace-handoff-20261111` @ `6f47224390f80fb9e6aea44616e27de3113ba929`; isolated method-trace experiment `experiment/android-a1-arm13-shell-profiler-no-bypass-20261111`, isolated sampling experiment `experiment/android-a1-arm13-sampled-stack-only-20261111`. **Neither profiler code branch is promoted into the product**. Never contact Yandex (owner veto). Stage A still NO-GO, Stage B locked.

> **Latest native ARM13 chronology, 11.11.2026:** [Merged one-pass logcat timeline CI #43003533643](https://github.com/manufact-test/nomusic/actions/runs/43003533643) — 54 tests PASS, native strict clone MAIN gate FAIL/NO-GO. Exact MAIN IllegalStateException error occurs before death in both cycles of the five-split and direct merged clones; LSPatch0 merged logcat chronology was non-monotonic, so temporal order not asserted there. Original publisher-signed MAIN remains alive without matching error in bounded observation. [Detailed evidence + next ART lab-only method trace](ANDROID-A1-ARM13-MERGED-LOGCAT-TIMELINE-20261111.md). No Yandex outreach, Play Protect weakening, credentials, or owner APK. Research backup before ART: `backup/android-a1-true-arm13-merged-timeline-pre-art-profile-20261111` @ `df5037fb2cbbc74e440dae5d88964960f0589ddb`.

> **NEW FINAL 11.11.2026 ARM13 PROCESS-EXACT STARTUP PROOF:** [CI 43001833178](https://github.com/manufact-test/nomusic/actions/runs/43001833178), exact native A1 source `4d79ef03e70845d6d7be6c3cada6fb8d4f058f9b`, **47/47 tests pass**, true ARM13 runtime strict product gate still FAIL. Across three separately signed clone layouts, every one has **two distinct exact-MAIN fresh PIDs**, each with `am_proc_start → am_proc_died`, `EXIT_SELF(0)`, and *same-PID* E/F `IllegalStateException` logging. Signed original is alive after one MAIN start with no MAIN death and without observed IllegalState marker. EventLog parser now follows exact AOSP processName fields (excludes :AppMetrica false positives), not arbitrary package-text matches. **This is a reproducible correlation, not a proven causal instruction, signature check or working clone.** [Complete reproducible report](ANDROID-A1-ARM13-EXACT-MAIN-DOUBLE-EXIT-DIFFERENTIAL-20261111.md). NO user APK, NO Phase B. Owner explicitly forbids unsolicited Yandex outreach. Do not repeat layouts merely to gather identical counters; move only with genuinely new, safe causal evidence.

> **NEW VERIFIED ENGINEERING RESUME 11.11.2026:** [True ARM13 exact MAIN IllegalState read-only witness](ANDROID-A1-TRUE-ARM13-FRESH-MAIN-ILLEGALSTATE-READONLY-20261111.md), code `b4ba630adbe6d5f73549059c035c672767a37c23`, [CI 42999367827](https://github.com/manufact-test/nomusic/actions/runs/42999367827): 38 tests PASS; fresh-only MAIN PID logs all 3 independent clone layouts show logged `IllegalStateException` before `EXIT_SELF(0)`. No Java/native crash, no exception stack frames, **not proven causal**, original signed MAIN alive. ARM13 events buffer lacks am_* tags even for surviving original — no inference from absent events. No user APK or Phase B. Backup before change `backup/android-a1-before-arm13-readonly-startup-diagnostics-20261111` @ `da87689e70ca2b268b066b3dd2f9e78b5c7085f1`. **Owner explicitly rejected any Yandex outreach as next step**. Do not propose or send partner contact; keep working the agreed native CELIKOM architecture within safety constraints. Previous licensing-contact language below is historical research, not a user-approved action.

# CELIKOM Android A1 — FINAL HANDOFF FOR NEXT CHAT — 11 November 2026

**This is the authoritative resume page.** The approved architecture has NOT changed. Read this first, then the approved master TZ, triple-layout proof, partner feasibility, and README. Historic notes in the older NEXT-CHAT remain available but are not the current status.

## Repository, requirements, stage gates

Repository manufact-test/nomusic, working branch experiment/android-native-a1-lspatch-clone-loader0-20261111. Canonical approved specification: docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md.

The user's required Android product is ONE independently installed, independently signed CELIKOM APK containing the **actual native Yandex.Music UI**, login, MyWave, library/playlist and the **original single Yandex audio decoder**. Licensed/approved replacement audio must be selected within that decoder, never by adding a second engine. Original publisher-signed Yandex must coexist safely and remain untouched. **No WebView substitution, second playback engine, external player, rooting, second device, or Play Protect disabling.**

Stage A is pinned upstream LSPatch feasibility to a real audible owner-accepted source swap and frozen rollback APK. Stage B is the custom independent injector, **only after actual owner acceptance of Stage A**; proactively remind owner at that checkpoint, not now.

## Actual verified results

The disposable CI guest is real ARM64 Android13 / API33 Redroid on ARM Linux, with ARMv7 32-bit support. NOT x86 NativeBridge.

| Evidence | Verified result | GitHub Action |
|---|---|---|
| OWN native ARMv7 app with pinned LSPatch sigBypassLevel 0 and one read-only LibXposed module | PASS: hook executed in OWN process, MAIN alive, Activity resumed | https://github.com/manufact-test/nomusic/actions/runs/42987483624 |
| Unmodified original Yandex 2026.10.3 #170gpr publisher-signed FIVE splits | PASS: installed, MAIN alive, Activity resumed | https://github.com/manufact-test/nomusic/actions/runs/42990078186 and https://github.com/manufact-test/nomusic/actions/runs/42991987794 |
| Independently signed FIVE-SPLIT clone without LSPatch | **NO-GO**: MAIN briefly runs and Activity resumes, then MAIN reports EXIT_SELF with status ZERO | https://github.com/manufact-test/nomusic/actions/runs/42991987803 |
| Independently signed ONE merged clone APK without LSPatch | **NO-GO**, same EXIT_SELF(0) | https://github.com/manufact-test/nomusic/actions/runs/42991348866 |
| Same merged clone with LSPatch 0 / zero modules | **NO-GO**, same EXIT_SELF(0) | https://github.com/manufact-test/nomusic/actions/runs/42991987803 |
| Documentary Stage-A/owner acceptance release gate | PASS as **audit**, reports product STAGE_A_RELEASE_NO_GO | https://github.com/manufact-test/nomusic/actions/runs/42994205737 |
| Native ARM13 Redroid clean boot with bounded recovery | PASS; supports 2 clean attempts, observed successful initial boot | https://github.com/manufact-test/nomusic/actions/runs/42994395668 |

The clone CI 42991987803 is intentionally workflow FAILURE due to strict native clone MAIN gate. It ran ALL 3 cases on successful rerun; its first attempt had a transient Redroid boot problem. Every clone briefly started, then voluntarily exited with code 0, **NOT a Java/native crash**. The signed original ran. No single-APK merge nor LSPatch is a necessary cause. Specific publisher security/identity reason is **NOT proven**: both package identifier and certificate differ. Do NOT claim definitive signature integrity failure.

Earlier Android11 x86-native ARMv7 translation SIGSEGV and EM_386/EM_ARM ELF mismatch are closed testing-environment issues, NOT relevant to native ARM13. No more ungrounded emulator alignment, synthetic source swap, layout or signature-bypass attempts.

## Current blocker and next engineering block

The independent Yandex native MAIN/UI is **NO-GO**, no releaseable Android APK. Login, MyWave, single-engine licensed audio swap, pause/seek/next, user acoustic acceptance, stock HONOR Play Protect have NOT been tested.

1. Read docs/android/CELIKOM-ANDROID-NATIVE-CLONE-MASTER-TZ-20261110.md; docs/android/ANDROID-A1-ARM13-THREE-CLONE-LAYOUTS-EXIT-SELF-NO-GO-20261111.md; docs/android/ANDROID-A1-PUBLISHER-SUPPORTED-INTEGRATION-OPTIONS-20261111.md; android/native-yandex-hooklab/README.md. Verify GitHub working HEAD and backups.
2. Further investigation must use **legitimate read-only** Android package/lifecycle public instrumentation or a publisher-authorized integration; no new repack/re-sign carousel. Only publish fixed-category, scoped privacy-safe diagnostics; no raw vendor/account data.
3. Public Yandex job descriptions mention an **internal SDK for other Yandex apps**, which is not evidence of a public SDK or external permission. Mobile software license limits modified and commercial redistribution without written consent, with applicable statutory exceptions. A draft official licensing/partner question is stored in the publisher-options doc; owner has NOT requested it to be sent.
4. If full native Yandex UI with separately signed app is not available through authorized means, escalate **architecture blocked by publisher/rights**, obtain explicit owner's product decision. Never silently replace the agreed architecture with WebView, Media3 or two apps.
5. Only if lawful native MAIN + native UI + untouched publisher co-install succeeds can auth/MyWave, actual original decoder, licensed same-engine audio, pauses/seek/next, Play Protect ON and audible owner test resume.

GitHub blocker: https://github.com/manufact-test/nomusic/issues/41 (keep OPEN). Gate source android/native-yandex-hooklab/native_clone_stage_a_evidence_gate.py, evidence docs/android/CELIKOM-ANDROID-A1-STAGE-A-EVIDENCE-20261111.json, unit tests android/native-yandex-hooklab/tests/test_native_clone_stage_a_evidence_gate.py, workflow .github/workflows/android-native-a1-stage-a-evidence-gate.yml. Current expected CLI result is STAGE_A_RELEASE_NO_GO; --require-release-ready MUST exit nonzero until all prerequisites are actually verified. Documentation consistency audit is not device or copyright authorization.

## Exact frozen source, backups and untouched systems

- Exact TRUE ARM triple-layout tested SHA 7c894ebe02e9b4ff1bc42f7a039e7f259e2e979d and backup/android-a1-native-arm13-three-layout-clone-exit-self-proven-20261111.
- Before this latest evidence-gate block: backup/android-a1-before-stage-a-readiness-hard-gate-20261111 at 8ea947c46cd926826b5047f67e58c179ead5cabb.
- Own ARM true-hook green: backup/android-a1-real-arm13-armv7-own-lspatch-hook-green-20261111 at 1390990fe3086c5690a8f0b2c33e5cc5dc2b00b9.
- Signed original ARM13 green: backup/android-a1-true-arm13-signed-yandex-original-and-owned-hook-green-20261111 at 06f2d237059c014c12548f85c5d67acf24e8ee00.
- Native research source: android/native-yandex-hooklab/clone_native_arm13_redroid_gate.py, clone_native_identity_phase2_ephemeral.py, clone_main_crash_buffer.py, native_arm13_signed_original_control.py; GitHub workflow .github/workflows/android-native-a1-arm13-clone-main-ab.yml.
- **IMMUTABLE user accepted Android Test.50** backup/android-test50-exact-source-owner-accepted-20261106 at 5d737d203a0b364b0cb4fd6886040b8bd0c6fbd1. Different audio architecture, don't conflate with native clone.
- **IMMUTABLE user accepted Windows W61 / 0.24.9** backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110 at 44e69d78b459ed512862819280ebdb8b3dbc7e7d.
- Do not modify Windows, browser extension, backend/production, old Android builds or user HONOR 50. Only the native A1 research branch and docs are in scope.

## No-go security boundaries

No user APK while MAIN/UI and Play Protect gates fail. No signer spoofing, LSPatch bypass 1/2, DRM/Passport interception, secret extraction, user-account testing, Yandex publisher code upload/distribution, third-party ChromaSync code re-use, root, Play Protect disabling, removing official Yandex or second phone. Redroid has no Google Play Services or Play Protect. Successful OWN-only hook is NOT proof of Yandex audio.

The next developer should work in large, meaningful blocks, report problem -> verified outcome -> remaining test -> blocker, preserve exact backups, and **not repeat** a known failed approach. Stage B reminder only after actual owner-approved, immutable, audible Stage A baseline.
