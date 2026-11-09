# W22 — independent native file-info source adapter (internal source-only)

**Goal:** replace PulseSync-specific playback SDK dependency with a CELIKOM-owned,
source-only resource adapter while keeping the regular desktop Yandex Music
UI, queue, audio decoder and transport controls.

## Actual source delivered

- \`native-resource-adapter.mjs\`: independent JavaScript adapter for the
  resource \`getFileInfo\` / \`getFileInfoBatch\` API shape demonstrated by
  the MIT FkCensor implementation. It has no PulseSync runtime/SDK import,
  third-party audio database, Yandex account access or second player.
- CELIKOM source grants are checked through the already-owned W15
  \`validateCelikomGrant\`: exact ID, origin, entitlement, signed media URL and
  expiration. Source MIME is preserved by the W15 .NET bridge (MP3 and M4A).
- Single request has a bounded deadline (1.25 seconds by default); future
  playback should not stall forever when CELIKOM backend hangs.
- Next/Stop invalidate pending requests; unsupported inputs fall back to
  native original. A batch uses cached approved grants only.
- \`dispose()\` restores native resource methods; no pause/seek/Next or
  playlist control hooks are installed.
- CI compiles and tests W15 bridge, W15 Node controller and this W22 adapter
  with 13 resource-contract scenarios. This is an **offline contract test**,
  not proof of real audio, installation into Yandex, valid original signature,
  Defender/SmartScreen acceptance or licensed commercial distribution.

## What is deliberately NOT yet wired

No patcher, EXE signature mutation, renderer injection, official-app
installation, localhost auto-pairing, account import, owner test or
consumer delivery. W20 consumer staging does not include this adapter.

## Rights / integration blockers

- The FkCensor project is MIT:
  https://github.com/S4YN3X/FkCensor/blob/main/LICENSE
  The Yandex resource response form was studied as a compatibility reference;
  the adapter itself is newly written, independently of PulseSync GPL SDK.
- This license does **not** authorize changes to/distribution of
  Yandex proprietary executable. FkCensor's own patch changes the EXE
  embedded ASAR hash, with the same Authenticode concern as W17.
- W21 verified recovery engine is the prerequisite for any **authorized**
  modified-client integration. W22 stays source-only until a consented,
  signed, version-gated implementation can be tested and commercial rights
  assessed.
- No real Yandex track sound or control operations have been validated yet.

**Next:** provision an isolated developer-owned authenticated Windows test,
determine a version-compatible insertion method and obtain distribution
rights where needed. Then verify native source+pause+seek+next+fallback,
signing/reputation and guarded rollback before publishing user installer.
