# W38 — native Windows Yandex Chromium exact CORS-error enum
Date: 2026-11-09. **Read-only, CI-only; no release and no owner work.**

## Evidence and preserved checkpoints
- W36 SUCCESS https://github.com/manufact-test/nomusic/actions/runs/42693758356: approved original native renderer `NATIVE_FETCH_BLOCKED_TYPEERROR_CSP_NONE`; trusted Electron main `MAIN_HTTP_403` + `MAIN_ACAO_NATIVE`; original signed vendor EXE/ASAR fully restored.
- W37 SUCCESS https://github.com/manufact-test/nomusic/actions/runs/42694895709: passive CDP `CDP_REQUEST_SEEN` and `CDP_LOAD_FAILED_CORS` for the deliberately **invalid-token** test request in the genuine native Yandex renderer. This proves the origin of *that probe's* failure is a browser CORS decision, not directly a Yandex decoder failure or a native CSP decision. CDP debugger detached and vendor bytes restored exactly.
- W37 accepted backup `backup/windows-w37-native-cdp-cors-confirmed-20261109` points to `f1e33c534d7aa1f5e7ea7c1ae7aa089945d14927`. Previous W36 backup also exists.
- Owner Windows CELIKOM 0.24.4 and matching module 0.24.4 untouched. No new installer, site, production, Android/Test.50 or account modification.

## Follow-up method
- W38 adds the **exact public Chromium CDP Network.CorsError enum** for this one fixed invalid-token request to sanitized CI logs, strictly allowlisting enum names. `failedParameter`, arbitrary URLs, request/response headers, cookies, account and audio data are never exported.
- Official enum source: https://github.com/ChromeDevTools/devtools-protocol/blob/master/pdl/domains/Network.pdl
- Identify whether error is invalid status, missing/mismatched Allow-Origin, preflight headers/methods, private network or scheme. `CORS` alone is still too broad to authorize a backend change.
- CI workflow requires both real original native renderer and `CDP_CORS_ENUM_*` category plus byte-for-byte vendor restoration. If no typed reason, fail **inconclusive** rather than invent a fix.

## W38 CI
https://github.com/manufact-test/nomusic/actions/runs/42695804499
**Final W38 CI #42695804499: SUCCESS.** `W33_RT_CDP_CORS_ENUM_MISSING_ALLOW_ORIGIN_HEADER` in genuine `NATIVE` Yandex renderer, `CDP_LOAD_FAILED_CORS`, `MAIN_HTTP_403` + `MAIN_ACAO_NATIVE`. Original vendor EXE+ASAR restored byte-identically; signature valid. This verifies missing browser-visible ACAO for a deliberately invalid-token request. It does NOT verify actual signed 206 media or audible substitution.

Exact pre-W39 backup: `backup/windows-w38-native-cors-missing-acao-confirmed-20261109` at `ec7b0ad7a264612728fd4f1af99d5bdc18c58bfc`.

W39 uses *passive* CDP-only categorization of the real renderer's outgoing Origin and returned ACAO/status. No actual header values or credentials are copied to logs. See `docs/windows/W39-NATIVE-ORIGIN-CLASSIFICATION-20261109.md`.

## Next
If W38 identifies an actionable specific CORS mismatch, isolate and test a minimal CORS response adjustment **without altering unrelated API, authorization, Yandex CSP/webSecurity, original native player or desktop installation**. Re-verify invalid token (403 remains denied), preflight and authorized approved 206/Range where permitted; never treat an invalid-token negative probe as real audio proof. Once signed media is confirmed, inspect the genuine Windows source schema, key/iv, codec/transport and decoder before any installation.
