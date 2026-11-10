# W52 — real Yandex media 403: root-cause classification staged; no release (2026-11-10)

## Status / owner acceptance
- Owner runs CELIKOM **0.24.6**; ordinary tracks are audible, approved replacements still stall with fast Play/Pause and silence. **AUDIO NO-GO**. No owner installation in W52, no live backend change, no Android/Yandex vendor binary change.
- W51 owner diagnostic establishes 7 genuine native Yandex Media GET requests to CELIKOM resource IDs 139 and 89, all HTTP 403; 0 accepted 200/206. These IDs are **replacement file IDs, not Yandex track IDs**.
- **Exact live 403 reason remains unproven by 0.24.6 evidence.** Diagnostic redaction omits both the native requested query and HTTP 403 body, and no authorized live matching-grant replay or server correlation was supplied. A signed grant accepted by the renderer is not proof that the later native GET preserved its query or passed current session checks.

## Source audit (from current code, not the live request)
- `server/src/Application/ResolveService.php` signs `/api/v1/audio/{replacement_id}?token=...&expires=...&sid=...`; HMAC in `AudioTokenService.php` binds replacement ID, version, expiry and optional session ID. `AudioController.php` returns 403 for invalid/missing signature/expiry/SID, or valid signed SID denied by current `AudioAccessService` entitlement/session check.
- Hosting/proxy/WAF 403 is **still possible**, since the source controller does not represent every HTTP response layer.
- Existing offline server tests `server/tests/smoke.php` cover valid signed streaming, invalid/expired token, version rotation, and SID binding; `server/tests/entitlement.php` covers session SID tampering, revoked audio access. Those tests cannot prove the owner's live URL remained identical.
- `windows-companion/w15/Celikom.Companion/GrantValidator.cs` validates granted URL; `w22/native-resource-adapter.mjs` maps it to `downloadInfo.urls[0]` and `downloadInfo.url`; the browser's subsequent native GET must be inspected separately. No basis yet to alter HMAC, disable SID binding, force CORS wildcard, or change MP3 again.

## W52 staging-only implementation
Changed `windows-companion/w23/host.cjs`:
1. Validated grant URL is held **only transiently** in the main-process per-view `WeakMap` with a maximum 32 resource IDs and the grant expiry, keyed by exact replacement resource ID, after authenticated localhost grant delivery and before renderer source application. No URL/token/SID is logged, hashed, serialized to a diagnostics file, or sent to other views. On disconnect, signed-out state or origin change, expectations are removed.
2. Passive CDP `Network.requestWillBeSent` for trusted CELIKOM `/api/v1/audio/{replacement_id}` compares the actual `origin+path+query` against the expected signed link. Emits **only** `PLAYER_URL_MATCH`, `PLAYER_URL_QUERY_MISSING`, `PLAYER_URL_QUERY_CHANGED`, `PLAYER_URL_EXPECTATION_MISSING`, or `PLAYER_URL_EXPIRED_AT_REQUEST`. A missing/changed query classification is evidence, not automatic proof of which native Yandex component changed it.
3. Native network diagnostic labels `resource_id=139` rather than misleading `track=139`; true Yandex track IDs retain `track=` in resolve/mapping logs. This avoids false track/resource correlation.
4. 403 response headers are read **for exact CELIKOM audio route only**, and logged as `PLAYER_403_JSON`, `PLAYER_403_HTML`, or `PLAYER_403_OTHER`. Optional `Network.getResponseBody` is scoped strictly to a real GET HTTP403 with JSON Content-Type on that audio route. It accepts only the tiny exact JSON envelope with one fixed error key and emits `PLAYER_403_PHP_INVALID_AUDIO_TOKEN` or `PLAYER_403_PHP_ACCESS_DENIED` (otherwise `PLAYER_403_JSON_UNCLASSIFIED`). No response body/error text is persisted. If CDP body read is unavailable, the observer fails open. **No native request interception or synthetic audio fetch.**
5. Bounded in-memory request state (64) and expectation state (32), existing Yandex origin restrictions, original player events, transport, player controls and source mapping preserved. The app GUI/installer version remains `0.24.6` in staging; this code is **NOT installed for owner**.

