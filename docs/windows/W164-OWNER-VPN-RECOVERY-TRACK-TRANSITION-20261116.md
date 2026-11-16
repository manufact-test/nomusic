# W164 — VPN recovery and track-transition polish

Date: 16 November 2026  
Product: CELIKOM Windows only  
Status: **source CI green, W20 internal owner-review package built and verified; owner manual acceptance pending.**

## Source of truth and rollback

- Repository: `manufact-test/nomusic`
- Working branch: `main`
- Code checkpoint: `2b7fb2d3627c27c1ec9052e49b7abdb49b87429e`
- W20 request/docs commit: `98bb24a3081e616e8a4767323bbc685cf1b2ecde` (request file only; no code change)
- Exact pre-W164 backup: `backup/windows-main-pre-w164-vpn-route-debounce-track-ui-20261116` @ `b5538b6bdbb62eeeaef74c57e10d0fe5a075af7a`
- App: **0.24.46.0**
- Native module: **0.24.31**
- Previous owner-installed version shown in supplied screenshot: **0.24.45.0**

Code commits:
- `167cda990f2ddb585731093b5d2e0d381e63e7e9` — route recovery, track transition and version bump.
- `5a395c7b0eed1f1718dc2a500cbe5163a8c3e621` — connection indicator follows live native heartbeat.
- `2b7fb2d3627c27c1ec9052e49b7abdb49b87429e` — bound previous-title handoff to the metadata grace period.

## Owner findings

1. A short VPN interruption lasts about 1–2 seconds from the owner's perspective, but the UI can keep saying that server connection is recovering for 20–30 seconds while the current audio source remains held.
2. The compact header word **«Связь»** changes vertical position and color during rapid recovery transitions.
3. On Next, the old title disappears and a transient text appears before the next title. The owner could not read it because it flashes too quickly.

## Diagnostic and code findings

The supplied W54 capture contains at least:
- 100 `ACTIVE_ENTITLEMENT_ROUTE_CHANGED` records;
- 27 `ACTIVE_ENTITLEMENT_TIMEOUT` records;
- 33 `ACTIVE_ENTITLEMENT_NETWORK_ERROR` records;
- 37 `ACTIVE_ENTITLEMENT_NETWORK_SUSPENDED` records;
- 30 `NATIVE_ROUTE_RECOVERY_SOURCE_HELD` records.

The source is being held during route recovery, consistent with the owner's report that music continues. The previous entitlement logic kept a 30-second fast-route window with a 3-second request deadline and did not clear the route hint after a successful authenticated response. Repeated Windows adapter notifications could therefore keep cancelling/restarting checks and make subsequent requests time out unnecessarily.

The track-transition text came from two UI fallbacks:
- a raw `Track ID …` placeholder when a new ID arrived before its title;
- `Проверяем версию песни CELIKOM…` while the per-track presence request was still in flight.

The diagnostic reports `NativeDecoderUrlPropertyObserved=false` and `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`. A source-held event or mapping does not independently prove which decoder source is audible.

## W164 implementation

### VPN / entitlement recovery

- Native source-hold markers are coalesced across an **8-second route burst**; every route event still advances the epoch, so the final event owns the recheck.
- The final entitlement recheck waits for a **3-second quiet period** after the last Windows address-change event.
- The immediate route-recovery request uses a **5-second deadline** and an **8-second fast-route window**, instead of a 3-second deadline retained for 30 seconds.
- A fresh authenticated entitlement response clears the route hint. Normal healthy polling returns to 15 seconds; suspended retries remain bounded and read-only.
- No offline entitlement, cached authorization bypass, server authority change or entitlement relaxation. A real server denial/network failure remains fail-closed.

### Connection indicator

- The header label is fixed to **«Связь»**, with fixed size, ellipsis enabled and vertical middle alignment. It no longer changes its text length/baseline during recovery.
- Its color follows a fresh native-host heartbeat. A pending server-route recheck alone no longer turns a still-live native host gray.
- If the bridge is genuinely suspended and the heartbeat is no longer fresh, gray remains correct; detailed recovery information is shown separately below.
- The exact active-replacement color gate is unchanged.

