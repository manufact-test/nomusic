## W99 update — 2026-11-13 (current integrated QA state)

Current lead status and the exact remaining owner action are documented in [W99-0.24.36-INTEGRATED-QA-STATUS-20261113.md](W99-0.24.36-INTEGRATED-QA-STATUS-20261113.md). Current branch `experiment/windows-w98-integrated-gain-and-original-vpn-20261113`, HEAD `b1f9064edfc33b83e08abe22e7d38a0a87298e59`; exact rollback `backup/windows-w99-0.24.36-green-hostinger-blocked-20261113`. GUI 0.24.36 / native 0.24.29 / W23 0.24.10. Full Windows CI [43470332842](https://github.com/manufact-test/nomusic/actions/runs/43470332842) SUCCESS; W91 sidecar CI [43469841569](https://github.com/manufact-test/nomusic/actions/runs/43469841569) SUCCESS. Hostinger verify/package passed, but deploy safely stopped before writes because repository Actions secret `CELIKOM_W98_TEST_EMAIL` is empty. Add that secret using the owner's primary CELIKOM account email (do not send it in chat), then advance the request JSON and rerun the guarded deployment. No final installer has been published yet.

# W97 — FINAL INTEGRATED WINDOWS TEST BUILD / OWNER HANDOFF (2026-11-13)

## W98 historical update — 2026-11-13 (superseded by W99)

The work continued on a separate branch from the exact W95 input, without changing W95 or the browser extension:

- Current W98 branch: `experiment/windows-w98-integrated-gain-and-original-vpn-20261113`.
- Exact W98 pre-change backup: `backup/windows-w98-pre-integrated-gain-and-original-vpn-20261113` @ `5ce1ec127009ba4a86a8e5ee1d129ec86623fd54`.
- Prepared candidate: GUI 0.24.35 / native 0.24.28.
- Latest full W98 CI [43462340493](https://github.com/manufact-test/nomusic/actions/runs/43462340493) SUCCESS on code SHA `696e36b65c2a5accaa0e5c6c8aeb7548611932f1`; Hostinger workflow YAML, owner-email session scoping, Linux package build, W22/W23/W60, W21, W24, W15 and GUI compile all passed.
- Issue #58 now has explicit original/unknown/actual-replacement classification and no reload for a confirmed original during VPN/entitlement transitions. W22/W23 regression tests pass; owner acoustic QA is still required.
- W98 has prepared private offline gain rendering, source/version/gain-bound sidecar registration, signed Range verification, and an explicit rollback CLI. Live verification is scoped to the owner's explicitly authorized account email via Actions secret `CELIKOM_W98_TEST_EMAIL`; it never scans other users' sessions. **Migration 020 and real sidecars have not been activated.**
- Hostinger attempt [43454991506](https://github.com/manufact-test/nomusic/actions/runs/43454991506) stopped before deployment because its branch revision was stale. No deploy or media writes occurred.
- Owner has explicitly authorized using his primary CELIKOM account by email. Live verification now resolves only that email and only its active session; no numeric user ID is needed and no other customer's session is scanned. The owner must add the one-time Actions secret `CELIKOM_W98_TEST_EMAIL` before any deployment/migration; the workflow preflight blocks if absent. Full detail: `docs/windows/W98-INTEGRATED-QA-AND-LIVE-GAIN-HANDOFF-20261113.md`.


## 0. Задача следующего ведущего

Владелец попросил не присылать очередной частичный установщик. Следующий ведущий должен **закончить интеграцию всех Windows-исправлений и выдать одну полноценную CELIKOM Windows TEST-сборку**, в которой уже подключены и серверное усиление из админки, и все согласованные исправления воспроизведения/VPN. Только после этого владелец будет проводить общий реальный тест на ПК.

**Не просить владельца тестировать усиление на 0.24.34:** эта сборка не получает реально зарегистрированные Windows gain sidecar-файлы с production Hostinger. Это был QA-кандидат, а не готовая сборка для полного теста. Не называть её финальной и не выдавать повторно как завершённую.

Ожидаемый результат — единый, воспроизводимый, откатываемый TEST-релиз (версия выше 0.24.34, номер выбрать по фактической сборке), а не production-stable без пользовательского теста. В комплекте EXE + ZIP, точный SHA256, зелёный полный Windows CI, проверка серверной выдачи и сохранённые резервные точки. Владелец тестирует всё одним проходом.

## 1. Репозиторий и точные исходные точки

- GitHub: `manufact-test/nomusic`.
- Рабочая ветка-кандидат: `experiment/windows-w95-02434-qa-candidate-20261113`.
- Код текущего 0.24.34 candidate: `4f8b3a72687577c5447d157be156365ab42a86fa`.
- HEAD ветки до добавления этого handoff-документа: `1d25a7d2af65b4b9901a8c2fe1769b88d80ac15e` (W95 code + docs). После документационных коммитов прочитать фактический HEAD ветки; не checkout-ить старый SHA вслепую.
- Полный backup до W95: `backup/windows-w95-pre-02434-qa-candidate-20261113` @ `80113ff54e0479c0412e51263cd81078b39082e1`.
- Backup перед W96 403 guard: `backup/windows-w95-02434-pre-w96-403-guard-20261113` @ `cc35d1fff1e6b60dd98eb1de6ce2b4ab61f67ecb`.
- Точный W89 / GUI 0.24.33 / native 0.24.26 backup: `backup/windows-w89-02433-ci-green-owner-handoff-before-volume-20261113` @ `6916c0229861aaa6f2486224f3e62092b343698e`.
- Предыдущий W88 / 0.24.32 rollback: `backup/windows-w89-before-vpn-recovery-audio-proof-20261113` @ `3ebded59b4bf596d54b1b5b29edfe16683ad45a0`.
- W95 full QA handoff: `docs/windows/W95-02434-OWNER-QA-DELIVERY-20261113.md`.
- Старый подробный W89 evidence/STOP-WORK: `docs/windows/W89-02433-VPN-RECOVERY-AND-FALSE-GREEN-TRACK-20261113.md`.
- Main next-chat pointer: `docs/windows/NEXT-CHAT.md`.

Перед любым изменением: fetch актуальный HEAD, проверить дерево и все резервные refs. Создать отдельную рабочую ветку от текущего W95 candidate и новый точный backup. Не коммитить поверх backup refs, не переписывать W88/W89.

## 2. Что реально собрано и почему 0.24.34 НЕ является общим тестовым релизом

- GUI **0.24.34**, native **0.24.27**.
- Полный Windows CI SUCCESS: [43442749658](https://github.com/manufact-test/nomusic/actions/runs/43442749658), artifact ID `14045829754`.
- EXE: `CELIKOM-Windows-0.24.34-AUDIO-VPN-QA-TEST.exe`, 43,551,775 bytes, SHA256 `83CF52CE7808CF03E33FBE461FDFE73C40080545642B29B5F9ED81015DEB1FFE`.
- ZIP SHA256 `6263CCB6CD6294CF33C17808E4BD1B3EA406F4C49A5955841A35E7B70CBD01D9`.
- Both files already in Library: `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.34-AUDIO-VPN-QA-TEST.exe` and matching `.zip`.
- Installer verified from artifact (ZIP CRC, EXE extracted SHA) and in-place W89 DPAPI/session preservation CI passed. No installation on owner's PC; no real playback/VPN test.
- W94 VPN last-route-event handling, W89 false-green/source proof and bounded refresh, W92 passive diagnostics, W96 pending-403-reload guard are included. These are CI-verified, **not owner field-verified**.
- Critical missing production integration: server migration `020_windows_gain_variants.sql` and actual private pre-rendered Windows gain assets are not deployed/registered. The production Yandex/browser original path remains unchanged. Therefore 0.24.34 alone cannot test actual admin gain. Do not tell owner to use it to validate boost.

## 3. Must-finish blocker: actual admin gain on every active Windows replacement with nonzero gain_db

Это не только Big City Life. Windows ранее получал исходные MP3 bytes, а `gain_db` из админки не применялся к Windows native playback. Chrome extension/admin preview используют Web Audio gain; Windows native path не применял это поле. Не менять Yandex boolean `downloadInfo.gain` на числовые dB и не крутить системную громкость.

Read first:
- `docs/windows/W90-ALL-ADMIN-GAIN-TRACKS-AUDIT-20261113.md`.
- `docs/windows/W93-PRIVATE-GAIN-STAGING-AND-ROLLBACK-20261113.md`.
- `server/src/Application/ResolveService.php`.
- `server/src/Application/WindowsGainVariant.php`.
- `server/src/Repositories/PdoCatalogRepository.php`.
- `server/src/Http/AudioController.php`.
- `server/src/Application/AudioTokenService.php`.
- `server/migrations/020_windows_gain_variants.sql`.
- `server/bin/windows-gain-stage.php`.
- `scripts/windows-gain-render.sh`.
- `windows-companion/w15/Celikom.Companion/CelikomApi.cs` and W15 grant validator/types.

Confirmed facts from read-only production audit [43438999212](https://github.com/manufact-test/nomusic/actions/runs/43438999212): 1493 active approved versions; active Big City Life / Триагрутрика Yandex track `40371622` has admin `gain_db=+11.5`; active count with nonzero gain is one; disabled «Папиросы» track `1944599` has +12.0; audit history had four edits across three versions and did not show mass reset. This does **not** mean every track was boosted or that admin settings disappeared. Re-run read-only inventory at execution time and discover every active replacement with gain_db != 0; don't hardcode only Big City Life.

Architecture already prepared in code:
- W15 client request includes `audio_profile=windows_gain_v1`.
- API resolves that profile only for a signed-in session; `ResolveService` selects a variant only when source/version/gain/hash/duration/private storage all match.
- Windows sidecar uses its own signed HMAC and Range path; browser extension continues using the original asset.
- W93 staging CLI is operations-only, dry-run by default; commit requires `--commit` plus `CELIKOM_W93_ENABLE_STAGE=YES_EXPLICIT_PRIVATE_STAGE`.
- Offline renderer `scripts/windows-gain-render.sh` uses ffmpeg + limiter; Hostinger production has no ffmpeg/ffprobe.
- Synthetic FFmpeg + disposable MariaDB tests passed [43440173979](https://github.com/manufact-test/nomusic/actions/runs/43440173979). This proves staging mechanics on synthetic audio, not Big City Life acoustic output or live Hostinger compatibility.

Required finish sequence:
1. Read-only production inventory for all active, approved, non-disabled replacement rows where gain_db != 0. Capture exact replacement ID, Yandex track ID, version, source SHA256, gain_db, duration, storage key metadata; never log credentials or signed URLs.
2. Implement a tightly scoped private transfer/render/stage operation using pinned SSH and ephemeral runner scratch. Hostinger must not transcode during HTTP requests. Do not commit private song bytes to GitHub, repository, ordinary workflow artifacts, or logs. Avoid public URLs and long-lived downloads.
3. Before each render verify source SHA/version/gain against the live approved DB row; render offline; verify MP3 decodes, duration within the existing 1500ms contract, size/hash, peak/clipping and expected measured gain/loudness. The limiter can constrain peaks, so don't claim +11.5 dB unless measured output supports it.
4. Transfer rendered MP3 only to private Hostinger staging; run W93 CLI dry-run first; inspect all exact metadata; commit only after source/version/gain still match and a restorable snapshot exists. Existing originals and audio_assets must remain byte-identical.
5. Apply additive migration 020 with an explicit rollback/snapshot plan, deploy compatible server code, stage all active nonzero-gain variants, and verify live HTTPS resolve + signed audio Range (206), correct `gain_applied=true`, correct variant identity/hash, and no fallback to raw original for a signed stale variant. If stale, re-resolve safely.
6. Check entitlement on every request/session as existing rules require. No cached/offline grant or auth bypass. Keep normal extension path and all original Yandex/browser files untouched.
7. Test Windows output at real levels (before/after LUFS/RMS/peak or equivalent, clipping/headroom, fade/end, seek/crossfade/Next/403/VPN); verify the gain is audible and consistent. Gain sidecar should be selected for every eligible active nonzero gain, not only Big City Life.
8. Only then build the new single Windows TEST installer that includes the matching W15 client. Add CI for production-shaped migration, multi-row sidecar resolution, signed Range, stale version/gain rejection, Chrome/original unchanged, no double gain, and in-place DPAPI-safe upgrade.

Do not mutate production blindly. Back up the database and exact affected assets/metadata before migration or variant registration; keep a tested rollback. If live host can't support the proposed migration safely, stop and report the concrete blocker rather than sending an installer that cannot exercise gain.

## 4. New issue #58: original track pop / dropout when switching VPN (NO replacement)

GitHub issue: https://github.com/manufact-test/nomusic/issues/58.

Owner reports that while «Моя волна» / ordinary original songs with **no active CELIKOM replacement** were playing, switching VPN made music disappear/interrupted it and emitted a distinct «пшик» like a track/source transition. This is separate from the 403 hiss #57 and Big City Life volume dip #54. Exact track ID and incident diagnostics are not yet available; root cause is unproven.

Expected: for an original track without active replacement, CELIKOM must be transparent to the current decoder. VPN/temporary entitlement errors may block future replacement attempts, but must not reload/recreate the current original track, change DownloadInfo/resource, call QUALITY_CHANGE, stop/restart the audio session, or run CELIKOM gain/crossfade. Keep server-confirmed entitlement for all actual replacements; don't bypass authorization or leave replacements enabled after deny.

Trace W15 network route and entitlement state → bridge SetEnabled / NATIVE_STATE → W23 host relay/state delivery → W22 resource adapter/DownloadInfo → Yandex decoder. Determine whether CELIKOM sends any player-affecting command on original tracks. Compare with Yandex without CELIKOM on same VPN if possible to separate Yandex/network buffering from CELIKOM. Add only allowlisted ORIGINAL / ACTIVE_REPLACEMENT / UNKNOWN and reload/state-reset evidence; never log signed URLs, tokens or audio. CI + owner PC check required.

## 5. All remaining owner-visible defects — keep separate

- **VPN 40–50 sec reconnect**: W94 preserves the last route event after rapid adapter notifications, cancels stale GET, then rechecks server entitlement. CI green, real VPN A→B timing not confirmed. No bypass.
- **#52 «Ты» / тринадцать карат, Yandex track 89285816**: mapping/green status previously lied while original played. W89 now requires matching current decoder `kUrl` + `kIsPlaying`, plus one bounded refresh. Must confirm owner hears actual CELIKOM version.
- **#53 Brave / Windows lag/freezes**: W92 passive `NATIVE_ELECTRON_EVENT_LOOP_STALL` and memory observer included; no proven cause. Capture real CPU/RAM/GPU/process data; no blind removal of CDP/403 recovery.
- **#54 Big City Life / Триагрутрика 40371622**: CELIKOM alternative suddenly drops to ~half perceived volume mid-track while still playing; admin preview and +11.5 dB setting remain. This is NOT the same as #56 missing gain parity. Need source/decoder/volume evidence at exact drop.
- **#56 all admin gain_db**: actual Windows per-track gain parity not deployed until Section 3 completed. Apply to every active nonzero gain, not all songs and not global Windows volume.
- **#57 hiss/pop on CELIKOM signed URL 403 → 206**: W96 suppresses only a pending redundant reload when exact current decoder is already confirmed; no owner test yet. Keep separate from #58 original track pop.
- **#58 original songs / My Wave VPN pop**: no replacement present; CELIKOM should not alter current original playback.

Do not close any issue from CI alone. A 403 sound artifact, original-track VPN pop, and mid-song gain drop are three different incident classes.

## 6. Final integrated installer — acceptance gate before sending owner

- Single coherent version >0.24.34; GUI/native version metadata correct; no partial parallel installer options.
- Full Windows CI SUCCESS, including all native/renderer/player tests and W15 contracts.
- Server gain migration/variants actually deployed and tested via public HTTPS signed Range; owner account/session entitlement works; no double gain.
- W94 VPN reconnect and #58 original no-replacement behavior covered by regression tests.
- #52 actual decoder source evidence, #54 sudden volume-drop path, #57 recovery pop guard and #53 diagnostics retained without regressions.
- Tests for pause/resume, seek, Next, queue, crossfade, autostart, manual Stop, logout, expired token/403, VPN switch, install-over-existing and rollback.
- In-place upgrade preserves DPAPI session and does not touch Yandex vendor files or extension/browser assets.
- Produce EXE + ZIP from the exact successful CI artifact, verify ZIP CRC and EXE SHA256, upload both to `/CELIKOM/Windows/Test/`, document exact paths/SHA/CI/artifact and rollback.
- Send the owner a concise test matrix only after all above are complete. Say explicitly which issues still require his actual ears/PC; don't label the candidate stable before that test.

## 7. Exact first message for the next chat

Copy the following as the first message to the next leading developer:

> Привет! Ты новый ведущий разработчик **CELIKOM Windows**. Продолжай существующую разработку в GitHub, ничего не начинай с нуля и не присылай мне очередной частичный установщик.
>
> **Репозиторий:** `manufact-test/nomusic`
> **Текущая ветка-кандидат:** `experiment/windows-w95-02434-qa-candidate-20261113`
> **Кодовая точка 0.24.34:** `4f8b3a72687577c5447d157be156365ab42a86fa`
> **Точный резерв до W95:** `backup/windows-w95-pre-02434-qa-candidate-20261113` @ `80113ff54e0479c0412e51263cd81078b39082e1`
> **Резерв перед W96:** `backup/windows-w95-02434-pre-w96-403-guard-20261113` @ `cc35d1fff1e6b60dd98eb1de6ce2b4ab61f67ecb`
> **W89 0.24.33 rollback:** `backup/windows-w89-02433-ci-green-owner-handoff-before-volume-20261113` @ `6916c0229861aaa6f2486224f3e62092b343698e`
>
> Сначала прочитай:
> 1. `docs/windows/W97-FINAL-READY-RELEASE-HANDOFF-20261113.md` — главный план и это сообщение.
> 2. `docs/windows/NEXT-CHAT.md`.
> 3. `docs/windows/W95-02434-OWNER-QA-DELIVERY-20261113.md`.
> 4. `docs/windows/W89-02433-VPN-RECOVERY-AND-FALSE-GREEN-TRACK-20261113.md`, включая STOP-WORK addendum.
> 5. `docs/windows/W90-ALL-ADMIN-GAIN-TRACKS-AUDIT-20261113.md` и `docs/windows/W93-PRIVATE-GAIN-STAGING-AND-ROLLBACK-20261113.md`.
>
> **Главное требование владельца:** закончи все исправления и подготовь ОДНУ полноценную Windows TEST-сборку, чтобы владелец мог проверить всё за один раз. 0.24.34 не подходит для полного теста: в ней есть клиентский `audio_profile=windows_gain_v1`, но production migration 020 и реальные усиленные Windows sidecar-файлы ещё не активированы. Не проси проверять усиление на этой сборке и не называй её финальной.
>
> Обязательно реализуй реальное применение `gain_db` из админки ко всем активным replacement с ненулевым значением (сейчас read-only аудит подтверждал Big City Life / Триагрутрика track 40371622 +11.5 dB; проверь актуальную базу повторно, не хардкодь одну песню). Используй подготовленный offline/private signed sidecar механизм W91–W93, migration 020, W93 CLI dry-run/explicit commit, с backup/rollback. Оригинальные audio_assets и браузерное расширение не менять. На Hostinger нет ffmpeg: рендерить офлайн, приватно, с проверкой SHA/version/gain/duration/peak/headroom, без публикации аудио в GitHub artifacts или логах. Затем проверить реальную HTTPS выдачу signed Range и `gain_applied=true`.
>
> **Обязательно добавлена новая задача #58:** при переключении VPN на «Моей волне» и обычных оригинальных песнях БЕЗ активной CELIKOM-замены музыка прервалась и был слышен «пшик», как будто переключился источник. Это не #57: там hiss после 403 на CELIKOM-треке. В #58 нужно доказать, что при ORIGINAL CELIKOM не трогает decoder/DownloadInfo, не вызывает reload/QUALITY_CHANGE, не пересоздаёт audio session и не запускает gain/crossfade. Проследи W15 route/entitlement → bridge SetEnabled/NATIVE_STATE → W23 host → W22 resource adapter → Yandex decoder. Не обходи серверную проверку подписки.
>
> Остальные задачи не потеряй и не смешивай: #52 — «Ты» (89285816), реальный source proof; #53 — Brave/Windows лаг; #54 — внезапное падение громкости Big City Life посреди альтернативы; #56 — общая gain parity; #57 — шипение после 403→206; плюс реальное ускорение VPN reconnect 40–50 секунд. Все эти проблемы должны быть покрыты тестами и попасть в одну итоговую сборку.
>
> Работай крупными самостоятельными блоками, не уходи в сторонние гипотезы. Перед изменениями проверь HEAD и сделай точный backup. После каждого блока запускай тесты и Windows CI. Не объявляй проблему решённой по одному CI. Не ломай pause/seek/Next/crossfade/autostart/Stop, entitlement, DPAPI, install-over-existing и Yandex vendor files.
>
> Когда всё действительно готово: собери один установщик и ZIP из точного CI artifact, проверь SHA256, загрузи оба в `/CELIKOM/Windows/Test/`, обнови документацию и пришли мне прямые ссылки плюс короткую инструкцию и единый чек-лист тестирования. До этого не отправляй промежуточные установщики. Ничего не устанавливай на мой ПК самостоятельно.
