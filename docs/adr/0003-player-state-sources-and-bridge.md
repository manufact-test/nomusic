# ADR-0003: Player state sources and isolated bridge

- Status: accepted for Stage 2 validation
- Date: 2026-10-07

## Context

The accepted PoC proved exact Track ID detection and master-media selection on the current Yandex Music SPA. Production code must preserve that evidence without allowing service-specific DOM, network or page-world details to spread through the extension. It must also survive SPA navigation, detached audio elements, repeated initialization and stale events.

## Decision

Production playback observation uses three boundaries:

1. `ServiceAdapter` is the stable client contract. It exposes `mount`, `unmount` and `getSnapshot`, and emits normalized snapshots and `PlayerEvent` values.
2. `YandexMusicAdapter` is the only component that knows Yandex selectors, `__STATE_PATCHES__`, Yandex JSON responses, route shapes or advertisement-media heuristics.
3. `PlayerBridge` transfers versioned data from MAIN world to the isolated content script through the namespaced `CELIKOM_PLAYER_V1` protocol.

The adapter resolves Track ID from multiple corroborating signals:

- track objects from state patches and bounded inline state;
- passive, size-limited JSON observation on Yandex-owned domains;
- Media Session, player bar and active-card metadata;
- player-scoped links and data attributes;
- the current route only as a weak fallback.

The selection is fail-closed. An ID below the confidence threshold or within nine points of another ID is not selected. Raw stream URLs, cookies and account credentials are neither extracted nor transferred.

Master media is selected from connected and detached `audio`/`video` elements. Known advertisement video is rejected, CELIKOM-owned media is excluded, and playing audio receives a deterministic priority. Media method and history wrappers are restored only if they are still owned by the adapter.

Normalized events are `TRACK_CHANGED`, `PLAY`, `PAUSE`, `SEEK`, `TIME_UPDATE`, `VOLUME_CHANGED`, `RATE_CHANGED`, `METADATA_CHANGED`, `ENDED` and `ERROR`. Every MAIN-world envelope has a session ID and monotonic sequence. The isolated bridge ignores foreign sessions and stale sequence numbers.

## Lifecycle contract

- `mount` and `PlayerBridge.start` are idempotent.
- `unmount` removes media, navigation and observer listeners, clears timers and restores owned wrappers.
- A new bridge session unmounts the previous adapter session before attaching.
- A visible-page heartbeat timeout detaches the adapter; the isolated bridge immediately reconnects with `INIT`.
- The adapter observes only in Stage 2. It never changes playback state or audio output.

## Consequences

Replacement and synchronization in Stage 3 can depend on one normalized player contract instead of Yandex internals. A future service integration supplies another adapter without modifying the content controller. The cost is a small MAIN-world observer and passive response cloning bounded to JSON bodies no larger than 5 MiB and 20,000 visited object nodes.

