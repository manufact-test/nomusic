# W64 — CELIKOM Windows 0.24.12 owner candidate (2026-11-10)

## Owner findings on REAL installed 0.24.11 (source-of-truth)

After owner tested W63 0.24.11 on his actual Windows desktop, he sent screenshots and a final list of bugs:
1. Gray/green status mark oversized and vertically misaligned; shrink/center. Application version footer floated in the middle of the screen instead of staying at the bottom.
2. Yandex install/startup message looked like a technical "Обновляем подключение"; need clearly visible: **"Подождите, идёт загрузка Яндекс.Музыки…"**.
3. Some Yandex tracks showed only the song name but not the artist (owner examples "Пушка — 10AGE", "TRITIA — Потрачено"); title/artist were cramped/cut. Preserve actual current-entity display, not a fake title or preload.
4. Server version-presence message was incorrectly the same during active replacement. Extension `version-status.ts` distinguishes **"Подмена активна · версия CELIKOM"** from **"Версия песни CELIKOM доступна для подмены"**.
5. "Предложить песню" showed oversized blank spaces, no beautiful enclosing border, and missing artist. **Real suggestion did reach admin successfully** — preserve API behavior.
6. "Загрузить версию": selecting an unrelated MP3 was *uploaded first*, and a length mismatch arrived **too late**; feedback green rather than red; file name appeared twice; Windows checkbox looked unstyled. Strict parity: validate local MPEG/MP4 duration on selecting, with red block if delta exceeds 1500ms, warn about filename mismatch without blocking on filename alone, style checkbox, selected file label and progress.
7. Popup expanding account/upload/support caused right-side gutter to nearly double; no working scroll to reach form bottom; promo section did not follow extension signed-in account order.
Owner explicitly said this was the **final batch** and authorized one substantial correction. Sound/Start/Stop/pause/seek/MyWave worked before W64 and must not change.

## Source / exact accepted backups

- Frozen owner-accepted audio baseline: `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` at `44e69d78b459ed512862819280ebdb8b3dbc7e7d`.
- Previous 0.24.11 built CI baseline: `backup/windows-w63-02411-built-ci-await-owner-20261110` at `266beacfcfa524eeb9ecae91d44b9316ec257286`.
- W64 exact source frozen for owner: `backup/windows-w64-02412-built-ci-await-owner-20261110` at `12c0833dbe51d5f2b5970feedbecc2a4427b0edb`.
- Working branch `experiment/windows-stop-lifecycle-20261110`. After W64 built, only an independent upgrade workflow and docs were added; no source code changes.
- Preserve one application. Never touch Android Test.50, production, original Yandex files, signed URL/audio reload logic.

## W64 implementation

**Compact Windows UI** (`CompactPopup.cs`, `MainWindow.cs`, `PopupSectionPanel.cs`, `PopupRightsCheck.cs`, `PopupFilePicker.cs`):
- Smaller centered status dot (grey disconnected/green on active), fixed footer version in dedicated second row of root `TableLayoutPanel`, never hidden under the scroll panel.
- Native `VScrollBar` with mouse wheel and explicit virtual offsets, no WinForms `AutoScroll` double-gutter/inaccessible form bug. It overlays the 16px right inset, so content width remains unchanged between open/closed states; expanded panels scroll without moving the footer. Tested actual `SetCompactOffset` and `MouseWheel` in Windows UI staging.
- Large, non-technical Yandex launch message as requested, same Start/Stop audio commands.
- Current song **separate lines** for title and artist with guarded extra read-only Yandex metadata field fallbacks from *current* player entity (not preloaded). Native bridge data strictly bounded and authenticated localhost only. A title may still fall back to Track ID or artist may be absent if Yandex exposes no suitable field; no owner-side proof yet.
- Exact extension status distinction: active mapping + enabled + server-approved shows `Подмена активна · версия CELIKOM`; approved but not active shows `Версия песни CELIKOM доступна для подмены`. Conservative: mapping acceptance is a technical signal, not independent audible playback proof.
- Upload/suggestion sections now have extension-matching dark borders, title/caption/track/controls in compact spacing, no blank result reservation when an ordinary form is shown. Server existing/pending still shows green result before upload/suggestion; API requests to admin unchanged.
- Signed-in account section order matches `extension/popup/popup.html`: promo control first, signed-in email, logout, rather than unrelated developer layout. Admin diagnostics remain protected by exact two allowlisted SHA256 email identities and revalidated live via `GET /auth/me`.
- `PopupFilePicker` now contains exactly one `Файл выбран` title and a subtitle **filename + size**; removed duplicated label below. `PopupRightsCheck` is owner-drawn with mint tick.
- `AudioPreflight.cs` local 30MiB-bounded MP3/M4A structural duration inspectors ported from `extension/src/upload/mp3-duration.ts` and `m4a.ts`. Immediate after file chooser uses **actual measured audio duration**, compares to known currently playing Yandex duration (manual reference only if native metadata missing), strict **absolute delta <= 1500ms**. Invalid/unknown duration fails closed, red multi-line warning, upload button disabled. Filename mismatch independently warns red without blocking if duration valid. File is validated **again immediately before multipart POST**, preventing simple TOCTOU and server remains ultimate authority. `ProgressReadStream` unchanged and reports local upload bytes read, not server moderation.
- Explicit original-file validation and mismatch errors are **red**. Green is limited to valid/approved/submitted states.
- No new API, no modified Yandex source switching, no user credentials logged.

