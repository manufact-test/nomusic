# W95 — CELIKOM WINDOWS 0.24.34 TEST OWNER QA DELIVERY (2026-11-13)

## Exact source, rollback, artifact
- Repo: `manufact-test/nomusic`, work branch `experiment/windows-w95-02434-qa-candidate-20261113`, **exact tested Windows code commit** `4f8b3a72687577c5447d157be156365ab42a86fa`.
- Source rollback **before W95**: `backup/windows-w95-pre-02434-qa-candidate-20261113` @ `80113ff54e0479c0412e51263cd81078b39082e1` (W94). Pre-W96 patch backup `backup/windows-w95-02434-pre-w96-403-guard-20261113` @ `cc35d1fff1e6b60dd98eb1de6ce2b4ab61f67ecb`. W89 **0.24.33** exact source `backup/windows-w89-02433-ci-green-owner-handoff-before-volume-20261113`, installer SHA `414EDBA856A12B25CB3EDE26D136C7F263CFC02FC3448730C7F7D02D60791879`. W88 0.24.32 separate rollback preserved.
- GUI **0.24.34**, native **0.24.27**; same installer AppId, non-admin installation, no bundled Yandex.
- **Final GitHub Windows CI SUCCESS** [43442749658](https://github.com/manufact-test/nomusic/actions/runs/43442749658), artifact ID `14045829754`. Native source renderer build; W15 `W15_NATIVE_CONTRACT_PASS 201`, later ZIP staged W15 PASS 205, W21 crash safety, W24 official vendor pinned install tests, W22/W23 pause/seek/403/volume-source witness, W94 VPN route burst. Installer in-place **W95_02433_TO_02434_INPLACE_DPAPI_AND_NEW_NATIVE_READY_PASS**: old W89 artifact verified by SHA; DPAPI session kept byte-identical & decryptable, both host+renderer updated as intended; vendor installation untouched by installer itself.
- Downloaded artifact locally, ZIP CRC verified and EXE extracted SHA checked. EXE `CELIKOM-Windows-0.24.34-AUDIO-VPN-QA-TEST.exe` size **43,551,775 bytes**, SHA256 **`83CF52CE7808CF03E33FBE461FDFE73C40080545642B29B5F9ED81015DEB1FFE`**. ZIP `CELIKOM-Windows-0.24.34-AUDIO-VPN-QA-TEST.zip` size **43,058,416**, SHA256 `6263CCB6CD6294CF33C17808E4BD1B3EA406F4C49A5955841A35E7B70CBD01D9`.
- Persistent user Library upload SUCCESS for **both files**:
  `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.34-AUDIO-VPN-QA-TEST.exe` (ID `libfile_a4d924edf8f48191a6fa183b41097408`);
  `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.34-AUDIO-VPN-QA-TEST.zip` (ID `libfile_e690d182c16c8191a1c851854ccbebaf`).
- **NOT deployed to owner PC or Hostinger**. Owner's installed version unknown (previously 0.24.32); 0.24.33 TEST wasn't actually listened to by owner. This is **TEST only**, NOT stable/fully fixed.

## What 0.24.34 actually changes
1. W94 VPN: events within 1.4s no longer drop last network-route signal; now debounces final event 750ms and cancels stale GET, requiring real fresh authenticated server entitlement. Verified Windows CI [43440706956](https://github.com/manufact-test/nomusic/actions/runs/43440706956). Owner's 40–50s live VPN reconnection still unverified.
2. W89 source verification: green only with matching current CDP `kUrl` + `kIsPlaying`; mapping-only neutral, bounded one-shot source reload for "Ты" original fallback. Actual audible alternative still unverified.
3. W92 evidence: passive, allowlisted `PLAYER_CURRENT_SOURCE_LEFT_CELIKOM`, `PLAYER_CURRENT_NATIVE_VOLUME_DROP` (only when CDP exposes `kVolume`), `NATIVE_ELECTRON_EVENT_LOOP_STALL`, memory high. CI [43438578606](https://github.com/manufact-test/nomusic/actions/runs/43438578606), no user-facing alarm spam. Need real diagnostic and owner correlation.
4. W96 mitigates redundant 403 reload: if **exact current decoder signed URL already playing** is confirmed, cancel ONLY a *pending* delayed 403 reload (not in-flight). If witness unavailable, previous bounded recovery unchanged; no player controls/queue/position change. CI [43442397134](https://github.com/manufact-test/nomusic/actions/runs/43442397134) success; field hiss still unproven.
5. W90/W91 gain pipeline metadata/profile code present; **IMPORTANT: on current production backend the Windows gain sidecar is NOT active**, because server migration 020 and pre-rendered Big City Life file have **not** been deployed. The 0.24.34 installer alone **does not give Big City Life +11.5 dB yet**. Server-side private staged offline approach thoroughly tested on disposable MariaDB + synthetic MP3 [43440173979](https://github.com/manufact-test/nomusic/actions/runs/43440173979); raw browser source remains untouched. Do not overpromise a gain fix or activate live file before explicit controlled QA/restore.

## Required owner live QA
- Install over present CELIKOM with Yandex closed, manually Start after native update (if needed), no re-login should be necessary. Preserve prior installer rollback.
- Listen to several normal songs including pause, resume, seek, Next, crossfade. For **«Ты» — тринадцать карат** (current reported track id 89285816), confirm ears hear CELIKOM version or original; green status means narrow decoder evidence, not speaker-proof.
- While listening, switch VPN A→VPN B, note real interruption and whether 40–50s problem persists; cannot infer from CI. Server MUST authenticate fresh; no bypass.
- For **«Биг сити лайф» — Триагрутрика** current active Yandex id 40371622, **admin +11.5 dB**, note baseline volume and any sudden mid-track drop. W95 may still sound unboosted because sidecar not deployed. Capture diagnostics at moment if owner has authorized export.
- Watch for hiss after natural 403 recovery, no forced expiry injection into production. If it still occurs, #57 stays open.
- If Brave/system lags, note process CPU/RAM (Yandex, CELIKOM, Brave) and whether native stall code appears. Do not assume cause or request admin privileges.
- If regression, reinstall exact old 0.24.33 or 0.24.32 TEST from Library, and send owner diagnostics. Do not delete account/DPAPI.

Outstanding: #52 audible decoder proof/«Ты», #53 Brave slowdown, #54 sudden Big City Life dip, #56 Windows gain not actually applied until validated sidecar rollout, #57 hiss. No final claim until owner test.
