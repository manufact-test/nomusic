# CELIKOM Android 0.3.77 — signed stable OTA release receipt

Date: 2026-11-01

**Status: published and verified on the existing stable Android channel.** Physical HONOR listening acceptance remains pending.

## Release identity

- Version: **0.3.77**
- versionCode: **78**
- Package: `pro.celikom.nativeprobe`
- APK size: **8,755,273 bytes**
- APK SHA-256: `70f4cbfd714baca098fa2dfe4aae812fa450e5aaabaa039368b395665c1d5f3d`
- Original signing certificate SHA-256: `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`

## Published endpoints

- Stable manifest: https://lemonchiffon-narwhal-791953.hostingersite.com/updates/android/stable.json
- Immutable signed APK: https://lemonchiffon-narwhal-791953.hostingersite.com/releases/android/78-70f4cbfd714baca098fa2dfe4aae812fa450e5aaabaa039368b395665c1d5f3d.apk
- The permanent user-facing download resolver remains the existing single URL: `/download/android`. Do not hand out the versioned immutable URL as a second user-facing download link.

## Build and publication evidence

- Repository: https://github.com/manufact-test/nomusic
- Production source branch: `feature/android-unified-preparation-seek-gate`
- Merge commit: `94afa76ff1739557e050f9020ef6b2a889e9e109`
- PR: [#25 — Android 0.3.77 stable promotion](https://github.com/manufact-test/nomusic/pull/25)
- Full production Android CI and signed Hostinger publisher: [run 41306428227](https://github.com/manufact-test/nomusic/actions/runs/41306428227) — SUCCESS.
- Staging Android SDK36/JDK17/D8 and native regression validation: [run 41304895181](https://github.com/manufact-test/nomusic/actions/runs/41304895181) — SUCCESS; staging publisher correctly skipped.
- The production publisher rebuilt the APK from the validated DEX and pinned original baseline, verified the original signing identity, APK v2/v3 signature, alignment, package/version/API, approved manifest boundary, unchanged catalogue assets and exact compiled addon DEX.
- The publisher uploaded the immutable APK, verified its SHA-256 and byte size on Hostinger, atomically switched the stable manifest, then fetched the live manifest and confirmed **0.3.77 / versionCode 78**.
- Independent read-only Hostinger preflight: run [41306898411](https://github.com/manufact-test/nomusic/actions/runs/41306898411) confirmed SSH access, private PHP resolver output and public manifest HTTP 200 for 0.3.77.
- Public APK delivery preflight: run [41307089948](https://github.com/manufact-test/nomusic/actions/runs/41307089948) confirmed **HEAD 200**, **GET 200**, exact size **8,755,273 bytes**, and exact SHA-256 match.

Two initial publisher attempts encountered a transient 504/empty response from the public manifest endpoint. No APK or manifest was promoted during those failed attempts. After the endpoint recovered, read-only checks passed and the final publisher completed successfully.

## What changed in 0.3.77

This release contains the narrow conservative album-duration identity confirmation change described in [ANDROID-0377-ALBUM-DURATION-CONFIRMATION-2026-11-01.md](ANDROID-0377-ALBUM-DURATION-CONFIRMATION-2026-11-01.md):

- Duration difference up to 500ms: existing automatic replacement behavior is unchanged.
- Difference over 500ms and up to 1500ms for an unconfirmed automatic album candidate: retain original Yandex audio and show the existing «Подтвердить» control.
- After explicit confirmation of the correct edition, perform a fresh live resolve before allowing the bounded 1500ms tolerance.
- Difference over 1500ms and other invalid/ambiguous cases remain fail-open to the original.

No new UI button or permission was added. Seek timing, crossfade, gain law, decoder ownership, Media3 arbitration, HTTP Range, updater logic, website code and backend were not changed by the audio candidate.

## Owner's device test — still required

1. Open the already installed CELIKOM app.
2. Press **«Проверить обновление»**.
3. The stable manifest now advertises **0.3.77**. The app should offer the update.
4. Use the normal in-app download action and confirm installation in Android. Do not uninstall CELIKOM or clear app data.
5. Reopen CELIKOM manually if Android closes it after installation; verify version **0.3.77**.
6. Test the tracks that previously showed duration mismatch. If «Подтвердить» appears, confirm only when the replacement is genuinely the same edition/edit.

CI and public HTTP checks prove signed delivery, not acoustic quality. Do not describe audio as accepted until the owner has listened on the HONOR device.
