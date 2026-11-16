# CELIKOM Android A1 — LfT2 exact signed-DEX closure (16 Nov 2026)

**Canonical result for this candidate:** CLOSED. The continuation hypothesis is false on the exact signed 2025.10.4 #120.1gpr binary. **Stage B stays NO-GO.**

## Proven target provenance — NAV17, not diagnostic manifest

- Owner-tested CELIKOM APK: `CELIKOM-A1-NAV17-PassportProviderFix-20261114.apk`, SHA-256 `8d7c1570367360c12ba11f3972fa72477aca4dcc33f30dce78b381aee939b20d`.
- Embedded actual `assets/lspatch/origin.apk`: SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`, identified as the original Yandex 2025.10.4 #120.1gpr base.
- Independent exact signed XAPK: SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 45,961,661 bytes, versionCode `24025542`, 16 verified publisher-signed splits, six DEX. CI confirms this original base SHA matches the embedded NAV17 origin.
- Original source proof: [NAV17 signed input and source audit](ANDROID-A1-NAV17-STAGE-B-PINNED-2025-FILEINFO-SOURCE-AUDIT-20261114.md). The `<queries>` entry in the companion manifest has no bearing on this determination.
- This establishes the source of **owner-tested NAV17**, not an irreversible choice of a future production build. 2026.10.3 #170gpr was verified independently as an ARM13 original control; 2026.09.5 #167gpr was previously present on the phone. Do not transfer obfuscated descriptors.

## Existing call path, not rerun

[CI #229](https://github.com/manufact-test/nomusic/actions/runs/43888792139) proved the same `LtCa;` TrackWrapper traverses `LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>`, and the constructor stores the same reference on `this`. The two identity-proven `Lxj8.for` constructor callsites are PC 210 and PC 432. The constructor has 9 direct callsites in 8 methods overall; not all have same-object proof.

## New exact class facts: CI #12 SUCCESS

[Run 43909098407](https://github.com/manufact-test/nomusic/actions/runs/43909098407), exact original publisher-signature/split/version/base-SHA gates, read-only.

- Class `LfT2;` defined in `classes4.dex`; `PUBLIC FINAL` (`0x11`); superclass `Ljava/lang/Object;`; **no interfaces**.
- Three instance fields, no static fields; field **types only**: one `LdA9;`, one `LtCa;` (TrackWrapper), one `LgA9;`. No private field names/values were read.
- Exact declared methods only:
  - `<init>(LdA9;LtCa;LgA9;)V`
  - `equals(Ljava/lang/Object;)Z`
  - `hashCode()I`
  - `toString()Ljava/lang/String;`
- **No** `invokeSuspend`, `resumeWith`, `invoke`, `create`, inherited continuation entry, or other executable Object→Object entry. It is a plain data holder, **not a coroutine continuation**.
- Every read of the stored `LtCa;` field in the declared non-constructor methods was checked with a bounded branch-sensitive same-object trace. All three scans finished with `scan_complete=true` and no unmodelled instruction states:
  - `equals` field-read PC 23 → same object to `kotlin/jvm/internal/Intrinsics.try(Object,Object):boolean` at PC 27 (one equality helper use);
  - `hashCode` field-read PC 9 → no same-object calls;
  - `toString` field-read PC 17 → `StringBuilder.append(Object)` at PC 19.
- **Zero same-object LfT2 playback edges** to MediaSource, MediaPeriod, DataSource, Extractor, Player, or native decoder. Data-holder `equals/hashCode/toString` uses are not playback continuation.
- Bounded audit source: `android/native-yandex-hooklab/ci/lft2_class_inspection.py`; CI workflow: `.github/workflows/android-a1-lft2-class-inspection-readonly.yml`.
- No APK produced or modified. Original signed XAPK inspected ephemerally and deleted. No tokens, private values, URLs, audio bytes or account data accessed.

## Correct status and future boundary

- **Stage A / NAV17 PASS** by owner: native Yandex account/UI/original audible music works.
- **Stage B NO-GO**: current selected Track → active native source/decoder and audible CELIKOM replacement are not proven.
- The `LfT2` route is **CLOSED**. Do not reinterpret this holder as a coroutine, re-run it, or reopen closed `LiLb` and `LXk6` routes.
- For any next distinct candidate, require **exact same-object** identity from selected Track through an *active* native source, not merely a similar type or prefetch/download object. Respect direct MediaSource APIs in Media3. This document does **not** authorize a new global scan.
- Last runtime-hook change `a655712d210189f3bc611847235de3ed4d985c1a` unchanged. NAV17, Test.50, frozen branches, Windows, extension, backend/production untouched.

## Checkpoints

- Last runtime code checkpoint: `27ccbe8348d598fead0386e70ef68573b04270c4` (prior accepted backup `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116`).
- Verified static-audit code: `e6bf9b6933d17d503b4f3b1d4f7d460df4b52f6a` (backup `backup/android-a1-lft2-class-structure-ci-green-20261116`).
- Pre-audit backup: `backup/android-a1-target-resolved-pre-lft2-class-inspection-20261116` @ `0143f904400d5ddd17a8d4469aa3c777adfe8f04`.
