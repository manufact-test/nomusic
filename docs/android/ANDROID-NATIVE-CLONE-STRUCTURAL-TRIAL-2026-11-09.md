# Native Yandex parallel clone research (ephemeral structural gate)

Purpose: before asking the owner to replace/uninstall their official
Yandex Music on HONOR, determine if 2026.10.3 #170gpr five signed
splits can be safely reconstructed with a different package identity.

The script uses Apktool v2.12.1 pinned by upstream SHA-256 and
a separately validated official-publisher signed XAPK with pinned SHA-256.
All work happens in ephemeral GitHub CI. It changes only manifest package,
ContentProvider authorities and selected own-package permission/identity
references. Java class names remain unchanged. DEX and native libraries
must remain byte-identical. All splits share one throwaway signing key.

**No APK artifacts uploaded, no device installation, no Play Protect
override, no Yandex session data, no bypass of app-integrity/login.**
Even a structural CI PASS cannot prove that the original Yandex account
login, app integrity checks, resources, media sources or audio work in clone.
An app copied under a different package may fail auth; stop, do not fake keys.

Source: android/native-yandex-hooklab/clone_native_splits_ephemeral.py
Workflow: .github/workflows/android-native-clone-structure-ephemeral.yml

Need exact real CI outcome and subsequent trusted runtime test before
claiming any installable CELIKOM-enabled native client exists.
