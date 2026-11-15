# W157 — Owner follow-up: VPN source handoff, Yandex lifecycle and UI truth

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Only working branch: `main`  
Product: the one existing CELIKOM Windows application  
Authority: this is the latest owner-reported follow-up. It supersedes the previous handoff statement that the only remaining action was W154 owner acceptance. It does not authorize an architecture change or unrelated work.

## 1. Checkpoint and evidence status

- Documentation baseline before this update: `b636fe61be9b1d210e4a10a056d506af1643e630` on `main`.
- Exact backup branch created before documentation changes: `backup/windows-main-pre-w157-owner-vpn-ui-findings-20261115` @ `b636fe61be9b1d210e4a10a056d506af1643e630`.
- Last documented release-source checkpoint: `bc59e0c7e4db749d616b318beb89369245811b44`.
- The earlier 0.24.38 bootstrap exists as an unpublished Draft Release. It predates the new owner findings and must not be treated as a fix for them.
- The owner has performed additional live tests and reported the observations below. The exact installed/tested version was not stated in this message; do not guess it.
- Diagnostics have been promised by the owner but have not yet been supplied in this handoff. No diagnostic files have been reviewed here.
- At the initial documentation-only W157 checkpoint, no application code was changed and no new build was produced. Subsequent W157 implementation is recorded in §7 below; diagnostic files remain outstanding.

## 2. New owner observations

### A. VPN reconnect causes an unnecessary source switch

Owner's observed sequence:

1. CELIKOM replacement is playing normally in Yandex Music.
2. VPN is switched off/on.
3. CELIKOM UI reports a disconnect/reconnect state, with a delay before the text changes.
4. Despite the internal disconnect indication, the replacement audio continues playing normally. The owner did not hear an actual loss of the CELIKOM track at this point.
5. When CELIKOM reports that it has reconnected, playback unnecessarily jumps from the CELIKOM replacement to the original and then back to the replacement. This creates the audible pop/transition.

**Owner's expected behavior:** if the current CELIKOM replacement is still playing, do not touch its audio source just because the CELIKOM server/network connection was interrupted.

Required behavior:

- Keep server connectivity, Yandex process/player lifecycle, playback state and current audio-source identity as separate states.
- A transient backend/VPN outage alone must not be treated as proof that the current decoder or replacement stream was lost.
- If the exact current replacement decoder is still active and playback continues, restore the server connection in the background. Do not reattach, restart, replace, or switch the audio source.
- Only run audio recovery if the current playback/decoder/source was actually lost, based on the existing exact-current-track evidence.
- Preserve the currently faster VPN reconnect. Do not regress to the old slow reconnect.
- Do not weaken source-verification safeguards or infer source identity from a stale heartbeat, mapping, URL transfer or network status.

The suspected category is a conflation of network/session loss with actual audio/player loss. This is a diagnostic direction, **not yet a proven root cause**.

### B. Fully closed Yandex Music remains displayed as the current song

Owner's observed sequence:

1. Yandex Music is fully exited/closed.
2. CELIKOM continues showing the previous song/current-player state for approximately 30 seconds, even though the player is already gone.
3. Only later the UI changes to `Ожидаем данные текущего плеера`.

Required behavior:

- Detect actual Yandex process/player destruction promptly.
- Clear the stale track and playback/source state as soon as the player is known to be closed; do not keep displaying the previous song for the lease timeout.
- Replace the vague `Ожидаем данные текущего плеера` state with a clear user instruction: `Подключитесь к Яндекс Музыке` (or the established equivalent wording used consistently across the app).
- Do not show a generic wait-for-player message when there is no Yandex player to provide data.
- Use the existing process/player lifecycle signals and correct state reconciliation; do not add an arbitrary cosmetic timer or weaken exact current-player identity checks.

### C. Other UI inconsistencies

Owner reports multiple interface defects: texts change incorrectly, some colors do not match the actual state, and status presentation is inconsistent.

Required behavior:

- Review the text and color mapping for the states touched by the two cases above and the related connection/player states.
- Make every label and color reflect the actual state; keep the same state vocabulary throughout the UI.
- Fix only confirmed inconsistencies. No redesign, new screens, unrelated cosmetic work, or broad UI refactor.
- Do not display a successful reconnect/source-transfer message unless the corresponding operation really happened.

### D. Diagnostics

