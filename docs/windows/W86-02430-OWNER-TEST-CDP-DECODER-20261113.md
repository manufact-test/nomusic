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
- **CI SUCCESS**: https://github.com/manufact-test/nomusic/actions/runs/43384241445
- Native tests (W22/W23/W60), W21 restore, W24 catalog, W15 login/entitlement, Windows build, Inno EXE, one-click update, **0.24.29 → 0.24.30 in-place DPAPI preservation and unchanged renderer.js** passed. Only the passive CDP host.cjs witness differs. CI line: `W86_02429_TO_02430_INPLACE_DPAPI_AND_ONLY_EXPECTED_PASS`.
- Exact extracted installer SHA256: `F289167A6106505FCFD46F89BE7B6DA34DAFD2DD27695AF3549F0D1A7BBD1AD8`; size **43,551,635 bytes**. The unsigned CELIKOM installer uses verified vendor Yandex files and doesn't modify vendor binaries during setup.
- GitHub Actions artifact: `14018310589`, https://github.com/manufact-test/nomusic/actions/runs/43384241445/artifacts/14018310589
- **Persistent ChatGPT Library upload verified:** `/CELIKOM/Windows/Test/CELIKOM-Windows-0.24.30-TEST-SOURCE-DIAGNOSTICS.exe` Library ID `libfile_e2c07d37b86c8191ad375857a5d44843`; exactly same checksum, 43,551,635 bytes.
- Local download at `/mnt/data/CELIKOM-Windows-0.24.30-TEST-SOURCE-DIAGNOSTICS.exe`. Explicit owner test and audio listening **not yet performed**. In case of problem install 0.24.29 stable from /CELIKOM/Windows, no uninstall.
