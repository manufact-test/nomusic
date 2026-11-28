# CURRENT HANDOFF — BETA31 NAV52 delivered; phone acceptance next

Date: 2026-11-28
Repository: `manufact-test/nomusic`
Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Read first

1. `docs/android/NEXT-CHAT.md` — this current handoff.
2. `docs/android/CELIKOM-A1-BETA31-NAV52-COMMITTED-CURSOR-LIFETIME-2026-11-28.md` — exact code correction, tests, build and delivery.
3. `docs/android/CELIKOM-A1-BETA30-NAV51-LIVE-DATASOURCE-WITNESS-2026-11-27.md` — NAV50/NAV51 lineage and counters.
4. `docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md` — delivery history and trusted security boundary.

## Current state

- **BETA31 NAV52 is built, signed and delivered through celikom.com.**
- Android source commit: `ef661ce23da8c50367b9aaaf0d27c65aed160ba1`.
- Source/export workflow run `46121780348`, attempt 1 — SUCCESS.
- Owner JVM gate and fresh Android 13 ARM64/ARMv7 native gate — SUCCESS.
- Targeted output included `RAMIL_AU_ORIGINAL_TRACK_ONLY_BETA_LINEAGE_PASS` and `NATIVE_EXO_SINGLE_PLAYER_ENCODED_BYTES_ROUTE_PASS`.
- Native verdict remains `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- APK: `CELIKOM-A1-RAMIL-AU-BETA31-HONOR50-20261128.apk`, 71,602,156 bytes.
- SHA-256: `fed4b9c150e45eadc6cc424b2a904f5ac5951160ef1e1e8c9227c039f37562fe`.
- Unpublished owner draft release ID: `461389699`.
- Trusted delivery run `46122831604`, attempt 3, job `140919835283` on `celikom-floki-ci02` — SUCCESS. The exact signer/package, provenance, size and digest passed. Root receipt and independent live HTTPS HTTP 200/content-type/size/SHA checks passed; the draft URL was read back successfully.
- The capability URL was delivered privately to the owner. Never copy it into Git, documentation, Actions logs or public summaries.
- **Phone listening result and fresh BETA31 diagnostic TXT are pending. Audible replacement is not yet proven.**

## BETA31 NAV52 correction

The original source setter now calls `NativeExoAlternateByteRoute.supersedeSelection()` rather than immediately cancelling the route. An already committed exact cursor can finish reads until its own native close; it cannot be reopened or re-armed. The next source remains independent. A focused regression covers overlapping source selection, cursor continuity, stale-source rejection, independent next-source bytes, unrelated-source rejection and exact close behavior.

See the BETA31 document for the precise implementation and test/build receipts. Do not repeat NAV51 work or build another telemetry-only version without a concrete reason.

## What was already established

BETA29 had a negative listening result. Authorization, alternate grant, DataSource arm/open and positive byte reads worked, but NAV50 could not correlate those reads to the active renderer period. NAV51 fixed the exact DataSource identity-witness lifetime error in `StageBAudioEvidence.java`: after exact Descriptor → Factory → DataSource binding, the resolver no longer depends on the vendor Descriptor/Factory weak references remaining alive. The durable `factorySourceIdentityBound` witness is invalidated on rebind; creator, wrapper, Track, source, reverse-link and Beta/Album checks remain.

BETA31 NAV52 addresses the next concrete lifecycle boundary. A new original source setter can run before the renderer closes the already committed previous source. The old `cancelForNext()` reset could close that committed cursor too early. The new `supersedeSelection()` retires the exact previous source but lets its already committed cursor finish reads until its own native close; it never grants a new open/re-arm right. The new source receives an independent grant/cursor. This is a targeted lifecycle correction, **not proof that this was the only phone-side cause** and not proof of audible replacement.

## Owner's overriding development priority — speed to a working mobile version

The owner clarified that the goal is **a functioning Android music replacement as quickly as possible.** Optimize the entire development loop for time to actual audible success. Diagnostics, source inspection and tests are tools, not milestones in themselves. Read the fresh TXT, select the most direct justified route, implement the correction, run the necessary gates and deliver a testable build. If the route is already known, act immediately; do not delay implementation by exploring additional theories or unrelated subsystems. If a concrete blocker requires deeper investigation, investigate only as far as necessary to unblock the fix. Diagnostic builds and targeted experiments are allowed when they are genuinely the fastest way to the working product; they are not categorically prohibited. Avoid long speculative detours, repetitive status reports, unnecessary research, and waiting on redundant checks. Preserve required safety/signing/release checks and existing working behavior. Measure progress by working mobile playback and time to the next meaningful correction, not by the number of investigations or completed CI runs.

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


## Next step — real phone acceptance

Install BETA31 **over BETA30** on the existing Honor 50. Do not uninstall CELIKOM or clear app data/cache.

1. Confirm CELIKOM status is `ВКЛ`.
2. Play Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, and listen to `00:43–00:54`.
3. Test the second song that previously had leading gaps.
4. Export a fresh BETA31 TXT and report separately whether the alternate sound was actually heard.

If it works, preserve this path and verify the remaining reproducible cases. If it does not, use the BETA31 TXT plus the listening result to choose the next narrow correction; do not ask for BETA30 diagnostics again and do not repeat already passed authorization/source-lineage investigations.

## Delivery recovery reference

The last delivery failure was isolated to CI01 accepting a job without starting a worker. Two BETA31 delivery attempts on CI01 ended before any step. A read-only host audit showed CI01 listener present but no worker; CI02 was healthy. The existing trusted spool was retried without rebuilding the APK; attempt 3 ran on CI02 and completed successfully. The root-owned timer is active, the service completed successfully, and the exact BETA31 receipt records `https_verified=true`. No runner restart, permission change, server product change, Windows change or delivery-security bypass was made. Do not re-investigate delivery unless a new concrete failure occurs.

Owner drafts remain unpublished. No GitHub APK URL should be sent instead of the celikom.com capability URL.

## Boundaries

Keep Android application changes on the working branch. Do not merge to main without a successful phone result and explicit owner approval. Do not change server/catalog, signed grants, Windows, stable Android or OTA without a separate justified need and authorization. Keep the original Yandex player; no second player or new architecture as a shortcut. Pre-NAV51 backup: `backup/android-a1-nav50-live-datasource-witness-pre-fix-20261127`. Older handoff revisions remain in Git history; do not revive their obsolete delivery instructions.
