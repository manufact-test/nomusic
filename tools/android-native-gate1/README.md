# LATEST — 2026-11-09 exact native HONOR #170gpr now available for SIGNED static audit

**IMPORTANT: supersedes old `#170gpr not obtained` statements below.** Exact `ru.yandex.music 2026.10.3 #170gpr (24026531)` acquired in ephemeral GitHub CI from APKPure XAPK (5 APK splits), validated by `aapt` and Android `apksigner` using the same Yandex publisher SHA256 certificate as independently obtained official RuStore `#170rur`: `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba`. [GPR CI SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42606555769). Publisher-verified XAPK SHA256 `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`. Binaries not retained or installed. [Code comparison SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42607424390); all method signatures equal, but not all method bodies equal across RUR/GPR. In-process audio-source mutation **NOT proven**.

The mapped `Lsy5; → Lqdw; → PlayAudioApi` has fixed static relative annotation route `plays` in the signed APK. That endpoint is **likely reporting/listening records rather than source URL selection**; exclude it from implementation until proven otherwise. See [full audit](../../docs/android/ANDROID-NATIVE-GPR-VERIFIED-2026-11-09.md). New isolated tools `trace_playaudio_boundary.py`, `trace_audio_neighbors.py`, `compare_dex_method_bodies.py`, `compare_gpr_rur_dex.py`, `trace_source_route_literals.py`, `audit_gpr_apkpure_once.py`. All require trustworthy native, signed input and are static/read-only; neither a patched APK nor a Play Protect pass is claimed.

---

# Native Yandex Gate 1 — read-only APK/XAPK inventory

**Purpose:** narrow an exact-version `ru.yandex.music` *media source boundary* using local, structurally parsed DEX method signatures. This tool does **not** patch an APK, hook it, read Android private data, install anything, connect to Yandex, or request Yandex credentials. It is intentionally **not** a new CELIKOM player or installable module.

## Usage (only with a lawfully obtained and trusted binary)

```bash
python3 tools/android-native-gate1/inspect_android_host.py /local/private/YandexMusic-2026.10.3.xapk --output /local/private/native-gate1-report.json
# Alternatively inspect explicit base and split APKs:
python3 tools/android-native-gate1/inspect_android_host.py /local/private/base.apk /local/private/config.arm64.apk
```

Supports APK, APK split sets, nested XAPK/APKS bundles; decodes DEX 035–041 structural class/method/prototype tables without running app code. Recognizes **candidate** Media3/ExoPlayer 2 source factory and queue methods, distinguishes a class *declared* inside a DEX from an external method *reference*, emits SHA256 per APK and a strict `NO_NATIVE_SOURCE_HOOK_PROVEN` verdict. No raw strings/tokens/URLs/audio dumped; only allowlisted media method signatures. No APK is uploaded or checked in.

**Security and verification:** do not run on the owner's primary phone. A third-party XAPK download is untrusted until checked against an independently verified official signature and authorized source; the tool's structural output does **not** validate APK signatures, publisher, dynamic behavior, rights, Play Protect or integration correctness. Never commit APKs, reports with confidential content or private device snapshots to this public repository. This script's synthetic tests avoid all third-party binary inputs. Runtime proof requires a separately controlled native test-client and permitted in-process observation of the *real* catalog track+edition ID **at the pre-playback source selection point**, then one-source native Play/Pause/Seek/Next.

**Confirmed target inventory:** last owner HONOR Android 13 `2026.10.3 #170gpr` code `24026531`; the public APKPure listing offers both armeabi-v7a and arm64-v8a XAPK variants of this version, with a base `ru.yandex.music.apk` plus config splits. **These listings are not proof of binary authenticity or compatibility.** We did not acquire, execute or install these packages. Relevant public listing: https://apkpure.net/yandex-music-books-podcasts-app/ru.yandex.music/download .

## Test and CI

```bash
python3 -m unittest discover -v -s tools/android-native-gate1/tests
```

Seven synthetic-only tests: candidate DEX detection, reference-only negative, allowlist negative, no-DEX rejection, nested XAPK split, bad DEX header, damaged table bounds. CI [run #42597718915](https://github.com/manufact-test/nomusic/actions/runs/42597718915) **SUCCESS**, Python syntax, tests and absence of Android binaries in tool folder. This proves the inspector works on synthetic fixtures **only**.

## What is STILL missing

- Audited actual `2026.10.3 #170gpr` host APK class inventory. Neither this repository nor CI contains an actual Yandex APK.
- A verified *executed* native player hook before prepare and exact catalog ID + edition metadata. A media3 factory method reference alone is insufficient.
- A lawful, privacy-safe, normal no-root installation plan with Play Protect ON; a differently re-signed `ru.yandex.music` cannot update the existing official app in place. No destructive owner-phone action is approved.
- One-player native seek/pause/next/radio test and account safety. **No signed APK has been produced by this work.**

See `docs/android/ANDROID-NATIVE-YANDEX-GATE1-SOURCE-AUDIT-2026-11-09.md` for exact source-level NO-GO and trust issues with existing Xposed examples.

## Latest verified native Android research — 2026-11-09

A **real official publisher-signed native Yandex RuStore APK**, `2026.10.3 #170rur` code `24026531`, was downloaded **only into ephemeral CI scratch space**, verified by Android `apksigner` v2/v3 and against the public RuStore signing SHA256 `aca405ded8b25cb2e8c6da69425d2b4307d087c1276fc06ad5942731ccc51dba`, scanned then deleted. APK SHA256 `dfa1091383ee9fead30f8bb34eb01b46d7705ae8ab400b8abfbc73c271e5bcde`. [Static proof #42599929142 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42599929142); [expanded media surface #42600494250 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42600494250). Six DEX; internal native Yandex playback/queue/media session classes and `PlayAudioApi` identified, 24 framework media invokes on classes3. **No actual source-replacement hook proven.**

New files: `trace_native_callers.py` (bytecode callsites, **not raw string matching**), `inventory_native_media_surface.py` (Yandex native playback class/method surface), `probe_rustore.py` (public store metadata), `audit_rustore_host_once.py` (ephemeral signed official APK check), `audit_gpr_aptoide_once.py` (exact Google Play channel attempt with signature/manifest gate, **not successfully sourced**). Do **not** publish, distribute, run or install third-party Yandex APKs. [Unit tests #42601003730 SUCCESS — 24 cases](https://github.com/manufact-test/nomusic/actions/runs/42601003730).

**Exact HONOR #170gpr still not obtained.** Public APKPure/Aptoide pages list it, but Aptoide API exposed a 2020 fallback and its documented version-pinned request returned HTTP 404. This correctly aborted before downloading. The `#170rur` signer pin must **not** be assumed to match Google Play signing; mismatches are blockers to investigate, not bypass. Full evidence: `docs/android/ANDROID-NATIVE-YANDEX-ACTUAL-SIGNED-APK-SURFACE-2026-11-09.md`. No owner phone action or installable CELIKOM candidate exists.
