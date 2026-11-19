# NAV40 follow-up — exact publisher-signed SLOT_B direct writer census (19 November 2026)

Scope: **static read-only audit only**, pinned signed original Yandex Music **2025.10.4 #120.1gpr**. This is NOT NAV41; no new owner APK, original app edits, Player/audio/decoder hooks, CELIKOM replacement, login or private media inspection.

Sole working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
Unchanged owner-signed NAV40 runtime: `34cb32c88a11743a64c9f4814fa71957223a1391`, backup `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`. Protected **pre-static-audit** backup `backup/android-a1-nav40-owner-phone-signed-slotb-pre-readonly-census-20261119` at `86addd96de8af868ca9da41b14540d86b6e8505a`.

## Trigger / background

Real NAV40 owner-phone TXT `CELIKOM-A1-Diagnostics-1795077619261.txt` establishes `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`, exact `Lo96` original source + same original scoped Player setter source, and `LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME=MANY`, three negative categories NONE.

**Important:** this still demonstrates bounded current original source ↔ historical creator Track/Flow/Album reference identity. It does not prove unique currently selected edition, playback generation, entitlement or replacement.

## Read-only signed writer proof

Signed input XAPK pinned at 45,961,661 bytes and SHA256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`. Verifier checks publisher-signed 16 split APKs, **six signed DEX**, and base APK SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`, matching the embedded unmodified NAV40 original.

**New narrowly extended CI auditor:** `android/native-yandex-hooklab/ci/exo_queue_slot_role_exact.py`, original name/field aliases kept internal; test `test_exo_queue_slot_role_exact.py`. It enumerates actual instruction-aligned **DEX `iput-object` 0x5b** writes to the identical `ExoPlayer/h.SLOT_B` field across **ALL declared method bodies of all six DEX**, instead of only the earlier `h/e` subset. A raw byte match is never counted as an opcode. Exact expected writer set is guarded fail-closed against missing, extra, duplicate or shifted instruction PCs.

**Publisher-signed exact result:** precisely **five direct DEX write sites**:

| Owner | Method | DEX PC | Observed signed bytecode role |
| --- | --- | ---: | --- |
| Native Exo engine | `e.break()V` | 307 | Initial holder: adjacent SLOT_A/B/C/D fields receive the same local holder reference |
| Native Exo engine | `e.break()V` | 659 | SLOT_B read → exact same holder-successor field read → SLOT_B write |
| Native Exo queue | `h.if()Lxh6;` | 12 | Conditional SLOT_B advancement through same exact holder-successor field |
| Native Exo queue | `h.while(Lxh6;)I` | 25 | Conditional SLOT_B assignment from SLOT_A |
| Native Exo queue | `h.for()V` | 35 | SLOT_B clearing after zero/null local constant |

The five PCs and exact field identity were verified on the immutable signed base. Exact successor field reference is identical at `h.if` PC10/51 and `e.break` PC657. Values are never exported. Method names here are original obfuscated bytecode labels, **not functional documentation for a user-facing API**.

**Green CI on exact static source `ea2dfb08092a4a468c6b7b8e6c98f74cc363b4d3`:** [read-only queue-slot audit run #44494854641 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44494854641). Both new unit fixtures passed. The CI output explicitly returns `publisher_dex_scanned=6`, `publisher_base_direct_iput_object_site_count=5`, `bounded_exact_site_proven=true`, `currently_selected_track_or_queue_epoch_proven=false`, `reflective_or_native_mutations_excluded=false`.

## Strict limits / no fake queue generation

- **Exhaustive only for direct `iput-object` references to this exact field in the six signed DEX.** It does **not** prove absence of reflective/native/other indirect mutations, or even execution of every listed branch during the phone session.
- **A hook on method entry/exit does not uniquely timestamp each internal write**: `e.break()V` has two distinct write PCs, and nested queue helper calls can change the field. One method invocation must never be treated as exactly one playback generation.
- Source setter exact `==`, live SLOT_B reference and exact historical `Track → Flow → Album` equality are positive structural witnesses, **not** the current selected edition or a reliable monotonic generation token.
- No title, track ID, URL, tokens, PCM, private field names/values or raw phone TXT committed.

## Next minimal technical work (STATIC FIRST)

Perform narrow signed-original, **branch-sensitive** inspection of the five writer paths and the current Player-selected item / MediaPeriod sequence boundary. Need an independently verifiable semantic identifier for **current selected queue generation**, including repeated same Track in consecutive epochs and same source prefetched/old holder. Prove it at the same **started audio renderer read**, rather than deriving it merely from counts of method calls or historical album matches.

If exact original selection/epoch boundary cannot be proven without modifying vendor Player/audio, stop: NAV40 remains `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. **No NAV41 APK yet.**

Any future NAV41 requires exact signed-original static guards, narrowly constrained read-only observer, fail-closed tests covering transitions/conflicts/GC/prefetch, pre-build backup, JVM + clone-alone ARM13 + publisher-first owner-signed ARM13 green CI, same signing certificate, original unchanged, APK/ZIP SHA-256 and Library readback.

See [real NAV40 owner phone](ANDROID-A1-NAV40-OWNER-PHONE-LATE-FLOW-SAME-20261119.md).
