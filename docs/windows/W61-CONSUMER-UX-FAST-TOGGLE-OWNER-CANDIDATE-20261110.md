# W61 — Windows 0.24.9 consumer interface + faster Start/Stop bridge (2026-11-10)

## Owner evidence and preserved baseline

- **0.24.8 user test:** owner directly confirmed that **Start and Stop finally change the already playing song**. The transition has audible interruption / sharp click and is perceptibly slow; **smoothness is NOT confirmed or solved**. User says the old 0.24.8 vs module 0.24.7 screenshot was simply before pressing the module upgrade button, **not a reproduction of update corruption**.
- The owner intended to attach a fresh ZIP diagnostics file, but **the ZIP is NOT available in the conversation file inventory** at the time of this handoff. Do not invent diagnostic findings.
- Working accepted **0.24.7 audio / pause / seek / Next / MyWave** stays frozen at `backup/windows-w57-owner-audio-accepted-0247-20261110`.
- Frozen actual owner-tested **0.24.8 Start/Stop baseline**: `backup/windows-w60-0248-owner-toggle-pass-before-ux-20261110` @ `a2a0a719080e101bc38f81adf59bcb76a185450b`. Never rewrite rollback.

## Source changes — experimental W61 branch only

Branch: `experiment/windows-stop-lifecycle-20261110`.

- Consumer `MainWindow.cs`: full-width navigation; account tab red until signed in; first run opens account panel; no API origin field, no developer exposition, rounded extension-style email/password controls `PopupInput.cs`, simple home Start/Stop and real status. Logged-in account page shows email + logout. Keeps extension palette.
- Public interface no longer displays **open Yandex, restore Yandex, connect/update module, application update, diagnostics** as six unrelated actions. **Start** launches installed native Yandex if absent and, with a clear confirmation, installs/refreshes the native CELIKOM integration if missing/outdated. Existing user integration prompts stay non-destructive; original Yandex snapshot and restore safety contracts remain. Staff-only update picker can still be opened via Ctrl+Shift+U; private admin diagnostics button may be shown on home.
- Diagnostics staff gate: **same exact email SHA256 allowlist as extension/src/auth/diagnostic-access.ts**, additionally validated by authenticated live CELIKOM `GET /api/v1/auth/me` user ID, active status and email; rechecked **on every download**, not just visually hidden. Ordinary users cannot export via UI. If backend unavailable, gate is fail-closed. No new server or authentication permission policy.
- `host.cjs`: serialized local-only state poll reduced **600ms → 260ms**. This removes some button latency but does **not** claim to accelerate Yandex network decoding or fix clicks. Actual Yandex `reloadEntity("QUALITY_CHANGE")` remains unchanged. Native source, W56 signed guard, media controls, MyWave and user audio remain otherwise untouched.
- `0.24.9` is a private unsigned staged owner candidate, **not a public release**. Same Inno AppId `D99FDB90-46BF-4EE5-989E-659A2B6450D6`, same installation path / data, one application.
- No audio-volume ramp / crossfade hack added. The signed Yandex player currently performs a native source reload; an unsound fade can break the user's volume and existing crossfade. Need real timestamps from owner diagnostic or verified vendor effect API first.

## Tests and exact distributable

- UI WinForms build, signed grant/native contract and PNG stage: GitHub Actions **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42811301969
- W60 native reload/source contract after faster polling: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42811289914
- W61 full Windows installer+native+tests+single-app disposable smoke **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42811326672
- **Independent existing 0.24.8 → 0.24.9 same-user DPAPI, single AppId, same uninstaller, native host 0.24.9, original Yandex untouched: SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42811784981
- Artifact ZIP ID: `13762134692`, archive SHA256 `85493b27f5315dae3f7bd9640b1cd0f51e0f5febc7e9810a2113818593c7ac1a`.
- Filename: `CELIKOM-W61-CONSUMER-UX-FAST-TOGGLE-UNSIGNED.exe`; exact EXE SHA256 `71c656129d68d596439e242513242fe86acd47eb0b9c35a94e7fb469f934159d`, 43,508,854 bytes.
- Uploaded to ChatGPT Library `/CELIKOM/Windows/CELIKOM-W61-CONSUMER-UX-FAST-TOGGLE-UNSIGNED.exe`, file ID `file_00000000a5d88246892f939fa3507c7c`. Independently re-materialized from Library and SHA256 **matches**.
- The 0.24.9 build is compiled from a branch snapshot preceding this docs-only commit; no source changes after installer CI.

## Owner trial and remaining action

1. Use the **existing 0.24.8 application's** `Обновить CELIKOM` picker and select exact new W61 EXE. Do not uninstall/re-login, never install a second player.
2. Verify account red on signed-out UI, normal green state after login; rounded fields; Start opens Yandex if closed, installs/refreshes integration when required, and Stop/Start change an already playing track.
3. Verify actual pause, seek, Next and MyWave unaffected.
4. **Click and long pause are NOT fixed / not owner-verified.** Need owner's real 15-minute `CELIKOM-diagnostics-....txt` (or ZIP containing TXT). Analyze `NATIVE_TOGGLE_RELOAD_*`, `RENDERER_STATE_*`, `PLAYER_NET_*`, `MEDIA_*` timing. Keep URLs/tokens redacted. Before changing volume or replacing sources by hack, validate exact pinned signed Yandex 5.126.1 API and guard user volume, pause/seek and MyWave.
5. Roll back to previously owner-accepted 0.24.8 if W61 has a regression; do not touch production backend, Android Test.50 or Yandex-original host.

W61 is **not yet owner-tested**. Do not equate clean CI with audible acceptance.
