# W132 — VPN A→B revalidation after verified source-left — 14 November 2026

- Repository: `manufact-test/nomusic`.
- Product: the one existing CELIKOM Windows application.
- Working branch: `main` only.
- Change type: regression coverage only; no runtime behavior changed.
- Exact pre-W132 backup: `backup/windows-main-pre-w132-vpn-source-left-revalidation-20261114` @ `507052a14841ee08bf2ade513315618612130e8a`.
- W132 test/current code-test HEAD: `c02cd4988292598f81e857062279d0179253a42a`.
- Main CI [43607847556](https://github.com/manufact-test/nomusic/actions/runs/43607847556) — **SUCCESS**.
- Windows integration CI [43607847627](https://github.com/manufact-test/nomusic/actions/runs/43607847627) — **SUCCESS**.

## Coverage added

A renderer integration test now covers the complete source-left/revalidation sequence for one current Yandex track:

1. The track initially receives a valid CELIKOM replacement grant.
2. The passive CDP witness confirms that the current decoder has left the CELIKOM signed source; W131 clears the stale mapping and cancels any future duplicate restoration.
3. VPN A→B causes the native state to turn off. The renderer must not issue another `QUALITY_CHANGE` reload of the already-original source.
4. VPN B becomes available and native state turns on again. A fresh authenticated resolve returns no active replacement for this exact track.
5. The original Yandex decoder remains untouched: no source reload, no replacement reload, no loss of playing state or playback position.

This complements W98's test for a track that is original from the outset and W131's source-left/state-off race test. The full W22/W23/W60 original-source, VPN, 403 and audio regression step passed.

## Acceptance boundary

W132 proves the renderer's no-reload behavior for this simulated state sequence. It does **not** prove that Yandex itself produces no audible pop during a real Windows VPN A→B network route switch. The owner's physical Windows playback check remains required; issue **#58 stays OPEN** until that check is accepted.

No installer was built. Continue on live `main`; preserve the one-product, exact-backup, no-intermediate-installer rules.
