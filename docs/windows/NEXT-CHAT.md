# 2026-11-13 W101 — CURRENT LEAD HANDOFF (READ FIRST)

**Authoritative current policy:** [W101-CELIKOM-WINDOWS-AUTO-UPDATE-AND-ROLLBACK-POLICY-20261113.md](W101-CELIKOM-WINDOWS-AUTO-UPDATE-AND-ROLLBACK-POLICY-20261113.md). Read this first, then W100 below.

**Repository:** `manufact-test/nomusic`.
**Active work branch:** `experiment/windows-w98-integrated-gain-and-original-vpn-20261113`.
**Current branch HEAD:** re-fetch from GitHub before work; documentation commits have advanced the branch beyond the code baseline below.
**Code baseline in the branch:** `e48e05f75629becc7efd2198dc7459a1ac91b825` (GUI 0.24.36 / native 0.24.29 / W23 0.24.10); commits after this baseline in the current handoff are documentation-only.
**Exact rollback before W101 documentation:** `backup/windows-w101-pre-update-policy-20261113` @ `39b763d6b94ce4ffb8660765da4eabeb3eeb9b48`.
**Earlier exact code rollback:** `backup/windows-w100-handoff-pre-docs-20261113` @ `e48e05f75629becc7efd2198dc7459a1ac91b825`.

