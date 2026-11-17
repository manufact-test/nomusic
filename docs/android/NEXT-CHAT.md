# CELIKOM Android A1 — CANONICAL CURRENT HANDOFF

**Updated:** 17 November 2026. This file takes precedence over earlier Android NEXT-CHAT/HANDOFF documents.

## Protected checkpoints

- Only working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Current successful **read-only static identity code checkpoint:** `a9408608562b3d70a51f8d01c8be17aa4a73589b`, backup `backup/android-a1-lca9-wrapper-mediasource-player-identity-ci-green-20261117` (17 Nov 2026).
- Older exact named-type MediaSource negative-audit checkpoint: `433191c0b6e5f2a2eabef8589aa01c02f326e3b1`, backup `backup/android-a1-direct-mediasource-contract-ci-green-20261117`.
- Prior completed LfT2 code audit checkpoint: `e6bf9b6933d17d503b4f3b1d4f7d460df4b52f6a`, backup `backup/android-a1-lft2-class-structure-ci-green-20261116`.
- Prior code/runtime baseline: `27ccbe8348d598fead0386e70ef68573b04270c4`, backup `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116`.
- Last runtime-hook modification: `a655712d210189f3bc611847235de3ed4d985c1a`. No hook/APK changes in this audit.
- Pre-audit safety backup: `backup/android-a1-target-resolved-pre-lft2-class-inspection-20261116` @ `0143f904400d5ddd17a8d4469aa3c777adfe8f04`.
- CI #229: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139), old constructor identity proof.
- CI #230: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101), compact logs.
- Exact class and branch-sensitive TrackWrapper audit **CI #12 [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43909098407)**, 16 publisher-signed splits / 6 DEX.
- Direct MediaSource-typed Player contract audit **CI #2 [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44049682525)** on 17 Nov (3/3 unit tests, exact 2025 signed input); CI #1 was blocked by private draft release access, not by the static scan.

## Product status

**Stage A / NAV17 PASS** (owner confirmation on 14 Nov): native Yandex login/UI and original music audible.

**Stage B NO-GO**: CELIKOM replacement audio not connected/proven; no selected native Track → active source/decoder same-object chain.

Goal remains one standalone CELIKOM APK with native Yandex UI/player and original native playback path, no second Player/decoder/AudioTrack. Never infer product packaging from the `pro.celikom.nativeprobe` diagnostic manifest or `<queries>` visibility declarations.

## Definitive *NAV17 tested artifact* origin (not a production-forward pin)

