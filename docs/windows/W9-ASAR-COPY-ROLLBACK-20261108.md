# W9 — physical ASAR copy, native Electron startup and byte-checked restore

**2026-11-08. Hard boundary:** synthetic temporary files, generic
test Electron 44.10.2 only. NEVER install this on owner's official
Yandex Music or patch its executable. User has not approved modification.

## Why this stage matters

Owner's official Windows Yandex Music 5.126.1.0 package
(ASAR SHA-256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`)
was inspected read-only in W1–W3. W5–W8 already prove dynamic source
descriptors, native decoding, recovery and CDP attachment in **separate
test Electron instances using public Yandex web classes**.

The missing bridge is a working, *reversible and version-gated* way
to make the running **official** app load CELIKOM. Electron archives
may have per-file integrity metadata and header SHA-256 embedded in
the **Windows executable's resource section**, enforced by a fuse.
A modified archive can fail to start if the integrity header changes.
Blindly rewriting ASAR contents or EXE hashes is unsafe and may break
the app's signature, future updates and application launch.

Official docs:
- https://www.electronjs.org/docs/latest/tutorial/asar-integrity
- https://www.electronjs.org/docs/latest/tutorial/fuses
- https://www.electronjs.org/docs/latest/tutorial/application-distribution

## W9 deliverables

`windows-companion/w9/fixture-app/` contains **our own tiny** Electron
app (two original files). `fixture-hook.cjs` is a harmless startup marker,
**not a real audio hook**. Both are checked in and contain no Yandex data.

`asar-copy-lab.mjs` uses pinned `@electron/asar@4.3.1` to:

1. Generate a *new* ASAR exclusively from the committed synthetic fixture.
   Creates a unique OS-temp directory, marker and independent backup, then
   verifies SHA-256 and ASAR header hash.
2. Only operate on `celikom-w9-generated-asar-only-*` directories with
   explicit marker and no symlinks. No API takes an arbitrary official
   application archive as input. No EXE file is opened or written.
3. Extract a **separate copy** of that synthetic archive, insert one
   known test-only require statement at a fixed marker, and repack it as
   an actual ASAR; original archive remains byte-for-byte untouched.
4. Detect the changed header hash and classify **unknown/active ASAR
   integrity enforcement as official-client NO-GO**, even when the
   temporary unsigned test Electron can launch the modified copy.
5. Simulate interruption after journal, after original copy parked
   and after candidate promoted. Restore only from byte-verified backup.
6. Refuse installation/rollback when an unknown third-party change,
   missing or corrupted backup or incompatible archive is observed.
   Never claim a successful restore until the copy's full SHA-256
   matches the generated original.
7. Resume interrupted recovery using a persisted journal. Copy-only
   rollback is idempotent; no permanent side effects beyond the OS
   temp fixture and CI logs.

`asar-copy-lab.test.mjs` checks integrity refusal, copy isolation,
header change, clean restoration, three simulated install failures,
three simulated restore failures, third-party changes and bad backup.

`run-boot-e2e.mjs` launches **a real generic Electron executable**
(not a fake Node substitute) against the original generated `app.asar`,
then against the modified isolated copy, and then against the SHA-verified
restored copy. Each startup must return an actual Electron-renderer
report verifying one media element and whether the test-only hook ran.
The restored archive must reboot without the injected test marker.
A child failure or missing boot marker causes RED CI.

Windows CI runs W9 alongside W4–W8, public pinned Yandex renderer
tests and existing W3 .NET read-only Windows probe. Code stays on
`experiment/windows-companion-integration-20261108` inside
`windows-companion/**`, `docs/windows/**` and the dedicated workflow.

## What a pass will NOT establish

- Owner's official Yandex `5.126.1.0` EXE was **not** present in CI,
  so its exact integrity fuse, signing, resource hash and update behavior
  remain unknown. W9 cannot authorize modifying those files.
- A generic Electron launch of our own unsigned fixture does not prove
  an authentic signed Yandex Windows client would accept a modified ASAR.
- No authenticated account, user music, CELIKOM signed-range backend,
  live queue, volume, native media hotkeys or original Yandex renderer
  was used here.
- No Windows installer, official client patch, debugger or browser
  modification was created.
- Any genuine live official-client experiment requires separate
  explicit owner approval, exact build/fuse compatibility evidence
  and a separate byte-restoration plan, without bypassing integrity.

## Decision after CI

If W9 passes, safe next evidence is a **read-only check of the actual
official Windows binary's embedded ASAR integrity metadata and
static boot/renderer target**, with no account or token reading.
A silent direct patch is NOT an acceptable default.
