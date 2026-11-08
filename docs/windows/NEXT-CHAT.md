# W14 SDK packaging step

Added a disabled PulseSync add-on package using published @pulsesync/addon-sdk 0.18.0, with Windows CI build. Its actual API shape is exercised at *build-time*, not in an installed Yandex client; no source request or account data. CI outcome must be observed before claiming build pass.

---

# W14 code checkpoint (2026-11-09)

Implemented first **PulseSync SDK candidate source-only CELIKOM controller** in `windows-companion/w14/source-controller.mjs` and 11 Node safety tests in `source-controller.test.mjs`; added Windows CI step. No live app modified or test installed. Read `windows-companion/w14/README.md` for audit and blockers. This is not proof that real modified Yandex works. Initial CI run 42526191317 started on commit 7e5932b; the follow-up W14 code fixes SDK-error false-positive reporting. Verify the latest commit CI separately.

---

# CELIKOM Windows Companion — current NEXT-CHAT, W14 revised scope (2026-11-08)

**LATEST PRODUCT DECISION:** The owner explicitly allows considering a disclosed modification of the official Yandex Windows client to make a real CELIKOM Companion. The player, queue, pause/seek/next and output remain in Yandex; **no second audio player**, no disabled Windows protection, no stealth security bypass. Read [W14 approach and safety plan](W14-MODIFIED-CLIENT-PATH-20261108.md) before W13.

**W13 remains a correct NO-GO only for the prior requirement that the official 5.126.1.0 installation must stay unmodified.** Do not keep freezing the entire Windows project based on an obsolete requirement. W10 actual ASAR integrity is still enforced. W14 proposes auditing PulseSync v2.1.5 (release says 5.126.1, but notes spoofing version from 5.125.3), and separate commercial permissions for PulseSync Client; MIT on PulseSync-mod does not grant this.

**Next task:** actionable PulseSync host/addon audit and a version-pinned, reversible, security-preserving **real-client** integration test plan. Owner's explicit test-specific approval is required before any actual modification/installation on Yandex. No owner test executed; no new claims of real native audio. Preserve both backup refs and do not touch shared branches/files.

---

## W13 handoff and W0–W12 history (see W14 above for current instruction)

# CELIKOM Windows Companion — current NEXT-CHAT, W13 decision (2026-11-08)

**Current Windows branch:** `experiment/windows-companion-integration-20261108` in `manufact-test/nomusic`.

**W13 VERDICT: NO-GO / BLOCKED for source replacement in the owner's unmodified official Yandex Music 5.126.1.0 under strict existing constraints.** This is a decision on available evidence, not a proof that all conceivable private interfaces are impossible.

**Read first:** [W13 final decision](W13-OFFICIAL-CLIENT-INTEGRATION-DECISION-20261108.md). This supersedes older 'next experiment' suggestions below.

