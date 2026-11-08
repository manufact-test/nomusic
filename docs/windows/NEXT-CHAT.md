# CELIKOM Windows Companion — NEXT-CHAT.md

**Handoff date: 2026-11-08 | Status: W2 ready; awaiting real owner W2 report.**

## Mission and restrictions

Build a **separate Windows companion app** for the **official installed Yandex Music**. The official app must remain the ONLY playback owner (native Play/Pause/Seek/Next/queue/volume). Target source-level audio substitution with CELIKOM's exact approved catalog. The user does NOT want an embedded music website, an independent player or a duplicated sound clock. Reuse shared CELIKOM server account, entitlement/trial/subscription, moderation, audio Range URLs and diagnostics **without changing the server**. Preserve fail-to-original and reversible integration.

**Parallel work:** Browser extension, Android (currently active **test** branch, not stable promotion), audio import, shared API and website are handled in other chats. DO NOT modify, merge, rebase or deploy their work. Browser accepted `0.4.73` at `archive/desktop-0.4.73-accepted-20261104` remains untouched. Previous experiments with native-source browser and competitor approaches did not demonstrate better production listening; do not import them as a working fix.

## GitHub working surfaces

- Repository: `manufact-test/nomusic`.
- Windows exclusive development branch: `experiment/windows-companion-integration-20261108`.
- Windows planning reference: `planning/windows-companion-v1-20261108`.
- Allowed implementation paths: `windows-companion/**`; docs `docs/windows/**`; dedicated `.github/workflows/windows-companion-readonly.yml` only for this experiment.
- Separate browser experiment `experiment/desktop-native-source-20261108`: **READ ONLY for research**. No cherry-pick/merge without owner approval.
- Do not edit `extension/**`, `android/**`, `server/**`, `website/**`, `main`, `develop`, the archived baseline or live deployment.

## Confirmed REAL user machine

Owner personally ran both W0 and W1 (not W2 yet):
- Windows 10 build 19045 x64.
- Official Yandex Music EXE `5.126.1.0`, running at `%LOCALAPPDATA%\Programs\YandexMusic\Яндекс Музыка.exe`.
- ASAR is present, parses successfully; package `YandexMusic` v`5.126.1`; entry `index.js` found; size 54.96 MiB; SHA-256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`.
- W1 sample: 48 local JS; BrowserWindow True; Webpack True; file-info marker False. **This does NOT prove unavailable hook**; it may reside in remotely delivered renderer bundles.
- No integration installed, no patched Yandex files.

## W2 COMPLETED (development & automated tests, not owner-run)

- Source commit `aef4a1db61af3de81fd31b60a362e30f22b2f089`.
- Windows CI [42506616157](https://github.com/manufact-test/nomusic/actions/runs/42506616157): **SUCCESS** (build, synthetic safety checks, single-file Win x64 exe, artifact).
- ZIP `CELIKOM-Windows-Probe-W2.zip`, SHA-256 `92add2300c5edcb372f221de8ee0d4903365f92db1679afdbd956df71026b1bc`, Library `CELIKOM/Windows/Test`, Library ID `libfile_3e9d8d3560d08191b4cfb9be0a320eae`.
- W2 read-only ASAR topology inventory: reports static presence of loadURL/loadFile/preload, Yandex Music/static host marker, getFileInfo/batch, Webpack, updater, archive hash match and scan limitations. It does NOT capture live requests, sources, personal data, credentials or audio, and does NOT modify Yandex.

## IMMEDIATE NEXT TASK — receive user's W2 output

User should unpack W2, run `START-CELIKOM-PROBE.cmd` with Yandex Music running, and send `CELIKOM-Windows-report.txt` to you. **Do not ask for another W1 result: already received.**

After inspecting W2 report:
1. Verify exact ASAR identity and whether any marker points to remote Yandex renderer. If changed, address version mismatch read-only before testing a hook.
2. Study code/design at `docs/windows/ARCHITECTURE.md`, `docs/windows/PRODUCT-DESIGN.md`, `docs/windows/mockup.html`, `docs/windows/ROADMAP.md`, `docs/windows/W2-TOPOLOGY-READONLY-20261108.md`.
3. Compare read-only competitor references `S4YN3X/FkCensor`, `Hazzz895/FckCensor`, and failed/limited browser experiment `docs/desktop/NATIVE-SOURCE-RESEARCH-2026-11-08.md`. Do not require any third-party mod installation.
4. Propose a **small isolated PoC**, using an approved synthetic resource/track fixture: exact ID, single Yandex decoder, original controls, source substitution, signed short-lived URL/Range handling, cancellation, Stop/Original, no network/account token leakage.
5. Only if the PoC is feasible: secure owner's explicit approval for backup + byte-checked rollback before altering official Yandex installation. Need update/version gate, no forced closure of running Yandex and no permissions escalation without explanation.
6. If direct integration is not viable, say so and recommend an alternative instead of silently building a separate player.

## Product direction

- Minimal branded CELIKOM window/tray; Manrope, `#0B1013`, mint `#66E0BF`, `#F7F8F4`. See visual mockup.
- UI: Yandex attached/offline/unsupported, Start/Stop, Restore Original, Upload Version, Suggest Song, account/trial/rewards, diagnostics and updates. Status must reflect reality; mockup is not product.
- Single CELIKOM account and server catalog across browser/Android/Windows; separate per-device token. Check current backend branch and hosting-migration status read-only; no hardcoded Hostinger domain.
- Never claim source playback, live compatibility or full restoration just because CI/ASAR scanning passed.

## Reporting

Concise Russian. Tell user only what truly works, what's still untested, what exactly to do next. Avoid needless questions, rambling diagnostics and repeated history.

**Full checkpoint:** [W2-TOPOLOGY-READONLY-20261108.md](W2-TOPOLOGY-READONLY-20261108.md).
