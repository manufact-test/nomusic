# CELIKOM Android — real signed ExoPlayer implementation census + ARM CI feasibility, 10.11.2026

## New actionable facts (NOT native audio playback)

**Pinned authentic Yandex Android:** publisher-signed `ru.yandex.music 2026.10.3 #170gpr`; exactly **five split APKs, six DEX, 57,161 class definitions**. `audit_native_media_engine.py` and `audit_native_media_implementors.py` both verify the full pinned original archive, publisher signer and split set. They never install or execute Yandex, touch the account, read tracks/stream keys, or publish APK/DEX/media.

1. **[CI #42791262439 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42791262439):** original app contains only **7 classes** under `androidx.media3.exoplayer` namespace and an `ExoPlayer` **interface**. It does **not define** the standard `androidx.media3.exoplayer.ExoPlayerImpl`, `DefaultMediaSourceFactory`, `ProgressiveMediaSource`, `DefaultDataSource`, `androidx.media3.common.MediaItem`, or the named equivalent legacy ExoPlayer2 classes. Static absence of the *named* classes does NOT imply no audio engine: they may be obfuscated/shaded/implemented via other packages.
2. **[CI #42791641169 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42791641169):** following actual DEX `class_def` superclass+implemented-interface graph, exact Media3 `ExoPlayer` has **four concrete implementors**, compiler-obfuscated: `Lfxc;`, `Lro7;`, `Lwxc;`, `Lyzt;`. Legacy `ExoPlayer2` interface was not defined (zero implementors). This is a real structural clue, NOT proof that any is actively playing music.
3. **[CI #42791829407 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42791829407):** across those four implementors **zero concrete `prepare()V` method bodies** and **zero matching inherited `prepare()V` method bodies** in the exact scanned inheritance graph, including abstract superclasses and interfaces. Thus hooking a guessed standard `ExoPlayerImpl.prepare` would be unsupported in this signed build. Do **not** install speculative `prepare` hooks against these four classes yet. Interface methods could be renamed/implemented via other infrastructure; static negative is bounded and does not prove native source absence.
4. **[CI #42791829435 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42791829435):** existing read-only native CELIKOM module build and synthetic tests pass with new audit sources. This does **not** certify a runtime hook inside actual Yandex.
5. **[CI #42792130918 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42792130918):** a **real native AArch64 Linux hosted runner** (`ubuntu-24.04-arm`) exists for our GitHub CI, but **`/dev/kvm` is not accessible for read-write**, and neither `qemu-system-aarch64` nor Android emulator is preinstalled. It is a Linux ARM build host, **not** a running Android native ARM device. It does not solve our guest Android runtime gate. Prior Apple Silicon Android ARM emulation also failed HVF virtualization; this is a DIFFERENT, one-time probe, not another x86 rerun.

## Engineering decision

**Real in-process native Yandex source replacement is still NO-GO**. We have an exact FileInfoDto converter pair candidate (`sw7.y0/z0 → eed`), and now narrowed possible R8-obfuscated `ExoPlayer` implementations; there is still **no witnessed relation** `current real trackId + edition + generation → FileInfo → chosen source in the actual decoder BEFORE prepare`. User-facing APK must not be offered as working.

**Do not**:
- contact Yandex, suggest official SDK/partner outreach (owner rejected);
- revive the rejected WebView, dual MediaPlayer or different-package clone;
- repeat old x86 LSPatch loader failures, AppMetrica patch guesses, broad class-name hooks or a synthetic test as proof of music;
- uninstall or modify real Yandex on the owner's HONOR, disable Play Protect, root, spoof signatures, access tokens/DRM, or publish repackaged Yandex.

**Next genuine prerequisite:** a separately authorized compatible **native ARM Android** runtime capable of safely running a prepared compatible natively signed package under normal security checks; record only the single native-Yandex read-only hook, real current edition and decoder-source identity. Without it, remaining static method search has diminishing returns. Do not ask owner to manually test until a real native candidate exists.

## Code and rollback

New, isolated reusable source:
- `android/native-yandex-hooklab/audit_native_media_engine.py` + `tests/test_native_media_engine.py` (exact public engine classes).
- `android/native-yandex-hooklab/audit_native_media_implementors.py` + `tests/test_native_media_implementors.py` (DEX hierarchy and inherited method bodies).
- `.github/workflows/android-native-media-engine-gate.yml`, `.github/workflows/android-native-media-implementors-gate.yml`.
- `.github/workflows/android-native-arm-linux-runner-gate.yml` (short ARM Linux capability probe, no APK).
- Pre-documentation code HEAD `fcd7550b86ee93082ff3a8b119e38b29d02482d8`; immutable backup `backup/android-native-real-media-implementation-evidence-20261110`.
- Test.50, main HONOR, Windows, extension, CMS, production server/API/DB all unchanged.

