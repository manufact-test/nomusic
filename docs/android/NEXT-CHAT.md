# CURRENT HANDOFF — BETA30 NAV51 delivered; fix audible replacement next

Date: 2026-11-28
Repository: `manufact-test/nomusic`
Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Read first

1. `docs/android/NEXT-CHAT.md` — this current handoff.
2. `docs/android/CELIKOM-A1-BETA30-NAV51-LIVE-DATASOURCE-WITNESS-2026-11-27.md` — NAV50/NAV51 code and exact counters.
3. `docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md` — only if needed for delivery.
4. `docs/android/CELIKOM-A1-BETA28-ALT-DATASOURCE-LIVE-RENDERER-CORRELATION-2026-11-27.md` and `docs/android/CELIKOM-A1-BETA28-OWNER-SESSION-RECOVERY-2026-11-27.md` — historical reference only when relevant.

This checkpoint supersedes all earlier queued/stalled-delivery instructions. Do not spend the next chat re-investigating the completed BETA30 delivery.

## Current state

- BETA30 NAV51 has been built, signed, delivered and the verified direct APK URL was sent privately to the owner.
- Source commit: `aef40439586304fd57dabcbf20dfcce3af52a181`; source/export run `46070081916`, attempt 1 — SUCCESS.
- Owner JVM regression `RAMIL_AU_ORIGINAL_TRACK_ONLY_BETA_LINEAGE_PASS` and fresh Android 13 ARM64/ARMv7 native gate `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO` passed.
- APK: `CELIKOM-A1-RAMIL-AU-BETA30-HONOR50-20261127.apk`, 71602156 bytes, SHA-256 `e33c3e31721d76ee82df7554f0eddb311202566328eafcb50f3f0958b7b53dfe`.
- Unpublished owner draft `461085315`, tag `celikom-a1-owner-46070081916-1`.
- Trusted Floki delivery run `46070217462`, attempt 5, job `140793123974` — SUCCESS. Provenance, exact signer/package, size/hash, root-owned HTTPS receipt and private draft readback passed. No APK rebuild was needed.
- The actual capability URL is private; never include it in Git, documentation or logs.
- BETA30 phone listening result and fresh NAV51 TXT are not yet present in this handoff. The owner will supply them in the next chat. **Audible replacement is not yet proven.**

## What was already established

BETA29 had a negative listening result. The earlier report names TXT `CELIKOM-A1-Diagnostics-1795806916651.txt`; a subsequent BETA29 TXT `CELIKOM-A1-Diagnostics-1795812695254.txt` was reported in the transferred chat with the same NAV50 outcomes. Authorization, alternate grant, DataSource arm/open and positive byte reads worked (`AUDIO_OPEN=ONE`, `AUDIO_READ=MANY`). NAV50 had no same-current-period or different-period confirmation; `NO_ROUTE_CURRENT_PERIOD=FEW`, `DATASOURCE_UNRESOLVED_CURRENT_PERIOD=FEW`. The process-wide counts cannot prove per-song or selection-generation causality. `BUFFER_EOS_ACCESS=NO_HOOK` was reported; do not treat unknown EOS as non-EOS.

NAV51 fixed a specific identity-witness lifetime error in `StageBAudioEvidence.java`: the first-open path releases the strong descriptor pin, but NAV50 required Descriptor and Factory weak references to remain alive after exact DataSource binding. The durable value-free `factorySourceIdentityBound` witness is set only after exact lineage verification and invalidated on rebind. The exact creator/wrapper/Track/source/reverse link and Beta/Album checks remain. This is a witness repair, not an audio-routing change. The targeted weak-reference/rebind regression passed. The other previously identified candidate, `NativeEarlySourceLifecycleBridge.cancelForNext()`, may reset the route at a subsequent selection; causation on the active song has not been demonstrated.

## Owner's overriding development priority — speed to a working mobile version

