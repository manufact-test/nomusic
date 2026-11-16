# CELIKOM Android A1 — CANONICAL CURRENT HANDOFF

**Updated:** 16 November 2026. This file takes precedence over earlier Android NEXT-CHAT/HANDOFF documents.

## Protected checkpoints

- Only working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Current successful **read-only audit** checkpoint: `e6bf9b6933d17d503b4f3b1d4f7d460df4b52f6a`, backup `backup/android-a1-lft2-class-structure-ci-green-20261116`.
- Prior code/runtime baseline: `27ccbe8348d598fead0386e70ef68573b04270c4`, backup `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116`.
- Last runtime-hook modification: `a655712d210189f3bc611847235de3ed4d985c1a`. No hook/APK changes in this audit.
- Pre-audit safety backup: `backup/android-a1-target-resolved-pre-lft2-class-inspection-20261116` @ `0143f904400d5ddd17a8d4469aa3c777adfe8f04`.
- CI #229: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139), old constructor identity proof.
- CI #230: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101), compact logs.
- Exact class and branch-sensitive TrackWrapper audit **CI #12 [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43909098407)**, 16 publisher-signed splits / 6 DEX.

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

## Next task and boundaries

**Do not repeat LfT2 or choose another obfuscated class without evidence.** To move Stage B, next distinct, narrowly scoped candidate must link *the current selected Track* to an **active**, not prefetch, native source/decoder by exact same-object proof on the signed NAV17 version. Existing [NAV17 Stage B source evidence](ANDROID-A1-NAV17-STAGE-B-PINNED-2025-FILEINFO-SOURCE-AUDIT-20261114.md) separates Exo source factory/open/read instance continuity from selected-item identity; an instance opening/reading is NOT selected-track proof. Media3 may accept MediaSource directly (not only MediaItem). Keep Stage B NO-GO until proof and owner-approved audio test.

No changes to original Yandex, NAV17, Test.50, frozen branches, runtime hooks, Android APK, Windows, extension, backend/API/DB or production. No reading/exporting Track/Album IDs/titles, URLs, DataSpec, account tokens, private field values, or audio bytes. All static work bounded, read-only and fail-closed. No full CI reports or large source dumps.
