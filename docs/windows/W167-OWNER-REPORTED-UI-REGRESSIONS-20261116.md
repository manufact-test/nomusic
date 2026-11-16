# CELIKOM Windows — W167 owner-reported UI regressions and rollback baseline

Date: 16 November 2026  
Product: CELIKOM Windows only  
Status: **handoff only. No W167 code fix or installer has been made. W166 / 0.24.48.0 is not owner-accepted.**

## 1. Source of truth — use the previous version

Repository: `manufact-test/nomusic`

**W167 working branch:**
`experiment/windows-w167-owner-ui-regressions-20261116`

**Branch starting point:**
`7b956d18314ef1d0d1bf6871551b33dc5d2840ba`

This is the exact pre-W166 backup snapshot:
`backup/windows-main-pre-w166-owner-status-dom-observer-20261116`

The branch contains the **W165 / 0.24.47.0 code**, with only the W165 documentation commits after the code checkpoint. The code checkpoint is:
`ebd16ca19f37620d620c0a6ee5e9e5361fddd607`

- Owner-review version: **0.24.47.0**
- Native module: **0.24.31**
- W165 installer artifact: [W20 run](https://github.com/manufact-test/nomusic/actions/runs/43885551217), artifact ID `14235136060`
- Exact older pre-W165 backup, if required: `backup/windows-main-pre-w165-owner-spacing-status-copy-20261116` @ `a8d9d43de68e03553acbbb21d09650c23ff64807`

**Do not use W166 / 0.24.48.0 as the starting point. Do not reset or force-push main.** Main remains a preserved W166 comparison point; W167 work belongs on the dedicated branch above.

W166 reference only:
- Code checkpoint: `5bfd6c6e33c4a1008952ba1fc6c53918ce93792e`
- W166 package commit: `07afc2da864ff44c87320d924eb4c94310628c65`
- Main documentation commit: `4f2caee1cc6889b2fe4f73654a823d9030129517`
- App version: **0.24.48.0**
- W166 CI/package passed, but owner runtime acceptance failed. CI success is not owner acceptance.

## 2. Owner's latest 0.24.48.0 report — three screenshots

The owner installed W166 / 0.24.48.0 and supplied three screenshots. The following are the observed states, not assumptions about their underlying cause.

### Screenshot 1 — immediately after pressing Start

Visible:
- Header connection dot is gray.
- Track area still says `Подмена выключена. Нажмите «Старт», чтобы подключиться к Яндекс Музыке`.
- An additional stale/action hint says `Нажми «Старт», чтобы обновить модуль CELIKOM.`
- The expected immediate green Yandex connection/loading text is absent.

**Required behavior:**
- The instant the user presses Start, immediately show the existing green `CompactPlaybackPresentation.ConnectingMessage`:
  `Подождите, идёт подключение к приложению Яндекса.`
  (The current source uses an intentional newline before `к приложению Яндекса.`.)
- During the explicit Start/module-upgrade operation, do not show the disabled-state copy and do not show the idle hint `Нажми «Старт», чтобы обновить модуль CELIKOM.`
- The connection/loading copy must appear before Yandex opens, not only after Yandex has launched.
- Preserve the actual native module version check and upgrade path. **Do not bypass module validation or pretend an update succeeded.** Suppress the idle hint only while the explicit Start/upgrade is in progress; show a genuine failure if the operation fails.

Source investigation clue from W165:
- `StartAction` initially sets `_compactStarting = true` and renders the connection message.
- In the module-mismatch path it later clears `_compactStarting` before calling `ConnectYandexAsync`.
- `RenderCompact` shows `hostHint = "Нажми «Старт», чтобы обновить модуль CELIKOM."` when the bridge is disabled, startup flag is false, and the installed module does not match the application.
- This is a strong candidate for the unwanted hint during an explicit Start, but verify the actual state sequence before changing it. Keep the explicit module refresh intact.

### Screenshot 2 — Yandex has opened, track metadata has not arrived yet

Visible:
- Connection dot is green.
- A transient row appears: `Ожидаем воспроизведения в Яндекс Музыке…`
- It remains for roughly 1–2 seconds; the next track then appears.

**Owner requirement: this transient text must not appear at all.** The owner says this behavior had already been corrected and must not return.

Required behavior:
- Do not show `Ожидаем воспроизведения в Яндекс Музыке…` during startup or the short track/metadata transition.
- Keep the agreed green connection/loading presentation while Yandex is attaching, or leave the transient track-status row blank until a real state is available. Do not invent a new waiting label.
- Preserve W164's 2.5-second previous-title/artist metadata handoff, its no-raw-Track-ID behavior, and its suppression of `Проверяем версию песни CELIKOM…` while the presence request is pending.
- Do not add a second waiting row under the startup banner.

Source investigation clue:
- `CompactPlaybackPresentation.TrackPlaceholder(...)` still returns `Ожидаем воспроизведения в Яндекс Музыке…` for the enabled + fresh-heartbeat + UNKNOWN-playback-state fallback.
- W164 hid the *presence-check* pending message; that is a different fallback. Verify the path that renders the exact screenshot text and remove/suppress only this transient state without breaking genuine stopped, paused, disconnected or error states.

### Screenshot 3 — current track is visible

Visible:
- Track: `Новогодняя`
- Artist: `GUF`
- Status: gray `Версия CELIKOM доступна`

**Required active wording:** `Играет версия CELIKOM`, in green, when the current track is genuinely using its CELIKOM replacement.

Important evidence boundary:
- W165 already defines the exact active wording `Играет версия CELIKOM`.
- Its green state requires current PLAYING + `ACTIVE_REPLACEMENT` + `NATIVE_SOURCE_VERIFIED` + approved presence.
- The W54 owner diagnostic from 0.24.46.0 saw Media properties but did not see CDP `kUrl`; it explicitly did not establish audible-source proof. Therefore `Версия CELIKOM доступна` can remain neutral if exact decoder proof is absent.
- W166 attempted a new passive DOM source observer, but the owner screenshot still showed the old gray availability text. No owner evidence confirms that the DOM fallback solved the current Yandex build.
- Do not simply force green based on mapping, entitlement, HTTP 206, prefetch, generic PLAYING or a different player. If exact proof remains missing, inspect the actual W55 diagnostic from 0.24.48.0 if the owner has it; distinguish an observer compatibility problem from a presentation problem. Do not transplant the W166 DOM observer into W167 without proving it is needed and correct.

## 3. Pause color — known W165 defect to correct narrowly

W165's color expression explicitly includes:
`activelyReplacing || (paused && serviceConnected)`

That makes `Пауза` green when the native service is connected. The owner previously called this out as wrong.

W166 removed the pause-green branch and made pause neutral. This is a useful isolated behavior, but do not carry over the rest of W166 wholesale.

W167 target:
- `Пауза` must be neutral/gray.
- Green is reserved for the exact verified active CELIKOM replacement state.
- Do not change the header connection dot: it is a separate service-heartbeat indicator and may remain green while paused.

## 4. Spacing — retain only the useful visual improvement

The owner said the only visible positive from W166 was the smaller bottom spacing; the gap still needs to be slightly tighter.

- W165 uses a 40 px active status row and 8 px gap.
- W166 changed this to 28 px row height and 4 px gap.
- The owner observed improvement, but asked for a little less space.

Port/rework this as a **small isolated layout change** on the W165 base. Compare the screenshot and adjust only the active status-to-Account spacing. Do not globally change window height, all row gaps, idle-state spacing, title/artist positions, or the whole popup.

## 5. Preserve previously accepted behavior

W164 / **0.24.46.0** was manually accepted for VPN/audio continuity:
- Repeated VPN changes did not interrupt CELIKOM playback.
- No extra recovery text flashed during those changes.

Do not modify:
- audio playback or source routing;
- VPN/network recovery and entitlement retry behavior;
- entitlement authority or server behavior;
- Yandex original files;
- updater architecture, signing or production deployment;
- Android or browser extension.

Do not repeat broad VPN/audio testing. There is no new audio regression in the owner's latest report.

## 6. W167 implementation order

1. Confirm the W167 branch is based on W165 and inspect the exact current source before editing. Keep main/W166 untouched.
2. Fix Start-state presentation first: immediate green connection message from the click, no disabled text or idle module hint during the explicit operation; preserve module upgrade and fail-closed checks.
3. Remove the short `Ожидаем воспроизведения в Яндекс Музыке…` flash while preserving W164 metadata grace and all real playback/error states.
4. Make `Пауза` neutral. Keep the service connection indicator independent.
5. Carry forward only the compact active-status spacing improvement and tighten it slightly if required by the screenshot.
6. Investigate active green status separately against real current-source evidence. Reuse W165's exact wording; do not force a false green.
7. Add only focused regression tests for these state transitions and colors. No broad audit, new runtime hooks, or large observer experiment.
8. Run relevant W15/W23/Windows integration and main CI. Produce one internal owner-review package only after the focused changes pass. No intermediate installers.

## 7. Required owner-visible acceptance

- Press Start: green Yandex connecting text appears immediately, before Yandex opens. No disabled copy or `Нажми «Старт», чтобы обновить модуль CELIKOM.` while Start/upgrade is in progress.
- Yandex opens: no `Ожидаем воспроизведения в Яндекс Музыке…` flash.
- Track title/artist remain stable through Next; no raw Track ID or presence-check flash.
- A genuinely active CELIKOM replacement displays `Играет версия CELIKOM` in green only with valid current-source proof.
- Pause is neutral, not green.
- Active status-to-Account gap is a little tighter; idle placeholder spacing is preserved.
- Existing VPN/audio behavior remains untouched.

## 8. Files and prior documentation to read

Read before editing:
1. `docs/windows/NEXT-CHAT.md`
2. This file: `docs/windows/W167-OWNER-REPORTED-UI-REGRESSIONS-20261116.md`
3. `docs/windows/W161-UI-STATE-START-COPY-20261116.md`
4. `docs/windows/W163-OWNER-TRACK-TRANSITION-UI-POLISH-20261116.md`
5. `docs/windows/W164-OWNER-VPN-RECOVERY-TRACK-TRANSITION-20261116.md`
6. `docs/windows/W165-OWNER-TRACK-SPACING-AND-ACTIVE-STATUS-20261116.md`

W166 is a rejected owner build and comparison point, not the implementation base.

## 9. Truthful status

No W167 code has been changed, no W167 CI has run, and no W167 installer exists yet. This handoff records the owner's observed defects and the exact rollback baseline. Do not claim any of the reported UI problems are fixed until the owner installs and checks the next build.
