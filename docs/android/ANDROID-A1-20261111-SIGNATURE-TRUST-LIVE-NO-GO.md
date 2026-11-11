# CELIKOM Android A1 — live signature-related failure and native exit verdict

Date: 11 November 2026. Experiment: `experiment/android-a1-exit-callsite-witness-20261111`. **Product: Stage A NO-GO. Stage B cannot start.**

## What is actually confirmed (not an inference)

Pinned original host: issuer-signed Yandex.Music 2026.10.3 #170gpr. In the disposable **real native ARM Android 13 guest**, the original issuer-signed application remains alive and resumed while the independently signed `pro.celikom.yandex.nativeclonelab` app repeatedly exits MAIN as Android `EXIT_SELF(0)`.

Our proprietary, **own-source**, permissionless LibXposed API102 diagnostic module was scoped only to the disposable CELIKOM lab package; LSPatch configuration stayed `sigBypassLevel=0`. Original host 6 DEX/3 native libs are preserved byte-for-byte in the research wrapper. Every hook calls the original API with unchanged arguments and return/throw behavior; no security override, Process.kill suppression, fake signer, fake Passport response, DRM modification or Play Protect interference.

[Real ARM13 CI 43040652116](https://github.com/manufact-test/nomusic/actions/runs/43040652116): in **two independent fresh MAIN PIDs**, `xx0(Context,2)` was constructed, `xx0.run CASE_2` executed, `OWN_AUX MATCH_TRUE` occurred on the same MAIN thread, `Process.killProcess` was called on **another PID**, then System/Runtime exit and actual `EXIT_SELF(0)`. Original issuer-signed MAIN remains alive.

[Real ARM13 CI 43042561533](https://github.com/manufact-test/nomusic/actions/runs/43042561533): a pass-through constructor hook specifically within `Lhi2.j` observed an `IllegalStateException(String)` whose message was classified as **EXC_SIGNATURE**. Only a finite lexical category was emitted; no raw message, account, token, or stack data.

[Real ARM13 CI 43043472606](https://github.com/manufact-test/nomusic/actions/runs/43043472606): for **both** fresh clone MAIN PIDs, an exact PID-scoped log-order correlation confirmed this sequence:
`HI2_EXCEPTION EXC_SIGNATURE` → `RUN_ENTER CASE_2` → `PREFIX_CHECK OWN_AUX MATCH_TRUE` → `PROCESS_KILL KILL_TARGET_OTHER` → actual clone `EXIT_SELF(0)`.
The summary explicitly reports `ordered_signature_mode2_aux_prefix_kill_chain_main_pids_bounded=2`, `hi2_signature_error_precedes_mode2_in_main_pids_bounded=2`, `hi2_signature_error_new_main_pids_bounded=2`, with 0 untrusted marker lines. **Observed event order plus a static reachable path is strong evidence, but does not by itself prove security-policy intent or which particular certificate/API was rejected.**

[Signed DEX CI 43034560475](https://github.com/manufact-test/nomusic/actions/runs/43034560475): in the exact `Lxx0.run` switch, branches 0 and 1 cannot reach the original `Process.killProcess` site; default branch can. [Signed DEX CI 43035121805](https://github.com/manufact-test/nomusic/actions/runs/43035121805): `Lby0.p(Context)` creates mode 0; `Lhi2.j(Object)` creates mode 2; `Lby0.a()` is not locally proven. [Signed DEX CI 43041843104](https://github.com/manufact-test/nomusic/actions/runs/43041843104): a path to the mode-2 constructor passes the `IllegalStateException` constructor, albeit CFG does not model catch edges. [Signed DEX CI 43042252251](https://github.com/manufact-test/nomusic/actions/runs/43042252251): nearby fixed literals are lexically related to authentication and signature/certificate, but static lexical hints cannot establish exact error semantics.

## Competitor and infrastructure

The exact owner-supplied `ChromaSync-Clone-3.0.1.apk` (SHA-256 `4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d`) was re-opened read-only. It is built around a different Yandex 2025.10.4 host, a private module and competitor LSPatch `sigBypassLevel=2`. It **does not prove** the current 2026 host will run without publisher trust, and its bypass MUST NOT be copied under our agreed requirements.

Ubuntu ARM runner started failing to resolve `ports.ubuntu.com`. A separate ephemeral ARM probe [CI 43040377969](https://github.com/manufact-test/nomusic/actions/runs/43040377969) confirmed four **TLS-valid official Canonical IPv4 endpoints**. Experimental workflow recovers the official HTTPS archive through a temporary hosts entry, Ubuntu's original archive GPG key and time-bounded apt commands. Native Android testing recovered at [CI 43040652116](https://github.com/manufact-test/nomusic/actions/runs/43040652116). No permanent system configuration or unsigned package introduced.

## Decision and honest release gate

**Stage A NO-GO for current 2026 host.** We cannot responsibly ship a one-APK native embedded Yandex UI clone while its signed-origin trust path produces an exception and terminates both main launches. Changing the vendor's signature/Passport/permission/security decision or reproducing the competitor's level-2 bypass is **outside approved scope**. Repackaging this host again is not a remedy.

The remaining product routes require an **owner decision**: use a publisher-authorized integration/signing contract or approved API (if actually offered), OR explicitly revise the native-embedded architecture and user requirements. Do not unilaterally substitute WebView, a second music player, patched issuer package, or fake account/login. No supported alternative has yet been verified to meet all originally agreed properties.

Main development source remains **untouched**: `experiment/android-native-a1-lspatch-clone-loader0-20261111` @ `cc4cb0f93489168db21502f3ef195855ae9fb743`; precise experiment checkpoint backup `backup/android-a1-signature-mode2-exact-arm13-two-pids-20261111` @ `1592098b4de7021abc718307ac32fc29284dabe1`. Existing accepted **Android Test.50**, Windows, browser extension, backend, production server and owner's HONOR 50/official Yandex install untouched. The independent B42 audio source contract is source-only and still does not prove an Android audible replacement.

No consumer APK was built or published. No need for owner to install/reinstall any APK at this stage.
