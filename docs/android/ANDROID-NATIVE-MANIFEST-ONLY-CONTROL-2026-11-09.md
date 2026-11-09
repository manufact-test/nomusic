# Android CELIKOM — no-DEX-mutation control (09.11.2026)

## Purpose
Prior signed DEX analysis [CI 42690904213](https://github.com/manufact-test/nomusic/actions/runs/42690904213)
proved the lab's direct in-place AppMetrica DEX literal rewrite **broke the
required DEX string_ids ordering**, while prior runtime [CI 42686813136](https://github.com/manufact-test/nomusic/actions/runs/42686813136)
had original Yandex alive but clone unable to load YMApplication.

This is a **controlled isolation test**, NOT a vendor DEX patch:
- Rebuild a separate package using the previously verified manifest and
  public provider authority changes, but preserve all SIX base DEX entries
  byte-for-byte identical to publisher original. Do not patch or reorder any
  DEX strings and retain the public provider's original authority references
  inside the DEX. Both source and output DEX are compared by bytes in the
  pipeline.
- Install the pinned signed original 5 splits and the ephemeral different
  package 5 splits only inside disposable, ABI-matched Android 11 x86 + ARMv7
  translator. Check real original launcher/process first, then clone launch.
- Do not request account credentials, grant signature-level privileges,
  patch original, evade Play Protect, install on HONOR or publish APKs.
- An original AppMetrica DEX authority may not match renamed manifest
  authority. Thus **successful process launch is not sufficient** for login,
  AppMetrica functionality, native decoder/source, real audio or product.
- If class loader now succeeds, the previously unsorted DEX edit becomes the
  leading *runtime* failure cause. If not, inspect new failure class
  categories, without treating the Android package as customer-ready.

Workflow: `.github/workflows/android-native-manifest-only-dex-preserved.yml`
Guard: `CELIKOM_MANIFEST_ONLY_ORIGINAL_DEX=1` only in ephemeral GitHub CI and
Android ARMv7 translated disposable emulator, never a distributable artifact.
