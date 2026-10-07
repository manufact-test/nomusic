# Client UI principles

Status: product contract for the later client UI stage. The Stage 1 popup is a technical shell, not the final design.

## Primary surface

The default client surface must be quiet, compact and immediately understandable. It exposes only the current state and four direct actions:

1. `Старт` — enable CELIKOM.
2. `Стоп` — stop replacement and leave the original player safe.
3. `Вернуть оригинал` — bypass replacement for the current track without reactivating a moment later.
4. `Добавить трек` — enter the guided upload/mapping flow.

The user must not need to understand Track IDs, drift thresholds, bridge state or internal phases. Diagnostics live behind a deliberate developer/support action.

## Secondary surfaces

Subscription is visible but does not crowd playback controls. It opens a separate account sheet containing:

- plan and entitlement status;
- next payment and auto-renewal state;
- payment action;
- promo-code entry;
- personal share/referral code or link;
- privacy and support links.

Adding a track is also a separate flow with progress, validation, conflict handling and a clear final state. It must never be disguised as a successful upload before the server confirms it.

## Behaviour rules

- Fail open: any uncertain state restores original audio.
- One primary action per state; destructive or billing actions require explicit confirmation.
- No autoplaying promotional UI, modal spam or permanent diagnostic overlay.
- Keyboard navigation, visible focus, reduced-motion support and readable contrast are required.
- Russian is the initial product locale; copy and layout must remain ready for English.
- Payment pages are server-backed and never rendered from untrusted extension HTML.
