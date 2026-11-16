# CELIKOM Windows — active handoff W167 (16 November 2026)

**Current task: recover the expected Windows UI behavior from the W165 / 0.24.47.0 baseline. W166 / 0.24.48.0 was not accepted by the owner. Handoff only: no W167 code changes or installer have been made yet.**

## Exact starting point

- Product: CELIKOM Windows only.
- Repository: `manufact-test/nomusic`.
- Working branch: `experiment/windows-w167-owner-ui-regressions-20261116`.
- Branch start: `7b956d18314ef1d0d1bf6871551b33dc5d2840ba`.
- Exact pre-W166 backup: `backup/windows-main-pre-w166-owner-status-dom-observer-20261116` @ `7b956d18314ef1d0d1bf6871551b33dc5d2840ba`.
- W165 code checkpoint: `ebd16ca19f37620d620c0a6ee5e9e5361fddd607`.
- Base app: **0.24.47.0**, native module **0.24.31**.
- W165 owner-review installer artifact: [W20 run](https://github.com/manufact-test/nomusic/actions/runs/43885551217), artifact ID `14235136060`.
- Main still preserves W166 / 0.24.48.0; do not reset or force-push main.
- W166 comparison: code `5bfd6c6e33c4a1008952ba1fc6c53918ce93792e`, app **0.24.48.0**. It passed CI/package checks but failed owner runtime acceptance.

## Owner's latest screenshots on 0.24.48.0

1. Immediately after Start: gray dot, disabled copy still shown, plus `Нажми «Старт», чтобы обновить модуль CELIKOM.`; the immediate green Yandex connection/loading text is missing.
2. After Yandex opens: `Ожидаем воспроизведения в Яндекс Музыке…` flashes for about 1–2 seconds before the next track appears. Owner explicitly says this must not appear; this behavior had already been corrected.
3. With track `Новогодняя` / `GUF`: status remains gray `Версия CELIKOM доступна` instead of the expected green `Играет версия CELIKOM` while the CELIKOM replacement is genuinely active.
4. Owner says the only visible improvement from W166 was the smaller bottom gap; it still needs to be slightly tighter.

## Exact target behavior

- Start click immediately displays the existing green `Подождите, идёт подключение к приложению Яндекса.` (source constant uses a line break before `к приложению Яндекса.`). Do this before launching/opening Yandex. During explicit Start/module refresh, suppress the disabled text and idle module hint. Keep module version checks and the real update path intact.
- Never flash `Ожидаем воспроизведения в Яндекс Музыке…` during startup/metadata transition. Preserve W164's 2.5-second previous-title handoff, no-raw-Track-ID rule, and suppression of `Проверяем версию песни CELIKOM…` while presence is pending.
- Active replacement copy is exactly `Играет версия CELIKOM`, green only with real current-source proof. Do not fake green from mapping, entitlement, HTTP 206, prefetch or generic PLAYING.
- `Пауза` is neutral, not green. Header connection dot is separate and can stay green while service heartbeat is fresh.
- Keep the W166 spacing improvement only as an isolated layout delta; tighten the active status-to-Account gap slightly further without global layout changes.
- Keep the previously accepted W164 / 0.24.46 VPN/audio behavior frozen.

## Useful source clues

- W165 `StartAction` sets `_compactStarting=true` and renders the connection copy, but clears it before the module-mismatch `ConnectYandexAsync` path. `RenderCompact` then allows `hostHint` to show `Нажми «Старт», чтобы обновить модуль CELIKOM.` while the explicit operation is underway. Verify the exact event sequence; suppress the idle hint during Start without bypassing the module update.
- `CompactPlaybackPresentation.TrackPlaceholder` has a fresh-heartbeat + UNKNOWN-state fallback that returns `Ожидаем воспроизведения в Яндекс Музыке…`. This is separate from the W164 presence-check message that was already hidden. Suppress this transition-only fallback without hiding genuine errors/stopped/paused states.
- W165's color expression `activelyReplacing || (paused && serviceConnected)` makes Pause green. W166 removed that pause-green branch; port only this narrow behavior.
- W165's exact active copy already exists. W54 showed Media properties but no `kUrl`, so active-source proof may remain unavailable. W166 added a passive DOM observer, but the owner's screenshot still showed neutral availability and does not establish that it worked. Inspect a W55 diagnostic if available; do not transplant the W166 DOM observer without evidence.

## Required work order

1. Read this handoff and `docs/windows/W167-OWNER-REPORTED-UI-REGRESSIONS-20261116.md`, then inspect W161/W163/W164/W165. Confirm the branch and baseline before changing anything.
2. Fix Start-state message timing and suppress the module hint during explicit Start/upgrade.
3. Suppress the transient playback-waiting row during startup/track metadata handoff.
4. Make Pause neutral; keep header connection status independent.
5. Carry only the compact spacing improvement and tighten slightly.
6. Investigate the active green proof separately; do not weaken its evidence gate.
7. Add focused regression tests, run relevant CI, then create one internal owner-review installer. No intermediate packages.

## Hard boundaries

No Android, browser extension, backend, audio engine, VPN recovery, entitlement authority, Yandex original files, updater architecture, production signing or deployment. No broad audits, speculative runtime hooks, or unrelated refactors. No claims of owner acceptance before manual verification.

## Full task document

`docs/windows/W167-OWNER-REPORTED-UI-REGRESSIONS-20261116.md`
