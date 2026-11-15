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
- The owner has performed additional live tests and reported the observations below.
- W54 diagnostics were supplied and are available in ChatGPT Library: `Вставленный текст(20261115-181400).txt`, `Вставленный текст(20261115-181616).txt`, plus a duplicate second capture `Вставленный текст(20261115-181902).txt`.
- The diagnostic package identifies app `0.24.38.0`, native module `0.24.29`, and unknown Yandex version. See [W54 analysis](W54-OWNER-DIAGNOSTIC-ANALYSIS-20261115.md).
- At the initial documentation-only W157 checkpoint, no application code was changed and no new build was produced. Subsequent W157 implementation is recorded in §7; W54 analysis is recorded in §8.

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

- W54 diagnostics have already been received and reviewed from ChatGPT Library; do not ask the owner to resend them.
- The first capture was generated at 18:13:51 UTC; the second VPN capture at 18:16:12 UTC; the 18:19:02 file is a duplicate of the second.
- The second capture shows source held during VPN suspension, followed by current-source revalidation and replacement-source reload after entitlement recovery. Exact event sequence and limitations are recorded in [W54 analysis](W54-OWNER-DIAGNOSTIC-ANALYSIS-20261115.md).
- W54 does not prove audible playback or the audible pop: its summary explicitly says replacement-audible proof is unavailable and no PLAYER_AUDIO_AUDIBLE event was observed.
- The W54 logs do not include a separate Yandex-process-close test. Keep owner-PC verification for that case pending.
- Use these diagnostics to close the exact no-`kUrl` VPN gap; do not broaden the investigation.

## 3. Strict execution order

Complete each item to implementation + targeted tests + CI-ready state before moving to the next. Do not mix tasks or start unrelated work.

1. **Yandex close/lifecycle state:** implementation and focused CI tests are complete. Owner-PC timing/behavior check remains pending.
2. **VPN audio continuity — partially implemented:** exact-`kUrl` preservation remains intact. A new no-`kUrl` path captures the prior mapped current-track identity during same-origin transient recovery; renderer suppresses revalidation/reload only if the actual current track ID still matches and the adapter still reports it mapped. This is not source proof and must not produce a green/verified status. The host regression for Yandex hiding `kUrl` passes. Remaining: explicit no-`kUrl` tests for Next/track change, manual Stop/player loss, logout, denial, API-origin change, unavailable/invalid state, recovery timeout and bounded recovery after actual source loss.
3. **UI consistency:** the confirmed closed-player/VPN status priority is corrected. Other reported text/color issues need concrete examples; no redesign.
4. **Diagnostics correlation:** W54 has been received and reviewed. Follow [W54 analysis](W54-OWNER-DIAGNOSTIC-ANALYSIS-20261115.md); no additional diagnostic upload is currently required.
5. **Verification:** the first no-`kUrl` host regression is now present and passes. Main CI `43756267555` and Windows integration CI `43756267579` both pass on `23538cab793be9d1381790d4c304db3cd4d4b417`; W23 native-host is `143/143`, W22/W23/W60 is `360/360`. Still add no-`kUrl` fail-closed/track-change regressions, then rerun both CI workflows. CI does not replace the owner's audible/manual acceptance.
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
- A same-origin VPN/network interruption does not cause an audio-source switch for an unchanged already-mapped current track on both Yandex builds that expose CDP `kUrl` and builds that do not. Source truth remains UNKNOWN unless exact decoder proof exists.
- If actual audio loss occurs, recovery is based on verified current-player/current-decoder state and does not create redundant handoffs.
- UI texts and colors match the real connection, player, playback and source states.
- Relevant diagnostics, when supplied, are checked and findings recorded without expanding scope.
- Focused tests and both required CI workflows pass.
- Exactly one new consolidated Windows build is delivered after all fixes; no intermediate packages are sent.

## 6. First message for the next chat

The initial W157 intake prompt below is historical and predates the implementation in §7. For any new chat, copy the authoritative current first message from `docs/windows/NEXT-CHAT.md`. It contains the live source checkpoint, exact backups, CI evidence, pending diagnostics and remaining work. Do not reuse the old intake prompt as the current handoff.

### Original W157 intake prompt (historical only)

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

- Current application-source HEAD: `23538cab793be9d1381790d4c304db3cd4d4b417`.
- Exact backup of current CI-green code: `backup/windows-main-post-w54-no-kurl-ci-green-20261115` @ `23538cab793be9d1381790d4c304db3cd4d4b417`.
- Exact backup before the no-`kUrl` code change: `backup/windows-main-pre-w54-no-kurl-fix-20261115` @ `6b1f6bf15dcf8fca6039b394ade2d6fd2de60224`.
- Backup before the retired-host VPN fence change: `backup/windows-main-pre-w157-retired-host-preserve-20261115` @ `40d653f1259f2561015af770a0b5aae9f5a92f66`.
- Work remains on `main`; no other product or platform was changed.

### Implemented

