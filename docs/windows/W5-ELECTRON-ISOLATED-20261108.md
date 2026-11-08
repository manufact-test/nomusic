# CELIKOM Windows W5 — isolated Electron native-source experiment

**Status:** W5 CI test implementation. No owner Yandex installation modified. All evidence is synthetic/isolated until Windows CI completes.

## Grounded prerequisites
Owner real W3: Windows 10 19045 x64; official Yandex Music 5.126.1.0;
SHA-256 `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`.
1117/1117 packaged JS scanned with no skips. getFileInfo appears in 19 JS,
getFileInfoBatch in 3, GetFileInfoResource in 19 and file-info endpoint
hints in 2. These are **static text occurrences**, not proof of an active
hook or actual source replacement in the running Yandex app.

W4: GitHub Actions [42509525224](https://github.com/manufact-test/nomusic/actions/runs/42509525224)
SUCCESS for 17 synthetic source-adapter Node contract tests. W4 does not play audio.

## W5 technical experiment
All files scoped to `windows-companion/w5/**`; existing W4 adapter is
used unchanged. No user-facing installer or test ZIP is needed.

1. Fetch **76 pinned publicly available frontend JS assets** for Yandex
   Music web build `v4.1726.0`, verified by SHA-256 against research manifest
   copied from our own read-only browser experiment. No third-party JS
   is committed to repository or distributed as executable product code.
2. Reconstitute original Webpack module factories in transient CI fixture.
   Export the **actual private native source class** from its original body
   for **test only**, without changing the class body.
3. Launch an independent installed-at-CI **Electron** renderer.
   This is a technical test harness, **not a separate production player**.
   It never loads official Windows Yandex, user profiles or credentials.
4. Exercise W4 wrapper against actual publicly shipped Yandex v1/v2
   `getFileInfo` and `getFileInfoBatch` class methods, with **synthetic**
   original resource responses and a strict exact-ID source gate.
5. Create two original sine-wave MP3s only at CI runtime with bundled
   FFmpeg. Use one actual Chromium `HTMLAudioElement` for real MP3 decoder,
   native Play/Pause, Seek, Next, long-track seek and re-acquired Original.
   Tests do not create a second playing media element.
6. Emulate short-lived, HMAC-authorized fixture audio URLs with 206 Range,
   403 access rejection on expired/missing signature and 416 invalid range.
   This validates local transport assumptions, not our real backend CDN.
7. Preserve original for unknown/prefetched tracks; generation-fence
   a delayed source request after Next. Stop and Original prevent subsequent
   substitution. No claims of instant mid-playback restoration.
8. Only signed fixture URL and Blob bytes are used; no CELIKOM/Yandex
   customer secrets, no logging signed URLs.

**CI:** `.github/workflows/windows-companion-readonly.yml` includes
Electron native-source verification before existing W3 .NET tests and
read-only probe publication. Electron and FFmpeg are pinned dev-only
dependencies under `windows-companion/w5/package.json`.

## Explicit limitations / blockers
- Public web build `v4.1726.0` is **not** proven to be the active renderer
  packaged or loaded by owner's Yandex Windows 5.126.1.0.
- Native class works in an isolated fixture only. Official app runtime
  hook/injection API, safe update behavior and running cache invalidation
  are still unproven.
- Complete-file MP3 preparation may make cold start slow; streaming
  performance and real backend entitlement/Range are not validated here.
- Real Windows Yandex audio and native queue/media keys **not tested**.
- A missing source class or failing Electron CI test is a hard failure,
  not a reason to silently replace with a synthetic-only happy path.
- No ASAR patch, no external mod, no Yandex process startup/shutdown,
  no production backend/Android/browser modifications.
- Any official client integration requires owner authorization and tested
  backup + byte-checked rollback, update/version gate and legal review.

## Decision
Upon CI result inspect assertions and any failure. If CI proves the
native source class + actual Electron decoder, next evidence gap is
**compatibility with owner's specific official Windows runtime and
restore behavior**. Do not claim Windows support before owner can listen
to one approved track in the original Yandex app with Play/Pause/Seek/Next
and verified rollback.

## VERIFIED Windows CI result — 2026-11-08

**Final code:** `bfe5ce7ca0c31780812de19f2de7e96eda06d9da` (after corrections).
[GitHub Actions run 42511997271](https://github.com/manufact-test/nomusic/actions/runs/42511997271): **SUCCESS**.

- Electron **44.10.2** executed real pinned public Yandex Webpack resource
  v1/v2 classes and original private native source class (test-only export).
- **35/35** W5 runtime assertions passed inside Electron.
- Native decoder in ONE real Chromium media element: synthetic alternate MP3
  starts, pause holds clock, seek reaches 6 s, Next switches to 36-second
  track, seek to 30 s plays, stale previous response is fenced.
- Explicit Original re-acquisition plays the synthetic signed original
  via the **same** media element; Stop blocks future substitution.
- Fixture signed URL checks: 206 correct byte range, 403 missing/expired
  signature, 416 invalid range.
- Existing W4 Node synthetic contract and W3 .NET read-only checks passed.
- **No** owner-installed Yandex app was used, modified or launched. This is
  strong **isolated** feasibility evidence, NOT product integration evidence.

### Correction tracked, not hidden

Initial [CI run 42511753607](https://github.com/manufact-test/nomusic/actions/runs/42511753607)
incorrectly showed SUCCESS despite Electron's renderer test failing
with native media code 4 while reacquiring the fixture original.
The Yandex getter appended its `?vsid` fields onto an already-signed
fixture URL, making the HMAC request unusable. The W5 test now normalizes
only its **exact known synthetic signed fixture URLs**; real Yandex URLs
are untouched. The runner also uses `app.exit(1)` so a future failed
assertion turns CI red. On re-run **35 assertions genuinely passed**.
This URL behavior is a concrete compatibility requirement for a future
CELIKOM signed audio bridge; it is not automatically solved for the live
Windows app.

### Next gate

Determine how to attach to the owner's **official Windows Yandex 5.126.1.0**
renderer by safe, isolated and reversible means, and where the live playback
owner/caches reside. No full Windows integration, no native Yandex UI button
test, no production CELIKOM server/session flow, no installable companion yet.
Do NOT initiate any app.asar modification without explicit owner consent,
version pin, backup/rollback, and an integrity recovery demonstration.
