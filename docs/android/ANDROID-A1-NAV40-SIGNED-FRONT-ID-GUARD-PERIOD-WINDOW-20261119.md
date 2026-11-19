# NAV40 exact signed original: front PeriodID post-UID guard and Timeline Period→Window

**19 Nov 2026 | READ-ONLY static original**. Sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Latest source `bac9dfcca42d23d5bd82ea21bbf5836c6695a8d5`; [CI #44519254855 SUCCESS 32/32](https://github.com/manufact-test/nomusic/actions/runs/44519254855). Prior focused source `14bb3a753661b689c5928acbd05b74b41d57262e`; [CI #44518516341 SUCCESS 30/30](https://github.com/manufact-test/nomusic/actions/runs/44518516341). Exact signed publisher Yandex Music **2025.10.4 #120.1gpr**, original signed 16-split XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`; base APK SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Six signed DEX checked ephemerally in CI. No private values, account data, media, field names or publisher binaries committed.

## New positive exact witnesses

**Original engine `e.break()` post-UID comparison:** previous proven PC1253–1276 compares the original PlaybackInfo PeriodID UID with the Queue front **SLOT_A** holder PeriodID UID via `Object.equals` and branches to PC1303 when false. The *same exact* typed PlaybackInfo ID and front-holder PeriodID fields are re-read via PCs1278/1280 and 1287/1289. The signed instructions additionally perform:

- PC1282 and PC1291: the same exact first `LSl6$b.I` field on the two ID instances, each checked against signed `const/4 -1` from PC1284. Original `if-ne` at PCs1285/1293 jumps to PC1303.
- PCs1295/1297: an exact matching **second distinct** `LSl6$b.I` field on the two ID instances. Original **`if-eq`** at PC1299 jumps to PC1303. It is NOT `if-ne`; the opposite branch cannot be inferred as an audible-selection admission.
- All three branch registers, opcode kinds and PC1303 targets are pinned. No unpinned inner branch allowed. Exact fields, registers and negative-one encoding fail closed in fixtures.

This is proof of **extra original comparison conditions** beyond Period UID alone, NOT proof any condition succeeded in phone runtime, that SLOT_A front is the audible SLOT_B, or that the comparison creates a fresh queue generation.

**Exact Timeline Period → Window index propagation** in original `e.I` and `e.z`:

| Original method | Original UID→Period call | Period returned | Exact Period int read | Timeline Window call |
| --- | --- | --- | --- | --- |
| `e.I` first | PC56 `LTva.goto` | PC59 | PC60 | PC64 `LTva.super(ILTva$d;)V` |
| `e.I` second | PC101 `LTva.goto` | PC104 | PC105 | PC109 `LTva.final(ILTva$d;J)LTva$d;` |
| `e.z` | PC17 `LTva.goto` | PC20 | PC21 | PC25 `LTva.super(ILTva$d;)V` |

All three integer reads use the **same exact original field reference** in `LTva$b` (not merely type `I`). Original engine fields used for `LTva$b` Period scratch (PC54 in `e.I`; PC15 in `e.z`) and `LTva$d` Window scratch (PC62 / PC23) also match exactly. Typed, unmodified register handoffs into exact Window callee descriptors are proven. The first Window field read after the lookup is PC67 (`LOf6$f;` type); after the second lookup, PC113 reads typed `Ljava/lang/Object;` from returned Window. **Neither is confirmed to be the original Player's currently selected Track/edition.**

## Negative tests and hard interpretation

Test suite now **32/32**, including mutations to the post-UID int fields, negative-one literal, comparison direction, branch target/registers, Period/Window scratch fields, same Period index field, exact Window callee/argument registers, local clobber and result registers. The scanner is read-only and emits neither field names nor user/media values. It does not prove runtime path execution, snapshots under concurrency, exceptional/reflective/native flows, equality of the playing SLOT_B versus SLOT_A, same Track replay discrimination, a new queue generation, prefetched/stale period or started-audio timing.

**No runtime admission:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`, `NAV41_readonly_runtime_admission_proven=false`. Last signed NAV40 source `34cb32c88a11743a64c9f4814fa71957223a1391`; protected backup `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`; protected static backup unchanged; NAV40 APK/ZIP remain in Library. Last owner diagnosis `CELIKOM-A1-Diagnostics-1795077619261.txt` (Track later Flow Album SAME/MANY, not Player selection). No new APK.

**Next precise gate:** prove original selected Player MediaItem/Track/edition through original Window and actual active `SLOT_B` period at *the same* started-audio read, including negative branch cases of prefetch, old period and repeated same composition. Structural Window lookups and post-UID comparisons alone do not justify NAV41.
