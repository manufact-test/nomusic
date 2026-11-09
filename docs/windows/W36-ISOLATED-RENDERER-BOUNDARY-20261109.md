# W36 — CELIKOM Windows: isolated genuine-renderer boundary probe
Date: 2026-11-09. **CI-only investigation; not an audio repair or owner update.**

## Locked baseline
- Windows working branch: `experiment/windows-companion-integration-20261108`, pre-change SHA `d999ac40ccc80c21f82ce7c5014ec6976a4cbb43`.
- Independent pre-change backup: `backup/windows-w36-pre-renderer-boundary-fix-20261109` at `d999ac40ccc80c21f82ce7c5014ec6976a4cbb43`.
- The owner retains CELIKOM Windows `0.24.4` and its matching Yandex native module; **nothing was reinstalled**. Android, extension, backend, public website and production were not changed.
- Previous owner `3.txt`: 4 x `AUDIO_PROBE_FETCH_BLOCKED` for approved sources, while ordinary tracks played. No true signed-audio HTTP status, decoder or audible-substitution proof.
- Prior CI-only W33 #42682820621 logged `W33_RT_BOOTSTRAP_ON`, but no actual renderer result; it was inconclusive. Successful vendor restore was independently observed in prior native CI.

## Diagnosis and narrow implementation
- W33 polled only 19 seconds (the standard CI host smoke observed the app for 20 seconds); a genuine renderer may not have been ready within that period.
- It marked a view checked before `executeJavaScript` succeeded. A navigation or load could permanently lose the result.
- New `windows-companion/w23/w33-runtime-probe.cjs` listens to approved genuine Yandex `web-contents-created`/DOM readiness and scans as fallback for a bounded 70 seconds, with per-view retry, de-duplication and timeout.
- From the original Windows Yandex renderer, makes **only one hardcoded deliberately invalid-token Range fetch** to the CELIKOM numeric audio endpoint. Separately makes the same invalid-token GET from trusted Electron main using Node HTTPS. Records **only categorical outcomes**: 403, 2xx, redirect, error, timeout, CSP directive category, origin class; no request URL, tokens, response body, Yandex data or audio.
- `w23-host-smoke.ps1` now observes 80 seconds **only** with `CELIKOM_W33_RUNTIME_PROBE=1`; ordinary smoke keeps 20 seconds.
- The existing genuine-Yandex CI restores the original vendor EXE/ASAR and verifies original bytes and signature. No permanent production or owner's machine change.
- Added four regression tests for DOM-ready, scan fallback, origin allowlist and evaluation retry; integrated them into the W36 workflow.
- No change to `toDownloadInfo`, actual Yandex file-info schema, player clock, Pause/Seek/Next, CSP/webSecurity, installer, keys or production API.

## Verification and interpretation
- New isolated workflow: https://github.com/manufact-test/nomusic/actions/runs/42691438851
- **W36 initial run #42691438851: FAIL/inconclusive for renderer.** Four probe unit tests passed; genuine Windows Yandex host was loaded/injected and native state reached; the trusted Electron main invalid-token request returned `MAIN_HTTP_403` with `MAIN_ACAO_NATIVE`. The probe returned `NO_APPROVED_RENDERER_OBSERVED` and `NO_RENDERER_RESULT_OBSERVED` despite the genuine host separately logging `APPROVED_VIEW`, `RENDERER_INJECTED`, `RESOURCE_ATTACHED`. **Do NOT infer renderer CSP/CORS from missing probe.** Native CI report: `originalBytesRestored=true`, `originalSignatureRestored=true`, `error=""`; workflow failed only on `W36_NO_APPROVED_RENDERER_FETCH_RESULT`.
- **Follow-up run #42692435777: FAIL gate, but real boundary event captured.** Trusted main got `MAIN_HTTP_403` and `MAIN_ACAO_NATIVE`. A genuine approved host view was found (`APPROVED_RENDERER_FOUND`, `VIEW_HOST_DESKTOP`); its fetch produced `OTHER_FETCH_BLOCKED_TYPEERROR_CSP_NONE`. `OTHER` is an incompletely classified renderer location, NOT proof of actual native `musicapplication:` CSP. Need identify native/web realm category without logging URL. `VIEW_LIST_EMPTY` also occurred on some polls (not necessarily an app error). Still no valid signed 206, decoder or audible proof.
- **Follow-up direct host-gate correction:** the disposable CI-built host now invokes the runtime probe *after the existing host's approved-view gate*, preventing a second lookup race. Source owner host and installed 0.24.4 unchanged. Run #42692983593 (pending at this update).
- `MAIN_HTTP_403` proves only the invalid URL is reachable to trusted main; never implies an authorized signed 206.
- `NATIVE_HTTP_403_VISIBLE` indicates a denied endpoint response is visible from native renderer under current policy, not that playback or codec compatibility works.
- `NATIVE_FETCH_BLOCKED_TYPEERROR_CSP_CONNECT_SRC` supports an actual native renderer CSP block; `FETCH_BLOCKED` without a CSP event cannot distinguish CSP, CORS, proxy or redirect.
- `NO_RENDERER_RESULT_OBSERVED` or CI failure is instrumentation inconclusive; never interpret as server CSP or decoder proof.
- Passing CI never proves audible playback. Until controlled signed audio fetch/Range and true native audio are confirmed, **do not issue any installer to owner**.

## Next
1. Read the final W36 report and logs (categorical only), then identify if the network gate is CSP/CORS/redirect/native fetch; if inconclusive, refine CI probe without touching owner.
2. ONLY after transport confirmed, inspect the real Windows `getFileInfo` source descriptor (presence flags only), codec/transport/key/iv and native decoder expectations. Current Windows adapter deletes key/iv and rewrites codec/transport/gain; a plausible separate risk, not an established cause.
3. Design a narrowly scoped authenticated signed-media path if needed; do not disable Yandex security globally or invent an independent player.
4. Accept audio only after real owner-approved substituted track with native play, pause, seek, next and first join.
