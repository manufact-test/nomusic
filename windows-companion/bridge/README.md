# W4 source resource adapter

Isolated fixture only; never runs in the owner's installed Yandex Music.

- `w4-source-resource-adapter.mjs`: in-memory source method wrapper with
  strict exact-ID / generation fencing, prepared Blob only, v1/v2 mixed-batch
  preservation, original-first semantics, and conservative cleanup.
- `w4-source-resource-adapter.test.mjs`: no-network, no-Yandex,
  no-audio synthetic Node contract tests.

Run locally: `node --test windows-companion/bridge/w4-source-resource-adapter.test.mjs`.

A passing test here **does not prove native Yandex decoding**. This adapter
does not install itself, patch ASAR, read credentials, or own a player.
It deliberately requires the real call-site and active renderer ownership
to be independently proven before a live integration can exist.
