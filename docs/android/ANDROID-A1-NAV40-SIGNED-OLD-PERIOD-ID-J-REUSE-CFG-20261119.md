# Signed original NAV40 continuation: old MediaPeriodId.J can flow to another MediaPeriodId constructor

19 November 2026. **Read-only pinned ORIGINAL static audit, not NAV41.** Sole branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

## Baseline and constraints

Original Yandex Music **2025.10.4 #120.1gpr**, signed 16-split private XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, six signed DEX; original base APK SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. CI verifies signatures and source bytes before scanning. User-phone NAV40 runtime unchanged at `34cb32c88a11743a64c9f4814fa71957223a1391` and protected signed backup `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`. No APK/ZIP rebuilt or changed.

Real NAV40 phone evidence from `CELIKOM-A1-Diagnostics-1795077619261.txt` confirms current original source chain and historical exact Track/late Flow/Album SAME, but not currently selected edition or unique queue generation.

## Verified original source results, fail closed

**All signed direct ID creation paths:** exactly **15 direct `LSl6$b` constructor call sites** in six signed DEX, four constructor signatures. They are guarded by exact caller+PC+descriptor+invoke opcode. Four Queue `J` values are proven through dominating `move-wide/from16` from exact typed caller `J` parameters, with CFG overwrite guards; see [constructor + J report](ANDROID-A1-NAV40-SIGNED-PERIOD-ID-CTOR-J-NORMAL-CFG-20261119.md).

**Immediate upstream Queue calls:** exactly **eight direct calls** to three original Queue helper builders `h.import`, `h.else` and `h.goto`, all from the signed `h` Queue class, with pinned caller/PC/target/opcode. Local candidate J registers include `iget-wide` reads from `LSl6$b`, `Lyh6` and other typed fields; these candidate instruction scans alone are **not** an all-path provenance assertion.

**New exact all-normal-CFG transitive proof** (no field names or values exported):

- In original `h.case(LTva;LSl6$b;JJ)Lyh6;`, PC **13** reads the **same exact original `LSl6$b.J` field** that the pinned `LSl6$b` constructor stores at PC 9. The receiver is precisely the method's typed incoming `LSl6$b` parameter. This J reaches original `h.else` call at PC **25** as its **second J** input.
- Same original `h.case`, PC **30** re-reads that same exact incoming ID's original J field. It reaches `h.goto` call at PC **40** as its **third J** input.
- In both cases the read dominates its call along all **normal DEX CFG** paths; neither the typed input ID reference before read nor the wide J register before call is overwritten.
- Independent signed-original builder proofs show these **exact second/third J formal inputs** are forwarded to new `LSl6$b` constructor J arguments in `h.else` at PC **11** and `h.goto` at PC **103**. Thus the original **old ID's exact J field can be propagated through two branches into another ID constructor**; no synthetic epoch counter or value-equality guess was used.

**Green exact static source commit:** `6fe28f562089852025793eb5e2e52d7fbd34382e`. [Read-only pinned-signer GitHub CI #44510497627 — SUCCESS, 19/19 fixtures](https://github.com/manufact-test/nomusic/actions/runs/44510497627). Suite includes negative branch bypass, wide register clobber, missing/changed ctor/queue caller sites and signature drift. Report explicitly: `old_period_id_J_field_to_new_period_id_constructor_normal_cfg=true`; `current_selected_item_or_unique_playback_generation_proven=false`.

## Interpretation and limits

This is a **static possible path**, not proof that the branch executed on the user's phone, that a newly allocated ID represents a different song, or that J is a monotonic queue generation. In fact, its original **same-J propagation** is a concrete reason **not** to treat that long field as independently unique to a new playback selection. The proof covers normal DEX paths and exact direct callsites, not exception edges or reflective/native/indirect mutations.

Even with matching `SLOT_B`, mutable `Lyh6`, exact `LSl6$b` Java reference, old ID J or historical Track/Album equality, the **original Player's currently selected track/edition linked to the active renderer queue generation** remains unproven. Nor does this identify PCM, request URLs, private Track values, media metadata or entitlement.

**No NAV41 / no replacement:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Original Yandex Player, renderer, decoder, audio, API, source, signed original and NAV40 unchanged.

## Next narrow original-only step

Inspect the exact signed-original **Player selected playlist item / timeline window / MediaPeriod object identity** attached to the **same started-audio `SLOT_B` read**, not just input J provenance. Require mutually exclusive read-time classification of current vs prefetched vs stale period and repeated same Track across queue generations. Preserve original semantics and fail closed on missing/conflicting evidence. No source or APK for NAV41 is justified by this J propagation finding.