- Owner intends to send diagnostic files separately.
- When they arrive, inspect them and correlate timestamps/events with items A–C.
- Until then, do not claim that diagnostics were checked, invent log findings, or block independent code inspection on files that have not yet been provided.
- Use diagnostics to confirm or reject a specific hypothesis, not as a reason to open unrelated investigations.

## 3. Strict execution order

Complete each item to implementation + targeted tests + CI-ready state before moving to the next. Do not mix tasks or start unrelated work.

1. **Yandex close/lifecycle state:** fix prompt detection of a closed Yandex player, stale song clearing and the user-facing connect instruction.
2. **VPN audio continuity:** stop the unnecessary source handoff when the current replacement is still playing; recover backend connectivity independently; preserve fast reconnect. Only recover audio after verified actual audio/source loss.
3. **UI consistency:** correct the confirmed text/color/status mappings for these states, without redesigning the interface.
4. **Diagnostics correlation:** when the owner supplies diagnostics, inspect only the relevant evidence and reconcile it with items 1–3. Do not invent extra tasks.
5. **Verification:** add focused regression tests for each fix, run the relevant Windows test suites and both required CI workflows. CI does not replace the owner's audible/manual acceptance.
6. **One consolidated build:** only after items 1–5 are complete, prepare and send exactly one new Windows version for owner testing. No intermediate EXE/ZIP/installers and no premature release. Use the existing approved release/updater pipeline; do not repeat key provisioning or redesign it.

The owner wants the developer to continue through the ordered work without stopping for small progress reports. Stop only when actual owner-side testing/input is required or when the complete consolidated build is ready.

## 4. Explicit exclusions

- Do not touch Android, the browser extension, shared server/backend, or the Yandex original installation/assets.
- Do not change the Windows product architecture or create a second player.
- Do not reopen the already completed updater/P-256 implementation, key provisioning, W155/W156 audit, autostart/tray work, or historical issues unless a specific regression in the new scope proves it necessary.
- Do not broaden the UI task into a redesign or general cleanup.
- Do not build intermediate packages.
- Do not publish the old 0.24.38 Draft or a production feed as part of this work.
- Work only on `main`; create an exact backup before substantial code changes; preserve existing release/security safeguards.

## 5. Definition of done

- Closing Yandex promptly clears the current song and shows a clear instruction to connect/open Yandex Music.
- A VPN/network interruption does not cause an audio-source switch while the exact current CELIKOM replacement continues playing.
- If actual audio loss occurs, recovery is based on verified current-player/current-decoder state and does not create redundant handoffs.
- UI texts and colors match the real connection, player, playback and source states.
- Relevant diagnostics, when supplied, are checked and findings recorded without expanding scope.
- Focused tests and both required CI workflows pass.
- Exactly one new consolidated Windows build is delivered after all fixes; no intermediate packages are sent.

## 6. First message for the next chat

Copy this as the next chat's first user message:

---

Привет! Принимай **CELIKOM Windows** как ведущий разработчик. Продолжай существующую работу строго с текущего состояния. Ничего не начинай с нуля и не меняй архитектуру.

**GitHub:** `manufact-test/nomusic`  
**Единственная рабочая ветка:** `main`  
**Документационный baseline до W157:** `b636fe61be9b1d210e4a10a056d506af1643e630`  
**Точный backup:** `backup/windows-main-pre-w157-owner-vpn-ui-findings-20261115` @ `b636fe61be9b1d210e4a10a056d506af1643e630`  
**Последний документированный release-source checkpoint:** `bc59e0c7e4db749d616b318beb89369245811b44`

Сначала прочитай верхний актуальный блок `docs/windows/NEXT-CHAT.md`, затем `docs/windows/W157-OWNER-FOLLOW-UP-VPN-PLAYER-UI-20261115.md`, `docs/windows/W150-OWNER-CONFIRMED-SCOPE-AND-SEQUENTIAL-WORK-ORDER-20261115.md` и `docs/windows/W154-CONSOLIDATED-REGRESSION-AND-OWNER-ACCEPTANCE-PLAN-20261115.md`. Старые handoff-блоки ниже актуального верха — история, не текущий план.

**Новые подтверждённые наблюдения владельца:**
- При переключении VPN CELIKOM ошибочно показывает переподключение, хотя наша версия продолжает играть. После восстановления соединения происходит ненужный скачок «наша версия → оригинал → наша версия» со звуковым артефактом.
- После полного закрытия Яндекс Музыки старая песня остаётся в интерфейсе примерно 30 секунд; затем появляется непонятное `Ожидаем данные текущего плеера`. Нужно быстро очищать состояние и писать понятное `Подключитесь к Яндекс Музыке`.
- В интерфейсе есть неправильные тексты, цвета и статусы.
- Диагностику владелец пришлёт отдельно; пока не утверждай, что она проверена.

