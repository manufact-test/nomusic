# W89: Windows 0.24.33 TEST — VPN switch revalidation + false green original (2026-11-13)

## User-supplied evidence / current scope

Owner reported two audio drops while listening on **0.24.32**, second after turning off one VPN and turning on another. First drop was loud with a brief hiss and fast apparent recovery; second smoothly fell back to original, then took around 40–50 seconds to reconnect.

Two diagnostics (`диагна.txt`, `Вставленный текст(20261113-123416).txt`) show:
- At 2026-11-13 **12:06:46 UTC** an expired audio URL received HTTP 403 `PLAYER_403_PHP_INVALID_AUDIO_TOKEN`, a new signed URL received HTTP 206 and a new player start at 12:06:47. **No confirmation about why hiss was loud**.
- At **12:26:28–12:26:29 UTC**, a track source `track=106040459` hit LOCAL_HTTP_TIMEOUT/RESOLVE_TRANSIENT while VPN changed. At **12:26:40** entitlement GET retried, at 12:26:44 the app disabled the bridge `ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED`. `ACTIVE_ENTITLEMENT_ROUTE_CHANGED` appeared only at **12:26:58** because old code ignored route changes while still enabled and busy. Failed rechecks at 12:27:07/18/28; recovered only at **12:27:29**. The long outage is real, not a visual warning.
- Owner screenshot has song **«Ты» by тринадцать карат** while CELIKOM UI showed **«Подмена активна · версия CELIKOM»**, but the owner hears the censored original. Fresh diagnostic at **12:33:19 UTC**: current `track=89285816`, grant found, `SOURCE_BATCH_MAPPED`, but **no matching signed media HTTP GET** in the following 34 seconds and `NativeMediaUrlExactMatchObserved=false`. A mapping alone does not prove current Yandex decoder used it. Avoid equating HTTP 206/prefetch or file-info mapping with sound. This **does not yet prove the exact cause** of original fallback; owner listening remains definitive.
- NativeIntegration Active, native module matching in 0.24.32. Old source witness CDP `kUrl` availability remains unknown and may never expose that property.

## Exact backup / work

Repo `manufact-test/nomusic`. Work branch `experiment/windows-w89-vpn-fast-recovery-audio-proof-20261113`.
- Exact rollback before any W89 code `backup/windows-w89-before-vpn-recovery-audio-proof-20261113` @ `3ebded59b4bf596d54b1b5b29edfe16683ad45a0`; stable W88 0.24.32 installer in Library `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.32-AUTORUN-DEFAULT-ON-TEST.exe` (id `libfile_c4548e97dfac81918a6d250d92ba3e73`), SHA256 `715D7F8B97F2D97E2ACE2FBBB0211F760F9A34E2EB14864FE91CB261C965CF4E`.
- New TEST version **0.24.33**, native module **0.24.26** (upgrade via original safe NativeIntegrationManager.Upgrade). Never overwrite owner's previous installed version remotely. Owner autostart/DPAPI/CI checks must be retained.

## Changes / safety

### VPN refresh
- `MainWindow.OnNetworkAddressChanged`: react even when playback still active; mark new route; cancel old GET; coalesce via 1.4s debounce and 750ms settle, reschedule one new check after current ends.
- `CompactPopupActions.RefreshCompactAccessAsync`: single shared CTS on active HTTP, passes cancellation to GET and original ordinary retry; short 3s GET on changed route or while suspended. An intentionally canceled old-route request must **not** disable music by itself.
- `EntitlementCheckRecovery`: suspended recheck cadence 3s instead of 5s, normal healthy 15s unchanged; fast-route mode only within 30s after network signal. Any recovered activation still needs a fresh successful authenticated server GET and unchanged account and verified official native module. Explicit Stop remains authoritative. No offline authorization bypass.
- No guarantee reconnects in under N seconds if new VPN blocks the CELIKOM server; no fabricated success.

