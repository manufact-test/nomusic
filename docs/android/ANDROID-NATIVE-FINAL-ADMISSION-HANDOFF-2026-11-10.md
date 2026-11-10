# CELIKOM Android — final admission-contract checkpoint / handoff (10.11.2026)

## 0. What owner actually wants

CELIKOM should assist the **one actual native Android Yandex.Music player**. The user signs in ONLY inside Yandex, listens via its authentic UI, playlists and radio, with native seek/pause/next. A rights-confirmed approved alternative can become the **one chosen audio source BEFORE native decoder prepare**, never a second CELIKOM MediaPlayer playing beside Yandex. No WebView, synthetic player presented as native, root requirement, OAuth interception, DRM/signature/Play Protect bypass, or reinstall of the owner's official app.

Repo: `manufact-test/nomusic`.
Working branch: `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
**Code HEAD verified before this documentation-only commit:** `6ee199858e25ceddcc229cd1ad51b0bb5526b8ab`.
**Code backup:** `backup/android-native-preprepare-final-code-20261110`.
**Earlier backup:** `backup/android-native-pre-final-admission-gate-20261110`.
Accepted Android Test.50 remains a separate owner-accepted historical baseline: DO NOT modify.
After this document is committed, obtain the **current branch HEAD** (the docs commit).

## 1. Verified existing publisher-native host evidence

| Layer | Result | Evidence |
| --- | --- | --- |
| Pinned genuine Yandex.Music Android `2026.10.3 #170gpr`, five splits / six DEX, publisher signed | Original runs on isolated Android 11 x86 with ARMv7 translation | Earlier original control CI; see `ANDROID-NATIVE-HANDOFF-2026-11-10.md` |
| Independent different-package clone installed alongside original (5+5) | **NO-GO MAIN UI**. MAIN starts/dies, `ApplicationExitInfo.reason=EXIT_SELF(1), status=0`; `:AppMetrica` helper remains; publisher-original runs | [strict CI 42776115700](https://github.com/manufact-test/nomusic/actions/runs/42776115700) FAIL exactly as expected |
| Attempted sorted AppMetrica identity correction | Same MAIN self-exit; old A/B retired, **do not repeat** | [CI 42706194581](https://github.com/manufact-test/nomusic/actions/runs/42706194581) |
| Exact signed manifest ART trace permission | `debuggable=false`, `profileable shell=false`; no publisher authorization to profile | [CI 42775600758](https://github.com/manufact-test/nomusic/actions/runs/42775600758). Profiler auto workflow disabled |
| Static signed Yandex FileInfo request | FileInfoApi/OldFileInfoApi param 0 annotated as trackId; `FileInfoDto -> sw7.y0/z0 -> eed` is a **static source candidate** | `ANDROID-NATIVE-TRACK-IDENTITY-EVIDENCE-2026-11-09.md` |
| Signed 6 DEX static model-to-Media3 graph | 230,533 method bodies, 837,500 invoke references; Media3 present (33 classes/384 refs). No 1–3-hop chain from identified FileInfo model to named Media3/ExoPlayer across all DEX. **This bounded negative does not prove the decoder absent** | [CI 42778331313](https://github.com/manufact-test/nomusic/actions/runs/42778331313) SUCCESS |
| Official Android external MediaSession/MediaController | Playback transport/control only; **not** a general cross-UID method for injecting a source into another app's native decoder | Android: https://developer.android.com/media/media3/session/control-playback and https://developer.android.com/reference/androidx/media3/session/MediaController |
| Authorized rootless in-process modified Yandex with reliable native playback | **NOT PROVEN** on isolated host or owner's HONOR, no Play Protect verdict, no catalog ID+edition at actual decoder | **NO-GO for user APK and native replacement** |

The signed Android original is not a currently usable in-process CELIKOM host on an ordinary unprivileged separate app. Yandex developer-approved audio-source plugin/SDK availability has **not been verified**. A third-party `MediaController` command is not a native audio source replacement. Do not conflate feasibility research with a shipped product.

## 2. What was actually IMPLEMENTED and CI-VERIFIED in this final batch

Pure-Java, permissionless, **not wired into publisher runtime**:

- `android/native-yandex-hooklab/app/src/main/java/pro/celikom/yandex/nativehooklab/NativePrePrepareAdmission.java` — new atomic coordinator combining the existing `NativeTrackIdentityGate` and `NativeSourceGate`.
- `android/native-yandex-hooklab/tests/src/NativePrePrepareAdmissionTest.java` — exact track + edition + generation; FileInfo and actual decoder descriptor must **both** match before a single-source pre-prepare decision; missing/blank identity, conflicting editions, unready/expired source, aborted generation, replay/late old generation, 5,000 fast Next transitions and duplicate prepare all fail closed.
- `NativeSourceGate.java` changed to return **UNDECIDED** for rejected/stale/late/duplicate source offers; it no longer exposes another selection's `ALTERNATE` choice on a rejected callback. Regression added in `NativeSourceGateTest.java`.
- CI updated `.github/workflows/android-native-yandex-hooklab.yml` to compile/run the new coordinator with existing original model contracts. It does **NOT** install a Yandex-clone or attach a native hook.

**[CI #42780177178](https://github.com/manufact-test/nomusic/actions/runs/42780177178) SUCCESS, 2/2 jobs.** Exact confirmed log results:
- `NativeSourceGate` **10,037** assertions PASS.
- `NativeTrackIdentityGate` **10,015** assertions PASS.
- `NativePrePrepareAdmission` **35,032** assertions PASS (includes 5,000 synthetic Next races).
- Gradle Android read-only CELIKOM module builds SUCCESS; metadata/signature verified. No media player, mutable hook result, credential capture or dangerous permission.
- These are **synthetic JVM policy assertions and module-build checks**. They do NOT show real Yandex `FileInfo` runtime, decoder `prepare`, sound, login, Bluetooth, device Play Protect or native seek success.

The material logic bug found in this batch: a rejected *stale* proposal previously returned the **current** generation's `ALTERNATE` choice alongside `STALE_REVISION`. Now a rejected proposal returns `UNDECIDED`, not a usable selection. This prevents mistaken caller implementation from treating a rejection as permission to change source.

## 3. Remaining hard blocker and next substantive work

**Current release/in-process verdict is NO-GO**, not "almost ready". There is still no safe verified execution path to place CELIKOM inside the real original Yandex playback source selector. The different-package clone exits before UI; publisher disallows ordinary shell ART tracing; rootless LSPatch loader had ABI/translator faults on tested x86 emulators (see `ANDROID-NATIVE-LSPATCH-EMULATOR-ROOT-CAUSE-2026-11-09.md`). Do not repeat those exact failed emulator runs, AppMetrica patch, speculative Media3 symbol hops, two-player DSP, WebView or own audio smoke.

Next developer, in this order:

1. **Confirm present code/CI and preserve backup**. Do not overwrite Test.50, Windows, extension, backend, DB, moderation, tracks, main HONOR app.
2. **Investigate genuinely authorized access to the native source boundary**, such as an openly documented publisher-supported plugin/SDK, a publisher-approved instrumented build, or explicit permitted compatibility agreement. Verify specific source/provenance/rights and whether it actually gives `trackId + edition + source-before-prepare`, not just playback controls, UI or unofficial login API. Do not invent an SDK or infer license from availability.
3. If there is no genuinely usable authorized native host, maintain **NO-GO** and make an explicit feasibility/owner-choice proposal. Do not silently substitute a second player or issue a "working" APK. Next iteration can improve tests/docs, but another random repackaging attempt is NOT evidence.
4. **Only after a viable permitted in-process host exists:** witness exact native track and edition, FileInfo model, same-generation descriptor handed to native decoder BEFORE prepare. Integrate the already-tested `NativePrePrepareAdmission` with trusted actual host calls and approved CELIKOM source broker; audit rights, codec, Range, crypto, duration. Keep original unless all checks pass. No original→alternate mid-play flicker.
5. **Only then device QA with owner authorization and separate spare ARM device** (Play Protect ON): RASKOL ID `42884423`, «Дым» ID `39949113` pause/seek, intro click, radio/playlist Next, Bluetooth, standby, VPN. Do not ask to uninstall or tamper with original Yandex on primary HONOR.

**No owner action is needed now**, and no phone APK was delivered. Explicitly call out lack of usable authorized host if that remains true. Future diagnostics are categorical/privacy-safe, never raw request/token/log/stream dumps.

## 4. Scope unchanged

The owner's accepted Test.50, official Yandex installation, other Android branches, Windows companion, browser extension, server, database, production and user music catalog were not altered. All final code in the isolated native hooklab branch, backup created. No license to distribute a repackaged proprietary Yandex APK is assumed.


---

## FINAL CHECKPOINT 10.11.2026 — legitimate public MediaSession experiment, NO usable source host

**Code HEAD:** `dc61cd8d7f6c116d91e74ae30c174a50528cde83`. **Immutable backup before docs:** `backup/android-native-public-session-final-evidence-20261110`. This is a *first-party CELIKOM-owned, read-only diagnostic* against the **genuine pinned publisher-signed Yandex**, not a native audio replacement and not a patched host.

**Verified CI:**
- [42782747091](https://github.com/manufact-test/nomusic/actions/runs/42782747091) SUCCESS, static signed five-split manifest. Three media service declarations, two `MediaBrowserService` actions; one explicit exported, enabled and without manifest permission binder candidate. This does **not** imply externally replaceable audio.
- [42783663050](https://github.com/manufact-test/nomusic/actions/runs/42783663050) SUCCESS test mechanics; cold guest-free disposable Android 11 controller handshake **not established**. `COMMAND_CHANGE_MEDIA_ITEMS` false only because controller was not connected.
- [42784630427](https://github.com/manufact-test/nomusic/actions/runs/42784630427) SUCCESS test mechanics; fallback through the platform `MediaBrowser.connect()` to that exported candidate **rejected**: `PUBLIC_BIND_REJECTED`. No playback command ever sent.
- [42785272172](https://github.com/manufact-test/nomusic/actions/runs/42785272172) SUCCESS test mechanics **after a single bounded launch of the unmodified original guest UI on isolated emulator** and verifying MAIN process exists: still **`PUBLIC_BIND_REJECTED`**, Media3 not connected, platform browser not connected. No login or account involved.
- [42785272231](https://github.com/manufact-test/nomusic/actions/runs/42785272231) SUCCESS existing synthetic hooklab jobs, **not publisher audio**.

**Narrow interpretation:** public *manifest* service candidate does not permit third-party controller access in the tested **unauthenticated disposable environment**. Exact binder rejection condition is **not known**; no claim about a logged-in publisher app or anti-tamper. The test did not call `replaceMediaItem`, `setMediaItem`, play/pause, seek, URL, FileInfo or decoder; no user metadata was read. Android `MediaController` may permit queue changes only if session owner advertises the required commands; here there was no connected controller to inspect. This does **not** establish a native pre-prepare source replacement.

**Engineering admission:** NO-GO for the requested exact original-Yandex one-player alternative audio source. There is **no verified supported publisher source API/SDK, authorized instrumented host, or runtime `track+edition+generation -> real decoder source` witness**. Stop additional emulator/package or speculative DEX experiments unless an actually new lawful host capability appears. No new user APK or manual QA now. Explicit next dependency: publisher-approved integration/compatibility agreement identifying actual source-before-prepare API and rights/DRM limits. Test.50, official HONOR, Windows, extension, server, DB and production untouched.

