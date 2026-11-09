# Android — static collision audit for parallel Yandex clone (2026-11-09)

Before offering a parallel test app to the owner's HONOR, independently inspect
the verified 2026.10.3 #170gpr official Yandex XAPK for clone incompatibilities.

New source: android/native-yandex-hooklab/audit_parallel_clone.py
New workflow: .github/workflows/android-native-yandex-clone-feasibility.yml
Synthetic tests: tests/test_parallel_clone.py

Properties:
- Offline inspection of the exact, publisher-signed XAPK with pinned SHA-256.
- No patch, repack, install, signing or public APK artifact; all APK files deleted after CI.
- Count provider authorities, manifest attributes tied to original ru.yandex.music,
  package string/descriptor dependencies in DEX, multi-split identity.
- Only print aggregate counts and risk categories; not literal strings, URLs,
  credentials, source code or private data.
- Exit with a safe NO-GO verdict: static inspection cannot prove the clone works.
- Owner's installed Yandex + music downloads must not be touched.

Remaining gates: find whether package rename can preserve five split APK structure,
host integrity, Yandex login, Play Protect and libxposed runtime. Without a viable
isolated package ID and trusted signing strategy, do NOT install conflicting
ru.yandex.music on the owner's HONOR.


## Actual pinned APK scan — PASS, but clone gate NO-GO

GitHub CI [42637284714](https://github.com/manufact-test/nomusic/actions/runs/42637284714) — SUCCESS. The exact publisher-signed #170gpr (5 split APK, 6 DEX files) was inspected read-only. No patched APK was made.

- 11 providers; **9** provider authorities include the original package ID. Changing only appId would leave conflicts with installed official Yandex.
- Of 109 manifest attributes containing the original package string, **86 are Android Java component class names**. These class names can in principle remain unchanged when applicationId changes; do NOT globally replace all 109 strings.
- 13 package-bound routing attributes (including the 9 provider authorities), 9 other package-bound attrs; require role-by-role review, NOT blind rewriting.
- Two exact `ru.yandex.music` DEX strings and 35 additional strings containing it may be runtime identity dependencies; 643 slash-path descriptors are mostly Java class descriptor references, not 643 confirmed clone blockers.
- sharedUserId detected: zero. This is encouraging but does not establish login or Play Protect compatibility.

**Decision:** no quick safe parallel clone package yet. Android native Yandex installed on HONOR remains untouched; do not attempt to install current same-ID lab APK over it.

Next independent check: **own-source 32-bit ARMv7 host** at `android/native-yandex-hooklab/armv7-loader-host/`. It uses package ID `pro.celikom.armv7loaderhost` with NO Yandex code and NO Android permissions. The separate loader-only host is a diagnostic for LSPatch runtime and will not test audio; physical phone verification is still pending. See `docs/android/ANDROID-NATIVE-OWNED-ARMV7-LOADER-2026-11-09.md`.

