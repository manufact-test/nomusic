# CELIKOM Windows W85 — 0.24.29 promo no-blink owner candidate

## Scope and owner instructions

Requested 2026-11-13: make newest Windows installer available in the user's Library for next-day music QA. **Keep all 0.24.28 music source and native integration behavior byte-identical**; add W83 fix only.

- Branch: `experiment/windows-w85-02429-promo-steady-owner-candidate-20261113`.
- Before-W85 exact rollback: `backup/windows-w85-pre-02429-exact-20261113` (W83 green source, no new installer).
- Previous owner installer W82 0.24.28: CI `43308400132`, EXE SHA256 `74E385DEEAA3FE94FF330CEB5B20D6EF60A8779F4CAA9517C888C9D10DFC5EE3`.
- New version: 0.24.29; do normal **in-place install over 0.24.28** without uninstalling, logging out or reinstalling Yandex.
- Changes: exactly W83 fixed entitlement label flicker. Previously 15-second authenticated poll wrote `Проверяем доступ…` over confirmed `Промокод · доступ навсегда`; now UI retains known status for same authenticated installation and account while GET revalidates. Revocation/expiry still follow server answer and stop playback; account switch invalidates label. Tested via `43310069470` SUCCESS.
- No experimental W84 source/decoder witness in owner candidate. That remains independent branch `experiment/windows-w84-readonly-player-source-evidence-20261113` and open issue #52 for actual-device/host verification.
- W85 installer GitHub Action `windows-w85-promo-steady-installer.yml`: W21 and W24 tests, all W15, W22/W23/W60 native audio tests, .NET publish, Inno setup, **exact 0.24.28→0.24.29 DPAPI and native byte-identity** test. Must be CI green before delivery; record run/artifact and SHA below.
- Existing W80 hourly Yandex update watch stays separate, no changes to old/new compatibility feed.
- User's actual listening test still required to confirm no song drops/incorrect diagnostic or promo flicker.

## Build evidence

PENDING: record green W85 GitHub Actions run and exact SHA256 after build.
