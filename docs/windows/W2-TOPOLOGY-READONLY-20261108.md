# CELIKOM Windows Companion — W2 renderer-topology handoff (2026-11-08)

**Status:** W2 executable built and CI-tested; on-owner Windows W2 report is **PENDING**. No native audio substitution has been attempted. No installed Yandex files changed.

## Observed owner's real Windows (W0/W1)

From the user's W1 output:

- Windows 10, OS version `10.0.19045.0`, x64.
- Official Yandex Music installed and **running**: `%LOCALAPPDATA%\Programs\YandexMusic\Яндекс Музыка.exe`.
- EXE version `5.126.1.0`; Electron ASAR exists.
- ASAR state `OK`, size **54.96 MiB**, SHA-256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`.
- Package `YandexMusic`, package version `5.126.1`, entry `index.js` **exists**.
- W1 scanned **48** packaged JS files. `BrowserWindow=True`, `Webpack=True`, `getFileInfo string=False`.
- **Interpretation:** The archive is parseable, but source-hook feasibility is NOT proven. The actual authenticated frontend resources may be remote; missing string in 48 samples proves no absence. No Yandex account / media / private credentials were inspected.

## W2 built (unmodified official Yandex)

- GitHub: `manufact-test/nomusic` branch `experiment/windows-companion-integration-20261108`.
- W2 source commit `aef4a1db61af3de81fd31b60a362e30f22b2f089`.
- CI run [42506616157](https://github.com/manufact-test/nomusic/actions/runs/42506616157): **SUCCESS**, native Windows compile, synthetic safety test, self-contained x64 executable, ZIP artifact.
- Artifact ID: `13627254186`; name `celikom-windows-w2-topology`.
- Downloaded ZIP name: `CELIKOM-Windows-Probe-W2.zip`; SHA-256 `92add2300c5edcb372f221de8ee0d4903365f92db1679afdbd956df71026b1bc`; archive CRC verified. Contains `CELIKOM-Windows-Probe.exe` and `START-CELIKOM-PROBE.cmd`.
- ChatGPT Library: `/CELIKOM/Windows/Test/CELIKOM-Windows-Probe-W2.zip`, stable library ID `libfile_3e9d8d3560d08191b4cfb9be0a320eae`.

### What W2 actually checks

`windows-companion/Celikom.Core/AsarTopology.cs` opens the **same installed ASAR read-only** (no hooks, no patch). Counts packaged JS/HTML/preload entries, scans up to 100 files / 28 MiB with maximum 6 MiB per JS, emits presence-only flags for `BrowserWindow`, `loadURL`, `loadFile`, preload binding, `music.yandex.ru`/static frontend markers, Webpack, updater and file-info markers. Reports whether its ASAR SHA matches the **owner's W1 identity**. Does **not** open renderer devtools, inspect authenticated sessions, capture network traffic, read cookies, write Yandex files, export script bodies, URLs or absolute personal paths.

**Important limitations:** These are static **string hints**, not proof of an active audio hook or what the current track actually plays. Remote source code may be absent from ASAR entirely. A matching archive hash only pins the tested identity, not trust/authenticity. On owner machine the W2 scan has not yet run.

### One user action

With official Yandex Music playing normally:
1. Remove only the old **CELIKOM Probe** unpacked folder (not Yandex Music).
2. Extract `CELIKOM-Windows-Probe-W2.zip`.
3. Double-click `START-CELIKOM-PROBE.cmd`.
4. Send the generated `CELIKOM-Windows-report.txt` to the **next Windows development chat**.

No passwords, cookies, audio files, remote desktop access or personal install-path disclosure required.

## Decision after reading owner W2 report

1. Check W2 `Topology state` is OK and hash matches W1; otherwise investigate install/update drift before any integration.
2. Determine whether packaged entry appears to load remote Yandex frontend; if so, examine a **separate synthetic/test environment**, not live user credentials, and the stable browser-native-source research: `docs/desktop/NATIVE-SOURCE-RESEARCH-2026-11-08.md` on `experiment/desktop-native-source-20261108`.
3. Produce a version-pinned, **reversible** experimental adapter proposal for Windows official Yandex. Prioritize source-only substitution under original Yandex play/pause/seek/Next, not a separate second player.
4. Check current backend auth/entitlement/exact-ID/short-lived signed URL/Range contract in **read-only** fashion; no new backend, no leaked signed URLs, no Yandex token extraction. Backend origin may change with hosting migration; don't hardcode old Hostinger.
5. Build isolated PoC only under `windows-companion/**` on Windows experiment branch. **Never patch the owner's installed app** until owner explicitly approves a separate backup/restore plan, compatibility checks and legal/ToS review. Unsupported version -> original unmodified.
6. The browser 0.4.73 archive is frozen, the Android test work belongs to another chat, and song import plus server belongs to other owners. Do not merge, rebase or edit other teams' files.

## User-facing message to carry forward

W2 is ready and saved in ChatGPT Library. The next chat should first **receive and interpret the actual W2 report**, then continue independent Windows-specific engineering. No false claims of audio integration before one real native successful listening test with pause/seek/Next and fallback. Keep reply brief and actionable.