New offline cases in `windows-companion/w23/native-host.test.mjs`: exact URL, stripped query, changed SID, unmapped resource ID, expired grant, JSON invalid token, JSON access denied, unknown server JSON, HTML/oversized/foreign responses, 206 non-inspection, URL secrecy and distinct `resource_id` label.

## Read-only vendor URL flow audit — follow-up
- Pinned vendor-signed Yandex ASAR scanned in isolated W49 runner; **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42788482449. No real session, player playback, media HTTP request or owner installation.
- The original `DownloadInfoSource.src` builds from `downloadInfo.urls[0]`, then optionally appends `getQueryParamsString()` and a media position fragment. The appended `?container=...&codec=...` is conditional on specific MP4 codec metadata, and `vsid/sourceIndex` would also force it. For mapped `codec=mp3`, `transport=raw` and `createMediaSource` without those options, **the normal MP3 source getter does not append that second query string**; it preserves the signed query through this getter (plus an HTTP-omitted `#t` fragment).
- Therefore the apparent double-`?` possibility is **not a demonstrated cause of these MP3 403s**. Do not append fake padding query parameters, modify backend token format, or patch vendor source based on that hypothesis. Query manipulation in later browser/loader stages still requires a real request/grant comparison.
- Server callchain review confirms `userAccess` checks session+entitlement before resolving a signed URL and `AudioAccessService` checks the session/entitlement again for each Range. This makes entitlement expiry/revocation possible but **not established**; the live 403 code and request query are still absent from 0.24.6 diagnostics.

## Release gate and interpretation
- `URL_QUERY_MISSING/CHANGED` on the **same resource ID**: investigate Yandex media source URL rewriting/prefetch and correct source construction without removing server signature/session protection; retest a disposable signed Yandex runner.
- `URL_MATCH` + `PHP_INVALID_AUDIO_TOKEN`: verify live PHP key/configuration consistency, database version changes and timestamp/expiry skew using privacy-safe server-side comparison and a fresh legitimately issued grant. Do not expose token/key or broaden TTL before proof.
- `URL_MATCH` + `PHP_ACCESS_DENIED`: investigate session revocation/entitlement/refresh expiry with narrow authorized test, preserve per-Range entitlement recheck.
- `URL_MATCH` + `PLAYER_403_HTML`: investigate specific hosting/WAF/proxy response; no blanket exemption.
- Genuine native GET 200/206 without audio: resume `createMediaSource/corePlay` and decoder/transport investigation, not `HTTP403` remediation.
- Do **not** publish a diagnostic-only installer or claim a fixed 403 from local tests. One owner audio test only after independently demonstrated end-to-end correction or a narrowly approved validation protocol; installer only via verified ChatGPT Library `CELIKOM/Windows`, as a single-app in-place update that retains DPAPI login.

## CI / rollback
- W52 source-only W48 native witness flow: https://github.com/manufact-test/nomusic/actions/runs/42787607771 **SUCCESS** (54 Node tests). Previous W48 failure at earlier W52 SHA was a stale W48 grep for removed W48 ResourceTiming, corrected to W50 current semantics.
- W52 W20 safe installer **staging** source compatibility: https://github.com/manufact-test/nomusic/actions/runs/42787432243 **SUCCESS**. This does not authorize distributing the built installer or mean sound works.
- W23 genuine signed vendor disposable flow (SHA `1e6ad2d5`) is tracked at https://github.com/manufact-test/nomusic/actions/runs/42787432599; **SUCCESS** (verified GitHub Actions). It tests isolated host and original restoration, **not user-account playback**.
- Frozen W51 backup: `backup/windows-w51-http403-pre-w52-stage-20261110` @ `a2797566fde88fc707e54f14ff0ef6e014e9c68b`.
- The earlier owner 0.24.6 source backup remains `backup/windows-w50-owner-0246-audio-403-pre-w51-docs-20261110` @ `38b9e0d691b47a11a800eb4c6d26d07fc47068fe`.

**Not yet verified:** actual signed URL equality at the owner's native Media GET, true source of response 403, backend/live session state, end-to-end HTTP206, audible playback, Windows installer upgrade after W52. Until independently verified, continue to mark audio NO-GO.
