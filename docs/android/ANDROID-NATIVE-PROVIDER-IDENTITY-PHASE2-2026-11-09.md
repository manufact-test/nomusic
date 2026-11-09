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
