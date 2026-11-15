# CELIKOM Windows — AUTHORITATIVE CURRENT HANDOFF / 15 November 2026

## W150 — OWNER-CONFIRMED SCOPE AND STRICT SEQUENTIAL WORK ORDER (READ FIRST)

- **This is the current owner-approved work order.** Read `docs/windows/W150-OWNER-CONFIRMED-SCOPE-AND-SEQUENTIAL-WORK-ORDER-20261115.md` before coding. It supersedes conflicting priority lists in W139 and commercial Authenticode/PFX provisioning in W148. W119 still governs one-product/main-only architecture.
- Work strictly in this order: (1) truthful current Yandex player/UI source synchronization; (2) current owner-reported VPN A→B audio pop while preserving faster reconnect; (3) autostart/tray verification; (4) one consolidated regression and acceptance preparation; (5) automatic updater/key/feed last; (6) build exactly one final owner EXE+ZIP after updater integration.
- Do not start #53, #54, #56, #57, #58 or any other historical OPEN Issue as a standalone task. #52 is relevant to current-source truth and remains open until owner acceptance. Do not treat historical ticket status as authorization.
- W141–W147 current-player/source evidence improvements are already in `main`; audit and finish only real gaps, do not restart the architecture. VPN transient still needs engineering work. Autostart first-launch ON and sticky user OFF are already present in code review; verify, do not rewrite without evidence.
- Updater final design: own P-256 signed manifest + SHA-256 packages; no commercial Authenticode certificate/PFX, no company identity, no Windows security bypass. Preserve current SmartScreen warning experience. `celikom.com` is purchased and fixed as future origin `https://celikom.com`; DNS/TLS/public feed are deferred until migration. One manual trusted bootstrap from installed unsigned 0.24.37; subsequent updates become automatic after migration activates DNS/TLS and the signed feed. W148 workflow is an outdated scaffold and must be refactored only in the final task.
- W150 code/doc baseline before the W150 documentation commits: `0524158177beeedb50bff85d59ae573d90c19823`. Exact pre-W150 docs backup: `backup/windows-main-pre-w150-owner-scope-handoff-20261115` @ that SHA. W150 documentation was subsequently corrected in commit `aa32d88fd54bcb2774e64a92c955c298e6afcb2d`; its Main CI `43702822315` and Windows integration CI `43702822253` were running when checked. Always fetch the live HEAD and latest CI before coding; do not rely on this historical SHA. Installed owner version remains 0.24.37; no new package delivered.
- W151 Task 1 and W152 Task 2 are implemented and CI-green at `59894be3fe88de0dfecd9d92c9164b509d0c7859`. The next continuation must verify live HEAD/CI, then work **only on Task 3 (autostart/tray verification)**. Audit the existing first-launch ON default, sticky user OFF, and absence of automatic Yandex launch/elevation; do not rewrite behavior already correct. Do not begin Task 4 acceptance, updater or packaging until Task 3 is complete. Full owner-approved order remains W150.


## W151 — Task 1 current-player/UI reconciliation (15 November 2026)

- **Task 1 implementation and CI are complete.** Final code HEAD: `dbd96fe99e498241125deb870215276215ae425a` on `main`. W151 implementation commit: `2f1c695045a1d3daef4ef4cb5e60fc74cd1688d0`; final test-assertion correction: `dbd96fe99e498241125deb870215276215ae425a`.
- Exact pre-W151 rollback point supplied by the owner and used as the parent: `backup/windows-main-pre-w150-owner-scope-handoff-20261115` @ `0524158177beeedb50bff85d59ae573d90c19823`. The live pre-code main HEAD was `b57f57c1094446a0fccf68d108800be792e19f94`.
- **CI:** Main `43706073512` SUCCESS; Windows integration `43706073517` SUCCESS. Native-host suite: 134/134; W15 companion suite: 375/375; GUI warning-as-error compile, supervisor warning-as-error build and W128 non-elevation checks SUCCESS. No installer or intermediate package was built.
- Main/compact UI now refresh from accepted current-player heartbeats, with a 1-second lease-expiry pulse to clear stale state after heartbeat loss. Startup completes only on a fresh enabled heartbeat. Track placeholders preserve PLAYING/PAUSED/STOPPED and never tell the owner to launch a track merely because the bridge is reconnecting.
- Native host now recognizes a newly published companion capability-file generation even when token bytes remain the same; it clears previous-session track/source caches and forces a fresh current-player sample/heartbeat. OFF→ON bridge transitions also bypass the normal sampling/heartbeat delay. Regression tests cover same-renderer queue changes (My Wave/Next), republished token-file generation and OFF→ON reconnection.
- Source truth remains fail-closed: ACTIVE_REPLACEMENT requires the exact current signed decoder proof and PLAYING; ORIGINAL is accepted only with the explicit `NATIVE_ORIGINAL_SOURCE_VERIFIED` witness. The native host does not currently emit that dedicated original witness, so uncertain original audio intentionally remains UNKNOWN. Audibility, mapping, stale status or an old heartbeat cannot invent ORIGINAL or replacement playback.
- W141–W147 behavior remains in place, including W142 retired-host ordering, W143 signed-feed coherence, W144 native audibility selection, W145 safe-point scheduler, W146 PAUSED/STOPPED precedence and W147 explicit native-silence precedence.
- **Owner-PC acceptance is still pending.** CI proves code/contracts only; it does not prove audible playback, current song display or VPN behavior on the owner's Windows machine. Do not claim Task 1 is field-accepted yet.
- **Next work is Task 2 only:** investigate the reported VPN A→B pop/click while preserving the faster reconnect; separately cover original tracks, ACTIVE_REPLACEMENT candidates and My Wave; recheck crossfade after recovery. Do not open historical Issues #53/#54/#56/#57/#58 as separate tasks. Task 3 autostart, Task 4 grouped regression/acceptance, Task 5 updater and Task 6 one final EXE+ZIP remain in W150 order.

---

# CELIKOM Windows — AUTHORITATIVE CURRENT HANDOFF / 14 November 2026

## W148 — P0 production signed-release pipeline prepared, NOT yet deployed (15 November 2026)

