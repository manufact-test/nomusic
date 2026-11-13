# CELIKOM Windows W86 0.24.30 — owner TEST of actual native decoder source witness

## Why this TEST exists
Owner correctly objected that an experimental diagnosis cannot be validated on their real PC without a build. This is a **separate TEST candidate**, not a production release. It is available only for explicit owner testing.

## Changes vs owner-stable W85 0.24.29
- All W82/W85 GUI, no yellow/false red error, promo access no blink, entitlement verification and compatibility preserved.
- The audio-source adapter (renderer.js), signing/streaming rules, login, account data and original Yandex binaries **unchanged**. The only native code update is `windows-companion/w23/host.cjs` passive CDP Media event correlation introduced in W84.
- Internal event `PLAYER_DECODER_CELIKOM_SOURCE_MATCHED` only if actual decoder `kUrl` matches currently signed approved grant, `kIsPlaying` true, and the Yandex current track ID matches the grant. This is stronger than “grant accepted” or HTTP 206, but does **not** prove sound physically reached speakers. In case of actual CDP player error for same current grant, emits `PLAYER_DECODER_CELIKOM_PIPELINE_ERROR`. Both events only go to local allowlisted diagnostics. No additional popup banners or spurious text.
- If Yandex CDP doesn't expose `kUrl` on the owner's exact build, result remains *unknown*; the app doesn't lie and shouldn't stop music.
- **Rollback:** stable 0.24.29 in personal Library `/CELIKOM/Windows/CELIKOM-Windows-0.24.29-PROMO-FIX.exe`; Windows app same AppId; reinstall from rollback without uninstall/logout.
- Original before W86 reserve `backup/windows-w86-pre-02430-source-witness-20261113`; W86 source branch `experiment/windows-w86-02430-source-witness-owner-test-20261113`.
- W84 isolated diagnostic tests green: https://github.com/manufact-test/nomusic/actions/runs/43311056109
- All real owner audio testing must be done on W86 in real Yandex Music Windows app: long song, pause, seek, Next, My Wave/random, listening to original vs CELIKOM and observing diagnostic export after a reproducer. If music regresses, roll back to 0.24.29 and attach diagnostics. No claim that owner sound test passed.

## Build CI evidence
Pending final W86 0.24.30 Windows test installer run `43384063882`, exact SHA256 and Library upload.
