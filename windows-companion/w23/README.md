# CELIKOM native desktop Yandex integration

- host.cjs: Electron main-process relay; only fixed local state and signed audio grant responses, without exposing CELIKOM bridge capability to Yandex renderer
- renderer-entry.mjs: attaches independently to official Yandex getFileInfo / getFileInfoBatch, requests exact track ID via main process queue, leaves native Yandex player, pause, seek and Next intact
- build.mjs: bundles our renderer script into dist/renderer.js at CI build time; no Node required on user Windows
- native-host.test.mjs: main process transport contract, trusted origin and capability isolation
- renderer-relay.test.mjs: real bundle with synthetic Yandex resource, positive single and batch/Next, Stop and native controls
- w23-host-smoke.ps1: ONLY disposable GitHub Windows runner, authentic Yandex 5.126.1, installed CELIKOM GUI, guarded patch/recovery and redacted proof
- W24 native .NET manager + W21 two-file recovery handle one-button connect and restore

Verified: real host [CI 42622540129](https://github.com/manufact-test/nomusic/actions/runs/42622540129) SUCCESS; single-install staging [CI 42622515498](https://github.com/manufact-test/nomusic/actions/runs/42622515498) SUCCESS.

Not yet checked: real audible approved track in an authenticated Yandex session. No second player, no Windows security exceptions, no manual mods.
