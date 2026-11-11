# Android A1 — ChromaSync exact APK native window witness (no UI content leak)

**11 November 2026.** Follow-up to [first real exact competitor ARM13 boot](ANDROID-A1-EXACT-CHROMASYNC-REAL-ARM13-BOOT-20261111.md). This is an observational research CI, **not** product Stage A acceptance.

**CI:** [43073971705](https://github.com/manufact-test/nomusic/actions/runs/43073971705), experiment `experiment/android-a1-chromasync-native-ui-witness-20261111` @ `0b4ddbaf6ad2347b14c1de6d3c61e168b0b55389`. 5 synthetic UI classifier tests + 13 existing probe tests PASS. Real native ARM13 Redroid boot PASS. Owner's exact ChromaSync APK SHA and size PASS from UNPUBLISHED GitHub Release draft, remains NOT published. Single guest standalone clone installed, explicit MAIN launch accepted, one MAIN PID alive / Activity resumed for all 16 observed seconds: **PASS**.

**Read-only OS window/screen details from real Android guest:**

- `contains_clone_window_line=true`: Android WindowManager knew a clone-owned window. This is additional positive evidence for native UI integration, not merely a process with no window.
- `screenshot_png_valid=true` with 720×1280 real native guest screen. Screenshot was **not** uploaded as an artifact or logged; only dimensions/header were inspected. PNG validity alone cannot prove the screen actually contains the Yandex UI rather than a splash.
- `window_focus_record_available=false`, `clone_focused_or_targeted=false`, `native_window_witness=false`: this bounded `dumpsys window windows` query did not expose recognized focus fields. It **does not** prove the app lacked focus; the observer did not have the required evidence.
- No `ui_hierarchy_decoded` or clone UI node count: `uiautomator dump` and file read in this guest did not yield a parseable XML hierarchy under the current observer. This does not prove the UI is absent.
- `user_account_used=false`, `audio_tested=false`, screenshot content unreported. No account login, MY WAVE, audio replacement, Play Protect, visual pixel contents or CELIKOM audio product function tested.

**Final honest interpretation:** Exact competitor native standalone Android MAIN and resumed Activity stable, WindowManager clone-window record observed and real screenshot obtainable. Actual visual screen content, focus and hierarchy still not proven. Avoid turning window-only evidence into native UI acceptance or acoustically functioning Yandex Music.

**Separately established:** [CI 43072904573](https://github.com/manufact-test/nomusic/actions/runs/43072904573) confirmed competitor native MAIN lives for 16s on real ARM Android13 **both alone and when the exact 2026 issuer-signed original is installed first**, without install conflict; earlier installer and implicit launcher test mistakes were fixed. The competitor's 2025 host, private module and LSPatch level 2 remain separate confounded variables, cannot be transplanted under the agreed no-security-bypass rule.

**Frozen checkpoints:** `backup/android-a1-chromasync-exact-live-arm13-both-pass-20261111` @ `6a6786ec34e7a9580b39dac56f226e44a256f5f4`; `backup/android-a1-chromasync-native-window-smoke-20261111` @ `0b4ddbaf6ad2347b14c1de6d3c61e168b0b55389`. Approved native A1 main `cc4cb0f93489168db21502f3ef195855ae9fb743`, Test.50, Windows, extension, server and HONOR unchanged.

**Next valuable work:** isolate authorized signed-2025-vs-2026 startup differences under no-bypass, then apply independent findings to CELIKOM native host. No repeats of same zero-bypass 2026 clone layouts or 8MiB ART trace. Keep Stage A NO-GO until CELIKOM itself starts and sound can be heard through one Yandex decoder.
