# CELIKOM Android — native-Yandex preflight for real failures (2026-11-09)

## Owner confirmation

On 2026-11-09 the owner listened to the independent CELIKOM ARMv7 Audio Smoke Test on HONOR 50, Android 13. **Audible source swaps, Pause/Resume, Seek, Next and original fallback worked** per owner. Prior screenshot `Screenshot_20261109_193331.jpg`: Module ARMED YES, Source changed BEFORE PREPARE YES, Prepare=3, Pause=1, Resume=1, SeekComplete=1, Next=1, Errors=0, Last STOPPED. These are OWN-app Android MediaPlayer results, **NOT** Yandex native audio results.

## Defects from old two-player app — reproduced in forensic evidence

- **RASKOL «Нас не понимают вообще»**, Yandex track `42884423`, and **Лёша Свик «Дым»**, `39949113`: Test.74 independent Android framework callbacks observed seek and pause correctly, while external Media3 bound to Yandex published seeks ~3.102–3.282 seconds late and sometimes kept `isPlaying=true` through a real pause. The CELIKOM second MediaPlayer was seeking/pausing from that stale controller. The new native route must never reintroduce a second playback clock or external-controller-derived seek sync.
- **«Пшик»/start overlap**: Test.31 used **16** commanded 160ms blends and still had an audible artifact; four post-seek re-grants used 0ms. Two audio output sessions lacked proven sample alignment. A single native decoder with the source chosen **before prepare** should eliminate that specific double-player handoff cause, but **acoustic success is not established**.
- **Cold joins/coverage**: Test.31 «Толер» entered replacement after an insufficient sparse buffer and then fell back; «Метамир» took ~11.8 seconds to grant. Never promote a partial alternate stream to the native decoder without decoder/key compatibility, seekable Range and proven contiguous playback runway.
- Test.76 did not fix the issue; its framework witness was disabled and RASKOL remained stalled. The old Test.50 is the owner-accepted safety reference only, not native Yandex audio acceptance.

## Implemented now (experiment branch ONLY)

1. `NativeSourceGate.java`, a **pure-Java pre-prepare admission contract**, not yet activated in the native Yandex hook. Single selection per track+edition; exact edition check; generation fencing across Next; bounded resolve time; rights/codec/crypto/duration/Range/runway all must be explicitly verified to select alternate; fail original if not; never flip already-playing audio back mid-song.
2. `NativeSourceGateTest.java` — [CI 42658954205](https://github.com/manufact-test/nomusic/actions/runs/42658954205) SUCCESS **10,031 JVM assertions**, including 2,500 rapid Next cycles, RASKOL/Dym 3-second delayed remote signals, no double source commit and no automatic post-playback blend. These are **model/logic tests**, not audio-in-Yandex or actual buffering measurements.
3. Signed #170gpr 5-split static source graph [CI 42659786583](https://github.com/manufact-test/nomusic/actions/runs/42659786583) SUCCESS: 6 DEX, 230,533 defined methods scanned, 6 model-consumer bodies, model converter `Lhee.a → Lsw7.y0/z0 → Leed` confirmed. Candidate downstream `Lged.a` calls `Leed.a():String`; [CI 42660229676](https://github.com/manufact-test/nomusic/actions/runs/42660229676). **NO direct Media3 source creation proved**: media classes are obfuscated or not within this precise graph. Do not call this native decoder/MediaSource verification.
4. `NativeHookEntry` now has optional **read-only invocation counter** for exact `Leed.a():String` accessor in addition to the modern/legacy FileInfoDto converters. **No string values, URLs, keys, IDs, account data or audio are read/logged**, and no source is mutated. If exact accessor is missing, original converter hooks remain unaffected. Native hook is not installed on owner's original Yandex.
5. Build/signing: original `ru.yandex.music` on HONOR must remain installed; the re-signed same-package host cannot update over publisher cert. Parallel native clone requires compatible new ID for all 5 splits, 9 package-bound provider authorities, its DEX runtime assumptions and normal auth. This is **not validated or built** and may be blocked by Play Protect/app-integrity checks.

## Next manual native-client test gate (NOT executed yet)

- Only after an isolated signed, non-conflicting native test-client install path is proven, with Play Protect ON and no Yandex credential extraction, test Yandex original decoder **first without modification**, using control vs RASKOL and «Дым».
- Confirm hook counts + per-stage redacted telemetry: exact FileInfo conversion, source descriptor before native prepare, actual start, native pause acknowledgement, native seek acknowledgement, Next. Absence of evidence is NOT_OBSERVED.
- Only after a real pre-prepare decoder path is confirmed: rightsholder-approved alternate on one song, with known codec/key/seek/range/duration/runway and native original fallback. No synthetic `file-info` response that strips key/iv.
- **Owner acceptance tests**: (a) RASKOL/Dym native Pause/Seek immediate and audible; (b) no audible `пшик` on first join; (c) playlist Next and random radio join, 20 rapid switches; (d) full-track ending and mid-track seek; (e) genuine Play Protect installation scan. CI pass never substitutes for on-device sound and protection verdict.
- If same-package sign conflict cannot be resolved without deleting owner's original app, stop; do NOT ask owner to turn off Play Protect, use root, bypass integrity, or remove official Yandex as a shortcut.

## No changes

Official installed Yandex, downloaded music/account, stable Android, accepted Test.50 backup, extension, Windows, production API and database remain untouched.

## Parallel install feasibility result: BLOCKED, not a music regression

The first ephemeral native client clone experiment confirmed source APK signatures and all 5 splits but failed resource reassembly under Apktool 2.12.1; [CI 42662932538](https://github.com/manufact-test/nomusic/actions/runs/42662932538). This is a separate packaging/Android resource framework block. Neither successful owner synthetic audio tests nor 10,031 model assertions prove patched Yandex Play Protect acceptance or source swap. Do not distribute any third-party clone binaries, delete official Yandex, disable Play Protect, or imply the native product is ready.
