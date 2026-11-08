# CELIKOM Windows W4 — isolated file-info source adapter (2026-11-08)

## Owner W3 result — confirmed real machine
- Windows 10 19045 x64; official Yandex Music 5.126.1.0 running.
- Electron ASAR identity remains pinned: `5a259722d60f746ec32c8bf6e880e375e888315080fb18e67c29b54b582c1215`, `MATCH_OWNER_W1`.
- W3 full packaged scan: **1117 / 1117 JavaScript files**, zero skipped.
- `getFileInfo`: 19 packaged files, `getFileInfoBatch`: 3,
  `GetFileInfoResource`: 19, endpoint strings: 2,
  source marker + Webpack in the same file: 19.
- Source marker in preload-named JS: 0, renderer-named JS: 0;
  loadURL + Yandex host co-located in one JS file; loadFile found in three.
- Audio descriptor `downloadInfo` + `codec`: 2 JS files.
- **Inference**: resource-layer substitution is technically plausible, but
  these counts are **not** evidence of runtime calls, loaded modules, an
  authenticated player hook, working audio or safe hot restoration.

## W4 code & safety
`windows-companion/bridge/w4-source-resource-adapter.mjs` is an original,
independent, **in-memory** adapter for method-shaped resource objects
(`getFileInfo` and `getFileInfoBatch`) provided by isolated synthetic tests.
It is NOT injected into or installed on Yandex, and it does not play audio.

- Only prevalidated in-memory Blob URL belonging to a configured fixture
  origin; no signed backend URL, Yandex token or account/session captured.
- Requires exact ID, explicit active track ownership, authorized/approved
  version, duration match, fully validated asset, short expiry, and bounded
  cache. No metadata-name guessing.
- Calls original method before attempting transformation, preserving
  underlying original errors and untouched responses on unsupported schema.
- Detects track changes with generation fencing; delayed response from a
  previous track is never applied. Aborted requests stay original.
- Mixed v1/v2 batch keeps element order, leaves other tracks untouched.
- Original selection persists through duplicate same-track notifications.
  Stop prevents new substitutions; uninstall restores only adapter-owned
  prototype methods. No global audio interception or second media clock.

`windows-companion/bridge/w4-source-resource-adapter.test.mjs` runs
deterministic Node tests using **only synthetic resource classes and URLs**.
Dedicated Windows workflow executes these tests alongside existing W3
.NET read-only tests. The CI result will be recorded after verification.

## Known blockers and no-go boundaries
- W4 has **NOT** loaded an actual Windows Yandex renderer module;
  the public browser resource class from other branch is research only.
- A synthetic wrapper returning `codec=mp3, transport=raw` does NOT prove
  native Windows decoder will consume it. Electron actual native tests with
  licensed synthetic audio and original source class are still required.
- Already-playing decoder restoration is not yet implemented. Stop/Original
  only affects subsequent resource acquisition. Do NOT claim instant
  restoration, native pause/seek/Next, audio quality or full compatibility.
- Complete-file Blob preparation can delay cold start and may not support
  arbitrary track lengths. Must test streaming/Range, caching, lifecycle
  and expiry before productizing.
- No additional diagnostics needed from owner for W4; do not ask to rerun W3.
- **DO NOT patch/alter user-installed Yandex.** Only consider this after
  version-gated copy/backup/byte-verified rollback, legal review and explicit
  owner approval. Unsupported Yandex must play original.

## Next required engineering proof
Build isolated Electron fixture using public/pinned Yandex renderer resource
class (not a fake second playback app for customers), one synthetic/authorized
audio asset and **one native media element**. Prove actual raw descriptor,
pause/seek/Next, mixed batch, stale request, URL signing/Range, source expiry,
Stop/Original reacquisition, fallback. If it cannot be proven with narrow,
reversible integration, say no and do not silently create another player.

## Verified W4 checkpoint
- Commit `a47d1c847da62dde42490da3be4ec4f9f8d06661`.
- Windows Actions run [42509525224](https://github.com/manufact-test/nomusic/actions/runs/42509525224): **SUCCESS**, includes W4 17 Node synthetic contract tests, existing W3 .NET safety/build and Windows read-only publish.
- No owner-side W4 ZIP necessary: there is no new official-Yandex integration to run, and repeating static probes would be misleading. User W3 evidence is sufficient for this gate.
- W4 native Yandex real playback compatibility: **NOT PROVEN**.
