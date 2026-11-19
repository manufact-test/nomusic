# NAV40 continuation: exact signed queue mutation reference origins and period-info refresh

19 November 2026. **Signed-original read-only STATIC only.** No new NAV41, modified APK, player/audio/decoder hook, replacement traffic or raw media data.

## Source and protected checkpoints

- The real phone NAV40 owner TXT `CELIKOM-A1-Diagnostics-1795077619261.txt` already confirms the strict original live `SLOT_B → Lo96 source → original Player setter source` and historical exact creator `Track → later Flow → Album SAME/MANY`. Negative categories NONE. The phone log remains private.
- Original Yandex Music `2025.10.4 #120.1gpr`, 16 signed XAPK splits, six DEX, pinned research XAPK SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`. Identical original base APK SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` (also embedded unchanged in NAV40).
- Only working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Signed NAV40 Java/runtime SHA **unchanged** `34cb32c88a11743a64c9f4814fa71957223a1391`, protected `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`. New static pre-provenance backup `backup/android-a1-nav40-signed-slotb-five-writers-ci-green-pre-provenance-20261119` and protected provenance-green backup `backup/android-a1-nav40-signed-slotb-five-origins-ci-green-20261119`.
- Existing bounded auditor `android/native-yandex-hooklab/ci/exo_queue_slot_role_exact.py`, its fail-closed `test_exo_queue_slot_role_exact.py`; no original application sources/binaries committed.

## 1. All five SLOT_B direct writers — signed exact reference origin

The immutable original has exactly five DEX `iput-object` sites to that specific original `ExoPlayer/h.SLOT_B` field, exhaustively scanned across **six DEX**. The new register + field + branch-target guards prove the **local** origin:

| Site | Safe local reference origin | What it does **not** prove |
| --- | --- | --- |
| `e.break()V` PC 307 | Same original locally held reference placed into initial A/B/C/D holder slots | Fresh selected song/epoch |
| `e.break()V` PC 659 | Previously read B holder → exact typed successor → B | That every call advances a song |
| `h.if()Lxh6;` PC 12 | Conditional front-holder successor → B; opposite branch skips store | Currently selected edition |
| `h.while(Lxh6;)I` PC 25 | Conditional exact SLOT_A reference → B | New generation |
| `h.for()V` PC 35 | Constant `null` clears B alongside other slots | Complete player teardown semantics |

Confirmed same typed holder-successor field at engine PC657 and queue PC10/PC51; original branch offsets and register aliases checked. Extra, missing, duplicate, wrong-register, shifted-site and wrong-branch fixtures fail closed. All conditions remain static and path-local; no direct claim about runtime frequency/selected track or absent reflective/native mutations.

CI [#44497888210 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44497888210), exact runtime-free source `e3014410a40d3f302cf4fb49e234ccf724b4a041`, signed original verified. Counters explicitly `whole_program_queue_epoch_proven=false`, `runtime_selected_edition_proven=false`.

## 2. Holder contains **mutable** period-info, not a stable playback epoch

New signed original exact, constructor-anchored typed reference proof:

`current live SLOT_B Lxh6 holder → Lxh6's Lyh6 period-info field → original Lyh6's LSl6$b period-id field → LSl6$b's long J component`.

Constructor anchors verified with exact field owner/type, opcode and parameter→field register:
- `Lxh6.<init>` PC 18 writes `Lyh6` provided by original constructor argument (after original move-object).
- `Lyh6.<init>` PC 48 retains its `LSl6$b` reference.
- `LSl6$b.<init>` PC 9 retains its original long argument.
- Six signed DEX scanned for all direct writes to those **same exact fields**: **8 writes** to holder's `Lyh6` pointer, **1** write to `Lyh6 → LSl6$b` (constructor), **1** direct write to `LSl6$b`'s J field (constructor).

**Key non-obvious result:** there is a signed in-place holder refresh `Lxh6.else(FLTva;Z)V`: it reads its current `Lyh6`, calls `Lyh6.for(J)Lyh6;`, receives another `Lyh6`, then stores it into that *same holder's* field (PC 56 → 64 → 67 → 68). The original `Lyh6.for(J)` copies **the same Java `LSl6$b` reference** (PC 15 → constructor PC 33) into a new `Lyh6` when that return path occurs. This is an exact source/reference register proof, not equal values guessed from timing.

Therefore **same SLOT_B holder can carry a replaced period-info** and **same period-id Java reference can survive period-info refresh**. The long J is a real typed constructor field but its role as unique monotonic playback epoch is **NOT proven**. Never promote this period-id or J to currently selected edition/generation just because it exists. The right check would compare the **exact current per-read holder+period-info+period-id** against an independently proven original Player selected item/sequence boundary.

Pinned private research binary never exported. CI [#44500003305 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44500003305) on exact signed-original proof source `11121607d094f348e7ece432217f1775455a9417`. Synthetic negative fixtures guard direct member-writer categories; separate cloned-info register-guard tests added afterward.

## Stage B safety & next

`CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`; no claimed audio correctness, pause/seek/Bluetooth bugs or new installed APK.

**Remaining source-backed question:** Which exact original Player state transition identifies the **currently selected playlist item/edition and its actual current period sequence** at the SAME started audio read? The new audit rules out guessing that `SLOT_B` writes, holder `==`, period-info `==`, period-id `==` or the long component alone are such a generation/selection proof. More study must stay scoped to this original selected-Player-item / current MediaPeriod boundary, branch-sensitive, fail-closed, with no private identifiers/metadata logged. If not provable, remain NAV40 structural-only; **no blind NAV41**.

See previous [exact five direct writers](ANDROID-A1-NAV40-SIGNED-SLOTB-DIRECT-WRITES-20261119.md) and [real owner NAV40 phone](ANDROID-A1-NAV40-OWNER-PHONE-LATE-FLOW-SAME-20261119.md).
