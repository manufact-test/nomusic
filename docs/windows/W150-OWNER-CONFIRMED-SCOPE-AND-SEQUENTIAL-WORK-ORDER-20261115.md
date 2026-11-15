# W150 — CELIKOM Windows owner-confirmed scope and strict sequential work order

Date: 15 November 2026  
Repository: `manufact-test/nomusic`  
Product: the one existing CELIKOM Windows application  
Only working branch: `main`

## 0. Authority — read this first

This is the owner's latest explicit correction and work-order approval. It supersedes conflicting priority lists in older handoffs, including W139's earlier "automatic updater first" ordering and the commercial Authenticode/PFX requirements in W148.

W119 still controls the product architecture and working rules (one product, `main` only, exact backups, no Windows TEST product, no experimental development branches, no intermediate installers). W150 controls the current task scope and order.

**The developer must finish one task to code/test/CI-ready state before moving to the next. Do not hop between tasks, reopen unrelated old tickets, or invent extra work from the repository's historical OPEN Issues.** The owner should receive one consolidated build only after all agreed code work is complete.

## 1. Exact repository baseline and backup

- Current `main` HEAD when W150 was authored: `0524158177beeedb50bff85d59ae573d90c19823`.
- Exact pre-W150 documentation backup: `backup/windows-main-pre-w150-owner-scope-handoff-20261115` @ `0524158177beeedb50bff85d59ae573d90c19823`.
- Owner's installed/last reviewed version remains CELIKOM Windows `0.24.37` (W138). No newer consolidated owner package has been delivered.
- Latest Windows runtime source before W148 release-pipeline scaffolding: W147 code HEAD `e174551dc086f8812f05840aa8e22d926889ad31`.
- Latest `main` CI at W150 baseline: Main CI run `43699852155` SUCCESS; Windows integration CI run `43699852121` SUCCESS. These are code/test results only, not owner-PC or audible acceptance.
- No new EXE/ZIP was built or delivered as part of W150 documentation correction.

## 2. Owner-confirmed task scope and order

### Task 1 — current Yandex player / CELIKOM UI synchronization and truthful source state

**This is the first active implementation task.** The owner observed these exact failures on 0.24.37:

- CELIKOM was closed and reopened while Yandex continued playing; the music played, but CELIKOM stayed at `Ожидаем` / `Идёт загрузка Яндекс.Музыки`.
- The alternate `Ты` (13 карат) played audibly, but CELIKOM showed stale `Зима` / CENTR and the false `Версия CELIKOM передана Яндексу` message.
- In Yandex `Моя волна`, a different song (owner identified the playing song as `Вечно молодой`) played while CELIKOM retained the previous track and transfer wording.
- After VPN reconnection, music played but CELIKOM said `Запустите трек в Яндекс Музыке` and failed to show the current song.

Required behavior:

- Reconcile the existing Yandex process/player on CELIKOM start/reopen and after reconnect; do not show startup instructions if Yandex is already playing.
- Current metadata must belong to the exact current player/queue/track identity, never a previous track, preload, previous session or late heartbeat.
- Distinguish playback state `PLAYING / PAUSED / STOPPED / UNAVAILABLE` from source `ORIGINAL / ACTIVE_REPLACEMENT / UNKNOWN`.
- `ACTIVE_REPLACEMENT` requires the existing exact-current-track + signed-current-decoder evidence. Mapping acceptance, URL transfer, HTTP 206, stale heartbeat or cache alone are not proof.
- Show `ORIGINAL` only when the current original source is actually identified. If not provable, show neutral `UNKNOWN`; do not guess.
- Immediately invalidate stale source/title/green/transfer wording on track change, stop, pause, player destruction, CDP detach, current-player switch or loss of current decoder proof.
- Never show `Версия CELIKOM передана Яндексу` as a claim of audible replacement unless the exact current decoder evidence proves it.
- Fix state reconciliation and event ordering, not a cosmetic timer or hardcoded text. Preserve the W127/W133/W134/W135/W141–W147 exact-evidence safeguards; do not weaken proof to make the UI greener.

Existing W141–W147 work already advanced this area, including current-player selection, queue/decoder reconciliation, explicit playback states, sequenced heartbeat renewal, stale-process retirement, audibility precedence and compact paused-state handling. **Do not restart from scratch.** Audit the current `main` implementation, close only genuine remaining gaps, add targeted regressions, run both CI workflows and prepare this task for the single owner acceptance build. Do not mark it owner-accepted until the owner checks the final build.

Tracking: Issue #52 is related to source-truth acceptance and stays OPEN until the owner's actual playback/source checks pass.

### Task 2 — VPN A→B audio artifact, while preserving the faster reconnect

Only the current owner-reported VPN issue is in scope:

- VPN A→B reconnect is now noticeably faster. **Preserve this improvement; do not regress to the old slow reconnect.**
- During the switch, owner hears a loud `пшик` / click / strange audio sound.
- Owner previously heard good/clean sound from the alternate `Ты` and the track he called `две гутыки`; do not rename that uncertain title.
- Crossfade sounded clean in ordinary listening without VPN; it still needs a VPN/recovery check.

