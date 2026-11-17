# CELIKOM Android A1 — exact native MediaSource → Player handoff (17 Nov 2026)

**Status:** read-only static source-side handoff improved. Stage A / NAV17 **PASS** by owner, Stage B **NO-GO**. No CELIKOM replacement connected, no audible substitution.

This is a **new, bounded route** in the *publisher-signed original embedded in owner-accepted NAV17*, **Yandex Music 2025.10.4 #120.1gpr**, base SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. All new CI inspections pin the exact signed XAPK SHA `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053` (16 publisher-signed splits / 6 DEX). Neither the 2026 #170gpr control nor old #167gpr phone package is a substitute.

## Proven signed-DEX structural facts

### 1. Exact Exo factory consumer (new, no generic census)

[Source factory CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44068715436) and [typed/identity CI #5 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44069492927):

- `com.yandex.music.shared.player.download2.exo.c.for(LdA9;LQAa;Lmu3;LgA9;)LOr2$a;` has **two exact direct callers**: `LgLb.for()V` and `LlLb.if(LdA9;LQAa;LOf6;LgA9;)LIr8;`.
- In `LgLb.for()`, the precise `LOr2$a` reference **returned** from the Exo factory at ordinal 354 passes unchanged to `Las2.<init>(LOf6;LOr2$a;)V` at 358. The same constructor receives one `LOf6` MediaItem created at ordinal 329. Method-local producer/argument identity confirmed; branch presence means no unclaimed whole-method universal route.
- `LOr2$a` implements `LCC2$a` (factory-like source interface). Do not call it MediaSource itself.
- `Las2` and `LgLb` implement `LZB3`, a distinct 3-method interface (`cancel/if/remove`). Do **not** confuse `LZB3` with the actual MediaSource interface below.

### 2. Actual obfuscated MediaSource subtype and nested source

[LIr8/LSl6 identity CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44069978477):

- Exact signed subtype chain: `LIr8 extends LdC0 implements LSl6` (via `LdC0`); `LiLb extends LWT1 extends LdC0 implements LSl6`. This is the now-grounded obfuscated MediaSource-like contract, rather than an assumed unobfuscated SDK name.
- Concrete `LIr8.for()LOf6;` reads a MediaItem field from the same `this` and returns that reference; this alone is **not** current playback.
- In `LiLb$a.invokeSuspend`, the `LIr8` returned by `LlLb.if(...)` at ordinal 569 / move-result 572 is passed as **the same Java reference** to `LWT1.strictfp(Ljava/lang/Object;LSl6;)V` at ordinal 577. That establishes a real static *child MediaSource attachment* edge from the coroutine; no runtime selected source/decoder identity inferred.
- Other verified `LIr8` construction paths exist; the code is not exclusive to the active song.

### 3. Exact native Player source setter exists, not just MediaItem

[Player source sink CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44070516863):

- `LA14.e(LSl6;J)V` forwards **the identical source parameter** to `androidx.media3.exoplayer.ExoPlayer.e(LSl6;J)V`. `LA14.T(LSl6;)V` also forwards identically. Exact type `LSl6` is accepted directly by these native Player interfaces.
- One important direct caller of `LA14.e(LSl6;J)V` is `LcA9.extends(LcA9;LA14;LtCa;Ljava/lang/Long;JJZLn26;Lnk0;Ljava/lang/String;)V`, which **receives TrackWrapper `LtCa`**. There are eight direct Player source setter callsites in the bounded signed DEX check, including forwarding wrappers. The fact that this caller contains both TrackWrapper and source setter is **not** yet same-object constructor→setter proof.
- The earlier exact named AndroidX `MediaSource`-parameter audit was negative **only for that unobfuscated exact name**; it did not rule out `LSl6`. Do not repeat named API or broad List/MediaItem sweeps.

## Single remaining bounded static question

Inspect **only** the exact `LcA9.extends(...LtCa...)` method with branch-sensitive register/object identity:

1. Is one exact `LiLb` allocation built with the TrackWrapper-derived MediaItem?
2. Is that very same `LiLb` object passed into the `LA14.e(LSl6;J)V` Player source setter, across every reaching branch? Do **not** conflate a shared source type with an actual allocation.
3. The Player forwarding of `LSl6` is separately proven. Never infer runtime selected audible state, album/edition/duration/generation or decoder from this static source setter.

Implementation: `android/native-yandex-hooklab/ci/lca9_exact_source_player_identity.py`; CI `.github/workflows/android-a1-lca9-native-source-identity-readonly.yml`. Status and result to be reconciled into the canonical `NEXT-CHAT.md` after the run.

## Protected checkpoints

- Before new Exo consumer study: `backup/android-a1-pre-exo-factory-consumer-20261117` @ `2eb2eae660aff62f3565a4d166f53fe47cc74e92`.
- Exact Exo / Las2 junction green backup: `backup/android-a1-exo-lor2-las2-source-junction-ci-green-20261117` @ `11c54f3d63365f811f2d40c46d30a9d11ddf364e`.
- Exact LIr8/LSl6 candidate green backup: `backup/android-a1-lsl6-lir8-composite-source-ci-green-20261117` @ `e71d62cbb6e8237d0c61372f50f1795ebde027a3`.
- Exact source-to-Player direct calls green backup: `backup/android-a1-lsl6-player-mutator-exact-ci-green-20261117` @ `26591977a07f926da069ac0960f2c80baba1a92d`.

**Boundaries:** no new runtime hooks (last change `a655712d210189f3bc611847235de3ed4d985c1a`), no APK, no original Yandex modification, no new Player, decoder or AudioTrack, no Test.50/NAV17/Windows/extension/backend/production changes, no account/Track IDs/titles, private field values, URL, DataSpec, audio bytes or tokens. CI green proves read-only static structure, never a real user audition or CELIKOM replacement.
