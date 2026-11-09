# CELIKOM Android — clean native ARM emulator route (09.11.2026)

The requested side-by-side modified Yandex app is **NOT safely installable yet**.
The independent ARSCLib offline path (first five-split job) got past Apktool
resource rebuild and reached signing/validation. A safety audit then identified
five original ContentProvider authorities still shared by the proposed parallel
clone: `@string/passport_sync_adapter_content_authority`,
`com.yandex.passport.authsdk.provider.ru.yandex.music`,
`com.yandex.passport.internal.provider.ru.yandex.music`,
`com.yandex.passport.internal.sso.ru.yandex.music`,
`com.yandex.preinstallsatellite.appmetrica.provider`.
CI https://github.com/manufact-test/nomusic/actions/runs/42668435366
stopped intentionally BEFORE any device install. Blind renaming would jeopardize
Yandex Passport account sign-in and third-party SDK communication. No clone
has been accepted, delivered or installed. The initial APKEditor gate does not
yet establish five-split structural compatibility.

**Alternative isolated native runtime gate (not a parallel clone):**
Run an ARM64 Android 13 emulator on a clean GitHub macOS ARM runner. Download
the same pinned #170gpr five publisher-signed split APKs, install only those
unaltered APKs in the disposable emulator, verify Android package and process
launch. Never authenticate, modify original, inject CELIKOM, play music, request
secrets, bypass Play Protect, or upload the vendor APKs. This can prove the
authentic app itself launches on independent ARM runtime (a prerequisite to a
future read-only source observation). It cannot by itself validate owner phone
compatibility, audio, account, hook or side-by-side installation.

Files:
- `android/native-yandex-hooklab/original_yandex_arm_emulator_ephemeral.py`
- `.github/workflows/android-native-original-arm-emulator-ephemeral.yml`

A separate future phase must decide how a permitted, patched native host can
be tested while retaining the official installed Yandex application. Work
profiles sharing the installed package do not solve the conflicting signatures
by assumption; avoid any owner-device experiment until technically proven.

Keep Test.50, original HONOR app, production, Windows, extension and backend unchanged.