- Owner-installed `CELIKOM-A1-NAV17-PassportProviderFix-20261114.apk`: SHA-256 `8d7c1570367360c12ba11f3972fa72477aca4dcc33f30dce78b381aee939b20d`.
- Its embedded original `assets/lspatch/origin.apk`: SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` = Yandex Music **2025.10.4 #120.1gpr**, code `24025542`. This is grounded in the [NAV17 input audit](ANDROID-A1-NAV17-STAGE-B-PINNED-2025-FILEINFO-SOURCE-AUDIT-20261114.md).
- Exact original verified XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 45,961,661 bytes, 16 splits / 6 DEX. Publisher signature and base SHA reconfirmed in CI #12.
- Yandex **2026.10.3 #170gpr**, code `24026531`, XAPK SHA `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`, five splits: original-only ARM13 verification CI #42990078186; separate structural clone experiment; **not** the proven NAV17 original.
- Yandex **2026.09.5 #167gpr / #167.1gpr**: formerly reported phone installation, no exact pinned signed package; **not** the proven NAV17 original.

The NAV17 source question is now resolved for the owner-tested artifact. The *future production target* remains a distinct owner/build decision and is not automatically pinned by a previous test. Never transfer obfuscated identifiers across versions.

## LfT2 closure — do not investigate again

Read only [ANDROID-A1-LFT2-EXACT-CLASS-CLOSURE-20261116.md](ANDROID-A1-LFT2-EXACT-CLASS-CLOSURE-20261116.md) for exact structural evidence.

- Earlier chain `LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>` carries and stores same `LtCa;` TrackWrapper, only on exact 2025 signed DEX.
- `LfT2;` is `PUBLIC FINAL extends Object` with no interfaces; fields of types `LdA9; LtCa; LgA9;`.
- Only constructor, `equals`, `hashCode`, `toString`. **No invokeSuspend** and no executable continuation method.
- Branch-sensitive complete audit of all its TrackWrapper field reads finds only equality and string formatting operations; **no** same-object playback handoff to MediaSource, MediaPeriod, DataSource, Extractor or Player. **This route is CLOSED.**
- Closed old routes: `LiLb`, `LXk6`; don't repeat Media3 ancestry, global List/Object tracing or ByteBuffer sink census.

## Recovered Yandex/Media3 research (documentation only, 16 Nov)

The previous developer's useful research **was already saved**: [YANDEX-MEDIA3-RESEARCH-RECOVERED-20261116.md](ANDROID-A1-YANDEX-MEDIA3-RESEARCH-RECOVERED-20261116.md) is a concise index to exact existing facts, not a new experiment.

- Official Android Media3/ExoPlayer exposes **direct** `setMediaSource`, `setMediaSources`, `addMediaSource`. This prevents an incorrect *MediaItem-only* assumption; it does **not** prove how signed Yandex dispatches into the player.
- Signed 2025 Yandex static [RAa continuity](ANDROID-A1-RAA-SOURCE-RESUME-IDENTITY-20261115.md), [CI #43696198020 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43696198020): real `RAa.invokeSuspend` resumes with the **same continuation instance** but an explicitly null TrackWrapper argument. Existing bounded weak-reference RAa recovery is a historical research result, not active-selected playback proof. `RAa` is **not** `LfT2`: the latter has no continuation methods and stays CLOSED.
- Native descriptor→Exo factory→source→open/read lifecycle already has source-instance evidence and read-only hooks in [NAV17 Stage B source audit](ANDROID-A1-NAV17-STAGE-B-PINNED-2025-FILEINFO-SOURCE-AUDIT-20261114.md); these can also reflect **prefetch/download**. Even a positive source read cannot attest the selected current track, album/edition/generation, nor an audible CELIKOM replacement.
- The official Yandex playback-support article mentions VPN/network stability, **not** a public signed-app playback call graph. Third-party clients/plugins are not evidence of official Yandex Android internals.
- This recovery changed **documentation only**. Safety snapshot before updates: `backup/android-a1-before-yandex-media3-research-handoff-20261116` @ `a324963b84876a88513bc1d208a42519489c397f`. No runtime hooks, APK, original Yandex or production changes; no new CI was requested.

## 17 Nov — exact direct MediaSource-to-Player API check, CI #2 SUCCESS

- Source: `android/native-yandex-hooklab/ci/direct_media_source_player_contract.py`; CI `.github/workflows/android-a1-direct-media-source-player-readonly.yml`. Before-work backup: `backup/android-a1-pre-direct-mediasource-contract-audit-20261117` @ `a142f5fe48f92d68727f4c9873a4a6cfda56b156`. Successful audit code backup: `backup/android-a1-direct-mediasource-contract-ci-green-20261117` @ `433191c0b6e5f2a2eabef8589aa01c02f326e3b1`.
- Bounded to **11 previously known Player interface/implementation owners** and **exact declared parameter type** `Landroidx/media3/exoplayer/source/MediaSource;` on the signed 2025.10.4 XAPK (16 issuer-signed splits / 6 DEX, NAV17 origin SHA confirmed).
- Result: `exact_media_source_class_defined=false`, `exact_direct_media_source_player_contract_count=0`, `direct_source_player_callsite_count=0`. 3/3 fail-closed tests PASS; original input deleted ephemerally. Runtime hooks, native code, APK, accounts and audio unchanged.
- **Interpretation:** This closes only the **named exact-typed direct MediaSource Player call** hypothesis in the listed owners. It does **not** disprove obfuscated MediaSource types, indirect dispatch, runtime selected item, or the public Media3 APIs. No negative inference beyond that scope. **Do not rerun a global census to compensate.**
- No selected Track + album/edition/duration/generation → active source/decoder same-object proof; Stage B remains NO-GO. Future candidate must have a separately grounded exact source-side or selected-player-owner link, otherwise do not expand tracing.

## 17 Nov — NEW proven TrackWrapper → native ExoPlayer source object handoff

**Read [exact source-to-Player signed proof](ANDROID-A1-EXACT-SOURCE-PLAYER-HANDOFF-20261117.md)** before any further Stage B work. Unlike previously closed MediaItem/List routes, this is a **specific verified source-side object identity into the native Player setter**:

- [Signed factory CI #5 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44069492927): `LgLb.for()` carries the identical `LOr2$a` result from Yandex Exo factory to `Las2(MediaItem,LOr2$a)`. `LZB3` is a distinct lifecycle interface, not the MediaSource type.
- [Signed media-source CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44069978477): `LIr8 extends LdC0 implements LSl6` (via superclass); `LiLb extends LWT1 extends LdC0 implements LSl6`. Within `LiLb$a.invokeSuspend`, `LlLb.if(...)` yields an `LIr8` which is passed as the same object to `LWT1.strictfp(Object,LSl6)`. These establish source-side nesting, not active audio.
- [Signed Player setter CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44070516863): exact `LA14.e(LSl6;J)V` forwards the identical source parameter to native `ExoPlayer.e(LSl6;J)`; `LcA9.extends(...LtCa...)` directly calls `LA14.e`.
- **Critical [branch-sensitive CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44070976535)**, signed 2025 NAV17, 4/4 fail-closed tests: exact `LcA9.extends(...LtCa...)` passes same TrackWrapper argument to `Lbq0.this` (PC 14), constructs the unique `LiLb` source with a MediaItem (PC 97), and passes the **exact same allocated LiLb instance** to `LA14.e(LSl6;J)` (PC 112), across 55 path states and 2 branches. Verdict **`LCA9_ONE_NATIVE_PLAYER_SOURCE_SAME_OBJECT_STATIC_PROVEN`**. This is the actual new static handoff result. No re-audit of this exact route.

**Precise boundary:** It proves source selection *call into ExoPlayer* on a TrackWrapper-bearing route, **not** that the setter receiver is the currently audible player, nor correct album/edition/duration/generation, active MediaPeriod/decoder, or CELIKOM bytes. Stage A NAV17 PASS; **Stage B NO-GO**. No runtime hooks or APK touched. Verified code at `a9408608...`, protected backup above.

## Next task and boundaries

**Continue solely from the new exact `LcA9.extends → LA14.e(LSl6;J) → ExoPlayer.e` same-object source proof.** The missing next edge is its runtime **current selected Player receiver/item/generation → active MediaPeriod/decoder**, with trusted Track+album+edition+duration. Distinguish active audio from queued/prefetch sources. Do **not** repeat LfT2, LiLb direct getter, LXk6, global List/Object/ByteBuffer, generic Player ancestry or the new source constructor identity audit. Existing factory→open/read lifecycle alone is not current-track proof. Keep Stage B NO-GO until owner-approved real audio verification; no runtime hooks or APK without concrete justified measurement.

No changes to original Yandex, NAV17, Test.50, frozen branches, runtime hooks, Android APK, Windows, extension, backend/API/DB or production. No reading/exporting Track/Album IDs/titles, URLs, DataSpec, account tokens, private field values, or audio bytes. All static work bounded, read-only and fail-closed. No full CI reports or large source dumps.
