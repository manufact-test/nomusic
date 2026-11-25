# Extension0.4.84 — buffer admission and audible fallback

## Confirmed owner failure

Installed0.4.83 diagnostic `Вставленный текст(20261125-190417).txt`: native43.73s, guard active; replacement seeking39s,readyState1,playPending=true,buffered[0,2.533877]. First64KiB appended; next512KiB response body reading. Request success/metadata availability was mistaken for audible readiness.0.4.83 removed whole-file restart but retained a guard over a decoder that could not play the requested position. This is a client defect. A200 API or206 header does not prove a playable audio body. The exact server throughput is not measurable from this bounded export.

## Correction

- Ordinary MSE admission checks actual audio.buffered at the fresh native position and decoder readiness. No unbuffered replacement seek is issued while original remains muted.
- An active replacement that lacks target bytes or remains seeking/unready yields its guard to the original. The same decoder, verified buffer and fetch continue; a renewed token fences the old GUARD_RELEASED. Re-admission waits for bytes/readiness and uses the current native clock. Stop, manual Original, access revocation and track/resource changes still dispose it and fence late work. This is not the withdrawn0.4.71 unbuffered prepareJoin implementation.
- MSE continuation remains64KiB while buffer ahead is below15s,128KiB below30s, then512KiB. The old64KiB-first/512KiB-next combination could exhaust a2.5second intro while waiting for the next whole response. All existing range/deadline/format/auth validation and bounded retries remain.
- Buffer backpressure follows the desired master position while waiting, so a seek beyond120s cannot leave the downloader sleeping forever at120s relative to an intentionally paused replacement.
- Complete native M4A/WAV and newly-approved MP3 routes, grant deadlines, backend, Android, Windows and central publisher implementation are unchanged.

## Verification and limits

Local397/397 tests PASS, including the exact2.533877s-buffer→39s-seek, late65s admission, buffered seek, stalled decoder, retained download recovery, Stop/Original/track cancellation, buffer-based Range sizing and packaged MAIN+ISOLATED physical original-unmute/reacquisition. Three new regression cases fail against the archived0.4.83 controller/player. Test media/transport are simulated; these results do not establish live audible Chromium quality. Local Chromium launcher exists but its binary target is absent, so no native browser pass is claimed.

0.4.82 and0.4.83 owner approvals are withdrawn. Do not restore them; retain historical immutable packages.0.4.84 needs exact successful Floki build/receipt before owner-channel approval. User acceptance remains open: ordinary Next and seek, then VPN reconnect/Next. When replacement bytes are genuinely unavailable, the intended fallback is audible original while download catches up, not a promise of instant alternative playback under every network condition.