### «Ты» / false green
- `PlaybackSourceEvidence` + CompactPopup: green **only** when native status is `NATIVE_SOURCE_VERIFIED`, a narrow CDP current decoder `kUrl`/signed-fields/`kIsPlaying` corroboration for current song. Merely `NATIVE_MAPPING_ACCEPTED`, `SDK_MAPPING_ACCEPTED`, `SOURCE_BATCH_MAPPED` yields **neutral** `Версия CELIKOM передана Яндексу` (NOT proof of actual speakers). No new yellow banners.
- `BridgeServer` accepts verified-only status; matching `MainWindow` label.
- `w23/host.cjs`: retains existing passive CDP proof but now attaches source confirmation to current status; invalidates on pause/source changes/bridge loss. Tracks recent **successful native Media HTTP 206/200 for the exact track** as only a suppression condition for a recovery attempt, NOT proof of sound.
- If current mapping accepted, a signed grant issued for the current song, native Network observer is present, **no corresponding 200/206 media GET** occurs within ~3.5–16s of first observed current entity: at most **one** `__celikomBridgeNativeRefreshUnfetched` request per track per 120s. Renderer independently checks exact current track, enabled state and native player availability, then requests Yandex's existing version-pinned `reloadEntity("QUALITY_CHANGE")` only; preserves queue/pause/seek. Cannot touch other tracks, no loop, no synthetic audio requests. This may help a Yandex original source retained from cache, but **requires owner field QA** and won't guarantee fix if cause is elsewhere.
- Approved signed URL, exact source and audio error evidence never exported to diagnostics; only allowlisted code/track IDs.
- Native host/renderer modified intentionally, so **0.24.32→0.24.33 manual Start may need safe module upgrade**, and W89 in-place CI MUST expect new assets, preserve encrypted DPAPI, same installer AppId and rollback.

## Required checks before delivering

1. W23 Node tests: native resource, renderer, source reload position/pause, CDP source witness, transient/403. W15 .NET entitlement and false-green. W21/W24 safe vendor and backup. GUI `-warnaserror`; Inno setup in-place from exact W88 artifact SHA.
2. Do not release until latest Actions W89 run is GREEN. Then confirm installer SHA and Library upload; preserve old candidate. Do not declare user's VPN/audio actually fixed without playback test on their PC.
3. Manual owner QA: change VPN while listening and check reconnect time; play **«Ты» by тринадцать карат**, distinguish original vs CELIKOM sound, and note the small neutral vs green status. Capture diagnostics if still original, and any hissing/transients. No forced VPN change or synthetic tests remotely.

## CI pending

- Workflow `.github/workflows/windows-w89-vpn-fast-recovery-track-fix-installer.yml`.
- Latest started workflow https://github.com/manufact-test/nomusic/actions/runs/43428796923; **verify outcome** before asserting success.

## Final tested W89 candidate — 2026-11-13

- Latest **Windows CI SUCCESS**: https://github.com/manufact-test/nomusic/actions/runs/43429303326, final uploaded installer artifact `14039475715` https://github.com/manufact-test/nomusic/actions/runs/43429303326/artifacts/14039475715.
- W15 native contract and added fast-route/decoder-proof tests: `W15_NATIVE_CONTRACT_PASS 188` and staged update check `PASS 192`. W23 existing renderer/native/Yandex player integration tests plus new W89 **unfetched-current one-shot 120s**, no reload after signed Media HTTP206, decoder-only verified heartbeat, preserve pause/position all passed. W21/W24 and warnings-as-errors GUI compiler passed.
- Actual EXE filename `CELIKOM-Windows-0.24.33-VPN-TRACK-TEST.exe`, size **43,550,095 bytes**, independently extracted and SHA256 checked **`414EDBA856A12B25CB3EDE26D136C7F263CFC02FC3448730C7F7D02D60791879`**, matches GitHub CI.
- Verified second deliverable ZIP `CELIKOM-Windows-0.24.33-VPN-TRACK-TEST.zip` size **43,049,480 bytes**, SHA256 `FEEEC0E1086D69D2318966F2E893F3C2F99B37BA2E9190F8B234F08C9E23F9A4`. ZIP internal CRC test and extracted EXE SHA256 verified.
- **Persistent Library successfully uploaded**:
  - `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.33-VPN-TRACK-TEST.exe` (Library ID `libfile_00ff6ff7f3a48191b77f343dd6bcc81d`)
  - `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.33-VPN-TRACK-TEST.zip` (Library ID `libfile_0180ed7336d0819199ada0ea3b57fff1`)
