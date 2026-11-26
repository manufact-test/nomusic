# Extension 0.4.88 — persistent native/metadata disagreement, 26 November 2026

Owner candidate, NOT accepted/public. This is detection and explicit recovery, NOT a proven root-cause fix for the Yandex UI/native audio divergence. Do not advertise all listening issues as fixed.

## Evidence
Input: Вставленный текст(20261126-115215).txt (Library libfile_8451bf3b5e7c819198ce954d6ce1320b), screenshot image(20261126-115226).png. Installed87. Final READY, active=null, guarded=false, bridge healthy, no replacement/startup error. Only one eligible native audio media-2:334.6s, running79.478s. UI/catalog48592143 (Не стесняйся) duration250210ms. Previous actual track48591518 had native334.6s. Both Yandex UI and extension show48592143, while owner hears another original.

During paused48591518 at28.489s, metadata becomes conflicted/unknown then48592143. Native duration/time remain334.6s/28.489s. The replacement is disposed on binding change; existing duration guard subsequently correctly prevents an asset for250.21s taking over334.6s audio. Later native resume starts again at28.489s with334.6s duration and stale48592143 metadata. Exact raw stream identity across historical rows cannot be proven: URLs are redacted to host, no prior resource revision was recorded. Do not claim network, VPN, Yandex or CELIKOM causality is proven. No actual alternate replacement remains playing in the final diagnostic.

## Candidate change
Adapter reports a continuously observed independent catalog/native-duration disagreement after1500ms settle. Existing duration admission checks are unchanged. Normal metadata-before-source transitions within this settle, ordinary seek, and unready media do not trigger the warning. While mismatch persists, track.id=null/ambiguous, preventing uploads/suggestions from targeting the stale visible identity. The visible candidate and prior bound identity remain in a bounded diagnostic object, without source URLs. Matching source readiness clears it automatically.

Popup removes the misleading version-available row, shows the mismatch, and offers explicit Обновить Яндекс. This performs a user-requested native page reload, not an automatic reload or a synthetic source/metadata rewrite. User must start music again. Worker accepts only the extension popup, rediscovers target, rechecks the same mismatch track+since, validates current tab URL and coalesces concurrent requests. Changed/recovered/navigated targets are refused. Enable intent and access logic remain unchanged.

Anonymous per-media resource revision and mismatch are included in snapshots/transition trace. Snapshot deduplication includes the mismatch so paused time cannot hide a newly matured warning.

Preserves85 warm current-track descriptors,86 hidden-pause/heartbeat fix and87 bounded confirmed intro wait. No decoder, Range, playback sync, wait bounds, entitlement, backend, server, Android, Windows or infrastructure changes.

## Verification and limits
416 local tests pass; manifest validation and67-file security build gate pass. New adapter regressions against unchanged87 fail for persistent mismatch recognition/publication;88 passes. Tests cover the diagnostic B334.6s -> paused stale A250.21s -> resume, normal metadata-first transition, seek/readiness, stale presence response, matching-source recovery, trusted sender, incident/target revalidation and duplicate click.

ZIP celikom-extension-0.4.88.zip:2495780 bytes, SHA256 aeb8f60cc7741830019a4cf8fd27791363f02c0bf0d13952e7ed82916f544d6a. All67 entries match the current build tree; manifest88,FlokiAPI/permission verified. No public website promotion. Local Chromium launcher exists but its engine binary is missing; no real Chrome/Brave/Yandex listening acceptance is claimed. Existing CI availability/results must be checked separately.

## Still open
E5 underlying UI/native divergence is NOT root-caused; explicit reload is recovery, not proof of permanent prevention. E1 late descriptor, E4 slow audio prepare, E2 late-join settling and E3 boundary-tail audit from87 backlog remain open. Do not enlarge intro holds or revive withdrawn71/81/82/84 mechanisms to mask them.
