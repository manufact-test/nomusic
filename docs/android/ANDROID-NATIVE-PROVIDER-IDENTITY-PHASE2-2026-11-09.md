# Android native Yandex — bounded provider identity patch research (09.11.2026)

Signed #170gpr base read-only authority audit: [CI 42669936573](https://github.com/manufact-test/nomusic/actions/runs/42669936573) SUCCESS. Eleven original providers found; five collide with a naive side-by-side clone. Three exact Passport provider authorities have zero literal occurrences in six DEX files (might be runtime-derived; **not proof**), the sync provider authority is a manifest `@string` resource with concrete value `com.yandex.passport.sync.ru.yandex.music`, and the AppMetrica provider has one exact DEX literal.

A narrow non-distributable CI structural Phase 2 is now defined:
- Rewrite only the four identified hardcoded manifest provider authorities (three Passport + one AppMetrica) to a separate test namespace; change one exact Passport sync resource value.
- The AppMetrica constant is a single fixed-length ASCII DEX literal. Research a one-occurrence reversible patch with DEX checksum/signature recomputation; verify every other DEX byte and all native libraries preserved. Do not silently patch other strings or touch files on user phone.
- Rebuild/sign five split APKs with one throwaway non-publisher key, independently check metadata and all output DEX/native bytes.
- Fail closed on any unexpected count, provider manifest issue, resource mismatch, signature mismatch or build error.
- **Never upload/install/share vendor APKs.** Structural SUCCESS would NOT verify app login, package-bound business logic, package reputation/Play Protect, read-only Xposed hook, FileInfo→decoder runtime or audible native replacement.

Workflow: `.github/workflows/android-native-identity-phase2-ephemeral.yml`
Script: `android/native-yandex-hooklab/clone_native_identity_phase2_ephemeral.py`

No impact to official Yandex/HONOR, Test.50, extension, server or database.


## Verified Phase 2 result (09.11.2026)

**PASS, STRUCTURAL ONLY:** [CI 42670648029](https://github.com/manufact-test/nomusic/actions/runs/42670648029).
Exactly **5/5** original #170gpr splits were decoded, narrowly edited, rebuilt,
zipaligned and signed with one ephemeral non-Yandex certificate. All five
manifest package/split/version metadata checks passed, as did signature
verification, all original native library byte comparisons, and exact DEX
payload comparison against the one explicitly permitted AppMetrica string
replacement (and its recalculated DEX header hashes). Exactly four manifest
provider identity changes, one sync resource change, one DEX literal change.
No third-party APK retained/published/installed.

This is *not* real Yandex login or native decoder proof. Real Android installer
side-by-side, process launch, account login, hook binding, Play Protect
and Yandex audio are all still **NOT TESTED**. Do NOT send to HONOR,
distribute modified publisher APKs, or call the native product ready.
Next safe gate: clean isolated ARM emulator install BOTH original and test clone
and verify process launch with NO authentication. Only after that consider
read-only FileInfo witness in genuine Yandex client.


## Resolved provider uniqueness static gate PASS — 09.11.2026

[CI 42678096410](https://github.com/manufact-test/nomusic/actions/runs/42678096410)
SUCCESS 5/5 structurally rebuilt split APKs. New
`resolved_provider_authorities` resolves the pinned resource-backed
Passport sync authority to its actual original and separate-clone value;
compares full public ContentProvider identity sets and fails closed if any
overlap, duplicate or unsupported resource reference remains.
Result: `resolved_original_vs_clone_provider_collisions: 0`.
Three new synthetic unit invariants PASS.

No publishing/retention of vendor APKs or keys; no device installation.
No proof of Login, Play Protect, Android PackageManager coexistence, native
decoder, Yandex signed package service assumptions or real audio.

Avoid auto-repeating known nonbootable macOS hosted ARM emulator; coexistence
workflow now explicitly manual-dispatch only for future authorized runners.
