# W93: Windows gain pre-render, guarded private registration (NO LIVE DEPLOY)

Source Windows chain: W90 gain metadata, W91 signed sidecar, W92 passive source/volume/performance observers. All experimental, **not installed on owner PC**.

## Why
Live read-only [43438999212](https://github.com/manufact-test/nomusic/actions/runs/43438999212):
- 1499 total replacement versions, **2 with gain >0**: 1944599 "Папиросы" (disabled, +12 dB) and 40371622 "Биг сити лайф" / "Триагрутрика" (active, +11.5 dB), **1492 of 1493 active versions are 0 dB**.
- 4 actual admin gain edits across 3 versions: replacement5 0→12 (later disabled); replacement2 0→0.5→0; replacement37 0→11.5. No evidence of mass admin gain reset.
- Windows old raw audio path ignored gain_db. Big City Life *mid-song* dip is separately unresolved; no captured event at exact time.

## Offline architecture and safe release conditions
- Hostinger production has **NO ffmpeg or ffprobe** verified via read-only job [43435848544](https://github.com/manufact-test/nomusic/actions/runs/43435848544). Do not try CPU-heavy on-the-fly PHP audio transcodes.
- `scripts/windows-gain-render.sh ORIGINAL.mp3 RENDER.mp3 11.5` uses offline ffmpeg with bounded limiter and duration/size checks. Original audio files remain untouched. GH CI only runs synthetic tone, no private owner song transferred.
- migration `020_windows_gain_variants.sql` adds private metadata only; don't run until deployment gate. Windows `?audio_profile=windows_gain_v1` opt-in returns signed derived audio only on exact match of active approved row, source SHA, version, gain dB, duration, mime, bytes and private storage key. Signed variant HMAC is separate and session+variant digest scoped. Chrome/extension always resolves ordinary original and still performs its own Web Audio gain.
- New `server/bin/windows-gain-stage.php` operations-only CLI, **never called by HTTP or cron**. Requires private staged MP3 under `STORAGE_PATH/incoming/windows-gain/`; positional flags `--replacement`, `--source-sha`, `--source-version`, `--gain-db`, `--render-sha`, `--file`. Dry-run is default, no writes. Commit additionally requires **`--commit` + `CELIKOM_W93_ENABLE_STAGE=YES_EXPLICIT_PRIVATE_STAGE`**. Locks exact approved version, verifies gain/hash/duration/MP3, refuses stale or mismatched sidecar overwrites, stores under private hashed key and inserts an isolated DB row. Errors do not expose filenames/SQL/music bytes/tokens. NEVER invoke commit without the operator's deliberate field QA gate.
- Registered Windows-only offline file is **not** active until an owner-approved server deployment of the migration + server code. Rollback: old source/installer branches untouched; remove feature request in Windows (old clients have no `audio_profile`), or revert server `ResolveService` profile route, and retain original media/DB. Never roll back original `audio_assets`. A pre-render may be stale if admin edits gain during playback; current signed URL then 403 -> fresh resolver; avoid changing gain mid-session, test 403/crossfade/no hiss before rollout.

## Tests and what remains
W91 [43437638500](https://github.com/manufact-test/nomusic/actions/runs/43437638500) SUCCESS: PHP signed Range/HMAC/variant stale+no-double-gain contract, independent synthetic ffmpeg, W15 .NET, W22/W23 Node and Windows compile. W92 [43438578606](https://github.com/manufact-test/nomusic/actions/runs/43438578606) SUCCESS: passive CDP native source lost/volume decrease, electron stall evidence, + all W89 source/403 regressions; no app installer built or deployed. W93 CLI syntax/guard must pass CI before any operations.
Remaining: production-representative MySQL migration/CLI dry-run in disposable DB; full host HTTPS/proxy Range test, real audio metering/provenance before/after Big City Life dip, owner 0.24.33/0.24.34 real VPN and "Ты" QA, no hiss, Brave profile before declaring stable.


## Full disposable MariaDB and private stager integration CI
[W93 run 43440173979](https://github.com/manufact-test/nomusic/actions/runs/43440173979): SUCCESS on both jobs. Linux ephemeral MariaDB 11.4, real migrations 001/018/020, synthetic sine MP3 original+offline boost, PHP Mp3Inspector, private staging CLI dry-run, explicit authorization deny/commit, idempotent retry, persistent variant row exactly one, original audio SHA unchanged, no production credentials or music read. This validates staging mechanics, not the acoustic quality of Big City Life and not live Hostinger compatibility. No production migration or SQL write.