Required engineering and regression coverage:

1. Trace the actual VPN route/reconnect/audio handoff and identify the cause of the audible transient before changing it.
2. Keep the existing faster A→B reconnection.
3. Cover separately: an active CELIKOM replacement during VPN A→B; an ORIGINAL track during VPN A→B; Yandex `Моя волна` during VPN A→B.
4. Check Next/crossfade after route recovery.
5. Avoid reloading/replacing an ORIGINAL stream when no CELIKOM replacement is active.
6. Do not modify original audio assets or unrelated audio-processing behavior.

Do not automatically expand this task into the old standalone #57 (403→206 signed-media recovery) or every historical #58 acceptance criterion. If code evidence proves a shared root cause, record the overlap and fix only what is necessary for the owner-described VPN A→B issue. Do not claim audible success from CI.

### Task 3 — Windows autostart and tray behavior

Existing code review already found:

- First launch calls `EnsureFirstLaunchDefault` and enables Windows startup by default.
- A deliberate user opt-out is persisted and must remain OFF.
- The app uses same-user startup (`HKCU Run`, `--background`); it must not demand administrator privileges or start Yandex/unauthorized playback automatically.

Work required:

- Verify the current implementation and add/fix code only if a real defect is found.
- Test first-install default ON, deliberate OFF persistence after restart and in-place upgrade, registry/menu agreement, X/tray behavior, and quiet background startup.
- Do not blindly reset an existing OFF choice to ON.
- Owner's actual machine state is not known until final consolidated acceptance.

### Task 4 — one consolidated regression pass and one owner package

After Tasks 1–3 are individually code/test/CI-ready:

- Review startup/reopen, existing Yandex reconciliation, current track/source transitions, stop/pause, VPN reconnect, tray/autostart and diagnostics after disconnect.
- Re-run the relevant Windows integration tests and both CI workflows on the final source.
- Preserve the existing Yandex vendor-update detection cadence of 15 minutes; do not accidentally change it.
- Build exactly one coherent owner EXE+ZIP from `main`, with matching GUI/Supervisor/installer versions and hashes. No intermediate installers or Windows TEST product.
- Deliver the package and one concise grouped owner test plan. Owner performs the consolidated local listening/GUI check; collect only the resulting actual defects and then fix those.

### Task 5 — automatic updater, P-256 trust and production feed (LAST)

The owner explicitly changed the order: complete the application fixes first; do the updater/key/release work only after Tasks 1–4 are ready.

Approved design:

- No commercial Authenticode certificate purchase.
- No company/legal-entity identity attached to CELIKOM for this purpose.
- Keep the existing Windows installation warning experience: if Windows shows the current unknown-app warning, the user can choose `More info → Run anyway`. Do not make this worse, do not suppress Windows security, do not ask users to disable Defender/SmartScreen/Smart App Control, and do not implement a security bypass.
- Use CELIKOM's own P-256 signed schema-2 update manifest. Embed only the public key in the client. Keep the private key outside the repository and out of chat/logs; store it in protected GitHub Actions secret/HSM for release signing.
- Verify exact product/version/sequence, signed manifest, package SHA-256 and size, and all expected payload identities before staging/install. Authenticode is **not** a required CELIKOM updater trust pin in this approved design.
- Preserve the existing safe-point download/install behavior, independent Supervisor READY handshake, DPAPI transaction, account/session/settings/native integration and one-shot automatic rollback.
- Installed 0.24.37 has no production P-256 pin. Therefore a one-time trusted manual bootstrap is unavoidable: owner installs the first coherent package containing the new public pin. After that, subsequent releases must be detected, downloaded, verified, staged and installed automatically without manual website downloads.
- Domain `celikom.com` is already purchased and is the fixed future production origin: `https://celikom.com`. DNS, TLS and public feed deployment are intentionally deferred until the product/infrastructure migration is complete. Prepare the code/config now, but do not attempt to publish to a non-existent HTTPS endpoint or change DNS early.
- W148's current workflow still contains PFX/Authenticode certificate/fingerprint gates. That scaffold is **not the final approved design** and must be refactored in this last task. Do not run it or ask the owner to buy a certificate.
- Prepare one safe local key-provisioning script/command for the owner to run once only if required by GitHub's protected-secret permissions. Generate the private key on a trusted owner-controlled machine; use authenticated GitHub CLI to upload the secret without displaying the PEM. The assistant must never ask the owner to paste the private key into chat.
- Test the updater end-to-end on the owner's PC after the bootstrap: detect → download during playback → verify → wait for safe point → Supervisor READY → in-place install → health check → forced one-shot rollback test. Preserve account, DPAPI, settings, native integration and music continuity.
- Windows may still apply its own policy to unsigned executables. Keep the current warning experience; never promise that P-256 manifest trust creates a Windows-verified publisher or bypasses SmartScreen/SAC. If a particular Windows policy blocks execution, report it honestly; never ask users to turn protection off.

