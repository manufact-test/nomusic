# W170 — Windows upload compatibility with automatic MP3 cleanup

Date: 21 November 2026

**Historical checkpoint:** W170/0.24.52 is superseded by W173/0.24.54.0. The old pending-owner-test notes later in this document describe the state at the original W170 handoff; current runtime audit and owner decisions are in `W173-START-UX-AND-OWNER-UPLOAD-AUDIT-20261121.md` and `NEXT-CHAT.md`.

## Baseline and safety

- Repository: `manufact-test/nomusic`
- Accepted Windows baseline: app **0.24.51.0**, native **0.24.32**
- W170 owner-review target: app and update supervisor **0.24.52.0**; native host/module version unchanged
- Baseline branch: `backup/windows-02451-owner-accepted-exact-20261117`
- Baseline commit: `c717428a7d9f01fc8e33b482fcf66a9ed1a02947`
- Work branch: `experiment/windows-w170-mainline-20261121`
- Main before work: `affb7b225d2e7eb2835f53294e975a1e60bb758b`
- Main backup: `backup/windows-main-pre-upload-cleanup-20261121` at the same SHA
- The PR branch starts from current main, restores the owner-accepted 0.24.51 Windows UI/installer baseline, and retains unrelated current-main Android A1 changes. Current-main W23 host/tests/package are intentionally kept unchanged; DiagnosticLog/PlaybackSourceEvidence use the accepted W169 baseline to preserve its truthful diagnostics contract. Main remains unchanged pending review.
- Shared server cleanup is already deployed. Do not deploy or copy the historical server branch.

## Server contract verified

The Windows client already uses the shared authenticated multipart endpoint:

- `POST /api/v1/uploads`
- `service=yandex`, `track_id`, `declaration=1`, `request_id`, `duration_ms`, metadata and the selected original file.
- The server returns HTTP **202** with `status=pending` and a positive `replacement_id` after the upload is accepted or deduplicated.
- The server independently normalizes MP3 metadata, measures duration, fully decodes audio, and rejects damaged payloads with `invalid_mp3`.
- M4A remains on the existing path.

## Windows changes

Only upload-related source and contract tests were changed:

1. `AudioPreflight.cs` now mirrors the extension's bounded MP3 structural parser for duration preflight:
   - multiple leading ID3v2 blocks, bounded to four tags / 8 MiB, including validated ID3v2.4 footer;
   - up to four leading Info/Xing metadata frames, including duplicate headers separated by ID3 tags; only the first header contributes duration;
   - validated APEv2 and ID3v1 tails, including the narrowly bounded UTF-8 inflated ID3v1 variant;
   - bounded zero padding;
   - no resynchronization past malformed audio and no skipping metadata that appears inside audio.
2. Local preflight remains inspection-only. It does not clean, rewrite, transcode, or replace the selected MP3. The original file bytes are sent unchanged so the shared server performs canonical cleanup.
3. Existing 30 MiB file limit, 1.5-second duration tolerance, rights declaration, request ID and in-flight duplicate-submit guard remain.
4. `CelikomApi.UploadTrackAsync` now requires HTTP 202 plus a `pending` response and positive `replacement_id`. A generic 2xx or malformed success body is not reported as an accepted upload.
5. Server `invalid_mp3`, `invalid_m4a`, `upload_too_large` and unconfirmed responses have readable Windows messages. Failed POSTs are not automatically retried.

## Verification — completed 21 November 2026

- Main CI: [run 44887076540](https://github.com/manufact-test/nomusic/actions/runs/44887076540) — **SUCCESS**.
- Windows integration CI: [run 44887076485](https://github.com/manufact-test/nomusic/actions/runs/44887076485) — **SUCCESS**.
- W20 internal safe-installer staging: [run 44887071981](https://github.com/manufact-test/nomusic/actions/runs/44887071981) — **SUCCESS**.
- W15 contract tests: `W15_NATIVE_CONTRACT_PASS 467`.
- W23 native tests: **156 passed**; W24 image-builder tests: **20 passed**; W21 recovery contract: **41 passed**; renderer bundle: **PASS**.
- GUI and update supervisor compiled with warnings treated as errors.
- Installer validation, PE version/anti-downgrade checks, disposable per-user install/uninstall smoke, single-installer ZIP packaging and SHA256 manifest all passed.
- PR #65 is open as a draft and reports mergeable. `main` has not been modified; keep the PR draft until the owner finishes runtime checks.

## Internal owner-review package

- App: **0.24.52.0**; update supervisor: **0.24.52.0**; native host/module unchanged (**0.24.32**).
- Installer: `CELIKOM-W170-WINDOWS-UPLOAD-CLEANUP-02452-UNSIGNED.exe`
- ZIP: `CELIKOM-Windows-0.24.52.zip` (contains exactly one root installer, byte-identical to the standalone EXE).
- Installer SHA256: `4a5c75bc70a936acfbc6af0c1c9d03281921203afce75b5fed55473a7ef59dc7`
- ZIP SHA256: `edd505333e400f0ef5da3d0c0aff3983b14255979cb5eb0f4d6fb7c7f5e67a4c`
- Actions artifact ID: `14700675953`, run `44887071981`, expires **1 December 2026, 08:58:05 UTC**.
- Artifact includes the EXE, ZIP and `SHA256SUMS.txt`; both hashes were independently recalculated and matched. Package remains internal and unsigned; no production release, signing or feed publication.

## Tests added

Synthetic, non-musical fixtures cover:

- multiple ID3v2.4 headers and footer validation;
- duplicate Info/Xing frames with an interleaved ID3 tag;
- metadata embedded after audio has started;
- valid and malformed APEv2 tails;
- the bounded UTF-8 inflated ID3v1 tail and rejection of extra control bytes;
- exact 1500 ms duration tolerance;
- structurally valid but damaged payload left for the server decoder;
- original MP3 bytes preserved through multipart upload;
- HTTP 202 / pending confirmation, same-request-ID duplicate retry, rejection of generic 200, and propagation of server `invalid_mp3`.

The CI checks above passed, but synthetic fixtures do not replace owner runtime verification. The real owner-provided repairable MP3, a known damaged MP3, and a retry after a lost response still need to be tested in the installed 0.24.52 build. No owner diagnostics have been reviewed yet.

## Scope guard

W170 upload changes do not modify playback, volume, Next/Previous, radio, audio routing, native Yandex integration, Android, permissions/access, billing, moderation, or the server. Current-main native host and playback-evidence files are retained unchanged. No server deployment. W170 internal owner-review installer/ZIP is stage-only; no production release, signing or feed publication.

## Next

1. Owner tests the known repairable MP3, a damaged MP3, and retrying the same upload after a lost response.
2. Review any diagnostics the owner supplies; fix only confirmed W170 upload regressions.
3. Keep PR #65 in draft and keep `main` unchanged until owner runtime acceptance.
4. Do not rebuild or publish another package unless a code fix is needed.
