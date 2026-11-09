# CELIKOM Android — genuine native FileInfo source candidate / Gate 2 (2026-11-09)

## Decision and scope

**First HIGH-CONFIDENCE candidate found in a real Yandex Android client.** Still **not an installed or acoustically verified CELIKOM replacement**. Reuse exact publisher-verified HONOR target `ru.yandex.music 2026.10.3 #170gpr` / `24026531`, not WebView, companion's own player or double media streams. Work only in `experiment/android-native-yandex-gate1-20261109`. Stable, owner-accepted Test.50, original on phone, production server/catalogue untouched.

## Evidence — exact Yandex-signed native build

- Signed native #170gpr, 5 APK splits, official publisher SHA256 certificate independently matched to RuStore: `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba`. [Signed APK source audit SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42606555769). No APK stored or installed. This is **publisher integrity**, not a patched APK Play Protect verdict.
- [Native route annotation audit SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42609347093), exact verified #170gpr:
  - `com.yandex.music.shared.player.content.remote.fileinfo.FileInfoApi.a` with fixed route **`resources/v2/file-info`**.
  - `com.yandex.music.shared.player.content.remote.fileinfo.OldFileInfoApi.a` with fixed route **`get-file-info`**.
  - `com.yandex.music.shared.player.content.remote.downloadinfo.DownloadInfoApi.b` with **`tracks/{trackId}/download-info`**.
  - Obfuscated Retrofit annotation type `Lt4e;`. Method HTTP semantics and exact request/response data flow require separate verification.
- [Native caller graph SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42609598200), exact #170gpr:
  - `Lhee;->a(...)` directly invokes **`FileInfoApi.a`** and later `Lefh.l(Call,Continuation)`, then `Lsw7.y0(FileInfoDto,boolean): Leed`.
  - In fallback branch `Lhee;->a(...)` invokes **`OldFileInfoApi.a`**, then `Lefh.l`, then `Lsw7.z0(OldGetFileInfoDto,boolean): Leed`.
  - `Ln39;->a(...)` invokes `DownloadInfoApi.a`, itself delegating to `DownloadInfoApi.b`. The download-info path is related, but may not own audible playback.
- [Native model shape SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42609925869), exact #170gpr: `FileInfoDto` has **`urls: List`, `codec: String`, `bitrate: Integer`, `key: String`, `quality: String`, `gain: Boolean`, `r128: R128Dto`**. The two file-info versions convert into `Leed;`, an internal model with multiple fields including `String`, `List`, `boolean` and a likely source descriptor. This is a strong candidate for source selection, but no dynamic `MediaSource.prepare` proof.

## Rejected false candidate

`Lsy5 → Lqdw → PlayAudioApi` is a real static callgraph but its annotation route is `plays`, likely playback telemetry. This is **not** the CELIKOM audio hook. Do not replace it or intercept private account headers; [confirmed static path](https://github.com/manufact-test/nomusic/actions/runs/42608101050).

## Safe technical approach — only AFTER true in-process verification

1. In a disposable isolated native test host, verify **actual** selection of `FileInfoDto` / `Leed` for a known, legally playable `trackId` AND edition, and observe which original source goes into the native decoder **before prepare**. Confirm old/new file-info branch, codecs, `urls`, `key`, decryptor and native ownership. Limit logs to sanitized test IDs and source type; no tokens/audio dumps.
2. Use the existing CELIKOM service solely to resolve **rights-approved replacement** for the exact track+edition. Alternate must be complete/seekable, correct duration/codec/key semantics, HTTP Range compatible, available before changing Yandex's native source. Do not alter production API/database now.
3. Replace a **single source descriptor before preparation**, preferably at verified post-`FileInfoDto → Leed` entry if mutable/compatible, or just before native `MediaSource` creation. No own audio clock, no remote-player control. If track cannot match or stream isn't prepared, keep original. Avoid mid-play original→alternate oscillation.
4. Test native Pause/Seek/Next, album playlists, radio/random, repeated seeking, bluetooth, startup and fallback on separate hardware. Explicit Play Protect ON check is mandatory; CI/static signing says nothing about a repackaged build's reputation.

## Objective remaining blocker — source evidence vs install path

Even though a real first-party `FileInfoDto.urls` candidate now exists, **no runtime call-through into original decoder is confirmed** and no installable signed CELIKOM+Yandex modified host passed a real device/Play Protect test.

An unprivileged CELIKOM companion cannot inject into an untouched Yandex app process. A rootless patcher can modify a copied native APK, but it must be re-signed under a different certificate; the modified same-package app cannot update the currently installed store-signed `ru.yandex.music` in place. Side-by-side clone requires package changes and may impact Yandex login/deep links/updates. Both change onboarding and require **owner's explicit permission before implementation or any destructive install**. We have NOT requested such permission yet, installed no APK and changed no user data. Alternative root/disable Play Protect is out of scope.

**Gate 2 verdict:** `FileInfoApi → FileInfoDto.urls → Leed` is a **real, highly relevant static source candidate**. Gate to a manual-test build remains **closed** pending native in-process owner/decoder proof and a trusted rootless install strategy that the owner approves. Don't falsely mark replacement as working.

