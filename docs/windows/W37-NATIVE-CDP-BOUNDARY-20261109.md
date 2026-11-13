# W37 — passive Chromium network-failure classification in genuine Windows Yandex
Date: 2026-11-09. **Diagnostic experiment only. No owner binary/update released.**

## Proven baseline and backup
- W36 native CI SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/42693758356
- Exact observed outcomes in original Yandex approved native renderer: `W33_RT_NATIVE_FETCH_BLOCKED_TYPEERROR_CSP_NONE`, `W33_RT_REALM_APPROVED`. Trusted Electron main with **same deliberately invalid-token URL** got `W33_RT_MAIN_HTTP_403`, `W33_RT_MAIN_ACAO_NATIVE`.
- W36 original vendor EXE/ASAR were restored byte-identically and signed; original app and native module version `0.24.4` remain installed on owner's Windows 10.
- Exact W36 pre-W37 backup: `backup/windows-w36-native-renderer-fetch-blocked-ci-pass-20261109` at `474290941f2d4ea10db3a75adfc07683669b1515`.
- W36 proved renderer fetch fails, **not whether CSP, CORS or network specifically causes the TypeError**. It also did not test any signed 206, actual media decoder, audio, Pause/Seek/Next.

## W37 only change
- In `windows-companion/w23/w33-runtime-probe.cjs`, gated by environment variable `CELIKOM_W37_CDP_PROBE=1` **in disposable GitHub Windows CI only**, attach read-only Chromium DevTools Protocol Network and Log observers to the same host-approved native Yandex webContents.
- Observe ONLY hardcoded invalid-token test request ID with Network.requestWillBeSent/responseReceived/loadingFailed. Redact everything to fixed categorical markers such as `CDP_REQUEST_SEEN`, `CDP_LOAD_FAILED_CSP`, `CDP_LOAD_FAILED_CORS`, `CDP_HTTP_403`, `CDP_CSP_CONSOLE` or `CDP_REQUEST_NOT_SEEN`.
- Never export URL, query, cookies, headers, body, keys, Yandex account state, or unrelated events. No network interception, security bypass, forced player control, stream or new decoder.
- CDP is detached after the probe (bounded) and remains disabled outside this isolated CI flag.
- Workflow now requires a classified CDP observation as well as approved native renderer result, main HTTP control and exact vendor restoration. **A missing/unsupported CDP remains an honest inconclusive FAIL.**

## CI
- W37 diagnostic workflow: https://github.com/manufact-test/nomusic/actions/runs/42694895709
- **W37 CI #42694895709: SUCCESS, passive network evidence.** `CDP_NETWORK_ENABLED`, `CDP_REQUEST_SEEN`, `CDP_LOAD_FAILED_CORS`, `NATIVE_FETCH_BLOCKED_TYPEERROR_CSP_NONE`, `REALM_APPROVED`; trusted main `MAIN_HTTP_403`, `MAIN_ACAO_NATIVE`. The original EXE/ASAR were restored byte-identically and signature validated, `error=""`. The deliberately invalid-token native renderer request is blocked by Chromium CORS. **This does not yet prove the same CORS branch for real signed 206 audio or establish native playback.**
- W37 exact accepted backup `backup/windows-w37-native-cdp-cors-confirmed-20261109` at `f1e33c534d7aa1f5e7ea7c1ae7aa089945d14927`.
- W38 disposable follow-up `#42695804499` uses the public DevTools `Network.CorsError` enum (fixed allowlist) to identify **which** CORS check fails, with no raw URL/header/`failedParameter` logging. Pending final result.

## Next gate
- If CDP explicitly reports CSP, decide a narrowly scoped authenticated audio delivery boundary for rights-approved CELIKOM media preserving Yandex webSecurity and its single native player.
- If CDP reports CORS/HTTP/Network or remains inconclusive, investigate only that layer. No global CSP relaxation, open proxy, speculative key/IV edits, or owner installer.
- After real signed audio 206/Range confirmed, audit the original Windows file-info codec/transport/key/iv consumer, before native playback acceptance tests.
