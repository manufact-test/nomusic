# Native Yandex authenticated laboratory — 2026-10-15

## Scope and acceptance gate

Owner-authorized disposable test account, original publisher-signed Yandex Music 2026.09.5 #167gpr, versionCode 24026501. This is an isolated Android emulator investigation. Root and Frida are laboratory tools only and are not an acceptable customer dependency. The customer requirement remains one ordinary APK alongside installed native Yandex Music, without F-Droid, USB, root or a shared server account.

Physical attenuation, independent test tone and public playback-state tests already accepted by the owner are preserved. Automatic exact catalogue identity and full synchronized replacement remain unverified. No new customer APK was produced by this session.

## Observed result

Run 38765567080 reached the native Passport phone-login screen. Opening More produced zero-bound menu controls, while the encrypted visual checkpoint still showed the phone screen. No credentials were entered on that path. The offered Google button successfully opened the system Google account form.

Run 38766841332 entered the owner-provided technical account address in the Google form. The keyboard obscured Next and the guarded tap correctly stopped with offscreen_control. A bounded manual laboratory command hid the keyboard and activated the now-visible Next button.

Google then displayed Verify it’s you / Confirm you’re not a robot with reCAPTCHA. No CAPTCHA was solved or bypassed. Selecting the offered Try another way returned Google couldn’t verify this account belongs to you. This occurred before password entry; it is not evidence of an incorrect password, missing Yandex account, or failed native playback.

The laboratory was stopped rather than repeating authentication attempts. No account-recovery or account-security changes were made. There is no successful authenticated native runtime trace from this session and no new ordinary-application source-ID channel.

## Changes and validation

The laboratory driver now rejects email entry on the phone-number method, accepts the explicitly offered Google provider for this Google test account, and restricts credential input to the known Yandex and Google system packages. Authentication errors preserve sanitized UI and encrypted screenshots so a bounded control round can inspect the actual failure. Credential values are never committed in command files or output reports. Python syntax was checked.

The unrelated general CI job 116531922651 failed before checkout/tests because the public ECR MySQL image pull returned toomanyrequests: Data limit exceeded. This was not a failed application test.

## Continuation

Clarify whether the disposable account already has a Yandex ID with its own normal login/password, or only a Google login. A normal Yandex login can be tested through the native Passport flow without requiring this blocked Google device sign-in. This is a laboratory prerequisite, not a proposal for a shared account or extra installer for customers. Do not ask the owner for another audio-only APK test, claim automatic identity solved, or submit a Google appeal based on this authentication result.

Evidence: docs/spikes/evidence/yandex-auth-lab-2026-10-15.json. UI reports contain redacted addresses; screenshots remain encrypted and are not published in this repository.
