# 0.4.48: native transition leak and M4A preparation

Owner accepted .47 startup/retry and MP3/M4A upload/admin. Still reports M4A icon disconnect on every switch and a foreign intro when switching to 1944611. Three owner diagnostics are .47, bridge healthy, no replacement/network errors; do not misclassify PREPARING as a service outage.

## Evidence

M4A 1944599 (Папиросы), replacement 27: prepare 14:11:10.121–12.812 (2.691 s), then 14:11:59.293–14:12:01.535 (2.242 s). Every native-container prepare fetched the complete file again using sequential 512 KiB signed ranges. PREPARING and normal RESTORING turned the connection icon gray.

MP3 1944611 (Всё пиздато), replacement 10: previous 27323608 is synchronously silenced/disposed before the new native play. The bounded transition trace shows original unguarded from native 100 ms through 402 ms while resolving/loading the new replacement. The old MAIN handoff ended on native source change, too early to protect new playback. This proves an original-audio leakage window, not the identity of the sound the owner heard. Private audio was not changed or exported.

## Changes

- Keep the existing original mute through resource replacement on the same native element, until a new guarded replacement, an explicit negative verdict, manual Stop/Original, loss of master, or the original one-second transition deadline.
- A verified positive resolve can transfer that existing mute to the new operation while decoding. This reserve cannot initiate a new mute on initial/unrelated playback; it requires exact track/media identity, confidence, independent duration, current session/generation. It has a separate ten-second fail-open deadline. Final ready admission remains mandatory. Cancellation, failure and late replies retain token fencing.
- Negative verdict releases only the matching transition, with session/generation and track/media checks. Unresolved metadata still fails open in one second. User intent and native clock remain under Yandex control.
- Native M4A retains the original container. Read first signed 512 KiB, validate MIME, strict Content-Range, total at most 30 MiB, exact body bounds, then fetch with at most four concurrent bounded readers. Verify consistent ETag/total across ranges and ordered byte concatenation.
- Keep only one complete native Blob in content-script memory, never persistent storage. Every reuse MUST make and validate a fresh signed GET first, in addition to existing authenticated/entitled resolve. Reuse requires server strong SHA-256/version ETag, origin/path, replacement ID/version, MIME and size. Revocation/403 cannot reuse bytes. Changed versions redownload. Cancelled or partial work cannot populate cache.
- Healthy authorized PREPARING/RESTORING are connection states, not disconnections. Real unhealthy bridge, suspension, startup/replacement error, unavailable/denied access, disabled setting still gray immediately. Popup retains preparation text.

## Validation and limits

258 extension tests pass locally, including parallel byte identity, authenticated cache hit, revocation, version change, body overflow, cancelled cache population, reserved preparation cancellation, negative release, source rebind silence and icon state. Repository lint, manifest validation and security audit pass. Native Chrome package run 38750893789 PASS, including actual source replacement/preparation/negative verdict, MP3 MSE, native M4A decoding, gain and popup cancellation/retry. Full CI run 38750900764 first attempt failed in unchanged reward-disclosure browser driver with no DOM result (not an audio assertion); same-source attempt 2 PASS (complete repository checks). Native test observes physical mute on emptied/loadstart/loadedmetadata/canplay/play/playing through actual source replacement, then preparation transfer and negative verdict.

This is not owner confirmation that the audible fragment is eliminated. Recheck 27323608 → 1944611, direct clicks and repeated M4A transitions after updating/reloading the Yandex tab. First-ever M4A still requires all original bytes; parallel fetch reduces waterfall and repeat playback reuses verified bytes, but startup is not guaranteed instantaneous.

Extension-only .48. Backend remains deployed .46; no music, mapping, moderation, gain or account writes. Preserve current replacement 27 and all other owner data. PR #6 remains OPEN/unmerged; issue #7 OPEN.
