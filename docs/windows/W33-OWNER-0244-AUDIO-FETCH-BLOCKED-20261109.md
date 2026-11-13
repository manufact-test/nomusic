# W33 — correct owner 0.24.4 diagnostic, renderer audio fetch failure (2026-11-09)

## What owner actually installed
Owner uploaded `3.txt` generated 2026-11-09T19:00:04Z. Header:
- AppVersion=0.24.4.0
- NativeModuleVersion=0.24.4
- NativeModuleMatchesApp=true
- NativeIntegration=ACTIVE, BridgeStarted=true, Enabled=true, SignedIn=true
- CodeBaseline=W32_EASY_UPDATE_NATIVE_IDENTITY
Owner's upgrade workflow now demonstrably correct; no more installer reinstall is needed for this diagnosis.

## Latest session only (18:59:24–18:59:53Z)
Note 3.txt contains hundreds of historical events from W28/W29/W31; DO NOT mistake old SOURCE_SYNTHETIC_RESPONSE logs at 14:40 for events at 18:59.
- 4 AUDIO_PROBE_STARTED and **4 AUDIO_PROBE_FETCH_BLOCKED**: tracks 42498653, 85025192, 78608850, 107389859.
- Zero AUDIO_PROBE_HTTP_PARTIAL, HTTP_FULL, HTTP_FORBIDDEN, MIME_*, BYTES_*.
- Zero AUDIO_CSP_BLOCKED events. Absence does NOT exclude CSP: generic TypeError in Fetch can be CSP, CORS, redirect or network; not all CSP events reach our listener.
- Yandex native resource hook active, RESOLVE_APPROVED/GRANT_DELIVERED/SOURCE_MAPPED. SOURCE_MAPPED on at least 42498653, 85025192, 78608850; 107389859 grant was probed but audio mapping was not observed within this latest window. Ordinary track 36892169 SOURCE_ORIGINAL.
- MEDIA_REQUEST_SEEN followed by MEDIA_HTTP_UNVERIFIED, not proof of playback/valid signed audio.
- Owner earlier reported instant pause on all approved tracks; this file has no direct media pause/decoder status (native player may use WebAudio).

## Independent read-only network/CSP CI
- [W33 server CORS and public CSP run #42679883888](https://github.com/manufact-test/nomusic/actions/runs/42679883888) SUCCESS. Live OPTIONS on numeric audio path: opaque Origin null, native musicapplication://desktop, HTTPS desktop.app.music.yandex.net, browser music.yandex.ru all 204 with correct ACAO and Range allowed. Invalid token GET from opaque origin returned 403 with ACAO=null (EXPECTED); no redirect in denied request. **This does not validate an actual authorized signed audio URL or owner network.**
- [W33 follow redirects public CSP run #42680166341](https://github.com/manufact-test/nomusic/actions/runs/42680166341) SUCCESS. Public https://music.yandex.ru/ and https://next.music.yandex.ru/ CSP headers: connect-src/media-src/default-src do NOT explicitly allow darkred-camel-588676.hostingersite.com or broad HTTPS wildcard. This is strong evidence that the web renderer rejects private-host music data under its CSP. BUT precise native musicapplication://desktop content CSP could not be read (public desktop.app.music.yandex.net redirects to 404 without signed context); **do not claim confirmed native CSP failure**.
- Electron security guidance: NEVER globally disable webSecurity or relax the Yandex app's CSP for arbitrary origins just to force the source. Safer design needs a verified authorized audio transport boundary, scoped to signed CELIKOM media, that preserves original player and account and does not leak URLs/tokens.

## Status and recommended next action
- Actual app installation/version problem is resolved in 0.24.4.
- Main audio failure is now in browser-context external signed audio fetch **or source consumption path**, not in Yandex resource selection. Backend CORS alone did not solve.
- Prioritize a **disposable signed-original Yandex CI runtime** (without owner credentials) that sends a deliberately invalid token request from inside the native renderer and checks whether HTTP 403 is observable versus a CSP violation / FETCH_BLOCKED. Compare with a read-only trusted Electron main process request to same URL. This can be done without owner reinstall and without real account/audio.
- Only after identifying the rejection layer implement a scoped, signed-media transport compatible with the original Yandex player, keeping CSP/webSecurity intact. Independently verify signed media 206 / mime / bytes, then decoder, pause, seek, queue in the owner's Yandex.
- No code was changed in production audio, server, Windows installer or Android in W33. Current owner app 0.24.4 stays installed. Do not deliver another ZIP on the strength of these diagnostics alone.

## Disposable genuine Yandex renderer research outcome
- A CI-only *fixed invalid-token* diagnostic was appended to the temporary host ONLY on a disposable Windows runner; owner installer and release code not modified.
- Normal signed real-Yandex native smoke #42682821206: SUCCESS, the genuine native host/renderer loaded and the original vendor EXE/ASAR bytes and signature restored.
- The special runtime probe #42682820621 was INCONCLUSIVE (job conclusion failure): it logged W33_RT_BOOTSTRAP_ON (CI appendix really executed in Electron main), but NO renderer-level W33_RT_FETCH result or CSP violation in the probe's 19-second observation window. The existing host itself DID see APPROVED_VIEW, RENDERER_INJECTED, RESOURCE_ATTACHED, and original signed bytes were restored. This is a CI instrumentation/timing gap, NOT evidence that native CORS works or fails.
- The special probe also failed earlier in CI due corrected test-only PowerShell script mistakes. Treat only actual read-only backend/CSP CI #42679883888 and #42680166341 as completed usable connectivity evidence.
- Next research: attach fixed invalid-token renderer fetch probe at actual approved-view or dom-ready event (rather than short polling window), within disposable signed original; compare main process HTTP 403 with renderer status. Never assume web CSP equals musicapplication://desktop CSP.
- No additional user installation needed. Do not change webSecurity, disable CSP globally, replace the original Yandex queue, or declare sound fixed.
