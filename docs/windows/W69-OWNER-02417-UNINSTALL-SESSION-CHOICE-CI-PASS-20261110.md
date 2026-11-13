# W69 — Windows 0.24.17: optional removal of saved login during uninstall (2026-11-10)

## Request
Owner installed prior W68 0.24.16 after deleting older Windows CELIKOM but remained logged in; this is by design, as Inno uninstaller intentionally retained Windows user-bound DPAPI file `%LOCALAPPDATA%\CELIKOM\Windows\session.dpapi`. Owner explicitly requests a user-facing checkbox **«Также удалить сохранённые данные входа»** in the *normal interactive CELIKOM uninstall*, then will install, uninstall (checking the option), and install anew to validate first-customer sign-in. Do not change trial clock, paid accounts, audio engine, signed URLs, vendor Yandex, or Android.

## Exact immutable code
- Main experiment branch: `experiment/windows-w69-uninstall-login-choice-20261110`.
- Exact W69 private tested binary source: `da046739d1be008dbc1a9db00bce29ce8867a635`, frozen as immutable backup branch `backup/windows-w69-02417-uninstall-login-choice-ci-pass-20261110`.
- Source changes only: `windows-companion/w20/installer/CELIKOM.iss` option UI, metadata version 0.24.17 in `w15/Celikom.Companion.csproj`, `w23/host.cjs` and matching updater tests. All W68 authorization/3-day trial/fail-closed signed playback functionality unchanged. Single AppId `D99FDB90-46BF-4EE5-989E-659A2B6450D6` unchanged.
- Uninstall form: `CreateCustomForm(480, 194, True, True)` (Inno Setup 6.6+ syntax), centered native `TNewCheckBox`, checked=false by default. `Continue`/Cancel. Cancel aborts uninstall before any restore or deletion.
- Interactive check only selects whether `session.dpapi` will be removed **after successful native Yandex restoration + uninstallation**. No recursive deletion of `%LOCALAPPDATA%\CELIKOM`; unrelated files preserved. Other Windows accounts unaffected. The *server* trial/subscription/promo for an email remains unchanged. Silent uninstall preserves as before. Explicit non-interactive `/CELIKOMREMOVELOGIN=1` used solely for CI/managed opt-in cleanup.
- Existing native restore-before-uninstall safety gate unchanged: if official Yandex restoration fails, neither uninstall nor session cleanup proceeds.
- This is a private **UNSIGNED** owner-test build, not a publicly signed or payment-ready release. Owner confirmation of actual interactive checkbox/first registration still pending.

## Results
- Full W69 native/.NET/WinForms build, 24 true mouse dropdown selections, real keyboard selector, native renderer, app+installer CELIKOM official icons, ZIP updater, Inno Setup 6.7.1 compilation, install/uninstall all **SUCCESS**: https://github.com/manufact-test/nomusic/actions/runs/42870959621
- Actual Windows per-user DPAPI **silent default uninstall** preserves ciphertext bytewise/decryptability and unrelated local file; reinstalled app and **explicit opt-in silent uninstall** deletes only session.dpapi, preserves unrelated file, leaves original Yandex alone:
  `W69_DEFAULT_UNINSTALL_RETAINS_DECRYPTABLE_DPAPI_PASS`, `W69_EXPLICIT_OPTIN_REMOVES_ONLY_SESSION_DPAPI_PASS`, `W69_OFFICIAL_YANDEX_UNTOUCHED_PASS`.
- Independent exact *0.24.16 W68→0.24.17 W69* upgrade checked historical CI artifacts, same original AppId, one installed application/uninstaller, DPAPI unchanged, native version 0.24.17, vendor untouched, uninstall defaults to preserve DPAPI: https://github.com/manufact-test/nomusic/actions/runs/42871865239 **SUCCESS**.
- Exact EXE artifact `13790650279`, `CELIKOM-W69-UNINSTALL-LOGIN-CHOICE-UNSIGNED.exe`, **43,528,746 bytes**, SHA256 `010f3db747af38229bfa3e3a06b85145be71f61ad9743470c0ca6fcda2eeaf21`.
- Library private versioned `/CELIKOM/Windows/CELIKOM-W69-UNINSTALL-LOGIN-CHOICE-UNSIGNED.exe`, file ID `file_00000000cf7081f9a0493cf8c5af69db`, library ID `libfile_6aeee9c6fe788191bb30ad3d0903de35`.
- **Owner-facing stable Library alias UPDATED** `/CELIKOM/Windows/CELIKOM-Windows-Setup.exe`, same existing library ID `libfile_9cef6593f5e88191a339835933fbc550`, new file `file_00000000e9d88243a8c742ae8beec529`. Both Library files were independently materialized into runtime and SHA256 compared byte-for-byte against exact GitHub artifact. Library is not a public HTTP website URL.

## Owner acceptance
1. Close CELIKOM/Yandex normally; install the Library `CELIKOM-Windows-Setup.exe` 0.24.17 **over installed W68 0.24.16**. This must preserve existing logged-in session by design.
2. In Windows Settings → Apps → CELIKOM → Uninstall (normal UI, not silent), observe checkbox **«Также удалить сохранённые данные входа»** unchecked by default. Check it, click Continue. If Yandex refuses native restoration, close Yandex and repeat. Owner needs to confirm real interactive UI, which CI did not physically click; CLI opt-in + compiled checkbox did pass.
3. Install the *same* W69 setup again, launch, and confirm the login/registration window is presented, rather than remembered email.
4. Logging in using same existing email must NOT create a new 3-day trial, nor reset subscription/ledger. New verified email is required for fresh-trial test. Local DPAPI deletion is not a server trial reset.
5. Optional: verify a normal uninstall with checkbox unchecked retains login (this branch was tested with silent default on Windows runner).
6. Re-test Start, Stop, pause/seek, MyWave, support only on real PC if desired; native audio is unchanged from W68.

## Still blocked for mass release (same as W68)
Existing paid-email/provider reconciliation, server paid feature rollout, actual secure public site/download URL, executable Authenticode signing, owner acceptance of new customer SMTP and actual fresh-device/Yandex version. No production changes or real payment attempts. See `docs/windows/W68-COMMERCIAL-TRIAL-ENTITLEMENT-AND-LAUNCH-BLOCKERS-20261110.md`.

## Never overwrite
- W68 exact immutable `backup/windows-w68-02416-private-entitlement-gates-ci-green-20261110` at `0eeccb99af50003914adf488e9dff2bc0fc08759`.
- W67 owner-proven `backup/windows-w67-02415-built-ci-passed-await-owner-20261110` at `5a1f5a3a81e0ae98909315ead137ca9a5260896b`.
- Android Test.50 immutable backup; don't modify original Yandex distribution.
