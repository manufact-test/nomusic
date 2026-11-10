# W67 — CELIKOM Windows 0.24.15 support dropdown native-click crash correction (2026-11-10)

## Authoritative outcome (private candidate; owner PC check still pending)

- **Built exact source commit:** `5a1f5a3a81e0ae98909315ead137ca9a5260896b`. Source frozen branch **`backup/windows-w67-02415-built-ci-passed-await-owner-20261110`**. The work branch may have later doc/independent-upgrade-workflow commits.
- **W67 private unsigned EXE:** `CELIKOM-W67-SUPPORT-SELECT-GUARD-UNSIGNED.exe` (43,534,754 bytes), **SHA256 `c885262a5fedb15cfa05f930531e6ce706ee41c4cc4505e129496d104df6ffab`**. Exact output of build CI and separate local ZIP extraction and Library round-trip hashing.
- **ChatGPT Library:** `/CELIKOM/Windows/CELIKOM-W67-SUPPORT-SELECT-GUARD-UNSIGNED.exe`, file `file_0000000042988243960d5afc1cdccc1b`, library file `libfile_7bbf7e9dd8f081919133c6c4982029fe`. Library readback matched build SHA byte-for-byte.
- **Main build:** https://github.com/manufact-test/nomusic/actions/runs/42858640960 **SUCCESS**; artifact `13782839469`. Compiled warning-as-error, native and API contract tests, Inno setup, icon PE, updater ZIP, actual Windows per-user install/uninstall.
- **Independent upgrade:** https://github.com/manufact-test/nomusic/actions/runs/42859695926 **SUCCESS**. Real 0.24.14 installer downloaded from W66 action, 0.24.15 downloaded from above build and independently SHA-checked, installed over the old app with same AppId and one uninstaller. DPAPI encrypted `session.dpapi` bytes identical and decryptable by same Windows user, native modules updated to 0.24.15, vendor Yandex untouched. Uninstall preserved DPAPI user state.
- **Actual GUI interactions:** https://github.com/manufact-test/nomusic/actions/runs/42857977946 **SUCCESS**. Actual Win32 mouse-down/up, 24 alternations of two support types, 8 outside dismiss/reopen cycles, keyboard Up/Down/Enter, actual selected category, menu bounds and row alignment, no process crash. GitHub artifact `13784201268` includes screenshot of actual highlighted menu.
- **Baseline fatal exception proof:** https://github.com/manufact-test/nomusic/actions/runs/42856421539 **FAILED as expected**. Reproduced owner's reported full-process exit using real mouse on 0.24.14. `System.ObjectDisposedException` in `ToolStripDropDown.SetVisibleCore`, called by `OnItemClicked` after `ContextMenuStrip.Closed` synchronously disposed dropdown. Not a speculative layout theory.

## Fixes, narrow scope

1. `windows-companion/w15/Celikom.Companion/PopupOptionSelect.cs`: native dropdown closed event **no longer disposes synchronously inside native ToolStrip OnItemClicked**; disposal and selection state updates are queued onto WinForms UI event loop. This allows the native click stack to complete before rebuilding compact form; no blanket exception suppression.
2. Menu width is clipped to the actual current selector/remaining owner-form width, not hardcoded 300; dark rows are owner-drawn with consistent text offset, vertically centered highlight, wrapping long labels and no default native image/check margins. Both support kind and category use same control; hardcoded 300px support widths removed.
3. `IsInputKey` returns true for arrow keys and Enter/Space to receive keyboard keys inside the selector instead of default focus traversal. Verified on real Windows runner after the initial keyboard tests exposed this missing behavior.
4. W67 bump: C# executable, Inno installer and native host *version metadata* only; all earlier official CELIKOM green C icon assets unchanged. Original `CompactSendSupportAsync` / API submission code unchanged.

## Explicit preservation / non-claims

Keep W66 immutable rollback: `backup/windows-w66-02414-built-ci-passed-await-owner-20261110` @ `6b4a8088b299f802366bc85e3ff28515930336e4`; W65 rollback `backup/windows-w65-02413-built-ci-passed-await-owner-20261110` @ `5ce1b6ebdecf9a49259d29241e5aa29619d2f429`. Accepted W61 native audio remains unchanged. No edits in Android Test.50, production backend, native audio switching algorithm, vendor Yandex originals. Existing support endpoint send-to-admin was **confirmed by owner with prior W66** and was **not retested against live admin** in W67 to avoid sending unsolicited tickets; related code unchanged.

**W67 is a PRIVATE UNSIGNED CANDIDATE, not an owner-accepted public release.** Owner needs to install from Library directly over existing 0.24.14 and verify: 20+ support kind changes mouse, multiple reopen/outside dismiss, keyboard arrows/Enter, dropdown aligned inside app, selected song issue category, actual support send reaches admin without duplicates, audio Start/Stop/pause/seek/MyWave, icon and login remain intact. Owner must explicitly confirm no full-process crash. Test Windows runner default DPI; 125% DPI has not been independently demonstrated, do not claim otherwise.

## Next handoff

Do not rebuild prematurely. Await owner feedback on 0.24.15; if failure, capture exact actions and diagnostics while preserving W67 frozen source. Avoid unrelated audio/Android/production modifications. Keep old working 0.24.14 install available for rollback.
