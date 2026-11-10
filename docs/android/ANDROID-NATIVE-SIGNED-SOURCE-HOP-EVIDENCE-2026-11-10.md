# CELIKOM Android — signed native source-to-decoder graph gate (10 Nov 2026)

## Exact baseline

- Repo: `manufact-test/nomusic`
- Branch: `experiment/android-native-yandex-fileinfo-hooklab-20261109`
- Source-graph code (before this docs commit): `b807fe3b312823961b1c4d55fd669fcbc1df57d1`
- Backup: `backup/android-native-crossdex-source-hop-readonly-20261110`
- Prior code/docs baseline: `99511ac892ee4de1a12823a8ec7e12c4d3859bb3`
- Signed native Yandex: `2026.10.3 #170gpr`, `versionCode=24026531`, 5 signed split APK, 6 DEX. Archive/source/signer checked against pinned identities before scanning.
- This investigation is **read-only** and performed in GitHub Actions disposable CI. No Yandex credentials, user-account API, protected stream, DRM, native hook, phone, or original APK release involved.

## New verified facts

1. [CI 42777930530](https://github.com/manufact-test/nomusic/actions/runs/42777930530) **SUCCESS**: exactly **230,533** defined method bodies and **837,500** unique per-method invoke edges scanned across six signed original DEX files. Exact public-named Media3 source/prepare API method references detected by the original strict classifier: **0**.
2. [CI 42778116766](https://github.com/manufact-test/nomusic/actions/runs/42778116766) **SUCCESS**: confirms Media3 classes are nevertheless **present**: **33** defined `androidx.media3` classes with **384** method references. Legacy `com.google.android.exoplayer2`: **5** classes, **54** method references. Platform `MediaCodec`: 29 method references, `AudioTrack`: 30, `MediaExtractor`: 7. These are method namespace counts, **not audio source decoder trace evidence**.
3. [CI 42778216759](https://github.com/manufact-test/nomusic/actions/runs/42778216759) **SUCCESS**: when treating *any* signed-defined Media3 or ExoPlayer method as a **possible namespace-level target**, no direct or two-/three-hop invoke chains from exact converter caller (`sw7.y0/z0`) or `eed` model-consumer seeds appear **within each DEX**.
4. [CI 42778331313](https://github.com/manufact-test/nomusic/actions/runs/42778331313) **SUCCESS**: explicitly merges method-reference triples across **all six DEX** and repeats same bounded search. Unique seed methods: **1 converter caller** and **6 model consumers**. Both find **0 paths at distance 1–3** to either strict public Media3 source APIs or the broader named Media3/ExoPlayer namespaces.
5. Existing runtime gate remains **FAIL**: [CI 42776115700](https://github.com/manufact-test/nomusic/actions/runs/42776115700) reports clone MAIN starts then `ApplicationExitInfo REASON_EXIT_SELF=1, status=0`. `:AppMetrica` helper alone persists; original signed Yandex runs. Native launcher foreground/focused UI is **NOT** available. [CI 42775600758](https://github.com/manufact-test/nomusic/actions/runs/42775600758) confirms publisher app is neither debuggable nor shell-profileable. ART profiler requires publisher permission; no bypass.

## Interpretation

- **NO-GO on real in-process decoder/source verification**. There is a *static FileInfo API route* and source-model candidate (FileInfoDto to `eed`), but **no demonstrated call to native decoder prepare, no proven track+edition same-generation association, and no audible replacement**.
- Missing expected source/prepare method symbols is **not** proof that Media3 is unused: third-party R8/obfuscation, indirect function dispatch, reflection, cross-process or native library transitions are all possibilities, not proven facts.
- An invoke path would **not**, by itself, prove data-flow or playable source. More speculative static hops and duplicate manifest-only clone experiments are not a productive acceptance criterion.
- Legitimate next prerequisite is a publisher-approved in-process runtime host (explicitly debuggable/profileable signed app or documented source/plugin integration) **without** defeating third-party signature, Passport, Play Protect or DRM protections. Without it, the requested original-Yandex single-player replacement remains blocked.
- Existing separate CELIKOM Android Test.50 remains the owner-accepted **immutable baseline**, but its two-audio-clock architecture must not be revived as native replacement. Do not ship Test.77 or an unverified APK.

## Safe next step (no owner intervention now)

Stop speculative clone patch iteration. Preserve this static analysis and fail-safe single-player policy models. Identify and validate a permitted original-Yandex source boundary/integration via the rights holder or an authorized developer build before any `FileInfo → decoder` runtime claim. Only then investigate real `trackId + edition + generation` in a sandbox and one media source chosen before native prepare; first audio acceptance must include RASKOL 42884423, «Дым» 39949113, initial join artifact and Next/radio.

**No phone test, APK install, Yandex login, Play Protect change, production/backend, Windows, browser extension, or Test.50 modifications occurred.**