### Track transition

- When a new track ID arrives before its title, the previous visible title/artist is retained for at most **2.5 seconds** while metadata catches up.
- The previous title is not retained after that bounded handoff; if new metadata never arrives, the row becomes blank rather than showing a technical ID.
- Raw `Track ID …` fallback was removed.
- The transient `Проверяем версию песни CELIKOM…` copy is hidden while the presence request is pending. Only a returned availability/error state is displayed.
- The current track ID still drives the presence request. No audio, queue, playback, decoder or source-resolution code changed.

### Scope boundaries

No W23 native host/renderer, audio engine, Yandex files, Android, browser extension, backend/API/database, entitlement authority or updater architecture changes. No production deployment or signing.

## Verification

On the code checkpoint:
- Main CI run [43878114276](https://github.com/manufact-test/nomusic/actions/runs/43878114276) — **SUCCESS**.
- Windows integration CI run [43878114256](https://github.com/manufact-test/nomusic/actions/runs/43878114256) — **SUCCESS**.
- W15 entitlement/login/native-state tests and GUI compile with warnings as errors — **SUCCESS**.
- W22/W23/W60 original-source, VPN, 403 and audio regressions — **SUCCESS**.

On the W20 package request commit:
- Main CI run [43878846340](https://github.com/manufact-test/nomusic/actions/runs/43878846340) — **SUCCESS**.
- W20 safe installer staging run [43878846320](https://github.com/manufact-test/nomusic/actions/runs/43878846320) — **SUCCESS**.
- W20 compiled the self-contained app and supervisor, ran W15/native preflight and installer policy checks, validated PE version and anti-downgrade, completed per-user install/upgrade/uninstall smoke, and packaged one EXE plus one ZIP.
- The ZIP contains exactly one root installer. Its EXE is byte-for-byte identical to the standalone EXE. SHA256 values were independently checked against `SHA256SUMS.txt`.

## Internal owner-review package

<badge>Internal unsigned owner-review build</badge>

- Version: **0.24.46.0**
- Native module: **0.24.31**
- Installer: `CELIKOM-W164-VPN-RECOVERY-AND-TRACK-TRANSITION-02446-UNSIGNED.exe`
- EXE SHA256: `451e8614a73bf20a446eeae72625715756c458b077e4274d004f8c7aa62a4054`
- ZIP: `CELIKOM-Windows-0.24.46.zip`
- ZIP SHA256: `5578b2854be1f874c07260fc85097c2a80b1de35ddeebb5c3729222737bdd1d0`
- W20 run: https://github.com/manufact-test/nomusic/actions/runs/43878846320
- Artifact ID: `14231891556`
- Artifact name: `CELIKOM-Windows-internal-stage-98bb24a3081e616e8a4767323bbc685cf1b2ecde`
- Direct artifact: https://github.com/manufact-test/nomusic/actions/runs/43878846320/artifacts/14231891556
- Artifact expires: **26 November 2026, 13:48:22 UTC**.

This is one private unsigned owner-review package only. No production signing, stable feed, Hostinger deployment, customer publication or release.

## Owner manual acceptance still required

Install **0.24.46.0 over 0.24.45.0** and check:

1. Toggle VPN off/on while a track is playing. Music should continue as before; the «Связь» label must stay vertically centered and should not gray merely because a route recheck is pending. A genuine server outage may still show recovery until a fresh authenticated request succeeds.
2. Check that the recovery message clears promptly after server access returns, rather than lingering for 20–30 seconds.
3. Press Next several times. There must be no raw Track ID or transient «Проверяем версию песни CELIKOM…» flash. The old title may remain briefly while the new metadata arrives, then the new title/artist must replace it.
4. Do not force the active full-version label green. It remains green only with exact current decoder-source proof. If the owner hears a CELIKOM version while that label remains gray, collect a fresh W54 diagnostic and investigate the native decoder observer separately.

Do not repeat broad audio/VPN audits unless a real regression appears. Do not claim audible source correctness from CI or the source-held diagnostic alone.
