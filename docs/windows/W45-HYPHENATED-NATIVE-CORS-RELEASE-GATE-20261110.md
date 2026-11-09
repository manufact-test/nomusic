# CELIKOM Windows — W45 exact native CORS hotfix ready, PRODUCTION NOT MODIFIED
Date: 2026-11-10. Working branch: `experiment/windows-companion-integration-20261108`.

## Owner/product contract
Windows CELIKOM 0.24.4.0 and native module 0.24.4 match and remain installed. Ordinary Yandex Music tracks play; rights-approved replacements immediately stop, 4/4 owner probes `AUDIO_PROBE_FETCH_BLOCKED`. No independent second player, no global webSecurity/CSP disable, no metadata/key/IV guess, no unsigned fresh installer. Android/Test.50 untouched.

## Root cause CONFIRMED for the diagnostic fetch
- The actual genuine signed Yandex 5.126.1 native renderer sends the exact on-wire **Origin: music-application://desktop** (hyphenated). The prior backend audio-only allowlist contained **musicapplication://desktop** (missing hyphen).
- W36 #42693758356 genuine renderer fetch TypeError, trusted Electron main returned expected invalid-token 403.
- W37 #42694895709 genuine renderer passive Chromium CDP confirmed CORS failure.
- W38 #42695804499 typed Chromium error `MissingAllowOriginHeader`.
- W39 #42700805271 and final #42701221204 confirmed native wire request had unlisted Origin, 403 without ACAO, main got 403 WITH ACAO.
- W40 #42701895118 `CDP_WIRE_REQUEST_ORIGIN_CUSTOM_SCHEME`.
- **W41 CI #42704012210 SUCCESS:** `CDP_WIRE_SCHEME_MUSIC_APPLICATION`, `CDP_WIRE_HOST_DESKTOP`, `CDP_WIRE_PORT_ABSENT`, native `403` with ACAO absent, trusted main `403` with ACAO present. Original vendor EXE/ASAR restored byte-identically and signature valid.
- All tests used a fixed deliberately **invalid token**; this does not prove actual signed 206/decoder/audible owner replacement.

## Narrow staged candidate
- In working Windows branch **only**, `server/src/Application.php` audio-only exact allowlist gained `music-application://desktop` (retaining old allowed origins). No change to unrelated routes, entitlement, HMAC, session/expiry, MIME, seek, playback, Yandex security settings, production API or owner installation.
- `server/tests/smoke.php` proves allowed GET/HEAD/OPTIONS, signed 200/206 Range, bad bearer stays 403 with ACAO for browser visibility, foreign lookalike origins cannot preflight or read, auth/resolve stay CORS-denied.
- W41/W30 PHP staged-only CI #42704641987 SUCCESS.
- W42 read-only PUBLIC LIVE #42704976449 SUCCESS: correct hyphenated Origin OPTIONS=404/ACAO MISSING; bad-token GET=403/ACAO MISSING; auth OPTIONS=405/ACAO MISSING. The correct fix **is not active on production**.
- W43 read-only live-file compare #42705379376 SUCCESS: active `Application.php` SHA256 `ec7f5d0d87978c823ece2dcfa2e76a021d4e2af09eb4f5c4d5fe52b6ab6c897e`; staged whole-file SHA256 `3a47292a3074181a4af1338c3762df4e74faf831c0a48d81a6d0e15ce7c2720a`. **FULL FILE REPLACEMENT IS NO-GO** because unrelated code differs. Surgical one-hunk patch to the exact live file yields SHA256 `920a4fa28357a3e61d6af64085448eacc76ea8c3c3c1946597b6428e61b506e0`.
- W44 ephemeral live-copy surgical rehearsal #42705730045 SUCCESS: exact input/output SHA, one hunk only, PHP syntax and full suite pass, no live writes.
- `server/deploy/w45-native-origin-surgical.php` guards exact live input SHA, isolated fresh `/releases/w45-native-cors-<12 hex>/src/Application.php` candidate only, and exact output SHA; no way to point at production current path or arbitrary file. W45 actual helper CI #42706261691 SUCCESS: wrong path refused, correct input patched, double patch refused, full PHP suite PASS. No deployment, no uploads.
- W45 accepted backup: `backup/windows-w45-candidate-guard-ci-pass-20261110` at `b5785a24cb1b531e531101632f7553c673cbbb5c`. Earlier `backup/windows-w41-cors-stage-ci-pass-20261110` at `42f1d8de2e6eb55bf219a781e51dd9ba35df0c5b`.

## Remaining manual release gate
**DO NOT DEPLOY without separate explicit owner authorization.** Once explicitly approved:
1. Check current release symlink and exact live PHP SHA again; fail on drift. Pin Hostinger SSH key and server host fingerprint as proven in W30/W43.
2. Under separate unique `releases/w45-native-cors-<12 hex>` clone exact live immutable release, make private backup of original PHP and previous symlink; run the W45 guarded candidate-only patch. Lint and require candidate HMAC/CORS/auth bounds before switching. Do not replace with the staged whole file. No database, catalog or Android/Windows installs.
3. Atomically switch symlink with automatic rollback on any failure; preserve old release and PHP backup. Account for the W30 LiteSpeed compiled PHP cache issue using the prior guarded one-use invalidation procedure, always remove its temporary file.
4. Post-switch verify public HTTPS correct origin OPTIONS 204 + `ACAO: music-application://desktop`, fixed invalid-token GET remains 403 **with** same ACAO, audio Range preflight allowed; existing opaque and browser origins still work; auth route remains CORS-denied; health 200. Roll back on any failure.
5. Separately test an authorized owner signed 206/Range and real native Yandex audible substituted audio + Pause/Seek/Next. Even correct CORS may reveal a distinct Windows `toDownloadInfo` codec/transport/key/IV decoder incompatibility. Don't assume completed until actual owner audio succeeds.

**Current owner action:** nothing to install or re-export. Explicit permission required only for the guarded live CORS change.
