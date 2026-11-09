# W39 — native Yandex renderer request Origin / ACAO categories (CI-only)
Date: 2026-11-09. No owner update, native player/codec/transport/production changes.

## Strictly verified
- CELIKOM Windows owner remains AppVersion=0.24.4.0 and NativeModuleVersion=0.24.4, audio stops when approved substitution is selected (4/4 AUDIO_PROBE_FETCH_BLOCKED in owner TXT).
- W36 genuine-Yandex native renderer observed FETCH_BLOCKED_TYPEERROR, Electron main invalid-token GET 403/ACAO_NATIVE. https://github.com/manufact-test/nomusic/actions/runs/42693758356 — SUCCESS.
- W37 passive Chromium Network CDP on true native renderer observed CDP_LOAD_FAILED_CORS. https://github.com/manufact-test/nomusic/actions/runs/42694895709 — SUCCESS.
- W38 fixed Chromium CorsError enum is **MissingAllowOriginHeader** for an intentionally invalid-token request. https://github.com/manufact-test/nomusic/actions/runs/42695804499 — SUCCESS. Original vendor EXE/ASAR and signature verified restored at each passed run. This is NOT confirmation of actual signed 206 or decoder/player behavior.
- W38 protected backup: backup/windows-w38-native-cors-missing-acao-confirmed-20261109 at ec7b0ad7a264612728fd4f1af99d5bdc18c58bfc.

## W39 scope
- Passive CDP Network request and extra-info events for only the fixed invalid-token URL on a disposable signed Yandex runtime. Categorize the outgoing Origin (native/null/Yandex-host/other/absent) and returned Access-Control-Allow-Origin (same allowlist), HTTP status and CORS error. NEVER expose raw values, query strings, keys, failedParameter, headers, response body, cookies, account information, music or third-party traffic.
- `windows-companion/w23/w33-runtime-probe.cjs` gate `CELIKOM_W39_CORS_HEADERS=1`; server/native host/renderer release logic unchanged; passive debugger detached after bounded observation.
- W39 unit test asserts typed CORS classification and fails if sensitive strings leak to recorded markers. Test is included in native CI.
- W39 workflow https://github.com/manufact-test/nomusic/actions/runs/42700903189 — check final verdict. Requires approved native render, main HTTP control, CORS category and original EXE/ASAR restoration. No owner action now.

## Decision gate
- Only after exact native Origin and actual server header behavior are corroborated, propose a minimal allowlist-safe corrective change if needed. Do not disable webSecurity/CSP, enable global wildcard CORS, create a proxy/player, alter key/iv/codec speculatively, or ship a Windows installer.
- For real playback verify authorized 206/Range and original Windows file-info/decoder metadata, then audible owner Play/Pause/Seek/Next. A 403/CORS probe cannot prove real stream playback.
