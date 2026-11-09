# Native Yandex clone — custom permission ownership blocker (09.11.2026)

One bounded, ABI-correct translated Android 11 x86 emulation run
[CI 42679652707](https://github.com/manufact-test/nomusic/actions/runs/42679652707)
proved that Android PackageManager successfully installed the authentic
publisher-signed original #170gpr five splits. **Installing the separate
lab clone then failed** `INSTALL_FAILED_DUPLICATE_PERMISSION` because
`com.yandex.permission.READ_CREDENTIALS` was already declared by the
original `ru.yandex.music` package. The clone did not install or launch.
Neither login, Play Protect, CELIKOM hook nor audio was tested.

This is Android platform custom permission ownership and signature
isolation, NOT a resource rebuild/ABI error. Per official Android
documentation, unrelated signers cannot both define the same named
custom permission. Don't bypass signature protection, weaken level, steal
credentials, or delete user original as a shortcut.

New read-only public Manifest + signed DEX literal-count audit reports
the declaration, its protectionLevel and same-name references without
reading any account, token, permission-granted data or secret. It may guide
a safe, principled design decision; **a blind permission rename/removal
is NOT authorized** and would not establish Yandex Passport functioning.

Only after proving a legitimate coexistence strategy that preserves
security boundaries should any clone installation be re-attempted, and
only in a disposable environment. HONOR and accepted Test.50 untouched.
