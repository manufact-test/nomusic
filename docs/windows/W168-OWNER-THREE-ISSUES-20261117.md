# CELIKOM Windows W168 — owner report 17 Nov 2026

## Scope and starting point

- Working branch: `experiment/windows-w167-owner-ui-regressions-20261116`
- Starting branch HEAD: `31e364bfba8795f84502f050d6716b2b6639f5cf`
- W168 pre-edit backup: `backup/windows-w168-before-owner-three-fixes-20261117` at the same HEAD
- W168 UI source commit: `2c352479b267266cd62fab7d8221bab97051c539`
- Proposed UI owner-review version: 0.24.50.0; **native module stays 0.24.31**.
- User explicitly requires exactly three issues assessed, **NO VPN/network recovery change**, no audio/source routing change, no W166 resurrection, no other UI change.
- Original W167 0.24.49.0 remains available in Library and source backup. main untouched.

## Owner issue 1: missing first-track guidance

After Start and native attach, before the user picks any song, the track row was blank. Restore `Откройте Яндекс Музыку и выберите песню.` only for an actually connected first session with unknown playback and no valid track observed for 2.5s. Do NOT show it while connecting, disconnected, paused, stopped, no player, or during Next / short metadata gaps after the first real track. Keep the existing immediate green Start banner and W164 metadata-grace logic. Implemented in CompactPlaybackPresentation, CompactPopup and StartAction; focused tests added.

## Owner issue 2: status colors (screenshots)

- `Версия CELIKOM доступна` should be **green** when presence for the current valid track is approved; this only claims availability, **not audible replacement proof**.
- `Пауза` should be **green** while the native service connection is actually live. On player loss/stale heartbeat, never show a false green pause.
- `Играет версия CELIKOM` remains guarded by exact current native decoder proof (`NATIVE_SOURCE_VERIFIED` + current playing + approved + fresh). No green claim from 206, mapping or generic PLAYING.
- This corrects W167's incorrectly neutral available and paused text, preserving original text and layout. Focused tests added.

## Owner issue 3: Yandex Music unexpectedly closes/reopens near end of song

Owner supplied two diagnostics from 0.24.49.0. VPN transitions are explicitly NOT the bug; those were accepted and still allow seamless music playback. Do not change VPN recovery or overlay display.

**Verified independent Yandex main-process restart in `диагн.txt`:**
- 2026-11-17 08:13:53.757Z: PLAYER_ENGINE_PAUSED
- 08:13:54.234Z: PLAYER_CDP_DETACHED
- 08:13:54.239Z: HEARTBEAT_UNAVAILABLE
- 08:13:54.798Z: HOST_LOADED
- 08:13:55.543Z: RENDERER_INJECTED / RESOURCE_ATTACHED; reconnected shortly after.
This establishes native host/main reinitialization, **not the underlying reason it restarted**. No logged CELIKOM `NATIVE_TOGGLE_RELOAD_REQUEST`, `NATIVE_REPLACEMENT_SOURCE_RELOAD`, crash reason, external update event or deliberate Start immediately before it. The prior active source was `SOURCE_ORIGINAL` (08:10:56.681Z), with a prolonged clean heartbeat before main restart. W167 only changed W15 UI, not W23 host/renderer (still 0.24.31).

**Different event in `Вставленный текст(20261117-084639).txt`:**
- 08:43:06.041Z: LOCAL_HTTP_ERROR / STATE_UNREACHABLE
- 08:43:07.311Z: PLAYER_CDP_DETACHED
- 08:43:15.832Z: GUI_STARTED (CELIKOM companion restarted)
- 08:43:21.126Z: HOST_LOADED (Yandex)
This second event includes CELIKOM GUI restarting, so do not conflate its trigger with the Yandex-only restart at 08:13:54. Owner emphasizes the Yandex-only restarts, not VPN disconnects.

**Important:** Cause of Yandex spontaneous restart is NOT established by available diagnostics. Do not claim it is fixed or ship a speculative host/renderer hook, change source recovery timing, disable CDP, interfere with updates, or reset Yandex. For proof, next evidence must distinguish Yandex main process crash, graceful quit/auto-update, and renderer failure via native process exit/WER logs; correlate precisely with these UTC times. Windows user crash event logs may be required. No safe behavioral change can be justified from these two exported event streams alone.

## Build acceptance

- Keep one internal W20 owner-review installer/ZIP only; no public deployment.
- W20 tests should pass W15 native contracts, W23 host tests, W24 native image tests, Windows warnings-as-errors compilation, and stage-only guard.
- Manual test: Start connection/hint, first song, Next (no prompt flash), confirmed availability green, Pause green, absence of false `Играет...`, and whether random Yandex restarts recur over ordinary playback.
- Do not claim owner runtime acceptance before owner's own test.
