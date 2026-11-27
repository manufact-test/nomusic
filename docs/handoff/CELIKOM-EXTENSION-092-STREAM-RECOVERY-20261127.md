# Extension 0.4.92 — interrupted MP3 range recovery

27 November 2026. Private owner candidate, not customer publication or listening acceptance.

## Evidence

Owner reported loss of replacement playback after accepting Yandex's page update/reload, then supplied another diagnostic reporting an audible dip during a mid-song join. Inputs: `Вставленный текст(20261127-095032).txt` and `Вставленный текст(20261127-095117).txt`.

The first 0.4.91 diagnostic identifies track 132465315 confidently; bridge and account/API reads remain healthy after a transient connection failure. At 09:49:27 UTC an MP3 range header request failed at offset 5,832,704, with simultaneous config transport errors. The player was destroyed and automatically re-created. At 09:49:38 another failure occurred while reading a successful HTTP 206 body at offset 4,259,840. That body exception became generic `remote-stream-error`, which is not an automatic-retry category. Replacement remained inactive although native playback continued.

The second diagnostic follows a fresh controller/page mount. Original playback resumed at 71 seconds; replacement decoding/positioning completed about two seconds later, with the guard still absent during that seek. The replacement then played and completed the whole file. The owner's audible dip is retained as a listening test target; these snapshots do not prove its exact acoustic cause. Do not claim a Yandex adapter incompatibility or that the dip is eliminated from unit tests.

## Narrow correction

The existing MP3 MediaSource pump now retries failed header/body transport reads at the same signed URL and exact byte range, before any bytes from that failed response are appended. Keep the same decoder, already committed buffer and playback state during bounded retries. Three attempts maximum; existing 15-second per-range deadline remains in force. An exhausted body transport failure is classified as `remote-stream-network`, preserving the controller's existing recovery path rather than permanently blocking the track as an unknown error.

HTTP access denial, malformed ranges, short completed bodies, changed strong ETag, wrong format and decoder errors remain failures. Stop/new track cancels the read/retry and cannot invoke a stale fatal callback. No native-file/M4A changes, new playback architecture, backend/auth changes or permission expansion.

## Verification and boundaries

Added nine targeted tests: header loss retaining the playing decoder; repeated body failure with no duplicate append; bounded exhaustion/network classification; Stop during backoff; short completed body rejection; access revocation after retry; first-range recovery; content identity change; timeout during retry backoff. Five of the first six new tests failed against unchanged 0.4.91 before the production correction. The remaining tests guard integrity and cancellation boundaries.

449 extension tests, full ZIP build, production manifest and security validation passed locally. Real owner listening remains required, especially uninterrupted playback through a connection change and an audible mid-song handoff. Work cloud unpacked extension installation remains blocked as documented earlier.

The separately deferred longer playback diagnostics are not implemented. The earlier VPN interruption is not globally declared resolved; this release addresses the now-proven transport teardown/permanent-block pathway. Server upload/proposal repair remains intact and owner-confirmed.

Stage and deliver only through the existing private Floki spool, exact owner approval, trusted publisher and verified celikom.com HTTPS URLs. Record actual source/run/size/digest and delivery receipt after completion; do not promote customers or infer listening acceptance from CI.

## Verified private owner delivery — 27 November 2026

- Playback fix commit: `e13d837a01882bd7a6c046a2eb91967eef1162b1`.
- Exact build source: `4e6ff1aeb8b8ad97c66ebf66ad66b6181bef4885`; Floki run `45978089929`, attempt 1. Tests/build, security, checksum and private spool steps passed. A separate earlier run was assigned to ci02 without starting steps; the existing trigger requested the next available runner rather than changing runner infrastructure.
- Independent root-owned consumer ZIP/spool validation: administrative run `45978201734`, SUCCESS.
- File: `celikom-extension-0.4.92.zip`, 2,502,122 bytes.
- SHA-256: `8c7cb39ec1564ad3f063bcfd8d9c0d361fc4bbea092057598d22d68877cece0b`.
- Approved in the existing owner-only manifest; public_stable remains null. Existing timer published the exact package and latest pointer.
- Explicit mirror-sync invocation reported an unrelated atomic push failure for another experiment branch on the local Git destination. Read-only audit `45978587799` confirmed the authoritative GitHub mirror already contained the 0.4.92 approval and the trusted current-owner receipt was already 0.4.92. No other branch, Git credentials, mirroring policy or Android/Windows infrastructure was modified.
- Final independent delivery verification: administrative run `45978702259`, SUCCESS. Trusted receipt matches source/run/attempt/size/hash; versioned and latest HTTPS downloads returned anonymous 401 and authorized 200 with exact bytes and digest.
- Verified owner URL: https://celikom.com/downloads/extension/celikom-extension-0.4.92.zip

No real Yandex listening acceptance or customer publication is claimed. Owner should update the existing unpacked folder, reload the extension and Yandex tab, then test interrupted connection and mid-song joining again. General expanded playback diagnostics remain deferred.