- Working branch `main`, W148 pre-change exact backup `backup/windows-main-pre-w148-production-release-pipeline-20261115` @ `18ad2b8b6aa66012f5e2bb61d779d0e2dd51bd10`. Latest W148 code before docs `f70e1c23fe69be5ba3786d845b11459d1064bb5c`.
- Signed release build/publisher **code** added: public pinned trust injection (source defaults stay empty), offline protected P-256 key generator, schema-2 manifest/package signature verifier, protected **manual** GitHub Actions workflow `windows-stable-signed-release.yml`, real Authenticode PFX/chain/fingerprint gates, immutable Hostinger publisher with exact official-domain HTTPS byte verification. Continuous regression tests wired in Windows integration CI.
- Owner/infra external dependencies in [GitHub issue #59](https://github.com/manufact-test/nomusic/issues/59), not automatically assigned: approved DNS+TLS and actual Hostinger root for celikom.com, trusted CA code-signing provider/certificate, protected GitHub environment/secrets/manifest private key. Current GitHub connector CANNOT set those admin-managed secrets or issue a real code-signing certificate.
- Crucial: **production auto-update NOT running**. Current installed unsigned 0.24.37 still has empty pins and needs one trusted signed bootstrap; then next signed release can update automatically. No package built, no deployment, no owner PC install, no real rollback test. W119/W139 constraints intact. Details `docs/windows/W148-PROTECTED-SIGNED-STABLE-RELEASE-PIPELINE-20261115.md`.
- W148 automated CI may still be running; confirm latest source HEAD after documentation before declaring green. Do not run manual signed-release workflow until real protected secrets/trust/domain are provisioned. All six issues remain OPEN.

## W147 newest playback-evidence continuation — 15 November 2026

- **Latest native Windows code HEAD before this documentation commit:** `e174551dc086f8812f05840aa8e22d926889ad31`, only on `main`. Exact pre-W147 rollback backup `backup/windows-main-pre-w147-electron-audible-property-precedence-20261115` @ `d63e5505e7300e83cb6307ba9a23866bc3db45a2`.
- W147 native host `nativeAudible(view)`: when Electron `isCurrentlyAudible()` provides an explicit boolean **false**, it now overrides an older `audio-state-changed(true)` event. True is also respected. Use last event only if the native method is absent/throws/unavailable. Current-player choice and PLAYING heartbeat share the same predicate. No media commands/audio edits; unknown sources remain UNKNOWN without signed current decoder proof.
- New W23 regression uses a simulated native false + delayed old audible event, advances the observer clock past the 4-second renewal and confirms the renewed heartbeat cannot claim PLAYING or CELIKOM replacement. W147 code commits `6a39633e476c1d349acaae6517a2a186402d4cc9`, `96135537190ccb287f36ce056f5bb2fb7f6de45c`, `e174551dc086f8812f05840aa8e22d926889ad31`.
- W145 both CI SUCCESS: Main 43696999275, Windows integration 43696999268. W146 both CI SUCCESS: Main 43697181373, Windows integration 43697181363. W147 CI at latest code `e174551dc0`: Main 43697422458 and Windows integration 43697422432 were running when authored; **check before declaring green**.
- No new EXE/ZIP, no production trust keys/cert/feed, no user-PC acceptance. Previously installed 0.24.37 stays unchanged, all six issues OPEN. W119/W139 and the following handoff sections remain binding.

## W145/W146 latest continuation — 15 November 2026

- **Live Windows code HEAD at this handoff:** `d4a94f63411e328b47aa5fe16b8acfbaf9dcb2a6`, working branch **main only**.
- W145: exact pre-code backup `backup/windows-main-pre-w145-pending-safe-point-scheduler-20261115` @ `8642b98ba05c27f445d1bb110b78bae1ea09dc4e`, code `6094432757c80d0305a1d49b32868a591b960ea0`. After an authenticated signed package has already been downloaded and verified, the existing stable-update scheduler runs a low-cost safe-point check every 30 seconds, not 30 minutes. While Yandex is running / playback not safe, **no network feed/payload re-fetch** occurs in the short interval. The install coordinator and existing strict gate still re-validate before Supervisor/installer; no audio interruption or bypass of missing production trust. W15 test covers interval and skip policy.
- W146: exact pre-code backup `backup/windows-main-pre-w146-compact-paused-source-status-20261115` @ `6094432757c80d0305a1d49b32868a591b960ea0`, code `d4a94f63411e328b47aa5fe16b8acfbaf9dcb2a6`. Compact popup renders pending mapping status only if the **fresh current native player state is PLAYING**; PAUSED and STOPPED take precedence. Tests assert no stale green while paused.
- W142, W143 and W144 both Main CI and Windows integration CI **SUCCESS** (W142 43696125856 / 43696125894; W143 43696396674 / 43696396709; W144 43696528740 / 43696528671). W142–W144 documentation HEAD `8642b98ba05c27f445d1bb110b78bae1ea09dc4e` also both SUCCESS (43696634634 / 43696634618). W145/W146 are newer and require checking latest CI before acceptance.
- **No live updater yet:** legitimate official HTTPS release origin, protected P-256 private signing key and matching public pin, trusted Authenticode signer fingerprint/certificate, protected package publisher and real owner-PC signed bootstrap/rollback not provisioned. Existing owner-installed unsigned 0.24.37 cannot autoupdate. Never invent anchors or claim this code delivered an update. No installer built, no owner-PC listening verified. All six issues #52 #53 #54 #56 #57 #58 OPEN, W119/W139 authoritative.

## W142–W144 continuation — 15 November 2026 (latest code)

- Working branch is ONLY `main`; latest W144 code HEAD `18aa813f0cbb83832b3f6f0e8150ada0a5439757`. No new Windows TEST product, installer or release. Do not alter Android or browser extension. All six issues #52 #53 #54 #56 #57 #58 remain OPEN.
- W141 final `09c7b0168c4d70f2d7afe6e974a90600391bd65c`: Main CI 43695545111 SUCCESS and Windows integration CI 43695545121 SUCCESS. Confirms code only, NOT owner-PC listening or audio quality.
- W142 exact pre-change backup `backup/windows-main-pre-w142-gui-source-and-heartbeat-handoff-20261115` @ `09c7b0168c4d70f2d7afe6e974a90600391bd65c`; code `c919d1ed15842bd9d704f2d6cdb7540c78de3b77`. Main GUI source text now agrees with compact GUI: active green only when exact current signed decoder + PLAYING; original only if directly identified; pause/stop/UNKNOWN do not inherit old mapping. Bridge retires superseded native process instance IDs, so late old heartbeats cannot resurrect a previous song. W142 Main CI 43696125856 and Windows integration CI 43696125894 SUCCESS.
- W143 exact pre-change backup `backup/windows-main-pre-w143-stable-feed-coherence-20261115` @ `c919d1ed15842bd9d704f2d6cdb7540c78de3b77`; code `e772ca977b70ad9c1a9b972175e93907db04235c`. Authenticated latest-feed JSON and detached signature are two static HTTPS files; a short publication race can mix generations. Added bounded 3-attempt signature-mismatch-only re-fetch of BOTH files and no-cache headers; permanently invalid signatures, redirects, malicious manifests still fail closed. Added W15 regressions for both transient recovery and persistent mismatch. This does not publish a production feed or provision keys/certificates.
- W144 exact pre-change backup `backup/windows-main-pre-w144-active-audibility-reconciliation-20261115` @ `e772ca977b70ad9c1a9b972175e93907db04235c`; code `18aa813f0cbb83832b3f6f0e8150ada0a5439757`. Native playback view selection and current-track heartbeat now consult the SAME Electron isCurrentlyAudible / audio-state-changed predicate. A true native audible property may report PLAYING even before an event arrives, but source remains UNKNOWN without exact current decoder proof. Added W23 regression.
- W143/W144 fresh CI runs were still IN PROGRESS when this note was authored: W143 main 43696396674 / Windows 43696396709; W144 main 43696528740 / Windows 43696528671. Re-check before declaring green.
- Mandatory P0 still blocked on REAL owner-approved official HTTPS origin, protected P-256 release signing key + exact client public-key pin, trusted Authenticode signer certificate + fingerprint, protected atomic publisher, a one-time trusted bootstrap for currently installed UNSIGNED 0.24.37 and actual owner-PC end-to-end install/forced-rollback. Never insert made-up values or claim a functioning auto-update channel.
- Next work: finish signed production publication and first bootstrap once genuine trust infrastructure is available; continue current Yandex source proof (ORIGINAL currently conservatively UNKNOWN), restart/VPN UI consistency, audible VPN pop/hiss without slower reconnect, autostart and remaining six issue acceptances. Do not request an intermediate owner installer. Preserve the W119/W139 contract.

> **READ FIRST.** This is the controlling handoff for CELIKOM Windows. Read `docs/windows/W119-AUTHORITATIVE-OWNER-CONTRACT-AND-WINDOWS-HANDOFF-20261114.md`. If any older W-series note or previous chat conflicts with this top section or W119, follow W119. Older sections below are technical history, not current work orders.

## W140/W141 current continuation — 15 November 2026

- Work only on main. Exact W140 pre-change backup: backup/windows-main-pre-w140-stable-update-download-during-playback-20261115 @ e2c7e3917fae29f14750007a49a541bb97c9c8b4. Exact W141 pre-change backup: backup/windows-main-pre-w141-current-player-sync-20261115 @ bd186871823b76a1208e302298c4efd8296e72d7.
- W140: signed feed discovery / authenticated current-install inspection and SHA-256 + Authenticode verified downloads are no longer blocked by active playback. Verified installer is held in a local pending cache and rechecked at the next safe install point. Same Supervisor and DPAPI rollback journal are retained. Full Windows CI SUCCESS at bd186871823b76a1208e302298c4efd8296e72d7.
- W140 remains non-production: StableUpdateTrustConfiguration.cs has no approved official HTTPS origin, P-256 public key or Authenticode signer fingerprint. Owner-review 0.24.37 is unsigned and lacks pins. No actual signed production feed or owner-PC installation/rollback was proven. Never fabricate credentials or declare auto-updates operational. A one-time trusted bootstrap may be necessary. The existing GitHub connector did not allow fetching release secret/environment metadata.
- W141: native main host selects one authoritative active/audible Yandex view; other webContents cannot overwrite the current song. Renderer player observer exposes explicit PLAYING, PAUSED, STOPPED. Current signed decoder proof is the sole ACTIVE_REPLACEMENT witness; ambiguous sources remain UNKNOWN (ORIGINAL requires further actual decoder attribution). 4-second sequenced native heartbeats refresh stable playback, local bridge discards out-of-order previous-song heartbeats and expires the UI state after 12 seconds. Compact popup/main status use current source evidence rather than mapping-only or stale labels. Existing 15-second UI pulse now refreshes an expired view after a silent host disconnect.
- W141 CI at 858c68128b09dc5a71cd34868bc123a1a52a3173: both Main CI and Windows integration CI SUCCESS including the added current-player/order/renewal tests. The later UI-lease documentation commit still requires fresh CI verification.
- No new installer, ZIP or Windows TEST product was created. Do not touch Android, browser extension or original audio. Issues #52 #53 #54 #56 #57 #58 remain OPEN.
- Outstanding priorities: protected official update trust and atomic signed feed publication; first trusted bootstrap; real owner-PC safe-point update, READY and forced one-shot rollback; strong ORIGINAL/current decoder evidence; Windows restart/VPN current-song truth; VPN audible pop and crossfade/gain/regression checks. Preserve W119/W139 owner contract and existing 15-minute Yandex update watch.

## Hard product rule — one product, one main version

- There is **one existing CELIKOM Windows product**.
- `main` is the actual version being developed and maintained. All code work happens directly on `main`.
- `backup/*` contains exact snapshots of `main` made before substantial changes. Backups are rollback points only, not development branches.
- There is NO Windows TEST product/version, no separate QA product, no `experiment/*` development branch, no parallel product and no intermediate installer.
- Never call `main` a test version. Automated CI/tests are engineering checks only; they do not create another product.
- Do not change the agreed architecture or start from scratch.
- Do not build/send an installer until the complete agreed work is finished. Then produce one final EXE+ZIP from `main`.

## Exact repository state

- Repository: `manufact-test/nomusic`.
- Code baseline before the W119 documentation-only update: `2c12ea50797d8c395e4a2e169c9000d897dffb11`.
- Current first-owner-review source/code HEAD: `1338b73f3709847d5e42f9eb47cc8e8078b70374` (W138, CELIKOM 0.24.37 private one EXE+ZIP). W139 is a documentation-only owner-feedback handoff; live `main` is newer. The most recent Windows runtime implementation remains W135 `3045a9deaa7f87e031313741b64f4f9fbdd6e5c5`. Always fetch live `main` before coding.
- Last Windows app implementation commit: `3045a9deaa7f87e031313741b64f4f9fbdd6e5c5` (W135 source-decision incident retention); W135 regression-test/final code-test HEAD: `5a40357d28f1a1cc4f467a16bfaaaf38aa530b3f`; W134 regression-test commit: `d6c091fb109baeaa1690b15ca3f90d7c914a279a`; W133 runtime commit: `d548ed0af0f3717669c1fbcd903fc4f626428c7e`; W133 regression-test commit: `d79c20f37ce7428fca0e1abf1bdf3b0ad1a05832`; W132 test: `c02cd4988292598f81e857062279d0179253a42a`; W131 runtime/test: `5fb5f32d0364d476889bf56d0f8e8fc0e38d71b2` / `2f41091d1af072483ed5c79782958002b0ee2101`; W127 implementation/test: `4fe42d745b6708524c65eb4f9855e026f314fefa` / `7e4c8268cba30f781a3fa091d9657718ec463b66`; W128 CI policy commit: `cedcc45e5151afa62c1b292a7f4e2220226b6ac3`; W130 host/test: `5acbcc2af1a6cee85ef96bc81ce45d56d2f90726` / `74b27a27c8f1560591ed9ae11c17f5fceb0d538e`.
- Exact pre-W128 CI policy backup: `backup/windows-main-pre-w129-elevation-policy-guard-20261114` @ `911983107f257ec761f6c5c6666eec4748db3fd9`.
- Exact pre-W130 diagnostics backup: `backup/windows-main-pre-w130-cdp-property-observability-20261114` @ `312d61a62fb4abcb779df539503adf4226818185`.
- W130 Main CI [43605388622](https://github.com/manufact-test/nomusic/actions/runs/43605388622) and Windows integration CI [43605388482](https://github.com/manufact-test/nomusic/actions/runs/43605388482) — **SUCCESS**.
- Exact pre-W127 rollback snapshot: `backup/windows-main-pre-w127-current-decoder-witness-race-20261114` @ `4b7d2277d98986d8d4ab0ed9ba42a76fc25da810`.
- W127 Main CI [43603865004](https://github.com/manufact-test/nomusic/actions/runs/43603865004) and Windows integration CI [43603864999](https://github.com/manufact-test/nomusic/actions/runs/43603864999) — **SUCCESS**.
- Previous exact green W126 rollback snapshot: `backup/windows-main-post-w126-ci-green-20261114` @ `ed41f613640f55c8de4a027a8f6f12ac31a15093`.
- W126 Main CI [43601959568](https://github.com/manufact-test/nomusic/actions/runs/43601959568) and Windows integration CI [43601959593](https://github.com/manufact-test/nomusic/actions/runs/43601959593) — **SUCCESS**.
- Exact pre-W126 backup: `backup/windows-main-pre-w126-single-start-activation-20261114` @ `2488e38ebfae605c78d9e3f511d6fca0901c5cc2`.
- W120 Main CI [43596984190](https://github.com/manufact-test/nomusic/actions/runs/43596984190) — **SUCCESS**; Windows integration [43596984195](https://github.com/manufact-test/nomusic/actions/runs/43596984195) — **SUCCESS**.
- W121 Main CI [43597478523](https://github.com/manufact-test/nomusic/actions/runs/43597478523) — **SUCCESS**; Windows integration [43597478531](https://github.com/manufact-test/nomusic/actions/runs/43597478531) — **SUCCESS**.
- The W119 contract and earlier Android A1 work are preserved; this continuation changed only Windows companion code/tests and Windows documentation.

## W139 — latest owner acceptance and mandatory next priorities (15 November 2026)

**This section and `docs/windows/W139-OWNER-ACCEPTANCE-FEEDBACK-AND-AUTOUPDATE-P0-20261115.md` supersede older work-order priority where they conflict. Read W119, then W139 before coding.**

- Exact pre-W139 docs backup: `backup/windows-main-pre-w139-owner-acceptance-handoff-20261115` @ `4ba4fab4313939afc45ef782dd5344b206d11286`. W139 itself is documentation only; no Windows runtime code, installer or package changed.
- Owner has now begun listening to the existing 0.24.37 private unsigned build. Do not say he has not tested it. First feedback:
  - «Ты» (13 карат) and another track owner called «две гутыки» audibly played CELIKOM versions with apparently good sound/positive gain. Keep this as positive but limited listening evidence; do not close #52/#56.
  - Crossfade had no obvious clicks in the ordinary test; it still needs retest under VPN.
  - VPN A→B reconnect is faster than before, but owner hears a loud pop/hiss/strange sound. Preserve faster reconnect.
  - UI is seriously stale/incorrect: after a full CELIKOM close/reopen while Yandex already plays it still says waiting/loading; while «Ты» played it showed stale «Зима»/CENTR and «Версия CELIKOM передана Яндексу»; in «Моя волна» it kept that stale track while «Вечно молодой» played; after VPN it showed «Ожидаем» / «Запустите трек в Яндекс Музыке» while music was playing, with no current track.
- **P0 automatic CELIKOM app updater.** Owner explicitly says this is mandatory and expected the 0.24.37 update to download/install on his PC automatically. W138 only created a private GitHub Actions artifact; it was NOT delivered through CELIKOM. W124 coordinator/scheduler/Supervisor code is present but production trust is still empty, so `TryGetProduction` returns false and the automatic path does no feed check/download/install. Complete the real signed HTTPS feed, protected P-256 manifest key, trusted Authenticode signer, atomic publishing, automatic background download, safe-point install, Supervisor READY, real health check and forced one-shot rollback. Do not invent pins. See W139 for full requirements and the one-time bootstrap constraint: the current 0.24.37 binary has empty trust pins; a single trusted bootstrap may be needed, after which future updates must be automatic.
- **P1 UI/source-state synchronization** across restart, already-running Yandex, current-track changes, stop/pause, «Моя волна» and VPN reconnect. Never show stale previous-track metadata or claim transfer/active replacement without exact current playing decoder proof. Fix the state/event model, not just the label.
- **P1 VPN audio**: preserve the newly faster reconnect while removing the loud pop/hiss on replacement and original tracks; retest «Моя волна» and crossfade under VPN.
- **Autostart:** code inspection confirms `MainWindow` calls `EnsureFirstLaunchDefault`; first launch defaults HKCU Run ON and preserves a deliberate opt-out. Owner wants default ON. Verify the actual tray preference/registry state on his PC; do not overwrite an explicit OFF.
- Still unaccepted: #53 performance/elevation prompt, #54 Big City Life mid-track volume, #56 global gain/headroom/clipping (positive one-track listening is not global proof), #57 403→206 hiss, #58 original/«Моя волна» VPN continuity, diagnostics after disconnect, Yandex vendor update detection (preserve W102's 15-minute cadence). Issues #52/#53/#54/#56/#57/#58 remain OPEN.
- **Next work order:** (1) P0 automatic updater end-to-end; (2) P1 UI/source truth; (3) VPN A→B pop/hiss while preserving fast reconnect; (4) verify autostart; (5) remaining open audio/performance/diagnostics work; (6) one consolidated owner-PC acceptance including full updater + forced rollback. No extra package until integrated changes are ready.
- Keep working directly in `main`, one product, exact backups before substantial code changes, no Windows TEST product/branch, no interim installers, no architecture rewrite, no tiny owner check-ins. CI is not audible acceptance or proof of automatic delivery.

## Current state — what is and is not done

## W138 — single first-owner-review package BUILT, not production stable

- Private GitHub Actions [W138 owner-review run 43617609655](https://github.com/manufact-test/nomusic/actions/runs/43617609655) — **SUCCESS**, exact source `1338b73f3709847d5e42f9eb47cc8e8078b70374`.
- GUI, Supervisor and Inno all identify the one existing CELIKOM product `0.24.37` / `0.24.37.0`, preserving the same existing AppId and user data. No second product or Windows TEST line.
- One private artifact ID `14122464630`: `CELIKOM-W138-WINDOWS-02437-UNSIGNED.exe` (SHA-256 `1986c8269c990c91ad0b5910fc76021915ecdbafd1cdf796dce8b474ad03bb38`), `CELIKOM-Windows-0.24.37.zip` (SHA-256 `adc372876b49b9d9a3fbded7d7b1a751d69874469de0f71b8492cee39f39d16a`, exactly one EXE) and `SHA256SUMS.txt`. Outer archive, both digests and inner ZIP content checked independently.
- Exact main-source CI: [Main 43617609632](https://github.com/manufact-test/nomusic/actions/runs/43617609632) SUCCESS and [Windows integration 43617609631](https://github.com/manufact-test/nomusic/actions/runs/43617609631) SUCCESS. Stage job verified native code/GUI/Supervisor, single-AppId upgrade, per-user install/uninstall, zipped updater acceptance and checksums.
- Latest exact backups: W136 `backup/windows-main-pre-w136-stage-pipeline-current-version-20261114` @ `b7789299e901cf2218520f724043057744ef05ec`; W137 `backup/windows-main-pre-w137-one-package-exe-zip-20261114` @ `c2620d34884aad7d69d7e641e7b98e67bfe9716c`; W138 `backup/windows-main-pre-w138-first-owner-review-version-20261114` @ `48bd36d47aa1f7f2abfb0b89e95ffb8d5ecbdbdc`.
- **FIRST OWNER MANUAL ACCEPTANCE NOW REQUIRED**: real audio/VPN («Моя волна», «Ты», Big City Life, gain, 403→206), login/reconnect/diagnostics, Brave resource usage, startup/tray and suspicious elevation prompts. Group all checks; keep all six owner issues OPEN pending evidence. See `docs/windows/W138-SINGLE-OWNER-REVIEW-02437-EXE-ZIP-CI-20261114.md`.
- This owner-review build is **UNSIGNED**, private and **NOT** production. Automatic updater is dormant: no real approved stable HTTPS origin / P-256 public key / Authenticode signer fingerprint. Do not mass-distribute or declare automatic rollback production-proven. Do not create a second installer merely because docs or unrelated work changes.


## W136 — unblock the one existing CELIKOM Windows package-validation pipeline

- **Source/workflow-only fix; no installer built or published.** The old manually dispatched W20 packaging check expected a W56 executable and PE version 0.24.7, while the current application + Inno installer are 0.24.36. A future owner acceptance packaging run would fail even when the correct binary was built.
- Added `windows-companion/w20/stage-package-identity.ps1`: validates that the current Inno AppVersion/VersionInfoVersion exactly match the current GUI project version, validates the existing narrow internal updater-compatible filename, and only when `-RequireBuilt` is explicitly used checks the compiled installer and exports its actual name/version to later workflow steps.
- `.github/workflows/windows-w20-safe-installer.yml` now uses that exact current filename/version for the ZIP contract, install/uninstall smoke and private stage artifact rather than stale W56 paths. `Celikom.Companion.Tests/Program.cs` ZIP fixture now validates the real current assembly version and updater filename contract rather than hardcoded W100.
- Main Windows integration CI runs the metadata parity check **without building an installer** and rejects reintroduction of obsolete W56 paths.
- Exact pre-W136 backup `backup/windows-main-pre-w136-stage-pipeline-current-version-20261114` @ `b7789299e901cf2218520f724043057744ef05ec`. W136 code/workflow HEAD `152d07123bff4cebd71118141c766c8c62651c5a`.
- Main CI [43616078527](https://github.com/manufact-test/nomusic/actions/runs/43616078527) — **SUCCESS**; Windows integration [43616078592](https://github.com/manufact-test/nomusic/actions/runs/43616078592) — **SUCCESS**, including the new W136 source/installer identity gate, W15, Supervisor, GUI and original-source/VPN/audio tests.
- The W20 installer stage workflow remains **manual/internal** and was NOT dispatched. It does not create another product. First user acceptance package remains subject to W119's one-final-EXE+ZIP contract. Production update feed / approved P-256 key / Authenticode signer fingerprint are still absent; never substitute fake values or silently publish unsigned production updates.


# W127 — Reconcile current-decoder proof after queue identity race — 14 November 2026

- The Yandex queue's current track ID and native CDP `kUrl`/`kIsPlaying` events can arrive in either order. Previously, a valid signed CELIKOM decoder event arriving before the queue ID could remain unconfirmed if no further CDP property event followed.
- W127 retains bounded per-player decoder state and reconciles it after the existing current-track sample. It still requires a currently playing exact signed CELIKOM source mapped to the same current Yandex track; HTTP 206, grant delivery or mapping alone never turns the UI green.
- When the late queue ID makes the proof valid, the host emits the source witness once, sends the verified-only heartbeat and invokes the existing hook that cancels only a still-pending redundant reload. CDP detach/player destruction invalidate the witness.
- Regression coverage explicitly delivers decoder properties before queue identity and verifies no early attribution, one later source proof, verified heartbeat, pending-recovery hook and URL-free diagnostics.
- W127 implementation: `4fe42d745b6708524c65eb4f9855e026f314fefa`; test: `7e4c8268cba30f781a3fa091d9657718ec463b66`; exact pre-change backup: `backup/windows-main-pre-w127-current-decoder-witness-race-20261114` @ `4b7d2277d98986d8d4ab0ed9ba42a76fc25da810`.
- Main CI [43603865004](https://github.com/manufact-test/nomusic/actions/runs/43603865004) and Windows integration CI [43603864999](https://github.com/manufact-test/nomusic/actions/runs/43603864999) — **SUCCESS**.
- **#52 remains OPEN.** This fixes event ordering only; it does not prove audible output on the owner's PC. VPN A→B and all other owner-PC audio acceptance also remain open. No installer was built.

# W128 — Read-only CELIKOM elevation launch audit and CI guard — 14 November 2026

- Reviewed the current app launch paths, updater, Supervisor launcher, native installer modules, project settings and Inno installer. No explicit `runas` / `Verb="runas"` request was found in the reviewed CELIKOM paths.
- MainWindow launches Yandex normally; AppUpdateManager launches the verified Inno updater without an elevation verb; Supervisor is a same-user child process with `UseShellExecute=false`.
- The installer declares `PrivilegesRequired=lowest` and installs under `%LOCALAPPDATA%\Programs\CELIKOM`; the release gate checks this policy.
- Added a Windows Integration CI guard that rejects explicit `runas` in reviewed launch paths, requires the updater/Supervisor launch modes, keeps the installer per-user, and rejects an administrator manifest in the companion project.
- Exact pre-guard backup: `backup/windows-main-pre-w129-elevation-policy-guard-20261114` @ `911983107f257ec761f6c5c6666eec4748db3fd9`; guard commit: `cedcc45e5151afa62c1b292a7f4e2220226b6ac3`.
- Main CI [43604761393](https://github.com/manufact-test/nomusic/actions/runs/43604761393) and Windows integration CI [43604761386](https://github.com/manufact-test/nomusic/actions/runs/43604761386) — **SUCCESS**, including the new W128 guard step.
- This does **not** identify the prompt the owner saw, prove it came from Yandex, or establish that it was harmless. #53 remains OPEN until the prompt publisher/title is known and owner CPU/RAM/GPU evidence is available. Do not grant administrator rights to an unknown prompt.
- Full audit: `docs/windows/W128-READ-ONLY-ELEVATION-LAUNCH-AUDIT-20261114.md`. No runtime behavior changed and no installer was built.

# W135 — Retain source-decision evidence in durable owner diagnostics — 14 November 2026

- Diagnostics/archive policy and regression tests only; no player or audio behavior changed.
- Previously emitted source-decision events were not all treated as durable incidents. W135 preserves the allowlisted ORIGINAL, UNKNOWN, ACTIVE_REPLACEMENT, source-revalidation/reload, source-left and exact decoder-match events in the seven-day incident archive and 15-minute automatic support snapshot.
- Numeric track IDs remain validated. No signed URLs, tokens, audio data or arbitrary error messages are stored. Ordinary `NATIVE_CONNECTED` remains polling/status chatter, not an incident.
- W15 tests verify these source decisions survive more than 2,500 later native status polls and remain in the persistent owner TXT/archive without secrets.
- Exact pre-W135 backup: `backup/windows-main-pre-w135-source-transition-incident-retention-20261114` @ `adc87e2d3358fb64fba0a760518374e7d88e56c5`.
- Implementation commits: `e8e482da6acbfc677823e754066baa14e6e7d48e`, `3045a9deaa7f87e031313741b64f4f9fbdd6e5c5`; regression-test/final code-test HEAD: `5a40357d28f1a1cc4f467a16bfaaaf38aa530b3f`.
- Main CI [43610044707](https://github.com/manufact-test/nomusic/actions/runs/43610044707) and Windows integration CI [43610044672](https://github.com/manufact-test/nomusic/actions/runs/43610044672) — **SUCCESS**. Full W22/W23/W60 original-source, VPN, 403 and audio regression step plus W15 native contract tests passed.
- **#58 remains OPEN** pending real owner-PC VPN A→B playback acceptance; **#52 remains OPEN** pending owner-PC proof of audible replacement on «Ты» (13 карат).
- Full record: `docs/windows/W135-SOURCE-DECISION-INCIDENT-RETENTION-20261114.md`. No installer was built.

# W134 — Immediate downgrade coverage for every decoder-proof invalidation — 14 November 2026

- Regression tests only; W133 runtime behavior is unchanged.
- W134 verifies that each of four invalidation events — pause (`kIsPlaying=false`), current player destruction, current decoder pipeline error and CDP observer detach — immediately downgrades the exact current track from `NATIVE_SOURCE_VERIFIED` to neutral `NATIVE_MAPPING_ACCEPTED`.
- Each subtest starts with an exact signed current decoder and verifies the green heartbeat first. It then triggers one invalidation and checks the neutral heartbeat without waiting for the regular 2.2-second sampler. Signed media URLs must remain absent from heartbeat payloads and diagnostics.
- Exact pre-W134 backup: `backup/windows-main-pre-w134-verified-status-invalidation-matrix-20261114` @ `63b3a155bde732d527cfa57e5280bae69b3acbb6`.
- Regression-test/current code-test HEAD: `d6c091fb109baeaa1690b15ca3f90d7c914a279a`.
- Main CI [43609116940](https://github.com/manufact-test/nomusic/actions/runs/43609116940) and Windows integration CI [43609116972](https://github.com/manufact-test/nomusic/actions/runs/43609116972) — **SUCCESS**. Full W22/W23/W60 original-source, VPN, 403 and audio regression step passed, including all four W134 subtests.
- **#52 remains OPEN** pending owner-PC proof that «Ты» (13 карат) actually plays the alternate source; CDP source selection is not speaker-level proof.
- Full record: `docs/windows/W134-IMMEDIATE-DECODER-STATUS-INVALIDATION-MATRIX-20261114.md`. No installer was built.

# W133 — Immediate downgrade when current decoder proof is invalidated — 14 November 2026

- The native host previously waited for the regular 2.2s status sample to remove a green `NATIVE_SOURCE_VERIFIED` heartbeat after CDP observed that the current decoder left CELIKOM, stopped playing, was destroyed, errored, or the observer detached.
- W133 immediately sends the exact current track's heartbeat as neutral `NATIVE_MAPPING_ACCEPTED` on those proof-invalidating events. The status cache is updated at the same time; a failed local heartbeat rolls the cache back so the regular sampler can retry. A later fresh signed-current-decoder proof can restore `NATIVE_SOURCE_VERIFIED`.
- No player control, source reload, URL, queue or audio behavior is changed.
- W133 regression verifies immediate downgrade after source-left and successful promotion back to verified when the exact signed source becomes current again. Signed URLs remain out of heartbeats and diagnostics.
- Exact pre-W133 backup: `backup/windows-main-pre-w133-immediate-source-witness-downgrade-20261114` @ `2958b9d03fdd803eaab2f20dfad3c9bb4c63d1d9`.
- Runtime commit: `d548ed0af0f3717669c1fbcd903fc4f626428c7e`; regression-test/current code-test HEAD: `d79c20f37ce7428fca0e1abf1bdf3b0ad1a05832`.
- Main CI [43608584535](https://github.com/manufact-test/nomusic/actions/runs/43608584535) and Windows integration CI [43608584562](https://github.com/manufact-test/nomusic/actions/runs/43608584562) — **SUCCESS**.
- **#52 remains OPEN** pending owner-PC proof that «Ты» (13 карат) actually plays the alternate source; CDP source selection is not speaker-level proof.
- Full record: `docs/windows/W133-IMMEDIATE-DECODER-WITNESS-STATUS-DOWNGRADE-20261114.md`. No installer was built.

# W132 — VPN A→B revalidation after verified source-left — 14 November 2026

- Regression coverage only; no runtime code changed. The test starts with a current CELIKOM replacement, simulates the verified CDP source-left event, then applies VPN state-off and state-on with a fresh authenticated no-replacement result.
- It verifies there is no duplicate `QUALITY_CHANGE` reload after the decoder has returned to Yandex original, no replacement reload after the fresh no-match response, and no loss of playing state or position.
- This complements W98's original-from-start no-reload test and W131's verified source-left/state-off race test.
- Exact pre-W132 backup: `backup/windows-main-pre-w132-vpn-source-left-revalidation-20261114` @ `507052a14841ee08bf2ade513315618612130e8a`.
- W132 regression-test/current code-test HEAD: `c02cd4988292598f81e857062279d0179253a42a`.
- Main CI [43607847556](https://github.com/manufact-test/nomusic/actions/runs/43607847556) and Windows integration CI [43607847627](https://github.com/manufact-test/nomusic/actions/runs/43607847627) — **SUCCESS**. Full W22/W23/W60 original-source, VPN, 403 and audio regression step passed.
- **#58 remains OPEN** pending real owner-PC VPN A→B acoustic acceptance. CI proves CELIKOM does not reload the original source in this simulated sequence; it does not prove Yandex itself has no audible network-route pop.
- Full record: `docs/windows/W132-VPN-A-TO-B-SOURCE-LEFT-ORIGINAL-REVALIDATION-20261114.md`. No installer was built.

# W131 — Invalidate stale source mapping after verified decoder source-left — 14 November 2026

- When passive CDP has proved that the current decoder left its previously verified CELIKOM signed source, the renderer now clears that track's stale mapped-source marker immediately. This happens before checking whether CELIKOM is still enabled, so a racing VPN/entitlement state-off transition cannot issue a redundant `QUALITY_CHANGE` reload of a track already returned to Yandex original.
- If CELIKOM remains enabled, the existing bounded recovery path is preserved and can reapply a fresh authenticated grant. No entitlement bypass or player architecture change.
- Regression test verifies source-left followed immediately by state-off causes no second reload and preserves playing state/position. Existing W99 recovery still passes.
- Exact pre-W131 backup: `backup/windows-main-pre-w131-source-left-map-invalidation-20261114` @ `9eb710d1227f56419d6e9f35b34b44b7941ef8ae`.
- Runtime commit: `5fb5f32d0364d476889bf56d0f8e8fc0e38d71b2`; test/current code-test HEAD: `2f41091d1af072483ed5c79782958002b0ee2101`.
- Main CI [43606490844](https://github.com/manufact-test/nomusic/actions/runs/43606490844) and Windows integration CI [43606490908](https://github.com/manufact-test/nomusic/actions/runs/43606490908) — **SUCCESS**.
- **#58 remains OPEN** pending real owner-PC VPN A→B playback acceptance; this fixes a redundant CELIKOM reload after a verified source-left event, not every possible Yandex/network audio pop.
- Full record: `docs/windows/W131-VERIFIED-SOURCE-LEFT-STALE-MAPPING-INVALIDATION-20261114.md`. No installer was built.

# W130 — Safe CDP property-visibility diagnostics — 14 November 2026

- The previous owner export could not distinguish "CDP Media attached but no player-property events" from "player-property events arrived but Yandex did not expose `kUrl`".
- The passive host now records `PLAYER_CDP_PROPERTIES_SEEN` and `PLAYER_CDP_URL_PROPERTY_SEEN` based only on property names. It never logs the URL value, token, SID or other player-property values.
- The owner TXT export and automatic support snapshot expose `NativeDecoderPropertiesObserved` and `NativeDecoderUrlPropertyObserved`. Both event codes are retained in bounded incident history.
- The export explicitly says these booleans only show Media-domain field availability. They do not prove current-track identity, decoder selection or audible replacement.
- Regression tests cover properties without `kUrl`, subsequent `kUrl` presence, secret-free diagnostics, durable event retention and both export formats.
- Exact pre-W130 backup: `backup/windows-main-pre-w130-cdp-property-observability-20261114` @ `312d61a62fb4abcb779df539503adf4226818185`; code/test HEAD: `74b27a27c8f1560591ed9ae11c17f5fceb0d538e`.
- Main CI [43605388622](https://github.com/manufact-test/nomusic/actions/runs/43605388622) and Windows integration CI [43605388482](https://github.com/manufact-test/nomusic/actions/runs/43605388482) — **SUCCESS**.
- **#52 remains OPEN.** These are diagnostic visibility flags only. W127's strict current-track/signed-decoder proof remains unchanged, and actual playback acceptance still requires the owner's PC.
- Full record: `docs/windows/W130-SAFE-CDP-PROPERTY-VISIBILITY-DIAGNOSTICS-20261114.md`. No installer was built.

# W120 — Native-host performance evidence without changing playback cadence — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W120 code backup: `backup/windows-main-pre-w120-native-host-performance-20261114` @ `e4da7bad1bc83b4eb2888de6c3f4d67a0732af78`.
- W120 implementation commit: `9a9193d7bd728a4ff1a2da2f8b5f11c42c4d8a7b`.
- Main CI [43596984190](https://github.com/manufact-test/nomusic/actions/runs/43596984190) and Windows integration CI [43596984195](https://github.com/manufact-test/nomusic/actions/runs/43596984195) — **SUCCESS**.

## Changes

1. Native host caches the last safe state sent to the Yandex renderer. Identical state is not executed into the renderer repeatedly; the cache is cleared on renderer reinjection.
2. A failed local state read invalidates the cached enabled/disabled observation, so the next successful read can report the transition truthfully.
3. Every 30 seconds the host samples only its own Electron main-process CPU usage. At 80% or higher it records the fixed event `NATIVE_ELECTRON_CPU_HIGH`. Raw CPU counters, PIDs, process names, account identifiers and audio metadata are never written.
4. `DiagnosticLog` recognizes the CPU event as an incident, includes `ElectronCpuHighObserved` in the text export and preserves the event in support snapshots and diagnostic history.

## Deliberately unchanged

- Existing 300ms native relay cadence remains unchanged.
- CDP playback observation and 403 recovery remain enabled.
- No audio-source, gain, VPN or original-file behavior was changed.
- This is instrumentation and removal of redundant renderer IPC, **not proof that #53 is fixed**.

W23 tests cover unchanged-state deduplication, fixed CPU-threshold recording and the unchanged 300ms cadence. W15 tests cover diagnostics allowlisting, export, imported incidents and durable archive. No installer was built. Owner Task Manager evidence is still required to identify whether the load comes from CELIKOM, Brave, Yandex renderer, GPU or another process.

# W121 — Gate duplicate Start actions during first connection — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W121 code backup: `backup/windows-main-pre-w121-start-action-gate-20261114` @ `9a9193d7bd728a4ff1a2da2f8b5f11c42c4d8a7b`.
- W121 implementation commit: `62ff2b67f869607e20e9d8899113f391eab80c7e`.
- Exact green rollback snapshot: `backup/windows-main-post-w121-ci-green-20261114` @ the W121 commit.
- Main CI [43597478523](https://github.com/manufact-test/nomusic/actions/runs/43597478523) and Windows integration CI [43597478531](https://github.com/manufact-test/nomusic/actions/runs/43597478531) — **SUCCESS**.

## Changes

- Added the pure `PlaybackStartGate` policy and use the same rule in both the Start handler and Start-button availability.
- The gate blocks Start while the bridge is not ready, integration/update is busy, a previous Start is still pending, the app is closing, or playback is already enabled for the active native module.
- `StartAction` immediately calls `UpdateSafe()` after setting `_compactStarting`, so repeated clicks cannot be silently accepted by an enabled-looking button and then ignored.
- During the initial host/entitlement check, the compact hint says `Проверяем Яндекс.Музыку…`; the normal loading status remains for the active Yandex startup phase.
- W15 tests cover each blocked/allowed gate state; the Windows integration workflow statically guards both call sites and the pending-start hint.

This addresses the duplicate-click race in the first/repeated Start flow. It does **not** close the broader first-run/reboot/autostart owner acceptance, and it does not change audio, native installation, VPN or updater behavior. No installer was built.

# W122 — Trusted Supervisor readiness handshake and immutable helper snapshot — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W122 code backup: `backup/windows-main-pre-w122-supervisor-handshake-20261114` @ `7d0d6e162e8a51c169db05fc232674d6de93f4d2`.
- W122 implementation commit: `7622b8034a47526547d406ed4ec5988afc0569b5`.
- Exact green rollback snapshot: `backup/windows-main-post-w122-ci-green-20261114` @ the W122 commit.
- Main CI [43598267910](https://github.com/manufact-test/nomusic/actions/runs/43598267910) and Windows integration CI [43598267928](https://github.com/manufact-test/nomusic/actions/runs/43598267928) — **SUCCESS**.

## Changes

1. Added `StableUpdateSupervisorHandshake`: a transaction-GUID named pipe restricted to the current Windows user.
2. The Supervisor first reads and validates the DPAPI journal, checks production trust and its own signed image, performs its first engine tick, then sends READY. It does not acknowledge an unreadable or unsafe transaction.
3. Added `StableUpdateSupervisorLauncher.StartAsync(record)`. It accepts only a schema-2 `Prepared` transaction with matching pinned signer and previous Supervisor hash; it copies the old signed Supervisor EXE into that transaction's immutable snapshot directory, starts it from there with the existing `--supervise <guid>` contract, and waits up to eight seconds for READY.
4. The helper runs from the snapshot copy, so the future installer can replace the installed `CELIKOM.UpdateSupervisor.exe` without locking the image that is actively monitoring rollback.
5. Added a stable journal snapshot-path helper and a Windows named-pipe handshake regression test.

## Safety boundary / what is not yet complete

- W124 now wires the coordinator to this launcher. The coordinator advances `Prepared → InstallerStarted` and launches only after `StartAsync` returns READY; it rechecks the signed target and exact transaction-bound path at the final launch boundary.
- Production feed origin, P-256 public key and Authenticode signer fingerprint remain intentionally empty. The launcher and coordinator stay fail-closed while production trust is unconfigured; no keys, URLs or certificates were invented.
- W124 adds the 30-minute stable-update scheduler and signed package staging, but **the automatic updater is still not active in production** until the owner supplies/approves the real feed origin and production signing identities.
- No installer was built and no user installation was requested.

# W123 — Signed no-update result for stable manifest polling — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W123 code backup: `backup/windows-main-pre-w123-manifest-no-update-20261114` @ `40b8898c6c2489313f80b0e7a979b9e793e47dac`.
- W123 implementation commit: `5ae6b285889ca542d2ba30bbe25b5d3233800333`.
- Exact green rollback snapshot: `backup/windows-main-post-w123-ci-green-20261114` @ the W123 commit.
- Main CI [43598711117](https://github.com/manufact-test/nomusic/actions/runs/43598711117) and Windows integration CI [43598711096](https://github.com/manufact-test/nomusic/actions/runs/43598711096) — **SUCCESS**.

## Changes

- Added `StableUpdateManifestVerifier.VerifyIfNewer` and `StableUpdateManifestFetcher.FetchSignedIfNewerAsync`.
- The detached signature is always verified before a same-sequence manifest can be reported as a normal no-update result.
- An equal authenticated sequence returns `null` (no update); an older sequence or invalid signature remains a hard rejection.
- Existing strict `Verify` and bootstrap/version-specific fetch behavior remain unchanged.
- Tests cover equal-sequence no-update, tampered signature rejection, older-sequence rejection and the signed feed transport seam.

This is required for a real periodic stable updater: a current manifest must not be misclassified as a broken feed. It does not fetch from a production origin, launch an installer or activate the Supervisor. Production trust values remain empty. No installer was built.

# W126 — Single bounded entitlement activation for first install/upgrade — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W126 code backup: `backup/windows-main-pre-w126-single-start-activation-20261114` @ `2488e38ebfae605c78d9e3f511d6fca0901c5cc2`.
- W126 final code HEAD: `ed41f613640f55c8de4a027a8f6f12ac31a15093`.
- Exact green rollback snapshot: `backup/windows-main-post-w126-ci-green-20261114` @ the W126 code HEAD.
- Main CI [43601959568](https://github.com/manufact-test/nomusic/actions/runs/43601959568) and Windows integration CI [43601959593](https://github.com/manufact-test/nomusic/actions/runs/43601959593) — **SUCCESS**.

## Changes

1. First Start now checks the native integration state before sending activation. If the native module must be installed/upgraded, it goes directly to the existing consented `ConnectYandexAsync` transaction. It no longer POSTs activation once in `StartAction` and a second time after consent in `ConnectYandexAsync`.
2. `ConnectYandexAsync` now uses `StartupActivationRecovery.ActivateAsync`: at most one bounded retry for transient transport/temporary server errors, only while the same Start generation and account remain active. 401/403 and 429 are not retried.
3. After the fresh activation response, the compact access label/account confirmation/timestamp are updated and any older read-only preview is invalidated before the native install/upgrade continues.
4. A failed bounded network retry is handled as an entitlement/network failure, not mislabeled as native integration damage. It does not trigger the native-failure Yandex catalog refresh or a misleading install-failure modal.
5. Integration CI guards the order of the native readiness gate versus activation, the retry helper in the install path, and the post-activation account label update.

## Safety / scope

- The native integration still requires the existing explicit consent and existing signed native installer path. No new architecture, native patching strategy, or product variant was introduced.
- Server activation remains idempotent; this change removes the unnecessary duplicate request rather than changing trial/subscription policy.
- CI validates code paths only. No installer was built and no owner-PC install/audio test was requested.

# W125 — Invalidate current-decoder proof when CDP detaches — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W125 code backup: `backup/windows-main-pre-w125-decoder-detach-invalidation-20261114` @ `efbd6a1b1965472d8ad29519621a09d45a8651da`.
- W125 code HEAD: `d083218b4adb0b7fb1d1321d09b56245ab40fbd1`.
- Exact green rollback snapshot: `backup/windows-main-post-w125-ci-green-20261114` @ the W125 code HEAD.
- Main CI [43601333189](https://github.com/manufact-test/nomusic/actions/runs/43601333189) and Windows integration CI [43601333191](https://github.com/manufact-test/nomusic/actions/runs/43601333191) — **SUCCESS**.

## Change

The native host previously logged `PLAYER_CDP_DETACHED` but retained the last verified decoder witness. If the passive CDP observer detached after a valid `kUrl + kIsPlaying` pair, a stale proof could remain eligible for the green UI state for up to ten minutes.

On a valid webContents CDP detach, W125 now immediately clears:
- the verified current-decoder witness;
- expected signed audio and native media-success evidence;
- observer-ready state and bounded unfetched-reload attempts;
- cached decoder-player property state.

The existing renderer status can therefore fall back to mapped-but-unverified. It does not claim that a replacement is playing after losing the observer that proved it. The host does not try to seize or reattach DevTools; this path intentionally fails closed.

Windows integration CI now checks that the detach handler invalidates the witness and observer state. No playback command, reload, audio source, VPN behavior or original file was changed.

## What remains open

- #52 remains OPEN. W125 closes only the stale-proof-on-detach edge case; the real «Ты» playback/source behavior still needs owner-PC evidence.
- CI is not audible acceptance. No installer was built and no owner installation was requested.

# W124 — Stable update coordinator, safe scheduling and Supervisor-gated install — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W124 code backup: `backup/windows-main-pre-w124-stable-update-coordinator-20261114` @ `e734579f0f6e6aff1436bbccdbc1396a055cb788`.
- W124 final code HEAD: `cd5d2bf623f368529e5efd16e3d95c813975ad8d`.
- Exact green rollback snapshot: `backup/windows-main-post-w124-ci-green-20261114` @ the W124 code HEAD.
- Main CI [43600704215](https://github.com/manufact-test/nomusic/actions/runs/43600704215) and Windows integration CI [43600704211](https://github.com/manufact-test/nomusic/actions/runs/43600704211) — **SUCCESS**.

## Changes

1. Added `StableUpdateInstallCoordinator`, the single stable update transaction. It checks the immutable production trust tuple first and refuses to run if any production pin is absent.
2. Added a 30-minute WinForms scheduler in `MainWindow.StableUpdate.cs`. It is started only when production trust is configured. Each check defers while CELIKOM bridge is enabled, Yandex is running, playback state is unknown, or another install/host operation is busy.
3. The coordinator obtains/verifies the signed last-known-good installer, polls the signed latest manifest using W123 equal-sequence/no-update semantics, downloads and verifies a newer package, then rechecks idle state after download.
4. It creates a DPAPI-backed transaction with byte-identical previous/target signed installers and existing account/session/native identity, launches the immutable signed Supervisor snapshot through W122, and waits for its READY handshake.
5. Only after READY does it advance `Prepared → InstallerStarted`, reverify the exact journal-bound target installer (SHA-256, Authenticode signer, manifest identity), and call the existing Inno AppId upgrade path. A launch failure is recorded as `ManualRecovery`; no unverified or unjournaled path can be executed.
6. Restored W117's asynchronous first-install LKG bootstrap call and method. It remains behind the same pinned production trust and Yandex-idle gates.
7. Added regression coverage for trust-unconfigured fail-closed behavior and the installer-started-to-manual-recovery transition. Windows integration CI also guards the coordinator, scheduler, Supervisor launcher, signed latest-manifest fetch and final signed-launch path.

## Safety boundary / what is not complete

- Production feed origin, P-256 public key and Authenticode signer certificate fingerprint are still empty by design. No real official delivery URL, key or certificate was invented.
- Therefore `TryGetProduction` returns false in this build: the scheduler does not start and the coordinator does no network or install work. **The updater is wired but not activated for production.**
- Still required: owner-approved official HTTPS feed, production P-256 public key, production Authenticode certificate fingerprint and protected release-side signing/publishing. Then run the real signed-feed install, forced-failure, Supervisor crash/one-shot rollback, account/session preservation and recovery tests.
- CI validates code and simulations only. No production installer was built; no owner installation or audible test was requested.


### Implemented and CI-validated infrastructure
W122 adds the transaction-scoped current-user Supervisor READY handshake and immutable snapshot launch bridge. W123 adds signed no-update polling semantics. W124 wires both into a single fail-closed stable update coordinator, the 30-minute scheduler, journaled signed staging and final verified installer launch. W125 invalidates the current-decoder proof immediately if CDP detaches, preventing stale green playback claims. W126 removes the duplicate first-install activation POST and applies bounded transient retry to the consented native install path. The updater path remains dormant until production trust pins are provisioned.
W105–W118 contain signed-package validation, SHA-256/Authenticode checks, DPAPI rollback journal, previous/target package retention, independent Supervisor health witness, schema-2 exact payload identity, signed manifest generation, immutable version manifests, initial LKG bootstrap and shared fail-closed trust configuration. W20 verifies the existing installer definition contains exactly:
- existing CELIKOM app EXE;
- `integration/host.cjs`;
- `integration/renderer.js`;
- `CELIKOM.UpdateSupervisor.exe`.

This is meaningful implementation progress, **not a production-ready automatic updater**.

### W118 server-side gain proof
- W90 inventory: 1,493 active approved replacements; one nonzero-gain row (replacement 37 / track 40371622 / +11.5 dB), 1,492 zero-gain rows, no invalid values.
- W98 verified the existing private sidecar's exact source/version/gain/SHA identity and live signed HTTP 206 range. No new render or sidecar row was needed.
- Stage 5 integrity audit passed; live DB was not restored/rewritten and original audio objects were not changed.
- Nine W98 identity/TSV tests passed.
- This is server-side proof only. It does not close Windows listening/seek/Next/crossfade/403/VPN behavior or #56 owner acceptance.

### Still incomplete
- All owner issues #52, #53, #54, #56, #57 and #58 remain **OPEN**; CI is not audible or owner-PC acceptance.
- W120 adds privacy-safe Electron main-process CPU evidence and removes repeated identical renderer-state deliveries; #53 root cause remains unproven until owner diagnostics and a Task Manager CPU/RAM/GPU capture are available.
- W121 blocks duplicate Start clicks during pending host/entitlement checks and shows a small progress hint. First/repeated connection, reboot, tray and autostart still need one grouped owner-PC acceptance pass.
- #52 source truth (W125 now also clears stale decoder proof on CDP detach), #54 Big City Life volume, #56 real gain loudness/headroom, #57 audible 403→206 recovery and #58 original-track VPN continuity still need owner-side evidence; do not mark them fixed from CI.
- Automatic updater is not production-ready: W124 now provides the coordinator/MainWindow callsite, 30-minute scheduler, signed package staging, DPAPI transaction, Supervisor READY gate and final signed launch checks. Production P-256 pin, Authenticode signer pin and official HTTPS feed origin are still empty/unprovisioned, so the path is deliberately dormant. A real production-signed feed/install/crash/one-shot rollback run remains outstanding.
- No final Windows EXE+ZIP has been built or delivered.

### Legacy installer naming — do not misinterpret it
The current Inno script still has historical `AppVersion=0.24.36` and `OutputBaseFilename=CELIKOM-W100-WINDOWS-02436-INTEGRATED-QA-TEST-UNSIGNED`. This is stale W100 metadata, **not** a separate product or a request to create a TEST build. Do not build/distribute that stale artifact. At the end, update the final version/name as part of the single final `main` build. No interim installers.

## Owner's complete task list

1. VPN A→B: reliable, fast reconnect/recovery without long hangs, hiss or quiet return.
2. #52 «Ты» (13 карат): truthful confirmation of the actual alternate playback source; no false “active” state.
3. #53 Brave/Windows performance: W120 adds main-process CPU threshold evidence and renderer-state deduplication without changing the 300ms relay; root cause and owner Task Manager evidence still pending.
4. #54 Big City Life: fix the mid-track volume drop.
5. #56 admin gain: apply consistently to intended tracks; verify real loudness/headroom, seek, Next, crossfade and recovery.
6. #57 expired URL 403→206: remove hiss/click/pop during stream recovery.
7. #58 originals/«Моя волна»: prevent pops/cuts when VPN changes during non-replaced playback.
8. First connection/startup: W121 prevents duplicate Start actions while a connection check is pending; unsupported-version/server errors, subsequent launches and grouped owner-PC acceptance remain.
9. Diagnostics: keep available after disconnect and make status truthful.
10. Autostart/tray: correct Windows startup, tray, reconnect and failure recovery.
11. Yandex update detection: at least every 30 minutes, preferably faster.
12. Signed updater: finish signature, SHA-256, Authenticode and package-substitution protection.
13. Supervisor: W122 adds the signed helper snapshot and READY launcher; W123 adds signed no-update manifest semantics; W124 wires the coordinator, scheduler, signed staging, READY gate and final verified launch. Production trust and real end-to-end signed-feed/rollback acceptance remain outstanding.
14. Automatic one-shot rollback: restore last working version after failure while preserving account/DPAPI/native/user data.
15. Production update delivery: real keys/certificates, official HTTPS origin, signed manifests and reliable delivery.
16. Integrated verification: update, forced failure, rollback, account/native/Yandex safeguards and full regressions.
17. One final EXE+ZIP and mass update only after all work and owner acceptance.

Full descriptions and strict work rules are in W119. Do not drop or replace any item.

## Mandatory work method and next order

- Continue directly on `main`; create and verify an exact `backup/*` before substantial code changes.
- Work in large coherent blocks; do not stop after each small patch or ask the owner to manually test intermediate builds.
- Finish the complete Windows issue/task list and the updater end-to-end in the one existing product. Do not package early.
- Never touch Android, browser extension behavior, original audio files or unrelated server logic during Windows work.
- Do not invent production pins, certificates or feed URLs. Do not request passwords/emails/tokens or private signing keys in chat.
- CI is necessary but does not prove audible or owner-PC acceptance. Keep issues open until the behavior is actually fixed.
- After the complete work, run integrated CI/security/regression checks, then create one final EXE+ZIP from `main`. Group unavoidable owner-PC checks into one consolidated acceptance pass. Only after acceptance prepare mass update.
- Keep reports short and infrequent. Continue working without progress spam; ask the owner only when a real owner action is necessary.

## Controlling handoff

Read `docs/windows/W119-AUTHORITATIVE-OWNER-CONTRACT-AND-WINDOWS-HANDOFF-20261114.md` first. The W117/W118 and W100–W118 notes below are historical implementation records. Their old “next priority”, “QA package”, “TEST release”, branch and installer instructions are superseded. Do not follow them as current work orders.

---

## Historical technical records — archive only; W119 overrides stale next steps

## W117 — shared fail-closed trust configuration and dormant first-LKG startup bootstrap

- Added `StableUpdateTrustConfiguration.cs`: one shared immutable trust tuple for GUI and Supervisor (official HTTPS origin, P-256 public key DER, Authenticode signer SHA-256).
- All three production values intentionally remain empty. No environment variable, CLI argument, registry, remote manifest or user-editable file can supply/override trust. The manifest private key is not in the client and must remain in protected release infrastructure.
- `TryCreate` validates HTTPS root origin, P-256 curve OID, DER consumption and exact 64-hex signer fingerprint; returned public-key bytes are defensively copied.
- `MainWindow` starts `BootstrapStableRollbackIfConfiguredAsync` in the background after startup. It runs only when the full production trust tuple is configured AND CELIKOM's bridge is disabled AND no Yandex Music process is running. It only verifies/seeds the exact-version LKG package; it does not install, restart CELIKOM or touch Yandex.
- Failures produce only the fixed diagnostic code `STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE`; no URLs, paths, exception text, credentials or music data are logged.
- Supervisor now reads the same shared trust tuple and exits code 3 before journal access or installer execution while values are empty.
- W15 tests cover valid P-256 config, non-P-256 rejection, malformed DER/Base64, HTTP/path/user-info rejection, malformed signer hash, immutable public-key copies and default production-disabled state. Workflow guard confirms the startup bootstrap cannot launch an installer and waits for Yandex idle.
- Exact code/test HEAD `5b5a2e0845eb1d9f02400ae382d702c25abedf43`: Main CI [43587767442](https://github.com/manufact-test/nomusic/actions/runs/43587767442) SUCCESS; Windows integration [43587767458](https://github.com/manufact-test/nomusic/actions/runs/43587767458) SUCCESS.
- Full details: `docs/windows/W117-TRUST-CONFIG-AND-DORMANT-LKG-BOOTSTRAP-20261114.md`.

## W116 — first signed-install bootstrap and immutable version manifest

- The first-install gap is implemented: exact-version immutable signed metadata can recover the signed installer for the currently installed release and seed the first DPAPI LKG package.
- Versioned `{version}/manifest.json` and `.sig` files are immutable; `latest.json` remains the mutable discovery pointer.
- Journal state `Seeded` is a real initial LKG, not a fake previous release. The first later signed update can reuse it as its previous installer.
- W117 now wires the bootstrap to startup behind the empty production trust gate and Yandex-idle check. It remains dormant until owner-approved pins and official origin are populated.
- Exact W116 code/test HEAD: `d1c807dbc2bb748a8a6d692ef0e01b96a5d9f7d5`; Main CI [43585155970](https://github.com/manufact-test/nomusic/actions/runs/43585155970) and Windows integration [43585155942](https://github.com/manufact-test/nomusic/actions/runs/43585155942) SUCCESS.
- Full details: `docs/windows/W116-FIRST-SIGNED-BOOTSTRAP-AND-IMMUTABLE-VERSION-MANIFEST-20261114.md`.

## W115 — durable signed last-known-good package cache

- Each completed transaction retains both verified previous and target installers, with DPAPI journal and exact four-file payload hashes.
- W116 added the initial `Seeded` package for the first signed install.
- Full details: `docs/windows/W115-LAST-KNOWN-GOOD-SIGNED-PACKAGE-CACHE-20261114.md`.

## Still blocked — do not call updater ready

- Production P-256 public-key pin, Authenticode signer certificate SHA-256 fingerprint and official stable-feed origin are not provisioned. Shared constants in `StableUpdateTrustConfiguration.cs` remain empty; Supervisor intentionally exits code 3.
- No live signed feed/package publisher or atomic upload target is confirmed.
- W117 wires only the dormant first-LKG bootstrap. The main app still has no signed `latest.json` consumer, no trusted same-user Supervisor launch callsite, no install coordinator and no automatic customer update scheduling/notices.
- No real production-signed installer/feed, forced GUI crash, automatic one-shot rollback, owner-PC account-preservation or Yandex-idle end-to-end test has run.
- No final EXE+ZIP has been built or delivered. No mass release.

Do not paste private keys into chat or commit them. Do not fill production pins with guessed values. Do not publish to the Hostinger QA hostname as a substitute for the official feed. Do not enable automatic installation until the actual signed update/rollback path passes on Windows.

## Superseded W117/W118 work-order snapshot — archive only

The W117/W118 implementation records immediately above this point are historical. Their old instruction to prepare an early “QA” or “TEST” EXE+ZIP is superseded and must not be followed. Their old Stage 5/W98 repair sequence is also superseded: W118 records the successful W90/W98/Stage 5 results. Current work is defined only by the authoritative top of this file and W119.

## W113–W114 implementation history — 14 November 2026

- **W113 manifest generation:** c7451d90863581794c70df7a3dc8c2525ee4930c; backup backup/windows-main-pre-w113-stable-manifest-publisher-20261114 @ d136d52d595574c25461fc05590ac7078a739cf6. Generator builds the exact schema-2 JSON and P-256 DER signature, requires the signing private key to match the client-pinned public key, and hashes the package plus installed payload. W116 extends output with immutable per-version manifest/signature files beside the mutable latest pair. W113 tests: Main CI 43578863477 SUCCESS; Windows integration 43578863492 SUCCESS.
- **W114 supervisor payload binding:** 5fbc5ed39694dbd43329d47e2ea169f4142cf540; backup backup/windows-main-pre-w114-supervisor-payload-20261114 @ c7451d90863581794c70df7a3dc8c2525ee4930c. Schema 2 now requires four installed-file hashes: CELIKOM.Companion.exe, integration/host.cjs, integration/renderer.js and CELIKOM.UpdateSupervisor.exe. DPAPI journal stores previous/target hashes for all four. The existing Inno installer includes the supervisor; the existing W20 and Hostinger QA build paths build it before compiling the same installer.
- **W114 implementation CI:** Main 43579759654 SUCCESS; Windows integration 43579759677 SUCCESS.
- **Packaging guard:** 273fe22132123d7af7d3e961748b9d09104c0c7a verifies the Inno entry, both build paths and installed-file smoke assertion. Main CI 43580005463 SUCCESS; Windows integration 43580005419 SUCCESS.
- **Still NOT production-ready:** production P-256 public-key pin, Authenticode certificate fingerprint and official feed origin remain unprovisioned in the shared `StableUpdateTrustConfiguration`; all three values are intentionally empty. W113/W116 generate signed metadata locally but do not publish a live feed. W117 wires only a dormant first-LKG startup bootstrap behind the empty trust gate and Yandex-idle check. The main app still has no signed latest-manifest consumer or trusted Supervisor launch callsite. No real signed install, forced GUI crash, one-shot restore or owner-PC test has run. No final EXE+ZIP has been produced.
- **Open owner checks remain:** issues #52, #53, #54, #56, #57, #58. CI does not replace VPN/audio/volume/original-track/first-run/tray checks on the owner PC.
- Do not use the Hostinger private QA domain as the official stable-feed origin without explicit confirmation. Do not paste or commit production keys/certificates. Do not run the manual Hostinger QA installer workflow or mass release as a substitute for the signed production flow.

**Next work order:** after the owner-approved Windows audio fixes and one coherent owner QA build, return to production trust provisioning; confirm the official HTTPS origin and atomic upload target; publish immutable per-version manifest/signature plus package; wire the signed latest-manifest consumer and same-user Supervisor launch; run a real signed update/forced-crash/one-shot-rollback test while preserving the account, native integration and Yandex playback. Only after that create one final EXE+ZIP for owner QA.

**Read first:**
1. `docs/windows/W102-SINGLE-PRODUCTION-LINE-YANDEX-15MIN-AND-WORK-ORDER-20261113.md`
2. `docs/windows/W101-CELIKOM-WINDOWS-AUTO-UPDATE-AND-ROLLBACK-POLICY-20261113.md`
3. `docs/windows/W112-EXACT-SIGNED-PAYLOAD-IDENTITY-20261114.md`
4. `docs/windows/W110-W111-INDEPENDENT-SUPERVISOR-SESSION-WITNESS-20261114.md`
5. `docs/windows/W109-DURABLE-SIGNED-ROLLBACK-JOURNAL-20261114.md`
6. `docs/windows/W105-W108-STABLE-UPDATER-TRUST-AND-NO-AUTOPLAY-20261114.md`
7. `docs/windows/NEXT-CHAT.md` (this file)
8. GitHub issues #52, #53, #54, #56, #57, #58; read actual code before changing.

**Exact latest code CI proof:**
- Main CI [43577376444](https://github.com/manufact-test/nomusic/actions/runs/43577376444) — SUCCESS.
- Windows integration CI [43577376383](https://github.com/manufact-test/nomusic/actions/runs/43577376383) — SUCCESS, including W22/W23/W60 audio/VPN/source/403, W21 recovery, W24 ASAR/catalog, W15 payload/session tests, W110 watchdog simulation, schema-2 payload identity, and warning-as-error GUI/supervisor builds.
- Earlier W112 checkpoint [43577075078](https://github.com/manufact-test/nomusic/actions/runs/43577075078) / [43577075086](https://github.com/manufact-test/nomusic/actions/runs/43577075086), both SUCCESS at `d066efc9` before the final stager-level missing-payload guard.
- Earlier W103 `d903ffae` failed four integration tests because expected reload occurred before new 150 ms confirmation window; fixed in `7a4768e` with tests preserving actual delayed behavior. Do **not** revert to the failed intermediate.
- Stage 5 Hostinger restore proof [43514995243](https://github.com/manufact-test/nomusic/actions/runs/43514995243) SUCCESS: 1498 original audio SHA256 checks and isolated DB restore with Big City Life gain sidecar. Live DB untouched in that test.
- Dedicated gain-stage job [132132259655](https://github.com/manufact-test/nomusic/actions/runs/43495186951) SUCCESS: Big City Life track 40371622, configured +11.5 dB, measured +6.70 dB RMS and verified signed Range 206. Its parent workflow failed later in updater ZIP verification, **not** sidecar staging.

## W112 — historical base: exact signed installed-payload identity (superseded by W113/W114)
- Exact code commit `a7dbed8e19c9f23d952f689c1074c6057d0116d0`; Main CI [43577376444](https://github.com/manufact-test/nomusic/actions/runs/43577376444) **SUCCESS**; full Windows integration [43577376383](https://github.com/manufact-test/nomusic/actions/runs/43577376383) **SUCCESS**.
- Exact post-W112 rollback: `backup/windows-main-post-w112-payload-identity-ci-green-20261114` @ `a7dbed8e19c9f23d952f689c1074c6057d0116d0`. Pre-W112 backup `backup/windows-main-pre-w112-signed-payload-identity-20261114` @ `3f2c528a9a3b01a1db6a76dcda84d8e466c724d2`; W112b pre-stager-guard backup `backup/windows-main-pre-w112b-require-payload-at-staging-20261114` @ `d066efc937803ec1d0a1b6362de1883a6cf6c812`.
- Signed stable manifest contract is now **schema 2** and requires lower-case SHA-256 values for three installed files: `applicationSha256` = `CELIKOM.Companion.exe`, `nativeHostSha256` = `integration/host.cjs`, `rendererSha256` = `integration/renderer.js`. Schema 1 feeds are rejected.
- `StableUpdatePackageStager.FetchVerifiedAsync` and `VerifyInstaller` both fail closed if any of the three signed payload hashes are missing/invalid. Package SHA256 remains separately checked against the signed installer package bytes.
- W109 DPAPI journal schema 2 stores the previous and target app/host/renderer hashes. New transactions require all six. The W110 engine refuses schema 1 or any missing payload witness; legacy records are never eligible for unattended transitions.
- The independent W110 health probe checks exact installed bytes for the EXE + both integration assets, then verifies Authenticode signer pin, PE identity/version, running process path, authenticated local bridge, original DPAPI account fingerprint and native integration. The rollback health check uses the previous version's exact three payload hashes too.
- Tests: W15 validates signed schema 2, rejects schema 1/malformed/missing hashes, tampering of each installed file, missing files and journal preparation without payload identity. W110 simulation checks mismatched app/host/renderer hashes and refuses schema 1. W15 and W110 test steps, GUI/supervisor warning-as-error builds and existing Windows regression suite are green.
- **W112 checkpoint only:** schema 2 was a code contract, not a published production feed. W113/W114 subsequently added the manifest generator and bundled/hash-bound the helper. Production P-256 public key and Authenticode certificate pins remain unprovisioned; the main app still does not launch the helper; no real signed installer/crash/rollback end-to-end test or owner-PC acceptance exists. No final signed EXE+ZIP or mass release.
- Historical W112 next steps are superseded by the current W113/W114 order above. Keep Yandex closed during any rollback.

## W110–W111 latest VERIFIED / 14 November 2026
- ONE active work branch `main`. Exact green W111 code: `be6bda507aeeb68a7046a4ad12c41448d139860a` with **Main CI** [43575703455](https://github.com/manufact-test/nomusic/actions/runs/43575703455) SUCCESS and **full Windows integration** [43575703509](https://github.com/manufact-test/nomusic/actions/runs/43575703509) SUCCESS. Exact snapshot: `backup/windows-main-post-w111-account-witness-ci-green-20261114` @ this SHA.
- W110 isolated internal-process supervisor green checkpoint `d6d2850e8f27e3b5a582879b8063465d4a442b80`, exact snapshot `backup/windows-main-post-w110-supervisor-ci-green-20261114`; CI [43575142613](https://github.com/manufact-test/nomusic/actions/runs/43575142613) and Windows [43575142609](https://github.com/manufact-test/nomusic/actions/runs/43575142609) SUCCESS. Pre-W110 backup `backup/windows-main-pre-w110-independent-supervisor-20261114` @ `6594328612c9349c3c4a235251dc1a88975a1d7b`. Pre-W111 backup `backup/windows-main-pre-w111-session-identity-witness-20261114` @ `d6d2850e`.
- W110 `Celikom.UpdateSupervisor` is a **separate internal helper process of the ONE CELIKOM product**, not a second consumer app. Simulated independent watchdog handles startup failure, signed-app/bridge/DPAPI/native checks, safe playback-idle rollback, verified old installer, at-most-one attempt, timeout and manual recovery. W110 tests cover 17 scenarios. W111 adds prior **installation GUID + normalized account** fingerprint to W109 DPAPI journal, fails closed on replacement/missing/corrupted login, does not punish token rotation. See `docs/windows/W110-W111-INDEPENDENT-SUPERVISOR-SESSION-WITNESS-20261114.md`.
- **ABSOLUTELY NOT customer-ready:** production certificate fingerprint remains empty in the shared trust configuration; Supervisor invocation exits code 3, confirmed in CI. The helper is included in the existing installer payload under W114, but the trusted main-app Supervisor launch callsite is still absent. W117 adds only a dormant LKG bootstrap callsite. Signing keys/pins, release-signed Authenticode EXE/helper, signed stable feed, independently tested real installation/recovery, scheduled notices and automatic rollout are missing. W110 unit tests simulate probes/installer, not a real signed Inno package or crash in the wild.
- **Next concrete code order:** publish and pin the schema-2 manifest/key/certificate through existing secure release infrastructure; add the supervisor's own payload hash when it is packaged; wire the helper into the same CELIKOM installer without creating another product; prove real signed update + killed-GUI rollback + preserved login on Windows while Yandex is closed; finish stable-feed scheduler and user UI; then one owner EXE+ZIP and field QA. No random branch, no new user secrets/accounts/emails, no interim release.
- Existing owner-PC defects VPN, #52/#53/#54/#56/#57/#58, startup/tray/diagnostics and audible proof remain OPEN. Green CI is not owner playback QA.

## W109 — 14 November 2026: durable rollback journal (CODE + CI GREEN)
- **Exact verified code:** `0d90fea82cfd8d95e7c830941e1443cafa594fd3`; backup `backup/windows-main-post-w109-rollback-journal-ci-green-20261114` points to the same SHA. Pre-W109 exact backup: `backup/windows-main-pre-w109-rollback-transaction-20261114` @ `2331a7de51c9ae2f33162bc382c77ad65bd34bb8`.
- CI [43572820346](https://github.com/manufact-test/nomusic/actions/runs/43572820346) **SUCCESS**; full Windows integration [43572820294](https://github.com/manufact-test/nomusic/actions/runs/43572820294) **SUCCESS**. Only `StableUpdateRollbackJournal.cs` and W15 contract tests changed in W109.
- Windows DPAPI-per-user durable journal + atomic rewrite, signed-old-installer byte snapshot and re-verification, pending-upgrade mutual exclusion, 10-minute bounded health decision, **one permitted rollback attempt**, and separate, evidence-gated `Healthy` / `Restored` transitions. A completed transaction permits another approved release while active/crash recovery records are never overwritten. Tests exercise healthy, failed/timeout, replay refusal, invalid health, tampered snapshot, DPAPI ciphertext alteration, and sequential release.
- **NOT a finished automatic rollback:** `PrepareSigned` has NO consumer call site; test-only synthetic verifier is not a real signed installer. No independent external watchdog process, install/rollback launcher, production signing pins/keys, signed live feed or real owner-PC install tests. W109 never modifies Yandex, plays audio, launches an installer or marks a user machine updated.
- **Next:** implement and test a truly independent signed-package watchdog (survives new app crashes) using this journal; obtain production signing/public trust configuration through existing release infrastructure without asking user for new secrets, then bounded stable polling/idle install/in-place recovery. One final signed EXE+ZIP only after end-to-end Windows and owner QA.
- Full file: `docs/windows/W109-DURABLE-SIGNED-ROLLBACK-JOURNAL-20261114.md`.

## Latest implementation W105–W108 / 14 November 2026

- **Verified code** `1ad2c63e78746db49ca8bca5e0c3c8bee2cbc48b` on the only active `main` branch. Exact green rollback: `backup/windows-main-post-w108-updater-guards-ci-green-20261114` @ that SHA. Other exact safety snapshots: `backup/windows-main-pre-w105-secure-package-staging-20261114` @ `553c5fb0059aa55e92959f93db1d18dbd2f9600e`, `backup/windows-main-post-w105-w106-ci-green-pre-feed-20261114` @ `61dd35c07951be0b5f607afd2fbf548ff1509eeb`, `backup/windows-main-post-w107-signed-feed-ci-green-20261114` @ `685e95a2f40c0b58d06df4d907e856a8da13bc19`.
- **Latest exact CI:** main [43569385121](https://github.com/manufact-test/nomusic/actions/runs/43569385121) SUCCESS; full Windows integration [43569385123](https://github.com/manufact-test/nomusic/actions/runs/43569385123) SUCCESS. Previous W107 main [43568654764](https://github.com/manufact-test/nomusic/actions/runs/43568654764) / integration [43568654802](https://github.com/manufact-test/nomusic/actions/runs/43568654802), both SUCCESS.
- **W105:** bounded immutable HTTPS binary stage, exact bytes and SHA256, Authenticode trust, *independently pinned signer certificate SHA256*, PE identity/version and pre-launch recheck; all failures fail closed and delete staged file. Does not execute downloads.
- **W106:** signed mandatory rollback is allowed only with a new monotonic release sequence, exact `fromVersion` equal to the running bad version and lower `toVersion`. Unsigned, replayed and arbitrary downgrades denied. This is *authorization logic*, not an automatic rollback helper.
- **W107:** read-only signed `latest.json` and `latest.json.sig` over exact HTTPS origin, bounded no-redirect response, detached P256 signature verification. No key is pinned into shipping application yet, no automatic checks are wired.
- **W108:** current staff/manual in-place update refuses to start while Yandex is running or CELIKOM bridge enabled; removes auto-start of Yandex after update and premature `APP_UPDATE_COMPLETED` claim; emits only actual local-start/native-identity evidence and clears pending ticket only if the installer never started. Windows integration has an explicit no-autoplay source guard.
- **NOT DONE:** no release-signed Authenticode CELIKOM binary, production manifest public key/pinned signer, live signed stable feed, consumer background polling/prompt/install, independent crash watchdog and last-known-good package rollback, or final signed EXE+ZIP. Those are release blockers per W101. No temporary/unsigned EXE was delivered, no mass publish or installation.
- **Owner QA remains:** VPN reconnect, #52/#53/#54/#56/#57/#58, first-launch/reboot/diagnostics/autorun and genuine audio, plus in-place upgrade and rollback. Do not mark audio fixed by CI.
- Full engineering details: `docs/windows/W105-W108-STABLE-UPDATER-TRUST-AND-NO-AUTOPLAY-20261114.md`. Work directly on `main`; create only `backup/*` before substantive changes, never edit Android, extension, original media or unrelated server. No new secrets/accounts/emails.

## Follow-up W104/W101 — 14 November 2026
- **Actual source**: last proven main code commit `9ac9a5ab485c3ce1bebc8aa6a2352b422c0ffa1c`; current pinned known-good pre-W104 backup `backup/windows-main-pre-native-failure-recheck-20261114` @ `f82dbe4448ff743945da4d4d26f159bfbaeb2766`. Intermediate exact green checkpoint `backup/windows-main-post-native-failure-recheck-ci-green-20261114` @ `f4449475ff0298c82b52426ded28b73217ec2439`. W101 contract pre-change backup `backup/windows-main-pre-w101-signed-feed-contract-20261114` @ `3cc58b93a244d3711b7cda06010e550212731935`.
- **W104 code+CI**: explicit authenticated native `HOST_ERROR`, 22-second Start with no native handshake, and native install/upgrade exception trigger an immediate data-only reviewed-catalog refresh followed by host inspection; events coalesce, repeated errors back off 2/4/8/15 minutes, native heartbeat resets the backoff. This never autoruns Yandex, changes audio source, patches the host, assumes entitlement, or trusts a new vendor version without exact proofs. W104 3cc CI [43528538262](https://github.com/manufact-test/nomusic/actions/runs/43528538262) SUCCESS, full Windows CI [43528538351](https://github.com/manufact-test/nomusic/actions/runs/43528538351) SUCCESS. Real owner field proof pending.
- **W101 progress, NOT automatic updater**: `StableUpdateManifestVerifier.cs` validates a detached P256 signature, stable-only manifest, monotonic release sequence, expiry, exact HTTPS origin and immutable version path; anti-replay and anti-downgrade tests. This class does not fetch, stage or launch binaries. No production-pinned public key, Authenticode-signed installer, independent crash-health rollback supervisor or signed live feed exists here. Auto-install remains OFF, and unsigned customer rollout is BLOCKED. Latest signed-manifest code+test gates: Main CI [43529667031](https://github.com/manufact-test/nomusic/actions/runs/43529667031) SUCCESS; Windows integration [43529666957](https://github.com/manufact-test/nomusic/actions/runs/43529666957) SUCCESS (exact code commit). Exact rollback for the new green code: `backup/windows-main-post-w104-w101-guards-ci-green-20261114` @ `9ac9a5ab485c3ce1bebc8aa6a2352b422c0ffa1c`. Intermediate W101 test compilers failed before the last fixes; do not use those intermediary revisions.
- **Still open**: #52/#53/#54/#56/#57/#58 acoustic/owner-PC evidence, VPN reconnect, first-launch GUI/reboot acceptance, complete signed in-app download/install/rollback, one owner-approved EXE+ZIP and mass rollout. No installer delivered in this continuation. See `docs/windows/W104-NATIVE-FAILURE-RECHECK-AND-W101-STABLE-MANIFEST-20261114.md`.

**Open defects (do not call them done):**
1. VPN reconnection 40–50 seconds — recovery code/CI exists, owner field test pending.
2. #52 «Ты» (тринадцать карат) false green — current decoder proof guard exists; audible alternative still needs confirmation.
3. #53 Brave/Windows load or freeze — durable Electron memory/event-loop + source diagnostics now exported; root bottleneck unproven. Need owner diagnostic and Task Manager CPU/RAM/GPU capture. Origin of elevated-rights prompt still unproven.
4. #54 Big City Life sudden mid-track volume dip — W54 records signed gain-variant URL selected/missing, native volume drop and source-left. This is **diagnostic evidence, not an acoustic fix**.
5. #56 admin gain — Windows private offline sidecar server stage/restore passed; owner seek/Next/crossfade/volume/headroom proof pending, no changes to extension originals.
6. #57 signed 403→206 hiss/pop — W103 now gives 150 ms post-prime CDP confirmation chance before reload; approved decoder already playing cancels pending reload only. No proof means bounded reload proceeds. CI green, owner acoustic test pending. Do not force a production 403.
7. #58 «Моя волна» and other original tracks pop under VPN change — original/unknown no-reload guards CI green, acoustic test pending.

**Other open work:** W121 now blocks duplicate Start clicks while the first host/entitlement check is pending. The broader first/second/third launch, reboot, tray and autostart behavior still needs grouped owner-PC acceptance. W120 keeps diagnostics useful after transient state failure and adds a privacy-safe CPU incident; owner diagnostic export after disconnect still needs acceptance. Initial popup, false outdated-module message and W87/W88 default tray autorun are implemented in code; runtime acceptance remains open. Yandex release detection uses the 15-minute catalog refresh and the app's existing refresh path; do not weaken the cadence or CDP recovery without objective profiling. W122 supplies the Supervisor READY launcher and W123 makes signed no-update polling possible, but the stable update coordinator and MainWindow callsite are still missing. W101 signed automatic in-app stable update and safe rollback remain **not implemented**; current updater is manual/staff only.

**Next work order:** after current audio blockers and one owner-accepted integrated Windows build, provision the schema-2 release trust pins/feed and connect the already bundled Supervisor through a trusted same-user launch callsite; prove real signed crash recovery and stable automatic updates per W101. Verify W104 bridge/start failure recheck on owner's PC; run CI after changes; make **one** coherent final Windows EXE + ZIP and link it only when successfully built and independently verified. Do not send partial TEST installers or ask for new secrets/accounts/emails. The user expects big completed chunks and a short status, not endless theory. Mass release only after owner QA. No final package has been delivered and nothing was installed on user's PC from this handoff.

**Owner-side proof required:** VPN A→B reconnect, «Ты» audible replacement, Big City Life full-song loudness, natural 403→206 without hiss, «Моя волна» originals on VPN switch, Brave/Windows resource usage, and startup/reboot behavior. Never claim a real playback bug fixed by CI alone.

## W114a continuation — 14 November 2026

- Latest code fix: `StableUpdateRollbackJournal.VerifiedPreviousInstallerCore` now passes `PreviousSupervisorSha256` into the reconstructed `VerifiedRelease`. Before this, the signed rollback package was re-verified without its required fourth payload hash and would be rejected by W114 stager validation.
- W15 synthetic verifier now asserts all four payload hashes (application, native host, renderer, supervisor) on each verified package, so this omission is covered by regression tests.
- Exact pre-change backup: `backup/windows-main-pre-w114-rollback-supervisor-hash-20261114` @ `ffb983ec97982263e4559b3d7e7aad120976ad76`.
- Fix commits: `54219d43e550e4c5ea42eb2fa511264a4255ee0e` (code), `a7c8474a9dadb55c55261bffe6e6141aabac1146` (test).
- Last verified HEAD before W114a: `ffb983ec97982263e4559b3d7e7aad120976ad76`; final CI for W114a must be checked against the newest `main` HEAD.
- No production signer pin/key/feed is provisioned. Supervisor launch callsite is still absent. Do not run Hostinger QA publish or claim automatic updates are live.

- Additional W114a hardening: schema-2 `ReadRecord` now rejects missing/invalid previous or target Supervisor hashes at journal-read time, matching the engine and stager fail-closed requirements. Exact pre-change backup: `backup/windows-main-pre-w114a-journal-supervisor-validation-20261114` @ `fd18154e6ffa68325510b1e90315c7020741c6d2`. Code commit: `59a84955308ec73f3a4e3b8dad1282002eb4f3ed`.
# CELIKOM Windows — AUTHORITATIVE CURRENT HANDOFF / 14 November 2026

## W148 — P0 production signed-release pipeline prepared, NOT yet deployed (15 November 2026)

- Working branch `main`, W148 pre-change exact backup `backup/windows-main-pre-w148-production-release-pipeline-20261115` @ `18ad2b8b6aa66012f5e2bb61d779d0e2dd51bd10`. Latest W148 code before docs `f70e1c23fe69be5ba3786d845b11459d1064bb5c`.
- Signed release build/publisher **code** added: public pinned trust injection (source defaults stay empty), offline protected P-256 key generator, schema-2 manifest/package signature verifier, protected **manual** GitHub Actions workflow `windows-stable-signed-release.yml`, real Authenticode PFX/chain/fingerprint gates, immutable Hostinger publisher with exact official-domain HTTPS byte verification. Continuous regression tests wired in Windows integration CI.
- Owner/infra external dependencies in [GitHub issue #59](https://github.com/manufact-test/nomusic/issues/59), not automatically assigned: approved DNS+TLS and actual Hostinger root for celikom.com, trusted CA code-signing provider/certificate, protected GitHub environment/secrets/manifest private key. Current GitHub connector CANNOT set those admin-managed secrets or issue a real code-signing certificate.
- Crucial: **production auto-update NOT running**. Current installed unsigned 0.24.37 still has empty pins and needs one trusted signed bootstrap; then next signed release can update automatically. No package built, no deployment, no owner PC install, no real rollback test. W119/W139 constraints intact. Details `docs/windows/W148-PROTECTED-SIGNED-STABLE-RELEASE-PIPELINE-20261115.md`.
- W148 automated CI may still be running; confirm latest source HEAD after documentation before declaring green. Do not run manual signed-release workflow until real protected secrets/trust/domain are provisioned. All six issues remain OPEN.

## W147 newest playback-evidence continuation — 15 November 2026

- **Latest native Windows code HEAD before this documentation commit:** `e174551dc086f8812f05840aa8e22d926889ad31`, only on `main`. Exact pre-W147 rollback backup `backup/windows-main-pre-w147-electron-audible-property-precedence-20261115` @ `d63e5505e7300e83cb6307ba9a23866bc3db45a2`.
- W147 native host `nativeAudible(view)`: when Electron `isCurrentlyAudible()` provides an explicit boolean **false**, it now overrides an older `audio-state-changed(true)` event. True is also respected. Use last event only if the native method is absent/throws/unavailable. Current-player choice and PLAYING heartbeat share the same predicate. No media commands/audio edits; unknown sources remain UNKNOWN without signed current decoder proof.
- New W23 regression uses a simulated native false + delayed old audible event, advances the observer clock past the 4-second renewal and confirms the renewed heartbeat cannot claim PLAYING or CELIKOM replacement. W147 code commits `6a39633e476c1d349acaae6517a2a186402d4cc9`, `96135537190ccb287f36ce056f5bb2fb7f6de45c`, `e174551dc086f8812f05840aa8e22d926889ad31`.
- W145 both CI SUCCESS: Main 43696999275, Windows integration 43696999268. W146 both CI SUCCESS: Main 43697181373, Windows integration 43697181363. W147 CI at latest code `e174551dc0`: Main 43697422458 and Windows integration 43697422432 were running when authored; **check before declaring green**.
- No new EXE/ZIP, no production trust keys/cert/feed, no user-PC acceptance. Previously installed 0.24.37 stays unchanged, all six issues OPEN. W119/W139 and the following handoff sections remain binding.

## W145/W146 latest continuation — 15 November 2026

- **Live Windows code HEAD at this handoff:** `d4a94f63411e328b47aa5fe16b8acfbaf9dcb2a6`, working branch **main only**.
- W145: exact pre-code backup `backup/windows-main-pre-w145-pending-safe-point-scheduler-20261115` @ `8642b98ba05c27f445d1bb110b78bae1ea09dc4e`, code `6094432757c80d0305a1d49b32868a591b960ea0`. After an authenticated signed package has already been downloaded and verified, the existing stable-update scheduler runs a low-cost safe-point check every 30 seconds, not 30 minutes. While Yandex is running / playback not safe, **no network feed/payload re-fetch** occurs in the short interval. The install coordinator and existing strict gate still re-validate before Supervisor/installer; no audio interruption or bypass of missing production trust. W15 test covers interval and skip policy.
- W146: exact pre-code backup `backup/windows-main-pre-w146-compact-paused-source-status-20261115` @ `6094432757c80d0305a1d49b32868a591b960ea0`, code `d4a94f63411e328b47aa5fe16b8acfbaf9dcb2a6`. Compact popup renders pending mapping status only if the **fresh current native player state is PLAYING**; PAUSED and STOPPED take precedence. Tests assert no stale green while paused.
- W142, W143 and W144 both Main CI and Windows integration CI **SUCCESS** (W142 43696125856 / 43696125894; W143 43696396674 / 43696396709; W144 43696528740 / 43696528671). W142–W144 documentation HEAD `8642b98ba05c27f445d1bb110b78bae1ea09dc4e` also both SUCCESS (43696634634 / 43696634618). W145/W146 are newer and require checking latest CI before acceptance.
- **No live updater yet:** legitimate official HTTPS release origin, protected P-256 private signing key and matching public pin, trusted Authenticode signer fingerprint/certificate, protected package publisher and real owner-PC signed bootstrap/rollback not provisioned. Existing owner-installed unsigned 0.24.37 cannot autoupdate. Never invent anchors or claim this code delivered an update. No installer built, no owner-PC listening verified. All six issues #52 #53 #54 #56 #57 #58 OPEN, W119/W139 authoritative.

## W142–W144 continuation — 15 November 2026 (latest code)

- Working branch is ONLY `main`; latest W144 code HEAD `18aa813f0cbb83832b3f6f0e8150ada0a5439757`. No new Windows TEST product, installer or release. Do not alter Android or browser extension. All six issues #52 #53 #54 #56 #57 #58 remain OPEN.
- W141 final `09c7b0168c4d70f2d7afe6e974a90600391bd65c`: Main CI 43695545111 SUCCESS and Windows integration CI 43695545121 SUCCESS. Confirms code only, NOT owner-PC listening or audio quality.
- W142 exact pre-change backup `backup/windows-main-pre-w142-gui-source-and-heartbeat-handoff-20261115` @ `09c7b0168c4d70f2d7afe6e974a90600391bd65c`; code `c919d1ed15842bd9d704f2d6cdb7540c78de3b77`. Main GUI source text now agrees with compact GUI: active green only when exact current signed decoder + PLAYING; original only if directly identified; pause/stop/UNKNOWN do not inherit old mapping. Bridge retires superseded native process instance IDs, so late old heartbeats cannot resurrect a previous song. W142 Main CI 43696125856 and Windows integration CI 43696125894 SUCCESS.
- W143 exact pre-change backup `backup/windows-main-pre-w143-stable-feed-coherence-20261115` @ `c919d1ed15842bd9d704f2d6cdb7540c78de3b77`; code `e772ca977b70ad9c1a9b972175e93907db04235c`. Authenticated latest-feed JSON and detached signature are two static HTTPS files; a short publication race can mix generations. Added bounded 3-attempt signature-mismatch-only re-fetch of BOTH files and no-cache headers; permanently invalid signatures, redirects, malicious manifests still fail closed. Added W15 regressions for both transient recovery and persistent mismatch. This does not publish a production feed or provision keys/certificates.
- W144 exact pre-change backup `backup/windows-main-pre-w144-active-audibility-reconciliation-20261115` @ `e772ca977b70ad9c1a9b972175e93907db04235c`; code `18aa813f0cbb83832b3f6f0e8150ada0a5439757`. Native playback view selection and current-track heartbeat now consult the SAME Electron isCurrentlyAudible / audio-state-changed predicate. A true native audible property may report PLAYING even before an event arrives, but source remains UNKNOWN without exact current decoder proof. Added W23 regression.
- W143/W144 fresh CI runs were still IN PROGRESS when this note was authored: W143 main 43696396674 / Windows 43696396709; W144 main 43696528740 / Windows 43696528671. Re-check before declaring green.
- Mandatory P0 still blocked on REAL owner-approved official HTTPS origin, protected P-256 release signing key + exact client public-key pin, trusted Authenticode signer certificate + fingerprint, protected atomic publisher, a one-time trusted bootstrap for currently installed UNSIGNED 0.24.37 and actual owner-PC end-to-end install/forced-rollback. Never insert made-up values or claim a functioning auto-update channel.
- Next work: finish signed production publication and first bootstrap once genuine trust infrastructure is available; continue current Yandex source proof (ORIGINAL currently conservatively UNKNOWN), restart/VPN UI consistency, audible VPN pop/hiss without slower reconnect, autostart and remaining six issue acceptances. Do not request an intermediate owner installer. Preserve the W119/W139 contract.

> **READ FIRST.** This is the controlling handoff for CELIKOM Windows. Read `docs/windows/W119-AUTHORITATIVE-OWNER-CONTRACT-AND-WINDOWS-HANDOFF-20261114.md`. If any older W-series note or previous chat conflicts with this top section or W119, follow W119. Older sections below are technical history, not current work orders.

## W140/W141 current continuation — 15 November 2026

- Work only on main. Exact W140 pre-change backup: backup/windows-main-pre-w140-stable-update-download-during-playback-20261115 @ e2c7e3917fae29f14750007a49a541bb97c9c8b4. Exact W141 pre-change backup: backup/windows-main-pre-w141-current-player-sync-20261115 @ bd186871823b76a1208e302298c4efd8296e72d7.
- W140: signed feed discovery / authenticated current-install inspection and SHA-256 + Authenticode verified downloads are no longer blocked by active playback. Verified installer is held in a local pending cache and rechecked at the next safe install point. Same Supervisor and DPAPI rollback journal are retained. Full Windows CI SUCCESS at bd186871823b76a1208e302298c4efd8296e72d7.
- W140 remains non-production: StableUpdateTrustConfiguration.cs has no approved official HTTPS origin, P-256 public key or Authenticode signer fingerprint. Owner-review 0.24.37 is unsigned and lacks pins. No actual signed production feed or owner-PC installation/rollback was proven. Never fabricate credentials or declare auto-updates operational. A one-time trusted bootstrap may be necessary. The existing GitHub connector did not allow fetching release secret/environment metadata.
- W141: native main host selects one authoritative active/audible Yandex view; other webContents cannot overwrite the current song. Renderer player observer exposes explicit PLAYING, PAUSED, STOPPED. Current signed decoder proof is the sole ACTIVE_REPLACEMENT witness; ambiguous sources remain UNKNOWN (ORIGINAL requires further actual decoder attribution). 4-second sequenced native heartbeats refresh stable playback, local bridge discards out-of-order previous-song heartbeats and expires the UI state after 12 seconds. Compact popup/main status use current source evidence rather than mapping-only or stale labels. Existing 15-second UI pulse now refreshes an expired view after a silent host disconnect.
- W141 CI at 858c68128b09dc5a71cd34868bc123a1a52a3173: both Main CI and Windows integration CI SUCCESS including the added current-player/order/renewal tests. The later UI-lease documentation commit still requires fresh CI verification.
- No new installer, ZIP or Windows TEST product was created. Do not touch Android, browser extension or original audio. Issues #52 #53 #54 #56 #57 #58 remain OPEN.
- Outstanding priorities: protected official update trust and atomic signed feed publication; first trusted bootstrap; real owner-PC safe-point update, READY and forced one-shot rollback; strong ORIGINAL/current decoder evidence; Windows restart/VPN current-song truth; VPN audible pop and crossfade/gain/regression checks. Preserve W119/W139 owner contract and existing 15-minute Yandex update watch.

## Hard product rule — one product, one main version

- There is **one existing CELIKOM Windows product**.
- `main` is the actual version being developed and maintained. All code work happens directly on `main`.
- `backup/*` contains exact snapshots of `main` made before substantial changes. Backups are rollback points only, not development branches.
- There is NO Windows TEST product/version, no separate QA product, no `experiment/*` development branch, no parallel product and no intermediate installer.
- Never call `main` a test version. Automated CI/tests are engineering checks only; they do not create another product.
- Do not change the agreed architecture or start from scratch.
- Do not build/send an installer until the complete agreed work is finished. Then produce one final EXE+ZIP from `main`.

## Exact repository state

- Repository: `manufact-test/nomusic`.
- Code baseline before the W119 documentation-only update: `2c12ea50797d8c395e4a2e169c9000d897dffb11`.
- Current first-owner-review source/code HEAD: `1338b73f3709847d5e42f9eb47cc8e8078b70374` (W138, CELIKOM 0.24.37 private one EXE+ZIP). W139 is a documentation-only owner-feedback handoff; live `main` is newer. The most recent Windows runtime implementation remains W135 `3045a9deaa7f87e031313741b64f4f9fbdd6e5c5`. Always fetch live `main` before coding.
- Last Windows app implementation commit: `3045a9deaa7f87e031313741b64f4f9fbdd6e5c5` (W135 source-decision incident retention); W135 regression-test/final code-test HEAD: `5a40357d28f1a1cc4f467a16bfaaaf38aa530b3f`; W134 regression-test commit: `d6c091fb109baeaa1690b15ca3f90d7c914a279a`; W133 runtime commit: `d548ed0af0f3717669c1fbcd903fc4f626428c7e`; W133 regression-test commit: `d79c20f37ce7428fca0e1abf1bdf3b0ad1a05832`; W132 test: `c02cd4988292598f81e857062279d0179253a42a`; W131 runtime/test: `5fb5f32d0364d476889bf56d0f8e8fc0e38d71b2` / `2f41091d1af072483ed5c79782958002b0ee2101`; W127 implementation/test: `4fe42d745b6708524c65eb4f9855e026f314fefa` / `7e4c8268cba30f781a3fa091d9657718ec463b66`; W128 CI policy commit: `cedcc45e5151afa62c1b292a7f4e2220226b6ac3`; W130 host/test: `5acbcc2af1a6cee85ef96bc81ce45d56d2f90726` / `74b27a27c8f1560591ed9ae11c17f5fceb0d538e`.
- Exact pre-W128 CI policy backup: `backup/windows-main-pre-w129-elevation-policy-guard-20261114` @ `911983107f257ec761f6c5c6666eec4748db3fd9`.
- Exact pre-W130 diagnostics backup: `backup/windows-main-pre-w130-cdp-property-observability-20261114` @ `312d61a62fb4abcb779df539503adf4226818185`.
- W130 Main CI [43605388622](https://github.com/manufact-test/nomusic/actions/runs/43605388622) and Windows integration CI [43605388482](https://github.com/manufact-test/nomusic/actions/runs/43605388482) — **SUCCESS**.
- Exact pre-W127 rollback snapshot: `backup/windows-main-pre-w127-current-decoder-witness-race-20261114` @ `4b7d2277d98986d8d4ab0ed9ba42a76fc25da810`.
- W127 Main CI [43603865004](https://github.com/manufact-test/nomusic/actions/runs/43603865004) and Windows integration CI [43603864999](https://github.com/manufact-test/nomusic/actions/runs/43603864999) — **SUCCESS**.
- Previous exact green W126 rollback snapshot: `backup/windows-main-post-w126-ci-green-20261114` @ `ed41f613640f55c8de4a027a8f6f12ac31a15093`.
- W126 Main CI [43601959568](https://github.com/manufact-test/nomusic/actions/runs/43601959568) and Windows integration CI [43601959593](https://github.com/manufact-test/nomusic/actions/runs/43601959593) — **SUCCESS**.
- Exact pre-W126 backup: `backup/windows-main-pre-w126-single-start-activation-20261114` @ `2488e38ebfae605c78d9e3f511d6fca0901c5cc2`.
- W120 Main CI [43596984190](https://github.com/manufact-test/nomusic/actions/runs/43596984190) — **SUCCESS**; Windows integration [43596984195](https://github.com/manufact-test/nomusic/actions/runs/43596984195) — **SUCCESS**.
- W121 Main CI [43597478523](https://github.com/manufact-test/nomusic/actions/runs/43597478523) — **SUCCESS**; Windows integration [43597478531](https://github.com/manufact-test/nomusic/actions/runs/43597478531) — **SUCCESS**.
- The W119 contract and earlier Android A1 work are preserved; this continuation changed only Windows companion code/tests and Windows documentation.

## W139 — latest owner acceptance and mandatory next priorities (15 November 2026)

**This section and `docs/windows/W139-OWNER-ACCEPTANCE-FEEDBACK-AND-AUTOUPDATE-P0-20261115.md` supersede older work-order priority where they conflict. Read W119, then W139 before coding.**

- Exact pre-W139 docs backup: `backup/windows-main-pre-w139-owner-acceptance-handoff-20261115` @ `4ba4fab4313939afc45ef782dd5344b206d11286`. W139 itself is documentation only; no Windows runtime code, installer or package changed.
- Owner has now begun listening to the existing 0.24.37 private unsigned build. Do not say he has not tested it. First feedback:
  - «Ты» (13 карат) and another track owner called «две гутыки» audibly played CELIKOM versions with apparently good sound/positive gain. Keep this as positive but limited listening evidence; do not close #52/#56.
  - Crossfade had no obvious clicks in the ordinary test; it still needs retest under VPN.
  - VPN A→B reconnect is faster than before, but owner hears a loud pop/hiss/strange sound. Preserve faster reconnect.
  - UI is seriously stale/incorrect: after a full CELIKOM close/reopen while Yandex already plays it still says waiting/loading; while «Ты» played it showed stale «Зима»/CENTR and «Версия CELIKOM передана Яндексу»; in «Моя волна» it kept that stale track while «Вечно молодой» played; after VPN it showed «Ожидаем» / «Запустите трек в Яндекс Музыке» while music was playing, with no current track.
- **P0 automatic CELIKOM app updater.** Owner explicitly says this is mandatory and expected the 0.24.37 update to download/install on his PC automatically. W138 only created a private GitHub Actions artifact; it was NOT delivered through CELIKOM. W124 coordinator/scheduler/Supervisor code is present but production trust is still empty, so `TryGetProduction` returns false and the automatic path does no feed check/download/install. Complete the real signed HTTPS feed, protected P-256 manifest key, trusted Authenticode signer, atomic publishing, automatic background download, safe-point install, Supervisor READY, real health check and forced one-shot rollback. Do not invent pins. See W139 for full requirements and the one-time bootstrap constraint: the current 0.24.37 binary has empty trust pins; a single trusted bootstrap may be needed, after which future updates must be automatic.
- **P1 UI/source-state synchronization** across restart, already-running Yandex, current-track changes, stop/pause, «Моя волна» and VPN reconnect. Never show stale previous-track metadata or claim transfer/active replacement without exact current playing decoder proof. Fix the state/event model, not just the label.
- **P1 VPN audio**: preserve the newly faster reconnect while removing the loud pop/hiss on replacement and original tracks; retest «Моя волна» and crossfade under VPN.
- **Autostart:** code inspection confirms `MainWindow` calls `EnsureFirstLaunchDefault`; first launch defaults HKCU Run ON and preserves a deliberate opt-out. Owner wants default ON. Verify the actual tray preference/registry state on his PC; do not overwrite an explicit OFF.
- Still unaccepted: #53 performance/elevation prompt, #54 Big City Life mid-track volume, #56 global gain/headroom/clipping (positive one-track listening is not global proof), #57 403→206 hiss, #58 original/«Моя волна» VPN continuity, diagnostics after disconnect, Yandex vendor update detection (preserve W102's 15-minute cadence). Issues #52/#53/#54/#56/#57/#58 remain OPEN.
- **Next work order:** (1) P0 automatic updater end-to-end; (2) P1 UI/source truth; (3) VPN A→B pop/hiss while preserving fast reconnect; (4) verify autostart; (5) remaining open audio/performance/diagnostics work; (6) one consolidated owner-PC acceptance including full updater + forced rollback. No extra package until integrated changes are ready.
- Keep working directly in `main`, one product, exact backups before substantial code changes, no Windows TEST product/branch, no interim installers, no architecture rewrite, no tiny owner check-ins. CI is not audible acceptance or proof of automatic delivery.

## Current state — what is and is not done

## W138 — single first-owner-review package BUILT, not production stable

- Private GitHub Actions [W138 owner-review run 43617609655](https://github.com/manufact-test/nomusic/actions/runs/43617609655) — **SUCCESS**, exact source `1338b73f3709847d5e42f9eb47cc8e8078b70374`.
- GUI, Supervisor and Inno all identify the one existing CELIKOM product `0.24.37` / `0.24.37.0`, preserving the same existing AppId and user data. No second product or Windows TEST line.
- One private artifact ID `14122464630`: `CELIKOM-W138-WINDOWS-02437-UNSIGNED.exe` (SHA-256 `1986c8269c990c91ad0b5910fc76021915ecdbafd1cdf796dce8b474ad03bb38`), `CELIKOM-Windows-0.24.37.zip` (SHA-256 `adc372876b49b9d9a3fbded7d7b1a751d69874469de0f71b8492cee39f39d16a`, exactly one EXE) and `SHA256SUMS.txt`. Outer archive, both digests and inner ZIP content checked independently.
- Exact main-source CI: [Main 43617609632](https://github.com/manufact-test/nomusic/actions/runs/43617609632) SUCCESS and [Windows integration 43617609631](https://github.com/manufact-test/nomusic/actions/runs/43617609631) SUCCESS. Stage job verified native code/GUI/Supervisor, single-AppId upgrade, per-user install/uninstall, zipped updater acceptance and checksums.
- Latest exact backups: W136 `backup/windows-main-pre-w136-stage-pipeline-current-version-20261114` @ `b7789299e901cf2218520f724043057744ef05ec`; W137 `backup/windows-main-pre-w137-one-package-exe-zip-20261114` @ `c2620d34884aad7d69d7e641e7b98e67bfe9716c`; W138 `backup/windows-main-pre-w138-first-owner-review-version-20261114` @ `48bd36d47aa1f7f2abfb0b89e95ffb8d5ecbdbdc`.
- **FIRST OWNER MANUAL ACCEPTANCE NOW REQUIRED**: real audio/VPN («Моя волна», «Ты», Big City Life, gain, 403→206), login/reconnect/diagnostics, Brave resource usage, startup/tray and suspicious elevation prompts. Group all checks; keep all six owner issues OPEN pending evidence. See `docs/windows/W138-SINGLE-OWNER-REVIEW-02437-EXE-ZIP-CI-20261114.md`.
- This owner-review build is **UNSIGNED**, private and **NOT** production. Automatic updater is dormant: no real approved stable HTTPS origin / P-256 public key / Authenticode signer fingerprint. Do not mass-distribute or declare automatic rollback production-proven. Do not create a second installer merely because docs or unrelated work changes.


## W136 — unblock the one existing CELIKOM Windows package-validation pipeline

- **Source/workflow-only fix; no installer built or published.** The old manually dispatched W20 packaging check expected a W56 executable and PE version 0.24.7, while the current application + Inno installer are 0.24.36. A future owner acceptance packaging run would fail even when the correct binary was built.
- Added `windows-companion/w20/stage-package-identity.ps1`: validates that the current Inno AppVersion/VersionInfoVersion exactly match the current GUI project version, validates the existing narrow internal updater-compatible filename, and only when `-RequireBuilt` is explicitly used checks the compiled installer and exports its actual name/version to later workflow steps.
- `.github/workflows/windows-w20-safe-installer.yml` now uses that exact current filename/version for the ZIP contract, install/uninstall smoke and private stage artifact rather than stale W56 paths. `Celikom.Companion.Tests/Program.cs` ZIP fixture now validates the real current assembly version and updater filename contract rather than hardcoded W100.
- Main Windows integration CI runs the metadata parity check **without building an installer** and rejects reintroduction of obsolete W56 paths.
- Exact pre-W136 backup `backup/windows-main-pre-w136-stage-pipeline-current-version-20261114` @ `b7789299e901cf2218520f724043057744ef05ec`. W136 code/workflow HEAD `152d07123bff4cebd71118141c766c8c62651c5a`.
- Main CI [43616078527](https://github.com/manufact-test/nomusic/actions/runs/43616078527) — **SUCCESS**; Windows integration [43616078592](https://github.com/manufact-test/nomusic/actions/runs/43616078592) — **SUCCESS**, including the new W136 source/installer identity gate, W15, Supervisor, GUI and original-source/VPN/audio tests.
- The W20 installer stage workflow remains **manual/internal** and was NOT dispatched. It does not create another product. First user acceptance package remains subject to W119's one-final-EXE+ZIP contract. Production update feed / approved P-256 key / Authenticode signer fingerprint are still absent; never substitute fake values or silently publish unsigned production updates.


# W127 — Reconcile current-decoder proof after queue identity race — 14 November 2026

- The Yandex queue's current track ID and native CDP `kUrl`/`kIsPlaying` events can arrive in either order. Previously, a valid signed CELIKOM decoder event arriving before the queue ID could remain unconfirmed if no further CDP property event followed.
- W127 retains bounded per-player decoder state and reconciles it after the existing current-track sample. It still requires a currently playing exact signed CELIKOM source mapped to the same current Yandex track; HTTP 206, grant delivery or mapping alone never turns the UI green.
- When the late queue ID makes the proof valid, the host emits the source witness once, sends the verified-only heartbeat and invokes the existing hook that cancels only a still-pending redundant reload. CDP detach/player destruction invalidate the witness.
- Regression coverage explicitly delivers decoder properties before queue identity and verifies no early attribution, one later source proof, verified heartbeat, pending-recovery hook and URL-free diagnostics.
- W127 implementation: `4fe42d745b6708524c65eb4f9855e026f314fefa`; test: `7e4c8268cba30f781a3fa091d9657718ec463b66`; exact pre-change backup: `backup/windows-main-pre-w127-current-decoder-witness-race-20261114` @ `4b7d2277d98986d8d4ab0ed9ba42a76fc25da810`.
- Main CI [43603865004](https://github.com/manufact-test/nomusic/actions/runs/43603865004) and Windows integration CI [43603864999](https://github.com/manufact-test/nomusic/actions/runs/43603864999) — **SUCCESS**.
- **#52 remains OPEN.** This fixes event ordering only; it does not prove audible output on the owner's PC. VPN A→B and all other owner-PC audio acceptance also remain open. No installer was built.

# W128 — Read-only CELIKOM elevation launch audit and CI guard — 14 November 2026

- Reviewed the current app launch paths, updater, Supervisor launcher, native installer modules, project settings and Inno installer. No explicit `runas` / `Verb="runas"` request was found in the reviewed CELIKOM paths.
- MainWindow launches Yandex normally; AppUpdateManager launches the verified Inno updater without an elevation verb; Supervisor is a same-user child process with `UseShellExecute=false`.
- The installer declares `PrivilegesRequired=lowest` and installs under `%LOCALAPPDATA%\Programs\CELIKOM`; the release gate checks this policy.
- Added a Windows Integration CI guard that rejects explicit `runas` in reviewed launch paths, requires the updater/Supervisor launch modes, keeps the installer per-user, and rejects an administrator manifest in the companion project.
- Exact pre-guard backup: `backup/windows-main-pre-w129-elevation-policy-guard-20261114` @ `911983107f257ec761f6c5c6666eec4748db3fd9`; guard commit: `cedcc45e5151afa62c1b292a7f4e2220226b6ac3`.
- Main CI [43604761393](https://github.com/manufact-test/nomusic/actions/runs/43604761393) and Windows integration CI [43604761386](https://github.com/manufact-test/nomusic/actions/runs/43604761386) — **SUCCESS**, including the new W128 guard step.
- This does **not** identify the prompt the owner saw, prove it came from Yandex, or establish that it was harmless. #53 remains OPEN until the prompt publisher/title is known and owner CPU/RAM/GPU evidence is available. Do not grant administrator rights to an unknown prompt.
- Full audit: `docs/windows/W128-READ-ONLY-ELEVATION-LAUNCH-AUDIT-20261114.md`. No runtime behavior changed and no installer was built.

# W135 — Retain source-decision evidence in durable owner diagnostics — 14 November 2026

- Diagnostics/archive policy and regression tests only; no player or audio behavior changed.
- Previously emitted source-decision events were not all treated as durable incidents. W135 preserves the allowlisted ORIGINAL, UNKNOWN, ACTIVE_REPLACEMENT, source-revalidation/reload, source-left and exact decoder-match events in the seven-day incident archive and 15-minute automatic support snapshot.
- Numeric track IDs remain validated. No signed URLs, tokens, audio data or arbitrary error messages are stored. Ordinary `NATIVE_CONNECTED` remains polling/status chatter, not an incident.
- W15 tests verify these source decisions survive more than 2,500 later native status polls and remain in the persistent owner TXT/archive without secrets.
- Exact pre-W135 backup: `backup/windows-main-pre-w135-source-transition-incident-retention-20261114` @ `adc87e2d3358fb64fba0a760518374e7d88e56c5`.
- Implementation commits: `e8e482da6acbfc677823e754066baa14e6e7d48e`, `3045a9deaa7f87e031313741b64f4f9fbdd6e5c5`; regression-test/final code-test HEAD: `5a40357d28f1a1cc4f467a16bfaaaf38aa530b3f`.
- Main CI [43610044707](https://github.com/manufact-test/nomusic/actions/runs/43610044707) and Windows integration CI [43610044672](https://github.com/manufact-test/nomusic/actions/runs/43610044672) — **SUCCESS**. Full W22/W23/W60 original-source, VPN, 403 and audio regression step plus W15 native contract tests passed.
- **#58 remains OPEN** pending real owner-PC VPN A→B playback acceptance; **#52 remains OPEN** pending owner-PC proof of audible replacement on «Ты» (13 карат).
- Full record: `docs/windows/W135-SOURCE-DECISION-INCIDENT-RETENTION-20261114.md`. No installer was built.

# W134 — Immediate downgrade coverage for every decoder-proof invalidation — 14 November 2026

- Regression tests only; W133 runtime behavior is unchanged.
- W134 verifies that each of four invalidation events — pause (`kIsPlaying=false`), current player destruction, current decoder pipeline error and CDP observer detach — immediately downgrades the exact current track from `NATIVE_SOURCE_VERIFIED` to neutral `NATIVE_MAPPING_ACCEPTED`.
- Each subtest starts with an exact signed current decoder and verifies the green heartbeat first. It then triggers one invalidation and checks the neutral heartbeat without waiting for the regular 2.2-second sampler. Signed media URLs must remain absent from heartbeat payloads and diagnostics.
- Exact pre-W134 backup: `backup/windows-main-pre-w134-verified-status-invalidation-matrix-20261114` @ `63b3a155bde732d527cfa57e5280bae69b3acbb6`.
- Regression-test/current code-test HEAD: `d6c091fb109baeaa1690b15ca3f90d7c914a279a`.
- Main CI [43609116940](https://github.com/manufact-test/nomusic/actions/runs/43609116940) and Windows integration CI [43609116972](https://github.com/manufact-test/nomusic/actions/runs/43609116972) — **SUCCESS**. Full W22/W23/W60 original-source, VPN, 403 and audio regression step passed, including all four W134 subtests.
- **#52 remains OPEN** pending owner-PC proof that «Ты» (13 карат) actually plays the alternate source; CDP source selection is not speaker-level proof.
- Full record: `docs/windows/W134-IMMEDIATE-DECODER-STATUS-INVALIDATION-MATRIX-20261114.md`. No installer was built.

# W133 — Immediate downgrade when current decoder proof is invalidated — 14 November 2026

- The native host previously waited for the regular 2.2s status sample to remove a green `NATIVE_SOURCE_VERIFIED` heartbeat after CDP observed that the current decoder left CELIKOM, stopped playing, was destroyed, errored, or the observer detached.
- W133 immediately sends the exact current track's heartbeat as neutral `NATIVE_MAPPING_ACCEPTED` on those proof-invalidating events. The status cache is updated at the same time; a failed local heartbeat rolls the cache back so the regular sampler can retry. A later fresh signed-current-decoder proof can restore `NATIVE_SOURCE_VERIFIED`.
- No player control, source reload, URL, queue or audio behavior is changed.
- W133 regression verifies immediate downgrade after source-left and successful promotion back to verified when the exact signed source becomes current again. Signed URLs remain out of heartbeats and diagnostics.
- Exact pre-W133 backup: `backup/windows-main-pre-w133-immediate-source-witness-downgrade-20261114` @ `2958b9d03fdd803eaab2f20dfad3c9bb4c63d1d9`.
- Runtime commit: `d548ed0af0f3717669c1fbcd903fc4f626428c7e`; regression-test/current code-test HEAD: `d79c20f37ce7428fca0e1abf1bdf3b0ad1a05832`.
- Main CI [43608584535](https://github.com/manufact-test/nomusic/actions/runs/43608584535) and Windows integration CI [43608584562](https://github.com/manufact-test/nomusic/actions/runs/43608584562) — **SUCCESS**.
- **#52 remains OPEN** pending owner-PC proof that «Ты» (13 карат) actually plays the alternate source; CDP source selection is not speaker-level proof.
- Full record: `docs/windows/W133-IMMEDIATE-DECODER-WITNESS-STATUS-DOWNGRADE-20261114.md`. No installer was built.

# W132 — VPN A→B revalidation after verified source-left — 14 November 2026

- Regression coverage only; no runtime code changed. The test starts with a current CELIKOM replacement, simulates the verified CDP source-left event, then applies VPN state-off and state-on with a fresh authenticated no-replacement result.
- It verifies there is no duplicate `QUALITY_CHANGE` reload after the decoder has returned to Yandex original, no replacement reload after the fresh no-match response, and no loss of playing state or position.
- This complements W98's original-from-start no-reload test and W131's verified source-left/state-off race test.
- Exact pre-W132 backup: `backup/windows-main-pre-w132-vpn-source-left-revalidation-20261114` @ `507052a14841ee08bf2ade513315618612130e8a`.
- W132 regression-test/current code-test HEAD: `c02cd4988292598f81e857062279d0179253a42a`.
- Main CI [43607847556](https://github.com/manufact-test/nomusic/actions/runs/43607847556) and Windows integration CI [43607847627](https://github.com/manufact-test/nomusic/actions/runs/43607847627) — **SUCCESS**. Full W22/W23/W60 original-source, VPN, 403 and audio regression step passed.
- **#58 remains OPEN** pending real owner-PC VPN A→B acoustic acceptance. CI proves CELIKOM does not reload the original source in this simulated sequence; it does not prove Yandex itself has no audible network-route pop.
- Full record: `docs/windows/W132-VPN-A-TO-B-SOURCE-LEFT-ORIGINAL-REVALIDATION-20261114.md`. No installer was built.

# W131 — Invalidate stale source mapping after verified decoder source-left — 14 November 2026

- When passive CDP has proved that the current decoder left its previously verified CELIKOM signed source, the renderer now clears that track's stale mapped-source marker immediately. This happens before checking whether CELIKOM is still enabled, so a racing VPN/entitlement state-off transition cannot issue a redundant `QUALITY_CHANGE` reload of a track already returned to Yandex original.
- If CELIKOM remains enabled, the existing bounded recovery path is preserved and can reapply a fresh authenticated grant. No entitlement bypass or player architecture change.
- Regression test verifies source-left followed immediately by state-off causes no second reload and preserves playing state/position. Existing W99 recovery still passes.
- Exact pre-W131 backup: `backup/windows-main-pre-w131-source-left-map-invalidation-20261114` @ `9eb710d1227f56419d6e9f35b34b44b7941ef8ae`.
- Runtime commit: `5fb5f32d0364d476889bf56d0f8e8fc0e38d71b2`; test/current code-test HEAD: `2f41091d1af072483ed5c79782958002b0ee2101`.
- Main CI [43606490844](https://github.com/manufact-test/nomusic/actions/runs/43606490844) and Windows integration CI [43606490908](https://github.com/manufact-test/nomusic/actions/runs/43606490908) — **SUCCESS**.
- **#58 remains OPEN** pending real owner-PC VPN A→B playback acceptance; this fixes a redundant CELIKOM reload after a verified source-left event, not every possible Yandex/network audio pop.
- Full record: `docs/windows/W131-VERIFIED-SOURCE-LEFT-STALE-MAPPING-INVALIDATION-20261114.md`. No installer was built.

# W130 — Safe CDP property-visibility diagnostics — 14 November 2026

- The previous owner export could not distinguish "CDP Media attached but no player-property events" from "player-property events arrived but Yandex did not expose `kUrl`".
- The passive host now records `PLAYER_CDP_PROPERTIES_SEEN` and `PLAYER_CDP_URL_PROPERTY_SEEN` based only on property names. It never logs the URL value, token, SID or other player-property values.
- The owner TXT export and automatic support snapshot expose `NativeDecoderPropertiesObserved` and `NativeDecoderUrlPropertyObserved`. Both event codes are retained in bounded incident history.
- The export explicitly says these booleans only show Media-domain field availability. They do not prove current-track identity, decoder selection or audible replacement.
- Regression tests cover properties without `kUrl`, subsequent `kUrl` presence, secret-free diagnostics, durable event retention and both export formats.
- Exact pre-W130 backup: `backup/windows-main-pre-w130-cdp-property-observability-20261114` @ `312d61a62fb4abcb779df539503adf4226818185`; code/test HEAD: `74b27a27c8f1560591ed9ae11c17f5fceb0d538e`.
- Main CI [43605388622](https://github.com/manufact-test/nomusic/actions/runs/43605388622) and Windows integration CI [43605388482](https://github.com/manufact-test/nomusic/actions/runs/43605388482) — **SUCCESS**.
- **#52 remains OPEN.** These are diagnostic visibility flags only. W127's strict current-track/signed-decoder proof remains unchanged, and actual playback acceptance still requires the owner's PC.
- Full record: `docs/windows/W130-SAFE-CDP-PROPERTY-VISIBILITY-DIAGNOSTICS-20261114.md`. No installer was built.

# W120 — Native-host performance evidence without changing playback cadence — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W120 code backup: `backup/windows-main-pre-w120-native-host-performance-20261114` @ `e4da7bad1bc83b4eb2888de6c3f4d67a0732af78`.
- W120 implementation commit: `9a9193d7bd728a4ff1a2da2f8b5f11c42c4d8a7b`.
- Main CI [43596984190](https://github.com/manufact-test/nomusic/actions/runs/43596984190) and Windows integration CI [43596984195](https://github.com/manufact-test/nomusic/actions/runs/43596984195) — **SUCCESS**.

## Changes

1. Native host caches the last safe state sent to the Yandex renderer. Identical state is not executed into the renderer repeatedly; the cache is cleared on renderer reinjection.
2. A failed local state read invalidates the cached enabled/disabled observation, so the next successful read can report the transition truthfully.
3. Every 30 seconds the host samples only its own Electron main-process CPU usage. At 80% or higher it records the fixed event `NATIVE_ELECTRON_CPU_HIGH`. Raw CPU counters, PIDs, process names, account identifiers and audio metadata are never written.
4. `DiagnosticLog` recognizes the CPU event as an incident, includes `ElectronCpuHighObserved` in the text export and preserves the event in support snapshots and diagnostic history.

## Deliberately unchanged

- Existing 300ms native relay cadence remains unchanged.
- CDP playback observation and 403 recovery remain enabled.
- No audio-source, gain, VPN or original-file behavior was changed.
- This is instrumentation and removal of redundant renderer IPC, **not proof that #53 is fixed**.

W23 tests cover unchanged-state deduplication, fixed CPU-threshold recording and the unchanged 300ms cadence. W15 tests cover diagnostics allowlisting, export, imported incidents and durable archive. No installer was built. Owner Task Manager evidence is still required to identify whether the load comes from CELIKOM, Brave, Yandex renderer, GPU or another process.

# W121 — Gate duplicate Start actions during first connection — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W121 code backup: `backup/windows-main-pre-w121-start-action-gate-20261114` @ `9a9193d7bd728a4ff1a2da2f8b5f11c42c4d8a7b`.
- W121 implementation commit: `62ff2b67f869607e20e9d8899113f391eab80c7e`.
- Exact green rollback snapshot: `backup/windows-main-post-w121-ci-green-20261114` @ the W121 commit.
- Main CI [43597478523](https://github.com/manufact-test/nomusic/actions/runs/43597478523) and Windows integration CI [43597478531](https://github.com/manufact-test/nomusic/actions/runs/43597478531) — **SUCCESS**.

## Changes

- Added the pure `PlaybackStartGate` policy and use the same rule in both the Start handler and Start-button availability.
- The gate blocks Start while the bridge is not ready, integration/update is busy, a previous Start is still pending, the app is closing, or playback is already enabled for the active native module.
- `StartAction` immediately calls `UpdateSafe()` after setting `_compactStarting`, so repeated clicks cannot be silently accepted by an enabled-looking button and then ignored.
- During the initial host/entitlement check, the compact hint says `Проверяем Яндекс.Музыку…`; the normal loading status remains for the active Yandex startup phase.
- W15 tests cover each blocked/allowed gate state; the Windows integration workflow statically guards both call sites and the pending-start hint.

This addresses the duplicate-click race in the first/repeated Start flow. It does **not** close the broader first-run/reboot/autostart owner acceptance, and it does not change audio, native installation, VPN or updater behavior. No installer was built.

# W122 — Trusted Supervisor readiness handshake and immutable helper snapshot — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W122 code backup: `backup/windows-main-pre-w122-supervisor-handshake-20261114` @ `7d0d6e162e8a51c169db05fc232674d6de93f4d2`.
- W122 implementation commit: `7622b8034a47526547d406ed4ec5988afc0569b5`.
- Exact green rollback snapshot: `backup/windows-main-post-w122-ci-green-20261114` @ the W122 commit.
- Main CI [43598267910](https://github.com/manufact-test/nomusic/actions/runs/43598267910) and Windows integration CI [43598267928](https://github.com/manufact-test/nomusic/actions/runs/43598267928) — **SUCCESS**.

## Changes

1. Added `StableUpdateSupervisorHandshake`: a transaction-GUID named pipe restricted to the current Windows user.
2. The Supervisor first reads and validates the DPAPI journal, checks production trust and its own signed image, performs its first engine tick, then sends READY. It does not acknowledge an unreadable or unsafe transaction.
3. Added `StableUpdateSupervisorLauncher.StartAsync(record)`. It accepts only a schema-2 `Prepared` transaction with matching pinned signer and previous Supervisor hash; it copies the old signed Supervisor EXE into that transaction's immutable snapshot directory, starts it from there with the existing `--supervise <guid>` contract, and waits up to eight seconds for READY.
4. The helper runs from the snapshot copy, so the future installer can replace the installed `CELIKOM.UpdateSupervisor.exe` without locking the image that is actively monitoring rollback.
5. Added a stable journal snapshot-path helper and a Windows named-pipe handshake regression test.

## Safety boundary / what is not yet complete

- W124 now wires the coordinator to this launcher. The coordinator advances `Prepared → InstallerStarted` and launches only after `StartAsync` returns READY; it rechecks the signed target and exact transaction-bound path at the final launch boundary.
- Production feed origin, P-256 public key and Authenticode signer fingerprint remain intentionally empty. The launcher and coordinator stay fail-closed while production trust is unconfigured; no keys, URLs or certificates were invented.
- W124 adds the 30-minute stable-update scheduler and signed package staging, but **the automatic updater is still not active in production** until the owner supplies/approves the real feed origin and production signing identities.
- No installer was built and no user installation was requested.

# W123 — Signed no-update result for stable manifest polling — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W123 code backup: `backup/windows-main-pre-w123-manifest-no-update-20261114` @ `40b8898c6c2489313f80b0e7a979b9e793e47dac`.
- W123 implementation commit: `5ae6b285889ca542d2ba30bbe25b5d3233800333`.
- Exact green rollback snapshot: `backup/windows-main-post-w123-ci-green-20261114` @ the W123 commit.
- Main CI [43598711117](https://github.com/manufact-test/nomusic/actions/runs/43598711117) and Windows integration CI [43598711096](https://github.com/manufact-test/nomusic/actions/runs/43598711096) — **SUCCESS**.

## Changes

- Added `StableUpdateManifestVerifier.VerifyIfNewer` and `StableUpdateManifestFetcher.FetchSignedIfNewerAsync`.
- The detached signature is always verified before a same-sequence manifest can be reported as a normal no-update result.
- An equal authenticated sequence returns `null` (no update); an older sequence or invalid signature remains a hard rejection.
- Existing strict `Verify` and bootstrap/version-specific fetch behavior remain unchanged.
- Tests cover equal-sequence no-update, tampered signature rejection, older-sequence rejection and the signed feed transport seam.

This is required for a real periodic stable updater: a current manifest must not be misclassified as a broken feed. It does not fetch from a production origin, launch an installer or activate the Supervisor. Production trust values remain empty. No installer was built.

# W126 — Single bounded entitlement activation for first install/upgrade — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W126 code backup: `backup/windows-main-pre-w126-single-start-activation-20261114` @ `2488e38ebfae605c78d9e3f511d6fca0901c5cc2`.
- W126 final code HEAD: `ed41f613640f55c8de4a027a8f6f12ac31a15093`.
- Exact green rollback snapshot: `backup/windows-main-post-w126-ci-green-20261114` @ the W126 code HEAD.
- Main CI [43601959568](https://github.com/manufact-test/nomusic/actions/runs/43601959568) and Windows integration CI [43601959593](https://github.com/manufact-test/nomusic/actions/runs/43601959593) — **SUCCESS**.

## Changes

1. First Start now checks the native integration state before sending activation. If the native module must be installed/upgraded, it goes directly to the existing consented `ConnectYandexAsync` transaction. It no longer POSTs activation once in `StartAction` and a second time after consent in `ConnectYandexAsync`.
2. `ConnectYandexAsync` now uses `StartupActivationRecovery.ActivateAsync`: at most one bounded retry for transient transport/temporary server errors, only while the same Start generation and account remain active. 401/403 and 429 are not retried.
3. After the fresh activation response, the compact access label/account confirmation/timestamp are updated and any older read-only preview is invalidated before the native install/upgrade continues.
4. A failed bounded network retry is handled as an entitlement/network failure, not mislabeled as native integration damage. It does not trigger the native-failure Yandex catalog refresh or a misleading install-failure modal.
5. Integration CI guards the order of the native readiness gate versus activation, the retry helper in the install path, and the post-activation account label update.

## Safety / scope

- The native integration still requires the existing explicit consent and existing signed native installer path. No new architecture, native patching strategy, or product variant was introduced.
- Server activation remains idempotent; this change removes the unnecessary duplicate request rather than changing trial/subscription policy.
- CI validates code paths only. No installer was built and no owner-PC install/audio test was requested.

# W125 — Invalidate current-decoder proof when CDP detaches — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W125 code backup: `backup/windows-main-pre-w125-decoder-detach-invalidation-20261114` @ `efbd6a1b1965472d8ad29519621a09d45a8651da`.
- W125 code HEAD: `d083218b4adb0b7fb1d1321d09b56245ab40fbd1`.
- Exact green rollback snapshot: `backup/windows-main-post-w125-ci-green-20261114` @ the W125 code HEAD.
- Main CI [43601333189](https://github.com/manufact-test/nomusic/actions/runs/43601333189) and Windows integration CI [43601333191](https://github.com/manufact-test/nomusic/actions/runs/43601333191) — **SUCCESS**.

## Change

The native host previously logged `PLAYER_CDP_DETACHED` but retained the last verified decoder witness. If the passive CDP observer detached after a valid `kUrl + kIsPlaying` pair, a stale proof could remain eligible for the green UI state for up to ten minutes.

On a valid webContents CDP detach, W125 now immediately clears:
- the verified current-decoder witness;
- expected signed audio and native media-success evidence;
- observer-ready state and bounded unfetched-reload attempts;
- cached decoder-player property state.

The existing renderer status can therefore fall back to mapped-but-unverified. It does not claim that a replacement is playing after losing the observer that proved it. The host does not try to seize or reattach DevTools; this path intentionally fails closed.

Windows integration CI now checks that the detach handler invalidates the witness and observer state. No playback command, reload, audio source, VPN behavior or original file was changed.

## What remains open

- #52 remains OPEN. W125 closes only the stale-proof-on-detach edge case; the real «Ты» playback/source behavior still needs owner-PC evidence.
- CI is not audible acceptance. No installer was built and no owner installation was requested.

# W124 — Stable update coordinator, safe scheduling and Supervisor-gated install — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W124 code backup: `backup/windows-main-pre-w124-stable-update-coordinator-20261114` @ `e734579f0f6e6aff1436bbccdbc1396a055cb788`.
- W124 final code HEAD: `cd5d2bf623f368529e5efd16e3d95c813975ad8d`.
- Exact green rollback snapshot: `backup/windows-main-post-w124-ci-green-20261114` @ the W124 code HEAD.
- Main CI [43600704215](https://github.com/manufact-test/nomusic/actions/runs/43600704215) and Windows integration CI [43600704211](https://github.com/manufact-test/nomusic/actions/runs/43600704211) — **SUCCESS**.

## Changes

1. Added `StableUpdateInstallCoordinator`, the single stable update transaction. It checks the immutable production trust tuple first and refuses to run if any production pin is absent.
2. Added a 30-minute WinForms scheduler in `MainWindow.StableUpdate.cs`. It is started only when production trust is configured. Each check defers while CELIKOM bridge is enabled, Yandex is running, playback state is unknown, or another install/host operation is busy.
3. The coordinator obtains/verifies the signed last-known-good installer, polls the signed latest manifest using W123 equal-sequence/no-update semantics, downloads and verifies a newer package, then rechecks idle state after download.
4. It creates a DPAPI-backed transaction with byte-identical previous/target signed installers and existing account/session/native identity, launches the immutable signed Supervisor snapshot through W122, and waits for its READY handshake.
5. Only after READY does it advance `Prepared → InstallerStarted`, reverify the exact journal-bound target installer (SHA-256, Authenticode signer, manifest identity), and call the existing Inno AppId upgrade path. A launch failure is recorded as `ManualRecovery`; no unverified or unjournaled path can be executed.
6. Restored W117's asynchronous first-install LKG bootstrap call and method. It remains behind the same pinned production trust and Yandex-idle gates.
7. Added regression coverage for trust-unconfigured fail-closed behavior and the installer-started-to-manual-recovery transition. Windows integration CI also guards the coordinator, scheduler, Supervisor launcher, signed latest-manifest fetch and final signed-launch path.

## Safety boundary / what is not complete

- Production feed origin, P-256 public key and Authenticode signer certificate fingerprint are still empty by design. No real official delivery URL, key or certificate was invented.
- Therefore `TryGetProduction` returns false in this build: the scheduler does not start and the coordinator does no network or install work. **The updater is wired but not activated for production.**
- Still required: owner-approved official HTTPS feed, production P-256 public key, production Authenticode certificate fingerprint and protected release-side signing/publishing. Then run the real signed-feed install, forced-failure, Supervisor crash/one-shot rollback, account/session preservation and recovery tests.
- CI validates code and simulations only. No production installer was built; no owner installation or audible test was requested.


### Implemented and CI-validated infrastructure
W122 adds the transaction-scoped current-user Supervisor READY handshake and immutable snapshot launch bridge. W123 adds signed no-update polling semantics. W124 wires both into a single fail-closed stable update coordinator, the 30-minute scheduler, journaled signed staging and final verified installer launch. W125 invalidates the current-decoder proof immediately if CDP detaches, preventing stale green playback claims. W126 removes the duplicate first-install activation POST and applies bounded transient retry to the consented native install path. The updater path remains dormant until production trust pins are provisioned.
W105–W118 contain signed-package validation, SHA-256/Authenticode checks, DPAPI rollback journal, previous/target package retention, independent Supervisor health witness, schema-2 exact payload identity, signed manifest generation, immutable version manifests, initial LKG bootstrap and shared fail-closed trust configuration. W20 verifies the existing installer definition contains exactly:
- existing CELIKOM app EXE;
- `integration/host.cjs`;
- `integration/renderer.js`;
- `CELIKOM.UpdateSupervisor.exe`.

This is meaningful implementation progress, **not a production-ready automatic updater**.

### W118 server-side gain proof
- W90 inventory: 1,493 active approved replacements; one nonzero-gain row (replacement 37 / track 40371622 / +11.5 dB), 1,492 zero-gain rows, no invalid values.
- W98 verified the existing private sidecar's exact source/version/gain/SHA identity and live signed HTTP 206 range. No new render or sidecar row was needed.
- Stage 5 integrity audit passed; live DB was not restored/rewritten and original audio objects were not changed.
- Nine W98 identity/TSV tests passed.
- This is server-side proof only. It does not close Windows listening/seek/Next/crossfade/403/VPN behavior or #56 owner acceptance.

### Still incomplete
- All owner issues #52, #53, #54, #56, #57 and #58 remain **OPEN**; CI is not audible or owner-PC acceptance.
- W120 adds privacy-safe Electron main-process CPU evidence and removes repeated identical renderer-state deliveries; #53 root cause remains unproven until owner diagnostics and a Task Manager CPU/RAM/GPU capture are available.
- W121 blocks duplicate Start clicks during pending host/entitlement checks and shows a small progress hint. First/repeated connection, reboot, tray and autostart still need one grouped owner-PC acceptance pass.
- #52 source truth (W125 now also clears stale decoder proof on CDP detach), #54 Big City Life volume, #56 real gain loudness/headroom, #57 audible 403→206 recovery and #58 original-track VPN continuity still need owner-side evidence; do not mark them fixed from CI.
- Automatic updater is not production-ready: W124 now provides the coordinator/MainWindow callsite, 30-minute scheduler, signed package staging, DPAPI transaction, Supervisor READY gate and final signed launch checks. Production P-256 pin, Authenticode signer pin and official HTTPS feed origin are still empty/unprovisioned, so the path is deliberately dormant. A real production-signed feed/install/crash/one-shot rollback run remains outstanding.
- No final Windows EXE+ZIP has been built or delivered.

### Legacy installer naming — do not misinterpret it
The current Inno script still has historical `AppVersion=0.24.36` and `OutputBaseFilename=CELIKOM-W100-WINDOWS-02436-INTEGRATED-QA-TEST-UNSIGNED`. This is stale W100 metadata, **not** a separate product or a request to create a TEST build. Do not build/distribute that stale artifact. At the end, update the final version/name as part of the single final `main` build. No interim installers.

## Owner's complete task list

1. VPN A→B: reliable, fast reconnect/recovery without long hangs, hiss or quiet return.
2. #52 «Ты» (13 карат): truthful confirmation of the actual alternate playback source; no false “active” state.
3. #53 Brave/Windows performance: W120 adds main-process CPU threshold evidence and renderer-state deduplication without changing the 300ms relay; root cause and owner Task Manager evidence still pending.
4. #54 Big City Life: fix the mid-track volume drop.
5. #56 admin gain: apply consistently to intended tracks; verify real loudness/headroom, seek, Next, crossfade and recovery.
6. #57 expired URL 403→206: remove hiss/click/pop during stream recovery.
7. #58 originals/«Моя волна»: prevent pops/cuts when VPN changes during non-replaced playback.
8. First connection/startup: W121 prevents duplicate Start actions while a connection check is pending; unsupported-version/server errors, subsequent launches and grouped owner-PC acceptance remain.
9. Diagnostics: keep available after disconnect and make status truthful.
10. Autostart/tray: correct Windows startup, tray, reconnect and failure recovery.
11. Yandex update detection: at least every 30 minutes, preferably faster.
12. Signed updater: finish signature, SHA-256, Authenticode and package-substitution protection.
13. Supervisor: W122 adds the signed helper snapshot and READY launcher; W123 adds signed no-update manifest semantics; W124 wires the coordinator, scheduler, signed staging, READY gate and final verified launch. Production trust and real end-to-end signed-feed/rollback acceptance remain outstanding.
14. Automatic one-shot rollback: restore last working version after failure while preserving account/DPAPI/native/user data.
15. Production update delivery: real keys/certificates, official HTTPS origin, signed manifests and reliable delivery.
16. Integrated verification: update, forced failure, rollback, account/native/Yandex safeguards and full regressions.
17. One final EXE+ZIP and mass update only after all work and owner acceptance.

Full descriptions and strict work rules are in W119. Do not drop or replace any item.

## Mandatory work method and next order

- Continue directly on `main`; create and verify an exact `backup/*` before substantial code changes.
- Work in large coherent blocks; do not stop after each small patch or ask the owner to manually test intermediate builds.
- Finish the complete Windows issue/task list and the updater end-to-end in the one existing product. Do not package early.
- Never touch Android, browser extension behavior, original audio files or unrelated server logic during Windows work.
- Do not invent production pins, certificates or feed URLs. Do not request passwords/emails/tokens or private signing keys in chat.
- CI is necessary but does not prove audible or owner-PC acceptance. Keep issues open until the behavior is actually fixed.
- After the complete work, run integrated CI/security/regression checks, then create one final EXE+ZIP from `main`. Group unavoidable owner-PC checks into one consolidated acceptance pass. Only after acceptance prepare mass update.
- Keep reports short and infrequent. Continue working without progress spam; ask the owner only when a real owner action is necessary.

## Controlling handoff

Read `docs/windows/W119-AUTHORITATIVE-OWNER-CONTRACT-AND-WINDOWS-HANDOFF-20261114.md` first. The W117/W118 and W100–W118 notes below are historical implementation records. Their old “next priority”, “QA package”, “TEST release”, branch and installer instructions are superseded. Do not follow them as current work orders.

---

## Historical technical records — archive only; W119 overrides stale next steps

## W117 — shared fail-closed trust configuration and dormant first-LKG startup bootstrap

- Added `StableUpdateTrustConfiguration.cs`: one shared immutable trust tuple for GUI and Supervisor (official HTTPS origin, P-256 public key DER, Authenticode signer SHA-256).
- All three production values intentionally remain empty. No environment variable, CLI argument, registry, remote manifest or user-editable file can supply/override trust. The manifest private key is not in the client and must remain in protected release infrastructure.
- `TryCreate` validates HTTPS root origin, P-256 curve OID, DER consumption and exact 64-hex signer fingerprint; returned public-key bytes are defensively copied.
- `MainWindow` starts `BootstrapStableRollbackIfConfiguredAsync` in the background after startup. It runs only when the full production trust tuple is configured AND CELIKOM's bridge is disabled AND no Yandex Music process is running. It only verifies/seeds the exact-version LKG package; it does not install, restart CELIKOM or touch Yandex.
- Failures produce only the fixed diagnostic code `STABLE_ROLLBACK_BOOTSTRAP_UNAVAILABLE`; no URLs, paths, exception text, credentials or music data are logged.
- Supervisor now reads the same shared trust tuple and exits code 3 before journal access or installer execution while values are empty.
- W15 tests cover valid P-256 config, non-P-256 rejection, malformed DER/Base64, HTTP/path/user-info rejection, malformed signer hash, immutable public-key copies and default production-disabled state. Workflow guard confirms the startup bootstrap cannot launch an installer and waits for Yandex idle.
- Exact code/test HEAD `5b5a2e0845eb1d9f02400ae382d702c25abedf43`: Main CI [43587767442](https://github.com/manufact-test/nomusic/actions/runs/43587767442) SUCCESS; Windows integration [43587767458](https://github.com/manufact-test/nomusic/actions/runs/43587767458) SUCCESS.
- Full details: `docs/windows/W117-TRUST-CONFIG-AND-DORMANT-LKG-BOOTSTRAP-20261114.md`.

## W116 — first signed-install bootstrap and immutable version manifest

- The first-install gap is implemented: exact-version immutable signed metadata can recover the signed installer for the currently installed release and seed the first DPAPI LKG package.
- Versioned `{version}/manifest.json` and `.sig` files are immutable; `latest.json` remains the mutable discovery pointer.
- Journal state `Seeded` is a real initial LKG, not a fake previous release. The first later signed update can reuse it as its previous installer.
- W117 now wires the bootstrap to startup behind the empty production trust gate and Yandex-idle check. It remains dormant until owner-approved pins and official origin are populated.
- Exact W116 code/test HEAD: `d1c807dbc2bb748a8a6d692ef0e01b96a5d9f7d5`; Main CI [43585155970](https://github.com/manufact-test/nomusic/actions/runs/43585155970) and Windows integration [43585155942](https://github.com/manufact-test/nomusic/actions/runs/43585155942) SUCCESS.
- Full details: `docs/windows/W116-FIRST-SIGNED-BOOTSTRAP-AND-IMMUTABLE-VERSION-MANIFEST-20261114.md`.

## W115 — durable signed last-known-good package cache

- Each completed transaction retains both verified previous and target installers, with DPAPI journal and exact four-file payload hashes.
- W116 added the initial `Seeded` package for the first signed install.
- Full details: `docs/windows/W115-LAST-KNOWN-GOOD-SIGNED-PACKAGE-CACHE-20261114.md`.

## Still blocked — do not call updater ready

- Production P-256 public-key pin, Authenticode signer certificate SHA-256 fingerprint and official stable-feed origin are not provisioned. Shared constants in `StableUpdateTrustConfiguration.cs` remain empty; Supervisor intentionally exits code 3.
- No live signed feed/package publisher or atomic upload target is confirmed.
- W117 wires only the dormant first-LKG bootstrap. The main app still has no signed `latest.json` consumer, no trusted same-user Supervisor launch callsite, no install coordinator and no automatic customer update scheduling/notices.
- No real production-signed installer/feed, forced GUI crash, automatic one-shot rollback, owner-PC account-preservation or Yandex-idle end-to-end test has run.
- No final EXE+ZIP has been built or delivered. No mass release.

Do not paste private keys into chat or commit them. Do not fill production pins with guessed values. Do not publish to the Hostinger QA hostname as a substitute for the official feed. Do not enable automatic installation until the actual signed update/rollback path passes on Windows.

## Superseded W117/W118 work-order snapshot — archive only

The W117/W118 implementation records immediately above this point are historical. Their old instruction to prepare an early “QA” or “TEST” EXE+ZIP is superseded and must not be followed. Their old Stage 5/W98 repair sequence is also superseded: W118 records the successful W90/W98/Stage 5 results. Current work is defined only by the authoritative top of this file and W119.

## W113–W114 implementation history — 14 November 2026

- **W113 manifest generation:** c7451d90863581794c70df7a3dc8c2525ee4930c; backup backup/windows-main-pre-w113-stable-manifest-publisher-20261114 @ d136d52d595574c25461fc05590ac7078a739cf6. Generator builds the exact schema-2 JSON and P-256 DER signature, requires the signing private key to match the client-pinned public key, and hashes the package plus installed payload. W116 extends output with immutable per-version manifest/signature files beside the mutable latest pair. W113 tests: Main CI 43578863477 SUCCESS; Windows integration 43578863492 SUCCESS.
- **W114 supervisor payload binding:** 5fbc5ed39694dbd43329d47e2ea169f4142cf540; backup backup/windows-main-pre-w114-supervisor-payload-20261114 @ c7451d90863581794c70df7a3dc8c2525ee4930c. Schema 2 now requires four installed-file hashes: CELIKOM.Companion.exe, integration/host.cjs, integration/renderer.js and CELIKOM.UpdateSupervisor.exe. DPAPI journal stores previous/target hashes for all four. The existing Inno installer includes the supervisor; the existing W20 and Hostinger QA build paths build it before compiling the same installer.
- **W114 implementation CI:** Main 43579759654 SUCCESS; Windows integration 43579759677 SUCCESS.
- **Packaging guard:** 273fe22132123d7af7d3e961748b9d09104c0c7a verifies the Inno entry, both build paths and installed-file smoke assertion. Main CI 43580005463 SUCCESS; Windows integration 43580005419 SUCCESS.
- **Still NOT production-ready:** production P-256 public-key pin, Authenticode certificate fingerprint and official feed origin remain unprovisioned in the shared `StableUpdateTrustConfiguration`; all three values are intentionally empty. W113/W116 generate signed metadata locally but do not publish a live feed. W117 wires only a dormant first-LKG startup bootstrap behind the empty trust gate and Yandex-idle check. The main app still has no signed latest-manifest consumer or trusted Supervisor launch callsite. No real signed install, forced GUI crash, one-shot restore or owner-PC test has run. No final EXE+ZIP has been produced.
- **Open owner checks remain:** issues #52, #53, #54, #56, #57, #58. CI does not replace VPN/audio/volume/original-track/first-run/tray checks on the owner PC.
- Do not use the Hostinger private QA domain as the official stable-feed origin without explicit confirmation. Do not paste or commit production keys/certificates. Do not run the manual Hostinger QA installer workflow or mass release as a substitute for the signed production flow.

**Next work order:** after the owner-approved Windows audio fixes and one coherent owner QA build, return to production trust provisioning; confirm the official HTTPS origin and atomic upload target; publish immutable per-version manifest/signature plus package; wire the signed latest-manifest consumer and same-user Supervisor launch; run a real signed update/forced-crash/one-shot-rollback test while preserving the account, native integration and Yandex playback. Only after that create one final EXE+ZIP for owner QA.

**Read first:**
1. `docs/windows/W102-SINGLE-PRODUCTION-LINE-YANDEX-15MIN-AND-WORK-ORDER-20261113.md`
2. `docs/windows/W101-CELIKOM-WINDOWS-AUTO-UPDATE-AND-ROLLBACK-POLICY-20261113.md`
3. `docs/windows/W112-EXACT-SIGNED-PAYLOAD-IDENTITY-20261114.md`
4. `docs/windows/W110-W111-INDEPENDENT-SUPERVISOR-SESSION-WITNESS-20261114.md`
5. `docs/windows/W109-DURABLE-SIGNED-ROLLBACK-JOURNAL-20261114.md`
6. `docs/windows/W105-W108-STABLE-UPDATER-TRUST-AND-NO-AUTOPLAY-20261114.md`
7. `docs/windows/NEXT-CHAT.md` (this file)
8. GitHub issues #52, #53, #54, #56, #57, #58; read actual code before changing.

**Exact latest code CI proof:**
- Main CI [43577376444](https://github.com/manufact-test/nomusic/actions/runs/43577376444) — SUCCESS.
- Windows integration CI [43577376383](https://github.com/manufact-test/nomusic/actions/runs/43577376383) — SUCCESS, including W22/W23/W60 audio/VPN/source/403, W21 recovery, W24 ASAR/catalog, W15 payload/session tests, W110 watchdog simulation, schema-2 payload identity, and warning-as-error GUI/supervisor builds.
- Earlier W112 checkpoint [43577075078](https://github.com/manufact-test/nomusic/actions/runs/43577075078) / [43577075086](https://github.com/manufact-test/nomusic/actions/runs/43577075086), both SUCCESS at `d066efc9` before the final stager-level missing-payload guard.
- Earlier W103 `d903ffae` failed four integration tests because expected reload occurred before new 150 ms confirmation window; fixed in `7a4768e` with tests preserving actual delayed behavior. Do **not** revert to the failed intermediate.
- Stage 5 Hostinger restore proof [43514995243](https://github.com/manufact-test/nomusic/actions/runs/43514995243) SUCCESS: 1498 original audio SHA256 checks and isolated DB restore with Big City Life gain sidecar. Live DB untouched in that test.
- Dedicated gain-stage job [132132259655](https://github.com/manufact-test/nomusic/actions/runs/43495186951) SUCCESS: Big City Life track 40371622, configured +11.5 dB, measured +6.70 dB RMS and verified signed Range 206. Its parent workflow failed later in updater ZIP verification, **not** sidecar staging.

## W112 — historical base: exact signed installed-payload identity (superseded by W113/W114)
- Exact code commit `a7dbed8e19c9f23d952f689c1074c6057d0116d0`; Main CI [43577376444](https://github.com/manufact-test/nomusic/actions/runs/43577376444) **SUCCESS**; full Windows integration [43577376383](https://github.com/manufact-test/nomusic/actions/runs/43577376383) **SUCCESS**.
- Exact post-W112 rollback: `backup/windows-main-post-w112-payload-identity-ci-green-20261114` @ `a7dbed8e19c9f23d952f689c1074c6057d0116d0`. Pre-W112 backup `backup/windows-main-pre-w112-signed-payload-identity-20261114` @ `3f2c528a9a3b01a1db6a76dcda84d8e466c724d2`; W112b pre-stager-guard backup `backup/windows-main-pre-w112b-require-payload-at-staging-20261114` @ `d066efc937803ec1d0a1b6362de1883a6cf6c812`.
- Signed stable manifest contract is now **schema 2** and requires lower-case SHA-256 values for three installed files: `applicationSha256` = `CELIKOM.Companion.exe`, `nativeHostSha256` = `integration/host.cjs`, `rendererSha256` = `integration/renderer.js`. Schema 1 feeds are rejected.
- `StableUpdatePackageStager.FetchVerifiedAsync` and `VerifyInstaller` both fail closed if any of the three signed payload hashes are missing/invalid. Package SHA256 remains separately checked against the signed installer package bytes.
- W109 DPAPI journal schema 2 stores the previous and target app/host/renderer hashes. New transactions require all six. The W110 engine refuses schema 1 or any missing payload witness; legacy records are never eligible for unattended transitions.
- The independent W110 health probe checks exact installed bytes for the EXE + both integration assets, then verifies Authenticode signer pin, PE identity/version, running process path, authenticated local bridge, original DPAPI account fingerprint and native integration. The rollback health check uses the previous version's exact three payload hashes too.
- Tests: W15 validates signed schema 2, rejects schema 1/malformed/missing hashes, tampering of each installed file, missing files and journal preparation without payload identity. W110 simulation checks mismatched app/host/renderer hashes and refuses schema 1. W15 and W110 test steps, GUI/supervisor warning-as-error builds and existing Windows regression suite are green.
- **W112 checkpoint only:** schema 2 was a code contract, not a published production feed. W113/W114 subsequently added the manifest generator and bundled/hash-bound the helper. Production P-256 public key and Authenticode certificate pins remain unprovisioned; the main app still does not launch the helper; no real signed installer/crash/rollback end-to-end test or owner-PC acceptance exists. No final signed EXE+ZIP or mass release.
- Historical W112 next steps are superseded by the current W113/W114 order above. Keep Yandex closed during any rollback.

## W110–W111 latest VERIFIED / 14 November 2026
- ONE active work branch `main`. Exact green W111 code: `be6bda507aeeb68a7046a4ad12c41448d139860a` with **Main CI** [43575703455](https://github.com/manufact-test/nomusic/actions/runs/43575703455) SUCCESS and **full Windows integration** [43575703509](https://github.com/manufact-test/nomusic/actions/runs/43575703509) SUCCESS. Exact snapshot: `backup/windows-main-post-w111-account-witness-ci-green-20261114` @ this SHA.
- W110 isolated internal-process supervisor green checkpoint `d6d2850e8f27e3b5a582879b8063465d4a442b80`, exact snapshot `backup/windows-main-post-w110-supervisor-ci-green-20261114`; CI [43575142613](https://github.com/manufact-test/nomusic/actions/runs/43575142613) and Windows [43575142609](https://github.com/manufact-test/nomusic/actions/runs/43575142609) SUCCESS. Pre-W110 backup `backup/windows-main-pre-w110-independent-supervisor-20261114` @ `6594328612c9349c3c4a235251dc1a88975a1d7b`. Pre-W111 backup `backup/windows-main-pre-w111-session-identity-witness-20261114` @ `d6d2850e`.
- W110 `Celikom.UpdateSupervisor` is a **separate internal helper process of the ONE CELIKOM product**, not a second consumer app. Simulated independent watchdog handles startup failure, signed-app/bridge/DPAPI/native checks, safe playback-idle rollback, verified old installer, at-most-one attempt, timeout and manual recovery. W110 tests cover 17 scenarios. W111 adds prior **installation GUID + normalized account** fingerprint to W109 DPAPI journal, fails closed on replacement/missing/corrupted login, does not punish token rotation. See `docs/windows/W110-W111-INDEPENDENT-SUPERVISOR-SESSION-WITNESS-20261114.md`.
- **ABSOLUTELY NOT customer-ready:** production certificate fingerprint remains empty in the shared trust configuration; Supervisor invocation exits code 3, confirmed in CI. The helper is included in the existing installer payload under W114, but the trusted main-app Supervisor launch callsite is still absent. W117 adds only a dormant LKG bootstrap callsite. Signing keys/pins, release-signed Authenticode EXE/helper, signed stable feed, independently tested real installation/recovery, scheduled notices and automatic rollout are missing. W110 unit tests simulate probes/installer, not a real signed Inno package or crash in the wild.
- **Next concrete code order:** publish and pin the schema-2 manifest/key/certificate through existing secure release infrastructure; add the supervisor's own payload hash when it is packaged; wire the helper into the same CELIKOM installer without creating another product; prove real signed update + killed-GUI rollback + preserved login on Windows while Yandex is closed; finish stable-feed scheduler and user UI; then one owner EXE+ZIP and field QA. No random branch, no new user secrets/accounts/emails, no interim release.
- Existing owner-PC defects VPN, #52/#53/#54/#56/#57/#58, startup/tray/diagnostics and audible proof remain OPEN. Green CI is not owner playback QA.

## W109 — 14 November 2026: durable rollback journal (CODE + CI GREEN)
- **Exact verified code:** `0d90fea82cfd8d95e7c830941e1443cafa594fd3`; backup `backup/windows-main-post-w109-rollback-journal-ci-green-20261114` points to the same SHA. Pre-W109 exact backup: `backup/windows-main-pre-w109-rollback-transaction-20261114` @ `2331a7de51c9ae2f33162bc382c77ad65bd34bb8`.
- CI [43572820346](https://github.com/manufact-test/nomusic/actions/runs/43572820346) **SUCCESS**; full Windows integration [43572820294](https://github.com/manufact-test/nomusic/actions/runs/43572820294) **SUCCESS**. Only `StableUpdateRollbackJournal.cs` and W15 contract tests changed in W109.
- Windows DPAPI-per-user durable journal + atomic rewrite, signed-old-installer byte snapshot and re-verification, pending-upgrade mutual exclusion, 10-minute bounded health decision, **one permitted rollback attempt**, and separate, evidence-gated `Healthy` / `Restored` transitions. A completed transaction permits another approved release while active/crash recovery records are never overwritten. Tests exercise healthy, failed/timeout, replay refusal, invalid health, tampered snapshot, DPAPI ciphertext alteration, and sequential release.
- **NOT a finished automatic rollback:** `PrepareSigned` has NO consumer call site; test-only synthetic verifier is not a real signed installer. No independent external watchdog process, install/rollback launcher, production signing pins/keys, signed live feed or real owner-PC install tests. W109 never modifies Yandex, plays audio, launches an installer or marks a user machine updated.
- **Next:** implement and test a truly independent signed-package watchdog (survives new app crashes) using this journal; obtain production signing/public trust configuration through existing release infrastructure without asking user for new secrets, then bounded stable polling/idle install/in-place recovery. One final signed EXE+ZIP only after end-to-end Windows and owner QA.
- Full file: `docs/windows/W109-DURABLE-SIGNED-ROLLBACK-JOURNAL-20261114.md`.

## Latest implementation W105–W108 / 14 November 2026

- **Verified code** `1ad2c63e78746db49ca8bca5e0c3c8bee2cbc48b` on the only active `main` branch. Exact green rollback: `backup/windows-main-post-w108-updater-guards-ci-green-20261114` @ that SHA. Other exact safety snapshots: `backup/windows-main-pre-w105-secure-package-staging-20261114` @ `553c5fb0059aa55e92959f93db1d18dbd2f9600e`, `backup/windows-main-post-w105-w106-ci-green-pre-feed-20261114` @ `61dd35c07951be0b5f607afd2fbf548ff1509eeb`, `backup/windows-main-post-w107-signed-feed-ci-green-20261114` @ `685e95a2f40c0b58d06df4d907e856a8da13bc19`.
- **Latest exact CI:** main [43569385121](https://github.com/manufact-test/nomusic/actions/runs/43569385121) SUCCESS; full Windows integration [43569385123](https://github.com/manufact-test/nomusic/actions/runs/43569385123) SUCCESS. Previous W107 main [43568654764](https://github.com/manufact-test/nomusic/actions/runs/43568654764) / integration [43568654802](https://github.com/manufact-test/nomusic/actions/runs/43568654802), both SUCCESS.
- **W105:** bounded immutable HTTPS binary stage, exact bytes and SHA256, Authenticode trust, *independently pinned signer certificate SHA256*, PE identity/version and pre-launch recheck; all failures fail closed and delete staged file. Does not execute downloads.
- **W106:** signed mandatory rollback is allowed only with a new monotonic release sequence, exact `fromVersion` equal to the running bad version and lower `toVersion`. Unsigned, replayed and arbitrary downgrades denied. This is *authorization logic*, not an automatic rollback helper.
- **W107:** read-only signed `latest.json` and `latest.json.sig` over exact HTTPS origin, bounded no-redirect response, detached P256 signature verification. No key is pinned into shipping application yet, no automatic checks are wired.
- **W108:** current staff/manual in-place update refuses to start while Yandex is running or CELIKOM bridge enabled; removes auto-start of Yandex after update and premature `APP_UPDATE_COMPLETED` claim; emits only actual local-start/native-identity evidence and clears pending ticket only if the installer never started. Windows integration has an explicit no-autoplay source guard.
- **NOT DONE:** no release-signed Authenticode CELIKOM binary, production manifest public key/pinned signer, live signed stable feed, consumer background polling/prompt/install, independent crash watchdog and last-known-good package rollback, or final signed EXE+ZIP. Those are release blockers per W101. No temporary/unsigned EXE was delivered, no mass publish or installation.
- **Owner QA remains:** VPN reconnect, #52/#53/#54/#56/#57/#58, first-launch/reboot/diagnostics/autorun and genuine audio, plus in-place upgrade and rollback. Do not mark audio fixed by CI.
- Full engineering details: `docs/windows/W105-W108-STABLE-UPDATER-TRUST-AND-NO-AUTOPLAY-20261114.md`. Work directly on `main`; create only `backup/*` before substantive changes, never edit Android, extension, original media or unrelated server. No new secrets/accounts/emails.

## Follow-up W104/W101 — 14 November 2026
- **Actual source**: last proven main code commit `9ac9a5ab485c3ce1bebc8aa6a2352b422c0ffa1c`; current pinned known-good pre-W104 backup `backup/windows-main-pre-native-failure-recheck-20261114` @ `f82dbe4448ff743945da4d4d26f159bfbaeb2766`. Intermediate exact green checkpoint `backup/windows-main-post-native-failure-recheck-ci-green-20261114` @ `f4449475ff0298c82b52426ded28b73217ec2439`. W101 contract pre-change backup `backup/windows-main-pre-w101-signed-feed-contract-20261114` @ `3cc58b93a244d3711b7cda06010e550212731935`.
- **W104 code+CI**: explicit authenticated native `HOST_ERROR`, 22-second Start with no native handshake, and native install/upgrade exception trigger an immediate data-only reviewed-catalog refresh followed by host inspection; events coalesce, repeated errors back off 2/4/8/15 minutes, native heartbeat resets the backoff. This never autoruns Yandex, changes audio source, patches the host, assumes entitlement, or trusts a new vendor version without exact proofs. W104 3cc CI [43528538262](https://github.com/manufact-test/nomusic/actions/runs/43528538262) SUCCESS, full Windows CI [43528538351](https://github.com/manufact-test/nomusic/actions/runs/43528538351) SUCCESS. Real owner field proof pending.
- **W101 progress, NOT automatic updater**: `StableUpdateManifestVerifier.cs` validates a detached P256 signature, stable-only manifest, monotonic release sequence, expiry, exact HTTPS origin and immutable version path; anti-replay and anti-downgrade tests. This class does not fetch, stage or launch binaries. No production-pinned public key, Authenticode-signed installer, independent crash-health rollback supervisor or signed live feed exists here. Auto-install remains OFF, and unsigned customer rollout is BLOCKED. Latest signed-manifest code+test gates: Main CI [43529667031](https://github.com/manufact-test/nomusic/actions/runs/43529667031) SUCCESS; Windows integration [43529666957](https://github.com/manufact-test/nomusic/actions/runs/43529666957) SUCCESS (exact code commit). Exact rollback for the new green code: `backup/windows-main-post-w104-w101-guards-ci-green-20261114` @ `9ac9a5ab485c3ce1bebc8aa6a2352b422c0ffa1c`. Intermediate W101 test compilers failed before the last fixes; do not use those intermediary revisions.
- **Still open**: #52/#53/#54/#56/#57/#58 acoustic/owner-PC evidence, VPN reconnect, first-launch GUI/reboot acceptance, complete signed in-app download/install/rollback, one owner-approved EXE+ZIP and mass rollout. No installer delivered in this continuation. See `docs/windows/W104-NATIVE-FAILURE-RECHECK-AND-W101-STABLE-MANIFEST-20261114.md`.

**Open defects (do not call them done):**
1. VPN reconnection 40–50 seconds — recovery code/CI exists, owner field test pending.
2. #52 «Ты» (тринадцать карат) false green — current decoder proof guard exists; audible alternative still needs confirmation.
3. #53 Brave/Windows load or freeze — durable Electron memory/event-loop + source diagnostics now exported; root bottleneck unproven. Need owner diagnostic and Task Manager CPU/RAM/GPU capture. Origin of elevated-rights prompt still unproven.
4. #54 Big City Life sudden mid-track volume dip — W54 records signed gain-variant URL selected/missing, native volume drop and source-left. This is **diagnostic evidence, not an acoustic fix**.
5. #56 admin gain — Windows private offline sidecar server stage/restore passed; owner seek/Next/crossfade/volume/headroom proof pending, no changes to extension originals.
6. #57 signed 403→206 hiss/pop — W103 now gives 150 ms post-prime CDP confirmation chance before reload; approved decoder already playing cancels pending reload only. No proof means bounded reload proceeds. CI green, owner acoustic test pending. Do not force a production 403.
7. #58 «Моя волна» and other original tracks pop under VPN change — original/unknown no-reload guards CI green, acoustic test pending.

**Other open work:** W121 now blocks duplicate Start clicks while the first host/entitlement check is pending. The broader first/second/third launch, reboot, tray and autostart behavior still needs grouped owner-PC acceptance. W120 keeps diagnostics useful after transient state failure and adds a privacy-safe CPU incident; owner diagnostic export after disconnect still needs acceptance. Initial popup, false outdated-module message and W87/W88 default tray autorun are implemented in code; runtime acceptance remains open. Yandex release detection uses the 15-minute catalog refresh and the app's existing refresh path; do not weaken the cadence or CDP recovery without objective profiling. W122 supplies the Supervisor READY launcher and W123 makes signed no-update polling possible, but the stable update coordinator and MainWindow callsite are still missing. W101 signed automatic in-app stable update and safe rollback remain **not implemented**; current updater is manual/staff only.

**Next work order:** after current audio blockers and one owner-accepted integrated Windows build, provision the schema-2 release trust pins/feed and connect the already bundled Supervisor through a trusted same-user launch callsite; prove real signed crash recovery and stable automatic updates per W101. Verify W104 bridge/start failure recheck on owner's PC; run CI after changes; make **one** coherent final Windows EXE + ZIP and link it only when successfully built and independently verified. Do not send partial TEST installers or ask for new secrets/accounts/emails. The user expects big completed chunks and a short status, not endless theory. Mass release only after owner QA. No final package has been delivered and nothing was installed on user's PC from this handoff.

**Owner-side proof required:** VPN A→B reconnect, «Ты» audible replacement, Big City Life full-song loudness, natural 403→206 without hiss, «Моя волна» originals on VPN switch, Brave/Windows resource usage, and startup/reboot behavior. Never claim a real playback bug fixed by CI alone.

## W114a continuation — 14 November 2026

- Latest code fix: `StableUpdateRollbackJournal.VerifiedPreviousInstallerCore` now passes `PreviousSupervisorSha256` into the reconstructed `VerifiedRelease`. Before this, the signed rollback package was re-verified without its required fourth payload hash and would be rejected by W114 stager validation.
- W15 synthetic verifier now asserts all four payload hashes (application, native host, renderer, supervisor) on each verified package, so this omission is covered by regression tests.
- Exact pre-change backup: `backup/windows-main-pre-w114-rollback-supervisor-hash-20261114` @ `ffb983ec97982263e4559b3d7e7aad120976ad76`.
- Fix commits: `54219d43e550e4c5ea42eb2fa511264a4255ee0e` (code), `a7c8474a9dadb55c55261bffe6e6141aabac1146` (test).
- Last verified HEAD before W114a: `ffb983ec97982263e4559b3d7e7aad120976ad76`; final CI for W114a must be checked against the newest `main` HEAD.
- No production signer pin/key/feed is provisioned. Supervisor launch callsite is still absent. Do not run Hostinger QA publish or claim automatic updates are live.

- Additional W114a hardening: schema-2 `ReadRecord` now rejects missing/invalid previous or target Supervisor hashes at journal-read time, matching the engine and stager fail-closed requirements. Exact pre-change backup: `backup/windows-main-pre-w114a-journal-supervisor-validation-20261114` @ `fd18154e6ffa68325510b1e90315c7020741c6d2`. Code commit: `59a84955308ec73f3a4e3b8dad1282002eb4f3ed`.

## W152 — VPN A→B source-handoff protection (15 November 2026)

- **Task 2 engineering implementation and CI are complete** at final code HEAD `59894be3fe88de0dfecd9d92c9164b509d0c7859` on `main`. Initial W152 implementation commit: `341c97cd49cde010bba7a3821c7e3c4f2d89c74a`; follow-up fixes/tests: `6e5e46d9b8b22faafebb64f7731a61be82a8ebf8`, `62d319f54b0b1a5b3a3399bf0958187c3227a29f`, `447c5e8f42b794d8db9d2cc763509f6bb6dabe83`, `501eed823d36f562cb1580171136cbdd5cd00670`, `536a8922206fcd8e8b79f01852ad2563904eb2ac`, `59894be3fe88de0dfecd9d92c9164b509d0c7859`.
- Exact pre-Task-2 rollback point: `backup/windows-main-pre-task2-vpn-audio-20261115` @ `43d0b551d210e08d1d5d05a32eaf6634a400c19e`. Exact pre-Task-3 backup now created: `backup/windows-main-pre-task3-autostart-20261115` @ `59894be3fe88de0dfecd9d92c9164b509d0c7859`.
- **Code-level cause addressed:** a transient entitlement failure during a VPN route switch could be treated like a manual stop: the renderer reloaded a mapped current song back to Yandex original, then re-enabled CELIKOM and reloaded it again to the replacement. This created two unnecessary source handoffs close together. The code fix prevents those redundant handoffs when the exact current signed decoder is still playing; it does not claim that every possible audible pop from the OS/network path has been disproved.
- MainWindow marks a route transition in the authenticated local bridge state. The marker survives a transient fail-closed suspension and re-enable until the resumed native host sends its first accepted heartbeat. A newer route signal invalidates an older heartbeat handshake, so a stale heartbeat cannot release the newest route hold.
- Native Host preserves its decoder-player witness only for the same signed-in API origin during this transient route recovery. It advertises `preserveCurrentSource` only when the exact current track still has a signed CELIKOM decoder URL, PLAYING state, and no observed decoder pipeline error. The track ID is carried separately and must match the renderer's current ID; My Wave/Next cannot inherit the previous song's witness.
- Renderer holds the already-loaded signed source while entitlement is revalidated, does not reload it to original merely because the bridge is temporarily disabled, and pauses transient/expired/source-left recovery timers. Deferred current-track candidates are retained rather than discarded during the route hold. When the route is validated, recovery resumes with the original bounded retry cadence. If the decoder survived, no source reload is performed; if it did not, only one fresh current-track source refresh is performed. Manual Stop, logout, authoritative entitlement denial and API-origin change still cancel/clear the hold and retain their existing behavior.
- **Regression coverage:** W23/W22/W60 original-source, VPN, 403 and audio suite SUCCESS, including original track during VPN transition, live replacement source preservation, one-refresh fallback when decoder is lost, My Wave track identity, paused recovery/deferred candidate retention, and latest-route heartbeat handshake. W15 entitlement/login/native-state suite SUCCESS, including repeated route signal invalidation. GUI warning-as-error compile SUCCESS; supervisor compile and existing W110/W114/W117/W128 checks SUCCESS.
- **CI:** Windows integration run `43708423469` SUCCESS; main CI run `43708423447` SUCCESS. No EXE, ZIP or intermediate installer was built.
- **Owner-PC acceptance remains pending:** this is not yet an audible acceptance claim. The consolidated Task 4 check must cover VPN A→B with original tracks, active replacements and My Wave; verify the fast reconnect remains fast; then test Yandex crossfade after recovery. Do not ask the owner to run intermediate builds now.
- **Next task: W150 Task 3 only — audit first-launch autostart ON by default, sticky intentional OFF, and no automatic Yandex launch or elevation.** W150 already says these behaviors appear present in code review: verify with existing code/tests first and change only a demonstrated gap. Do not start Task 4, updater, old Issues or installers before Task 3 is complete.

