# W83 Windows — eliminate recurring lifetime promo flicker (2026-11-13)

**Owner request:** "Промокод · доступ навсегда" flashes frequently even without switching accounts; keep it steady. **Do not modify installed 0.24.28 before tomorrow's actual music listening QA.**

## Root cause
`windows-companion/w15/Celikom.Companion/MainWindow.cs` runs a 15-second authenticated entitlement timer while the bridge is enabled. `CompactPopupActions.RefreshCompactAccessAsync(force: true)` forcibly replaced the green permanently-active promo text with `Проверяем доступ…` at the start of **every GET** and put the original text back after response. No server entitlement change was involved.

## Work complete
- Exact previous source and rollback: `backup/windows-w83-pre-promo-steady-exact-20261113` @ `a69f91858f5336727a0fdab0c65ebc87b4026e9c`.
- Branch: `experiment/windows-w83-promo-steady-entitlement-20261113`.
- New pure `CompactAccessRefresh.cs`: preserve last confirmed label only for exact installation ID and case-insensitive same email during a pending authenticated GET; new/unknown identities show checking. Prevent unnecessary WinForms label repaint on identical text.
- `CompactPopupActions.cs`: no transitory "checking" on 15s polls for the same confirmed account. On server success update current authority, expiry, revocation and bridge as before. On server/network error keep existing fail-closed playback and explicit explanatory text.
- `CompactPopup.cs`: confirmed identity fields and reset utility. `MainWindow.cs`: clear on login/logout, cache authenticated Start response for same installation.
- Contract tests: unchanged lifetime promo, subscription text, new account/device isolation, initial checking and real server revoke requiring repaint.
- CI SUCCESS: https://github.com/manufact-test/nomusic/actions/runs/43310069470 (Windows tests, native compatibility, warnings-as-errors build).
- No version bump/installer yet: stage this patch in the next Windows release **after** owner 0.24.28 music QA. No change to `windows-companion/w23` audio in W83.

## Follow-up
Issue #52 tracks actual source witness; experimental read-only investigation in `experiment/windows-w84-readonly-player-source-evidence-20261113`. Issue #48 stays open until migration, issue #44 until owner's real-world listening.