## Verified gates, real installer / checksum / Library

- Actual source-only WinForms 9 PNG snapshots (including fixed footer, expanded support/account/upload, green approved state, invalid-audio red warning, scrolled pane and wheel action): **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42830887008.
- Windows original native W60 source reload regression: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42831338168.
- Full 0.24.12 Windows self-contained build + tests, exact installer and clean-runner install/uninstall: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42831368648, head `12c0833dbe51d5f2b5970feedbecc2a4427b0edb`.
- Independent same Windows user **0.24.11 → 0.24.12** DPAPI encrypted session unchanged, one Inno AppId/uninstaller, native module 0.24.12 and Yandex vendor files untouched: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42831819681.
- GitHub Actions artifact id `13770404399` ZIP `CELIKOM-W64-EXTENSION-FINAL-UX-UNSIGNED.zip`, SHA256 `c34713ef492d00feb5463c6ba94bf2608e67dd30b685b42eae7724309d107039`.
- **EXE** `CELIKOM-W64-EXTENSION-FINAL-UX-UNSIGNED.exe`, **43,540,794 bytes**, SHA256 `c8e5dd395fdb7133a91f8418d0b910f97c84168111586166592ffac03144b5b7`.
- Uploaded to ChatGPT Library `/CELIKOM/Windows/CELIKOM-W64-EXTENSION-FINAL-UX-UNSIGNED.exe` Library ID `libfile_9e5b773199b88191b695a8610f216c6d`, file ID `file_000000002c048246b2d291ac04157925`. Materialized from Library to test directory; **cmp exact match and sha256 match** original GitHub artifact.
- This is a **private, unsigned owner trial**, NOT published to production and NOT owner-accepted. The real audible behavior and Yandex song metadata on user's PC remain an acceptance test.

## Owner test (next action)

Install exact W64 EXE over existing 0.24.11; do not uninstall or log out. Check:
1. Indicator & footer, open album/search buttons, Yandex loading text and stable 16px gutters while opening/closing account, upload, support.
2. Wheel/scrollbar down to **send button**, rights checkbox and promo without clipping; version remains anchored.
3. Song title + artist on actual "Пушка"/"Потрачено"/"До дна"; owner should say whether any artist is still missing. Approved server version versus *actually active* native replacement text.
4. Select **wrong-duration MP3** against current song: **red warning before network, submit disabled**, no request sent; matching version yields green duration notice and optional filename warning. Do not intentionally submit actual audio unless owner wants server-side test.
5. Start/Stop playing song, pause/seek/Next/MyWave: no regressions. If regression, install archived owner-reviewed W63 0.24.11 or W61 0.24.9 accepted sound baseline. Never change the signed player reload due to cosmetics.

For ongoing work, no extra source changes until owner trials unless a self-evident CI regression. Do not claim perfect pixel/feature equality with browser extension without owner confirmation.
