# W53 — make native HTTP403 evidence actually exportable; no live audio claim (2026-11-10)

## Confirmed new defect in W52 code (stage only)
W52's Electron `host.cjs` emitted typed `PLAYER_403_*` events with digits and `resource_id=<CELIKOM file id>`, but the installed Windows GUI's `DiagnosticLog.IsSafeEntry()` allowlist accepted only `[A-Z_]` with optional `track=<id>`. It silently discarded **all** new W52 403 classification events and **all** correctly labeled native media events before the owner TXT was produced. Furthermore, `PlayerNetworkRequestObserved` and `PlayerNetworkCorsFailureObserved` only searched for the erroneous W50 `|track=` label, so summary flags would falsely read `false` with W52's corrected logs. W52 should not be released without this correction.

## W53 staged fixes
1. `windows-companion/w15/Celikom.Companion/DiagnosticLog.cs`: retain strict timestamp and uppercase-code validation, now allowing numeric code parts and exactly one numeric label, `track` or `resource_id`. Reject raw URL, `?`, `&`, `=` extras, malformed IDs, appended secrets and newlines. Correct event summary to read real `resource_id` and backward-compatible old `track`. Add explicit typed indicators `NativeAudio403Observed`, `NativeMediaUrlExactMatchObserved`, `NativeMediaUrlQueryMismatchObserved`, `Native403PhpSignatureRejectionObserved`, `Native403PhpAccessDenialObserved`, `Native403HtmlResponseObserved`. Preserve `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING`, 15-minute scope and original player/sound claims.
2. `windows-companion/w15/Celikom.Companion.Tests/Program.cs`: end-to-end test actual on-disk native TXT events with numeric code/resource ID; verify owner-export inclusion, all summary flags and rejection of query strings/sessions/other sensitive payloads. Old W50 track label still accepted for historical compatibility.
3. `windows-companion/w23/host.cjs`: make real URL and 403 classification events non-deduplicated (existing `note` logic otherwise records only first observation per code, destroying per-resource correlation). Still bounded by file rotation and 15-minute export. Keep actual URLs only ephemeral in memory.
4. Narrow optional `Network.getResponseBody` for actual native HTTP403 JSON: request only if the known `Content-Length` is <=160 bytes or the actual `Network.loadingFinished.encodedDataLength` is <=4096 bytes. Never retrieve unbounded, foreign, successful or media-content responses. Classify fixed PHP enums without logging the body or arbitrary error text. This is only a passive CDP observer; no media interception or additional HTTP traffic.
5. `w23/native-host.test.mjs`: verify repeat native GETs preserve per-request categories and denial body read limits. No version bump, production deploy, installer publication, or owner update.

## Server / Yandex chain facts still true
- Owner 0.24.6 sees normal Yandex songs play, approved substitutes immediately stall; real native Yandex Media GETs 7/7 fail HTTP403 on CELIKOM resource IDs 139 and 89. 0 successful native 200/206. Current owner log contains neither query nor 403 response-body enum, so the *exact* live culprit is still **NOT PROVEN**.
- Original pinned signed Yandex 5.126.1 read-only static audit https://github.com/manufact-test/nomusic/actions/runs/42788482449 SUCCESS: the normal mapped RAW MP3 `DownloadInfoSource.src` retains `urls[0]` signed query, adding only an ignored `#t` fragment. It does not normally append a second query without codec/VSID/sourceIndex flags. Do not claim that Yandex necessarily strips signed URL.
- PHP `ResolveService` signs resource/version/expiry/optional session; `AudioController` 403 comes from invalid token/sid/expiry/HMAC/version or `AudioAccessService` session/entitlement denial. HTML/proxy/WAF denial remains a separate possibility until a real response is categorized.
- Do not remove URL signing, increase token TTL blindly, copy encrypted keys to plaintext MP3, alter CORS again, or ship another diagnostic-only installer. Production, backend, original Yandex files, Android/Test.50 stay untouched.

## Acceptance / next
Source tests must pass and the owner must not be asked to install the still-silent 0.24.6 again. W53's improved diagnostic output is **not on the owner's machine** until a future approved update. Exact live rejection reason cannot be inferred from simulated test data, however detailed. Continue with supported read-only source validation and the least invasive evidence path; only once a narrow corrective change is proven should a signed/bounded same-app upgrade and single owner playback validation be requested. Library delivery must use verified `CELIKOM/Windows` file card, never a guessed sandbox path.

## Verification / rollback
- W53 W48 native tests workflow: https://github.com/manufact-test/nomusic/actions/runs/42789543674 (SUCCESS, including new native GET regression fixtures).
- W53 W20 staging workflow: https://github.com/manufact-test/nomusic/actions/runs/42789543676 (final result must be verified, no published installer).
- W53 W23 genuine vendor disposable workflow: https://github.com/manufact-test/nomusic/actions/runs/42789543699 (final result must be verified, original vendor restore required).
- W52 rollback: `backup/windows-w52-403-classification-before-export-fix-20261110` at `34e4559de0edeef7df89567cb928de1a99d13859`.
- Earlier W51 pre-W52 rollback: `backup/windows-w51-http403-pre-w52-stage-20261110` at `a2797566fde88fc707e54f14ff0ef6e014e9c68b`.

**NO-GO:** HTTP403 cause in the owner's native renderer, end-to-end actual HTTP206, audible substitute, Pause/Seek/Next are not yet validated.
