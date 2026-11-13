# W65 — CELIKOM Windows 0.24.13 owner-candidate (2026-11-10)

## Owner feedback / acceptance boundaries

User installed W64 0.24.12. The audio and track titles were broadly satisfactory; no new audio defect reported. Owner provided a final batch of screenshots and explicitly authorized fixing everything together:

1. Colored dot next to CELIKOM ~30% too big and not vertically centered;
2. Promo input font too big/odd color; signed-in account looked like ungrouped controls;
3. Standard right scrollbar sits practically against buttons/fields; should remain symmetric on expansion, no width jump;
4. Support kind selector and multiline form showed white default Win32 framing and looked nothing like the extension;
5. **Completely remove filename mismatch detection or warnings**, including for Chinese and arbitrary filenames. Filename never determines eligibility; keep actual audio duration checking only;
6. In browser extension, account is one bordered card with its own details, promo, email and “Бонусы и друзья”; Windows previously lacked the border and benefits section. Each expanded section must be visibly grouped.

**Sound / Start / Stop / pause / seek / MyWave must stay frozen.** Never modify the original Yandex application, Android Test.50 or production backend.

## Source work (only experiment branch)

- Exact W65 tested source: `5ce1b6ebdecf9a49259d29241e5aa29619d2f429` in `experiment/windows-stop-lifecycle-20261110`.
- Immutable W65 backup: `backup/windows-w65-02413-built-ci-passed-await-owner-20261110` at exact SHA above.
- Pre-W65 owner-screen and audio rollback: `backup/windows-w64-02412-owner-last-ui-feedback-before-w65-20261110` at `3cde12a3bb7ac439d621f9b8d8b3d065e0d16af1`. Previously accepted 0.24.9 sound backup: `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` @ `44e69d78b459ed512862819280ebdb8b3dbc7e7d`.
- `AudioPreflight.cs`: **deleted** `FilenameSuspicious` and the corresponding warning fields from the result type. `CompactPopupActions.cs` still performs local MP3/M4A read, format, strict <=1500ms duration tolerance before sending; backend still validates duration. Unicode arbitrary filename regression added. No new name-based checks or validation.
- `CompactPopup.cs`, `PopupButton.cs`, `PopupSectionPanel.cs`: account and support summary/content now nested in ONE rounded bordered accordion card, not separate button+floating content. Inner summaries render without redundant borders; promo text uses extension-size 8.5pt, `PopupInput` consistent 9pt. Signed account order: promo accordion, verified email, feature-gated benefits, logout. Server promo feedback distinguishes green success, red errors. Signed-out account border is red.
- `CompactBenefits.cs` + `CelikomApi.cs`: *existing* feature-gated /config + /referrals + /rewards endpoints; real referral counts, earned reward summary, code shown; create only on explicit action, copy to clipboard; no invented bonuses, no automatic POST, on logout invalidate cached benefits. Benefits hidden if feature disabled or data fetch fails. Same extension source semantics.
- `PopupOptionSelect.cs`, `PopupMultilineInput.cs`: custom dark select and rounded textarea replace white default Win32 border and scrollbar, with actual native keyboard/text editing and sending support preserved.
- `PopupThinScroll.cs`: 5px owner-drawn dark draggable scrollbar inside right gutter; button widths are constant regardless of expanded state, ~15px gap from right edge of content to thumb. Version footer fixed.
- Dot: actual live Windows renderer showed a 10px mark despite 7px request; root cause `Place()` had hard minimum width 10. Replaced label with painted Panel and changed minimum to 1. Actual Windows preview now verifies **7px dot**.
- Native player state refresh, signed media URL guard, installed Yandex files and original audio switching code remain **unchanged**. Package version and native identity bumped to `0.24.13` with the same Inno AppId/path as 0.24.12, not a second app.

## Verification

- **Actual WinForms screenshot suite SUCCESS:** https://github.com/manufact-test/nomusic/actions/runs/42838998161 — rendered default/expanded signed-out Account, Support, song support, upload, approved version, invalid duration, scrolled/wheel. Checks parent cards and balanced widths, borderless promo and benefits controls, dark support, no `FilenameSuspicious` symbol/warning, 7px status dot and pinned footer. These are static/controlled UI tests, NOT owner's live signed-in account.
- **Full W65 0.24.13 Windows installer SUCCESS:** https://github.com/manufact-test/nomusic/actions/runs/42838998263 — source SHA `5ce1b6ebdecf9a49259d29241e5aa29619d2f429`, audio/native regression and CI installer smoke.
- **Independent W64 0.24.12 → W65 0.24.13 SUCCESS:** https://github.com/manufact-test/nomusic/actions/runs/42839920232 — same user same app and Inno uninstaller, DPAPI session ciphertext unchanged and decryptable, native module `0.24.13`, original Yandex vendor directory untouched, clean uninstall preserves user state.
- GitHub Actions artifact ID `13775480729`, ZIP SHA256 `d5657c2d2d715592f75f149c443d3c213a03a38e20043d28a2770147e68d30a4`.
- **EXACT EXE:** `CELIKOM-W65-ACCOUNT-SUPPORT-UX-UNSIGNED.exe`, 43,542,477 bytes, SHA256 `6d8f1ff5ca26260c5a3350e8d8adad8732b350ca412628f870c3889a51fb6574`. Uploaded to ChatGPT Library `/CELIKOM/Windows/`, file ID `file_00000000ce28824390eab48175e050fb`, library ID `libfile_526fdf375cfc819182c18e1a29ed83d5`. **Round-trip bytewise / SHA256 exact match**.
- This is unsigned, private staging, **not publicly released and not owner-tested**; do not call it production-ready or claim 100% visual parity until owner confirms in installed app.

## Owner next action

Install 0.24.13 directly over installed 0.24.12, no uninstall or re-login. Check:
1. Circular dot smaller/centered; its color switches grey/green.
2. Account expansion has one continuous border, promo typography, email, sign-out, and feature-gated real benefits.
3. Support expansion has outer border, fully dark dropdown and textarea, text entry, and Send reachable via scroll.
4. Right scrollbar does not crowd buttons or change widths; bottom version stays pinned.
5. Select arbitrary named (e.g., Chinese) MP3 and see ONLY the duration-based red error for bad length; no filename comparisons. Matching-duration file may warn/allow based on actual audio duration (DO NOT submit unless intentional).
6. Pause, seek, Start/Stop and MyWave still behave exactly as owner-approved before W65.
Rollback to W64 exact owner build or W61 accepted audio branch if audio regresses. No changes to production, Android Test.50, original Yandex player or private server.