Production updater is not currently operational. W148 scripts/workflow are only scaffolding; no production P-256 secret/pin, HTTPS feed or owner bootstrap has been completed.

## 3. Explicitly excluded from this work order

Do **not** start, investigate, patch, or pull these in just because their old GitHub Issues remain OPEN:

- #53 — historical Brave/Windows freezes, resource usage and external elevation prompt.
- #54 — historical Big City Life mid-track volume drop.
- #56 — historical global gain_db/headroom/clip/seek/Next matrix.
- #57 — historical 403→206 signed-media recovery hiss.
- #58 — historical original/My Wave VPN interruption issue as a separate broad ticket. Task 2 is limited to the current VPN A→B audio transient described by the owner in W139.
- Any other old issue, audio feature, performance investigation or unrelated cleanup not explicitly included above.

These Issues must not be silently closed or deleted; they simply are not current authorized work. If a future owner test raises one of them again, obtain explicit scope before starting it.

## 4. Work protocol and reporting

- Work only on `main`; create an exact `backup/*` snapshot before each substantial code block.
- Keep one existing CELIKOM Windows product. No Windows TEST product, no experiment/development branch, no architecture rewrite, no unrelated Android/extension/server changes.
- Complete the current task end-to-end (implementation + targeted tests + CI) before starting the next task.
- Do not pause for tiny reports or ask the owner to test each intermediate patch. Do not build intermediate installers.
- Keep concise progress updates: task, actual code/test status, remaining blocker. Never claim done based only on CI.
- One final owner package after Tasks 1–4; the updater/key/feed is the last engineering block.
- The owner should not have to repeat the requirements in this document.

## 5. First message for the next chat

Copy the following as the first user message in the next chat:

---

Привет! Ты принимаешь **CELIKOM Windows** как ведущий разработчик. Продолжай существующую работу строго по актуальной документации. Ничего не начинай с нуля и не меняй архитектуру.

**Репозиторий:** `manufact-test/nomusic`  
**Единственная рабочая ветка:** `main`  
**Текущий HEAD на момент передачи:** `0524158177beeedb50bff85d59ae573d90c19823`  
**Точный резерв перед W150:** `backup/windows-main-pre-w150-owner-scope-handoff-20261115`

### Сначала обязательно прочитай
1. `docs/windows/W119-AUTHORITATIVE-OWNER-CONTRACT-AND-WINDOWS-HANDOFF-20261114.md`
2. `docs/windows/W150-OWNER-CONFIRMED-SCOPE-AND-SEQUENTIAL-WORK-ORDER-20261115.md` — главный актуальный список задач и очередность.
3. `docs/windows/NEXT-CHAT.md`
4. `docs/windows/W139-OWNER-ACCEPTANCE-FEEDBACK-AND-AUTOUPDATE-P0-20261115.md`
5. `docs/windows/W148-PROTECTED-SIGNED-STABLE-RELEASE-PIPELINE-20261115.md` — только чтобы понять имеющийся scaffold и что в нём теперь устарело.

### Правильный порядок — строго без перескоков
1. Довести синхронизацию интерфейса с фактическим текущим плеером/источником (ORIGINAL / ACTIVE_REPLACEMENT / UNKNOWN и PLAYING / PAUSED / STOPPED). Сохранить W141–W147, исправлять только реальные оставшиеся пробелы.
2. Устранить громкий «пшик»/щелчок при VPN A→B, сохранив быстрое переподключение. Отдельно проверить replacement, original, «Мою волну» и crossfade после восстановления.
3. Проверить автозапуск и трей: ON по умолчанию, сохранение намеренного OFF, без автозапуска Яндекса и без повышения прав.
4. Сделать одну общую регрессионную проверку и собрать один итоговый EXE+ZIP для владельца.
5. Только затем завершить автообновление на собственном P-256 signed manifest + SHA-256. Никакого коммерческого Authenticode, PFX, привязки CELIKOM к компании или просьб отключать защиту Windows. Домен уже куплен: `https://celikom.com`; DNS/TLS включим после полной миграции. Нужен один ручной bootstrap поверх 0.24.37, затем все обновления автоматические.

**Не брать в работу:** #53, #54, #56, #57, #58 и другие старые Issues как самостоятельные задачи — владелец их сейчас не поручал. #52 относится к текущей проверке правдивости источника и остаётся открытой до реальной приёмки.

### Важные правила
- Перед каждым существенным изменением делай точный backup.
- Работай большими законченными блоками.
- Не делай промежуточных установщиков.
- Не проси владельца проверять каждую мелочь.
- Не объявляй задачу готовой по одному CI.
- Закрывай текущую задачу по коду, тестам и CI до перехода к следующей.
- В конце подготовь одну сборку и один сгруппированный план ручной проверки.
- Не проси владельца повторять требования из W150.

Начни с проверки актуального HEAD, CI и оставшихся пробелов в **Задаче 1**. Пока не закончил Задачу 1 — не переключайся на VPN, автозапуск или updater.

---

