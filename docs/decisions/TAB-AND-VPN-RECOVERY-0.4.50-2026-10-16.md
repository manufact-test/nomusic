# 0.4.50: reopen/return recovery after VPN changes

Owner confirmed .49 playback/format fixes appear correct on 2026-10-15 18:26 MSK and continues testing. New 2026-10-16 report: closed Yandex, worked elsewhere/switched VPN, reopened once without automatic reconnect; later reopen attempts worked. No diagnostics for that occurrence, so its exact cause is not established. Do not describe a code-path reproduction as proof of the owner's exact failure.

## Reproduced failure paths

- Bootstrap cached EVERY thrown script injection error until navigation or explicit Retry, including transient removed-frame/navigation faults. Automatic tab recovery made only one attempt and discarded errors. A subsequent close/reopen naturally used a new tab ID, matching the reported pattern.
- A controller can be healthy while its access/resolve reads belong to a previous network connection. Worker online/offline hints alone do not cover tab return or all VPN route changes. Content had no online/visibility recovery hint. A transient player error could retain its 5–60 s backoff even after fresh authorization because ordinary allowed state did not clear that block.
- A stalled local tab message/injection had no overall bootstrap deadline. Late bootstrap work could continue after navigation.

## Changes

- Only genuine permission/protected-page injection denials are cached. Transient errors remain retryable. Bootstrap has a five-second overall deadline and checks the current tab-operation lease after awaits, preventing obsolete work from continuing after replacement/navigation.
- Tab events coalesce one recovery job per tab. Transient startup/bridge/injection errors automatically retry after 500/1500/4000 ms (three retries maximum). Recheck persisted enabled and live supported/non-discarded/non-loading tab before every attempt. Closure, replacement and navigation cancel old jobs. No permanent worker, polling, forced reload, focus changes or additional permissions.
- Content sends narrow installed-worker hints on new document, online and visible return. A healthy ordinary foreground visit does not reset working transport. A return after an idle pulse gap (>5 s), known transient error/suspension, current failed access check, or online event clears stale GET transport and performs fresh entitlement verification. Duplicate same-reason hints within one second coalesce. Page hint acknowledgment is bounded to three seconds. Hint is only a request to verify, never authority to play.
- Recovery revalidates the actual sender tab, fences old epoch replies and does not replay writes/trial activation. Fresh allowed recovery can immediately clear only transient network/bridge backoff. Duration/token/revocation blocks, Stop, manual Original, account/session denials and normal retry pacing remain enforced. Ordinary healthy heartbeats do not bypass network backoff.
- Diagnostics add lastRecoveryHint reason/time, no URLs or credentials.

## Validation / limits

274 extension tests pass locally: removed-frame retry without Start, cached permission denial, stalled receiver deadline/late result, bounded/coalesced retries, navigation/closure/Stop cancellation, idle/VPN hints, late stale authorization, no unauthorized hint, Stop during fresh authorization, manual Original and semantic failure preservation. Native Chrome fixture imports actual MAIN/content bundles and dispatches online/visibility return events with real browser message loop; verifies hint delivery and Stop/Original preservation. Native Chrome/full CI results recorded in handoff before delivery.

This does not simulate an actual commercial VPN change on the owner's device. Genuine network outage or denied permission/access still fails open and cannot be guaranteed to reconnect before network/access is restored.

Extension-only .50. Backend remains deployed .46-f2d1cc31f598a983c46660688b453392faf0fc8d; no audio, catalog mapping, moderation, gain or account changes. Preserve M4A replacement 27. PR #6 OPEN/unmerged, issue #7 OPEN; preserve concurrent Android commits through 02cbfafb7aa94b85a4226460925c7671c8c6916a and subsequent unrelated work.
