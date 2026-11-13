# CELIKOM Windows W66 / 0.24.14 — owner candidate (2026-11-10)

## Owner observations

Owner tested Windows **0.24.13** and approved broad functioning but reported the final set of UI defects:
- Support textbox almost touched Submit button; add ~10–12 px. Support messages already reached admin; do not rewrite this integration.
- Promo input/toggle and Activate almost touching; the native promo placeholder color was wrong/too brown.
- Upload form wasted significant vertical space between track title, duration, file picker, and below Submit; no pre-reserved vertical space for upload progress/notes. Expand only when warning/progress appears.
- Several artist names lost uppercase D and other characters, e.g. Yandex **kavabanga Depo kolibri**, Windows **kavabanga epo kolibri**. This affected song labels and contribution views.
- Grey/green connectivity dot was ~7px but vertically below CELIKOM logo text; align it.
- Windows taskbar/title/tray/setup used the stock Windows application/doc icon, not official CELIKOM "C". Use actual repo asset and one identity everywhere.

These form a single W66 batch. No new changes to original Yandex binaries/audio source reload, Android Test.50, server API, or public release.

## Exact source and immutable backups

- Work branch `experiment/windows-stop-lifecycle-20261110`, code built from `6b4a8088b299f802366bc85e3ff28515930336e4`.
- **W66 exact source backup:** `backup/windows-w66-02414-built-ci-passed-await-owner-20261110` at `6b4a8088b299f802366bc85e3ff28515930336e4` — never rewrite.
- **Pre-W66 owner 0.24.13 rollback:** `backup/windows-w65-02413-owner-final-feedback-pre-w66-20261110` at `de08b9c5ef509811347771d2c044e635e15ad3d4`.
- Previous owner-accepted audio baseline `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` @ `44e69d78b459ed512862819280ebdb8b3dbc7e7d`. All untouched.

## Fixes made

1. **Proven loss of D:** `windows-companion/w60/current-source-refresh.mjs` had erroneous literal RegExp `/[\\u0000-\\u001f\\u007f]/g`: escaped backslashes made a character class that wrongly matched many printable chars including uppercase **D**; `windows-companion/w23/host.cjs` repeated the error as a rejection filter. Both now use the real **control-character ranges** `/[\u0000-\u001f\u007f]/`, preserving all letters, numbers, Unicode, whitespace except controls. Unit regression tests test **"kavabanga Depo kolibri", "TRITIA 10AGE 02468 ABCDFHJLNPRTVXZ", Cyrillic and Chinese**. Current Yandex observer stays read-only; no media calls.
2. **Dynamic upload dimensions:** `CompactPopup.cs` uses `TextRenderer.MeasureText` for actual current-song label height and upload note height. No perpetual `"Новая версия появится после проверки"` informational note or any placeholder height. The form grows only for real duration-validation notice, real upload progress, or errors; collapses again when gone. Progress callback triggers re-layout. MP3/M4A duration preflight and 1500ms tolerance unchanged; arbitrary filenames including Chinese still fully allowed.
3. **Support gap and feedback:** textarea-to-Send gap ~13px for standard and song support; initial feedback hidden; entire support accordion height recalculated when an actual message is shown and collapsed afterward. Support send remains real /api/v1/support and admin delivery unchanged.
4. **Promo:** 12px promo-toggle-to-input gap and 10px input-to-Activate gap. Replaced native Windows placeholder color with `PopupInput.Hint` and owner-painted text `#AAB8BE`. Server-based promo functionality unchanged.
5. **Indicator:** smaller 7px dot from W65, moved from Y=17 to Y=15 to align with visible CELIKOM text (not text box bound).
6. **Exact icon:** reused genuine source `extension/assets/icons/green-{16,32,48,128}.png` (same C used by extension), **not a newly generated/imagined brand**. New `windows-companion/w20/scripts/build-app-icon.cjs` deterministically packs those original PNGs into a Windows `CELIKOM.ico` using ICO directory with PNG entries. MSBuild builds it from source before compiling the native WinExe; project ApplicationIcon embeds it in PE. Inno `SetupIconFile` sets installer/uninstaller icons; `MainWindow.Icon` and `NotifyIcon.Icon` use extracted PE icon for titlebar/taskbar/tray. CI validates green C pixels in **actual published app EXE and installer EXE**, both PASS. Does not embed Yandex files or distribute fonts.

## Verified tests & exact artifact

- **Real WinForms staged preview** and support gap, scroll/footer, upload-height growth/collapse, promo neutral hint, 7px dot: **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42845448149 . Screenshot asset `CELIKOM-W59-UI-STAGE` artifact id `13777034555`, includes `-w66-compact-upload.png`.
- **Full W66 0.24.14 Windows source/contract tests, Node and native UI compile, single-file publish and clean-runner installer smoke:** **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42846306058 . Source SHA exactly `6b4a8088b299f802366bc85e3ff28515930336e4`. CI log `W66_OFFICIAL_C_ICON_APP PASS` and `W66_OFFICIAL_C_ICON_INSTALLER PASS`.
- **Independent installed 0.24.13 → 0.24.14 same AppId, same-user synthetic DPAPI encrypted session byte preserved/decryptable, one uninstaller, native module identity, and Yandex install directory untouched:** **SUCCESS** https://github.com/manufact-test/nomusic/actions/runs/42846415169, rerun after new artifact appeared. This is an isolated test identity, NOT owner’s real credentials.
- GitHub Actions artifact `13777993165`, ZIP digest `sha256:d13f6307cf0a8fdb08c1b1884f54aa183ccee45625c1da4b9d3797927ba84fd9`.
- **Exact executable:** `CELIKOM-W66-COMPACT-UX-BRAND-UNSIGNED.exe`, **43,492,716 bytes**, SHA256 `2028f53113eef88cfc65b4181336fc9db723a7360a051a551b280863668493f9`.
- **ChatGPT Library:** `/CELIKOM/Windows/CELIKOM-W66-COMPACT-UX-BRAND-UNSIGNED.exe`, File ID `file_00000000a96c8243811ad4bc82387b4b`, Library ID `libfile_44cba65dcd248191a832c60c5f42ce3b`. Downloaded from GitHub artifact, ZIP + EXE hashes verified; uploaded Library; **re-materialized from Library and byte-for-byte cmp + SHA256 exact match**.
- Both EXE and Library source are safe to give as a direct file card. UNSIGNED private owner candidate, not production release and not owner-tested yet.

## Next owner test

Install exact 0.24.14 over existing 0.24.13 (same app; no uninstall/relogin). Check:
- Taskbar icon, titlebar and tray now show brand C not OS icon, plus installer’s C. Dot vertically aligns while grey and green.
- Expanded signed-in account > promo: placeholder neutral, gaps; support text area > Send has gap and successful delivery.
- Upload form with original known duration and **no selected file**: no enormous blank areas top/bottom; selected valid/wrong-duration MP3 creates corresponding warning and dynamic height; clear/cancel closes appropriately; same Chinese/different filename behavior (no name-based rejection).
- Play Yandex songs with D in artist/title, e.g. "Город и Туман — kavabanga Depo kolibri"; inspect normal popup, Upload and Suggest title. Test real playback/pause/seek/Next/MyWave remain as before. Current metadata may vary by vendor; CI regression cannot independently confirm exact Yandex live feed.

Any regression: rollback to private 0.24.13 build `backup/windows-w65-02413-built-ci-passed-await-owner-20261110`, and don't touch accepted W61 audio branch. NEVER announce owner acceptance before actual PC verification.
