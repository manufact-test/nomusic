
# W154 — Consolidated regression and owner acceptance preparation

Date: 15 November 2026  
Repository: manufact-test/nomusic  
Product: the one existing CELIKOM Windows application  
Working branch: main only  
Scope: W150 Task 4 only. No updater, installer or package changes.

## Baseline and CI

- Final application-source HEAD: c697a30c87c945f308cac0595e42b247ecc43a54.
- Exact pre-Task-4 backup: backup/windows-main-pre-task4-consolidated-regression-20261115 @ c697a30c87c945f308cac0595e42b247ecc43a54.
- Main CI run 43710085631: SUCCESS.
- Windows integration CI run 43710085801: SUCCESS.
- W15 native contract: W15_NATIVE_CONTRACT_PASS 390.
- W23/W22/W60 original-source/VPN/403/audio regressions, W21 recovery, W24 catalog/ASAR builder, GUI warnings-as-errors compile, W110 supervisor/rollback, W114, W117, W128 and W108: SUCCESS.

## Consolidated review

1. W151 current-player/UI: exact current player and queue identity, accepted heartbeat lease, PLAYING/PAUSED/STOPPED precedence, and conservative ORIGINAL / ACTIVE_REPLACEMENT / UNKNOWN source truth. Stale source proof is not inherited across Next/My Wave.
2. W152 VPN A→B: transient entitlement suspension no longer forces a mapped current track to original and then back to CELIKOM. An exact still-playing signed decoder is held; if lost, only one current-track refresh is issued. Faster entitlement/reconnect cadence is preserved. Audible acceptance remains pending.
3. W153 autostart/tray: actual HKCU Run and Windows StartupApproved state are reconciled; explicit OS OFF is preserved; first-launch default ON, sticky OFF, explicit tray ON/OFF and same-user quiet startup are tested. Background resume never starts Yandex.
4. W75 diagnostics: transient transport failure can preserve the previously verified owner's UI control, but every export/copy requires a fresh online authorization. Logout, identity change and genuine server denial revoke it.
5. W128 launch policy: no CELIKOM runas request or administrator manifest; installer remains per-user.
6. Official Yandex compatibility catalog: 15-minute normal cache remains unchanged; a detected version change forces immediate refresh.

No additional Task 4 code change was necessary. The consolidated CI run already exercised the relevant suites on the final application source.

## Grouped owner acceptance — after Task 6 only

Do not ask the owner to test intermediate builds. The only owner package is the single final EXE+ZIP after Task 5.

1. **In-place upgrade and preservation:** install over 0.24.37 using the same AppId. Confirm account/session, DPAPI data, settings, autostart choice, original Yandex backup and native integration remain intact.
2. **Current-player/UI truth:** start Yandex playback while CELIKOM is closed, then open/reopen CELIKOM. Confirm exact current song and PLAYING/PAUSED/STOPPED state. Exercise Next and My Wave; no previous track's source proof may leak. ACTIVE_REPLACEMENT requires exact current signed-decoder evidence and PLAYING. ORIGINAL requires the dedicated original-source witness; otherwise UNKNOWN is correct.
3. **VPN A→B audio:** test an active replacement, an original track and My Wave separately. Confirm reconnect remains as fast as the current baseline, no redundant source handoff occurs, and listen for the reported pop/click. After recovery test Next and Yandex crossfade. Capture diagnostics for any remaining artifact; do not reopen excluded Issues without explicit owner scope.
4. **Autostart/tray:** compare Windows Startup Apps with the CELIKOM tray menu. Verify OS OFF stays OFF across restart/update; explicit tray ON clears the OS disabled marker. On sign-in CELIKOM appears quietly in the tray only; Yandex remains unopened. Confirm no UAC/elevation. Test minimize-to-tray, tray double-click restore, X and explicit Exit.
5. **Stop/entitlement safety:** after explicit Stop, reboot and confirm no automatic playback resume. Any background reconnection requires the same account/installation and a fresh positive server entitlement; it must never launch Yandex or start a new trial.
6. **Diagnostics after disconnect:** a transient outage may preserve the previously verified owner's control, but export/copy cannot proceed on stale permission. Reconnection requires a fresh server check; logout, account/device change or genuine server denial revokes the control.
7. **Updater integrity:** only after DNS/TLS and signed feed are live, verify the bootstrap's public P-256 pin and future origin, then subsequent automatic update and one-shot rollback. Do not claim production update delivery before the feed is live.

## Status and next order

- Tasks 1–4 are code/test/CI-ready. Tasks 1–3 are **not** owner-PC field-accepted; #52 remains OPEN.
- No EXE, ZIP, installer or release artifact was built. Owner remains on 0.24.37.
- Next: W150 Task 5 only — refactor the obsolete W148 PFX/Authenticode scaffold to the approved P-256 signed manifest + SHA-256 updater/feed. No commercial certificate, PFX, security bypass or early DNS/TLS activation. Task 6 is exactly one final EXE+ZIP after Task 5.
