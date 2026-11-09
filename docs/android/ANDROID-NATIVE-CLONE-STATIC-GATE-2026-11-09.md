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

CI evidence must be entered here after the first real run. Before that: UNVERIFIED.
