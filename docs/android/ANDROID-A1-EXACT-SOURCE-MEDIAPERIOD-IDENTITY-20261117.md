# CELIKOM Android A1 — exact signed native source → MediaPeriod identity (17 Nov 2026)

**Status:** NEW successful *static* original-source-to-period object identity. **Stage A NAV17 PASS. Stage B NO-GO.** Real active-player selection, actual decoder/audible replacement and owner confirmation remain unproven.

## What is newly proven

The previous bounded, successful source-to-Player and playlist-holder audits are documented in:

- [ANDROID-A1-EXACT-SOURCE-PLAYER-HANDOFF-20261117.md](ANDROID-A1-EXACT-SOURCE-PLAYER-HANDOFF-20261117.md) — exact `LcA9(...LtCa...) → LiLb → LA14.e → ExoPlayer.e` same-object source setter.
- [ANDROID-A1-EXOPLAYER-PLAYLIST-HOLDER-IDENTITY-20261117.md](ANDROID-A1-EXOPLAYER-PLAYLIST-HOLDER-IDENTITY-20261117.md) — `ExoPlayer.d.e → singletonList → d.T0 → d.A0 → i$c → Lp96 → LuIb` same source retention.

**New exact [MediaPeriod CI #3 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44077450137)**, script `android/native-yandex-hooklab/ci/lp96_media_period_entry_exact.py`, 16 original publisher-signed Yandex Music 2025.10.4 #120.1gpr splits / six DEX; focused fail-closed unit tests (including all-return, wrong-field and duplicate-allocation negative cases).

1. `LuIb.<init>(LSl6;)V` stores the **exact incoming original MediaSource reference** on `this`, in an `LSl6`-typed field. Previously checked in signed A0/source-holder CI.
2. The exact `Lp96.transient(LSl6$b;LrH2;J)Lo96;` **reads the same DEX field reference**, not merely a field of a similar type. The static audit compares the full original DEX field reference from `LuIb` constructor write to `Lp96` read, but **does not export its name or any field value**.
3. Inside `Lp96.transient`, the unique `Lo96` MediaPeriod object is constructed once via `Lo96.<init>(LSl6$b;LrH2;J)V`. The LSl6 source reference read from `LuIb.this` is stored unchanged into the `Lo96` object's own LSl6 field (PC 18), as verified by branch-sensitive identity with `ORIGINAL_MEDIA_SOURCE_FROM_THIS_FIELD`.
4. Both return-object branches in the method (PC 51 and 64) return the **same uniquely allocated Lo96 period reference**, not another period of the same type. Exactly one allocation, one constructor call, and **2/2 returns** with `MEDIA_PERIOD_NEW_INSTANCE`. The identity CFG completed, 34 states, no error.
5. On one branch, `LWT1.strictfp(Object,LSl6)` also receives that very same original source from the base field (PC 61), consistent with native child source attachment. This secondary call is **not** active playback proof.

Full fail-closed verdict: `static_same_source_to_returned_MediaPeriod_proven=true`, with `LuIb_same_exact_source_field_stored_and_read=true`, `same_source_reference_stored_into_Lo96=true`, `all_period_returns_use_same_new_Lo96=true`.

**Result:** We now have a grounded *static object-identity chain from TrackWrapper-bearing native MediaSource via the actual ExoPlayer playlist holder into a newly created native MediaPeriod*. This is substantially stronger than factory/open/read witnesses or type-name guesses. It gives a precise anchored starting point for testing an **actual active period**, without any new Player/decoder/AudioTrack.

## What remains NOT proven

- Whether a particular `Lp96.transient` invocation generated the **current audible** MediaPeriod, rather than a prepared next period, prefetch or an unrelated Player instance.
- The current selected Track + **explicit album / edition / duration / generation** across this same native Player and period at the moment playback starts; no field values, IDs or account data were read.
- Any **same decoded audio buffer / renderer** object belonging to this precise current MediaPeriod.
- Any CELIKOM authenticated grant, replacement bytes, sound, seek/pause/Next/radio or owner playback QA.

No source swap has been made. Static CI on exact original **cannot** assert runtime current audio; **Stage B remains NO-GO**. Do not add replacement hooks or publish an APK on this evidence alone.

## Exact next candidate and gates

Start only with the already proven `ExoPlayer.d.e → d.T0 → d.A0 → i$c → Lp96/LuIb → Lp96.transient → Lo96`. The next necessary observation is **which Lo96 instance became the current native playback period**, bound by the exact Player instance/current item and generation (with confirmed native Track/Album/Edition/Duration). A period being created and the original DataSource opening/reading do not distinguish active from prefetched. Only after the exact same active period is tied to decoder input can the existing authorised CELIKOM identity/entitlement/HEAD-Range path be considered. No other static census of LfT2, LiLb getter, LXk6, generic List/MediaItem/ByteBuffer, full Player ancestry, or external Yandex builds.

## Signed original, protections and checkpoints

- Publisher-signed original: Yandex Music **2025.10.4 #120.1gpr**, pinned XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`; NAV17 embedded base SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. This is not the separate 2026 ARM13 original.
- Exact successful static period code: `24c37a59d454cc5ec0b69f9e548fbe3349108673`. Reserve: `backup/android-a1-exact-source-to-lo96-mediaperiod-ci-green-20261117`.
- Prior successful source-to-playlist-holder code: `dca9e8e5c6ac7503a2f307411c6a495fe8b74093`; reserve `backup/android-a1-source-into-internal-playlist-holder-ci-green-20261117`.
- The last runtime hook change remains **`a655712d210189f3bc611847235de3ed4d985c1a`**.
- In this pass changed ONLY read-only Python static audits, unit tests, isolated CI workflows and Android documentation. No original Yandex bytecode/APK, NAV17, Test.50, Windows, browser extension, backend, production, user accounts, URLs, tokens, MediaPeriod runtime methods, decoders or audio data accessed/modified.
