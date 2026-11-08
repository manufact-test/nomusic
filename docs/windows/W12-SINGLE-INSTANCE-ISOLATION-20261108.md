# CELIKOM Windows W12 — official-client launch guard and synthetic single-instance collision

**2026-11-08. Strictly limited to the existing isolated Windows branch.**

## Starting facts (owner's real W10, verified)

- Official Windows 10 x64 Yandex Music EXE: `5.126.1.0`; running.
- app.asar SHA-256: `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`.
- Electron embedded ASAR integrity fuse: `ENABLED`.
- OnlyLoadAppFromAsar fuse: `ENABLED`.
- EXE ElectronAsar integrity resource `PRESENT`, hash `MATCH`.
- In-place ASAR modification is **NO-GO**, rewriting EXE resources or disabling integrity is not approved.
- W11 Windows [CI run 42518263737](https://github.com/manufact-test/nomusic/actions/runs/42518263737) SUCCESS: private inherited CDP pipe inside a disposable test Electron, **6/6** policy tests and **33/33** genuine synthetic single-decoder media assertions. **This was not the official app.**

## Why W12 must not just start official Yandex with --user-data-dir

Electron's `app.requestSingleInstanceLock()` can redirect a second launch into an already-running primary process through the `second-instance` event. A new profile command-line switch is **not proof** that a third-party app uses a separate lock namespace or honors that profile at application startup. The official app's startup sequence, main-process userData location, updater and single-instance behavior are unknown. Starting a signed logged-in user EXE with debug flags risks handing an elevated debugger session to the current account.

Authoritative reference: https://www.electronjs.org/docs/latest/api/app#apprequestsingleinstancelockadditionaldata

## W12 implemented

- `windows-companion/w12/official-launch-gate.mjs`:
  - Pure, read-only **fail-closed** policy. Exact owner W10 EXE/hash/OS and integrity identity required as input.
  - Existing official app running or unknown => explicit blocker.
  - Unknown official single-instance semantics, profile isolation, data guarantees or test-specific consent => blockers.
  - Even if all supplied flags claim success, it **never** grants launching official Yandex, loading its profile, opening a debugger or modifying any EXE/ASAR.
  - No official launcher is implemented or distributed.
- `official-launch-gate.test.mjs`: deterministic negative tests for mismatched identity, altered integrity, running app, lack of isolation, consent and false privilege grants.
- `synthetic-single-instance.cjs`: minimal **our-own** Electron app, requires random nonce, explicit synthetic-only env marker and a newly generated OS-temp directory. On startup it sets `app.setPath('userData', ...)` before `app.requestSingleInstanceLock`. It cannot run Yandex's code or touch a real Yandex profile.
- `run-single-instance-e2e.mjs`: starts real generic Electron from the existing W5 dev-only dependency:
  1. First fixture process with synthetic profile A acquires the lock.
  2. Second fixture process with SAME profile A must fail to acquire the lock.
  3. First process must receive a `second-instance` notification.
  4. Third fixture process with different synthetic profile B must acquire a separate lock.
  5. All children are terminated and temp directories removed.
- W12 CI additions to `.github/workflows/windows-companion-readonly.yml`. Existing W4–W11 + .NET W10 read-only build and all regression tests remain.
- Backup preserved before W12: `backup/windows-w11-verified-before-w12-20261108` at SHA `2e4134554843a416181153d01bc4df06bdf5590f`.

## What W12 CANNOT prove

- That a separate official Yandex 5.126.1.0 process can be started without forwarding to the **already-running, authenticated** primary instance.
- That official Yandex respects `--user-data-dir`, or any CLI flag, before requesting its lock.
- That an untouched official signed EXE allows a private DevTools pipe in a separately consented copy.
- That CELIKOM can intercept native audio on the owner's live official renderer.
- That playing licensed user tracks, account data, cookies or tokens could be inspected safely.

**Do not produce or recommend a real Yandex launcher at this stage.** An actual test needs an independently verifiable identity-isolated, throwaway Windows environment with an offline, non-authenticated copy and explicit opt-in; do not use the current user profile or change official installed files.

## Acceptance evidence

W12 Windows CI is required before calling the synthetic experiment passed. If CI is red, fix the test without weakening the no-go policy. Do not ask the user to re-run W10 or upload their Yandex EXE. No W12 owner ZIP needed.

## Next decision

Verify whether an officially supported plugin/SDK or other permission-limited audio-source interface exists for Yandex Music Windows 5.126.1.0. If no supported seam is demonstrated, record Windows live client as **blocked**. Product must never silently fall back to a second music player, disable integrity or expose authenticated CDP. Any attempt at a separate official-app copy is a new consent-and-threat-model gate, not implied by synthetic W12 success.

## Verified W12 Windows CI — 2026-11-08

- Source commit \`89c648af08c2016cb49ce2605cd96cd8ccf10330\`.
- [Actions run 42520309048](https://github.com/manufact-test/nomusic/actions/runs/42520309048):
  **SUCCESS** (Windows runner, Node 22, Electron 44.10.2, .NET 10).
- W12 production launch fail-closed policy: **6/6** unit tests, all pass.
  It never grants official EXE launch/debugging/ASAR modification, even
  with seemingly perfect W10 identity and user-consent flags.
- W12 genuine disposable Electron single-instance experiment: **5/5**
  runtime assertions passed:
  - first generic fixture process with test profile A acquired lock;
  - second with same profile A was denied as independent player;
  - primary A received the \`second-instance\` forwarding event;
  - third with separate test profile B acquired independent lock;
  - no second player/profile confusion, no official Yandex process.
- Existing W11 private pipe **33/33**, W7+W8 native error recovery
  **33/33**, W5 native audio **35/35**, W9 real generated ASAR
  copy restore, W6 **15/15**, and W10 .NET offline safety tests passed.
- Backup ref **before W12**:
  \`backup/windows-w11-verified-before-w12-20261108\`
  at \`2e4134554843a416181153d01bc4df06bdf5590f\`.
- **No official Yandex application process was started, debugged, modified,
  or inspected live.** The official Windows single-instance mechanism
  is still unverified, and the owner W10 report already proves ASAR-only
  patches violate the enabled integrity check.
- No owner W12 ZIP is necessary. Do not ask for another W0–W10 scan.
- **Next gate is real official-app feasibility, not W13 more synthetic
  success:** locate a genuine supported, permission-limited source
  integration interface. If none exists, document Windows native
  integration as BLOCKED. A separate test of the official signed EXE
  needs explicit narrowly scoped risk review/owner approval and must
  guarantee not to forward into their logged-in running instance.
