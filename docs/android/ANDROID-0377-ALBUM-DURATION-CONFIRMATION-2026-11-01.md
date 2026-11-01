# CELIKOM Android — 0.3.77 candidate: conservative album-duration confirmation

Date: 2026-11-01
Status: signed test candidate; not yet acoustically accepted on HONOR. Stable publication intentionally skipped.

## Baseline and recovery

- Production baseline: Android 0.3.76, versionCode 77, source commit 712e7226052419647b46a16086921e4b82732051.
- Candidate: Android 0.3.77, versionCode 78.
- Immutable recovery branch: backup/android-0376-before-strict-seek-clock-20261101.
- Staging branch: feature/android-077-album-duration-confirmation-staging-20261101.
- The signed production APK, stable manifest, signing identity and updater are unchanged.

## Evidence from the owner's 0.3.76 journal

- Eight tracks were accepted through the automatic album-candidate path.
- Three measured replacement files differed from the Yandex source duration by approximately 582ms, 663ms and 1354ms.
- The identity decision explicitly reported automaticSourceIdVerified=false; album/title/artist uniqueness is not proof that the exact same edit/master was selected.
- Nevertheless, verifiedDurationIdentity() treated every ALBUM candidate as verified and allowed the extended 1500ms tail tolerance automatically. This was inconsistent with the identity evidence.

Track names, IDs and the private diagnostic are intentionally not stored in this document or Git.

## Narrow change

- Measured difference up to 500ms: existing automatic playback behavior is unchanged.
- Difference over 500ms and up to 1500ms for an unconfirmed automatic album candidate: CELIKOM keeps the original Yandex audio, skips that replacement and exposes the existing «Подтвердить» control. No new button or permission is added.
- After the owner confirms that the candidate is the correct edition, CELIKOM performs a fresh live resolve and may use the existing bounded 1500ms allowance.
- Difference over 1500ms, invalid metadata, wrong session or other failed checks remain fail-open to the original.
- No seek timing, gain law, crossfade, decoder ownership, Media3 arbitration, HTTP Range, desktop, website, backend or updater logic was changed.

## Verification

Local verification passed:
- tests/run_engine.py, including the actual engine, 582ms / 663ms / 1354ms / 1469ms long-tail cases, confirmation retry, and all historical audio regressions;
- tests/run_addon_host.py with Android SDK 36;
- tests/check_release_contract.py;
- Android SDK 36 / JDK 17 source compilation and D8;
- signed APK structure, version, alignment, DEX and signing certificate verification.

GitHub Actions run 41304895181: SUCCESS; publish-stable: SKIPPED.

Signed test APK: CELIKOM-0.3.77-HONOR-test.apk  
Size: 8,755,273 bytes  
SHA-256: 6ebc28f459951d663d8ed8e6f72584c4726bdac735b45a6edb29f08ab12a688a  
Signing certificate SHA-256: 67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f

The APK is a direct test artifact only. No stable manifest, public update channel, website or backend was changed.

## HONOR acceptance requested

1. Play normally through the songs that previously sounded inconsistent.
2. If the new «Подтвердить» prompt appears, listen to the original and confirm only if the offered replacement is genuinely the same version/edit.
3. After confirmation, verify that the replacement starts and that seeking remains as before.
4. Check that tracks with no prompt continue replacing normally.

A green host/SDK build is not acoustic acceptance. The owner's listening result decides whether this candidate is kept.