### What was really verified
- Real owner's official client 5.126.1.0, Windows 10 x64; packaged ASAR SHA-256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`; W10: embedded ASAR integrity ENABLED, OnlyLoadAppFromAsar ENABLED, PE resource PRESENT/MATCH. **Never edit installed EXE/ASAR.**
- W5–W12 Windows CI results apply to isolated GENERIC Electron fixtures and public web Yandex source classes, **not** to authenticated official Windows application. W12 CI [42520309048](https://github.com/manufact-test/nomusic/actions/runs/42520309048) SUCCESS, 6/6 + 5/5 synthetic checks.
- PulseSync add-on API is real but requires a separately modified client runtime. Electron `loadExtension` cannot be triggered externally without host cooperation. Windows media transport and OS audio effects cannot select a source inside the Yandex decoder. Unrestricted CDP/debugging of authenticated client is forbidden. No independently verified official source-plugin API found for exact owner version.

### Next actions: NOT another synthetic Windows test
- Freeze native Windows Companion integration/installer/UI as BLOCKED. No W14 laboratory iteration, no zip to owner, no repeat diagnostics, no official launch.
- Recommend using existing browser-extension CELIKOM for browser-based Yandex Music on Windows — explicitly **not** native Windows-client integration.
- Reopen only if a genuine Yandex/vendor-supported permission-limited source provider is documented and validated, or if owner **explicitly changes constraints** to consider a third-party modified-client dependency after independent security/commercial review.
- Any new official binary/profile/renderer test first requires a separate precise safety proposal and owner approval. No production, server, Android, extension changes.
- Keep backup refs `backup/windows-w11-verified-before-w12-20261108` and `backup/windows-w12-verified-handoff-20261108` untouched.

### W13 delivery
W13 research + documentation only; no executable or new CI claim. No action needed from owner unless they choose a revised product constraint or bring a supported vendor SDK.

---

## Archived earlier handoffs, W0–W12 (historical; superseded for future actions)

# Historical CELIKOM Windows Companion — NEXT-CHAT (W0–W12)

**Updated 2026-11-08. Owner W10 ASAR integrity ENABLED/MATCH, direct ASAR patch NO-GO. W11 and W12 verified Windows CI. Next: W13 genuine official-client feasibility go/no-go.**

## Objective
Official Windows Yandex Music is the ONLY owner of audio, pause, seek, next, queue,
volume and native player state. CELIKOM should substitute the selected source,
not run its own playback clock. Reuse existing CELIKOM auth/approved catalog,
subscription and short-lived signed Range API without editing backend.

## Strict boundaries
Repository `manufact-test/nomusic`, dedicated branch
`experiment/windows-companion-integration-20261108`.
Allowed paths: `windows-companion/**`, `docs/windows/**`,
`.github/workflows/windows-companion-readonly.yml`.
Do NOT edit browser extension, Android, website, server, production releases,
other people's branches, or the frozen desktop 0.4.73 archive.
No installation or patching of official Yandex until exact compatibility,
independent rollback and explicit owner consent. Never extract Yandex tokens.

## Verified real owner machine (W0/W1/W2)
- Windows 10 `10.0.19045.0`, x64; official Yandex 5.126.1.0 is running.
- `%LOCALAPPDATA%\\Programs\\YandexMusic\\Яндекс Музыка.exe`.
- Electron ASAR `YandexMusic` 5.126.1; 54.96 MiB, `index.js` exists.
- ASAR SHA-256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`.
- W1: 48 inspected JS, BrowserWindow and Webpack found; file-info marker absent.
- W2: `Topology state: OK`, `Owner W1 archive identity: MATCH_OWNER_W1`.
- W2: 1117 packaged JS; only 100 scanned; HTML 84; preload-named JS 4.
- W2: loadURL, loadFile, preload, Yandex Music/static hosts, local renderer,
  `getFileInfo`, batch source markers, Webpack and updater: ALL TRUE.
- W2: ASAR unpacked folder FALSE; scan INCOMPLETE.
- These are static hints; NONE proves live authenticated source interception.
- User has not installed an integration; official app remains unchanged.

## W3 source-seam analysis and offline contract
W3 extends the same read-only Win x64 probe. It inventories more packaged
JS, correlates file-info identifiers/API endpoints with Webpack/preload/renderer
and startup loaders **by same-file counts only**; exports no script text, file
names, URL literals, credentials or audio. It also tests a pure source gate on
synthetic data: exact ID, entitlement, duration, validated file, signed HTTPS
origin/expiry, Stop/Original, and generation cancellation. No real player
interaction or patch is part of W3.

Code: `windows-companion/Celikom.Core/AsarSourceSurvey.cs`,
`AsarSourceSurveyReport.cs`, `SourceSwapGate.cs`.
Read `docs/windows/W3-SOURCE-SEAM-READONLY-20261108.md` and CI result.

## Next decision
1. W3 report RECEIVED — no repeat owner action needed.
2. CONFIRMED unchanged hash and W3 counts, especially
   `Source marker + Webpack marker in SAME file`, loader hints,
   and survey completeness. They are heuristics, not executable hook evidence.
3. If W3 supports a narrow packaged seam, build a SMALL independent Electron
   test fixture with synthetic approved audio. Prove single native decoder,
   pause/seek/next, exact-ID fencing, signed URL/Range and Stop/Original.
   If renderer is remote, use isolated public asset fixture or documented
   supported SDK route; do not inject user Yandex session or auto-patch.
4. Only propose touching the installed Yandex after a separate explicit
   owner approval and byte-checked, tested backup+restore plan. An unsupported
   client must play original without any CELIKOM hook.
5. For source background consult `docs/windows/ARCHITECTURE.md`,
   `PRODUCT-DESIGN.md`, `ROADMAP.md`,
   `docs/desktop/NATIVE-SOURCE-RESEARCH-2026-11-08.md` (READ-ONLY
   on `experiment/desktop-native-source-20261108`).
   Browser native-source fixture passed isolated tests but **was not** a
   reliable authenticated Windows integration; do not copy blindly.

## Reporting
Russian, concise. Distinguish CI fixture success from real user Windows
behavior. Don't claim source substitution without audible owner acceptance.

## Verified W3 build / delivery
- Source commit: `3b91d8fec9df1402447075c08ca4352ba163704d`.
- [CI run 42507700601](https://github.com/manufact-test/nomusic/actions/runs/42507700601): **SUCCESS** (.NET build, synthetic checks, native Win x64 publish, ZIP artifact).
- Artifact ID `13628595552`; ZIP `CELIKOM-Windows-Probe-W3.zip`.
- ZIP SHA-256 `4fbbe806a859a091ceac376ff9932eec9f87610b37b1b7eb819ead632f7b350b`; archive CRC checked; contains one EXE and `START-CELIKOM-PROBE.cmd`.
- ChatGPT Library: `/CELIKOM/Windows/Test/CELIKOM-Windows-Probe-W3.zip`, library ID `libfile_13cdbbfeb5588191b1ba18859aadba26`.
- Real owner W3 run: **RECEIVED, PASS read-only**. 1117/1117 JS inspected, no skips; `getFileInfo` in 19 packaged files, batch in 3, `GetFileInfoResource` in 19, endpoint strings in 2. No installed integration; original works. CI validates only synthetic fixtures, not official Yandex source substitution.

## W4 isolated adapter (no owner installation)
- See `docs/windows/W4-SOURCE-ADAPTER-ISOLATED-20261108.md`.
- Code `windows-companion/bridge/w4-source-resource-adapter.mjs` and
  `w4-source-resource-adapter.test.mjs`; W4 Windows CI uses Node 22 tests.
- Implements exact-ID, original-first single/batch resource wrappers,
  time-limited prepared Blob URLs, cancellation, Stop/Original and cleanup.
- Nothing hooks the installed Yandex client, touches browser/Android/backend,
  or plays independent audio. Source response contract tests are **synthetic**.
- Next proof: isolated Electron fixture with actual pinned Yandex resource
  class and synthetic audio; then assess patch/rollback strategy. DO NOT ask
  owner to reinstall or repeat diagnostics absent a new safe user action.

## Verified W4 CI
- Source commit `a47d1c847da62dde42490da3be4ec4f9f8d06661`.
- GitHub Actions [42509525224](https://github.com/manufact-test/nomusic/actions/runs/42509525224): **SUCCESS**; W4 Node synthetic adapter stage passed, W3 .NET build/safety stages passed.
- 17 named W4 synthetic tests cover v1/v2, mixed batch, wrong ID, delayed Next, abort, Original, duplicate-track preference, double hook, Stop, expiry, unsafe asset, original failure/error, unsupported prototype, cleanup and secret-safe diagnostics.
- No new owner-side diagnostic is needed; do not confuse CI fixture passing with live audio.

## W5 Electron source-level media fixture
- Detailed scope: `docs/windows/W5-ELECTRON-ISOLATED-20261108.md`.
- `windows-companion/w5/**` contains pinned public Yandex JS asset hashes,
  test-only factory preparation, offline signed Range fixture, isolated
  Electron main/renderer tests; uses original W4 in-memory source adapter.
- Tests actual **public web** Yandex resource/source classes in a genuine
  Electron audio renderer with generated synthetic MP3; **NOT** the owner's
  official Yandex Windows 5.126.1.0 binary, and no user tokens.
- Assert native one-decoder playback, pause, seek, track change, late seek,
  a delayed stale request, explicit original reacquisition, Stop and
  signed URL 206/403/416. If CI fails, identify and fix without weakening
  real assertions.
- W5 is NOT a Windows CELIKOM installer. No owner action/ZIP unless a
  subsequently approved, reversible live-client test can be designed.
- Check W5 Windows workflow result before claiming verified.

## W5 validated, next stage is official-client integration feasibility

- W5 source `bfe5ce7ca0c31780812de19f2de7e96eda06d9da`.
- [CI run 42511997271](https://github.com/manufact-test/nomusic/actions/runs/42511997271): **SUCCESS**, **35/35 runtime assertions** with Electron 44.10.2 and original pinned **public Yandex web frontend** resource/source classes.
- Covers actual Electron decoder (one media element), native pause/seek,
  Next to longer MP3, late seek, delayed-response fencing, explicit original
  reacquisition, Stop, synthetic signed fixture 206/403/416 and cleanup.
- First W5 CI showed false success despite native original decoding failure.
  Both the synthetic signed-URL suffix interaction and actual nonzero CI exit
  were fixed in the follow-up commit. Do not erase this history.
- Public Yandex frontend `v4.1726.0` is not proven identical to the
  renderer running inside official owner's Windows `5.126.1.0`.
- **W5 is NOT an installable companion**. No new download for owner yet; no
  installed Yandex, browser, Android, server or shared release changes.
- Next real gate: safe method to attach to official renderer, exact version
  compatibility, native player ownership/cache lifecycle and verified
  byte-for-byte rollback. Must secure owner's explicit approval BEFORE
  patching installed Yandex or accessing user sessions.

## W6 safety work / next checkpoint

- Read `docs/windows/W6-ROLLBACK-SAFETY-20261108.md`.
- `windows-companion/w6/compatibility.mjs`: owner-specific strict identity
  gate; matches real W3 identity but **never grants official file writes
  or live renderer attachment**. Version/hash/process mismatch => no go.
- `windows-companion/w6/rollback-fixture.mjs` + Node tests: temp
  **synthetic-only** backup, staged change, simulated power loss, restore,
  outsider edit/backup corruption => hard stop. NEVER takes installed
  Yandex path as a write target.
- Read-only competitor inspection exposed possible EXE hash rewrites for
  Electron ASAR patching. Do not reuse this blindly; official integrity,
  signing and update implications remain unproven.
- W6 changes are only Windows paths and Windows CI workflow. Verified Windows CI run 42513323017: W6 15/15, W5 35/35, W4 and W3 regression PASS.
- W6 does not produce any owner installer. Next technical gate is a
  defensible official Windows renderer attachment model, with formal
  opt-in and truly byte-verified restore; if impossible report NO-GO.

## W6 verified handoff
- Commit `75a8e407a8528b13de9db37198f5c4807e49bb12`,
  [Windows CI 42513323017](https://github.com/manufact-test/nomusic/actions/runs/42513323017) SUCCESS.
- W6 **15/15** synthetic OS-temp backup/recovery tests.
- Windows case canonicalization bug in initial CI corrected; initial failed
  run 42513155758 must not be described as a clean first pass.
- W5 regression **35/35** real Electron fixture runtime assertions.
- W6 is not a genuine Yandex app.asar patcher nor an owner-installed recovery
  tool. Do NOT ship a W6 test ZIP as though it proves real app integration.
- Next: evaluate an attach seam in the actual official Electron process
  without unsafe binary modifications; if no safe supported method exists,
  document the limitation and require explicit owner opt-in for a separately
  verified reversible test. No unapproved access to Yandex account data.

## W7 external sidecar attachment research

Read `docs/windows/W7-EXTERNAL-ATTACH-FIXTURE-20261108.md`.
The experiment adds `windows-companion/w7/` with exact nonce/URL/path CDP
gate, a standalone disposable Electron window containing pinned public
Yandex Webpack factories, a separately spawned Node sidecar using only
Runtime.enable/Runtime.evaluate, and a test-only dynamic W4 activation
that exercises one native decoder and Stop/Original. **Production decision
always denies enabling a DevTools port on the owner's authenticated Yandex.**
No installed Yandex files were changed; synthetic client only.
CI result must be confirmed separately; a green W5 does not imply W7 passed.
No owner ZIP and no repeated W0–W3 scans are needed here.

## W7 verified, W8 underway

- [W7 Windows CI 42514425074](https://github.com/manufact-test/nomusic/actions/runs/42514425074)
  **SUCCESS**: external Node sidecar attached to a non-authenticated
  standalone Electron 44 test renderer and dynamically activated W4
  against original pinned public web Yandex resource/source classes.
  **28/28** actual fixture assertions. Never enable a debugger on
  the user's authenticated installed Yandex; this is fixture-only.
- W8 pure recovery controller and synthetic unit tests:
  `windows-companion/w8/native-original-recovery.mjs` and
  `native-original-recovery.test.mjs`. Exact track, one-shot, no loops,
  original-first, snapshot pause/seek, Next/Stop fencing, no second decoder.
- W8 extends the **W7 actual Electron** CDP fixture: cause a real
  decoder failure using corrupt synthetic MP3, auto-reacquire original
  through W4/Yandex public class on the SAME native element and restore
  position/play state. Do not count this as passed until CI verifies.
- Read `docs/windows/W8-NATIVE-ERROR-RECOVERY-20261108.md`.
- No owner installation or test ZIP. Only Windows working branch.
- Real official Windows renderer attachment remains unproven and requires
  an explicit opt-in after safety and rollback assessment.

## W8 VERIFIED acceptance: no owner action

- Commit `8e85da515b20f9c9b825d048aef6eaec5dfe106f`.
- [CI 42514969269](https://github.com/manufact-test/nomusic/actions/runs/42514969269): **SUCCESS**, W8 contract **12/12**, W7+W8 live synthetic media inside Electron **33/33**, W5 baseline **35/35**, W6 **15/15** (plus W4/W3).
- One actual Chromium decoder reports error for corrupted synthetic MP3;
  W8 auto-reacquires the corresponding original through W4 and the
  pinned public Yandex source class, restoring seek/pause state on the
  SAME `HTMLAudioElement`, without overlay player or retry loop.
- This is still **NOT a real Windows Yandex integration**. W7 CDP
  exposes unsafe broad debugger power and MUST NOT be enabled in a
  customer/authenticated Yandex session.
- Safe next work: evidence of official Windows 5.126.1.0 native attachment
  API or independent opt-in, version-pinned and truly reversible
  integration feasibility, with explicit consent before modifying any
  installed file. Existing W3 owner snapshot remains the sole real-client
  evidence; do not ask for W0-W3 scans again.

## W9 generated ASAR copy & rollback with actual Electron launches

- `docs/windows/W9-ASAR-COPY-ROLLBACK-20261108.md` defines the
  strict experimental boundary. ASAR integrity may be embedded in
  the Windows EXE's resources and checked by the Electron fuse.
  If unknown, any official-client modification is **NO-GO**.
- `windows-companion/w9/asar-copy-lab.mjs` creates only its own
  temp generated ASAR, independently backs it up, hashes, repacks
  modified **copy**, simulates interrupted install/restoration
  and refuses third-party changes.
- `run-boot-e2e.mjs` must launch a REAL generic CI Electron
  44 against an original synthetic `app.asar`, then modified copy,
  then byte-restored original, verifying absence of hook after restore.
- This is physical copy testing, **not an actual user's Yandex file
  backup, installation, live renderer interception or consent**.
- W9 Windows CI result must be inspected, not assumed.
- After W9, a real read-only integrity observation on the actual
  installed Yandex EXE could resolve current blockers, but do not
  ask owner to repeat W0–W3 or issue a patched client unapproved.

## W9 verified; W10 actual official binary read-only evidence

- W9 [CI 42516545399](https://github.com/manufact-test/nomusic/actions/runs/42516545399) SUCCESS.
  **15/15** generated ASAR copy crash/restore tests; actual generic
  Electron boots original generated ASAR, modified copy with test-only
  hook, then byte-restored original with no hook. No official Yandex touched.
- First W9 CI failure 42516425634 was an `await` omission in
  fixture file existence; fixed in `145dc26b8d0daef3b8ff24f3446f3016f89709fa`.
- W10 code: `windows-companion/Celikom.Core/ElectronIntegrityReadOnly.cs`,
  with tests in `Celikom.Core.Tests/Program.cs`. Directly **reads only**
  documented Electron V1 fuse 4 (embedded ASAR integrity), fuse 5
  (only load ASAR) and optional Windows PE resource
  `Integrity/ElectronAsar`; compares with actual app.asar header SHA.
- W10 Probe rechecks owner W3 archive SHA and W10 integrity result,
  without repeating the full 1117-file W3 source scan.
- W10 is NOT an installer, source hook or signed official Yandex patch;
  does not enable remote debugging or access app accounts. Any missing
  or unknown evidence is NO-GO for writing official binary.
- Source details `docs/windows/W10-EXE-INTEGRITY-READONLY-20261108.md`.
  New W10 CI and owner artifact to be verified/delivered before asking
  the owner to run. Do not claim passed before CI result is real.

## Verified W10 package and next action

- [Actions 42517089821](https://github.com/manufact-test/nomusic/actions/runs/42517089821)
  **SUCCESS**, commit `507911ac52bb5886ccd2f461ab56a6fc17bafc95`.
- `CELIKOM-Windows-Probe-W10.zip` 32909420 bytes, sha256
  `d021bb12a3436e69c403ea5c06c5e981b07b7d1a3008da93d6adc039a9b8e327`.
  CRC verified, contains EXE and CMD only.
- Uploaded to Library:
  `/CELIKOM/Windows/Test/CELIKOM-Windows-Probe-W10.zip`,
  library ID `libfile_65577f120f4c8191adcf345a9406d5dd`.
  GitHub run artifact ID `13631553715`.
- Owner runs read-only W10 `START-CELIKOM-PROBE.cmd` and provides
  `CELIKOM-Windows-report.txt`. NEVER request original credentials
  or installed app binary upload. No installed files changed.
- W10 reads Electron fuse sentinel (official V1 indexes 4/5) and
  optional Windows `Integrity/ElectronAsar` resource, comparing
  documented hash with ASAR header. **EXE integrity result on actual
  owner Windows not yet observed**. W10 CI validated only synthetic
  fake PE + packaged tool, not owner's official client.
- Important: an enabled integrity fuse matching resource is a clear
  NO-GO for modifying official ASAR. Fuse disabled / resource absent
  still does NOT prove an approved live plugin interface exists.

## W10 real owner finding — ASAR patch is NOT viable

Official Windows 10 x64, Yandex EXE \`5.126.1.0\`, ASAR
\`5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215\`
MATCH W3. W10 reports: \`V1_FOUND\`, Embedded ASAR Integrity
\`ENABLED\`, OnlyLoadAppFromAsar \`ENABLED\`, EXE
\`ElectronAsar\` resource \`PRESENT\`, resource hash \`MATCH\`.
Official app currently running; no CELIKOM integration installed.
**DO NOT patch installed Yandex app.asar**. Modifying EXE resource
to evade validation compromises signature/update and is NOT approved.
Never say a synthetic copy boots means actual official signed client
patch works; both fuses on the actual owner's machine are now confirmed.

## W11 no-port inherited debug pipe experiment

Read \`docs/windows/W11-PRIVATE-PIPE-FEASIBILITY-20261108.md\`.
The existing W7 fixture supports \`CELIKOM_W11_PIPE_ONLY=YES\`
plus a random nonce and separate temporary user-data directory.
It does not create a TCP DevTools port in this CI-only mode.
\`windows-companion/w11/pipe-protocol.mjs\` provides strict JSON-NUL
FD3/FD4 CDP framing, allowlisted methods, nonce-bound localhost
target matching, bounded response sizes/timeouts and fail-closed errors.
\`windows-companion/w11/run-pipe-e2e.mjs\` must launch isolated
generic Electron with \`--remote-debugging-pipe\`, then externally
attach using only inherited pipes and run W7+W8 actual native
media regression. Any failure must fail CI; NO port fallback allowed.
No official Yandex app/EXE/ASAR, accounts, or user data accessed.
**CI outcome not yet confirmed**; do not misrepresent green until
the actual Windows job finishes and logs show private-pipe PASS.

Following W11, only consider a carefully permissioned non-authenticated
sandbox experiment on a COPY of an official app with explicit consent
and without disabling integrity/signature safety. The normal installed
client remains untouched. Never request another W0-W10 report.

## Verified W11 — secure transport research, not a finished client

[Actions 42518263737](https://github.com/manufact-test/nomusic/actions/runs/42518263737)
SUCCESS, source `a953ed992b4952bbcc7aec725c659d2e98010002`.

- W11 6/6 pipe policy tests PASS. Real Electron 44 inherits
  private standard FD3/FD4 CDP `--remote-debugging-pipe`,
  no TCP debugger port, clean disposable profile. External Node
  sidecar attached and dynamically activated W4/W8 against the
  pinned original public web Yandex source/resource classes.
- W11 actual native single-decoder playback and error recovery
  **33/33**, W7 equivalent **33/33**, W5 **35/35**. All existing
  W4/W6/W8/W9/W10 offline tests/build regression passed.
- **Never conflate** success of private pipe on a disposable
  test renderer with permission to debug an authenticated official
  Yandex Music Windows app. CDP privileges remain unrestricted
  inside that one renderer.
- W10 actual official app fuse+ASAR resource both ENABLED/MATCH:
  modifying installed official app.asar without EXE changes is a
  definite NO-GO. EXE rewriting/signature changes are not approved.
- No safe permission-limited documented official audio-source API
  has been verified. No further proxy audio clock or second player.
- The next concrete research stage would require a separately
  authorized, clean-profile, read-only **official Windows client**
  compatibility observation using a test-only private pipe. This
  would launch a separate instance, must preserve official install
  and fail closed on single-instance handoff, account screen or
  app update; do NOT do it without explicit owner permission.
- No new test ZIP required at W11 stage; installed client untouched.

## W12: same-profile collision is a risk, not proof of official separation

Read `docs/windows/W12-SINGLE-INSTANCE-ISOLATION-20261108.md`.
- Current owner's installed official Yandex is RUNNING and authenticated state is not to be inspected. No official EXE was launched for W12.
- Electron `requestSingleInstanceLock` can forward second launch into existing primary. Do not assume `--user-data-dir` ensures separate official Yandex profile/process.
- `windows-companion/w12/official-launch-gate.mjs`: real app launch / signed ASAR changes / opening authenticated debugger explicitly forbidden. Pure synthetic tests check refusal.
- W12 disposable generic Electron fixture experiments with same synthetic profile vs different synthetic profile and real `second-instance` forwarding; Windows CI **VERIFIED PASS**.
- W12 tested code restricted to `windows-companion/w12/`, `windows-companion/w5/package.json`, workflow and docs.
- Pre-W12 verified backup ref: `backup/windows-w11-verified-before-w12-20261108` at `2e4134554843a416181153d01bc4df06bdf5590f`.
- Do NOT ask owner to run another W10 read-only scanner. No new owner ZIP needed for W12. No live source swap yet.

## W12 Windows CI accepted — owner handoff (2026-11-08)

- Source commit \`89c648af08c2016cb49ce2605cd96cd8ccf10330\`.
- [CI run 42520309048](https://github.com/manufact-test/nomusic/actions/runs/42520309048): **SUCCESS**.
- W12 fail-closed official launch policy **6/6**; real GENERIC Electron
  test \`run-single-instance-e2e.mjs\` **5/5** assertions passed:
  first synthetic profile A owns lock; second with A is blocked and
  forwards \`second-instance\` to A; independent profile B gets own lock.
- W11 private inherited pipe **33/33**, W7+W8 **33/33**,
  W5 **35/35**, W9 actual generated ASAR original/copy/restore
  boot verified, and earlier .NET/Node regression all PASS.
- W12 has **NO official Yandex launcher**; \`official-launch-gate.mjs\`
  deliberately returns NO_GO even with W10 identity and consent.
- No official app process was launched, no Yandex account or profile
  inspected, no installed EXE/ASAR, browser, Android, website, backend
  or production branch changed. No owner W12 ZIP needed.
- Pre-W12 backup \`backup/windows-w11-verified-before-w12-20261108\`
  -> \`2e4134554843a416181153d01bc4df06bdf5590f\`.
- W10 definitive actual owner: ASAR SHA matches, Electron integrity
  \`ENABLED\`, ASAR-only \`ENABLED\`, PE resource \`PRESENT/MATCH\`.
  **NEVER** patch installed ASAR or flip fuses/EXE hash.
- New concise next-chat entry message is in
  \`docs/windows/W12-NEXT-CHAT-PROMPT-20261108.md\`.

### Next phase W13 — stop making hypothetical fixtures

1. Read project docs and W10–W12 evidence, inspect current branch.
2. Investigate a **supported, limited, noninvasive** native desktop
   audio-source seam in the official Windows Yandex build, including
   how it would retain Yandex's own decoder/pause/seek/queue.
   Do NOT assume public web source classes == installed official ones.
3. Treat W11 private CDP as privileged debugger and W12 synthetic
   profiles as a risk demonstration, **NOT product approval**.
4. If no supported or independently verifiable safe seam exists,
   state clear NO-GO/BLOCKED, stop endless fixture work, offer
   realistic options without a second player.
5. Never launch current owner's authenticated Yandex with debug
   flags, never modify signed official EXE/ASAR, never extract
   tokens/cookies or duplicate paid production systems. An
   actual isolated signed app test must be separately scoped and
   explicitly approved after a safety review.
6. Keep work on Windows branch and preserve backup refs.
7. Owner prefers *large chunks* and concise factual status, no
   ten-minute stops, no repetitive W0–W10 probe requests.
