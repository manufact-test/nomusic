# CELIKOM Android — current status at 0.3.78 stable baseline

Date: 2026-11-01  
Status: **0.3.79 experimental APK built, signed and verified; owner listening test pending**

## Stable and rollback points

- Stable owner baseline: **0.3.78 / versionCode 79**.
- Immutable recovery branch: \`backup/android-0378-original-before-cached-join-20261101\`.
- Immutable recovery SHA: \`bf011dcf1a70c504883a8e5e742e0b038f41d9b0\`.
- Verified APK source commit: \`e04d5a7d5eafac2e03c61c885bbe86238e4638d9\`.
- Package: \`pro.celikom.nativeprobe\`.
- Signing certificate SHA-256: \`67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f\`.

The backup branch remains at the exact original SHA. Do not move, force-update or commit to it.

## Staging branch and final code behavior

- Branch: \`feature/android-0379-cached-decoder-join-staging-20261101\`.
- Candidate: **0.3.79 / versionCode 80**.
- The cache stores a validated audio file, not a prepared decoder. A cache hit creates a fresh MediaPlayer.
- New/coherent local-file attachments now use the existing streaming decoder-motion and transport-clock gate.
- Streaming keeps its existing gate.
- Retained local Pause/Resume and route-resume reattachment keep their previous path.
- Unstable local decoder startup fails open to the original.
- No changes to AudioOwnership, seek/WARM constants, transition duration, gain law, Pause/Resume, Next, Bluetooth, UI, or permissions.

## CI acceptance

GitHub Actions: [run 41324403134](https://github.com/manufact-test/nomusic/actions/runs/41324403134)

| Check | Result |
|---|---|
| Full native host regression suite | PASS |
| Cached decoder join regression | PASS — 13 checks |
| Existing audio / Media3 / lifecycle suites | PASS |
| Android API 36 source compilation | PASS |
| D8 compilation | PASS |
| Source-to-DEX provenance | PASS |
| Signed APK rebuild and release verification | PASS |
| Same signing certificate / APK v2-v3 signature | PASS |
| Test-only staging artifact upload | PASS |
| Hostinger stable publication | SKIPPED |
| Stable manifest update | NOT PERFORMED |

The native host run reported 6,730 checks across 34 test groups.

## Experimental APK

- GitHub artifact: \`celikom-android-0.3.79-cached-decoder-join-signed-test\`
- Artifact ID: \`13090493627\`
- File: \`CELIKOM-Android-0.3.79-SIGNED.apk\`
- Size: 8,755,273 bytes (about 8.4 MiB)
- Version code: \`80\`
- Package: \`pro.celikom.nativeprobe\`
- APK SHA-256: \`77d262ce9cbee85d5ec529e7c40bc9842209559eddda986003f73352cef9e66f\`
- Signing certificate SHA-256: \`67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f\`
- Receipt: \`stable_published: false\`

The APK can be installed over 0.3.78 without uninstalling because package and signing identity match and versionCode is higher. It is a direct test download and will not appear in the in-app updater; no stable release was published.

## Next owner test

1. Install the experimental APK over 0.3.78.
2. Test the cache-hit path on **“Биг сити лайф”**: allow the replacement to load once, switch to another song, then return to the same track.
3. Listen for a volume dip, silence, click, late join or unstable transition.
4. Compare with a first-load streaming replacement and send the resulting diagnostics.

Do not adjust timing or gain parameters before the device test. A green CI run is not acoustic acceptance.

## Scope boundary

Android only. No Desktop, Backend, website, CMS, catalogue or Hostinger stable release changes.
