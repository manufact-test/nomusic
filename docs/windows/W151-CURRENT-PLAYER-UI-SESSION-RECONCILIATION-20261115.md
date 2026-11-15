# W151 — Task 1 current-player/UI reconciliation

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Working branch: `main` only  
Scope: W150 Task 1 only. No VPN, autostart, updater or installer work was started.

## Baseline and rollback

- Owner-supplied exact pre-W150 backup: `backup/windows-main-pre-w150-owner-scope-handoff-20261115` @ `0524158177beeedb50bff85d59ae573d90c19823`.
- Live code HEAD before W151: `b57f57c1094446a0fccf68d108800be792e19f94`.
- W151 implementation: `2f1c695045a1d3daef4ef4cb5e60fc74cd1688d0`.
- Final W151 code/test HEAD: `dbd96fe99e498241125deb870215276215ae425a`.

## Implemented

1. **Heartbeat-driven UI synchronization.** Accepted bridge heartbeats refresh the main and compact surfaces on the UI thread. A dedicated 1-second timer only detects expiration of the existing 12-second heartbeat lease; it does not poll Yandex or the native player.
2. **Fresh-session reconciliation.** The native host tracks the generation of the published companion capability file using file metadata, not the secret token value. A new generation clears old per-view track/source state and forces a fresh current-player sample and heartbeat, even when the token bytes are unchanged. Missing-token state also clears prior-session caches.
3. **Immediate re-enable reconciliation.** An effective OFF→ON transition (including signed-in state) bypasses the ordinary 2.2-second sample and 4.8-second heartbeat gates. The currently audible renderer is sampled before the UI remains in a startup state.
4. **Queue identity and My Wave/Next.** The same audible renderer publishes a new current track identity and does not transfer the previous track's source witness to the new queue item.
5. **Playback-state and prompt truth.** Compact placeholders distinguish PLAYING, PAUSED and STOPPED when metadata is absent. Reconnecting CELIKOM no longer tells the owner to start a Yandex track or claims Yandex itself is still launching.
6. **Strict source tri-state.** ACTIVE_REPLACEMENT requires the current signed decoder witness and PLAYING. ORIGINAL requires the explicit native `NATIVE_ORIGINAL_SOURCE_VERIFIED` status plus source ORIGINAL. A bare renderer ORIGINAL hint, mapping state, old heartbeat or audibility signal remains UNKNOWN. The native host currently does not emit the dedicated ORIGINAL witness, so ambiguous originals remain conservatively UNKNOWN.

## Regression coverage

- W23 native-host suite: **134/134 passed**, including W151 same-renderer queue change, capability-file republish and OFF→ON immediate heartbeat tests.
- W15 companion suite: **375/375 passed**, including original-source proof gating, source-failure messaging, compact startup/playback states and accepted-heartbeat UI refresh.
- GUI compile with warnings as errors: SUCCESS.
- Independent update supervisor compile with warnings as errors: SUCCESS.
- W128 non-elevation launch-path tests: SUCCESS.
- Main CI run `43706073512`: SUCCESS.
- Windows integration CI run `43706073517`: SUCCESS.

## Not claimed / next order

- No owner-PC audio or UI acceptance has been performed. CI does not prove audible replacement, accurate on-device current-song display or VPN behavior.
- No EXE, ZIP or intermediate installer was built.
- W141–W147 protections remain intact. This work does not change W142 retired-host semantics, W143 signed-feed handling, W144 audibility selection, W145 update safe-point policy, W146 paused/stopped precedence or W147 native-audibility precedence.
- Next: W150 Task 2 only — resolve the reported VPN A→B pop/click without regressing the faster reconnect; separately cover original tracks, alternatives and My Wave, then crossfade after reconnection. Continue with Tasks 3–6 strictly in W150 order.
