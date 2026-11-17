# CELIKOM Android A1 — signed ExoPlayer internal source-holder same-object bridge (17 Nov 2026)

**NEW exact static result. Stage A / NAV17 PASS; Stage B NO-GO.** This document continues the source→Player proof in [ANDROID-A1-EXACT-SOURCE-PLAYER-HANDOFF-20261117.md](ANDROID-A1-EXACT-SOURCE-PLAYER-HANDOFF-20261117.md). It supersedes assumptions that direct MediaSource dispatch stops at a Player call.

## Exact signed NAV17 input

Publisher-signed Yandex Music **2025.10.4 #120.1gpr**, embedded NAV17 original base SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Every read-only CI pins XAPK SHA `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, size 45,961,661, **16 publisher-signed splits / 6 DEX**, exact original package version and NAV17 base. Original input ephemeral; no files/audio/user data exported.

## New native same-object chain

1. **Already proven:** `LcA9.extends(...LtCa...)` receives TrackWrapper, constructs one `LiLb` MediaSource around derived MediaItem, and passes that **same LiLb** to `LA14.e(LSl6;J)`; `LA14.e` forwards the **same source** to native `ExoPlayer.e(LSl6;J)`. [CI #44070976535](https://github.com/manufact-test/nomusic/actions/runs/44070976535) SUCCESS.
2. **Exact Player implementation:** concrete `androidx.media3.exoplayer.d.e(LSl6;J)` forwards that same source to `Collections.singletonList(Object)`, then passes the **same resulting List** into `d.T0(Ljava/util/List;IJZ)V`. Also confirmed for the `d.T(LSl6;)V` variant. Branch-sensitive source parameter→singletonList→T0 **PASS**, no branches in the two setters. [ExoPlayer setter implementation CI #2](https://github.com/manufact-test/nomusic/actions/runs/44074575554) and [T0 CI #1](https://github.com/manufact-test/nomusic/actions/runs/44075018858), both SUCCESS.
3. `d.T0` forwards its exact List argument into `d.A0(Ljava/util/List;I)Ljava/util/ArrayList;` at PC 51, all paths in its bounded CFG. It then builds an internal timeline/scheduling update (including `LvW7`, `LTva`, `androidx.media3.exoplayer/e$b`), but the scheduling calls **do not imply audible playback**.
4. **`d.A0` exact source holder:** calls `List.get(I)` on that same incoming List (ordinal 14); the **exact returned reference**, after `check-cast LSl6` (which preserves Java identity), is passed to `androidx.media3.exoplayer.i$c.<init>(LSl6;Z)` (ordinal 22). There is one getter, one constructor, no branch or overwrite between them. The one `i$c` newly allocated object is passed unchanged to the first `ArrayList.add(Object)` (ordinal 25). This is a local exact register/alias proof, not an inference from similar types.
5. **Retained source inside nested wrapper:** `i$c.<init>` forwards the **same LSl6 source parameter** into a newly created `Lp96.<init>(LSl6;Z)`, and stores that exact `Lp96` instance on its own `this`. `Lp96.<init>` forwards the source parameter unchanged into `LuIb.<init>(LSl6;)`. In `LuIb.<init>`, the **exact source parameter is stored on this** as an `LSl6`-typed field (ordinal 3), proven branch-sensitively by `FIELD_STORE_TYPED_IDENTITY`; field **name/value not read or exported**.
6. **Result:** the source passed into the native ExoPlayer source setter flows into a singleton playlist and is retained inside an actual player-side `i$c → Lp96 → LuIb` source-holder object. This is a real object-identity proof reaching internal playlist ownership, not just a factory/read event.

**Signed CI #5 [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44076441146)**. Script: `android/native-yandex-hooklab/ci/exoplayer_a0_source_holder_exact.py`; associated exact CI workflow. Verdict field `one_source_to_internal_playlist_holder_static_proven=true` (including `List.get_to_i$c=true`, `i$c.new→ArrayList.add=true`, `i$c→Lp96=true`, `Lp96→LuIb=true`, `LuIb.field_store=true`). The audit explicitly returns `active_selected_media_period_confirmed=false`, `same_source_to_current_decoder_proven=false`, `replacement_audio_connected=false`.

### Still missing, not to be handwaved

- This is **static** source insertion/retention, not the runtime **current selected Player item** or audible MediaPeriod. Other internal playlist owners and prefetch exist.
- Need exact current selected **Track + album + edition + duration + generation** linked to this retained same source, not inferred from track ID or timing.
- Need actual MediaPeriod/decoder instance for that selected source, not just `open/read`, registration, source creation or internal playlist assignment.
- CELIKOM approved grant/entitlement, independent session, HEAD/Range and on-device acoustic check remain unperformed. Stage B **NO-GO**. No APK, no runtime hooks, no original Yandex alteration.

### Next strictly scoped technical candidate

Inspect **only** the newly established `i$c → Lp96 → LuIb` source wrapper at an exact **MediaPeriod creation** call and its active Player selection path. Candidates must start from exact signed `Lp96` / `LuIb` object and demonstrate runtime current selected source/generation before any read-only probe or hook is justified. No generic re-census of `MediaItem`, `List`, `ByteBuffer`, `LfT2`, `LXk6`, `LiLb` getters. Static field metadata only; no private field values.

## Protection

- Latest successful exact static code checkpoint `dca9e8e5c6ac7503a2f307411c6a495fe8b74093`.
- Exact backup `backup/android-a1-source-into-internal-playlist-holder-ci-green-20261117`.
- Previous source admission backup `backup/android-a1-exoplayer-t0-source-list-admission-ci-green-20261117` @ `429570903fc13a2ee7bf692c417c7ae346d0661c`.
- Previous ExoPlayer source setter implementation backup `backup/android-a1-exoplayer-d-source-admission-ci-green-20261117` @ `00b50ba1deef0070190b49cbdd66d132e10e9db7`.
- Last runtime hook code `a655712d210189f3bc611847235de3ed4d985c1a`. All changes in this pass **Python read-only static audits, fixtures, CI and docs only**. No APK, build artifact, original vendor binary, NAV17, Test.50, Windows, backend, production or user account changed.
