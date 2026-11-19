# NAV40: exact signed original PlaybackInfo period UID comparison against Queue front

19 November 2026. **Pinned issuer-signed original Yandex Music 2025.10.4 #120.1gpr**, read-only static research. Not NAV41 and not replacement playback. Original XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, unchanged base APK SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Six signed DEX / all 16 splits checked via existing CI. Private binary never checked in.

## Exact new source-level crosschecks

Original `Landroidx/media3/exoplayer/d.M0(LCD7;LTva;Pair;)LCD7;` works with state `LCD7` and timeline `LTva`. Original engine `e.break()V` reads **the exact same `LCD7.LTva` field** at PC673 as `d.M0` reads at PC25. Its `LCD7` reference reads at PCs 671 and 1260 use the **same exact engine field**, not merely a same-typed field. In original `LCD7`, there are **at least two distinct `LSl6$b` typed fields**: the one that engine reads at PC1262 corresponds exactly to `d.M0` PC74/96/259, while the field in `d.M0` PC138/257 is **distinct**. Conflating those two fails correct attribution.

A new fail-closed original-source exact register/field/callee/branch proof at `e.break`:

- PC1253 calls the original Queue `h.if()Lxh6;` on its exact Queue receiver, retaining returned holder reference in v11 at PC1256. The previous signed Queue proof establishes this method's front-holder `SLOT_A` return after its conditional local update; this is **not** a claim about audible period.
- Engine's exact `LCD7` at PC1260 → exact current `LCD7.LSl6$b` field at PC1262 → its `Ljava/lang/Object;` UID field at PC1264, stored in v1.
- Exact returned front holder v11 → anchored original `Lxh6.Lyh6` at PC1266 → anchored `Lyh6.LSl6$b` at PC1268 → the **same exact UID field** from that second `LSl6$b` at PC1270, stored in v2.
- Original `Object.equals(Object)` at PC1272 receives **precisely v1 and v2**. PC1275 takes the boolean result, and PC1276 branches on that result to PC1303. No local DEX branch occurs between the returned front-holder path and the equality check, and the exact referenced fields match those used in the prior signed period-info constructor/renderer region.
- The engine's original period-info pointer in the renderer region at PC675/679 and `Lyh6.LSl6$b` at PC677/681 match the exact constructor-anchored fields, not unrelated fields of the same type.

The original **engine PlaybackInfo period UID** is thus really compared against the **Queue front `SLOT_A` holder period UID** in a specified signed method. This is a specific comparison *boundary*, not an inference from repeated log messages. But the outcome of `equals` is not observed at runtime; and the **`SLOT_A` front is distinct in role from the `SLOT_B` renderer/reader reference** in NAV40 at PC547. This static comparison does **not yet** bind the original selected Track/edition to the `SLOT_B` audio period at the same started audio read.

**Signed exact source commit:** `549c6d332734327f5395075d431b58b1f7c736ae`. [CI #44513983147 SUCCESS, 23/23 unit fixtures](https://github.com/manufact-test/nomusic/actions/runs/44513983147). Tests reject wrong UID field, changed Queue holder register, changed equality callee, and shifted branch target. Earlier exact player/engine field correspondence [CI #44513279643 SUCCESS, 21/21](https://github.com/manufact-test/nomusic/actions/runs/44513279643). Original binaries not modified, no values, names, IDs, streams, URLs, media, account data or raw owner diagnostics exported.

## Explicit limits and next

This check does **NOT** prove any actual current-media-item/Track/edition, another queue epoch, a unique period sequence, runtime equality outcome, current vs prefetched `SLOT_B`, or simultaneous snapshot with NAV40 started-audio read. Same period UID may occur with different original ad indexes/MediaPeriodId/sequence; same `J` from old PeriodID can be forwarded into a new constructor. The original method has additional index/period branches **after** the UID comparison: do not interpret UID equality alone as acceptance.

The correct next narrow original-only question: analyze the exact subsequent original branches (PC1278–1303), independent `LCD7` period identity versus `SLOT_A` and `SLOT_B` at the read site, and map the same original selected Timeline/MediaItem to the candidate Track/edition. Require actual signed-source reference identity and fail-closed tests before minimal read-only NAV41 is justified; **do not infer** a generation by method-call counts or object equality alone.

The runtime stage remains `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Owner-signed NAV40 source SHA `34cb32c88a11743a64c9f4814fa71957223a1391` and protected `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119` unchanged. NAV40 Library APK/ZIP untouched, no NAV41 APK built.
