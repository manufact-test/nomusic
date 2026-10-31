# CELIKOM Android 0.3.70 / versionCode 71 — signed release and HONOR QA

**31.10.2026. Signed/online: YES. Acoustic acceptance: PENDING. Android only.**

## Source and provenance

- Production: `feature/android-unified-preparation-seek-gate`, signed source commit `06c2d9d01730007e453e15b5b20b067972bf1bf6`.
- Nonpublishing staging: `feature/android-0370-honor-join-pause-updater-staging`, same tested source. Branch created directly from signed 0.3.69 baseline.
- Original owner-approved benchmark, unchanged: `backup/android-0369-honor-listening-control-20261031` -> `a30f949b10a72f62977e70cba30767b7c382a249`.
- Initial code CI [41226550426](https://github.com/manufact-test/nomusic/actions/runs/41226550426): SUCCESS, publish skipped. First version-bump check [41226668488](https://github.com/manufact-test/nomusic/actions/runs/41226668488) caught a mistaken negative case expecting code71 to be rejected; corrected without playback changes. Final versioned staging [41226755602](https://github.com/manufact-test/nomusic/actions/runs/41226755602): SUCCESS, publish skipped.
- Production Android SDK36/D8, full regression suite, private old-certificate signed build, APK verification and stable publication [41226869075](https://github.com/manufact-test/nomusic/actions/runs/41226869075): **SUCCESS**.

## Signed APK receipt

| Property | Confirmed |
| --- | --- |
| Release | `0.3.70`, `versionCode=71` |
| SHA256 | `799bab36eba2eccecd7e1602ee33735b9914fc53401b1eb6b8e5eef1c8d12850` |
| Byte length | `8742985` |
| Certificate | Original pinned SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f` |
| Signature | Android v2/v3 verified |
| Contents | Exact CI-compiled add-on DEX, no extra DEX/source/signing files; original catalogue assets unchanged |
| Package / API | `pro.celikom.nativeprobe`, installation metadata checked by `verify_release.py` |
| Stable manifest | Live `0.3.70/code71`; publisher verified live manifest equals release candidate |
| Updater entry | `https://lemonchiffon-narwhal-791953.hostingersite.com/download/android/` |

The workflow checked the remote uploaded file's size and SHA and atomic stable.json promotion. No physical phone installation or on-device speaker/Bluetooth capture was performed by CI. Do not call this an accepted acoustic fix.

## Actual changes

1. **HONOR 35.7s detached pause:** previously an `effect==null` bypass permitted `resume_aligned.driftMs=132,seekSkipped=true`, then blended two potentially offset sessions. `ReplacementEngine` now uses existing 85ms pause alignment tolerance when the original DSP was released after a genuine >=30s pause and the retained decoder differs; makes **one silent seek** with original audible before reattachment, not an audible correction. Normal short pauses with retained effect keep the previous <=350ms shortcut.
2. **After successful system package update:** `UpdateInstallReceiver` checks matching installed `versionCode` after `PackageInstaller.STATUS_SUCCESS`; then uses Android's own `ActivityManager.AppTask.finishAndRemoveTask()` to remove the old CELIKOM task from Recents. Cancel/error/pending user action cannot clear the task. No self-relaunch/background activity launch added. Android OEM behavior still needs HONOR verification.
3. **Intermittent cold dip/micro-repeat:** cold same-song `complementary_linear` join 160ms and finger-seek `exclusive_single_turn` **unchanged**. New passive `replacement_join_clock_summary` has initial/end/min/max coarse transport drift while the join runs; it explicitly flags no PCM phase or hardware amplitude measurements. Drift alone cannot demonstrate or repair cancellation. **This symptom remains open.**

## HONOR owner checklist (ONE run, not A/B)

- Install 0.3.70 via in-app updater. Check that system confirmation succeeds, old CELIKOM task is removed from Recents; manually open CELIKOM again and verify account/settings still present. Separately, if practical, test cancellation on a later update (do not force a second build only for this).
- Hear 2–3 natural next-track joins and one manual Yandex Next; note any brief dip, repeated syllable/note, sound gap. Do a few finger seeks after Next.
- Within one playing song, first a normal short pause and resume, then a >35 second pause and resume; listen for repeated segment and for new seek-related lag.
- Stop and resume if convenient; optionally Bluetooth/route loss and cellular/VPN Range seek. No false claim of physical BT/Stop coverage from CI.
- If any anomaly is audible, privately send **one combined diagnostic** and a note of which exact moment sounded wrong. Analyze **only the final `run_start(version=0.3.70)`** in the file. Do not publish owner TXT, song names, album IDs or other private media metadata.

## Next engineering gate

Use real 0.3.70 per-join clock summaries, compare good vs bad starts and check decoder ready, DSP gain command order and position variance. If coarse drift is stable but sound varies, this strengthens (does not prove) the unmeasured waveform/phase hypothesis. Any new cure needs a reproducible failure mechanism and targeted red test before changing audible output. Never retune arbitrary fade durations or reintroduce a lab A/B selector. Preserve signed 0.3.69 backup and all Next, seek, pause, Stop, buffering, prefetch/Range and route ownership protections.

**Desktop, website, backend, catalogue, authentication, stable distribution logic and release keys were not changed.**
