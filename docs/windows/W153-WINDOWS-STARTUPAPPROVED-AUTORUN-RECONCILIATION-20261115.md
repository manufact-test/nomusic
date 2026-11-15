
# W153 — Windows StartupApproved / autostart reconciliation

Date: 15 November 2026  
Repository: manufact-test/nomusic  
Product: the one existing CELIKOM Windows application  
Working branch: main only  
Scope: W150 Task 3 only. No updater, installer, package or playback-path changes.

## Baseline and rollback

- Pre-Task-3 code backup: backup/windows-main-pre-task3-autostart-20261115 @ 59894be3fe88de0dfecd9d92c9164b509d0c7859.
- Final Task-3 code/test HEAD: c697a30c87c945f308cac0595e42b247ecc43a54.
- Exact pre-Task-4 backup: backup/windows-main-pre-task4-consolidated-regression-20261115 @ c697a30c87c945f308cac0595e42b247ecc43a54.

## Defect found

CELIKOM previously checked only the HKCU Run command. Windows separately records the Startup Apps / Task Manager approval state in HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\StartupApproved\\Run. Windows can leave the Run command present while marking the app disabled. The old CELIKOM state check could therefore report ON and permit automatic reconnect while Windows startup was OFF.

## Implementation

1. Effective autostart state now requires the exact expected same-user HKCU Run command and an enabled Windows StartupApproved marker.
2. Missing approval marker retains Windows' default-enabled behavior. The binary state parser recognizes enabled even-byte states including 0x02, 0x04, 0x06, 0x08; disabled odd-byte states and malformed/truncated/non-binary values fail closed.
3. MayResume relies on the effective state, so Windows-level OFF blocks automatic playback recovery.
4. Explicit tray ON writes the Run command and clears a previous OS-level disabled marker. Explicit tray OFF deletes only CELIKOM's own Run value and saves the sticky AutoRunConfigured choice.
5. On first enrollment, if an older installation already has a Run entry that Windows explicitly disabled, CELIKOM adopts that OFF as a sticky choice instead of re-enabling it.
6. No changes to audio/native renderer/host, VPN reconnect, updater, installer or package version.

## Startup, tray and safety audit

- First launch remains ON by default.
- A deliberate app-level OFF remains sticky across later launches and in-place upgrades.
- A Windows Startup Apps OFF marker is reflected in the effective tray state and blocks background resume.
- Quiet --background startup creates no visible main window/taskbar entry and hides to tray.
- Minimize hides to tray; tray double-click restores the window. The tray's explicit Exit command and the window X close the process. No prior explicit owner requirement to change X semantics was found, so existing behavior was retained.
- Background resume still requires the user's prior Start intent, the same account/installation, a fresh server entitlement response and a safe matching native module. It deliberately does not launch Yandex.
- No runas, administrator manifest or UAC behavior was added. W128 non-elevation guard remains active.
- Diagnostics visibility after a transient disconnect retains only the previously verified owner UI; every export/copy still performs a fresh server permission check. Logout, identity change and actual permission denial revoke access. W75 regression coverage remains.
- Yandex compatibility feed cache remains 15 minutes; a detected Yandex version change still forces an immediate refresh.

## Regression tests

- Pure tests cover first-launch default, sticky app choice, StartupApproved enabled/disabled marker variants, malformed data, and preservation of an existing OS OFF marker.
- Windows-only HKCU integration tests snapshot and restore the original test values, then exercise:
  - clean first-launch ON and actual Run command;
  - Windows Startup Apps OFF with Run entry retained;
  - first enrollment adopting the existing OFF choice;
  - explicit tray ON clearing the OS disabled marker;
  - explicit tray OFF removing CELIKOM's Run value and remaining OFF on the next startup/upgrade path.
- W15 suite: W15_NATIVE_CONTRACT_PASS 390.

## CI

- Main CI run 43710085631: SUCCESS.
- Windows integration CI run 43710085801: SUCCESS.
- W23/W22/W60 original-source, VPN, 403 and audio regressions: SUCCESS.
- W21 crash rollback and unknown updater refusal: SUCCESS.
- W24 reviewed catalog and ASAR builder: SUCCESS.
- W15 entitlement/login/native-state suite: SUCCESS.
- GUI compile with warnings as errors: SUCCESS.
- W110 independent Supervisor build and rollback checks: SUCCESS.
- W114, W117, W128 and W108 gates: SUCCESS.

## Not claimed / next order

- CI does not prove owner-PC reboot, Windows Settings UI, tray interaction, audible replacement or VPN A→B behavior.
- No EXE, ZIP, installer, release artifact or owner-machine modification was made.
- Task 1 and Task 2 remain code/test/CI-ready but not owner-PC field-accepted; issue #52 remains OPEN.
- Next: W150 Task 4 only — consolidated regression review and one grouped owner acceptance plan. Do not begin Task 5 updater or package work until Task 4 is complete.


## W158 owner-PC retest — 16.11.2026 (targeted lifecycle regression)

The owner's autorun diagnostic shows GUI_STARTED and BRIDGE_STARTED, followed by WIN_AUTORUN_MODULE_REPAIR_REQUEST / OK, START_ENABLED and WIN_AUTORUN_CONNECTED_IN_TRAY. HOST_LOADED, BUNDLE_PRESENT, WEB_CONTENTS_PRESENT, APPROVED_VIEW, PLAYER_CDP_READY and PLAYER_NET_READY appear only after the owner manually presses Stop and Start.

Code review identifies the likely false-ready boundary: ResumeSavedPlaybackAsync sets the local bridge Enabled and records WIN_AUTORUN_CONNECTED_IN_TRAY immediately after entitlement checks; it does not wait for a native-host/player heartbeat. The UI then treats bridge Enabled as sufficient to block Start. The owner reproduces a reboot case where CELIKOM looks enabled but is not attached and requires Stop/Start.

This specifically reopens runtime lifecycle acceptance; it does not reopen the completed Windows StartupApproved registry semantics. Preserve first-launch default ON, sticky OFF, explicit tray ON/OFF, per-user startup, no UAC and the rule that CELIKOM must not launch Yandex at sign-in. Keep saved Start intent separate from actual native/player readiness, wait for Yandex to become available, and attach automatically without a Stop/Start workaround. Explicit Stop must cancel the pending intent.

See docs/windows/W158-OWNER-FIELD-REGRESSION-VPN-AUTORUN-UI-20261116.md.
