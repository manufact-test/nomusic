# CELIKOM Windows — CURRENT handoff

**Last updated:** 17 November 2026. This is the **single active Windows entry point**. Earlier W167/W168/W169 handoffs below are historical; do not act on them as live task instructions.

## Owner accepted current working build

**CELIKOM Windows app 0.24.51.0, native Yandex module 0.24.32 — OWNER ACCEPTED AS CURRENT WORKING BUILD, LIMITED PRIVATE BETA.** The owner ran it for several hours (normal playback, Next, pause and VPN toggles) without any observed Yandex restart, sound interruption or UI regression and explicitly said to freeze this version if nothing further breaks. Do not call it a signed public release or assert that the rare past crash root cause has been proved permanently cured. User intends a clean reinstall on his machine and private testing on a friend's PC; website/public release requires separate signoff.

**FIRST READ**:
1. `docs/windows/CURRENT-WORKING-RELEASE.md` — frozen exact package, SHA256, status, evidence and rollback.
2. `docs/windows/PRIVATE-BETA-INSTALL-AND-PUBLICATION-20261117.md` — exact uninstall/reinstall, friend test, release gating.
3. `docs/windows/W169-TRACK-HANDOFF-AND-YANDEX-RESTART-GUARD-20261117.md` — historical implementation and diagnostic caveats.

**Exact W20 reviewed package source SHA:** `c717428a7d9f01fc8e33b482fcf66a9ed1a02947` (no newer code is considered accepted merely because docs HEAD moves). Frozen source branches `stable/windows-02451-private-beta-20261117` and `backup/windows-02451-owner-accepted-exact-20261117` both point to it. Active documentation branch `experiment/windows-w167-owner-ui-regressions-20261116`. `main` intentionally unchanged.

**Distribution:** owner-approved internal unsigned EXE `CELIKOM-W169-TRACK-HANDOFF-02451-UNSIGNED.exe` plus optional ZIP `CELIKOM-Windows-0.24.51.zip` and checksums in verified **personal ChatGPT Library `/CELIKOM/W169/`**. Do not provide or suggest GitHub Actions artifact URLs or sandbox download links. Do not falsely claim a per-file public Library URL; the friend needs a private file transfer. No new build or change is requested now.

**Public release gate remains active:** `windows-companion/w20/release-gate.ps1 -Mode Release` blocks until signed/verified. Do not bypass it or publish owner test binary to the public website/feed. Production signing and independent clean-machine audio/security validation are still outstanding.

**Freeze:** no unsolicited VPN/network recovery tuning, track/status UI edits, Yandex native host changes or server/account changes. Rare Yandex restarts were absent in the owner's hours-long W169 test; if reproduced later, collect exact timestamps, current diagnostic and Windows event entries before changing source.

## Historical references (NOT current instructions)

- `docs/windows/W168-OWNER-THREE-ISSUES-20261117.md` — 0.24.50 UI restoration and prior crash investigation.
- `docs/windows/W167-OWNER-REPORTED-UI-REGRESSIONS-20261116.md` — W167 0.24.49 fixes.
- `docs/windows/W164-OWNER-VPN-RECOVERY-TRACK-TRANSITION-20261116.md` — already accepted VPN route recovery.
- Other older docs are archive context only, not a reason to roll back or rebuild accepted 0.24.51.

**Next action:** owner will manually uninstall/reinstall this exact binary; an invited friend will test. Nothing to patch unless the owner provides a concrete regression, or separately approves production release work.