The owner clarified that the goal is not merely to avoid diagnostic-only APKs: **deliver a functioning Android music replacement as quickly as possible.** Optimize the entire development loop for time to actual audible success. Diagnostics, source inspection and tests are tools, not milestones in themselves. Read the fresh TXT, select the most direct justified route, implement the correction, run the necessary gates and deliver a testable build. If the route is already known, act immediately; do not delay implementation by exploring additional theories or unrelated subsystems. If a concrete blocker requires deeper investigation, investigate only as far as necessary to unblock the fix. Diagnostic builds and targeted experiments are allowed when they are genuinely the fastest way to the working product; they are not categorically prohibited. Avoid long speculative detours, repetitive status reports, unnecessary research, and waiting on redundant checks. Preserve required safety/signing/release checks and existing working behavior. Measure progress by working mobile playback and time to the next meaningful correction, not by the number of investigations or completed CI runs.

## Next task — prioritize an actual fix

The owner explicitly requests a faster, outcome-driven development process. Read the fresh BETA30 TXT and listening result immediately. Use existing evidence and source to choose the smallest justified fix. Do not automatically create another diagnostic-only version; use one if it is the fastest justified route to a functional fix.

- If the owner hears the correct alternate audio, preserve that path and investigate only remaining reproducible failures; do not break working behavior.
- If the owner does not hear it, inspect the existing NAV51 counters and relevant NAV50 correlation together. Confirm the TXT is BETA30/NAV51; do not ask for previous diagnostics again.
- If exact current-period alternate reads are established, concentrate on the downstream extractor/decoder/output boundary instead of redoing authorization/download/source identity. A same-source counter alone is not proof of audible output.
- If a different period or generation is established, concentrate on source selection and lifecycle/prefetch. If NO_ROUTE remains, inspect when the route is reset, including cancelForNext, without assuming that it is the cause.
- If source resolution remains missing, use the existing 12 NAV51 reasons to identify the concrete failed link and repair that boundary. Only add narrowly scoped evidence if it is genuinely necessary to decide between incompatible fixes; avoid another broad telemetry-only round.
- Once there is a concrete, justified correction, implement it in this branch, run the focused regression and existing required build/signing gates, deliver the next signed APK using the trusted route, and request a short real-phone test. Do not run redundant checks or rebuild an unchanged APK due to delivery infrastructure.
- If evidence is insufficient, investigate the specific missing fact with a clear decision it will enable; do not wander into unrelated subsystems or propose an arbitrary architecture rewrite. Do not make speculative destructive changes just to produce a version.

Keep updates short: concrete fault, what changed, test result, verified direct APK link, what the owner needs to check. Do not replace implementation with lengthy reports. Do not ask the owner to operate GitHub Actions. Final success means the owner hears the intended alternate audio inside original Yandex Music, not CI SUCCESS or byte-read counts.

## Phone test

Install over BETA29 without uninstalling or clearing app data/cache (if not already installed). CELIKOM status should be `ВКЛ`; if necessary use explicit CELIKOM session/login action, not Yandex login. Ramil / 10AGE «Ау», album `38902809`, track `144530503`, 00:43–00:54; then another song with prior leading gaps. Fresh TXT and listening outcome. If the owner already provides them, do not request the same test again before acting.

## Delivery recovery reference (resolved for BETA30)

The shared self-hosted runner accepted jobs but cancelled workers before the first step. Host storage/memory/DNS were healthy. Existing owner-enabled maintenance channel was used; read-only host check run `46083699896` succeeded. CI02 logs showed JobDispatcher immediately cancelling the worker. First restart guard failed on docker top; a corrected PID-tree guard confirmed no worker, then restarted only existing `celikom-ci-runner2.service` in run `46084579328` — SUCCESS. Maintenance request cleared in main commit `684c4298ab6518f91c87d838f46b1d5bfa68eff0`. BETA30 attempt 5 delivered successfully afterward. This proves CI02 worked for that delivery, not that CI01 or all infrastructure is permanently repaired. Do not repeat this recovery unless a real new delivery failure warrants it. See Floki delivery document for details. Keep owner drafts unpublished; do not bypass the root verifier, expose credentials, change security permissions or publish the APK.

## Boundaries

Keep Android application changes on the working branch. Do not merge to main without a successful phone result and explicit owner approval. Do not change server/catalog, signed grants, Windows, stable Android or OTA without a separate justified need and authorization. Keep the original Yandex player; no second player or new architecture as a shortcut. Pre-NAV51 backup: `backup/android-a1-nav50-live-datasource-witness-pre-fix-20261127`. Older handoff revisions remain in Git history; do not revive their obsolete delivery instructions.
