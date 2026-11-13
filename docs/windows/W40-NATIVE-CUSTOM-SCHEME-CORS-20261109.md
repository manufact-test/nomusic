# W40 — confirmed native custom-scheme Origin and missing CORS allow header
Date: 2026-11-09. **Research-only. No customer app, backend, audio, or original native decoder changes.**

## Verified evidence
- Owner CELIKOM 0.24.4.0 + native module 0.24.4, originals play, rights-approved substitutions immediately stop. Four owner audio probes failed at fetch.
- W36 https://github.com/manufact-test/nomusic/actions/runs/42693758356: original genuine Yandex native renderer `FETCH_BLOCKED_TYPEERROR`; trusted Electron main sees HTTP 403 for hardcoded deliberately invalid token.
- W37 https://github.com/manufact-test/nomusic/actions/runs/42694895709: passive CDP `LOAD_FAILED_CORS`.
- W38 https://github.com/manufact-test/nomusic/actions/runs/42695804499: `CorsError: MissingAllowOriginHeader`.
- W39 https://github.com/manufact-test/nomusic/actions/runs/42700805271 and final tests https://github.com/manufact-test/nomusic/actions/runs/42701221204: genuine renderer request `WIRE_REQUEST_ORIGIN_UNLISTED_OTHER`, server response HTTP 403 with `WIRE_RESPONSE_ACAO_ABSENT`. Trusted Electron main HTTP 403 **does** include `ACAO_NATIVE`; native-request headers differ from main.
- **W40 https://github.com/manufact-test/nomusic/actions/runs/42701895118: SUCCESS.** The original Yandex native renderer's actual on-wire `Origin` has a **custom scheme**, category `CDP_WIRE_REQUEST_ORIGIN_CUSTOM_SCHEME`, rather than approved `musicapplication://desktop`, `null`, HTTPS-Yandex, localhost, extension, file or Chromium internal schemes. Native HTTP response 403 / ACAO absent; CDP CORS MissingAllowOriginHeader. No actual authorized token or audio used.
- Every successful genuine-runner test restored official EXE/ASAR bytes and genuine vendor signature; W40 confirms `originalBytesRestored=true`, `originalSignatureRestored=true`, `error=""`.
- W40 exact passed-source backup `backup/windows-w40-custom-origin-cors-ci-confirmed-20261109` at `8d7fe03eb042d906c427a043cdf282af36a06851`. Earlier W39 backup at `805a6142fb0055311b61609315fa0ed99caf72b8`.

## What is and is not proven
A CORS mismatch is now confirmed for **only the hardcoded invalid-token diagnostic GET** in genuine Windows Yandex. Native browser sends a custom-scheme Origin for which the current server returns no ACAO. We still need a **specific, authenticated, stable, legitimate Yandex origin and verified server response contract**, not wildcard/custom-scheme broad grants.
Real grant signed GET/Range 206, first audio bytes, native original Windows file-info codec/key/iv/transport, decoder, audible substitute, Pause/Seek/Next have not been confirmed. Do not call owner fix completed.

## Safe next gate
1. In disposable CI, identify *only* the static native origin scheme/host contract against the genuine signed Yandex version, without logging arbitrary URL values, owner data, tokens or auth headers.
2. If it is stable and provably trusted, write a narrowly scoped staging-only CORS contract for numeric signed audio GET/HEAD/OPTIONS. Preserve 403 for invalid tokens and deny unrelated API/auth/admin and untrusted origins. Never broaden to all custom schemes.
3. Verify actual signed/authorized audio 206 + Range with explicitly approved test asset, then validate the original Windows file-info descriptor semantics and decoder. Do not reinstate key/iv or overwrite codec blindly, and do not disable CSP/webSecurity or add a second player.
4. Require audible original Yandex Pause/Seek/Next before any owner ZIP/EXE release. Owner installation 0.24.4 stays untouched until then.

## No changes outside CI
- Changed only disposable runtime diagnostic, its regression test, workflows and docs. No changes to owner app, audio adapter metadata, Android/Test.50, server/production, site or browser extension.
