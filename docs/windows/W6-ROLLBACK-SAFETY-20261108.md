# CELIKOM Windows W6 — strict compatibility and synthetic recovery

**Status:** isolated safety development, **not** a Yandex desktop integration or an installer.

## Starting evidence

- Owner's real Windows 10 (19045, x64), official Yandex Music `5.126.1.0`.
- Official Electron ASAR package `5.126.1`, SHA-256
  `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`.
- Owner W3 scanned 1117 / 1117 JS files, found static file-info markers.
- W5 isolated native Electron 44.10.2 + original **public web** Yandex
  resource/source classes: 35/35 runtime assertions, [CI 42511997271](https://github.com/manufact-test/nomusic/actions/runs/42511997271).
- **No proof** these public web factories are the ones currently loaded
  by the official installed Windows 5.126.1.0 client.

## Why a naive patch is not safe

A read-only review of `S4YN3X/FkCensor`'s `internal/asarpatch/asarpatch.go`
(commit `c1b142c03868d0513d48fcb090c7b0564559545b`) shows a route
that rewrites an ASAR entry and adjusts a hash inside the official EXE.
That is third-party implementation research **only**; no code is imported.
Changes to the EXE, installer signature/integrity state or update machinery
would be a significant compatibility and maintenance hazard. Do not
silently adapt the patch, modify checksums, disable integrity mechanisms
or represent it as a proven CELIKOM integration.

## Implemented W6

`windows-companion/w6/compatibility.mjs`
- A strict read-only identity gate for the real owner version/hash/build.
- **Even when matched**, returns `MATCHING_W3_IDENTITY_ONLY`, never
  `mayEditOfficialFiles=true` or `mayAttachToLiveRenderer=true`.
- Any changed EXE version, package version, ASAR digest, OS, architecture,
  missing process or invalid archive makes the identity unknown.
- Static `getFileInfo` markers and W5 tests do not upgrade the result
  to `SOURCE_COMPATIBLE`.

`windows-companion/w6/rollback-fixture.mjs`
- A **synthetic-only, deterministic crash/recovery laboratory**.
- Creates its own temporary `celikom-w6-synthetic-*` directory with
  fixed fake filenames (`synthetic-client.bin`), a unique temporary
  fixture and explicit synthetic marker. **Accepts no Yandex install
  directory or user file paths for modification.**
- Creates a separate backup and verifies original SHA-256, tests staged
  faux replacement, simulated interruption and byte-for-byte restoration.
- On changed active fixture or corrupted backup it **refuses** to replace
  unknown bytes or claim success.
- Simulates interruptions after journal write, after original file parking
  and after replacement promotion; a reopened lab must recover.
- This is a **safety-method test**, not permission or proof of official
  `app.asar` / EXE restoration. Real Windows application signatures,
  file locks, elevated permissions, auto-updates and user data are **not**
  exercised.

`windows-companion/w6/rollback-fixture.test.mjs`
- Negative tests for unsupported versions/hashes and no live-write grants.
- Positive synthetic backup, patch, clean restore, idempotency.
- Simulated crash/restart across install and restoration stages.
- Third-party file changes, bad backup, repeated installation and
  non-temporary arbitrary directory blocked.
- Run `node --test windows-companion/w6/rollback-fixture.test.mjs`.
- Windows GitHub workflow runs W6 before W4/W5 and legacy W3 checks.

## Gates before any genuine official Windows integration

1. Establish a **legitimate, version-pinned way to access the running
   renderer** without disabling security or extracting Yandex credentials.
   Prefer a supported extension/API if one exists. The official client
   currently has no demonstrated supported CELIKOM plugin seam.
2. Independently prove that a load-time adapter can be disabled/unhooked;
   source-only interception must preserve original app player, queue,
   native media controls and access checks. No second audio engine.
3. Decide whether any patching is justified only after reviewing
   app integrity/signing, update behavior, licensing/ToS and a genuine
   Windows backup/restore plan. Any **installed** file modification requires
   explicit owner approval **in a separate step**, exact hash gate and
   byte-checked rollback with failure recovery.
4. If safe attachment is not possible, report **NO-GO**, do not create
   an autonomous player or silently rewrite Yandex's executable.
5. No owner-side W6 ZIP is needed. W6 exercises temporary CI fixtures only.

**Do not call W6 a functioning Windows companion, a patcher, or an accepted
rollback of official Yandex Music.**

## Verified CI checkpoint — 2026-11-08

- Source commit `75a8e407a8528b13de9db37198f5c4807e49bb12`.
- [GitHub Actions run 42513323017](https://github.com/manufact-test/nomusic/actions/runs/42513323017): **SUCCESS** on Windows.
- W6 **15/15** isolated synthetic tests passed (zero failures).
- W4 Node source adapter regression passed; W5 genuine public resource
  classes in isolated Electron 44.10.2 passed **35/35** runtime assertions;
  legacy W3 .NET read-only build/safety/publish also passed.
- Initial [CI run 42513155758](https://github.com/manufact-test/nomusic/actions/runs/42513155758) FAILED W6: strict equality of Windows realpaths
  mistakenly treated Windows canonical path normalization as a symlink.
  Fixed to enforce OS-temp containment using realpath + relative paths,
  lstat symlink rejection, a synthetic-only marker and fixed fake filenames.
  No real client paths were touched.
- **No owner-device rollback tested**, no official app hooks installed,
  no direct source playback in installed Yandex proven, and no user ZIP
  is appropriate for this synthetic-only stage.
