# CELIKOM Windows Companion — NEXT-CHAT

**Updated 2026-11-08. W2 real owner report RECEIVED. W3 is a read-only follow-up.**

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
1. Obtain owner's **W3 report** from `START-CELIKOM-PROBE.cmd`.
2. Check exact unchanged hash and W3 counts, especially
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
- Real owner W3 run: **PENDING**. CI validates only synthetic fixtures, not official Yandex source substitution.
