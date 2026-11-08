# W10 — read-only actual Windows executable fuse + ASAR integrity resource

**2026-11-08. This is NOT a CELIKOM source injector, patch or installer.**

## Why W10, not more W3 source scans

Owner's actual Yandex Music 5.126.1.0 / Windows 10 x64 app
has already been inspected in W0–W3, with ASAR SHA-256
\`5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215\`
and **1117/1117 JS scanned**. W5–W8 prove the original public
Yandex web resource/source classes can drive one native Electron media
element in a disposable test environment. W9 passed genuine ASAR
boot/modified-copy/reboot rollback with **our own unsigned Electron app**.

But the user's **official Yandex executable** might enforce ASAR integrity
using a Windows PE \`Integrity/ElectronAsar\` resource, and Electron
\`EnableEmbeddedAsarIntegrityValidation\` fuse (V1 index **4**).
\`OnlyLoadAppFromAsar\` fuse is V1 index **5**. Unknown integrity
is a NO-GO for any attempt to rewrite official archives. These are
documented by Electron and \`@electron/fuses\`.

Official sources:
- https://www.electronjs.org/docs/latest/tutorial/asar-integrity
- https://www.electronjs.org/docs/latest/tutorial/fuses
- https://github.com/electron/fuses/blob/main/src/config.ts

## W10 single new user-side observation

\`windows-companion/Celikom.Core/ElectronIntegrityReadOnly.cs\` uses
normal **read-only Windows file handles** on the exact already detected
official executable and adjacent \`resources/app.asar\`. It never reads
browser cookies, process memory, Yandex session or private music data.

1. Streams the EXE without exporting bytes. Looks for the exact
   documented Electron fuse sentinel and safely parses V1 wire
   (ASAR validation and ASAR-only lookup states). Missing, removed,
   malformed or multiple sentinels => UNKNOWN, not falsely disabled.
2. Reads the ASAR JSON **header only**, calculates SHA-256 without
   exporting source code. The W1 archive identity also rechecks exact
   SHA-256; no repeat full W3 1117-file source scan.
3. On Windows, reads **only** the named optional
   \`Integrity / ElectronAsar\` PE resource via
   \`LoadLibraryExW\` as DATAFILE / IMAGE_RESOURCE (never executes
   the target EXE). Exports presence and whether its documented
   embedded hash matches the ASAR header; never the JSON body.
4. Redacts full filesystem paths, tokens, account data, raw executable
   content, filenames, downloaded media and URL literals.
5. Prints a concise W10 status after existing Windows discovery.
   App files and running processes are **unchanged**.
6. All outcomes, including "DISABLED", are evidence only. They **never**
   authorize editing official binaries or attaching a debugger.

\`windows-companion/Celikom.Core.Tests/Program.cs\` tests synthetic
sentinel at a 128 KiB streaming boundary, V1 index decoding,
missing/ambiguous/removed fuses, invalid ASAR header,
synthetic resource matches and mismatches, malformed JSON,
and fail-closed result for a fake non-PE file.

**W10 executable output:** compiled by the same dedicated Windows
GitHub CI, published as a single-file win-x64
\`CELIKOM-Windows-Probe.exe\` plus
\`START-CELIKOM-PROBE.cmd\`. It is a standalone utility, not an
installer or service. It requires no account login and makes no
network requests. It includes no Yandex code.

## Gate / next real-client step

If actual owner W10 reports embedded integrity ENABLED and resource
matches, **modifying the official ASAR would be expected to break
integrity verification; NO-GO for in-place patching**. Do not disable
fuses, patch the executable signature or change checksum resources.

If those are absent/disabled, still do **not** assume an approved
plugin/source mechanism exists: official runtime media ownership,
asset provenance, version compatibility, updater behavior,
app signing and legal permissions remain unproven. Any later
installed-client experiment needs separate explicit user approval and
a demonstrated real backup/restore plan.

W10 must not be described as working real source replacement.

## Verified W10 Windows CI / delivery — 2026-11-08

- Source commit `507911ac52bb5886ccd2f461ab56a6fc17bafc95`.
- [Actions run 42517089821](https://github.com/manufact-test/nomusic/actions/runs/42517089821):
  **SUCCESS**. Windows .NET build with warnings as errors and synthetic
  W10 fuse/PE-resource tests passed, alongside W9 physical ASAR E2E and
  W4–W8 regressions (W5 35/35; W7+W8 33/33).
- W10 published win-x64, self-contained single-file probe ZIP: GitHub
  artifact `13631553715`, name `celikom-windows-w10-integrity-readonly`.
- Final archive `CELIKOM-Windows-Probe-W10.zip`, 32909420 bytes,
  SHA-256 `d021bb12a3436e69c403ea5c06c5e981b07b7d1a3008da93d6adc039a9b8e327`.
  ZIP CRC verified, exactly two files:
  `CELIKOM-Windows-Probe.exe`,
  `START-CELIKOM-PROBE.cmd`.
- Uploaded and independently listed in ChatGPT Library:
  `/CELIKOM/Windows/Test/CELIKOM-Windows-Probe-W10.zip`,
  Library file ID `libfile_65577f120f4c8191adcf345a9406d5dd`.
- Real owner W10 EXE fuse/resource report: **NOT YET RECEIVED**.
  Do NOT claim any official app compatibility or source hooking until
  that real observation and later authorized native integration tests.
- Owner test action: extract W10 ZIP, run existing
  `START-CELIKOM-PROBE.cmd` with official app running, return only
  `CELIKOM-Windows-report.txt`. This is read-only and does not
  repeat W3's 1117-file source scan.