**Работай строго по очереди:**
1. Закрытие Яндекса: lifecycle, очистка старого трека, правильное сообщение.
2. VPN: не переключать аудио, если текущая CELIKOM-версия продолжает играть; восстановление сервера — в фоне; сохранить быстрый reconnect.
3. Исправить только подтверждённые тексты, цвета и статусы.
4. Когда придут диагностические файлы — сверить их только с этими задачами.
5. Точечные тесты и оба CI.
6. После завершения всего — собрать и передать **одну новую версию Windows**.

Не делай промежуточных сборок. Не смешивай задачи и не уходи в дебри. Не трогай Android, расширение, сервер, архитектуру, уже завершённый updater/P-256, autostart/tray и старые Issues. Не публикуй старый Draft 0.24.38 и production feed. Перед существенными изменениями — точный backup. Не ослабляй проверки текущего плеера и декодера.

Продолжай крупными блоками без остановок ради коротких отчётов. Остановись только если нужна моя реальная проверка/помощь или когда одна новая итоговая версия будет готова. Не объявляй исправления завершёнными без тестов и подтверждения.

---


## 7. W157 implementation progress — 15 November 2026

### Current checkpoint and backups

- Current application-source HEAD: `67fd6a7386715a15dee83447c0c497084deb7034`.
- Exact backup before this documentation update: `backup/windows-main-pre-w157-docs-update-20261115` @ `67fd6a7386715a15dee83447c0c497084deb7034`.
- Backup before the retired-host VPN fence change: `backup/windows-main-pre-w157-retired-host-preserve-20261115` @ `40d653f1259f2561015af770a0b5aae9f5a92f66`.
- Work remains on `main`; no other product or platform was changed.

### Implemented

1. **Yandex lifecycle:** added a process lifecycle tracker and a one-second companion check; the native host reports destruction of the selected renderer with an immediate sequenced `UNAVAILABLE` heartbeat. The bridge clears song/title/artist/duration, source and playback lease, and retires the exited host instance. A genuinely new Yandex host can publish a fresh current player.
2. **VPN audio continuity:** same-origin transient network suspension retains signed expected-audio and exact decoder evidence. If the exact current signed CELIKOM decoder remains playing, the resumed renderer keeps that source instead of triggering a redundant current-track source refresh. The existing quick route recheck was not slowed or redesigned.
3. **Retired-host race:** a transient VPN disable no longer clears the retired native-host ID fence. A late heartbeat from a process already declared exited remains rejected after the bridge is re-enabled; a new Yandex process ID is accepted.
4. **UI priority:** when the player is actually unavailable, `Подключитесь к Яндекс Музыке` now outranks the simultaneous network-recovery text in track/action surfaces. Server recovery remains a separate status. Unavailable/unknown source presentation remains neutral and does not become green.

### Verification

- Main CI run `43753821690`: **SUCCESS** on `67fd6a7386715a15dee83447c0c497084deb7034`.
- Windows integration CI run `43753821682`: **SUCCESS** on the same commit.
- W23 native-host tests: `142/142`, no failures.
- W22/W23/W60 original-source/VPN/403/audio suite: `360/360`, no failures.
- W15 native contract: `W15_NATIVE_CONTRACT_PASS 411`.
- W21 recovery contract: `41`; W24 builder: `20`.
- GUI compilation with warnings as errors: **SUCCESS**.
- Targeted W157 regressions cover selected-renderer destruction, signed decoder retention across a kUrl refresh, player-unavailable UI during VPN suspension, and rejection of a retired Yandex host after VPN recovery.

### Still outstanding

- The owner-promised diagnostic files have **not** been supplied or reviewed. Do not claim otherwise. When received, correlate only with the three W157 tasks.
- Owner-PC verification of prompt Yandex closure and audible VPN continuity remains pending. CI does not establish that the audible pop is gone on the owner's machine.
- No new installer/package was built. The old unpublished 0.24.38 Draft predates W157 and must not be published or delivered as the fix.
- After diagnostics correlation and any necessary targeted correction, run both CI workflows on the final source and prepare exactly one consolidated Windows package. No intermediate builds.

