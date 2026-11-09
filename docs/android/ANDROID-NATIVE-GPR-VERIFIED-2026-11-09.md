# 2026-11-09 · New exact #170gpr native FILE-INFO source candidates (read this first)

**Critical finding:** The exact publisher-signed native `2026.10.3 #170gpr`, `24026531`, does contain REAL first-party API interfaces under `com/yandex/music/shared/player/content/remote/`, not merely a speculative `PlayAudioApi`. From the actual exact signed XAPK's `classes4.dex`, we decoded safe compile-time Retrofit annotation routes and method signatures:

| Native Yandex interface | Obfuscated method | Static media route |
| --- | --- | --- |
| `com/yandex/music/shared/player/content/remote/fileinfo/FileInfoApi` | `a(String,String,String,String,long,String,Integer,Integer,String): retrofit2.Call` | **`resources/v2/file-info`** |
| `com/yandex/music/shared/player/content/remote/fileinfo/OldFileInfoApi` | `a(String,String,String,String,long,String,Integer,Integer,String,String): retrofit2.Call` | **`get-file-info`** |
| `com/yandex/music/shared/player/content/remote/downloadinfo/DownloadInfoApi` | `b(String,Boolean,Boolean,String): retrofit2.Call` | **`tracks/{trackId}/download-info`** |
| `com/yandex/music/shared/generative/data/GenerativeApi` | `b(String,String): retrofit2.Call` | `rotor/station/{stationId}/stream` (separate radio/generative path; don't confuse with track bytes) |

**Proof:** [GitHub Actions #42609347093 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42609347093), exact Google Play channel version, cryptographic signer/manifest gates passed before inspection, 1,105 method annotations examined on the owning DEX. All identified route annotations use obfuscated `Lt4e;` (the exact HTTP verb is not independently proven by this alone). No APK, credentials, audio content or arbitrary annotation values are retained/logged. This is **real, highly relevant static source-boundary evidence**, though not proof of runtime execution or ability to replace the MediaSource in place. An isolated caller-graph audit of these three API interfaces is now in `tools/android-native-gate1/trace_source_api_consumers.py`.

**Important rejection retained:** `PlayAudioApi` is annotated with route `plays`, likely playback reporting. It should NOT be treated as the substitution hook. We now favor the first-party `fileinfo` and `downloadinfo` boundary for *read-only runtime verification* of track+edition-to-source mapping before modifying playback.

**Remaining safety gate:** Avoid externally controlled double players, WebView, root and OAuth interception. A patched native Yandex APK re-signed by CELIKOM cannot silently update the genuine existing Yandex package. Any uninstall/clone/install behavior requires owner approval; Play Protect ON acceptance requires a physical device test and cannot be claimed from static CI. No test APK ready; never touch Test.50, stable production, song database or owner phone.

---

# UPDATE / source-boundary correction — 2026-11-09

**Critical correction to section 3:** On the publisher-signed native `#170rur` DEX, the obfuscated `Liml;` method annotation on `PlayAudioApi.a` has safe static route literal **`plays`**. Verified without accessing credentials or content in [GitHub Actions #42608101050 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42608101050). This makes the `Lsy5; → Lqdw; → PlayAudioApi` graph **more consistent with reporting/accounting of plays than with pre-prepare stream URL selection**. It remains a factually correct callgraph, but **must not be selected as the CELIKOM audio replacement hook** on available evidence. The HTTP verb/semantics and server response are not proven; infer only a likely reporting role, not certainty.

Current next step: bounded search for real `stream/source/download-info/track` API route literals and corresponding invoked methods, then a test-environment witness of exact track+edition and the live native source owner **before decoder prepare**. No new user-facing APK or destructive installation.

---

# CELIKOM Android — exact native #170gpr is now obtained & publisher-verified (2026-11-09)

**Status: genuine progress, but NOT a working replacement.** This supersedes the claim in the previous Gate 1 report that exact #170gpr had not been acquired. The source audit of `#170rur` is retained for history. All changes are isolated on `experiment/android-native-yandex-gate1-20261109`; not merged to stable CELIKOM or Test.50.

## 1. Verified genuine native Android Yandex host (without touching owner device)

- **Package:** `ru.yandex.music`.
- **Owner's exact Google Play release:** `2026.10.3 #170gpr` code `24026531`. Found an XAPK from public APKPure download endpoint; **5 split APKs**. Size 60,433,885 bytes; XAPK SHA256 `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`.
- **Android SDK integrity evidence:** `apksigner verify` passed on every split; manifest package and versionCode verified, base APK versionName exactly `#170gpr`.
- **Publisher certificate on all splits:** SHA256 `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba`; **identical to the certificate independently verified for official RuStore `#170rur`**.
- [CI #42606555769 SUCCESS — exact #170gpr version, package and signer verified](https://github.com/manufact-test/nomusic/actions/runs/42606555769).
- **Strict boundaries:** 3rd-party host download is not proof of Play Protect acceptance. Binaries existed ONLY in ephemeral CI temporary folders; no installs, execution, account access, publishing or long-term artifacts. No phone work or password requested.

## 2. Comparison with official RuStore #170rur

Both publisher-signed releases are 6 DEX, **57,161 classes, 319,816 method IDs**. The six DEX SHA256 hashes are ALL different, so **byte-for-byte equivalence is false**. Instead we compared DEX type descriptors, method signatures and each method's decoded instruction array, without executing any code.

[CI #42607424390 SUCCESS — semantic code comparison](https://github.com/manufact-test/nomusic/actions/runs/42607424390):

| DEX | Methods with code | Changed code bodies (#rur to #gpr) | Type & method signatures |
| --- | ---: | ---: | --- |
| classes.dex | 38,894 | **5** | Equal |
| classes2.dex | 1,204 | **0** | Equal |
| classes3.dex | 44,862 | **0** | Equal |
| classes4.dex | 47,413 | **1** | Equal |
| classes5.dex | 51,761 | **1** | Equal |
| classes6.dex | 46,399 | **6,349** | Equal |

All method signatures match across both channels; however **many instructions differ in classes6**, so no blanket equivalence claim. Named audio classes and targeted `Lqdw;`/`Lsy5;` callsites did not appear among changed code bodies. Further compatibility must be exact-version-scoped.

## 3. Actual confirmed Java/Kotlin flow of the native target

The path **exists in both signed builds**, not a made-up Xposed interface:

```text
Lsy5;->invokeSuspend(Object)
    -> Lqdw;->a(Lqdw, List, Continuation)
         -> Lku8;->w(List): BulkPlaybacksRequestDto
         -> PlayAudioApi.a(String, BulkPlaybacksRequestDto): retrofit2.Call
         -> Lxcn;->u(Call, Continuation): Object
```

The call is proven by native DEX opcode `invoke-interface 0x72`; static [#42605769031](https://github.com/manufact-test/nomusic/actions/runs/42605769031) and upstream [#42606338503](https://github.com/manufact-test/nomusic/actions/runs/42606338503), both SUCCESS. The interface is defined in `classes4.dex`; `classes.dex` invokes it. In `classes4.dex` its method has `Ldalvik/annotation/Signature;`, `Lorg/jetbrains/annotations/NotNull;`, and **obfuscated annotation `Liml;`**; method-annotation types were independently parsed in [#42607929938](https://github.com/manufact-test/nomusic/actions/runs/42607929938). The annotation's meaning is NOT yet certain; direct standard `Lretrofit2/http/POST;` name is not present.

**Caution:** The existence of `PlayAudioApi` or a `BulkPlaybacksRequestDto` **does not prove** this is where a stream URL enters the same native decoder. It could be unrelated accounting or queue-related playback reporting. No extraction or interception of OAuth headers, tokens, copyrighted stream contents or private device files has occurred. Need actual input/response semantics (sanitized test data only) and source-owner proof before mutation.

## 4. Source and tests added

- `tools/android-native-gate1/audit_gpr_apkpure_once.py`: exact signed #170gpr acquisition in ephemeral CI.
- `tools/android-native-gate1/compare_gpr_rur_dex.py` and `compare_dex_method_bodies.py`: semantic DEX equality, with no APK files retained.
- `tools/android-native-gate1/trace_playaudio_boundary.py`: public method-level HTTP-annotation and strict cross-DEX callsite inventory; only safe static routes shown.
- `tools/android-native-gate1/trace_audio_neighbors.py`: upstream coroutine flow and invoke neighbors, never secret-bearing strings.
- Regression fixes for DEX long string handling; synthetic tests [#42607517652 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42607517652). 

## 5. Objective remaining blockers — STOP before any installable APK

1. **No proven in-process SOURCE-SELECTION hook:** trace `PlayAudioApi` response to a **real original Yandex decoder** with exact track and edition before `prepare`, then fail-safe original on unavailable alternate. Static callgraph isn't dynamic confirmation.
2. **Rootless integration and installation UX:** an ordinary app with Android sandbox privileges cannot rewrite the playback state and audio source inside the unchanged foreign `ru.yandex.music` process. LSPatch can patch APK without root, **but the patched package must be re-signed**; Android won't allow update over store-signed official APK with different signer. Removing or cloning Yandex changes account/install behavior and requires owner **approval BEFORE coding/distributing**, never a silent decision.
3. **Play Protect ON:** published signer validation is different from *patched* APK device install/reputation review. No Play Protect claim without actual test on a spare device, and no bypass request.
4. **Legal/privacy:** audit any licensing/distribution implications of a modified proprietary Yandex client. CELIKOM must never request Yandex password, intercept OAuth tokens or force root/disabled protections.
5. **Quality gate:** a successful implementation must use Yandex's own sole playback clock/decoder and obey native Play/Pause/Seek/Next, playlists, random radio, uncached fallback. No WebView or double-player overlay.

**Decision:** One genuine signed host and a real candidate callgraph exist. **No verified source substitution, no Play Protect pass, no installable candidate yet.** Continue source-only and isolated technical research. Do NOT repack or ask owner to uninstall original until source hook proven and explicit owner decision on changed install path.

