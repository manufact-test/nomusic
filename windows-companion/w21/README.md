# W21: backup and recover two original Yandex files safely (internal)

New independent CELIKOM-owned C# recovery engine; no PulseSync Client or SDK
dependency. It handles only two known paths, \`Яндекс Музыка.exe\` and
\`resources/app.asar\`. It NEVER modifies a Yandex installation on its own.

## Why we need it

W17/W18 showed that even successful third-party mods can invalidate Yandex's
Authenticode. The MIT-licensed FkCensor project demonstrates another
integration approach independent of PulseSync, but also changes the
EXE-embedded ASAR integrity hash. **Neither fixes Yandex signature or
commercial redistribution permissions.**

## Recovery lifecycle (not currently activated for consumers)

1. Future integration component performs read-only
   \`YandexHostProbe.Inspect\` and requires supported official signed build.
2. Before any approved installation: \`PairRecovery.Capture\` demands both
   known original hashes, stores copies in an outside CELIKOM directory and
   writes immutable prepared manifest. Snapshot never overwrites existing.
3. Only after an approved adapter has applied a patch and recorded the **known**
   post-change hashes: \`PairRecovery.RegisterApplied\` marks the exact pair
   recoverable. The engine is deliberately not a patcher.
4. \`PairRecovery.Restore\` refuses if Yandex is running, source files have
   changed due to update/foreign mod, backup hashes differ, or backup path is
   redirected. It restores each original file using same-volume staging and
   validates bytes. A \`RESTORING\` marker permits retry after interruption;
   multiple files are NOT one atomic filesystem transaction.
5. Original backup and manifest remain present even after restoration.

Only synthetic fixture tests run in CI until permission and exact real
installer/audio verification exist. No APK, website, server, browser extension
or production changes. **W20 consumer installer does NOT bundle this W21
library or mutate Yandex.**

### Independent source research

- MIT FkCensor: https://github.com/S4YN3X/FkCensor/tree/main/internal/asarpatch
- It modifies official ASAR and embedded EXE hash, so verified signature
  and Yandex licensing remain blockers.
- Its MIT license covers its authors' code, NOT proprietary Yandex files.
  Third-party audio datasets are NOT an authorized CELIKOM catalog.
- Reuse CELIKOM exact-ID approved grants, never foreign catalogs, and do not
  import PulseSync GPL SDK into an independently licensable adapter.

Next: build and test an independently licensable exact-ID resource adapter
**only as isolated developer code**, then obtain the necessary rights and
real authenticated Windows audio verification before integrating the
consumer installer.