**Windows CI:** [43500415302](https://github.com/manufact-test/nomusic/actions/runs/43500415302) SUCCESS on exact code SHA `e48e05f75629becc7efd2198dc7459a1ac91b825`.

**Latest Hostinger + gain + final installer workflow:** [43500415358](https://github.com/manufact-test/nomusic/actions/runs/43500415358) is now **COMPLETED / FAILURE**, not in progress. Verify/package job passed. Deploy failed at **“Verify preserved data and restore new snapshot in isolated MySQL”**. Private gain staging, final installer build and publish were skipped. Only the server-package artifact remains. Re-fetch the exact failing job log and determine actual remote state before doing anything. Do not blindly rerun, increment the one-shot request, repeat migrations, or make speculative server changes. The prior handoff's instruction to continue this run while it was in progress is superseded.

**Gain evidence:** Previous run [43495186951](https://github.com/manufact-test/nomusic/actions/runs/43495186951) passed private Windows sidecar staging for replacement 37 / track 40371622, admin +11.5 dB; measured +6.70 dB RMS with peak limited to 0 dB; live signed Range 206 and `gain_applied=true` passed. The latest run did not repeat this stage because deploy stopped. Do not claim current run staged or published gain files.

**One coherent next version only:** continue the existing CELIKOM application and same AppId/install path. Do not create a parallel app, do not send intermediate installers, and do not install anything on the owner's PC. The owner wants the next original CELIKOM release, not a series of user-facing “TEST apps”. Internal CI/QA is an engineering gate only.

**Updater truth:** the current CELIKOM app updater is manual local ZIP/EXE selection, staff/diagnostics-only via Ctrl+Shift+U. It is NOT a customer-facing automatic updater. W101 defines the required stable signed update feed, background check/download, in-place install, health check and automatic rollback. Do not claim automatic CELIKOM app updates already exist. Yandex vendor update monitoring is separate and already has its own hourly discovery + reviewed compatibility catalog.

**Do not ask the owner for another account, email, password, token or GitHub secret.** Do not expose or log existing secret values. Software update discovery must be independent of user login and entitlement.

**Owner's open Windows tasks remain:** VPN reconnect; #52 «Ты» actual audible replacement; #53 Brave/Windows stalls; #54 Big City Life mid-track volume drop; #56 admin gain for all active nonzero-gain alternatives; #57 403→206 hiss/pop; #58 original songs/My Wave must not be interrupted on VPN change. Keep #54, #56 and #57 separate. CI is not proof of audible success.

**Next actions:**
1. Read W101 and W100.
2. Re-fetch current branch HEAD and inspect run 43500415358's exact failed MySQL restore/audit log and actual server state. No duplicate deploy until root cause and idempotency are established.
3. Resume the current Windows fixes in the existing branch, one issue at a time; exact backup before each substantial change.
4. Deliver one coherent in-place update package only after server gain path and full installer pipeline pass.
5. Only after the owner has checked the coherent version, implement W101's automatic updater as a dedicated work block and make it a release requirement before general customer rollout.

## First message to the next lead

You are the lead developer for the existing CELIKOM Windows application. Continue; do not start over.

Repository: `manufact-test/nomusic`.
Work branch: `experiment/windows-w98-integrated-gain-and-original-vpn-20261113`.
Read first: `docs/windows/W101-CELIKOM-WINDOWS-AUTO-UPDATE-AND-ROLLBACK-POLICY-20261113.md`, then the historical W100 snapshot (now corrected to mark run 43500415358 as failed), then this file.

The current code baseline is GUI 0.24.36 / native 0.24.29 / W23 0.24.10 at `e48e05f75629becc7efd2198dc7459a1ac91b825`; re-fetch the current branch HEAD before editing. Exact rollback points are listed above.

Your first task is not a new architecture: inspect the completed failed workflow 43500415358, especially the isolated MySQL restore/audit step, and determine the actual state before any retry. Its gain staging, final installer and publish jobs were skipped. Do not blindly rerun deployment or mutate the one-shot request.

Then continue the owner's existing Windows fixes in the same CELIKOM product, one issue at a time: VPN reconnect, #52 «Ты», #53 Brave/Windows load, #54 Big City Life mid-track volume drop, #56 admin gain, #57 403→206 hiss, #58 original-song interruption/pop on VPN change. Keep #54/#56/#57 separate. Preserve pause, seek, Next, crossfade, autostart, authorization, Yandex originals and subscription enforcement. Make an exact backup before substantial changes. Do not count CI as proof of real audio.

The owner wants one coherent next release of the original CELIKOM application, installed over the existing AppId/path with saved login/settings preserved. No parallel app, no intermediate installers, no remote installation on the owner's PC, no unnecessary new branches, no new accounts/emails/secrets, and no user-facing “TEST app” terminology. Do not ask the owner to configure anything unless a real blocker is proven and explained first.

Important updater finding: current CELIKOM app updater is manual local ZIP/EXE selection behind a staff/diagnostics shortcut; it is not automatic for ordinary users. Implement the automatic signed stable-feed updater, background download, safe in-place install, post-update health check and automatic rollback from W101 as a separate bounded block after the current audio fixes and coherent owner delivery. Yandex vendor update monitoring is separate and already exists.

Work in large coherent blocks. Report only what changed, what is proven, what remains unverified, and the single current blocker. Never announce completion based only on CI.

---


# 2026-11-13 W99 — CURRENT LEAD HANDOFF (READ FIRST)

**Current branch:** `experiment/windows-w98-integrated-gain-and-original-vpn-20261113`.
**Current HEAD:** `b1f9064edfc33b83e08abe22e7d38a0a87298e59`.
**Exact rollback:** `backup/windows-w99-0.24.36-green-hostinger-blocked-20261113` @ `b1f9064edfc33b83e08abe22e7d38a0a87298e59`.
**Main status:** GUI 0.24.36 / native 0.24.29 / W23 0.24.10; exact Windows CI [43470332842](https://github.com/manufact-test/nomusic/actions/runs/43470332842) SUCCESS. W91 sidecar CI [43469841569](https://github.com/manufact-test/nomusic/actions/runs/43469841569) SUCCESS.
**Read first:** `docs/windows/W99-0.24.36-INTEGRATED-QA-STATUS-20261113.md`, then `docs/windows/W97-FINAL-READY-RELEASE-HANDOFF-20261113.md`, W90 and W93.
**Only current blocker:** Hostinger deploy [43470332960](https://github.com/manufact-test/nomusic/actions/runs/43470332960) stopped before snapshot/deploy/migration/media writes because Actions secret `CELIKOM_W98_TEST_EMAIL` is empty. Owner must add that repository secret with the primary CELIKOM account email in Settings → Secrets and variables → Actions; do not ask the owner to post the email in chat. After the owner confirms it is added, advance `.github/deploy/hostinger-request.json` to request 022 and rerun the guarded workflow. Do not bypass the gate or send a partial installer.
**No installer has been published yet.** After the guarded deployment, sidecar verification and final in-place/DPAPI checks pass, publish one EXE + ZIP to `/CELIKOM/Windows/Test/`. Owner acoustic QA remains required for #52/#53/#54/#57/#58.

---

# 2026-11-13 W98 — HISTORICAL LEAD HANDOFF (superseded by W99)

**Latest integrated work branch:** `experiment/windows-w98-integrated-gain-and-original-vpn-20261113`.
**W98 pre-change exact backup:** `backup/windows-w98-pre-integrated-gain-and-original-vpn-20261113` @ `5ce1ec127009ba4a86a8e5ee1d129ec86623fd54`.
**Latest W98 code SHA with full CI SUCCESS:** `696e36b65c2a5accaa0e5c6c8aeb7548611932f1` (documentation may advance branch HEAD; re-fetch before any new work).
**Full current handoff:** `docs/windows/W98-INTEGRATED-QA-AND-LIVE-GAIN-HANDOFF-20261113.md`.

W98 adds issue #58 original-track no-reload handling, W22/W23 regressions, Windows-only private gain sidecar staging/rollback, and a single 0.24.35 / native 0.24.28 installer pipeline. Browser extension sources remain unchanged. W98 full CI [43462340493](https://github.com/manufact-test/nomusic/actions/runs/43462340493) SUCCESS on SHA `696e36b65c2a5accaa0e5c6c8aeb7548611932f1`: Hostinger YAML, owner-email-only session gate, Linux packaging, W22/W23/W60, W21, W24, W15 and GUI compile all passed.

**Do not trigger live Hostinger gain staging yet:** production migration 020 and real sidecars are not activated. The prior deploy attempt [43454991506](https://github.com/manufact-test/nomusic/actions/runs/43454991506) stopped at pre-deploy snapshot due stale branch SHA; deploy and staging jobs were skipped. The owner explicitly authorized his primary CELIKOM account by email. The helper resolves only that email and only that user's active session; no numeric ID is needed and no other customer session is scanned. The owner must add the one-time GitHub Actions secret `CELIKOM_W98_TEST_EMAIL`; preflight blocks before snapshot/deploy/migration if missing. Once added, update the one-shot request file and run the private deployment. See W98 handoff for exact details.

---

# 2026-11-13 W97 — OWNER REQUEST: ONE COMPLETE WINDOWS TEST BUILD (READ FIRST)

**Главный handoff и готовое первое сообщение следующему чату:** [W97-FINAL-READY-RELEASE-HANDOFF-20261113.md](W97-FINAL-READY-RELEASE-HANDOFF-20261113.md).

Владелец просит **не присылать очередной частичный установщик**. Следующий ведущий должен закончить серверную + Windows интеграцию и отдать один единый TEST-релиз, чтобы владелец проверил все проблемы за один проход. **0.24.34 не является сборкой для полного теста:** клиент просит `audio_profile=windows_gain_v1`, но production migration 020 и реальные sidecar MP3 с усилением не установлены/не зарегистрированы. Не просить владельца тестировать gain на 0.24.34.

**Новая задача #58:** на «Моей волне» / оригинальных треках без активной CELIKOM-замены при VPN switch музыка прервалась и прозвучал «пшик». Это отдельно от #57 (403→206 hiss), #54 (падение громкости Big City Life) и #56 (gain parity). При ORIGINAL CELIKOM должен быть прозрачен для текущего decoder; проследить W15 route/entitlement → bridge state → W23 host → W22 adapter → Yandex decoder. Не обходить серверный entitlement.

Открытые задачи: #52 «Ты» / реальный decoder proof; #53 Brave/Windows лаг; #54 Big City Life mid-track drop; #56 реальное применение gain_db ко всем активным ненулевым настройкам; #57 hiss после 403→206; #58 оригинальный трек pop при VPN; плюс реальное ускорение VPN reconnect 40–50s. См. критерии и полный план в W97.

**Baseline:** branch `experiment/windows-w95-02434-qa-candidate-20261113`; code `4f8b3a72687577c5447d157be156365ab42a86fa`; W95 exact backups и W89/W88 rollback перечислены в W97. До любых правок fetch current HEAD и создать новый exact backup. Владелец не разрешал установку на его ПК; только отдать installer после готовой сборки.

---

# 2026-11-13 — WINDOWS 0.24.34 W95 QA INSTALLER GREEN + LIBRARY (READ FIRST)

**LATEST Windows test candidate:** source branch `experiment/windows-w95-02434-qa-candidate-20261113`; exact installer/audio code `4f8b3a72687577c5447d157be156365ab42a86fa` (subsequent commits may be docs-only). **Full owner handoff:** `docs/windows/W95-02434-OWNER-QA-DELIVERY-20261113.md`.

**0.24.34 GUI / native 0.24.27:** final Windows CI SUCCESS [43442749658](https://github.com/manufact-test/nomusic/actions/runs/43442749658); W89 0.24.33→W95 in-place DPAPI + two updated native files pass, AppId/pinned vendor safety pass. Installer SHA256 **83CF52CE7808CF03E33FBE461FDFE73C40080545642B29B5F9ED81015DEB1FFE**, 43,551,775 bytes. Both EXE and ZIP extracted/CRC verified and persistently uploaded to Library:
- `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.34-AUDIO-VPN-QA-TEST.exe` (`libfile_a4d924edf8f48191a6fa183b41097408`).
- `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.34-AUDIO-VPN-QA-TEST.zip` (`libfile_e690d182c16c8191a1c851854ccbebaf`).
- Previous W89 0.24.33 and W88 0.24.32 installers and **exact rollback** `backup/windows-w95-pre-02434-qa-candidate-20261113` @ `80113ff54e0479c0412e51263cd81078b39082e1`, and pre-403 W95 backup `backup/windows-w95-02434-pre-w96-403-guard-20261113` @ `cc35d1fff1e6b60dd98eb1de6ce2b4ab61f67ecb`.

**What changed:** W94 last VPN route event always revalidates fresh entitlement (no 1.4s dropped final signal); W89 prevents mapped-only false green and does one bounded current source refresh on «Ты»; W92 passive decoder source-loss/current volume-drop and event-loop stall signals; W96 verified-current signed decoder suppresses only pending redundant 403 reload (possible hiss mitigation). All offline native tests green. **No owner real playback or VPN QA yet; never mark issues solved.**

**Gain:** real read-only production: 1493 active songs, one **«Биг сити лайф» Триагрутрика 40371622 +11.5 dB**, disabled **«Папиросы» Зануда 1944599 +12 dB**, 4 historical edits, no mass reset. W90–W93 isolated Windows-only pre-render signed sidecar pipeline tests green with disposable MariaDB/FFmpeg. **Production server migration 020 and boosted Big City Life file NOT deployed**: Windows 0.24.34 test **still does NOT actually add +11.5 dB** until explicit verified media processing/sidecar activation, and cannot by itself prove the sudden mid-track drop. Hostinger has no ffmpeg. Browser original remains unchanged.

**Next priority:** owner installs 0.24.34 TEST and listens to «Ты», Big City Life, natural 403 recovery, VPN A→B, Brave performance; gather authorized diagnostics. Then fix remaining **actual** audio source/volume without second player or blanket gain, and stage Windows-only media variant under controlled rollback. Follow issues #52 decoder, #53 performance, #54 Big City Life dip, #56 boost parity, #57 hiss. Do not change production/Yandex or owner PC automatically.

---

# W94 CHECKPOINT 2026-11-13 — SAFE PRIVATE BOOST PATH + VPN ROUTE BURST (EXPERIMENT, NO INSTALLER)

**Latest work branch** `experiment/windows-w94-vpn-route-burst-recheck-20261113`; exact pre-W94 frozen `backup/windows-w94-pre-vpn-route-burst-20261113` @ `5f339d2f77b57eb8da5df7705a6e6235cd66d7c7`. W94 source `e4100eb9e83fae2e954ce4819178485ad54e2427`: network address signals within 1.4s now each update route epoch and cancel stale rechecks; coalescing limits only log. Last VPN signal wins after quiet 750ms. Entitlement still MUST come from fresh authenticated server; no offline grant. W94 Windows CI: https://github.com/manufact-test/nomusic/actions/runs/43440706956 (verify final state). Real 40-50s owner VPN test NOT yet performed.

**W90/W91/W92/W93 stacked on current branch**: admin gain +dB was not applied at all by Windows Yandex native source-only route; backend stored +11.5 dB Big City Life 40371622, +12dB disabled Папиросы 1944599. [READONLY 43438999212](https://github.com/manufact-test/nomusic/actions/runs/43438999212) showed 1493 active, only 1 boost, 1499 total versions, 4 gain edits: 0→12, 0→0.5→0, 0→11.5. NO evidence of massive settings loss. On Hostinger no ffmpeg/ffprobe. W91 implements optional Windows-only, offline *pre-rendered* SHA/version/gain-bound sidecar with signed scoped HMAC and Range; unprocessed URL for Chrome unchanged. W91 [CI 43437638500](https://github.com/manufact-test/nomusic/actions/runs/43437638500) SUCCESS. W92 adds passive CDP current source leaves CELIKOM / optional native volume-drop / event-loop stall/memory warnings; [CI 43438578606](https://github.com/manufact-test/nomusic/actions/runs/43438578606) SUCCESS. W93 operations-only private gain stager dry-run/commit; [full disposable MariaDB + MP3 CI 43440173979](https://github.com/manufact-test/nomusic/actions/runs/43440173979) SUCCESS. See `docs/windows/W90-ALL-ADMIN-GAIN-TRACKS-AUDIT-20261113.md` and `docs/windows/W93-PRIVATE-GAIN-STAGING-AND-ROLLBACK-20261113.md`. **No LIVE media converted, no production migration, no newly delivered Windows installer, no owner actual speaker gain proof**.

**Do not confuse** the systematic Windows missing gain with Big City Life's **sudden mid-song volume dip**, which remains unexplained without actual owner trace. Also unresolved: «Ты» 89285816 original fallback, hiss after fast 403, Brave/Windows freezes (issues #52, #53, #54, #56). W89 0.24.33 TEST CI-green but still not owner tested; W88 0.24.32 rollback and all frozen branches preserved. W94 must pass Windows CI, then separate Windows installer and owner listening QA before declaring any issue fixed. Never deploy server variant without migration, separate Hostinger restore plan, real rendered media validation, and owner explicit gate.

---

# 2026-11-13 — W90 WINDOWS OWNER UPDATE: GLOBAL ADMIN GAIN LOSS CONFIRMED IN CODE, ONE LIVE BOOSTED SONG

**Current W90 experimental / NON-RELEASE** `experiment/windows-w90-boosted-tracks-gain-parity-20261113`, based on W89 owner handoff HEAD `ba46821aaee8f9750b725699d4b7db7656a2b0cc`; exact rollback `backup/windows-w90-pre-gain-parity-20261113`. W90 code commit `d097981a41e37b754fee834b7643901f47ef936b`, CI **SUCCESS** [43433517528](https://github.com/manufact-test/nomusic/actions/runs/43433517528). W89 0.24.33 TEST and installer unchanged, **not field-verified**; no W90 installer or deployment.

**Definite systemic admin gain gap**: server `ResolveService` returns numeric `gain_db`, admin preview and Chrome extension add Web Audio gain, but signed Range audio serves raw original bytes; prior Windows `GrantValidator` dropped gain, and native Yandex downloadInfo `gain: false` is boolean. W90 safely transports gain through C# grant and emits code-only `GAIN_CONFIGURED_NATIVE_DSP_NOT_APPLIED` for nonzero positive/negative gain in native single/batch; **no actual DSP yet, no audible fix claimed**. See `docs/windows/W90-ALL-ADMIN-GAIN-TRACKS-AUDIT-20261113.md`, [Issue #56](https://github.com/manufact-test/nomusic/issues/56).

**New LIVE read-only query result**, [Actions 43434214069](https://github.com/manufact-test/nomusic/actions/runs/43434214069) SUCCESS: 1493 active approved replacements; **one boosted**, zero attenuated, 1492 with 0 dB, 0 invalid. Historical inactive/pending gain edits and identity of the one boosted track **not yet checked**, so cannot infer others lost their settings. Big City Life's sudden *mid-song* dip is separate Issue #54 with no root cause proof.

**Next:** implement validated per-track audible gain without a second player / without breaking native Yandex, account entitlement, Range 403/VPN, pause/seek/Next and Chrome parity. Do not set Yandex boolean gain to numeric dB, do not globally amplify on server or Windows. Preserve W89 and W88 rollbacks, test offline then Windows CI, only then owner-sound TEST. Continue W89 VPN and «Ты» source QA, hiss, Brave freeze per W89 documentation. W90 is not stable/a production release.

---

# 2026-11-13 — WINDOWS OWNER HANDOFF / STOP CODING (ALL ISSUES INCLUDING BIG CITY LIFE)

**Owner instructed current developer to STOP and hand all remaining work to the NEXT chat.** Preserve and continue existing repo, no rewrite. **Read first** `docs/windows/W89-02433-VPN-RECOVERY-AND-FALSE-GREEN-TRACK-20261113.md`, especially the newest **STOP-WORK / OWNER HANDOFF ADDENDUM** at its end.

**Repo:** `manufact-test/nomusic`.
**Working Windows branch:** `experiment/windows-w89-vpn-fast-recovery-audio-proof-20261113`.
**Exact W89 CI-green code/source backup:** `backup/windows-w89-02433-ci-green-owner-handoff-before-volume-20261113` @ **`6916c0229861aaa6f2486224f3e62092b343698e`**. Older W88 0.24.32 rollback `backup/windows-w89-before-vpn-recovery-audio-proof-20261113` @ `3ebded59b4bf596d54b1b5b29edfe16683ad45a0`.
**Last CI-green TEST installer:** 0.24.33 (native 0.24.26), run https://github.com/manufact-test/nomusic/actions/runs/43429303326, artifact `14039475715`, EXE SHA256 `414EDBA856A12B25CB3EDE26D136C7F263CFC02FC3448730C7F7D02D60791879`. Library `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.33-VPN-TRACK-TEST.exe` and same basename `.zip`. CI green, **NOT user-playback tested**. Never claim field verification or deploy automatically.

**ALL outstanding defects, priority:**
1. **40–50s VPN switch loss**. Older owner 0.24.32 `диагна.txt` and second snapshot `Вставленный текст(20261113-123416).txt`: at 12:26:29 UTC LOCAL_HTTP_TIMEOUT, 12:26:44 NETWORK_SUSPENDED, later VPN route changed, repeated GET timeouts until around 12:27:29; W89 0.24.33 short bounded cancellation/rechecks implemented and CI passed, **owner still must validate speed on actual VPNs**. NEVER bypass signed-in fresh server authorization.
2. **«Ты» — тринадцать карат**: owner screenshot shows green «Подмена активна» while original music actually plays; mapped current `track=89285816` but no matching CELIKOM Media GET in the following ~34s. W89 marks mapping neutral instead of false green and adds bounded one-shot source refresh on exact current track; **audible replacement still unverified**.
3. **NEW: Big City Life (artist as user called it «трио Гутрика»)**: alternative CELIKOM version **suddenly becomes ~2× quieter while still playing**, remains quiet; **admin volume boost and loud preview remain intact**. Do not invent gain measurements or assert admin lost gain. Trace server-side boosted file/metadata vs delivered signed resource, client source switches, Yandex normalization, crossfade/volume. **Issue #54 https://github.com/manufact-test/nomusic/issues/54**. No incident-specific diagnostics yet.
4. **Loud hiss/pop after fast 403 recovery**: initial drop had expired audio URL, 403, fresh HTTP206 within ~0.5s; audible hiss cause unknown. Avoid blanket gain or sudden cut fixes.
5. **Global Brave/system freeze with Yandex + CELIKOM**: owner reported temporary slowdown, extra-rights prompt source unknown; issue #53. Needs actual process loads / prompt identity, no malware conclusions or random permission changes.
6. **Native decoder evidence**: grant/206/file-info is NOT playback proof; CDP kUrl may be absent; #52 remains open.

**What's already done:** W89 GUI 0.24.33 + native 0.24.26 code has short verified VPN refresh and current-source-guard tests; Windows CI `W89_02432_TO_02433_INPLACE_DPAPI_AND_NEW_NATIVE_READY_PASS`. Installer and separate ZIP uploaded to Library. Owner currently showed 0.24.32 diagnostics and screenshot; don't assume they installed 0.24.33. No new code changes requested in current chat.

**Next developer instruction:** read W89 handoff and backup, continue on NEW dedicated child branch if making risky improvements, work in independent sizable blocks with tests, retain both old installers; first focus true audio for «Ты» and volume dip for Big City Life without breaking stable 0.24.32 playback, independently validate VPN recovery. Do not write reassuring success statements without real owner listening tests. Keep docs/next-chat current, produce a new tested installer only after CI-green and explicit QA path. Any code changes must have their own rollback.

---

# W89 — WINDOWS 0.24.33 TEST: VPN FAST RECOVERY + «ТЫ» FALSE GREEN (2026-11-13, FIRST PRIORITY)

Owner's 0.24.32 actual diagnostics `диагна.txt` and `Вставленный текст(20261113-123416).txt` show two music drops, including VPN switch which held CELIKOM disabled for ~49 seconds after initial failed access check; first transient expired signed URL HTTP403 recovered with HTTP206 in ~0.5s but audible hiss unexplained. Owner screenshot: **«Ты» / тринадцать карат** plays censored original yet CELIKOM wrongly claims green `Подмена активна · версия CELIKOM`. Latest screenshot/log current `track=89285816`, source batch mapped but **no corresponding CELIKOM Media GET in next ~34sec**. File-info mapping/HTTP206 is not proof audio source was used. Actual audible version not independently observable yet.

**Working** `experiment/windows-w89-vpn-fast-recovery-audio-proof-20261113`. **Exact owner-accepted source rollback** `backup/windows-w89-before-vpn-recovery-audio-proof-20261113` @ `3ebded59b4bf596d54b1b5b29edfe16683ad45a0`; old W88 installer 0.24.32 preserved in Library. Full detailed task/evidence/limits docs: `docs/windows/W89-02433-VPN-RECOVERY-AND-FALSE-GREEN-TRACK-20261113.md` (READ FIRST).

Implemented candidate **GUI 0.24.33 / native 0.24.26**:
- New network-route signal cancels GET tied to retired VPN, reacts even when bridge is still active, coalesces change 750ms, starts fresh authenticated read-only entitlement GET. Short 3s timeout on fresh route / while suspended, every 3s until new server success; healthy 15s unchanged; no offline grant or manual Stop override. Exact account/native safety remains.
- UI green ONLY when current signed CDP decoder `kUrl` and `kIsPlaying` corroborate source, bridged as `NATIVE_SOURCE_VERIFIED`. Mapped-only current song (including false positive «Ты») is a small neutral `Версия CELIKOM передана Яндексу`, not fake confirmation.
- For exact current mapped+approved song only, when CDP Network observer present but **no Media HTTP200/206 for its valid signed source** ~3.5–16s after first observed current track, one (120s cooldown) safe in-place `reloadEntity("QUALITY_CHANGE")` through existing Yandex player, same-track and enabled checks. This is a bounded source-recovery attempt, not confirmed audible fix, no player/queue/seek replacement, no forced audio fetch.
- Preserved existing expired-token 403 immediate current-track recovery, original files trust pins, first Start/Stop, promo and tray autorun default-on. W89 native host and renderer assets intentionally change; app will need safe native update by Start on first 0.24.33 use (don't claim green until native installed).

**CI** workflow `.github/workflows/windows-w89-vpn-fast-recovery-track-fix-installer.yml`, final observed run https://github.com/manufact-test/nomusic/actions/runs/43429303326 (pending at time of this entry). Tests include W89 renderer one-shot, native CDP proof/206 suppress and old Yandex reload pause/seek/queue, W15 fast VPN, W21/W24 backup, signed installer in-place DPAPI. **Before delivering confirm CI GREEN + exact SHA and Library upload**. Do not claim user's actual audio fixed without their Windows VPN and «Ты» test; download 0.24.33 only as TEST, with old 0.24.32 available to roll back. Network route checks cannot fix a blocked endpoint on the new VPN. Open issue #52 real source proof, #44 owner QA, #53 Brave/Yandex system stalls.

---

# W88 0.24.32 CI GREEN + LIBRARY — DEFAULT WINDOWS AUTORUN WITH STICKY OPT-OUT (2026-11-13)

User requested autoplay-launch toggle inverted from W87: **CELIKOM auto-starts in Windows tray by default**, no need to opt in. User may right-click tray → **«Отключить запуск с Windows»**, and that opt-out remains permanent across in-place updates and Windows logins. This launches CELIKOM in background, **NOT** Yandex automatically; auto-reconnection requires last explicit Start and fresh verified entitlement, supported vendor source and exact native module. Manual Stop survives reboot. Implementation: `WindowsLaunchSettings.EnsureFirstLaunchDefault`, sticky `AutoRunConfigured` HKCU setting, updated dynamic tray menu. Working branch `experiment/windows-w88-default-autorun-optout-20261113`. Original W87 backup `backup/windows-w88-pre-default-autorun-exact-20261113` @ `9acee0c2ca33c7d3ca2ed940abacc57a037ca1d3`.

**W88 Windows CI SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/43404108350; artifact `14026731408`; 0.24.32 installer SHA256 `715D7F8B97F2D97E2ACE2FBBB0211F760F9A34E2EB14864FE91CB261C965CF4E` size 43,546,132 bytes. Windows in-place 0.24.31→0.24.32 preserved encrypted DPAPI login and BOTH native audio files byte-identically. **Persistent Library upload verified**: `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.32-AUTORUN-DEFAULT-ON-TEST.exe` (ID `libfile_c4548e97dfac81918a6d250d92ba3e73`), local sandbox `/mnt/data/CELIKOM-Windows-0.24.32-AUTORUN-DEFAULT-ON-TEST.exe`. Full docs `docs/windows/W88-DEFAULT-WINDOWS-AUTORUN-OPT-OUT-20261113.md`. Owner real Windows reboot and music QA **NOT yet performed**; old 0.24.31 TEST and stable 0.24.29 remain for rollback, no remote installation. No audio/stream rewrite or new popup errors. Issue #44 playback, #52 source-proof, #48 migration still open.

---

# W88 0.24.32 — AUTORUN DEFAULT ON, PERSISTENT OPT-OUT (2026-11-13)

User revised Windows startup UX: CELIKOM **must enable autostart automatically on first application launch** after installation. If undesired, right-click CELIKOM tray and choose **«Отключить запуск с Windows»**; keep user's opt-out across future restarts/upgrades. Former W87 0.24.31 asked the user to opt IN; W88 fixes that. Uses HKCU Run with `--background`, sticky user preference marker `HKCU\Software\CELIKOM\Windows\AutoRunConfigured`. Existing fresh-entitlement and manual last Stop guard remain unchanged: startup does NOT auto-open Yandex nor authorize music without server. Full docs `docs/windows/W88-DEFAULT-WINDOWS-AUTORUN-OPT-OUT-20261113.md`.

Work branch `experiment/windows-w88-default-autorun-optout-20261113`; pre-W88 exact backup `backup/windows-w88-pre-default-autorun-exact-20261113` @ `9acee0c2ca33c7d3ca2ed940abacc57a037ca1d3`. W87 0.24.31 working TEST remains available Library `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.31-AUTORUN-TEST.exe`. W88 candidate CI workflow `windows-w88-default-autorun-installer.yml`, run `43404108350` in progress at creation of this note. MUST verify job conclusion and exact installer SHA before calling finished. No changes to host.cjs or renderer.js native audio. Reboot/Windows field QA still pending. Source witness issue #52 open, #48 future migration.

---

# W87 0.24.31 WINDOWS AUTORUN + QUIET REPAIR — CI GREEN, LIBRARY DELIVERED (2026-11-13)

Source: `experiment/windows-w87-autostart-quiet-repair-20261113`; **pre-work immutable backup** `backup/windows-w87-before-autostart-qa-owner-20261113` @ `77cd940ea9bb4bb20b70341e33957ee757e45d41`. Full detailed owner QA, code/test changes, remaining physical tests: `docs/windows/W87-OWNER-QA-20261113-STARTUP-AUTORUN-REPAIR-HANDOFF.md` (read first).

**User listened to 0.24.30 on real Yandex and reports music works.** Latest diagnostics file `Вставленный текст(20261113-084941).txt`: `NativeModuleMatchesApp=true`, `NativeIntegration=ACTIVE`, `Enabled=true`. At 08:49:22 UTC one expired signed URL caused 403 `PLAYER_403_PHP_INVALID_AUDIO_TOKEN`, immediately followed by a refreshed URL HTTP 206. This is confirmed transient recovery; no W87 audio logic modification and **no proof of audible output**. Issue #52 remains open.

**W87 fixed:** false red outdated-module warning (ordinary post-update hash mismatch is now quiet grey "Нажми «Старт», чтобы обновить модуль"), smooth first window paint, manual Start updates prior-consented module and opens actual Yandex after successful repair; new optional right-click tray → **Запускать с Windows** sets HKCU Run `--background`. Single-instance guard allows reopening tray via desktop shortcut. Previously approved Start intent tied to exact user installation, manual Stop survives reboot. On sign-in CELIKOM quietly checks fresh server entitlement, native trust/hash; repairs only supported signed approved build when Yandex isn't running; retries with 2m backoff, no automatic Yandex launch, no auth/unknown-build bypass. Promo display stays steady, W86 passive CDP source diagnostic stays internal, no new alarm colours.

**WIN CI GREEN** https://github.com/manufact-test/nomusic/actions/runs/43398111483 — W87 0.24.31 installer artifact `14024195652`, SHA256 `762B9F4166B611BB78FDD7CE4F1F8311E2DA05E7171CC3E3EC3EC6017061EF83`, 43,545,042 bytes, direct owner file `/mnt/data/CELIKOM-Windows-0.24.31-AUTORUN-TEST.exe`. **Persistent ChatGPT Library upload success**: `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.31-AUTORUN-TEST.exe` (ID `libfile_9bb79f49b7908191a11150cafcd9c5fb`). 0.24.30→0.24.31 disposable Windows in-place passed with DPAPI decryptable and BOTH host.cjs + renderer.js unchanged. **Owner physical reboot/playback QA still pending**, no deployment over owner's installed app automatically. Stable 0.24.29 and previous TEST 0.24.30 files preserved in Library. User should test tray autorun/reboot/explicit Stop, smooth initial GUI, manual native repair, songs/seek, send diagnostics if issue.

Remaining: issue #44 audio QA, #52 actual decoder proof, #48 future migration. If a future chat resumes: **do not overwrite W87 or claim completed field QA**; start from source branch/doc and next owner results.

---

# W87 OWNER CHECKPOINT + AUTOSTART / REPAIR — 2026-11-13 (READ FIRST)

Owner 0.24.30 test listening seems normal, but screenshot showed erroneous `Модуль CELIKOM устарел. Нажми «Обновить модуль»` despite no such button. Pressing **Старт** actually did repair native module: 07:48:13 `NATIVE_UPGRADE_REQUEST`, 07:48:24 `NATIVE_UPGRADE_OK`, then `START_ENABLED`. Latest owner diagnostics 08:49:25 show `NativeModuleMatchesApp=true`, `NativeIntegration=ACTIVE`, `Enabled=true`. One **transient 403** at 08:49:22 due to expired audio URL (`PLAYER_URL_EXPIRED_AT_REQUEST`, `PLAYER_403_PHP_INVALID_AUDIO_TOKEN`) was followed by renewed signed URL HTTP 206; do NOT claim all audio is independently proven or change playback blindly. App popup briefly displays blank blocks before initial render.

**Owner explicitly authorized coding after we save docs first**: smooth startup UI, remove misleading red warnings / nonexistent «Обновить модуль»; use actual Start for automatic native verification/repair and launch Yandex on manual Start. Add optional Windows login autorun **minimized to tray** with remembered last user Start/Stop preference, unattended safe native reconnection and entitlement checks (NO auto-launch Yandex on boot). Manual Stop must survive reboot; avoid enabling without verified entitlement or vendor trust. Real red error only when actionable. **No new yellow warnings or large technical text**. W83 promo stable no-blink preserved.

**Exact rollback first**: `backup/windows-w87-before-autostart-qa-owner-20261113` @ `77cd940ea9bb4bb20b70341e33957ee757e45d41`. Working `experiment/windows-w87-autostart-quiet-repair-20261113`. All detailed requirements, facts, and test plan saved *before code* to `docs/windows/W87-OWNER-QA-20261113-STARTUP-AUTORUN-REPAIR-HANDOFF.md`. User's current installed 0.24.30 TEST is unaffected, stable 0.24.29 Library backup preserved. Source witness issue #52 stays open; CDP no actual proof of audible replacement.

---

# W86 0.24.30 — real Windows CDP source diagnosis TEST installer uploaded 2026-11-13

Owner asked why the experimental sound diagnostics was not provided for testing on their real Yandex Music computer. Corrected: delivered **separate TEST 0.24.30**, preserving stable 0.24.29 separately. **Windows installer CI green** https://github.com/manufact-test/nomusic/actions/runs/43384241445, SHA256 `F289167A6106505FCFD46F89BE7B6DA34DAFD2DD27695AF3549F0D1A7BBD1AD8`, 43,551,635 bytes, artifact `14018310589`. Verified persistent Library upload: `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.30-TEST-SOURCE-DIAGNOSTICS.exe` (`libfile_e2c07d37b86c8191ad375857a5d44843`). Owner real-device QA pending: use new TEST to listen normally and send owner diagnostics, observing `PLAYER_DECODER_CELIKOM_SOURCE_MATCHED` and `PLAYER_DECODER_CELIKOM_PIPELINE_ERROR`; may be unknown if Yandex doesn't expose CDP kUrl. No new user-facing warnings. If regression, reinstall stable 0.24.29 from Library `/CELIKOM/Windows/CELIKOM-Windows-0.24.29-PROMO-FIX.exe` (same AppId). In-place 0.24.29→0.24.30 tested with retained DPAPI and unchanged renderer audio file, only passive host.cjs witness differs. Branch `experiment/windows-w86-02430-source-witness-owner-test-20261113`; exact pre-edits `backup/windows-w86-pre-02430-source-witness-20261113`. Full details `docs/windows/W86-02430-OWNER-TEST-CDP-DECODER-20261113.md`. Issue #52 remains open until owner's live test.

---

# W83 promo steady / W84 current-decoder source evidence — 2026-11-13

Current owner version **0.24.28** (W82 CI green, user said «вроде всё хорошо», plans live music QA tomorrow). **Do not ask owner to replace 0.24.28 before that QA.**

**W83 PROMO FLICKER FIX READY (not released):** `experiment/windows-w83-promo-steady-entitlement-20261113` / safe backup `backup/windows-w83-promo-steady-windows-ci-green-20261113`. The 15s entitlement poll was changing label from **«Промокод · доступ навсегда» → «Проверяем доступ…» → back**. Fixed display-only, preserving live authenticated revocation and account switching; tests Windows CI SUCCESS [43310069470](https://github.com/manufact-test/nomusic/actions/runs/43310069470). Read `docs/windows/W83-PROMO-ENTITLEMENT-NO-BLINK-20261113.md`. No installer/version bump yet; carry into next release after owner QA.

**W84 PASSIVE CURRENT PLAYER SOURCE RESEARCH (experimental, not released):** `experiment/windows-w84-readonly-player-source-evidence-20261113`, exact backup `backup/windows-w84-pre-evidence-w83-green-20261113`. CDP reports `PLAYER_DECODER_CELIKOM_SOURCE_MATCHED` only when observed current decoder kUrl equals valid unexpired signed CELIKOM grant and `kIsPlaying` true, Yandex current track matches; correlated player errors `PLAYER_DECODER_CELIKOM_PIPELINE_ERROR`. Not user-facing and **not proof of audible speaker playback**. Native test CI [43311056109](https://github.com/manufact-test/nomusic/actions/runs/43311056109) SUCCESS. See `docs/windows/W84-PASSIVE-NATIVE-DECODER-WITNESS-20261113.md`. Issue [#52](https://github.com/manufact-test/nomusic/issues/52) stays OPEN for real-player verification.

**Other outstanding Windows tasks:** issue #44 remains open pending owner live playback and actual error reports; issue #48 only actionable at future GitHub→private host migration. Neither may be closed based on CI alone. W82 owner's current 0.24.28 was not changed remotely.

---

# W82 — Windows 0.24.28 quietly restores compact popup, fixes false connection errors (2026-11-12)

Owner tested 0.24.27 and saw **false red "Нет ответа..."** after 30s of a healthy unchanged song and **yellow "Фактический звук ещё не подтверждён"** on successful audio plus dotted focus buttons. Cause: W23 native `host.cjs` only sends `/v1/heartbeat` on native state/track **changes**; W81 incorrectly treated a silent 30s as disconnected. Mapping-accepted was also misclassified as a warning. Full docs: `docs/windows/W82-COMPACT-QUIET-STATUS-FALSE-ALARM-FIX-20261112.md`.

- Branch: `experiment/windows-w82-compact-quiet-status-ui-20261112`.
- Exact source before edits: `backup/windows-w82-pre-ui-quiet-exact-20261112` @ `7339dcb464bd942e27fac74c7f18a3008275d038`.
- W82 removes dotted popup-button focus outlines, removes the W81 30-second false error, no yellow notices, restores green "Подмена активна · версия CELIKOM" under the song on an accepted approved version; only one small red error for actual reported source/host failure. The only large status is "Идёт загрузка Яндекс.Музыки…" during actual Start.
- Live entitlement and native files/auth/audio scripts still unchanged from verified W81 and native 0.24.25; GUI candidate version 0.24.28.
- False queued-start-error must not persist after `_bridge.Enabled=true`. Explicit host incompatibility remains actionable.
- **Important limitation:** actual audible CELIKOM source vs original cannot yet be independently verified; [issue #52](https://github.com/manufact-test/nomusic/issues/52) tracks genuine media-source witness. Do NOT claim that accepted URL proves audible audio; but **do not show alarms to ordinary users on normal playback**.
W82 final CI **GREEN**: GUI/native health https://github.com/manufact-test/nomusic/actions/runs/43308399922; Windows EXE in-place W81 0.24.27→W82 0.24.28 https://github.com/manufact-test/nomusic/actions/runs/43308400132; EXE SHA256 `74E385DEEAA3FE94FF330CEB5B20D6EF60A8779F4CAA9517C888C9D10DFC5EE3`, 43,545,102 bytes; artifact 13984233778. Owner 0.24.28 physical QA pending.

- Exact CI: `.github/workflows/windows-w82-compact-quiet-regression.yml`, `.github/workflows/windows-w82-quiet-ui-installer.yml`; verify newest green run and artifact before giving owner EXE.
- Do not overwrite old W81 and W80 reserves; in-place installer preserves DPAPI and Yandex originals.

---

# W81 Windows release watcher + 2026 compatibility + visible audio errors — CI GREEN (2026-11-12)

Source: `experiment/windows-w81-vendor-monitor-compat-visibility-20261112`; pre-W81 reserve `backup/windows-w81-pre-monitor-and-status-exact-20261112`. Full documentation `docs/windows/W81-YANDEX-AUTO-WATCH-2026-STATUS-20261112.md`. Owner Windows 0.24.25 seems to work; owner planned full music QA tomorrow — **do not ask to replace the owner working 0.24.25 tonight**.

**Four project decisions implemented:** portable official Yandex Windows `latest.yml` release watcher (hourly GitHub workflow installed on `main`, future private runner migration tracked by [issue #48](https://github.com/manufact-test/nomusic/issues/48)); additive signed pinned versions 5.86 / 5.102 / 5.121 / 5.126 / 5.127 and v2 catalogue while legacy v1 remains intact; visible red/yellow warning states for unsupported version, song source failure, disconnected/stale host; safe owner untouched until physical tests. No untested vendor build automatically published.

Green final CI: `43302843768` (four real signed 2026 temporary native Install/Restore), `43303386737` (GUI tests and live catalog v1/v2), `43303122284` (old pin immutability), `43302843825` (W81 0.24.27 candidate Inno in-place from 0.24.26 preserving login/DPAPI and unchanged native 0.24.25 audio). Candidate artifact `13982362622`, SHA256 `87CDEBDF1C0B448ECE11C71525B4C2DDA6BCE40A662FC3768E495B485CA07D8D`. Still requires owner audible real-world QA; not a production sign-off. Hourly scheduling not yet observed in wild; confirm after first cron event.

---

# W80 Windows vendor-update auto-reconnect candidate 0.24.26 — CI GREEN, OWNER BASELINE QA FIRST (12 NOV 2026)

Owner reported Windows **0.24.25 "вроде бы работает"**, and intends to check real music tomorrow. **Do not disturb that working installation.** For future Yandex updates W80 isolated branch `experiment/windows-w80-vendor-update-auto-reconnect-20261112` has a complete data-only reviewed compatibility feed, exact Authenticode+YANDEX LLC publisher+EXE/ASAR hashes, previously ACTIVE→official vendor overwrite detection and one-click next Start auto-reconnect, immutable old originals, and safe refusal of unsupported/partial updates. It does NOT bypass unknown future versions.

Exact doc: [W80-VENDOR-UPDATE-RECONNECT-20261112.md](./W80-VENDOR-UPDATE-RECONNECT-20261112.md). Remote reviewed compatibility feed: branch `support/windows-yandex-compatibility`, `windows-companion/w24/compatibility/official-yandex-builds-v1.json` (only signed proven Yandex 5.127.0 initially). **New builds require independent proof before feed update, not a new CELIKOM EXE.**

W80 Windows CI genuine official 5.127.0 lab PASS [43293978441](https://github.com/manufact-test/nomusic/actions/runs/43293978441), full W80 Inno GUI-only 0.24.26 over 0.24.25 **PASS** [43294151762](https://github.com/manufact-test/nomusic/actions/runs/43294151762). Official installer artifact [13977289582](https://github.com/manufact-test/nomusic/actions/runs/43294151762/artifacts/13977289582), SHA256 `1AE9698109AAAA01A65D3409CD8CD95186274277AE5A76C925AA455E0C1FC849`. Same native host/renderer byte-for-byte as W79 stable. Owner install is **not** required until audio baseline 0.24.25 has been listened to, and W80 physical QA remains pending. Old issue #44 should stay OPEN until owner confirms real native Active/audio.

---

# W79 emergency recovery 0.24.25 — CI GREEN, OWNER QA STILL PENDING (12 NOV 2026)

**FIRST PRIORITY ONLY:** fix broken CELIKOM Windows 0.24.24 on owner's signed Yandex 5.127.0; no new release planning. Surgical recovery code in `experiment/windows-w79-upgrade-transaction-recovery-20261112`; authoritative evidence + safety restrictions + owner steps in [W79-SIGNED-YANDEX-51270-OWNER-RECOVERY-20261112.md](./W79-SIGNED-YANDEX-51270-OWNER-RECOVERY-20261112.md). The initial issue is [#44](https://github.com/manufact-test/nomusic/issues/44), **KEEP OPEN UNTIL OWNER TESTS**.

**Important success**: exact signed YANDEX LLC 5.127.0.r22015925 vendor EXE and ASAR verified, native ASAR patch staged on real official bytes and full simulated owner `RESTORED + updated vendor 5.127` to CELIKOM Active, safe Upgrade, exact Restore tested on Windows CI [43289688797](https://github.com/manufact-test/nomusic/actions/runs/43289688797) PASS. Full 0.24.24→0.24.25 Inno inplace install, saved DPAPI and native module verification, original Yandex untouched CI [43289538835](https://github.com/manufact-test/nomusic/actions/runs/43289538835) PASS. Candidate EXE artifact [13976688090](https://github.com/manufact-test/nomusic/actions/runs/43289538835/artifacts/13976688090), SHA256 `6CF6A9BB3FCF82386C9E4E1E2A880C682854B6672B8BE167AD366846D08AE79C`.

**Current physical owner status:** not yet confirmed. Owner should install candidate over existing 0.24.24, not uninstall Yandex, preserve snapshots/session, press Start/approve native integration, confirm Active 0.24.25 and real audio. If mismatch, fail closed; do not force unknown host files. Only afterwards investigate problem songs. Never claim CI proves physical owner music plays.

---

# URGENT FIRST READ — W78 OWNER WINDOWS 0.24.24 BROKEN AFTER UPDATE (12 NOV 2026)

**TOP PRIORITY: repair previously-working Windows CELIKOM. DO NOT plan a new release, rewrite architecture, touch extension/server/Android, or ship W77. STATUS: NOT FIXED.**

**Full authoritative handoff with REAL owner diagnostic:** [`docs/windows/W78-OWNER-YANDEX-51270-UPGRADE-BLOCKER-HANDOFF-20261112.md`](./W78-OWNER-YANDEX-51270-UPGRADE-BLOCKER-HANDOFF-20261112.md). Read it *before* coding. Current GitHub incident [#44](https://github.com/manufact-test/nomusic/issues/44).

Owner's real `CELIKOM-YANDEX-CHECK.txt` confirms:
```text
APP_VERSION=0.24.24.0
YANDEX_EXE_VERSION=5.127.0.r22015925
INTEGRATION_ASSET_VERSION=0.24.24
MANIFEST_STATE=RESTORED
ORIGINAL_EXE_BACKUP_HASH_OK=True
ORIGINAL_ASAR_BACKUP_HASH_OK=True
CURRENT_EXE=CHANGED_OR_UNKNOWN
CURRENT_ASAR=CHANGED_OR_UNKNOWN
HOST_PAIR_RESULT=UNRECOGNIZED_CHANGE_NO_AUTOREPAIR
2026-11-12T15:36:16.593Z|NATIVE_UPGRADE_REQUEST
2026-11-12T15:36:22.622Z|NATIVE_RESTORE_OK
2026-11-12T15:36:24.167Z|NATIVE_UPGRADE_FAILED
2026-11-12T15:36:33.620Z|START_HOST_PREFLIGHT_BLOCKED
```
**Interpretation:** W77 EXE 0.24.24 over previously working W76 0.24.23 led Start to successfully remove prior native integration but fail installing new. The CURRENT Yandex is now **5.127.0**, while native installer accepts only 5.126.1 and its exact baseline SHA. Both current EXE/ASAR are changed relative to verified saved original and applied hashes. Backup ORIGINAL bytes verify; do not mistake RESTORED manifest for current original files, and **do not forcibly restore or overwrite changed/new-version files**. Exact time/cause of 5.127.0 update is not yet proven. Direct EXE install lacks the in-app `--complete-update` ticket path; old CI did not test active Yandex upgrade. Reinstalling CELIKOM 0.24.23 alone won't make Yandex 5.127 supported.

**Immediate task:** based on these already obtained facts, inspect `NativeIntegrationManager.cs`, `PairRecovery.cs`, `MainWindow.cs`, `StartupHostPreflight.cs`, `CELIKOM.iss`. Make exact safe reproduction and transaction-like repair in a **new** isolated branch; preserve backup, DPAPI, no original Yandex deletion, no unsupported-version bypass. Owner must verify actual current Yandex connectivity before declaring resolution. No more diagnostic ZIP requests absent specific new need. Previous working baseline `backup/windows-w77-pre-kishlak-incident-20261112` / W76 0.24.23. Broken W77 **DO NOT INSTALL**.

---

> **W77 FINAL INPLACE CI PASS:** [43242885632](https://github.com/manufact-test/nomusic/actions/runs/43242885632): exact owner-installed W76 0.24.23 exe hash `CC3711E3...` → W77 0.24.24 exe hash `E0E3A7BC...`. Saved DPAPI session hash and decrypt unchanged, installed host.cjs/renderer.js both updated, only one AppId/uninstaller, vendor Yandex folder untouched. No actual owner's audible Kishlak proof yet.

# LATEST — W77 KISHLAK «САМЫЙ ЛУЧШИЙ ДЕНЬ» PARTIAL ORIGINAL, 12.11.2026

Owner was running installed Windows 0.24.23/native 0.24.23. Current approved catalog row for Yandex track **102494056**: Kishlak «Самый лучший день», `approved active`, asset #65, duration 93,336ms vs original 93,250ms; read-only CI https://github.com/manufact-test/nomusic/actions/runs/43240364480. In owner's 2026-11-12T14:35:02 UTC diagnostic: `SOURCE_BATCH_REQUEST` → `LOCAL_HTTP_TIMEOUT` → `RESOLVE_TRANSIENT` → `SOURCE_RECOVERY_SCHEDULED`; no `SOURCE_RECOVERY_RETRY` or native resource #65 GET afterward. **W76 failed to retain a transient prefetch miss until the song actually became current**; the immediate retry's guard cancels it because the preceding song was still playing. This correlates with original censorship/silence heard around 1min, though decoder-audible content is not independently observed.

**W77 fix** in branch `experiment/windows-w77-kishlak-audio-path-20261112`, new version **0.24.24** GUI and native module. `deferred-track-recovery.mjs` retains only exact failed track for <=12min/12 IDs and promotes only after W60 current-player ID matches, then W76 bounded signed-source re-resolve and in-place Yandex reload; Stop/logout/account change cancel; background failures don't reschedule forever. W60 guards expected current ID, native diagnostics throttled 10s to preserve owner evidence. No new player, no audio assets or server writes. Real doc `docs/windows/W77-KISHLAK-DEFERRED-RECOVERY-20261112.md`.

**CI:** Main 0.24.24 release [43241899043](https://github.com/manufact-test/nomusic/actions/runs/43241899043) SUCCESS, 87 native tests, .NET and installer PASS, W77 EXE SHA256 `E0E3A7BC3ED8D0C194471A2BCAECD88187A5A53567F76CD777346E2AD5AF4068`. Previous accepted W76 installer file SHA256 `CC3711E3A2D7933838D429A2FF5F18C961E5C673115ED1989DC9B4FFCC453175` from [43209453291](https://github.com/manufact-test/nomusic/actions/runs/43209453291). Separate W76→W77 inplace proof [43242885632](https://github.com/manufact-test/nomusic/actions/runs/43242885632): check final status. First attempt failed due incorrectly pinned older W76 intermediate SHA, NOT code.

**Immediate next action:** owner installs W77 EXE *over* 0.24.23 (no uninstall), accepts normal Yandex native integration refresh/restart if prompted, checks both version numbers 0.24.24, plays Kishlak «Самый лучший день» minute 1 and compares to browser extension. Cannot claim audible fix without owner's acceptance. Collect new diagnostics if still censored. Backup before W77: `backup/windows-w77-pre-kishlak-incident-20261112` SHA `9e4fd1d6e56e8e102c4a244a0e46fc6ffdf191fc`; final W77 backup will be `backup/windows-w77-02424-kishlak-deferred-recovery-ci-green-20261112`.

---

# LATEST — W76 Windows track-specific replacement failures: 12.11.2026

**Owner observations:** 0.24.21 / native 0.24.20 falsely says CELIKOM works while «ты» — тринадцать карат and «Биг сити лайф» — Триагрутрика play original/censored audio. Production catalog has active approved replacement #56 for Yandex 106040459 and #37 for Yandex 40371622. First song had local 1 s bridge timeout and grant miss. Second song log proves expired previously approved signed media URL, genuine 403, then fresh 206 and SOURCE_MAPPED; 206 does NOT prove audible replacement. Existing UI confuses global enabled status with audible track success.

**W76 implemented + green CI:** 0.24.23 branch `experiment/windows-w76-track-parity-audit-20261112`, source, bounded background re-resolve for transient misses, exact-current-only Yandex source refresh for expired signed native 403 (one cycle/min per ID), truthful recovering/error/unverified UI statuses. [Final successful Windows build CI 43209453291](https://github.com/manufact-test/nomusic/actions/runs/43209453291), artifact `CELIKOM-W76-TRACK-RECOVERY-UNSIGNED`; installer is an in-place upgrade, not yet owner-audibly-tested. **Do not claim the music fixed until owner plays both songs on W76.** Full report: `docs/windows/W76-TRACK-PARITY-RECOVERY-20261112.md`. Unmodified input backup `backup/windows-w76-pre-track-specific-audit-20261112` (94a743d); do not push these changes into W75/stable without owner acceptance. No server, library, production DB, Android or browser extension modifications.

---

# FIRST READ — W75 0.24.22 FIXED DISAPPEARING DIAGNOSTICS (11.11.2026)

**Latest owner complaint:** CELIKOM Windows disconnected during listening, automatically resumed only after ~60–90 sec, then owner-only diagnostics button vanished on click. Physical disconnect's root cause **NOT YET KNOWN**; must obtain current local log files from the owner before touching network/audio/reconnection timing.

**Confirmed independent GUI bug:** old `RefreshDiagnosticsAccessAsync` clears the button before every `auth/me` probe; `CopyDiagnosticsAuthorized` catches any exception (temporary VPN/timeout included) and treats it as revoked authorization. This is why owner's button vanished. This is NOT proof the remote server revoked staff privileges.

**W75 fix:** `DiagnosticsAccessRecovery.KeepButtonOnFailure` retains *visibility only* after prior verified owner permission for same signed-in origin/installation/email and transient error; export STILL requires fresh successful online `auth/me`. 401/403, logout, actual denial, other users never bypass. At temporary click failure shows `Нет связи · повтори` instead of hiding. `DiagnosticLog.Record` now independently writes bounded safe incident markers (connection lost/recovery etc) to `%LOCALAPPDATA%\CELIKOM\Windows\incident-events.log(.1)`; no token/email/URL/raw error content. Owner TXT export also includes retained last 7 days (max 1000 and size capped). **Already happened outages (before 0.24.22):** owner may still have `companion-events.log(.1)` and `native-events.log(.1)` in same directory. DO NOT ask for `session.dpapi` (secret saved login). Do not assert actual outage cause without them.

**Version:** Windows 0.24.22 (GUI-only), branch `experiment/windows-w75-diagnostics-resilience-20261111`. Original backup `backup/windows-w75-pre-diagnostics-resilience-20261111`; original W74 0.24.21 CI 43085966611. Main authoritative report `docs/windows/W75-PERSISTENT-DIAGNOSTICS-02422-20261111.md`. No music/native scripts/server/backoffice/extension changes.

**Verified CI:** [43091527029](https://github.com/manufact-test/nomusic/actions/runs/43091527029) SUCCESS; Windows .NET 154/158 contract checks (158 including ZIP), 16 native image contracts, genuine 0.24.21→0.24.22 reinstall in place with DPAPI same user and identical 0.24.21 native asset hashes, no files Yandex touched. EXE SHA `ECEA2166B087702D5A66590130A6D8DC647E9DB8E33F2E7B0C5063469DBA4FCA`. Download zipped `CELIKOM-W75-PERSISTENT-DIAGNOSTICS-UNSIGNED` from CI run 43091527029 and run installer once OVER existing version. No uninstall.

**Next action:** owner to send original actual logs **now** from AppData; analyze whether network/entitlement response, bridge/native status, or Yandex itself caused the 1–1.5 min drop. Do NOT mix this independent issue with the proven disappearing button bug. Wait for owner's physical 0.24.22 verification before claiming issue fixed in their environment.

---

# FIRST READ — W74 0.24.21 START-RACE / TRANSIENT REQUEST PATCH, CI SUCCESS (11.11.2026)

**Owner's latest bug:** 0.24.20 first click «Старт» showed false modal «Установленная версия Яндекс.Музыки пока не поддерживается», second click generic «Не удалось проверить доступ на сервере», third click correctly prompted open Yandex and worked. W74 addresses exactly these, preserving music/entitlement/native code.

**W74 branch:** `experiment/windows-w74-start-preflight-retry-20261111`.
**Full report:** `docs/windows/W74-START-PREFLIGHT-RETRY-02421-20261111.md`.
**Authoritative CI:** [43085966611](https://github.com/manufact-test/nomusic/actions/runs/43085966611) SUCCESS — .NET 10 win-x64 warnings-as-errors, 147 W15 contracts incl HostPreflight/one retry/no retry on 401/403/429/cancel, 16 native image contracts, complete Inno Setup and verified existing-owner W72 0.24.20 → W74 0.24.21 in-place upgrade. Old W72 setup SHA pinned; DPAPI saved sign-in preserved and decryptable, installed native host.cjs/renderer.js identical SHA, same AppId/no duplicate uninstaller; Yandex folder untouched. Unsigned installer SHA256 `2AB54A9B51D7C2E908EE4DBE537FDD4E58840907D1D6A1D5F2AE07FD4AB1CCA2`.
**Artifact:** Actions run 43085966611 → Artifacts → `CELIKOM-W74-START-PREFLIGHT-RETRY-UNSIGNED` → `CELIKOM-W74-START-PREFLIGHT-RETRY-UNSIGNED.exe`. Requires a **single in-place update** from installed 0.24.20, never uninstall, never repatch Yandex just for this GUI fix. No server/php/admin/Android/extension/native audio changes, no fake success on network failure.
**Safety rollback:** W74 pre-work branch `backup/windows-w74-pre-start-guards-02420-20261111`; original W72 accepted 0.24.20 code `66ffb6348f821416adabb9de4ce110adef1d5b7b`; original W72 installer Actions 42998876460. W74 final exact backup recorded by branch `backup/windows-w74-02421-start-race-retry-ci-pass-20261111`.
**Next action:** owner installs W74 build on own PC and presses Start **once**. This physical result remains **not yet verified**. If failure remains, get hidden support diagnostic; don't change music playback, native scripts, or active Hostinger release speculatively. Only change confirmed problem.

---

> **ФИНАЛЬНЫЙ РЕЗУЛЬТАТ НА ТОЧНОМ ДЕЙСТВУЮЩЕМ PHP:** [GitHub Actions 43006529881](https://github.com/manufact-test/nomusic/actions/runs/43006529881) — **SUCCESS**. Через SSH read-only скопированы исключительно 8 актуальных PHP-файлов `browser-support-076-b807cd691074` во временный CI runner, сверены хеши Application, SupportService, SupportAdminView и SmtpMailer. В `celikom_test` на этом точном серверном коде прошла цепочка Windows `general+diagnostics` → приватный JSON и тикет в админке → настоящий `/admin/support/reply` → Gmail SMTP → **реальный Inbox пользовательского alias**. Отдельно Inbox уведомления поддержки, идемпотентность и song без обязательной почты. Production backend/DB не менялись, клиент не пересобирался. Этот запуск окончательно заменяет менее строгие предыдущие проверки на старом PHP snapshot.

# FIRST READ — W73 FINAL E2E CONFIRMED (2026-11-11)

**W73 support task complete; no Windows/server code fix necessary.** Full verified contract: Windows 0.24.20 `kind=general` with bounded hidden `diagnostics.platform=windows` → authenticated API ticket → owner-only downloadable sanitized JSON in admin → actual `/admin/support/reply` with CSRF → real SMTP → customer email in Gmail **INBOX**. Independent disposable MySQL + synthetic private Gmail alias, exact final CI [43005996273](https://github.com/manufact-test/nomusic/actions/runs/43005996273) SUCCESS; also [43005920992](https://github.com/manufact-test/nomusic/actions/runs/43005920992) SUCCESS. Two authentic live general support notification emails verified 2/2 in production support Gmail INBOX [43004471837](https://github.com/manufact-test/nomusic/actions/runs/43004471837). Song still no mail; retries are idempotent, admin JSON private. 

**Full report:** `docs/windows/W73-END-TO-END-REPLY-GMAIL-RECEIPT-20261111.md`. No production changes and no 0.24.21 installer. Windows original `66ffb6348f821416adabb9de4ce110adef1d5b7b` and actual shared server unchanged; no need to contact owner for more information. Do not interpret this as an automatic customer receipt feature: client email follows actual admin reply only. End-of-W73 Git exact backup recorded in final W73 doc/branch.

---

# FIRST READ — W73 LIVE MAIL VERDICT (11.11.2026): real Windows general notifications found in Gmail Inbox

**Authoritative new report:** `docs/windows/W73-LIVE-MAIL-DELIVERY-AUDIT-20261111.md`. Verified actual active release `browser-support-076-b807cd691074`; Windows 0.24.20 source `66ffb6348f821416adabb9de4ce110adef1d5b7b` unchanged. Two real general notification emails marked SMTP `sent` were both independently FOUND in the configured Gmail **INBOX**, after exact live-vs-GitHub SMTP identity match: CI https://github.com/manufact-test/nomusic/actions/runs/43004471837. Independent real SMTP sent both support/general and admin-reply probes: CI 43003487354; separate Gmail receipt proved: CI 43004186705; prod read-only mail/ticket audit: CI 43004088750. Recent real DB: two admin replies `sent`; their recipient inboxes aren't accessible. Two song cases correctly have `mail_required=0`.

**Do not fix a nonexistent Windows or support SMTP bug.** Browser and Windows do NOT automatically email customers upon creating general tickets; support receives the initial mail, customer email comes only after an admin reply. Owner's missing expected mail may refer to another mailbox or customer receipt, but this explanation is not proven without owner confirmation. Existing support notifications are NOT lost; real Gmail inbox verified 2/2. No Windows EXE, PHP production release, admin UI, music, subscription or DB changed. W73 added only protected CI checks/docs. Preserve all existing backup branches, especially `backup/windows-w73-before-mail-chain-audit-20261111` and W72 compiled original.

---

# FIRST READ — W73 TASK HANDOFF (2026-11-11): Windows ordinary support EMAIL not confirmed

**Owner's latest real-world feedback:** Windows 0.24.20 **song-problem diagnostics arrive correctly**, but in an **ordinary support message the expected email does not arrive**. The owner asked for a **precise TZ and transfer to the NEXT CHAT**, not for speculative quick patches in this one. **This is an OPEN defect, NOT fixed.** No Windows code/installer/server changed for W73 yet.

**MAIN CURRENT TZ:** `docs/windows/W73-TZ-WINDOWS-GENERAL-SUPPORT-EMAIL-AND-DIAGNOSTICS-PARITY-20261111.md`. Read it in full FIRST. Then `docs/support/SUPPORT-DIAGNOSTICS-CONTRACT-20261111.md` and `docs/decisions/DESKTOP-SUPPORT-ATTACHMENTS-20261111.md` from extension/server implementation.

**Critical verified distinction:** Browser 0.4.76 general POST uses `support_diagnostics`; Windows 0.24.20 general POST uses `diagnostics:{platform:"windows"}` — active PHP `Application.php` explicitly accepts BOTH. Its `SupportService` schedules an initial **general** email to `mail_from`/support mailbox; after an **admin reply**, user email receives the response. There is **NO automatic end-user email receipt** on creation in the existing browser contract; **song does not require mail**. UI `Сообщение отправлено` means API returned successfully, **not SMTP delivered**. Server records `support_messages.delivery = pending/sending/sent/unknown`; live SMTP wasn't tested by prior extension CI, because production QA disabled sending. Check actual live current release/database ticket and status, authorized SMTP pipeline and inboxes before changing any code. Do not assume the problem is Windows versus SMTP; do not leak account/SMTP credentials in logs.

**Current known good Windows source:** exact compiled SHA `66ffb6348f821416adabb9de4ce110adef1d5b7b`; `backup/windows-w72-02420-extension-anti-drop-and-support-ci-green-20261111`. Branch `experiment/windows-w72-extension-anti-drop-guards-20261111` includes this handoff docs. CI Windows/server https://github.com/manufact-test/nomusic/actions/runs/42998876460 ; Windows 0.24.17→0.24.20 upgrade CI https://github.com/manufact-test/nomusic/actions/runs/42999441879 . Preserve working installed W72 and owner-accepted W69. Browser/server source: `feature/desktop-support-attachments-20261111` and `feature/server-general-support-attachments-20261111`. Last documented active live release: `browser-support-076-b807cd691074` — verify current anew. **Never upload old Windows-branch PHP over live browser team's server.**

**Acceptance:** one ordinary Windows ticket, private owner-only JSON in admin, one working inbound general email to support mailbox, one real admin reply email to user (NOT automatic customer acknowledgment), stable UUID retry/no duplicate, song report unchanged, safe and transparent delivery failure. Return to owner only with verified root cause, solution, exact backup, and real proof; if only SMTP/server is faulty, DO NOT release a meaningless new Windows EXE.

---

# FIRST READ — W72 0.24.20 Windows support diagnostics + extension-derived anti-drop safeguards (2026-11-11)

**Full authoritative handoff:** `docs/windows/W72-EXTENSION-ANTI-DROP-GUARDS-02420-20261111.md`.

Owner corrected speech-to-text: wanted a review of **browser extension** anti-drop design, **not Android**. The owner wants **one** Windows installer with both hidden automatic support diagnostics and reconnect fixes. Completed in W72 0.24.20, isolated from accepted W69 0.24.17.

- Real W69 0.24.17 diagnostic `Вставленный текст(20261111-090013).txt` proved Windows itself switched off on an unsuccessful entitlement check at 08:59:21Z and owner manually restarted at 08:59:39Z. Three reported drops, but only that instance is individually proven.
- Auto hidden 15-minute/64-event allowlisted diagnostics are included in both general and song support messages. W72 fixed the earlier 1600-line truncation so an incident 13 minutes earlier survives 2500+ native poll messages. Live backend/admin already updated by extension team; **do NOT deploy W72's older inherited PHP to Hostinger**.
- Transient GET network failures: bounded retry, 5s suspended/15s normal recheck, fresh no-cache/Connection:close GET after VPN route problems, network-address-change hint only accelerates recheck. Replacement remains disabled until an **explicit new allowed server entitlement**; 401/403, expired entitlement, manual Stop, sign-out and account changes never auto-resume. Concurrent token-refresh session resurrection fixed with lock/identity guard, with delayed-401/Logout tests. More granular privacy-safe failure logs.
- Browser extension source used: `extension/src/shared/read-recovery.ts`, `extension/src/background/{service-worker,tab-recovery,controller-bootstrap}.ts`, `extension/src/auth/auth-broker.ts`, `extension/src/player/{player-bridge,replacement-controller,fail-open-controller,original-audio-guard}.ts`. Browser audio guard and heartbeat are NOT directly portable because Windows native host lifecycle differs; original native audio/pause/seek/next and Yandex files unchanged.
- Exact compiled code **`66ffb6348f821416adabb9de4ce110adef1d5b7b`**, backup `backup/windows-w72-02420-extension-anti-drop-and-support-ci-green-20261111`. Current working branch `experiment/windows-w72-extension-anti-drop-guards-20261111` includes later docs and independent upgrade workflow.
- Complete 0.24.20 Windows + disposable MySQL support CI **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42998876460; actual owner W69 **0.24.17 → W72 0.24.20** DPAPI-preserving Yandex-untouched one-app upgrade **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42999441879. Native contract tests **138 PASS**.
- One private unsigned 0.24.20 EXE, **43,542,513 bytes**, SHA256 `1cc9321d8aeb1482a8c23aad8cc1285bb1896f81402ea60c6692b483c180ccd9`. GitHub artifact `13845601337`, familiar Library `/CELIKOM/Windows/CELIKOM-Windows-Setup.exe` (stable `libfile_9cef6593f5e88191a339835933fbc550`) and versioned `/CELIKOM/Windows/CELIKOM-W72-SUPPORT-ANTI-DROP-GUARDS-UNSIGNED.exe` (`libfile_01af2848721481918220f25bdf06d1d5`). Both Library versions SHA/byte verified. Previous versioned 0.24.17 installer and backups preserved.
- Await owner's physical test on Windows: 20–30 min music/MyWave, pause/seek/Next, manual Stop, optional VPN switch; send general + song test support messages and verify hidden admin JSON. CI success does not prove owner-device intermittent audio is fixed. No public release/signing or payment-provider work yet.

---

# FIRST READ — W70 Windows 0.24.18 automatic private diagnostics attached to every support message (2026-11-11)

**AUTHORITATIVE:** `docs/windows/W70-AUTO-SUPPORT-DIAGNOSTICS-02418-20261111.md`. Owner confirmed Windows 0.24.17 works, then noted standard support reports lacked automatic hidden diagnostics. W69 0.24.17 was general TEXT ONLY; song had numeric track/bridge booleans; full developer log was manual + staff-only. This is now implemented **on an isolated W70 branch**, and requires separate backend rollout before customer reports can be seen in live admin.

- Branch `experiment/windows-w70-auto-support-diagnostics-20261111`; exact compiled source SHA `3c01da7e9edd4acd2e4f74f3a43801b081c49f1d` (immutable backup `backup/windows-w70-02418-auto-support-diagnostics-ci-green-20261111`). No changes to owner-accepted W69 backup `backup/windows-w69-02417-uninstall-login-choice-ci-pass-20261110`.
- Customer support send *automatically* includes allowlisted last 15 min / 64 event Windows diag, status and native/Yandex versions. Both **general** (`diagnostics`) and **song** (`report.diagnostics.windows`). No credentials, email, raw logs, signed audio URLs, local paths. Developer diagnostic UI still not shown to non-admin users. Retry UUID caches one immutable snapshot. Server independently strips unknown fields, stores only within private `report_json`; email/visible message is unchanged. Owner/moderator can view and download JSON; ordinary customer general thread is not exposing report.
- CI real Windows and disposable MySQL **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42984907950 . Independent exact 0.24.17→0.24.18 DPAPI-preserving Windows upgrade **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42985581262.
- Exact **PRIVATE unsigned** 0.24.18 EXE `CELIKOM-W70-SUPPORT-AUTO-DIAGNOSTICS-UNSIGNED.exe`, 43,525,923 bytes, SHA256 `41822a4d09c9ca225ef8407a0209abd919e33788c7fe6abc6e6e87eed4233634`; Library `/CELIKOM/Windows/`, file `file_00000000fec481f48a15887605c4221c`, Library `libfile_ae404da954a88191999ecc7102b4dcba`; Library re-download matches original CI. The **stable** `CELIKOM-Windows-Setup.exe` Library alias still points to W69 0.24.17, intentionally not overwritten before owner's real PC test.
- CRITICAL: **PHP server changes staged ONLY in GitHub; NOT deployed to production**. Tests used disposable MySQL only, no real customer data; older production PHP may IGNORE new diagnostic fields, so live admin will not see them until safe host deploy/backup/rollback. No new DB migration required if 017 present. Owner must approve safe production backend rollout, then owner PC acceptance/real support ticket. Do not assert end-to-end production success yet.
- Billing/subscriptions and public site download/signature remain deferred per owner request. Never modify Android, original Yandex, or owner accepted audio, and don't restart implementation from zero.

---

# FIRST READ — W69 Windows 0.24.17 optional saved-login deletion checkbox; private owner trial ready (2026-11-10)

**READ FIRST:** `docs/windows/W69-OWNER-02417-UNINSTALL-SESSION-CHOICE-CI-PASS-20261110.md`. Owner requested user-selectable **«Также удалить сохранённые данные входа»** on CELIKOM *uninstall*, because uninstall/reinstall W68 0.24.16 correctly kept a prior encrypted `%LOCALAPPDATA%\\CELIKOM\\Windows\\session.dpapi` and silently restored the prior login. Login persistence is expected, **not** unlimited rights. Owner will install W69, uninstall with checkbox checked, reinstall and confirm a real fresh sign-in.

- Branch `experiment/windows-w69-uninstall-login-choice-20261110`; exact built W69 source `da046739d1be008dbc1a9db00bce29ce8867a635` frozen `backup/windows-w69-02417-uninstall-login-choice-ci-pass-20261110`. No Windows audio/entitlement algorithm changes from W68; version 0.24.17 with same AppId, native and updater metadata.
- Inno Setup 6.7+ `CreateCustomForm(480,194,True,True)` shows unchecked checkbox with Continue/Cancel. Normal uninstall with opt-in deletes **only** current Windows user's `session.dpapi`, after safe native restoration; default leaves it intact. Silent uninstall always keeps login unless explicit `/CELIKOMREMOVELOGIN=1`. Other app data and Yandex untouched. Cancelling does not restore/edit Yandex or delete session.
- W69 complete real Windows CI https://github.com/manufact-test/nomusic/actions/runs/42870959621 **SUCCESS**; live Windows silent uninstall both modes using actual DPAPI: preserved by default, deleted on explicit opt-in, unrelated file retained. Inno native checkbox compiled but interactive mouse path **still awaits owner**.
- Independent exact 0.24.16→0.24.17 DPAPI-preserving one-AppId upgrade https://github.com/manufact-test/nomusic/actions/runs/42871865239 **SUCCESS**.
- Versioned private unsigned installer `CELIKOM-W69-UNINSTALL-LOGIN-CHOICE-UNSIGNED.exe`, size 43,528,746 bytes, SHA256 `010f3db747af38229bfa3e3a06b85145be71f61ad9743470c0ca6fcda2eeaf21`. Exact versioned Library path `/CELIKOM/Windows/CELIKOM-W69-UNINSTALL-LOGIN-CHOICE-UNSIGNED.exe`, ID `file_00000000cf7081f9a0493cf8c5af69db`; stable alias `/CELIKOM/Windows/CELIKOM-Windows-Setup.exe`, Library ID `libfile_9cef6593f5e88191a339835933fbc550`, updated backing file `file_00000000e9d88243a8c742ae8beec529`. Both downloaded back from Library, compared byte-for-byte against CI artifact.
- **Owner acceptance pending**: install W69 above W68 without clearing session; uninstall via Windows Settings, check checkbox; reinstall W69 and verify sign-in required; same old email NEVER gets second 3-day trial; test new verified owned email separately. Existing 0.24.15 and W68 baselines retained. The real merchant/payment and public website download readiness remain deferred and **NOT approved** per W68 docs. Do not invent public HTTPS URL and do not deploy production.
- Next work: await owner's real UI/first install results. Do not redo existing source or run production queries without explicit need.

---

# FIRST READ — W68 Windows 0.24.16 PRELAUNCH ENTITLEMENT PRIVATE CANDIDATE; PUBLIC LAUNCH BLOCKED (2026-11-10)

**AUTHORITATIVE:** `docs/windows/W68-COMMERCIAL-TRIAL-ENTITLEMENT-AND-LAUNCH-BLOCKERS-20261110.md`. Owner explicitly confirmed 0.24.15 W67 seems ideal on his actual PC, then asked to verify three-day trial, paid email subscriptions, promo/expiry, strong app/API access enforcement and offer a stable public download link before any real customers. We MUST NOT publish an unpaid-bypass or false paid-access release. Keep owner-approved 0.24.15 exact baseline and original Yandex intact.

- **W68 isolated commercial audit branch** `experiment/windows-commercial-entitlement-audit-20261110`. W68 0.24.16 exact PRIVATE unsigned installer source `0eeccb99af50003914adf488e9dff2bc0fc08759`; backup `backup/windows-w68-02416-private-entitlement-gates-ci-green-20261110`. W67 baseline frozen `backup/windows-w67-02415-built-ci-passed-await-owner-20261110` @ `5a1f5a3a81e0ae98909315ead137ca9a5260896b`.
- Fixed **missing Windows trial activation**: `POST /auth/activate` on Start/Connect; fail-closed for denied, expired, network errors; local 15s recheck while active, user/session switching guarded; signed audio must carry session `sid`. First login/read-only preview does not start trial, reinstall cannot reset MySQL user trial. Paid source/period and lifetime promo recognized if server confirms. Old audio algorithms and selector untouched.
- Staged server support `FEATURE_PAID_ENTITLEMENT` (default OFF), wired into entitlement/resolve/signed GET/Range/auth activation/promo; old private `API_TEST_TOKEN` bypass rejected in customer mode, sid-less audio forbidden. No live production/backend changes; no real payment provider connected.
- **SUCCESS** PHP + disposable MySQL 3day/paid/refund/token tests https://github.com/manufact-test/nomusic/actions/runs/42864505556 ; live public config READ-ONLY https://github.com/manufact-test/nomusic/actions/runs/42865291678 (auth/entitlement/replacements ON but **cannot verify paid billing**). Full W68 Windows 0.24.16 installer/real mouse/WinForms/native icon and ZIP CI https://github.com/manufact-test/nomusic/actions/runs/42864892275 **SUCCESS**. Independent DPAPI-preserving W67 0.24.15→W68 0.24.16 upgrade https://github.com/manufact-test/nomusic/actions/runs/42865607963 **SUCCESS**.
- **Private unsigned W68 EXE:** `CELIKOM-W68-SUBSCRIPTION-TRIAL-GATE-UNSIGNED.exe`, SHA256 `8f9455f4be4e750d1be6afa629d7d2a8519293e10f200281aaa21ebe23319665`, 43,526,871 bytes, Library `/CELIKOM/Windows/`, file `file_000000007d2882468a68cd15fdf2f4f9` library ID `libfile_54e7b98436f8819198eb15dabcb0b964`. Library re-download SHA/cmp verified. **No PUBLIC link; do not claim paid-ready.**
- **BLOCKERS:** no verified real merchant webhook/checkout or mapping existing paid emails to DB `users.id`, commercial feature not deployed, website public/stable download gate not approved, EXE/updates lack cryptographic publisher signing, real consumer SMTP/first install and pinned Yandex 5.126.1 compatibility not yet accepted. No real payments or real customer auth tests were performed. Stage11 payment test adapter is simulated. Owner trial of W68 still needed. Keep W67 rollback and W61 approved audio baseline.

---

# FIRST READ — W67 Windows 0.24.15 built/CI/upgrade PASS, awaiting owner-PC test (2026-11-10)

**READ:** `docs/windows/W67-OWNER-02415-SUPPORT-SELECT-LIFECYCLE-CI-PASS-20261110.md`. W67 Windows source is frozen at **`5a1f5a3a81e0ae98909315ead137ca9a5260896b`**, protected backup `backup/windows-w67-02415-built-ci-passed-await-owner-20261110`. Continue original repo `manufact-test/nomusic`, branch `experiment/windows-stop-lifecycle-20261110` (later docs/CI-only commits do not change built exe). Do NOT redo from scratch.

**Cause proven** on 0.24.14 with actual native Windows mouse-click in CI #42856421539: `ContextMenuStrip.Closed` disposed the dropdown *synchronously* while `ToolStripDropDown.OnItemClicked` still used its handle; fatal `System.ObjectDisposedException` exited process. Not just hypothetical layout re-entrancy. W67 defers disposal/selection until native event dispatch completes, bounds menu to compact control width, custom draws even highlight/text, adds keyboard arrows/Enter/Space via `IsInputKey`. Also removed hardcoded dropdown width 300. Support API unchanged.

**W67 real interaction CI** https://github.com/manufact-test/nomusic/actions/runs/42857977946 **SUCCESS** (24 physical mouse changes, 8 outside dismiss/reopen, arrow/Enter, category). **W67 full actual installer CI** https://github.com/manufact-test/nomusic/actions/runs/42858640960 **SUCCESS** (code/native tests, icons, PE, stage/security, installer + install/uninstall smoke). **Independent 0.24.14→0.24.15 same-AppId same-user DPAPI/host/Yandex preservation CI** https://github.com/manufact-test/nomusic/actions/runs/42859695926 **SUCCESS**.

**Direct owner candidate**: ChatGPT Library `/CELIKOM/Windows/CELIKOM-W67-SUPPORT-SELECT-GUARD-UNSIGNED.exe`, **SHA256 `c885262a5fedb15cfa05f930531e6ce706ee41c4cc4505e129496d104df6ffab`**, 43,534,754 bytes. Library roundtrip SHA rechecked. Library file `file_0000000042988243960d5afc1cdccc1b`, `libfile_7bbf7e9dd8f081919133c6c4982029fe`. GitHub artifact `13782839469`.

**NEXT:** Owner has NOT yet tested 0.24.15 on actual computer. Ask him to install over 0.24.14 without uninstall, click switch support kinds repeatedly, check no process exit/menu bounds/row alignment, support delivery (previous W66 had working admin delivery), login, audio Start/Stop/pause/seek/MyWave. Do not call it owner-accepted until he reports. DPI125% unverified. W66 rollback `backup/windows-w66-02414-built-ci-passed-await-owner-20261110` and audio baseline W61 must remain untouched. No Android Test.50, production or Yandex originals changes.

---

# FIRST READ — W67 P0 SUPPORT SELECTOR CRASH / WINDOWS 0.24.14 OWNER TEST (2026-11-10)

**URGENT NEXT ACTION:** Read `docs/windows/W67-SUPPORT-SELECT-CRASH-OWNER-HANDOFF-20261110.md` FIRST, then W66 document below. The owner **actually installed and tested W66 / 0.24.14** and observed a **new blocking regression: the entire Windows CELIKOM app exits while opening/changing `Вид обращения` inside `Связь с поддержкой`**. Two UI defects coexist: popup extends outside window to the right and active menu row/text is misaligned. This is **three issues, not just cosmetic**. Owner explicitly requested **NO code fixes now**, only this handoff, with the next chat to fix them as one block. This chat made **documentation-only commits**: **current 0.24.14 binary and exact frozen source are untouched**.

**Likely source:** `windows-companion/w15/Celikom.Companion/PopupOptionSelect.cs` — ContextMenuStrip hard minimum width (parent `_compactSupportKind.DropDownWidth = 300`), `SelectedIndexChanged` raises `LayoutCompact()` from `CompactPopup.cs` synchronously while menu item clicked, menu.Close() and menu.Closed => Dispose. The lifecycle/reentrancy is a HYPOTHESIS, not an established crash cause. Reproduce, log actual exception and add real mouse menu-item lifecycle tests. Existing screenshot harness only assigned SelectedIndex programmatically and missed this crash.

**Keep unchanged:** repository `manufact-test/nomusic`, working branch `experiment/windows-stop-lifecycle-20261110`, **W66 exact backup** `backup/windows-w66-02414-built-ci-passed-await-owner-20261110` @ `6b4a8088b299f802366bc85e3ff28515930336e4`; W65 rollback `backup/windows-w65-02413-built-ci-passed-await-owner-20261110` @ `5ce1b6ebdecf9a49259d29241e5aa29619d2f429`. No new W67 installer yet. W66 remains the built owner candidate: GitHub https://github.com/manufact-test/nomusic/actions/runs/42846306058, Library `/CELIKOM/Windows/CELIKOM-W66-COMPACT-UX-BRAND-UNSIGNED.exe`, SHA256 `2028f53113eef88cfc65b4181336fc9db723a7360a051a551b280863668493f9`.

**Next developer:** correct all 3 support selector defects in a single substantial W67 / 0.24.15 build; preserve working support-to-admin API and DPAPI session, native Start/Stop, pause/seek/MyWave, Yandex originals, production, and Android Test.50. Validate real dropdown click/selection/close and keyboard navigation (not screenshot alone); run installer and in-place 0.24.14→0.24.15 CI proof; publish verified exact EXE into ChatGPT **Library → CELIKOM → Windows** and return a direct Library **file card**, not a sandbox guess. Don't declare user-PC crash resolved until owner validates. Owner prefers no small status updates: work in a large block and report when substantial/full.

---

# FIRST READ — W66 Windows 0.24.14 PRIVATE OWNER TRIAL (2026-11-10)

**Authoritative next handoff:** `docs/windows/W66-OWNER-02414-ICON-METADATA-AND-DYNAMIC-UI-20261110.md`. Continue existing `manufact-test/nomusic`, branch `experiment/windows-stop-lifecycle-20261110`. This chat completed W66 source and build; user **has not tested W66 on real PC yet**. Do NOT begin anew or change music engine/audio source logic.

**Fixed owner's confirmed bugs:** malformed JS RegExp stripped capital "D" (and other uppercase letters/digits) from artist/song labels in both vendor current-source reader and localhost host sanitation; both corrected and regression-tested (incl. kavabanga Depo kolibri, Unicode). Fixed support Send gap and on-demand feedback, promo gap and neutral placeholder, eliminated empty reserved upload area by measured title/note heights and conditional validation/progress, adjusted 7px status dot to align to text. Replaced Windows document icon in titlebar, taskbar, tray, installer with **exact official green C from extension/assets/icons**; deterministic ICO source script, PE and Inno embedding verified.

**W66 exact frozen built source:** `backup/windows-w66-02414-built-ci-passed-await-owner-20261110` @ `6b4a8088b299f802366bc85e3ff28515930336e4`. **Pre-W66 W65 backup:** `backup/windows-w65-02413-owner-final-feedback-pre-w66-20261110` @ `de08b9c5ef509811347771d2c044e635e15ad3d4`. W61 accepted-audio backup unchanged.

**CI SUCCESS:** W66 real UI screenshots/height and gap validation https://github.com/manufact-test/nomusic/actions/runs/42845448149; full W66 0.24.14 build/Node/native/source/installer/icon from exact frozen SHA https://github.com/manufact-test/nomusic/actions/runs/42846306058; independent synthetic same-user DPAPI 0.24.13→0.24.14 one AppId and vendor untouched https://github.com/manufact-test/nomusic/actions/runs/42846415169.

**Direct owner EXE:** `CELIKOM-W66-COMPACT-UX-BRAND-UNSIGNED.exe` 43,492,716 bytes, SHA256 `2028f53113eef88cfc65b4181336fc9db723a7360a051a551b280863668493f9`, GitHub artifact `13777993165`; ChatGPT Library `/CELIKOM/Windows/`, file ID `file_00000000a96c8243811ad4bc82387b4b`, lib ID `libfile_44cba65dcd248191a832c60c5f42ce3b`. **Round-trip sha and cmp exact**.

**NEXT:** Owner installs directly over installed 0.24.13, checks D in artist/title across popup and upload, icon taskbar/title/setup/tray, dot alignment, promo/support gaps, dynamic upload form, validates audio Start/Stop, pause, seek, MyWave no regressions. No public release, no claim of owner acceptance before actual testing; no Android Test.50, production, Yandex originals changes.

---

# FIRST READ — CELIKOM Windows W65 / 0.24.13 PRIVATE OWNER TRIAL (2026-11-10)

**READ FIRST:** `docs/windows/W65-OWNER-02413-ACCOUNT-SUPPORT-UX-20261110.md`. Continue existing Windows app in `manufact-test/nomusic`, branch `experiment/windows-stop-lifecycle-20261110`; do NOT create another app. User approved final batch of W64 0.24.12 UI fixes. W65 0.24.13 uses one bordered account accordion and one bordered support accordion, fully dark custom selectors and textarea, compact promo typography, actual API-backed opt-in benefits/referrals, 7px aligned status dot, 5px right-gutter scroll thumb. **All filename-based guessing and warnings removed** even for Unicode names; upload eligibility still checks actual audio format and duration. Never change W60 audio source reload/seek/pause/MyWave, original Yandex files, Android Test.50 or production.

**Immutable exact W65 built source backup:** `backup/windows-w65-02413-built-ci-passed-await-owner-20261110` @ `5ce1b6ebdecf9a49259d29241e5aa29619d2f429`. Pre-W65 backup `backup/windows-w64-02412-owner-last-ui-feedback-before-w65-20261110` @ `3cde12a3bb7ac439d621f9b8d8b3d065e0d16af1`. Accepted W61 audio baseline `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` @ `44e69d78b459ed512862819280ebdb8b3dbc7e7d`.

**SUCCESS:** actual WinForms screenshot, expanded account/support, promo/benefits, scrollbar, negative filename-heuristic tests https://github.com/manufact-test/nomusic/actions/runs/42838998161; full unsigned Windows 0.24.13 installer https://github.com/manufact-test/nomusic/actions/runs/42838998263; independent 0.24.12→0.24.13 same-user DPAPI, same app/uninstaller, untouched Yandex https://github.com/manufact-test/nomusic/actions/runs/42839920232.

**EXACT unsigned owner EXE:** `CELIKOM-W65-ACCOUNT-SUPPORT-UX-UNSIGNED.exe` 43,542,477 bytes, SHA256 `6d8f1ff5ca26260c5a3350e8d8adad8732b350ca412628f870c3889a51fb6574`; GitHub Actions artifact `13775480729`. ChatGPT Library `/CELIKOM/Windows/CELIKOM-W65-ACCOUNT-SUPPORT-UX-UNSIGNED.exe` (`file_00000000ce28824390eab48175e050fb`, `libfile_526fdf375cfc819182c18e1a29ed83d5`); byte-for-byte round-trip SHA reverified.

**NEXT ACTION:** Owner installs 0.24.13 over existing 0.24.12 without uninstalling or logging back in. Visually test account/promocode/benefits, support, scrollbar equal gutters, 7px indicator, no filename warning on bad-duration arbitrary-name MP3; then pause, seek, Start/Stop, MyWave. Do not claim W65 owner-tested or ready for public release before user's direct acceptance. Source is frozen since CI; new commits after source backup are docs/upgrade workflow only.

---

# FIRST READ — CELIKOM Windows W64 / 0.24.12 PRIVATE OWNER TRIAL (2026-11-10)

**READ FIRST:** `docs/windows/W64-OWNER-02412-UX-PREUPLOAD-SCROLL-20261110.md`. Continue existing CELIKOM Windows `manufact-test/nomusic`, branch `experiment/windows-stop-lifecycle-20261110`. User finished all screenshot feedback on actual 0.24.11 and requested one large integrated fix. W64 0.24.12 addresses fixed bottom version, smaller centered status dot, precise Yandex loading text, title/artist multi-line, active/native version status distinction, extension-like suggestion/upload UI, immediate red 1.5-second file-duration preflight with blocked send, filename warning, styled rights checkbox, stable gutters and real scrollable account/support/upload panels. **Native audio switching/reload remains unchanged.**

**Frozen source backup** `backup/windows-w64-02412-built-ci-await-owner-20261110` @ `12c0833dbe51d5f2b5970feedbecc2a4427b0edb`. Previous W63 source `backup/windows-w63-02411-built-ci-await-owner-20261110` @ `266beacfcfa524eeb9ecae91d44b9316ec257286`. Accepted audio W61 0.24.9 `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` @ `44e69d78b459ed512862819280ebdb8b3dbc7e7d`. Never rewrite backups.

**CI SUCCESS**: 9 real visual Windows snapshots/scroll/footer/red-error checks https://github.com/manufact-test/nomusic/actions/runs/42830887008, signed source/native W60 check https://github.com/manufact-test/nomusic/actions/runs/42831338168, W64 installer build https://github.com/manufact-test/nomusic/actions/runs/42831368648, **independent 0.24.11→0.24.12 same-user DPAPI, one app and untouched Yandex** https://github.com/manufact-test/nomusic/actions/runs/42831819681.

**Exact installer:** `CELIKOM-W64-EXTENSION-FINAL-UX-UNSIGNED.exe` SHA256 `c8e5dd395fdb7133a91f8418d0b910f97c84168111586166592ffac03144b5b7` (43,540,794 bytes). Library path `/CELIKOM/Windows/`, file ID `file_000000002c048246b2d291ac04157925` / library ID `libfile_9e5b773199b88191b695a8610f216c6d`. **Read-back hash identical**.

**NEXT STEP:** user installs over actual 0.24.11 without uninstall/relogin, checks gutter/scroll/footer/account/promocode, song title+artist and actual native-active status, wrong audio MP3 preflight immediately red with no server transfer, then checks pause/seek/Start/Stop/MyWave. W64 is NOT owner-tested and not publicly released. Potential remaining artist extraction depends on Yandex current-player metadata; no invented artist/title. Do NOT alter Android Test.50, production, original Yandex audio/player files.

---

# FIRST READ — W63 Windows 0.24.11 PRIVATE OWNER TRIAL (2026-11-10)

**READ:** `docs/windows/W63-OWNER-02411-EXTENSION-UX-TRACK-20261110.md`. Continue CELIKOM Windows in `manufact-test/nomusic` / `experiment/windows-stop-lifecycle-20261110`, **NOT a new app**. Owner explicitly rejected W62 0.24.10 UI while audio worked. New **0.24.11** addresses empty account and clipped support, no Original button, Start label, real status green approved/pending before showing contribution forms, song title/artist from current player when present, true startup feedback, proper compact widths and admin-only diagnostics. Do NOT claim pixels/features are fully identical before user test. No source edits after successful W63 build, just docs.

**W63 exact source backup:** `backup/windows-w63-02411-built-ci-await-owner-20261110` @ `266beacfcfa524eeb9ecae91d44b9316ec257286`; owner-accepted 0.24.9 audio backup `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` @ `44e69d78b459ed512862819280ebdb8b3dbc7e7d`; owner rejected 0.24.10 GUI snapshot `backup/windows-w62-02410-owner-ui-rejected-before-w63-20261110` @ `25101ccfb4fbb09e255e3b10a1664e8c69de4b6e`. **Leave all unchanged**.

**SUCCESS:** Installer https://github.com/manufact-test/nomusic/actions/runs/42824296777, Windows visual expanded account/support/green existing/upload https://github.com/manufact-test/nomusic/actions/runs/42824296883, independent **0.24.10→0.24.11 one-app same-user encrypted session + original Yandex untouched** https://github.com/manufact-test/nomusic/actions/runs/42824740871. Artifact id `13768535851`. File `CELIKOM-W63-EXTENSION-UX-TRACK-UNSIGNED.exe` SHA256 `591e76abfab8573770fb34c88cc809f85d175f1c1649b61abd8e3b95e0f5a276`, 43,543,132 bytes. Direct Library `/CELIKOM/Windows/` file ID `file_00000000850c81f4a77794566d9616c7`; downloaded round-trip and SHA rechecked.

**Next:** Owner must test real 0.24.11 app UX/title/green server statuses and audio pause/seek/Start/Stop/MyWave. Sound switching not modified; display metadata may fall back to Track ID and manual duration if Yandex does not supply these fields. No production, Android Test.50 or vendor-original changes. Never announce owner acceptance before actual test.

---

# FIRST READ — CELIKOM WINDOWS W62 / 0.24.10 PRIVATE OWNER TEST (2026-11-10)

**New authoritative handoff:** `docs/windows/W62-EXTENSION-PARITY-AND-OWNER-AUDIO-20261110.md`. User personally tested 0.24.9 and confirmed replacement, seek, pause, Start/Stop, NO audible click; delay remains around 0.36s dispatch + 0.74s official Yandex source reload. Owner diagnostic `1.zip` was actually read and analyzed. 0.24.9 approved audio baseline **frozen** at `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` SHA `44e69d78b459ed512862819280ebdb8b3dbc7e7d`.

**W62 built successfully, not owner-tested yet:** new compact native Windows layout matching actual extension screenshot hierarchy (302-ish px, no wide tabs), functional authenticated account registration/recovery, server-backed entitlement/promocode and support, typed song reports, contribution endpoints, passive current song ID. Source backup `backup/windows-w62-02410-built-ci-await-owner-20261110` @ `eb1c9f2e1de69091c14f0e275d99f000f94d4d00`. No native audio switching algorithm changes; W61 polling/reload retained.

**Verified build:** https://github.com/manufact-test/nomusic/actions/runs/42817316962 SUCCESS. **Visual anti-overlap and layout screenshot:** https://github.com/manufact-test/nomusic/actions/runs/42817228046 SUCCESS. **Independent same-app 0.24.9→0.24.10 DPAPI proof:** https://github.com/manufact-test/nomusic/actions/runs/42817785847 SUCCESS. **Exact file:** `CELIKOM-W62-EXTENSION-PARITY-UNSIGNED.exe`, EXE SHA256 `ed2dff94d3d59bc600432f7f9b826ecc13850778937944a07bc198dbee6a5cde`, Library `/CELIKOM/Windows/`, file `file_000000006a7481f4bd310f424f863a46`. Re-downloaded SHA verified. **Do NOT publish as owner-accepted yet**.

**Next:** let owner test UX and audio on 0.24.10. Known functional distinctions from browser extension: Return Original currently equals global Stop; upload asks duration seconds instead of inspecting audio automatically; real track ID shown, metadata title/artist not fetched. Do not misrepresent as pixel/feature identical; preserve all accepted sound paths and signed Yandex baseline. Production, Android Test.50 and original vendor files untouched.

---

# FIRST READ — CELIKOM Windows W61 / 0.24.9 PRIVATE OWNER CANDIDATE (2026-11-10)

**READ FIRST:** `docs/windows/W61-CONSUMER-UX-FAST-TOGGLE-OWNER-CANDIDATE-20261110.md`. Continue existing native Windows companion, NOT new app. Owner **personally confirmed 0.24.8 Start/Stop correctly changes the source of an already playing song**, but complains of delayed and sharp audible transition ("пшик"). Missing fresh diagnostic ZIP: user says it was attached, but it did not appear in available files. **Do not invent log evidence or claim click fixed.**

**W61 0.24.9 already compiled:** full CI **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42811326672; independent **0.24.8→0.24.9 same-user DPAPI one-app update SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42811784981; UI/Windows tests pass. Exact EXE `CELIKOM-W61-CONSUMER-UX-FAST-TOGGLE-UNSIGNED.exe`, SHA256 `71c656129d68d596439e242513242fe86acd47eb0b9c35a94e7fb469f934159d`. **Uploaded to ChatGPT Library** `/CELIKOM/Windows/`, library file `file_00000000a5d88246892f939fa3507c7c`; re-downloaded and checksum verified. Need owner's actual real-machine test, not another blind build. Start from current branch head, which adds docs only on top of successful W61 source.

**W61 UX:** full-width navigation, red Account until login, first-run login screen with email/password only, no visible API/dev clutter, diagnostics ONLY authenticated live-verified staff from exact Chrome extension email-hash allowlist, Start can connect/update installed native module with confirmation and automatically open Yandex if closed. Local state poll reduced from 600ms to 260ms. **No experimental volume fading**; signed source reload preserved until sound problem is causally researched. Preserve real owner 0.24.8 source backup `backup/windows-w60-0248-owner-toggle-pass-before-ux-20261110` @ `a2a0a719080e101bc38f81adf59bcb76a185450b` and owner accepted 0.24.7 backup. Never edit Android Test.50, production or vendor original signed Yandex.

---

# FIRST READ — CELIKOM Windows W60 / 0.24.8 OWNER TRIAL READY, NOT YET OWNER-TESTED (2026-11-10)

**Контекст:** Продолжение уже существующего CELIKOM Windows companion for the **real installed desktop Yandex.Music**, not a fork and not a second music player. Owner uses 0.24.7, personally confirms sound replacement + pause + seek + Next + MyWave all work great. Owner NOW wants **instant same-track Start/Stop** and **desktop GUI identical in style to real browser extension**. Owner asked previous assistant to STOP, save and hand off; **do not restart design or root-cause research from scratch**.

**Source repo:** manufact-test/nomusic; active experiment branch **`experiment/windows-stop-lifecycle-20261110`**; start from its latest HEAD, and this file. Read full `docs/windows/W60-LIVE-SOURCE-RELOAD-AND-EXTENSION-WINDOWS-UI-20261110.md` plus `docs/windows/W58-OWNER-0247-CONTROLS-PASS-STOP-LIFECYCLE-20261110.md` and W56 signed-query guard.

**Confirmed root behavior from owner's `CELIKOM-diagnostics-20261110-134519.txt`:** at 10:44:49 Stop genuinely turned native state OFF (renderer OFF 10:44:50); 10:45:05 Start genuinely turned it ON (renderer ON 10:45:06); but Yandex did NOT refetch the currently playing song's media source. Signed URL guard and HTTP206 continue working, no 403. Source update necessary, rather than simple toggling. The original vendor 5.126.1 signed ASAR **statically verifies** `playback.reloadEntity("QUALITY_CHANGE")` reloads via `getMediaSource({disableCache:true})` preserving position and paused state. Exact version/ASAR signature and hashes in W60 doc. Do not use page reload / Play-Pause hacks / Next, and never touch original Yandex account or backend HMAC.

**Already implemented, not a suggestion:** native controller observer in `windows-companion/w60/current-source-refresh.mjs`, renderer live reload on subsequent ON/OFF in `windows-companion/w23/renderer-entry.mjs`, state poll shorter in `w23/host.cjs`. Full native tests in `w60/current-source-refresh.test.mjs`, existing `w23/renderer-relay.test.mjs`. Dark extension-style Windows UI in `w15/Celikom.Companion/MainWindow.cs` and rounded buttons `PopupButton.cs`, colors copied from `extension/popup/popup.css`, separate working Start/Stop, auth, diagnostic download, native restore and update. Do not add fake upload/track support buttons; feature parity is not yet implemented. **It is NOT proven on the owner's actual Yandex playback yet** that player state getter observation or live reload works. Real-user test is essential.

**New private TEST build already built:** 0.24.8, Inno filename `CELIKOM-W60-LIVE-TOGGLE-EXTENSION-UI-UNSIGNED.exe`, **exact same Inno AppId/install directory as installed 0.24.7**, no second app or re-login. Build workflow **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42806599439, GitHub Actions artifact **13760040010** name `CELIKOM-W60-LIVE-TOGGLE-EXTENSION-UI-UNSIGNED`. Source build commit **`b752573a9a1d3b076a6038878ba40fb0a232123e`**. EXE SHA256 from Windows build log **`a1c5380c25b17872723a27dc013fed0dbd9eebce3e38bb6b47017ede29578fee`** (note: artifact ZIP SHA differs: `91c6efb246da7373ed267dd7fd206e492d4df7b8ff3b2456682cb2802ac6ba79`). Independent genuine **0.24.7→0.24.8 same-user DPAPI preserved upgrade** **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42807129308. Additional tests W59 PASS #42806556823, W60 renderer PASS #42806516765, vendor signed source audit #42804556792. CI verifies no user account removed, one uninstaller, Yandex original unaffected and native signed URL guard still present.

**Next-chat first task:** Do a quick read-only verification of branch HEAD/CI and artifact integrity. Download GitHub artifact 13760040010 using GitHub connector, unzip/verify EXE SHA above, then **UPLOAD the EXE to ChatGPT Library `/CELIKOM/Windows/`**, verify with files.list/materialize/checksum, and **deliver a working direct Library file card**, NOT a fabricated sandbox link. If the file is already in Library, use its existing card and verify. User previously had broken links, so delivery matters. Do NOT make a new build just to change its name, and never modify previously accepted 0.24.7. Inform user it is **unsigned private owner-test build**; avoid telling them to disable antivirus/Play Protect. User should use 0.24.7 app's **Обновить CELIKOM**, choose new EXE and confirm same-app in-place update. Then ask just this short check: already substituted playing song → **Стоп** should switch SAME track to original at same position; **Старт** should switch back; try paused state + one Next/MyWave. If fails, request a new 15-minute diagnostics TXT, watch `NATIVE_TOGGLE_PLAYER_OBSERVER_READY`, `NATIVE_TOGGLE_RELOAD_REQUEST/OK/FAILED/DEFERRED` alongside `SOURCE_MAPPED` & `PLAYER_NET_HTTP_PARTIAL`. Do not claim success until owner hears it.

**Rollback:** accepted owner 0.24.7 unchanged under `backup/windows-w57-owner-audio-accepted-0247-20261110`, EXE already in Library `/CELIKOM/Windows/CELIKOM-W56-SIGNED-QUERY-GUARD-UNSIGNED.exe`. Experimental base snapshot `backup/windows-w60-stage-source-before-0248-packaging-20261110`. Do not touch Android Test.50, production PHP, user sessions, vendor original Yandex, other projects.

---

# CELIKOM Windows — W57 OWNER AUDIO PLAYBACK SUCCESS 0.24.7 (2026-11-10)

**FIRST READ:** `docs/windows/W57-OWNER-0247-REAL-AUDIO-SUCCESS-20261110.md`, then W56 signed-query guard. The owner **explicitly reports real approved replacements now play** on installed CELIKOM Windows **0.24.7**: «Охуеть, всё работает.)))». Attached owner actual diagnostics `CELIKOM-diagnostics-20261110-132656.txt` (generated 10:26:59 UTC) validate native installed 0.24.7, `NativeIntegration=ACTIVE`, valid signed field comparison, and **two genuine native Media GET HTTP 206** (resource IDs **139 and 1**), **zero HTTP403**, zero observed CORS block; positive Yandex track mapping and session continuity. This is the **first owner-accepted core AUDIO PLAYBACK baseline**. The user hearing audio confirms sound; CDP `PlayerAudibleEventObserved=false` means only the CDP couldn't prove sound. Old `PLAYER_ENGINE_FAST_PAUSE` preceded source mapping; one native resource 139 loadFailed after 206/track switch remains non-403/undetermined. Pause/Seek/Next long-run QA is still **not separately verified**, not a known regression.

**DO NOT REGRESS:** Keep exact W56 `&celikom_native_query_guard=0` source-only suffix on validated signed native `downloadInfo.url/urls[0]`, never weaken PHP HMAC, sid, entitlement or change audio transport blindly. Owner-installed 0.24.7 is good; don't push another build without a specific justified improvement and owner need. Signed original Yandex host and Android/Test.50 untouched. Private unsigned installer (not public signed release) Library `/CELIKOM/Windows/CELIKOM-W56-SIGNED-QUERY-GUARD-UNSIGNED.exe`, SHA256 `cdd69637336045de8922c07fe4063f3b0e942e2e536d7d972469b921bf4f02f8`. Packaging and 0.24.6→0.24.7 same-app DPAPI CI have passed.

**NEXT:** Preserve W57 as exact frozen owner-approved rollback; only follow up on distinct Pause/Seek/Next and stability when appropriate. No new owner 0.24.7 installation/retest request and no needless diagnostic build.

---

# CELIKOM Windows — W56 native signed URL guard + 0.24.7 candidate (2026-11-10)

**FIRST READ:** `docs/windows/W56-NATIVE-TELEMETRY-QUERY-HMAC-GUARD-20261110.md`. Continue existing `experiment/windows-companion-integration-20261108`; never start over. Original owner **0.24.6** AUDIO NO-GO evidence in W51 (7 native Media GETs all 403 to resource IDs 139/89). No Android/production/Yandex-owner changes.

**NEW CAUSAL CODE FINDING** from exact vendor-signed Yandex 5.126.1 ASAR: telemetry hook sets `DownloadInfoSource.vsid` and `sourceIndex` before media playback; `src` naively concatenates `?vsid=...` to the supplied URL. For CELIKOM `...?token=...&expires=...&sid=7`, PHP receives `sid=7?vsid=...` and returns 403. Earlier W52 assumption of safe MP3 construction was incomplete; later TelemetryPlugin mutates the source. Verified pinned vendor audit #42795212512 and source contract #42796327933 SUCCESS. The user's original actual seven GET URLs remain redacted; owner real audio PASS not claimed yet.

**W56 fix staged in `windows-companion/w22/native-resource-adapter.mjs`:** after independently validating an approved grant, append ignored `&celikom_native_query_guard=0` only to native media `downloadInfo.urls[0]`/`url`; telemetry `?vsid` lands in guard value, token/expires/sid and `#t` seek remain intact. No PHP authorization/signing change. Stage-only Node + PHP/MySQL tests including 206 valid Range and 403 tampered/expired/revoked session **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42796387968. Signed genuine Yandex disposable host restore #42796125980 SUCCESS. W53 diagnostics export safety retained.

**0.24.7 TEST CANDIDATE READY AND VERIFIED:** W20 EXE package CI https://github.com/manufact-test/nomusic/actions/runs/42796898660 **SUCCESS**; genuine original Yandex staging https://github.com/manufact-test/nomusic/actions/runs/42796852849 **SUCCESS**; independent real **0.24.6→0.24.7 same-app encrypted DPAPI upgrade** https://github.com/manufact-test/nomusic/actions/runs/42797545026 **SUCCESS**. No duplicate app, session preserved, original Yandex untouched. EXACT EXE SHA256 `cdd69637336045de8922c07fe4063f3b0e942e2e536d7d972469b921bf4f02f8`. **Uploaded verified EXE to ChatGPT Library** `/CELIKOM/Windows/CELIKOM-W56-SIGNED-QUERY-GUARD-UNSIGNED.exe`, file ID `file_0000000029d08212a1e08d5efc34d6b0`; re-downloaded and bytewise verified. EXE name must not be changed (in-app updater whitelist). Unsigned **TEST BUILD**, NOT final audio release.

**NEXT ACTION REQUIRES OWNER:** Use the current CELIKOM 0.24.6 `Обновить приложение` with exactly that EXE; install OVER the existing app, do NOT uninstall or re-login. Open ordinary Yandex desktop and test the previously failing substituted song (resource 139/89), Play/Pause/Seek/Next, and ordinary source. If audio still fails, export and upload 15-minute W53 TXT for exact `PLAYER_URL_*` and `PLAYER_403_*` classification. Do NOT claim real playback success before this trial. No further diagnostic-only installer.

**BACKUP:** `backup/windows-w55-before-native-signed-query-guard-20261110` @ `b56ad543f15c1e0970f38a6b4429ff59c6f2eb9a`. Earlier exact owner 0.24.6 `backup/windows-w50-owner-0246-audio-403-pre-w51-docs-20261110`.

---

# CELIKOM Windows — W53 native 403 export regression fixed, still NO-GO (2026-11-10)

**FIRST READ:** `docs/windows/W53-HTTP403-DIAGNOSTIC-EXPORT-GATE-20261110.md`, then `docs/windows/W52-REAL-403-PRIVACY-SAFE-ROOT-CAUSE-STAGE-20261110.md`, and the owner's real W51 handoff.

**Critical correction:** The W52 C# GUI owner's TXT export would have SILENTLY DROPPED every `PLAYER_403_*` and `resource_id=` event due its old `[A-Z_]` / `track`-only allowlist; even `PlayerNetworkRequestObserved` summary would falsely be `false`. W53 fixes strict allowlist, summaries, 15-minute export and companion end-to-end tests. W53 also fixes per-resource `PLAYER_403_*` deduplication, permits bounded CDP JSON enum read ONLY for a tiny genuine audio-GET HTTP403, and distinguishes `PLAYER_URL_SIGNED_FIELDS_INTACT` from harmless query reorder or extra unrelated params. The fixed PowerShell genuine-Yandex owner-log gate must match exactly the new allowlist. Multiple earlier CI failures were from that outdated PowerShell gate, not evidence of owner playback failure.

**Current 0.24.6 audio still RED on owner machine:** original/ordinary tracks audible, approved substitutes silent, 7 real Media GETs all HTTP403. A separate source audit found original mapped MP3 URL getter normally preserves token query. Exact live reason **NOT PROVEN** because original 0.24.6 owner TXT cannot expose real request URL or body, and W53 hasn't been installed. Do NOT claim a server-side or URL rewrite fix. No production/backend/Android/vendor-owner changes; no new owner installer for diagnosis only.

**W53 CI source+GUI regression:** W48 #42790106070 SUCCESS; W20 #42789543676 SUCCESS; W15 Preview #42789294565 SUCCESS. Newest complete CI on corrected W23 disposable PowerShell gate https://github.com/manufact-test/nomusic/actions/runs/42790279901 and W41 https://github.com/manufact-test/nomusic/actions/runs/42790279982 must be verified before any future packaging gate; W20 https://github.com/manufact-test/nomusic/actions/runs/42790280129 is source/staging only. All tests synthetic or disposable; none authenticated/audio-PASS. **Rollback** `backup/windows-w52-403-classification-before-export-fix-20261110` at `34e4559de0edeef7df89567cb928de1a99d13859`. Working branch `experiment/windows-companion-integration-20261108`.

**W53 CI safety correction:** Synthetic malformed owner-export examples were accidentally written into the global native-events log by the W15 test suite, causing strict W23/W41 disposable-host smoke to reject them. Fixed via an isolated temp export directory; nothing malformed now enters the real owner-log path. W23/W41 workflow triggers include these tests. Distinguish `PLAYER_URL_SIGNED_FIELDS_INTACT` (order or extra unrelated query) from actual token/expires/sid corruption. Full detail in W53 doc.

**W54 read-only live SSH preflight:** https://github.com/manufact-test/nomusic/actions/runs/42791183852 SUCCESS, found **zero accessible recent candidate HTTP access/error logs** under the narrowly inspected Hostinger domain paths. No production writes, URLs, IPs or secrets logged. Thus cannot retroactively classify the owner's original seven HTTP403s from server access logs.

**W53 verified end-to-end stage gates:** W15/W22 #42791600640 SUCCESS, Windows preview #42791600534 SUCCESS, W20 #42791600240 SUCCESS, genuine signed original Yandex disposable W23 #42791811325 SUCCESS with byte-identical restore. New conditional legacy W41 observer ownership check #42792654175 needs final CI verdict; when host owns CDP it does NOT remeasure old wire-Origin categories. The one-use W54 Hostinger SSH census workflow has been removed after SUCCESS and zero accessible log candidates; only sanitized documentation and its historical run remain. Backup `backup/windows-w53-403-export-isolation-nativehost-pass-20261110` at `b5eeb51`. Owner app still 0.24.6 unchanged, sound NO-GO, no new EXE.

**NEXT:** Establish cause of LIVE audio 403 using a low-risk path, not an invented token/host bypass; inspect only legitimately authorized session/server evidence. Once fix is proven, create actual version >0.24.6 and run verified same-app DPAPI-auth-preserving update, then deliver exclusively through verified ChatGPT Library `CELIKOM/Windows`. No manual owner trial of unchanged 0.24.6.

---

# CELIKOM Windows — W52 staged 403 root-cause classification, NO RELEASE (2026-11-10)

**CURRENT FIRST READ:** `docs/windows/W52-REAL-403-PRIVACY-SAFE-ROOT-CAUSE-STAGE-20261110.md`. Preserve W51 real owner evidence in `docs/windows/W51-OWNER-0246-REAL-MEDIA-HTTP403-ROOT-CAUSE-HANDOFF-20261110.md`.

Owner still has **0.24.6**, audible approved replacement **NO-GO**. Existing 7 native Media GETs all 403; exact live reason **NOT PROVEN** by old redacted logs. W52 stage-only `w23/host.cjs` now compares trusted granted URL with native request URL privately in RAM, emits fixed `PLAYER_URL_*` classification + scoped 403 JSON/HTML and optional PHP denial enum, changes resource label to `resource_id=`. Added Node tests and updated stale W48 smoke check: W48 #42787607771 SUCCESS; W20 staging #42787432243 SUCCESS. W23 signed Yandex disposable runner https://github.com/manufact-test/nomusic/actions/runs/42787432599 SUCCESS (verified); no authenticated owner playback run. New rollback `backup/windows-w51-http403-pre-w52-stage-20261110` @ `a2797566`.

Original signed Yandex MP3 source getter has now been checked read-only: https://github.com/manufact-test/nomusic/actions/runs/42788482449 SUCCESS; normal MP3 `src` forwards `urls[0]` without appending its extra MP4/VSID query. The tempting second-`?` explanation is **not supported for our MP3 mapping**. Do not add padding/query hacks. Live HTTP403 remains unclassified.\n\n**DO NOT** ship W52 diagnostics-only EXE, alter backend/production, waive HMAC/session binding, or claim the silent playback fixed. Need causal proof by live URL comparison and/or scoped server 403 category before narrow repair, then strict tests and one authorized in-place owner update through verified ChatGPT Library `CELIKOM/Windows`. Android and vendor Yandex installation untouched.

---

# CELIKOM Windows — W51 handoff: owner 0.24.6 native Media GET HTTP 403 (2026-11-10)

**START HERE:** `docs/windows/W51-OWNER-0246-REAL-MEDIA-HTTP403-ROOT-CAUSE-HANDOFF-20261110.md` (evidence + confirmed server 403 branches + privacy-safe root-cause plan). **Ready-to-copy next chat:** `docs/windows/W51-START-NEXT-CHAT-20261110.md`.

**Owner's final REAL audio test on installed 0.24.6 is RED:** ordinary native Yandex tracks play; replaced tracks rapidly toggle Play/Pause and stall silent. Diagnostic `CELIKOM-diagnostics-20261110-114109.txt`, generated 08:41:11 UTC, confirms GUI/native 0.24.6, native bridge active and signed in, `SOURCE_MAPPED`. W50 removed ALL self-generated audio probes. CDP genuine Yandex native network shows **7 real GET / 7 HTTP 403** on signed audio path resource IDs 139 (4), 89 (3); 0 successful Media 200/206, no CORS error and no audible event. Those **139/89 are replacement resource IDs**, mislabeled `track=` in W50's diagnostic; don't confuse with Yandex track IDs. Earlier rapid start/pause events preceded approved mapping, so cannot assert their attribution to it. User's real audible fail is decisive regardless.

**SERVER** `AudioController.php` 403 JSON cases are invalid `sid/token/expires/HMAC/version` or `access_denied` for revalidated session/entitlement; also consider hosting/WAF 403 until error origin classified. Independent W48 signed 32-byte fetch yielded 206, but W50 native Media GET is denied. **Most useful hypothesis** native Yandex rewrites/strips signed URL query, **NOT PROVEN** (query/body intentionally redacted). Compare expected grant URL vs CDP requested URL safely in RAM only; log typed exact/missing/changed/expired flags, no secrets; distinguish server 403 category/upstream and fix ONLY the proved cause. Don't modify CORS, waive signing or entitlement, change codec/bitrate again, use standalone player, or publish blind installer. **No code/production changes in W51.**

**Branch:** `experiment/windows-companion-integration-20261108`. **Frozen W50 pre-W51 backup:** `backup/windows-w50-owner-0246-audio-403-pre-w51-docs-20261110` @ `38b9e0d691b47a11a800eb4c6d26d07fc47068fe`. W50 baseline release tests remained green but NOT audio acceptance. Android/Test.50 untouched. Only after evidence-based repair and real CI + safe single-app update may owner retest. When sending a future EXE, use verified **ChatGPT Library `CELIKOM/Windows`** and a directly clickable file card — owner rejects broken sandbox download links.

## Archived W50 handoff

# CELIKOM Windows — W50 0.24.6 real-network CI PASS, owner manual playback gate, 2026-11-10

**Read primary:** `docs/windows/W50-REAL-YANDEX-NETWORK-NO-SELF-PROBE-20261110.md`, then `docs/windows/W49-OWNER-0245-SIGNED-SOURCE-CALLCHAIN-20261110.md`. Owner 0.24.5 diagnostic disclosed NO audible approved replacement; owner described native fast Play↔Pause and silence on older 0.24.4. W49 proved fast pause in 0.24.5 export preceded first approved mapping, so **not attributable**. Original vendor-signed Yandex supports raw MP3 and original getMediaSource→corePlay; working MIT reference sets nominal bitrate 320 vs our inherited AAC bitrate.

**W50 0.24.6 INTERNAL experimental installer is READY, not audio PROVEN:** removes self-generated signed 32byte GET, so CDP Network shows only true native Yandex requests / preloading; classifies GET/HEAD, 200/206/403, CORS credentials/CSP and failures with **no URLs/tokens**. Fixes MP3 mapped bitrate to 320; preserves source/clock/controls. GUI and native module version both 0.24.6, same AppId, 15-min diagnostic export `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`. No production/backend/Android changes; W45 CORS live remains.

**CI facts:** W20 full 0.24.6 https://github.com/manufact-test/nomusic/actions/runs/42781645724 **SUCCESS**, artifact `CELIKOM-W50-NATIVE-NET-UNSIGNED` id `13746152125`, direct EXE SHA256 `0c6617f2aa496020e1440d90b8f0f3b58d980e2a782842df31e66dcdd1dd3975`; W23 genuine signed Yandex https://github.com/manufact-test/nomusic/actions/runs/42781645177 **SUCCESS**, original EXE/ASAR restored, audio `NOT_TESTED_NO_ACCOUNT`. W50 independent 0.24.5→0.24.6 same-app/DPAPI/native-assets/no-Yandex-write https://github.com/manufact-test/nomusic/actions/runs/42782200205 **SUCCESS**. Direct EXE file mounted and verified `/mnt/data/CELIKOM-W50-NATIVE-NET-UNSIGNED.exe` in this session and linked to owner via sandbox in preceding partial final. No more GitHub web-page hunt needed. **Backup:** `backup/windows-w50-network-bitrate-0246-owner-ci-pass-20261110` @ `62a1aed0575a193ef834130ca341ddd9e5c555d9`.

**NEXT:** Wait for owner to install one W50 experimental 0.24.6 over existing 0.24.5 (one app, account preserved, native module refreshed by approved installer), test approved and ordinary Yandex song, send fresh TXT, report actual audible outcome. `PLAYER_NET_REQUEST` after `SOURCE_MAPPED` distinguishes native stream request; `PLAYER_NET_HTTP_PARTIAL/FINISHED` does NOT prove audible. If **no** PLAYER_NET_REQUEST for approved mapped, pursue internal `getMediaSource/corePlay`; if native network request fail with CORS credentials/preflight, investigate narrow server audio CORS/credentials under authorization, no wildcard; if 206 succeeded but silent, pursue native codec/decoder/transport/state before further owner builds. Do not call success until he HEARS replacement and controls work.

## Archived previous W50 stage handoff

# CELIKOM Windows — W50 genuine-network and bitrate experiment staged, 2026-11-10

**READ FIRST:** `docs/windows/W50-REAL-YANDEX-NETWORK-NO-SELF-PROBE-20261110.md` plus owner report `docs/windows/W49-OWNER-0245-SIGNED-SOURCE-CALLCHAIN-20261110.md`. Owner currently installed **0.24.5** GUI+native; approved mapped tracks are silent; ordinary Yandex songs play. Last attached `CELIKOM-diagnostics-20261110-105211.txt` proved original source FileInfo has AAC/key/transport and genuine CDP media-start/pause **before** first approved mapping. After approved mapping, no further native media start observed. Do not misattribute global fast-pause to approved tracks or call signed 32-byte probe actual playback.

**W49 signed original Yandex 5.126.1 read-only CI confirms** true chain `getMediaSource → getFileInfo → createMediaSource → corePlay`, raw/encraw & MP3 supported. Working open MIT reference `S4YN3X/F_ckCensor` uses raw MP3 with no key and bitrate 320, contrasting our inherited original AAC bitrate. The key problem may instead be genuine Yandex network fetch and its credentials/CORS; W45 signed 32-byte probe uses `credentials:omit` and is NOT real player network proof.

**W50 source-only changes** (version **0.24.6**, experimental unsigned update, not yet owner-installed): no independent 32-byte audio GET; passive CDP Network exact trusted audio origin + numeric track path only, emits real `PLAYER_NET_REQUEST`/HTTP206/403/CORS/failed/finished classified codes without URLs/query/tokens or requests modification; new `PLAYER_AUDIO_RESOURCE_TIMING_SEEN` might be prefetch, no sound claim; MP3 nominal bitrate 320; owner log last 15m and typed evidence. W50 CI unit + W23 signed Yandex disposable + W20 internal installer must ALL pass, then separate **0.24.5→0.24.6 same-app upgrade** proof before user link. Previous backup `backup/windows-w49-signed-native-and-competitor-source-verified-20261110` @ `57cc262384dad3e785237d9fc814c7bf196ac416`. W45 server CORS live remains unchanged. Android/Test.50 untouched.

**If CI succeeds and owner tests 0.24.6:** success only audible replacement in actual native Yandex + pause/seek/Next. If no `PLAYER_NET_REQUEST` after `SOURCE_MAPPED`, investigate native prepare/corePlay. If real signed GET blocked, analyze native CORS/credentials; if genuine GET206 finished but silent, investigate decoder. Do not blindly alter backend, keys/IV, or send more empty diagnostic-only installers.

## Archived W48 handoff

# CELIKOM Windows — W48 true diagnostic 0.24.5 stage and owner-upgrade PASS (2026-11-10)

**Owner's actual verdict RED:** accepted mapped tracks on currently installed 0.24.4 trigger rapid UI Play/Pause oscillation and end paused/silent; ordinary untouched Yandex tracks work. This is NOT a CORS issue anymore: owner's 4.txt has 3/3 signed independent tiny MP3 HTTP 206 after W45. **No real native replacement audio ever confirmed.** Read `docs/windows/W48-REAL-PLAYER-DIAGNOSTIC-OWNER-FAIL-20261110.md`.

**Ready for one owner diagnostic trial (NOT audio-fix claim):** W48 internal unsigned same-app `0.24.5` package `CELIKOM-W48-PLAYER-DIAG-UNSIGNED` in https://github.com/manufact-test/nomusic/actions/runs/42776884046 (SUCCESS, artifact 13743709542). One-click ZIP in old CELIKOM 0.24.4 via **«Обновить CELIKOM»**, preserves owner account, auto native module refresh if version differs. Independent 0.24.4→0.24.5 same-app test https://github.com/manufact-test/nomusic/actions/runs/42777269209 **SUCCESS**: one app/uninstaller, DPAPI preserved, Yandex untouched. Genuine signed Yandex disposable host https://github.com/manufact-test/nomusic/actions/runs/42776853665 **SUCCESS**, original byte-identically restored; no account/audio verification.

**New observability:** Electron real media-start/pause, audible/silent, fast pause; passive CDP Media decoder error enum signals (fail-open), read-only redacted genuine file-info structure, `AUDIO_URL_RESOURCE_UNATTRIBUTED` instead of fake media request, recent 60m sorted export and explicit `ReplacementAudibleProof=NOT_AVAILABLE_FROM_PROBE_OR_MAPPING`; UI mapping message does not promise sound. Stage Node CI https://github.com/manufact-test/nomusic/actions/runs/42776927650 SUCCESS. Android/Test.50 untouched, W45 production backend unchanged. **If user exports fresh 0.24.5 TXT after one approved test, diagnose actual native decoder path and schema, then implement evidence-based fix.**

**Backup:** `backup/windows-w48-true-playback-diagnostics-owner-upgrade-ci-pass-20261110` @ `b8e772126c9f5498ca84f472422ee3960a251803`.

## Archived pre-W48 handoff

# CELIKOM Windows — W48 owner confirms audio RED, truthful 0.24.5 diagnostic staging (2026-11-10)

**Current first doc:** `docs/windows/W48-REAL-PLAYER-DIAGNOSTIC-OWNER-FAIL-20261110.md`. Owner actual Windows 0.24.4 sound verdict **RED:** approved substitute causes fast Play → Pause → Play → Pause, remains paused and SILENT; ordinary native Yandex tracks play. No need to ask him to repeat on unchanged 0.24.4. Morning W45 audio probes 3/3 HTTP206+MP3 bytes confirm CORS only, not genuine native playback. Old `MEDIA_REQUEST_SEEN` included independent own probe, old GUI `NATIVE_MAPPING_ACCEPTED` falsely suggested success.

**W48 source staged** on same Windows branch: Electron-native player started/paused + audible/inaudible events, explicit fast-pause, passive CDP Media-only decoder errors (no bodies or URLs, fail open), redacted genuine Yandex original file-info structure/codec/key-presence witness, `AUDIO_URL_RESOURCE_UNATTRIBUTED` instead of fake player-fetch counters, GUI honest label, 60-minute chronological diagnostic with typed engine/error evidence, new **0.24.5** same-app one-click internal **unsigned** diagnostic installer. W48 Node CI https://github.com/manufact-test/nomusic/actions/runs/42776927650 PASS; old W23 genuine Yandex disposable original restored https://github.com/manufact-test/nomusic/actions/runs/42776042891 PASS. **W20 latest 0.24.5 signed/audio status gate:** complete full CI check before giving artifact. This is an instrumentation upgrade, NOT a validated audio fix. Old Windows original and Android/Test.50 untouched. Backend W45 CORS remains active.

**Pre-W48 frozen source:** `backup/windows-w47-owner-audio-failure-before-truthful-diagnostics-20261110` @ `8d1096eecc038ff1bf8e8e163d0382a47cf3106e`.

## Archived W47 handoff

# CELIKOM Windows — W47 first owner report after W45 CORS, 2026-11-10

**Read first:** `docs/windows/W47-OWNER-POST-CORS-REPORT-20261110.md`. Owner sent morning `4.txt`, installed CELIKOM Windows 0.24.4 and matching native module. At 07:19 UTC three approved tracks (42498653, 85025192, 78608850) all show **real browser-context tiny audio probe HTTP 206 + audio/mpeg + MP3 magic**. No morning `AUDIO_PROBE_FETCH_BLOCKED`. W45 production CORS confirmed fixed. **No evidence yet that original Yandex decoder played replacement.** `MEDIA_REQUEST_SEEN/HTTP_UNVERIFIED` may include 32-byte independent probe itself; no real native player response status or confirmed audible Pause/Seek/Next. Await **owner's audible playback verdict** before modifying source or creating installer. If still silent, investigate true Yandex media fetch and file-info descriptor codec/key/iv/transport; do not confuse probed 206 with playback.

Working branch `experiment/windows-companion-integration-20261108`; W45 release backed up, Android and owner installed versions untouched. No new installer needed for CORS. W46 cross-audit includes Android native file-info risks.

## Archived W46 handoff

# CELIKOM Windows — W46 Android native cross-audit saved, 2026-11-10

**New cross-audit:** `docs/windows/W46-ANDROID-NATIVE-CROSS-AUDIT-20261110.md`. Inspected current Android native hooklab branch `experiment/android-native-yandex-fileinfo-hooklab-20261109`, latest Android native handoff/exit audit and genuine signed Yandex Android FileInfo static API evidence, plus older Media3 research. NO Android changes made. Key Windows next risk: W22 `toDownloadInfo` deletes `key/iv`, forces `codec/transport/gain`; genuine decoder may reject the synthetic descriptor. Do NOT copy original encrypted keys back blindly; first inspect original Windows native file-info/decoder shape and real signed Range 206 after W45 CORS. Android clone remains NO-GO (MAIN self-exits); no native Android audio success to transplant.

**Important:** W45 CORS is already LIVE, independent HTTPS W42 rerun PASS. Owner will test installed Windows 0.24.4 in the morning; no reinstall now. Avoid overwriting narrow `music-application://desktop` CORS when Android backend/0.3.93 catalogue migration releases. Keep Android/Test.50/server/Windows installer untouched during read-only research.

## Archived W45 production handoff

# CELIKOM Windows — W45 production CORS activated, 2026-11-10

**Сначала:** `docs/windows/W45-HYPHENATED-NATIVE-CORS-RELEASE-GATE-20261110.md`. Владелец разрешил W45 в текущем чате (“Делай”), live CI https://github.com/manufact-test/nomusic/actions/runs/42707502289 **SUCCESS**. Применена **одна точная вставка** в `Application.php` через новый неизменяемый релиз, не заменялся весь файл. Правильный Windows Yandex Origin `music-application://desktop` теперь получает CORS только для числового аудиомаршрута. Исходный SHA production `ec7f5d0d87978c823ece2dcfa2e76a021d4e2af09eb4f5c4d5fe52b6ab6c897e`; текущий ожидаемый `920a4fa28357a3e61d6af64085448eacc76ea8c3c3c1946597b6428e61b506e0`.

**Реальное HTTPS подтверждение после выпуска:** `OPTIONS 204` + ACAO native, bad-token `GET 403` + ACAO native, authorization/foreign Origin still blocked, legacy origins remain, health 200; независимый W42 rerun https://github.com/manufact-test/nomusic/actions/runs/42704976449 **SUCCESS**. Backup/private rollback `backups/w45-native-cors-d11481668524` + prior original release; automatic rollback was armed, not triggered. Owner Windows CELIKOM 0.24.4 + native module 0.24.4, original Yandex, Android/Test.50 untouched.

**Следующее:** владелец может проверить текущую 0.24.4 без переустановки: Stop/Start CELIKOM, при необходимости перезапустить Яндекс, одну подменяемую песню, обычную песню, паузу/перемотку/Next. Если не заиграет — новый TXT. CORS-фикс подтверждён, но **реальный audio decoder / key/iv/codec/transport и слышимый звук НЕ доказаны**. Не выпускать установщик наугад. Синхронизировать W45 CORS с canonical backend `feature/api-range` перед следующим полным выкладыванием серверного пакета, иначе возможен откат исправления.

**Резерв кода:** `backup/windows-w45-candidate-guard-ci-pass-20261110` at `b5785a24cb1b531e531101632f7553c673cbbb5c`.

## Архивная передача W45 до разрешения на выпуск



**Сначала прочитать:** `docs/windows/W45-HYPHENATED-NATIVE-CORS-RELEASE-GATE-20261110.md`. Рабочая ветка `experiment/windows-companion-integration-20261108`, основа владельца CELIKOM Windows **0.24.4** + native **0.24.4**, никаких переустановок.

**Точная подтверждённая причина W41**: настоящий подписанный Windows Яндекс отправляет **Origin: `music-application://desktop`**; backend разрешал `musicapplication://desktop` без дефиса. Native Chromium GET CORS blocked, MissingAllowOriginHeader. W41 genuine Yandex CI #42704012210 SUCCESS, vendor files + signature restored.

**Server stage-only fix**: exact hyphenated origin added ONLY to token-scoped audio path with unchanged HMAC/auth/range security. W30 stage CI #42704641987 SUCCESS; W42 production read-only #42704976449 confirms fix NOT active; W43 #42705379376 confirmed **full-file replacement NO-GO** (live PHP drift). W44 #42705730045 and W45 strict PHP candidate helper #42706261691 SUCCESS: one-hunk surgical live-copy fix, exact before/after SHA, all PHP tests, wrong path/re-patch forbidden.

**Release gate:** No production deployment made. Owner separate explicit permission needed for guarded one-file CORS update. Must create clone/backup, preserve old release, automatic rollback, LiteSpeed cache refresh, post-deploy original/current checks. NO new EXE. Real signed 206/audio, original Yandex Pause/Seek/Next and codec/key/IV requirements still unproven.

**W45 backup:** `backup/windows-w45-candidate-guard-ci-pass-20261110` at `b5785a24cb1b531e531101632f7553c673cbbb5c`. Android/Test.50, original owner Yandex install, extension, FOX/site, production backend/database untouched.

## Archived previous W40 handoff



**Current primary:** `docs/windows/W40-NATIVE-CUSTOM-SCHEME-CORS-20261109.md`. W40 native Windows genuine-Yandex read-only CI **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42701895118. The genuine native renderer's on-wire `Origin` is categorically `CUSTOM_SCHEME`, **not** approved `musicapplication://desktop`/`null`/known HTTPS; server denied fixed invalid-token GET as HTTP 403 with **no ACAO**, Chromium `MissingAllowOriginHeader`. Same invalid token from trusted Electron main produced 403 **with ACAO_NATIVE**. This is a *confirmed CORS mismatch for the invalid-token probe*, **NOT** proof that signed authorized audio 206 / original Yandex playback works.

**Backup:** `backup/windows-w40-custom-origin-cors-ci-confirmed-20261109` at `8d7fe03eb042d906c427a043cdf282af36a06851`. Changes exclusively disposable CI research/tests/docs. Original vendor EXE/ASAR bytes+signature restored. No owner installer, production backend, Android/Test.50, or native audio source metadata changes.

**Next:** identify exact trusted static origin scheme/host in isolated original Yandex without leaking values, design only a safe narrow signed-audio allowlist staging preflight, then real authorized 206/Range and original Windows file-info codec/key/iv decoder inspection. No wildcard CORS, no global security bypass, no proxy/open player. Owner CELIKOM 0.24.4 + native 0.24.4 remain installed; no manual action needed.

## Archived W40 start



**W39 verified:** read `docs/windows/W39-NATIVE-ORIGIN-CLASSIFICATION-20261109.md`. Actual original Yandex `NATIVE` renderer sends an `Origin` categorized `UNLISTED_OTHER`, HTTP 403 response has `ACAO_ABSENT`; Chromium records `MissingAllowOriginHeader`. Trusted main request with deliberately invalid token still sees `MAIN_HTTP_403`+`MAIN_ACAO_NATIVE`. CI #42700805271 and post-test-fix #42701221204 SUCCESS. Original EXE/ASAR were restored to verified originals.

**W40** only narrows the previously unknown Origin to a safe scheme family without logging the actual value. CI https://github.com/manufact-test/nomusic/actions/runs/42701895118 — check verdict. Pre-W40 backup `backup/windows-w39-actual-native-origin-cors-evidence-20261109` at `805a6142fb0055311b61609315fa0ed99caf72b8`. No new installer or native audio fix. No backend changes without proof; avoid generalized permissive CORS.

**Owner** 0.24.4 + native module 0.24.4 stay installed. No TXT/reinstallation needed. Android/Test.50, site, production, extension not touched.

## Archived W39 transfer



**Главное:** `docs/windows/W39-NATIVE-ORIGIN-CLASSIFICATION-20261109.md`, затем W38/W37/W36/W35.

W38 настоящая Windows Яндекс-Музыка (CI #42695804499) доказала в своём `NATIVE` renderer: `CDP_LOAD_FAILED_CORS` с точным `MissingAllowOriginHeader`. Trusted Electron main для **намеренно INVALID токена** получал `HTTP_403` / `ACAO_NATIVE`. Видна настоящая транспортная проблема контрольного запроса; **реальный подписанный 206 и аудиодекодер всё ещё не проверены**.

W39 проверяет категории реального outgoing `Origin` и returned `Access-Control-Allow-Origin` по passive CDP. CI https://github.com/manufact-test/nomusic/actions/runs/42700903189 — проверь окончательный результат. Не изменяй PHP/server, настройки security Яндекса, key/iv или codec до однозначной проверки причин. W38 backup `backup/windows-w38-native-cors-missing-acao-confirmed-20261109` at `ec7b0ad7a264612728fd4f1af99d5bdc18c58bfc`.

Owner `0.24.4` / module `0.24.4` сохраняются. Нет нового установщика/пользовательской диагностики. Android, Test.50, расширение, production не трогать.

## Archived W38 transfer



**Сначала:** `docs/windows/W38-NATIVE-CORS-ENUM-20261109.md`, затем `docs/windows/W37-NATIVE-CDP-BOUNDARY-20261109.md` и W36/W35.

**Доказано:** W36 CI #42693758356 получил `NATIVE_FETCH_BLOCKED_TYPEERROR` в настоящем оригинальном renderer при `MAIN_HTTP_403`; W37 CI #42694895709 пассивно обнаружил `CDP_LOAD_FAILED_CORS` на этом **намеренно invalid-token** запросе. В обоих случаях original signed EXE/ASAR restored. Точный код CORS (preflight vs Origin/headers etc.) ещё выясняется в W38 CI #42695804499. Do NOT change backend or native codec/key/IV before evidence.

**Backup:** `backup/windows-w37-native-cdp-cors-confirmed-20261109` at `f1e33c534d7aa1f5e7ea7c1ae7aa089945d14927`. Owner CELIKOM Windows 0.24.4 + module 0.24.4 unchanged and stays installed; no new installer or TXT necessary. Android/Test.50 untouched.

## Archived W37 transfer



**Новая передача:** `docs/windows/W37-NATIVE-CDP-BOUNDARY-20261109.md`. W36 genuine native renderer failure independently verified in SUCCESS CI #42693758356: `NATIVE_FETCH_BLOCKED_TYPEERROR_CSP_NONE` vs trusted Electron main `MAIN_HTTP_403` + `MAIN_ACAO_NATIVE`. Vendor original bytes/signature restored. **Do NOT claim CSP specifically, audio transport fixed, decoder compatible or audible substitution.**

**Accepted W36 backup:** `backup/windows-w36-native-renderer-fetch-blocked-ci-pass-20261109` at `474290941f2d4ea10db3a75adfc07683669b1515`.

**W37 CI-only:** passive Chromium CDP Network/Log classification on approved native view, no interception/security bypass/owner changes. Run https://github.com/manufact-test/nomusic/actions/runs/42694895709 — check final status and filtered categorical evidence before any follow-on code. If inconclusive, no installer.

**Owner** keeps Windows CELIKOM 0.24.4 + matching native 0.24.4. No reinstall, no re-export TXT required now. Android/Test.50, extension, Yandex account, live backend/production all untouched.

## Archived W36 transfer



**Новое W36 (CI-only, не выпуск):** изучи `docs/windows/W36-ISOLATED-RENDERER-BOUNDARY-20261109.md` перед W35/W34/W33. Резерв `backup/windows-w36-pre-renderer-boundary-fix-20261109` at `d999ac40ccc80c21f82ce7c5014ec6976a4cbb43`.

Исправлена именно временная/событийная недоработка W33 genuine-Yandex CI-only диагностики: ждать approved Yandex `dom-ready` и проверять ответ invalid-token GET из настоящего renderer против Electron main, с редактированными категориями ошибок. CI: https://github.com/manufact-test/nomusic/actions/runs/42691438851 (проверить финальный verdict). Отдельно unit tests на readiness/retry и обычный W23 native smoke, без подмены аудио.

**Владелец:** CELIKOM Windows `0.24.4` + native module `0.24.4` остаются установлены, обновлять/переустанавливать **ничего не нужно**. Исходная проблема — 4/4 `AUDIO_PROBE_FETCH_BLOCKED`, реальной подмены не доказано. В W36 не меняли ни `toDownloadInfo`, ни backend, ни Android, ни аудиопроигрыватель. Пока signed 206 и native decode не доказаны, не выпускать installer.

## Сохранённая передача W35



**ГЛАВНОЕ:** продолжать проект, не с нуля. На компьютере владельца CELIKOM 0.24.4 + native module 0.24.4 совпадают (owner TXT 3.txt), но подменное аудио моментально останавливается. Новая установка сейчас НЕ нужна. Никакой аудиоподмены в оригинальном Windows Яндексе ещё не подтверждено.

**Рабочая ветка:** `experiment/windows-companion-integration-20261108`. Последний HEAD бери из ветки (документация W35 — конец этого этапа). Независимый backup: `backup/windows-w35-pre-final-handoff-20261109` at `a62b969d21236b94ea07b9d5b433495c2ea6802e`.

**Читай по порядку:** 
1. `docs/windows/W35-HANDOFF-AFTER-ANDROID-REVIEW-20261109.md` — полный статус, следующий порядок действий, все ограничения.
2. `docs/windows/W34-ANDROID-CROSS-AUDIT-20261109.md` — выводы из мобильной ветки и осторожности по file-info/криптографии.
3. `docs/windows/W33-OWNER-0244-AUDIO-FETCH-BLOCKED-20261109.md` — последняя реальная диагностика, тесты CORS/CSP и ограничения CI.
4. `docs/windows/W32-OWNER-EASY-UPDATE-20261109.md` — уже решённое обновление из ZIP и отображение версий.
5. `docs/windows/W35-START-NEXT-CHAT-20261109.md` — готовое первое сообщение следующему чату.

**Владелец:** `AppVersion=0.24.4.0`, `NativeModuleVersion=0.24.4`, `NativeModuleMatchesApp=true`. Треки без подмены играют. 4/4 approved audio probes: `AUDIO_PROBE_FETCH_BLOCKED`, HTTP/MIME/decoded audio не подтверждены. CORS live серверной audio-route работает; публичный web-CSP Яндекса не допускает частный аудиодомен, но **точный native desktop CSP не доказан**. CI-only запрос в genuine Windows Yandex #42682820621 был inconclusive; обычный smoke #42682821206 SUCCESS и оригинальные vendor-байты восстановлены.

**Android cross-check:** read-only latest observed `experiment/android-native-yandex-fileinfo-hooklab-20261109` HEAD `36ca37bd0ce1e37cea1bc005789b0a970cbe6464`; Android DTO has urls/codec/key/gain/r128; Windows `toDownloadInfo` removes `key/iv` and overwrites codec/transport/gain → potential separate native-decoder mismatch after transport is addressed, NOT proof. Latest Android CI #42688277066: **unmodified original emulator app process alive**, cloned app fails classloading (`YMApplication` hint); still NO Android native audio or login proof. No changes to Android.

**NEXT:** debug Windows actual signed original renderer invalid-token fetch vs trusted main at correct `dom-ready`/approved event **in disposable CI only**; do not modify owner installation. After transport is proven, inspect actual Windows original file-info/decoder and implement narrow fail-safe single-source solution. Never ship another EXE based on SOURCE_MAPPED alone. Android/owner Yandex/backend/production/extension/Test.50 untouched.

**История:** long previous `NEXT-CHAT.md` preserved as `docs/windows/NEXT-CHAT-ARCHIVE-BEFORE-W35-20261109.md` and in Git history. W34 owner handoff preserved. No actual audio fix claimed.