- Windows in-place CI **`W89_02432_TO_02433_INPLACE_DPAPI_AND_NEW_NATIVE_READY_PASS`**: old verified W88 installer SHA checked, session.dpapi preserved, encrypted sign-in decrypts; installer replaces host.cjs and renderer.js with W89 assets (as expected), original vendor Yandex file tree NOT touched by installer itself, AppId unchanged.
- No remote deployment. **Owner Windows field QA not yet performed**. Reboot/autostart remains inherited; on first 0.24.33 Start may safely refresh native module 0.24.25→0.24.26. Do not assert audible source or <N-second VPN reconnect from CI alone. User still needs real playback of «Ты» and VPN changes.
- Existing W88 0.24.32 rollback preserved in Library / backup.


## STOP-WORK / OWNER HANDOFF ADDENDUM — 2026-11-13: NEW Big City Life VOLUME DROP

**Owner explicitly asked to stop development in this chat, save everything, and transfer all unfinished issues to the next leading developer.** This addendum is documentation-only. No further code edits, release changes, or installation on the owner's machine are authorized by this handoff.

### Third separately reproducible user-reported audio defect — Big City Life

- User's song name: **Big City Life**, performer as named by user **«трио Гутрика»** (preserve wording; check exact track ID later, do not invent an artist identity).
- While playing the **CELIKOM alternative version**, sound **suddenly becomes roughly half as loud**, without user intervention or a visible track failure. According to owner the **alternative keeps playing**, but its output stays low and **does not recover**.
- The CELIKOM **admin panel still shows track-specific volume amplification**, and the **admin preview plays correctly, at the intended louder volume**. On Windows/Yandex playback, the volume drops and stays low.
- **Not proven** whether the server's gain value changed, an encoded/alternate stream switched, normalization/gain got applied differently in the Yandex player, or Windows audio session changed. No timestamp/diagnostic associated with this volume incident has yet been provided, so do not invent one. Do not automatically equate a half-volume perception with a -6 dB technical measurement. Preserve server-side amp, cached audio/gain metadata, range streaming and Yandex original gain/normalization for inspection.
- **Issue #54** https://github.com/manufact-test/nomusic/issues/54 created with full evidence and next checks.
- Reconcile admin preview and actual served signed stream byte provenance / gain pipeline before touching live media. A client-side playback-time gain fix could conflict with Yandex normalization, clipping, crossfade, and route-change. Do not blanket amplify all songs.

### ALL unfinished issues — explicit priority order for next chat

1. **VPN switch: 40–50s reauthorization/outage**. 0.24.32 owner diagnostics show first `LOCAL_HTTP_TIMEOUT` at 12:26:29 UTC, entitlement suspends 12:26:44, route changed signal 12:26:58, repeated GET timeouts until 12:27:28, connection recovered about 12:27:29. W89 0.24.33 implements route-aware cancellation, short fresh authenticated GET and 3s retry cadence; Windows CI green, **real VPN test on owner's PC not yet done**. Never bypass entitlement on offline/VPN.
2. **«Ты» by тринадцать карат: false CELIKOM green, actual original audio**. Owner screenshot & diagnostics (current `track=89285816`) show mapping `SOURCE_BATCH_MAPPED`, but no confirming CELIKOM player Media GET in ~34 s. W89 changes UI green only for independent current CDP decoder `kUrl` source evidence; mapped state neutral. W89 includes bounded one-shot current-source reload when signed CELIKOM media was never fetched. **Still unverified audibly**; do not call fixed until owner hears alternative. Issue #52 proof remains open.
3. **Big City Life (user: «трио Гутрика»): CELIKOM alternative becomes ~2× quieter suddenly; admin configured enhancement and admin preview still normal**. **New/uninvestigated, #54**. Find exact audio/normalization/gain divergence and why it persists, preserve clip/headroom, compare served files and playback normalization.
4. **Abrupt hiss/pop on the first drop**. Older 0.24.32 diagnostics show an expired signed URL→HTTP403, fresh signed HTTP206 within ~0.5 s, but sound may have popped loudly. No direct noise waveform diagnosis or safe fix yet. Preserve no-hard-cut/crossfade behavior; don't assert root cause from 403 alone.
5. **Brave/Windows global freezes or lag while CELIKOM + Yandex active**; fine when both closed. Owner earlier reported a vague extra-rights prompt in Yandex. Issue #53. Exact prompt not captured. Don't declare malware, don't request admin, and no unverified resource optimizations. Native observer CDP pre-exists W88; no more blind rewrites.
6. **Decoder source evidence remains not comprehensive**. #52 open: `PlayerAudibleEventObserved=false`, `NativeMediaUrlExactMatchObserved=false` in older diagnostics; signed HTTP 206 and mapping do not prove audible replacement.

