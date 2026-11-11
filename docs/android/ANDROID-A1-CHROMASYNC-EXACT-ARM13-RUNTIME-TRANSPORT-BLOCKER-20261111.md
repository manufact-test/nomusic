# CELIKOM Android A1 — exact ChromaSync 3.0.1 native ARM13 attempt, transport blocker

**Date:** 2026-11-11. **Product Stage A:** NO-GO. No change to native player contract, security checks, phone or accepted Test.50.

## What was truly verified this turn

- Original owner-uploaded `ChromaSync-Clone-3.0.1.apk` is available in the local chat sandbox, 102,572,843 bytes; `sha256=4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d`. Its previous full offline ZIP/manifest/DEX check remains documented in `ANDROID-A1-CHROMASYNC-UPLOADED-APK-LOCAL-VALIDATION-20261111.md`.
- Local chat sandbox **does not contain Android, ADB, Docker or /dev/kvm**. This is not an Android runtime.
- New isolated experiment branch `experiment/android-a1-chromasync-real-arm13-probe-20261111`, backup branch `backup/android-a1-chromasync-probe-preflight-20261111` at previous research SHA `b9d1b06497e031123804bb64ad36f4fca29a5a8a`.
- New non-invasive SHA-pinned diagnostic CLI `android/native-yandex-hooklab/ci/chromasync_exact_arm13_probe.py`: rejects wrong SHA, non-loopback guest, non-ARM13 and dirty Android image; checks actual Android install result, launcher activity and five observed live MAIN/Resumed states in a 16-second window. Distinguishes `INSTALL_FAILED_CONFLICTING_PROVIDER` and other Android installer errors. Supports **standalone** and **fresh guest stock-first** modes. It neither changes vendor app bytes nor touches authorization, player, signature, credentials or Play Protect.
- Synthetic tests `android/native-yandex-hooklab/tests/test_chromasync_exact_arm13_probe.py`: **8/8 passed** in [CI run 43055366507](https://github.com/manufact-test/nomusic/actions/runs/43055366507). This tests the observer, **not ChromaSync runtime**.
- New private-runner workflow `.github/workflows/android-a1-chromasync-exact-arm13-private.yml` reuses the existing genuine ARM13 Redroid guest; expects a private HTTPS source of the **same exact** APK, checks SHA256 before any installation, and can then compare the separate standalone run with a different clean signed-stock-first guest. Stock controls are pinned to the already used official 2026 five-split archive, exact SHA and publisher validation. No APKs are uploaded to GitHub artifacts, Git history or logs.
- **Actual observed CI:** `synthetic-not-runtime=SUCCESS`; `live-arm13=FAILURE` at first preflight with **`BLOCKED_NO_PRIVATE_APK`**. It did not boot Android, install or run ChromaSync, or start the official-stock coexistence run. It is explicitly **not** a failed Android app launch and not a runtime comparison.

## Why this cannot silently proceed

The exact uploaded 98 MiB APK exists **only** in the chat file sandbox. The connected GitHub API tools can create text source and workflows but do not stream this local binary into a GitHub Actions runner. The independently executable local sandbox lacks an ARM Android image/runtime, ADB and Docker. The public ChromaSync-Mobile repository provides descriptive text and Telegram instructions, **not a verified exact-SHA direct APK download**. We deliberately did not copy proprietary code, trust overrides, media or the 98 MiB competitor APK into version control or public CI artifacts.

For the already prepared *real* CI run, the **only unresolved dependency** is secure private transfer to the ephemeral runner: a HTTPS download URL stored as GitHub Actions secret `CELIKOM_CHROMASYNC_301_EXACT_URL`, containing the byte-identical APK, can be read only transiently in the job and is SHA-pinned. The URL is not configured in this repo at the time of run 43055366507; the job correctly fails rather than fabricate success. Do not ask owner to install on HONOR 50 or uninstall official Yandex.

## Competitor suitability caveat, independently of runtime

The exact uploaded ChromaSync clone manifest retains a global AppMetrica provider authority also expected in official Yandex; installer collision is possible with both apps. ChromaSync public installation instructions themselves warn that a modified app may require uninstalling the original because of signing differences. Its embedded LSPatch configuration includes `sigBypassLevel=2`, which is outside the approved CELIKOM non-bypass experiment; the competitor APK is **not** an authorized template to copy security behavior. Earlier real CELIKOM ARM13 runs showed the 2026 clone experiences signature-related exception / MAIN exit; that remains uncorrected.

## Stop rules and next checkpoint

1. Do not claim native UI, login, stock coexistence, replacement audio, MyWave, Play Protect or release PASS from a ZIP audit, unit test, clean install or CLI launch alone.
2. If private byte-identical APK becomes available in CI, run the branch workflow; record **exact** PackageManager outcomes and fresh MAIN/Activity samples for standalone and stock-first. Then review the result against the preexisting signed 2026 host failure without copying level-2 bypass or vendor modules.
3. If the only launchable behavior depends on evading publisher trust, keep Stage A NO-GO and ask for an explicit product/legal decision. Do not secretly change architecture to WebView, separate audio player, or require removing stock app.
4. Main A1 `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`, Test.50, Windows, extension, backend, production and owner's HONOR 50 remain untouched.

**Evidence link:** [CI 43055366507](https://github.com/manufact-test/nomusic/actions/runs/43055366507), new branch `experiment/android-a1-chromasync-real-arm13-probe-20261111`.


## Follow-up: genuine Android13 runner verified, false-positive crash-loop gate fixed

- [GitHub Actions 43060795087](https://github.com/manufact-test/nomusic/actions/runs/43060795087): actual GitHub-hosted ARM runner booted ephemeral Redroid Android13 successfully: `sdk33=true`, `native64=true`, `native32=true`, `second_clean_boot_attempt_used=false`. `pm list packages` was real and proved clean original/competitor guest; **NO competitor binary was present or executed.** Native empty-guest job **SUCCESS**. Live exact APK job **FAILED** at SHA-pinned private-input preflight `BLOCKED_NO_PRIVATE_APK`, before app install.
- Eliminated ADB dependency by using `DockerGuest` backed by `docker exec`, `docker cp` and guest `pm install`/ `pm install-multiple`. Tested command scoping and input restrictions. The official signed-stock verifier still specifically requires `aapt`/`apksigner`; those tools are prepared only **after** competitor-alone run using the previous official TLS-verified Ubuntu Ports + archive GPG bootstrap. This branch keeps the pinned vendor stock hash and signer verification unchanged.
- Improved MAIN survival gate: sixteen 1-second samples now require **the exact same MAIN PID** plus resumed Activity in all samples. Earlier PID-presence-only observations could misreport an automatic fast crash/restart as sustained running. The output never discloses raw PIDs. A stable PID and resumed Activity is a minimal lifecycle gate, **not a proof of visibly rendered UI or actual audio**.
- [GitHub Actions 43061191461](https://github.com/manufact-test/nomusic/actions/runs/43061191461): **13/13 synthetic classifier tests PASS**, including simulated process restart rejection and steady PID acceptance; genuine ARM13 **empty guest boot PASS**; live ChromaSync still **BLOCKED_NO_PRIVATE_APK**, not an Android app crash.
- Current isolated experiment code latest at `4971a22c0a5720e65087a20be3d2fdf153d060ec`. Do not merge this research scaffolding to main A1 until genuine competitor and signed-stock comparator evidence has passed appropriate gates.

**Honest remaining blocker**: need exact privately staged APK bytes in ephemeral runner. Neither the chat sandbox nor the GitHub connector provides a tool to stream the uploaded 102,572,843-byte binary into remote GitHub Actions; private URL secret `CELIKOM_CHROMASYNC_301_EXACT_URL` is not configured. Avoid committing/printing/transmitting competitor binary in Git, PR, issue, workflows or public artifacts just to work around transport.
