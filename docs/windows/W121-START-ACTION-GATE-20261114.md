# W121 — Gate duplicate Start actions during first connection — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W121 code backup: `backup/windows-main-pre-w121-start-action-gate-20261114` @ `9a9193d7bd728a4ff1a2da2f8b5f11c42c4d8a7b`.
- W121 implementation commit: `62ff2b67f869607e20e9d8899113f391eab80c7e`.
- Exact green rollback snapshot: `backup/windows-main-post-w121-ci-green-20261114` @ the W121 commit.
- Main CI [43597478523](https://github.com/manufact-test/nomusic/actions/runs/43597478523) and Windows integration CI [43597478531](https://github.com/manufact-test/nomusic/actions/runs/43597478531) — **SUCCESS**.

## Changes

- Added the pure `PlaybackStartGate` policy and use the same rule in both the Start handler and Start-button availability.
- The gate blocks Start while the bridge is not ready, integration/update is busy, a previous Start is still pending, the app is closing, or playback is already enabled for the active native module.
- `StartAction` immediately calls `UpdateSafe()` after setting `_compactStarting`, so repeated clicks cannot be silently accepted by an enabled-looking button and then ignored.
- During the initial host/entitlement check, the compact hint says `Проверяем Яндекс.Музыку…`; the normal loading status remains for the active Yandex startup phase.
- W15 tests cover each blocked/allowed gate state; the Windows integration workflow statically guards both call sites and the pending-start hint.

This addresses the duplicate-click race in the first/repeated Start flow. It does **not** close the broader first-run/reboot/autostart owner acceptance, and it does not change audio, native installation, VPN or updater behavior. No installer was built.

