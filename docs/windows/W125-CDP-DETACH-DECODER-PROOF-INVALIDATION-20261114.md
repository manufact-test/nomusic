# W125 — Invalidate current-decoder proof when CDP detaches — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W125 code backup: `backup/windows-main-pre-w125-decoder-detach-invalidation-20261114` @ `efbd6a1b1965472d8ad29519621a09d45a8651da`.
- W125 code HEAD: `d083218b4adb0b7fb1d1321d09b56245ab40fbd1`.
- Exact green rollback snapshot: `backup/windows-main-post-w125-ci-green-20261114` @ the W125 code HEAD.
- Main CI [43601333189](https://github.com/manufact-test/nomusic/actions/runs/43601333189) and Windows integration CI [43601333191](https://github.com/manufact-test/nomusic/actions/runs/43601333191) — **SUCCESS**.

## Change

The native host previously logged `PLAYER_CDP_DETACHED` but retained the last verified decoder witness. If the passive CDP observer detached after a valid `kUrl + kIsPlaying` pair, a stale proof could remain eligible for the green UI state for up to ten minutes.

On a valid webContents CDP detach, W125 now immediately clears:
- the verified current-decoder witness;
- expected signed audio and native media-success evidence;
- observer-ready state and bounded unfetched-reload attempts;
- cached decoder-player property state.

The existing renderer status can therefore fall back to mapped-but-unverified. It does not claim that a replacement is playing after losing the observer that proved it. The host does not try to seize or reattach DevTools; this path intentionally fails closed.

Windows integration CI now checks that the detach handler invalidates the witness and observer state. No playback command, reload, audio source, VPN behavior or original file was changed.

## What remains open

- #52 remains OPEN. W125 closes only the stale-proof-on-detach edge case; the real «Ты» playback/source behavior still needs owner-PC evidence.
- CI is not audible acceptance. No installer was built and no owner installation was requested.

