# CELIKOM Android A1 — signed native ExoPlayer period-holder continuation (17 November 2026)

**Current verdict:** NEW grounded *static* media-period-to-native-engine-holder continuation; **no proof of current audible period, no decoder or replacement audio. Stage A NAV17 PASS; Stage B NO-GO**.

This study starts **only** from the already confirmed signed, same-reference source→Player→internal source holder→`Lo96` MediaPeriod route. It is not a global Media3, renderer, ByteBuffer, source or player census.

## Exact input and protected provenance

Owner-tested NAV17 native Yandex original **2025.10.4 #120.1gpr**; original embedded base `assets/lspatch/origin.apk` SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`; original XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053` (16 verified publisher-signed APK splits, six DEX). The 2026 #170gpr control is **not** this signed original.

Baseline: `docs/android/ANDROID-A1-EXACT-SOURCE-MEDIAPERIOD-IDENTITY-20261117.md`; signed CI #44077450137 previously proved the **same native source** was stored in `Lo96` MediaPeriod by `Lp96.transient`, with 2/2 identical period return paths. This is still a *static* source-to-created-period witness, not proof of actual playback.

## New two-stage signed CI results

### 1. `Lo96` period handed into Exo's native period-holder machinery

[Lo96→native holder CI #3 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44093915839), 3/3 scoped test fixtures:

- The exact `Lp96.goto(LSl6$b;LrH2;J)Lwh6;` simply calls `Lp96.transient(... )Lo96;` and **returns the same result**. There is no additional duplicate period constructed in this adapter.
- `Lxh6.<init>([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V` obtains its `Lp96` wrapper through the **exact `i$c` Lp96-typed field** already proved in the Player playlist holder. It calls `Lp96.transient(...)` at PC 96; the identical `Lo96` returned at PC 99 becomes the **IdentityHashMap key** at PC 102 (key identity, not a claim about map value or active ownership).
- The same period reference is passed to `Lup1.<init>(Lwh6;ZJJ)V` at PC 132 (verified branch-sensitive local provenance). The exact `Lup1` constructor **stores the same incoming `Lwh6` period parameter on `this`**, at PC 3.
- `Lxh6` thus has a concrete path from a verified `i$c → Lp96 → Lo96` period into a native playback-period wrapper, rather than only source factory or `open/read` lifecycle evidence. **Neither IdentityHashMap membership nor `Lup1` allocation proves that period was selected or audible.**

### 2. Single exact ExoPlayer internal engine constructor caller

[Native engine CI #2 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44094591928), scoped fixtures PASS:

- Exactly one direct signed `invoke-* ` of `Lxh6.<init>([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V` exists in this bounded six-DEX check: `Landroidx/media3/exoplayer/e;.break()V` at PC 275. This routine allocates **one local `Lxh6` at PC 240**, and the exact same new object enters its constructor (constructor argument origin `NEW_INSTANCE_AT_240`).
- The method also accesses `Landroidx/media3/exoplayer/h` fields typed as `Lxh6` (queue-like holding state) and invokes native `Lxh6` lifecycle methods, plus renderer/engine-like calls. The obfuscated method name `break` **does not identify a semantic method without further evidence**.
- The method is very large and branchy. Its holder links **must not** be upgraded from exact constructor arguments + typed queue fields to a proven *current/selected* period. In particular a newly allocated holder may be loading/queued/next/prefetch, and this audit does **not** prove same new holder was the playing queue node or associated with the current decoder.

**Why this is useful:** we now have one precise, bounded bridge to inspect for active-period ownership, instead of searching every ExoPlayer or audio renderer. The static object route is `LcA9(TrackWrapper) → LiLb source → LA14.e → ExoPlayer.d.e → d.T0 → d.A0 → i$c → Lp96/LuIb → Lo96 MediaPeriod → Lxh6/Lup1 native holder`; the native engine creates the `Lxh6` holder at `e.break()`.

## What has NOT been demonstrated (do not oversell)

- No live currently selected `Track + album + edition + duration + queue generation` binding to this exact `Lo96`/ `Lxh6` pair; `Landroidx/media3/exoplayer/h` queue may contain several period holders.
- No exact runtime **active/reading** Lo96→renderer/decoder proof, nor source audio bytes.
- No CELIKOM entitlement/grant→native substitution, no user acoustic verification or stable seek/pause/next/radio playback.
- Static CI green = **signed original analysis only**, not an installed working Stage B APK. **Stage B NO-GO**.

## Narrow next handoff — do not redo completed proofs

**Only remaining target:** determine **which `Lxh6` holder referenced by exact native `ExoPlayer/e` + `ExoPlayer/h` queue is the *current audible* node**, its same `Lup1`/ `Lo96` period, and the decoder input, with current selected Track/album/edition/duration/generation (without exposing identifying metadata). Distinguish loaded/queued/prefetch from active renderer consumption; a constructor/map registration/field access is not sufficient. Consider one narrowly instrumented, privacy-safe observation only if a concrete hook event is first justified and a new safety backup is created; no blind runtime modifications.

No repeat of `LfT2`, `LiLb` getter/caller census, `LXk6`, broad `List/Object/MediaItem/ByteBuffer/Renderer` scan, source `open/read`, or already-proven Player→Lo96→Lxh6 constructors.

## Exact checkpoints

- Last **green, signed, read-only code**: `762088f55114553bacb96b324530ee241ce72dcd`, backup `backup/android-a1-exoplayer-engine-period-holder-ci-green-20261117`.
- Prior scoped exact period-holder auditor code `abdcffd32a84a9a58a2de695f47b58884793074d`, signed CI #44093915839 SUCCESS; backup `backup/android-a1-lo96-native-holder-caller-static-ci-green-20261117` protects its first green run at `6dd64052ce3eaa8729c5ba844637f9a0bca1f44b`.
- Pre-pass full backup `backup/android-a1-pre-period-activation-last-pass-20261117` @ `a07c5dbb174f714e9d750d7ebff8fc54e60221fe`.
- All new files only under `android/native-yandex-hooklab/ci/`, `.github/workflows/` and `docs/android/`. **No runtime-hook edits since `a655712d210189f3bc611847235de3ed4d985c1a`**. Original Yandex, installed NAV17 APK, Test.50, Windows, extension, backend/API/DB and production unchanged.
- Exact code paths: `android/native-yandex-hooklab/ci/native_period_activation_handoff_exact.py`, `native_engine_period_queue_exact.py` and unit tests; CI workflows `android-a1-native-period-activation-readonly.yml`, `android-a1-engine-period-queue-readonly.yml`.
