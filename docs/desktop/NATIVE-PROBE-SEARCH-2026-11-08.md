# Read-only engine probe 0.0.2 — owner search failure

Follow-up: probe 0.0.2 found the owner controller but exposed a wrong Playback state path. Current check is 0.0.3; see [NATIVE-PROBE-STATE-2026-11-08.md](NATIVE-PROBE-STATE-2026-11-08.md). Historical evidence below is unchanged.

Scope: `experiment/desktop-native-probe-search-20261108`, based on `4d33706b546a33c7db61db726d183907b1b72cef` from the lifecycle research branch. Accepted 0.4.73, product source/manifest, server and Android are unchanged.

## Owner evidence

Owner returned probe data at `2026-11-08T13:11:32.107Z`: controllerFound/found false, no binding, no search trace. This proves only that the original discovery did not find a controller. It does not prove that native source replacement is impossible or establish the exact cause on the owner's page.

## Confirmed shortcomings in the first probe

1. It inspected up to 16 nodes matching exact player selectors and enumerable React fiber keys only. A different player layout or non-enumerable root could be skipped.
2. It checked three named prop values while walking `.return`; it did not inspect committed context dependencies or alternate fibers. The actual pinned Yandex React renderer maintains `dependencies.firstContext.memoizedValue`, including for context consumers. Real playback is not established by a hand-written provider-only fixture.
3. Its generated reader returned early whenever the old global reader existed. Updating/reloading the extension on an ALREADY OPEN Yandex tab could keep the older reader code. This behavior is independently reproduced by a regression, not inferred from the owner's one result.

## Changes

- Broaden discovery to player/control/media seeds and bounded DOM fallback, getOwnPropertyNames for non-enumerable roots, context dependency lists, alternate fibers and a small whitelist of controller wrappers. No arbitrary recursive app-state enumeration.
- Bound search to 100 ms / 4096 DOM nodes / 12000 fibers / 4000 candidate objects, with per-path/context bounds and cycle detection. Return explicit `limited` and count metadata when work is incomplete.
- Report seed counts, visited nodes/fibers/contexts/candidates, getter failures, match source and readerVersion 2. No HTML/text, account identifiers, private objects, credentials or audio URLs are serialized.
- Inspect uses one controller search rather than repeating the broad scan for each field.
- Add a reader version guard and replace an older global reader in place. Same-version reinjection remains idempotent; a fresh inspect reads the current DOM. Popup reports extension probeVersion 0.0.2.
- No invocation of reload/play/pause/source loaders during discovery. The generated reader continues to expose only inspect/version, and the separate probe has no background task or blanket host permission.

## Verified

Functional commit `f2871db8bbb1ec5a1a255513698b96a4e84ddc45`.
[CI 42484351341](https://github.com/manufact-test/nomusic/actions/runs/42484351341), job `128742865275`: SUCCESS.

- Chrome 156.0.8078.79 and Brave 157.1.99.55: each passed the native/media suite plus three discovery checks using the ACTUAL React renderer/context implementation downloaded from Yandex's pinned public frontend.
- The React consumer was rendered outside known player selectors; the new finder found its controller through `fiber-context`, while all fake engine control callbacks remained uncalled. This proves the discovery path, not the presence of that controller on the owner's page.
- 29 lifecycle/discovery cases plus 3 generated-reader cases passed, including non-enumerable roots, dependency-only values, alternate fibers, getter faults, cycles, stale reader replacement, current-DOM refresh and non-mutation.
- All 360 accepted desktop regressions passed; repository lint passed.
- Read-only anonymous real-site probes still found no active controller, with 22 observed context dependencies. This remains separate from a signed-in playing owner tab and is not claimed as a successful live playback binding.

## Delivery / required one-shot owner check

`CELIKOM-Engine-Check-002.zip`: 5134 bytes.
SHA-256: `30e05189bb6013028986545e490a8c690c8a93dd8f4bc4af2f4cf8cae754ec39`.
Persistent Library identity remains `libfile_6fcfc601349881919dc743c12ac355e3` with version history (latest contains probe 0.0.2); local delivery name includes 002.

Extract these five files over the EXISTING separate engine-check extension folder. On brave://extensions reload ONLY “CELIKOM — проверка движка”. On the already open Yandex tab with a song playing, open the check extension and copy the new result. No Yandex refresh is required for replacing the old reader, as verified by the generated-reader regression.

Expected freshness: top-level probeVersion `0.0.2` and engine.readerVersion `2`, with engine.discovery counts even if controllerFound remains false. Use that trace to determine whether the owner's page lacks matching roots, hits a search budget, or exposes contexts with a different controller shape. Do not infer a live native backend is ready until exact binding and lifecycle behavior are demonstrated.