1. **Yandex lifecycle:** added a process lifecycle tracker and a one-second companion check; the native host reports destruction of the selected renderer with an immediate sequenced `UNAVAILABLE` heartbeat. The bridge clears song/title/artist/duration, source and playback lease, and retires the exited host instance. A genuinely new Yandex host can publish a fresh current player.
2. **VPN audio continuity:** exact signed decoder evidence is retained when CDP `kUrl` exists. For W54's no-`kUrl` Yandex build, host now retains only the previously mapped current-track identity across same-origin transient recovery; renderer suppresses source revalidation/reload only if the current ID still matches and the adapter still reports it mapped. This is a continuity hint, not decoder/source proof. The existing quick route recheck was not slowed or redesigned. No-`kUrl` fail-closed coverage remains outstanding.
3. **Retired-host race:** a transient VPN disable no longer clears the retired native-host ID fence. A late heartbeat from a process already declared exited remains rejected after the bridge is re-enabled; a new Yandex process ID is accepted.
4. **UI priority:** when the player is actually unavailable, `Подключитесь к Яндекс Музыке` now outranks the simultaneous network-recovery text in track/action surfaces. Server recovery remains a separate status. Unavailable/unknown source presentation remains neutral and does not become green.

### Verification

- Main CI run `43756267555`: **SUCCESS** on `23538cab793be9d1381790d4c304db3cd4d4b417`.
- Windows integration CI run `43756267579`: **SUCCESS** on the same commit.
- W23 native-host tests: `143/143`, no failures.
- W22/W23/W60 original-source/VPN/403/audio suite: `360/360`, no failures.
- W15 native contract: `W15_NATIVE_CONTRACT_PASS 411`.
- W21 recovery contract: `41`; W24 builder: `20`.
- GUI compilation with warnings as errors: **SUCCESS**.
- Targeted W157 regressions cover selected-renderer destruction, signed decoder retention across a kUrl refresh, player-unavailable UI during VPN suspension, rejection of a retired Yandex host after VPN recovery, and a host-side same-origin VPN hold when Yandex does not expose CDP `kUrl`.
- The no-`kUrl` host test passes, but the fail-closed matrix for track change, manual Stop/player loss, logout, denial, origin change, invalid state/timeout and actual-source-loss recovery still needs explicit targeted coverage.

### Still outstanding

- W54 owner diagnostics have been received and reviewed; see §8 and `W54-OWNER-DIAGNOSTIC-ANALYSIS-20261115.md`. No resend is needed.
- The no-`kUrl` continuity path is partially implemented: host captures the previously mapped current-track ID during same-origin transient recovery, and renderer only holds if the actual current ID still matches and the adapter still reports it mapped. The new host regression passes. No-`kUrl` fail-closed tests for track change, manual Stop/player loss, logout/denial/origin change, invalid state/timeout and actual-source-loss recovery remain.
- Owner-PC verification of prompt Yandex closure and audible VPN continuity remains pending. W54 does not prove audible output; CI cannot prove that the audible pop is gone.
- No new installer/package was built. The old unpublished 0.24.38 Draft predates W157 and must not be published or delivered as the fix.
- Current code checkpoint `23538cab793be9d1381790d4c304db3cd4d4b417`; exact checkpoint backup: `backup/windows-main-post-w54-no-kurl-ci-green-20261115`. Main CI `43756267555` and Windows integration CI `43756267579`: SUCCESS. W23 `143/143`; W22/W23/W60 `360/360`.
- After the remaining no-`kUrl` fail-closed tests/corrections, rerun both CI workflows on the final source and prepare exactly one consolidated Windows package. No intermediate builds.


## 8. W54 diagnostic findings and remaining VPN gap

See the standalone [W54 diagnostic analysis](W54-OWNER-DIAGNOSTIC-ANALYSIS-20261115.md). The key correction is that the logs are present in ChatGPT Library and were missed by the previous handoff; they are not missing from the owner's submission.

- W54 second capture: network suspension at 18:15:14.643, source held at 18:15:15.250, entitlement recovered at 18:15:19.745, then `NATIVE_CURRENT_SOURCE_REVALIDATE` at 18:15:20.848 and `NATIVE_REPLACEMENT_SOURCE_RELOAD` at 18:15:20.850 for the same current track.
- A second cycle: suspension at 18:15:30.634, source held at 18:15:31.029, recovery at 18:15:42.781, revalidation at 18:15:43.103, replacement reload at 18:15:43.105 and reload success at 18:15:44.028.
- The diagnostic reports `NativeDecoderUrlPropertyObserved=false`. Before the partial correction in commit `23538cab793be9d1381790d4c304db3cd4d4b417`, host preservation required `currentDecoderPlayer`, which in turn required a matching signed `kUrl` plus `kIsPlaying`; therefore the original W157 code could not set `preserveCurrentSource` in this real configuration. The new no-`kUrl` host regression was added in the later commit; the remaining fail-closed matrix is still outstanding.
- Implemented partially on `23538cab793be9d1381790d4c304db3cd4d4b417`: host stores a short-lived same-origin recovery hold containing only the previous mapped current-track ID; renderer independently checks that the actual current ID still matches and `adapter.hasMappedTrack(currentTrackId)` remains true before suppressing revalidation/reload. The hold is not source proof and must not make the UI green.
- Remaining: add no-`kUrl`-specific regression coverage for Next/current-track change, manual Stop and player destruction, logout, denial, API-origin change, invalid/unavailable state, recovery timeout, and bounded recovery after actual source loss. Then rerun both CI workflows.
- Audible limitation: W54 says `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING` and `PlayerAudibleEventObserved=false`. This confirms the internal revalidation/reload sequence, not the actual sound waveform or pop.

