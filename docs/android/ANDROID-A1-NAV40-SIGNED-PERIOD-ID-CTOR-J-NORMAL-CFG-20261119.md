# NAV40 signed-original MediaPeriodId constructors and exact Queue long-argument normal CFG

19 November 2026. This is **static, read-only research** against the pinned publisher-signed original Yandex Music **2025.10.4 #120.1gpr**, NOT a new NAV41, runtime hook or APK. Sole working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

## Verified signed input / existing checkpoints

- The same publisher original as NAV40: private XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, base APK SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`; all 16 signed splits and all six DEX checked in CI. Private original bytes remain ephemeral in the runner.
- Owner-phone NAV40 evidence unchanged: `CELIKOM-A1-Diagnostics-1795077619261.txt` showed strict active source and historical Track/Flow/Album SAME, not current item/edition/epoch.
- Last owner-signed NAV40 runtime still `34cb32c88a11743a64c9f4814fa71957223a1391`, protected `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`. Do not rebuild, modify or delete signed NAV40 or its Library APK/ZIP.

## New exact evidence

Extended `android/native-yandex-hooklab/ci/exo_queue_slot_role_exact.py` and bounded fail-closed fixture suite `test_exo_queue_slot_role_exact.py`:

1. Exact opcode-boundary census across the six signed DEX yields **15 direct constructor call sites** for original `LSl6$b` MediaPeriodId. Four constructor descriptors occur, with counts `(IJLjava/lang/Object;)V: 3`, `(JLjava/lang/Object;)V: 3`, `(Ljava/lang/Object;)V: 4`, `(Ljava/lang/Object;IIJI)V: 5`. Every caller method, PC, descriptor and direct/direct-range opcode is pinned; missing, shifted, duplicated or additional sites fail closed.
2. Four specific Queue constructor J arguments derive on **all normal DEX CFG paths** from a typed incoming `J` parameter of the exact caller, not from a merely similar value. The CFG proves the source `move-wide/from16` dominates the constructor and neither the incoming two-register J nor the copied two-register J is overwritten along relevant normal paths:

| Signed Queue owner method | Constructor PC | Wide move PC | Typed source J register | Constructor J register |
| --- | ---: | ---: | ---: | ---: |
| `h.import(LTva;Ljava/lang/Object;JJLTva$d;LTva$b;)LSl6$b;` | 126 | 124 | 18 | 10 |
| same `h.import` alternate constructor | 139 | 130 | 18 | 10 |
| `h.else(LTva;Ljava/lang/Object;IIJJZ)Lyh6;` | 11 | 9 | 23 | 4 |
| `h.goto(LTva;Ljava/lang/Object;JJJZ)Lyh6;` | 103 | 101 | 34 | 14 |

3. The negative test fixtures cover a branch bypassing the copy and an overwritten source wide register; they do **not** turn a constructor occurrence into an epoch. `wide_definition_register_shape` also uses the correct nibble-sized register destination for `iget-wide`.
4. Last static source commit: `b6de25c7f146610e7f25ad7838d11529edca07b2`; [GitHub Actions #44507724826 SUCCESS, **15/15 tests**](https://github.com/manufact-test/nomusic/actions/runs/44507724826). Exact fields in the signed report: `exact_direct_constructor_callsite_count=15`; `all_four_queue_J_parameters_to_period_ID_proven_on_normal_CFG=true`; `selected_player_item_generation_at_audio_read_proven=false`.

## Explicit limits (fail closed)

The constructor's long argument **originates in a caller parameter** on four specific normal CFG paths. It is **not demonstrated** to be a monotonically unique playback generation, selected playlist edition, audible MediaPeriod, or a new song on each call. A J parameter may originate further upstream, be reused, represent a window sequence rather than a new track, or appear in prefetch/old periods. The DEX normal CFG does not include exceptional control flow; the direct constructor-site census does not rule out reflection/native/indirect creation. No method-call count, Java holder identity, period ID identity, Long value or historical Track→Flow→Album match may be promoted to selected edition.

**Stage B unchanged:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. No original Player, renderer, decoder, audio, APK, original publisher binaries, private media content/IDs/URLs/tokens or exported raw diagnostics changed.

## Next scoped question, no blind NAV41

Trace **the callers of exact Queue `h.import`, `h.else` and `h.goto` J parameters** back to an independently proven original current Player selected playlist item/window and current MediaPeriod at the **same started-audio read**. Require branch-sensitive same-identity and sequence semantics under repeated same Track, holder refresh, prefetch, stale previous period and transitions. If no independent selected item/generation witness can be shown, retain NAV40 structural-only. Do not build NAV41 until signed-original proof, fail-closed tests and a narrow read-only runtime target exist.

## New signed-original old ID reuse proof (19 November 2026)

See [exact two old `LSl6$b.J` → new Queue ID-builder branches](ANDROID-A1-NAV40-SIGNED-OLD-PERIOD-ID-J-REUSE-CFG-20261119.md). CI #44510497627 SUCCESS, 19/19; original J itself may be carried into another constructor. **Do not** promote Long, ID ref, call count or holder ref to selected-item generation. No NAV41.
