# W25 — CELIKOM native main-process relay (2026-11-09)

## Как устроен реальный Windows клиент

1. CELIKOM.Companion.exe запускает локальный HTTP-сервер только 127.0.0.1:21471. Сессию CELIKOM хранит защищённым способом; пароль и сессия Яндекс.Музыки не читаются и не копируются.
2. Настоящий Yandex Music.exe 5.126.1 и собственный CELIKOM модуль в Electron main process: windows-companion/w23/host.cjs.
3. Main process читает свой локальный ephemeral capability и обращается к CELIKOM за состоянием и разрешёнными source grants. Никакого прямого localhost fetch из Yandex renderer, поэтому не нужно ломать CSP и настройки браузера.
4. Renderer musicapplication://desktop (windows-companion/w23/renderer-entry.mjs) получает only state и конкретные grant ответы через Electron executeJavaScript. Source-only W22 adapter подменяет getFileInfo / getFileInfoBatch внутри родного проигрывателя. Сохраняет штатный контроль Yandex: pause, seek, Next, очередь, радио.
5. W24 NativeIntegrationManager использует точную оригинальную версию и пару EXE/ASAR, W21 до установки сохраняет исходные файлы и умеет откатывать прерванные установки. Устанавливается только с подтверждения владельца в UI; неподдерживаемые версии не изменяются.

## Evidence

- [Authentic Yandex Windows CI 42622540129](https://github.com/manufact-test/nomusic/actions/runs/42622540129): SUCCESS, 35/35 Node, 61 native .NET. Defender real-time ON.
- Main process loaded, authentic renderer injected, resource hook attached. Local CELIKOM bridge GET /v1/state реально достигнут с правильным ephemeral capability; renderer получает state. Ранее CSP-блокировка direct fetch устранена переносом сети в Electron main.
- W24 actual manager install and restore verified; two original file hashes and original signature match after restore.
- [Single installer CI 42622515498](https://github.com/manufact-test/nomusic/actions/runs/42622515498): SUCCESS, artifact 13677290496 (CELIKOM-W24-INTERNAL-NATIVE-UNSIGNED).
- Положительные fixtures: native source MP3/AAC, batch-first, Next and Stop cancellation, native pause/seek methods untouched. Signed URL and exact ID checked; unknown grants fall back to Yandex original.

## Оставшееся продуктовое испытание

No authenticated account in GitHub Windows runner, thus no actual audible replacement / pause / seek / Next confirmed. Owner manual acceptance should happen ONCE with real approved CELIKOM track in installed Yandex, no Sandbox/terminal or separate mods. This test is required to distinguish source selection from actual audio playback.
