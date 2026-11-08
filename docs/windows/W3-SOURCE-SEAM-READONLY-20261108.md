# W3 — source-seam survey and strict source gate (2026-11-08)

## Why W3
Real owner W2 confirms unchanged Yandex 5.126.1.0 ASAR and packaged
`getFileInfo` / batch string markers. But W2 scanned only 100 of 1117
JavaScript files and did not correlate where its flags appeared. W2 is NOT a
hook or audio-compatibility proof.

## W3 deliverable
- Same read-only x64 native probe; still detects app and prints W0/W1/W2.
- New bounded `AsarSourceSurvey`: up to 96 MiB of JS, 12 MiB/file; counts
  source method, batch, `GetFileInfoResource` and endpoint strings.
- Counts methods/endpoint markers co-located in a single JS with Webpack
  or named preload/renderer. Counts `loadURL` co-located with Yandex host,
  `loadFile` and descriptor hints. Does not dump paths or code.
- Prints scanned/total/skipped for honest completeness.
- New offline `SourceSwapGate`: selects only approved, entitled, duration-
  checked, validated exact-ID candidate using configured HTTPS API origin,
  expiry guard and generation fencing. Stop and Original deny selection.
- Zero active hooks; no media capture, user account/session, patching or
  installed Yandex modifications.
- Synthetic CI tests exercise source/boot hints, redaction and rejection
  of wrong ID, wrong origin, revoked entitlement, expiry, Stop and Next.
  They do not establish live playback or Yandex descriptor compatibility.

## W2 actual report (owner)
`Topology state: OK`; `MATCH_OWNER_W1`; 1117 packaged JS / 100 scanned;
84 HTML / four preload JS; local and remote renderer hints TRUE;
`getFileInfo` and batch TRUE; updater TRUE; ASAR SHA
`5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`.
The owner confirms no intervention was installed.

## Next real-world step
User runs W3 via `START-CELIKOM-PROBE.cmd` with official Yandex running and
returns `CELIKOM-Windows-report.txt`. Evaluate only what W3 actually
observed; a marker does not imply that runtime requests use that code.
Do not begin an official-client patch without a separate owner-approved
backup/rollback plan and compatibility/legal assessment.
