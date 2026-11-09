# Install-only clone probe: preserve publisher signature-protected permissions

Exact Android11 x86/ARMv7 [CI 42679652707](https://github.com/manufact-test/nomusic/actions/runs/42679652707):
original 5/5 publisher-signed APKs installed successfully, but clone rejected
before launch with `INSTALL_FAILED_DUPLICATE_PERMISSION` on
`com.yandex.permission.READ_CREDENTIALS`.

Read-only [CI 42680372407](https://github.com/manufact-test/nomusic/actions/runs/42680372407)
confirmed exactly TWO original declared custom permissions, both
`android:protectionLevel="signature"`:
- `com.yandex.music.RELAY_PERMISSION`
- `com.yandex.permission.READ_CREDENTIALS`

The original requests `READ_CREDENTIALS` and `AM_COMMUNICATION`.
No other manifest attribute directly references `READ_CREDENTIALS`; its
literal does not appear in any of the six DEX files. **This does not
prove authentication works without the declarations.**

For ONE disposable Android11 translated install-only experiment, explicitly
opt in `CELIKOM_OMIT_SHADOWED_SIGNATURE_DECLS=1` (requires
`CELIKOM_CLEAN_ANDROID_ARMV7_TRANSLATION=1`). Only the *clone's two
duplicate <permission> declarations* are omitted. Original publisher app
still owns them; NO `uses-permission` request is changed; no protection
level weakened and no signature checked or bypassed. The original stays
signed/installed; clone runs with separate signer and therefore cannot
automatically receive the original's signature-level permission.
Fail if permission definitions differ from exact pinned expectations.

This is not an auth or production strategy. A clean PackageManager install
or app launch only means coexistence at the OS level; normal Yandex login,
Play Protect, FileInfo runtime/decoder and audio remain untested.
Never install the experiment on the user's HONOR or distribute patched APKs.
