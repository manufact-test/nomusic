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