### Build, release and branch state at handoff

- Latest built/tested **Windows TEST 0.24.33**, native 0.24.26. Windows CI **SUCCESS**, run https://github.com/manufact-test/nomusic/actions/runs/43429303326, artifact `14039475715`.
- Installer exe SHA256 `414EDBA856A12B25CB3EDE26D136C7F263CFC02FC3448730C7F7D02D60791879`, **43,550,095 bytes**. ZIP SHA256 `FEEEC0E1086D69D2318966F2E893F3C2F99B37BA2E9190F8B234F08C9E23F9A4`.
- Already stored both files in Library:
  `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.33-VPN-TRACK-TEST.exe`
  `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.33-VPN-TRACK-TEST.zip`
- **Important:** 0.24.33 is CI-tested but **has not passed the owner's real playback/VPN/volume test**, and should not be presented as stable production. The owner is on/testing **0.24.32**, based on latest supplied logs. Do not assert 0.24.33 has been installed.
- Current branch `experiment/windows-w89-vpn-fast-recovery-audio-proof-20261113`; exact pre-handoff code commit **`6916c0229861aaa6f2486224f3e62092b343698e`**. Code backup `backup/windows-w89-02433-ci-green-owner-handoff-before-volume-20261113` pinned to same SHA. Previous **0.24.32 W88** rollback `backup/windows-w89-before-vpn-recovery-audio-proof-20261113` @ `3ebded59b4bf596d54b1b5b29edfe16683ad45a0`.
- No code changed during this addendum; docs and issue #54 only. Next chat should start from GitHub branch and these documents, work in large independently validated blocks, preserve old exact versions, and deliver a new installer only when tested. Do not automatically modify production/Yandex or owner's PC.


## W97 STOP-WORK / OWNER HANDOFF ADDENDUM — 2026-11-13 (LATEST OWNER INSTRUCTION)

This later owner instruction supersedes the earlier W89 STOP-WORK scope: the current chat must stop after saving documentation, and the **next leading chat is explicitly asked to continue development** and finish a single complete integrated TEST installer. The owner does not want another intermediate build or a request to test 0.24.34 for admin gain; the gain sidecar is not live on production yet.

New distinct issue **#58**: while «Моя волна» / original songs with no active replacement were playing, VPN switch caused interruption and audible «пшик». CELIKOM must be transparent to an original decoder; inspect route/entitlement → bridge state → W23 host → W22 adapter → Yandex decoder. This is separate from #57 403 recovery hiss, #54 Big City Life sudden mid-track volume drop, and #56 missing admin gain parity. Full evidence and acceptance: https://github.com/manufact-test/nomusic/issues/58.

**Required final outcome:** one complete TEST build with real Windows gain_db sidecars active for all eligible active nonzero-gain tracks, safe production migration/rollback and signed Range proof; fix/test #58; retain VPN fast server recheck, «Ты» source proof, Big City Life dip, 403 hiss, Brave diagnostics and all playback/install/session safety. Do not send partial installers. Full instructions and first message are in `docs/windows/W97-FINAL-READY-RELEASE-HANDOFF-20261113.md`.

Current W95 0.24.34 is CI-green but not owner-field-tested and cannot validate gain. Existing exact W95/W89/W88 rollback branches remain untouched. No installation on owner's PC. This addendum changes documentation only.
