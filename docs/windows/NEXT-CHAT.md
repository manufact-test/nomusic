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
