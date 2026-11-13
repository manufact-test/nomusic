# W14 — first REAL Windows-client test: isolated approval checklist

**Date 2026-11-09. Proposal only; NOT EXECUTED and NOT automatically approved.**

This is the single practical next gate after the successful W14 candidate SDK build. It is not another pure Electron laboratory audio test. The owner has permitted considering mods for a CELIKOM product; no consent has yet been given for the exact real-Yandex installation actions described here.

## Preconditions before any official-client modification

- Windows VM or independently isolated throwaway Windows machine, with a snapshot capable of restoring full OS and local profile; never the owner's running authenticated 5.126.1.0 client.
- Windows Defender and SmartScreen enabled. No manual exclusions, no advice to disable security, no hidden persistence, no copying of any Yandex user cookie or token.
- Official Windows Yandex installer downloaded from vendor and its provenance/signature checked; target version must match **5.126.1.0** or test is recorded as incompatible, not relabeled. Separate empty Windows profile; separate test Yandex account only if later specifically approved and required to validate playback.
- PulseSync and PulseSync-mod artifact provenance, version, hashes, license/telemetry and installation side effects independently reviewed. The PulseSync-mod v2.1.5 release **spoofs 5.125.3 to 5.126.1**, which is NOT a compatibility proof.
- Before/after on that disposable machine, record: EXE file SHA-256, ASAR SHA-256, ASAR integrity resource match, Windows Authenticode signature status, Defender/SmartScreen result, original Yandex ability to launch. Only redacted statuses/hashes may leave VM; never profiles, tokens or media.
- Maintain independently verifiable recovery: clean VM snapshot or clean vendor reinstall, with original binaries unmodified. Replacing ASAR hash bytes in EXE invalidates original signed-byte identity and must not be represented as normal signed official binary.
- Separately determine whether PulseSync Client EULA allows the planned commercial CELIKOM relationship; without permission do NOT bundle, rename, sell or redistribute their proprietary client. Mod MIT license is different.

## Exact test sequence (only after informed specific owner consent)

1. Snapshot VM; verify normal protected app starts and runs original music under test account if available. Save only signature/hash/version statuses and playback test conclusion.
2. Install the **separately approved versions** of PulseSync Client and mod in the throwaway VM with normal Windows protection on; explicitly observe all files changed. If Defender/SmartScreen blocks or signature status unexpectedly changes, **STOP**, do not bypass.
3. Confirm source-replacement SDK capability from the W14 **disabled** add-on against the real host, without any CELIKOM credentials. First test should only establish host/addon loading, single-instance behavior and no unexpected account exposure.
4. After host test, add one **separately approved** CELIKOM Companion-to-addon resolver over a narrow authenticated IPC; authorize one test track only, with server-confirmed entitlement and short-lived HTTPS Range grant. Confirm Yandex remains the sole native decoder and all Play/Pause/Seek/Next/queue controls remain its own.
5. Negative cases: no mapping, expired signed URL, stop, original, next during slow resolve, restart, malformed URL, incompatible Yandex update, offline, Defender quarantine. The unmodified original must remain operable after rollback.
6. Restore snapshot and verify initial official EXE/ASAR hashes and signature, confirm no mod or CELIKOM hook remains.

## Stop conditions

- Original Yandex cannot start, W10 integrity prevents launch, Windows protection blocks modification, signature fails or loses provenance, an authenticated personal account/debugger must be used, single-instance forwarding reaches a logged-in primary, rollback cannot be proven, commercial permission is absent for a paid release, or native controls/queue break.
- NEVER treat turning off security, patching Windows protection or disguising the third-party mod as a legitimate shortcut.

## Owner decision needed for next gate

Request an **explicit yes/no approval for this isolated test plan**, with the exact PulseSync binary/version and test environment specified first. Approval to investigate in conversation does not authorize changing the current Windows installation. If no disposable VM exists, arrange one; do **not** quietly test in the owner's existing profile.

## Verified engineering checkpoint (no real install)

- W14 controller: `windows-companion/w14/source-controller.mjs`; **11/11 Node tests**, confirmed by Windows CI.
- Published PulseSync `@pulsesync/addon-sdk@0.18.0` successfully compiled disabled candidate `windows-companion/w14/addon/` to `dist/6f812b94-dcf8-4b6f-b913-0a3f10c77c20/script.js` (~13.56 kB).
- All earlier Windows W4–W12 regressions passed at [Windows run 42526627485](https://github.com/manufact-test/nomusic/actions/runs/42526627485) against source commit `16cb39000cbcbcb6925eb0d7a6fd3099b13eadfb`.
- This means the SDK build **compiles** and earlier fixtures work. It does NOT mean the add-on has been installed into PulseSync or that official Yandex 5.126.1.0 plays a CELIKOM asset.
