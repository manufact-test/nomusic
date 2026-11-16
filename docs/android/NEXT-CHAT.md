# CELIKOM Android A1 — CURRENT HANDOFF

**Updated:** 16 November 2026  
**Canonical current state.** If any older Android note conflicts with this file, this file wins. Do not append history dumps.

## Checkpoint

- Repository: `manufact-test/nomusic`
- Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`
- Last code checkpoint: `27ccbe8348d598fead0386e70ef68573b04270c4`
- Code backup: `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116` @ same SHA
- Last runtime-hook change: `a655712d210189f3bc611847235de3ed4d985c1a`; no later hook changes
- CI #229: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139), signed Yandex 2025.10.4 #120.1gpr, 16 splits / 6 DEX, read-only
- CI #230: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101), compact summary only. Log reduced from 2,517,490 to 68,361 bytes (~97.3%); full report temporary and deleted
- Current docs-only backup before this reconciliation: `backup/android-a1-docs-hygiene-and-yandex-research-20261116` @ `01efbed6d4a382585a7105942f2b2925dcc32983`

No APK was built, patched, installed or released during CI #229/#230.

## Product status — newest decision takes precedence

- **Stage A / NAV17: PASS by owner confirmation (14 Nov).** The owner confirmed real Yandex account/UI, albums/My Wave and original Yandex music in CELIKOM.
- **Stage B: NO-GO / NOT CONNECTED.** CELIKOM replacement audio has not been proven audible. No selected Track → native source/decoder same-object chain is proven.
- Older 12–13 Nov documents that say Stage A NO-GO are historical pre-NAV17 status, not the current product state.
- Product architecture remains one CELIKOM APK with native Yandex UI/player and the same native playback path; no second Player/decoder/AudioTrack. Do not mistake a diagnostic/probe manifest for a complete packaging specification.

Owner evidence: [NAV17 Stage A and Stage B boundary](ANDROID-A1-NAV17-OWNER-REAL-MUSIC-GREEN-STAGE-B-SOURCE-ADAPTER-20261114.md).

## Yandex build matrix — exact roles

| Build | What is actually verified | What it is **not** |
|---|---|---|
| **2025.10.4 #120.1gpr**, code 24025542 | Publisher-signed XAPK, 45,961,661 bytes, SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 16 splits / 6 DEX. Used by 2025 LSPatch2 lab experiments and current static CI #229. | Not yet confirmed as the final product runtime target. |
| **2026.10.3 #170gpr**, code 24026531 | Publisher-signed XAPK, 60,433,885 bytes, SHA-256 `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`, 5 splits. Original-only native ARM13 control [CI #42990078186](https://github.com/manufact-test/nomusic/actions/runs/42990078186) passed package/signature/install/MAIN-liveness checks. The pinned helper `android/native-yandex-hooklab/clone_native_splits_ephemeral.py` also documents a separate structural clone trial using this #170gpr input. | Not the CI #229 LfT2 specimen. The cited original-only control did not test clone stability, login, audio, Play Protect or product readiness. Not automatically the final product target. |
| **2026.09.5 #167gpr / #167.1gpr** | Previously reported as installed on the owner's phone. | No exact publisher-signed original package and SHA are pinned in current A1 evidence; not a verified static specimen. |

Do not conflate #170gpr with #170rur (different distribution channel). Do not infer that the manifest `<queries><package name="ru.yandex.music"/></queries>` proves Yandex is embedded or absent; it only declares package visibility. Inspect actual packaged DEX/resources and build inputs.

**Target selection is still unresolved.** The CI specimen, original ARM13 control, phone-installed build and final CELIKOM product target are distinct evidence categories. The next chat must reconcile them before another long DEX trace.

## First task — determine the actual CELIKOM A1 source/runtime target

Do not immediately continue tracing obfuscated classes, and do not ask the owner the old false binary question “2025.10.4 or 2026.09.5?”

1. Inspect the current A1 packaging/build pipeline, private release inputs, source APK/XAPK references, split merge scripts, workflow pins and exact artifact history. Determine whether the current `pro.celikom.nativeprobe` build is the product clone or a diagnostic/probe. A package-visibility manifest entry alone does not answer this.
2. Compare the existing verified inputs above: #120.1gpr (CI #229 / 2025 clone lab), #170gpr (verified original ARM13 control and structural clone helper), and #167gpr (phone-reported only).
3. Establish which exact original build is the intended CELIKOM runtime/source. If repository/build evidence proves it, document the proof and proceed. If not, ask the owner once, with all three candidates and their different roles. Do not silently choose the newest version.
4. Before analyzing a selected build, verify the exact original package: publisher signature, package/version/versionCode, complete split set, size and SHA-256. Never transfer obfuscated descriptors between builds.

## Second task — only after target is established

The latest bounded route is specific to the signed **2025.10.4 #120.1gpr** DEX:

`LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>`

CI #229 proves the same TrackWrapper reaches the LfT2 constructor and is stored on that instance. The exact `LfT2.invokeSuspend(Object):Object` body was not found. No same-object handoff to MediaSource, MediaPeriod, DataSource, Extractor, Player or decoder is proven. `active_selected_item_proven=false`; `same_native_item_to_decoder_proven=false`.

After target build verification, inspect only exact `LfT2;` in that build:
1. class flags, superclass, interfaces and declared methods;
2. actual executable continuation entry, if any;
3. reads of the stored TrackWrapper and immediate same-object calls;
4. identity-proven edges into MediaSource / MediaPeriod / DataSource / Extractor / Player.
If no same-object handoff exists, close this candidate. No global scan and no repeat of the already proven chain.

Media3 allows direct MediaSource playlist APIs, so do not restrict the search to MediaItem. This is a search boundary, not proof of Yandex internals. See [external research](ANDROID-A1-EXTERNAL-PLAYBACK-RESEARCH-20261116.md).

## Closed routes — do not reopen

- `LiLb`: holder constructor/getter has no direct Player handoff; closed in CI #216. [Closure](ANDROID-A1-LILB-PLAYER-HANDOFF-CLOSURE-20261116.md)
- `LXk6`: inner List.get → MediaItem → Player mutator exists, but outer caller/runtime dispatch and List element provenance are unresolved; closed. [Closure](ANDROID-A1-PLAYLIST-CALLBACK-ROUTE-CLOSURE-20261116.md)
- Current-item getter / Player mutator evidence: [MediaItem/Player handoff](ANDROID-A1-MEDIAITEM-PLAYER-PLAYLIST-HANDOFF-20261116.md)
- ByteBuffer → native sink is separate; no current-item identity reaches it. [Renderer census](ANDROID-A1-RENDERER-FIELD-WRITER-CENSUS-20261115.md)

## Hard constraints

- Android CELIKOM A1 only; no Windows or browser extension work.
- No architecture/vendor/runtime-hook/APK changes during this read-only target-selection and static-analysis phase.
- No second Player, decoder or AudioTrack.
- Do not read/export Track/Album IDs/titles, URLs, DataSpec, tokens, account data, private field names/values or audio bytes.
- Do not touch NAV17, Test.50, frozen A1/LSPatch baseline, Windows, extension, backend/API/DB or production.
- Static inspection remains bounded, read-only and fail-closed.
- Work in one substantial block. No progress narration or repetitive reports.

## Documentation

[docs/android/README.md](README.md) is the entry-point/index. Follow [ANDROID-DOCUMENTATION-HYGIENE.md](ANDROID-DOCUMENTATION-HYGIENE.md). Archives and legacy handoffs are evidence storage, not startup reading.
