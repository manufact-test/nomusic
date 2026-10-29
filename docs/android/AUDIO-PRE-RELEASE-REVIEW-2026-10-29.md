## Release audit update: archive strictness, CI provenance and explicit unsigned inspection

Reviewed complete CI `40941509415` PASS on `7e49152d`. The signed `verify_release.py` now calls the same `release_archive.inspect_zip` used by the unsigned structure tool; it rejects additional, missing or changed catalogue assets, duplicate ZIP members, unexpected DEX files, source/signing material and archive traversal. `check_release_archive.py` contains 16 positive/negative cases. `ci_provenance.py` records the SHA-256 of every Java source and the corresponding DEX, together with the CI Git commit; `check_ci_provenance.py` contains 11 cases, and the offline inspector rejects mismatched code/DEX.

A real APK 0.3.52 was rebuilt from the original base and exact CI DEX with the **same official assembly path** in explicit `--unsigned-inspection` mode. The offline kit was downloaded and its four release gates run successfully without Git checkout. The inspection report is `UNSIGNED_INSPECTION_ONLY_NOT_INSTALLABLE`; it does NOT prove signed-release completion or acoustic playback. Original signing key remains unavailable; PR #22 remains draft. Full report: `RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md`.

---

## 29.10.2026 — new 0.3.52 structural package evidence supersedes previous "no package" statement

Code revision `04a583a5` + CI https://github.com/manufact-test/nomusic/actions/runs/40937933292 both passed. A LOCAL **UNSIGNED smoke APK** now exists for structural inspection (do not distribute). Apktool 2.11.1, real baseline 0.3.22, exact pinned JARs and API36 were used. The compiled DEX from the JDK17 GitHub CI artifact was injected exactly byte-for-byte, and `zipalign`, `aapt` versionCode 53/0.3.52, assets catalogue equivalence, absence of source/secret packages, and two DEX entries all passed. This was an inspection-only local variation of the release builder (no key, no signature). The official signed release path was NOT completed. `verify_release.py` correctly rejected the unsigned output.

The old signed 0.3.22 and 0.3.51 share the same pinned signer. The original signing .p12 and config are not present in the recovered build environment and have not been supplied here. No signed installable 0.3.52 exists, no device playback test has been run, and PR #22 remains draft. Review the full, exact checksum record at [RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md](RELEASE-0352-STRUCTURAL-SMOKE-2026-10-29.md).

---

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
