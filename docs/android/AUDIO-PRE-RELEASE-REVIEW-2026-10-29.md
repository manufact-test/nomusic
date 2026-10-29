# CELIKOM Android — static pre-release review · 29 October 2026

This review is an **architecture and CI checkpoint**, not an approval of actual acoustic playback. The last code commit reviewed is `ce52b178c9101835619ceb8ee4a66b8784477f45` on `feature/android-0348-audio-ownership-stabilization`. Complete workflow PASS: https://github.com/manufact-test/nomusic/actions/runs/40931276362. PR #22 remains OPEN/DRAFT, Issue #20 remains OPEN.

## Verified in code and CI

- `AudioOwnership` gates decoder start, seek, emergency silence, effect control, positive gain, and ordered native gain restoration; same-song **decoder retirement** now invalidates stale callbacks without invalidating a retained decoder on a long pause.
- Repeated stable polling does not keep rewriting identical native attenuation or positive secondary gain. All zero-volume emergency silencing still reaches `MediaPlayer`.
- `SourceEventArbiter` checks live event identity for seek, not merely clock position; stale cross-song transitions and coincidental timestamps cannot initiate a new decoder alignment.
- Clock, duration, drift, repeat/early completion, stop/rearm, streaming, buffering, user seek, long pause, and source route regression cases remain in blocking host tests; Android API36 + D8 compile, pinned JAR SHA-256 matching and 16 addon tests pass.
- `compare_commits(b9c3e383…ce52b178)`: 21 changed files, entirely under `android/native-companion/` and `docs/android/`. Desktop, backend, site and CMS are untouched.

## Release blockers (do not skip)

1. **No new APK exists.** The installed rejected 0.3.51 is versionCode 52. Packaging files `build_release.py`, `verify_release.py`, and `addon/src/.../AppVersion.java` currently still identify 0.3.51. A next candidate requires coordinated update (for example 0.3.52 and versionCode 53) *before any signing or APK delivery*.
2. Reproduce the package using the SHA-pinned baseline APK 0.3.22, all 5 SHA-pinned JARs, Android API36, Build Tools 36 and Apktool 2.11.1. Signing files must remain outside Git and the built APK must retain the **same signing certificate** as the installed baseline. Run `build_release.py` and `verify_release.py`, verify actual signed DEX, source fingerprints, assets, manifest and APK version. No keys, original journals or raw listening histories in Git or released packages.
3. Before proposing a real-device install, review any remaining lifecycle exceptions and callback orders once more against the exact signed DEX. Do not infer physical zero-overlap from a successful host fake or command trace.
4. On HONOR with Yandex Music and Bluetooth, verify actual audible handovers: next track while predecessor ends, short/long pause, seek, route loss/reconnect, background playback and sustained >700ms drift. A failure must restore the original, not leave two sessions audible. Only actual listening can close this gate.

**Preserved point:** `backup/android-audio-callback-fencing-green-20261029` → `ce52b178c9101835619ceb8ee4a66b8784477f45`; older backup branches remain intact. The original 0.3.51 combined device report remains private.
