# Android owner acceptance and design checkpoint — 2026-10-21

The owner installed 0.3.23 and reported that playback now works well, authorizing the design stage. The attached report was read from its supplied scratch copy, not through Library.

Report: `CELIKOM-combined-20261021-104019.txt`, 87 events, version 0.3.23. The headphone route pause retained automatic mode and prepared audio. Resume used `replacement_resume_aligned`, drift -1ms, `seekSkipped: true`. No extra download was needed. The file ended through `replacement_completed`; native playback subsequently reported approximately 180954ms against a nominal 180880ms song. This trace does not show a several-second early cutoff. The one recovery event is natural file completion, not a new network/playback failure. This is evidence for the observed run, not every device/track/call case.

Desktop remains the accepted 0.4.61; its branch, backend and website are outside this work. No additional hosting, staging setup or device reinstall is required for the design proposal.

## Design proposal

`android/native-companion/design/interface-preview.html` contains the revised single-screen proposal based on the accepted desktop extension's popup HTML/CSS. It has no network calls, real login, persistent credentials, live playback control or automatic report transmission. It retains the desktop dark background (#0b1013), neutral buttons and mint Start action (#66e0bf).

Owner feedback: keep the desktop interface and settings, simplify the mobile design, and avoid inventing features. Removed the marketing heading, automatic-replacement switch/card, artwork/progress card and bottom navigation. The screen follows the desktop order: Start/Stop, Restore original, Upload version, Suggest song, access/song/version labels, Account, Support and diagnostics. Android connection help is collapsed. The proposal discloses the existing 12-minute test-session limit rather than implying an already implemented unlimited background release.

Upload, suggestions and support are existing desktop actions shown for interface continuity; their native Android integrations are not implemented by this design change. The preview explicitly reports that submissions are not sent. Account shows only the current basic native actions; desktop registration, recovery, promo and referral flows are not silently added. Porting any missing flow needs a separate implementation using the existing contract, not new server behavior. This change modifies no Java, APK, playback, authentication or desktop files.

Next: owner design feedback, then native UI implementation in this same Android directory. Preserve playback/session behavior and signing identity. Do not rebuild or reinstall the app solely to view the proposal. Design does not authorize silently removing the current foreground-run limit or changing shared service contracts. Calls remain deferred.

## Follow-up before production

The report also contains a same-identity restart after natural completion while the 30-second completion backoff is active. This is not a reported owner failure, but same-track repeat should be reviewed before claiming full repeat-mode coverage. Keep it out of the design-only change and batch any necessary functional verification with a later candidate.
