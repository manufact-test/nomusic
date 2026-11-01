# CELIKOM Android — 0.3.77 candidate: conservative album-duration confirmation

Date: 2026-11-01
Status: non-publishing staging candidate; not yet accepted on HONOR.

## Baseline and recovery

- Production baseline: Android 0.3.76, source commit 712e7226052419647b46a16086921e4b82732051.
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

Local tests/run_engine.py passes, including actual-engine preparation, pause/resume, seek, Next, Stop and ownership regressions; long-run and phone timeline replays; 0.3.74 strict join and 0.3.75 WARM latency gates; explicit confirmation and fail-open tests for the 1354ms and 1469ms measured-tail cases; release-contract, source-ownership and Android add-on host checks.

The local environment does not contain Android SDK 36, so the full SDK36/D8 workflow remains mandatory. The staging workflow must finish with publish-stable skipped. No signed APK has been published by this staging change.

## HONOR acceptance requested

1. Play normally through the songs that previously sounded inconsistent.
2. If the new «Подтвердить» prompt appears, listen to the original and confirm only if the offered replacement is genuinely the same version/edit.
3. After confirmation, verify that the replacement starts and that seeking remains as before.
4. Check that tracks with no prompt continue replacing normally.

A green host/SDK build is not acoustic acceptance. The owner's listening result decides whether this candidate is kept.
