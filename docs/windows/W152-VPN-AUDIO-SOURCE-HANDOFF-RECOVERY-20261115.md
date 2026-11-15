# W152 — VPN A→B source-handoff protection

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Working branch: `main` only  
Scope: W150 Task 2 only. No autostart, final updater, packaging or installer work was started.

## Baseline and rollback

- Pre-Task-2 code backup: `backup/windows-main-pre-task2-vpn-audio-20261115` @ `43d0b551d210e08d1d5d05a32eaf6634a400c19e`.
- Final Task-2 code HEAD: `59894be3fe88de0dfecd9d92c9164b509d0c7859`.
- Pre-Task-3 backup: `backup/windows-main-pre-task3-autostart-20261115` @ `59894be3fe88de0dfecd9d92c9164b509d0c7859`.

## Root mechanism addressed

A transient entitlement failure during a VPN route change could be interpreted by the renderer as an ordinary Stop. If the current track was mapped, the renderer requested a source reload to Yandex original. After the server check succeeded and CELIKOM re-enabled, it primed the same track and requested another source reload back to the CELIKOM replacement. Two source handoffs in quick succession were an avoidable source of audible discontinuity.

This code-level mechanism is now guarded. It is not a claim that all audible pops from the OS/network path are eliminated; owner-PC listening acceptance remains pending.

## Implementation

1. MainWindow marks a route transition in the authenticated local bridge state. The marker is cleared on a successful check when the bridge never suspended, or after the first accepted heartbeat from a re-enabled native host. A newer route signal resets the prior re-enable handshake.
2. Native Host preserves the decoder-player witness only during a same-origin, signed-in transient route recovery. It advertises `preserveCurrentSource` only when the exact current track still has a signed CELIKOM decoder URL, is PLAYING, and has no observed decoder pipeline error. The current track ID accompanies the witness.
3. Renderer holds the currently loaded signed source during transient entitlement revalidation. It does not force a mapped current song back to original solely because the bridge is temporarily disabled.
4. Transient source recovery and deferred current-track recovery pause while the route is unsettled. Deferred candidates are retained. Retry attempt cadence is preserved across pause/resume.
5. After route validation, an exact surviving decoder is kept without a reload. If it is no longer current/playing/verified, the renderer performs one fresh current-track refresh. A new My Wave/Next track cannot inherit the previous song's decoder witness.
6. Manual Stop, logout, authoritative denial, and API-origin change continue to clear/cancel route recovery and preserve the existing fail-closed behavior. The fast entitlement recheck cadence was not slowed.

## Regression and CI

- W23/W22/W60 original-source, VPN, 403 and audio regression suite: **SUCCESS**.
- W152 renderer tests cover original track during route transition, active replacement preservation, one-refresh fallback, My Wave identity, paused source recovery and deferred candidates.
- W152 Native Host test verifies that only an exact current signed decoder witness can be preserved and that the marker clears after route settlement.
- W15 entitlement/login/native-state suite: **SUCCESS**, including repeated VPN route signals and heartbeat release of only the latest route hold.
- GUI compile with warnings as errors: **SUCCESS**.
- Independent update supervisor build with warnings as errors: **SUCCESS**.
- Existing W110/W114/W117/W128 checks: **SUCCESS**.
- Windows integration CI run `43708423469`: **SUCCESS**.
- Main CI run `43708423447`: **SUCCESS**.

## Not claimed / next order

- No owner-PC audio test has been performed. Crossfade is Yandex-native and still needs manual confirmation after VPN recovery.
- Final grouped acceptance must separately test original tracks, ACTIVE_REPLACEMENT tracks and My Wave; confirm fast reconnect remains fast; then test crossfade after recovery.
- No EXE, ZIP or intermediate installer was built.
- Next: W150 Task 3 only — verify first-launch autostart ON by default, sticky user OFF, and no automatic Yandex launch/elevation. Existing W150 says these behaviors already appear present; audit before changing code.


## W158 owner-PC retest — 16.11.2026 (field regression)

The 0.24.39.0 / native 0.24.30 owner diagnostic now shows that the no-kUrl continuity path is not fully accepted on the owner's Yandex build. For track 144530503, NATIVE_ROUTE_RECOVERY_SOURCE_HELD is followed after entitlement recovery by NATIVE_CURRENT_SOURCE_REVALIDATE and NATIVE_REPLACEMENT_SOURCE_RELOAD for that same track. A second route-change signal occurred during the hold. Four other held/kept cycles did reach SOURCE_KEPT, so this is a narrow recovery-guard/state-ordering gap, not evidence that every VPN transition reloads the source.

Reopen only this specific no-kUrl path. Determine which host/renderer guard prevented SOURCE_KEPT, add privacy-safe fixed reason codes if needed, and preserve the same already-mapped current source when the same track remains PLAYING/PAUSED on the same origin. Keep actual source/player-loss, Next, Stop, logout, denial, origin-change and timeout fail-closed behavior. Do not infer audible continuity from these logs; owner listening acceptance is still required.

See docs/windows/W158-OWNER-FIELD-REGRESSION-VPN-AUTORUN-UI-20261116.md for the exact event sequence and ordered work.
