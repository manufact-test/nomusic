# CELIKOM extension — baseline audit and release hold,25 November2026

## Owner steering

After repeated0.4.81–83 regressions, owner requested comparison with the accepted pre-migration implementation rather than further symptom-driven changes.0.4.84 is saved and tested but NOT approved/released; `.github/release/extension-owner-promotions.json` remains empty. Do not automatically promote82/83/84 based on this audit or test counts. Existing immutable files/latest pointer were not modified here.

## Verified reference

Accepted source0.4.73:89726d1f5af42f4f97e1597e89499d9ee17e29db. First migration candidate0.4.79:0e7d22025ff6f968478b30e61444d168c1c16830. Three playback blobs are IDENTICAL:

| File | Git blob SHA1 in both |
| --- | --- |
| extension/src/player/replacement-player.ts |13be2197e33bcaf8109616f3f4c1c94ea7d168b7|
| extension/src/player/replacement-controller.ts |070f270de0ef82629d9a79813e5c4706d32a614d|
| extension/src/player/sync-engine.ts |6a5499676eefbee77f042e7cf7dfe66fd13b0d0a|

Original0.4.73 ZIP was already rebuilt byte-identically in the migration acceptance record:SHA256968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb. The existing immutable control package already targets api.celikom.com; do not reconstruct an assumed Hostinger-only version from memory. No need for a new architecture or separate product.

## Distinguish causes

1. Introduced regression:0.4.81 broadened whole-file MP3 joins and discarded an existing streamed decoder after the intro deadline.0.4.82 inherited it;0.4.83 removed it. This was our client change, not evidence of a server migration defect.
2. Existing latent condition:0.4.73 already requested64KiB first and512KiB next, and its ordinary guard/sync could seek beyond buffered audio while keeping original muted. The captured0.4.83 state is native43.73s, replacement seeking39s/readyState1,buffered0–2.533877s,first64KiB only. Running the new captured-seek regression against the exact0.4.73 controller also fails: it remains REPLACEMENT_ACTIVE instead of yielding original. This does NOT contradict the owner's historical successful listening; it shows old code is unsafe under the currently observed buffer condition.
3. Why that buffer condition now occurs remains UNPROVEN. Different network/VPN path, actual Floki audio-body throughput, Nginx/FPM buffering or load could expose it. The diagnostic has no per-body progress, so body phase alone does not identify a server stall. API JSON200 and audio206 headers do not establish complete transfer speed.

## Server source comparison

Between reference89726d and audited current main, the following repository blobs remain identical:
- AudioController.php:d49a69e556635b29e179f261508be567ec3f2eb6
- Response.php:6757ef9500a44d0ad89f480b5d4dbbae9271fa99
- AudioAccessService.php:a64a9bd387bbc182686334e3cee064ce9ef5cf13
- ByteRange.php:bfdc05ba8adb0ca20177523c73aad324ecfa9b3b

AudioController reads/echoes64KiB pieces within the requested range. Client arrayBuffer() appends only after the entire requested response is read. This makes response size vs available playable buffer relevant. Git equality does NOT verify deployed live PHP bytes, Nginx/FPM configuration, disk/network performance or equivalence to historical Hostinger configuration. No such live audit was performed here; do not blame or exonerate Floki from these source comparisons alone.

## Saved candidate, not acceptance

0.4.84 candidate sourcec13049e83609424b29bfa158f7d10e98de8faab5; functional changesd22c98a99eaab21ea82af6c84b9ccc3c7f484889. Local+Floki run45683261081/job139449054898 PASS397 tests,4 spool tests,manifest/security and identical ZIP hash9f702a53c161b4bcf020fa4c2fd2d749f67ea09aaf6b13ba9986c0d02c7dd463,size2492831. Earlier run45683003706 failed a test that assumed projected running time stayed exactly0.1; test corrected to capture the unchanged pre-seek position. Production ZIP unchanged. Candidate keeps original audible while retaining missing-buffer downloads and uses smaller initial continuations. No live native Chromium audible proof: local browser binary absent; media tests are simulated. Do not convert these passes into owner acceptance.

## Next bounded investigation

Use the exact0.4.73 control with the new API and compare the SAME signed audio content/current authorization under matched network conditions; preserve trial/access/payment state. The key missing measurement is complete64KiB vs512KiB Range bodies, time to headers, time to last byte, exact byte count and hash, at offset0 and a later offset. Compare cold/warm and sequential requests; do not just measure health/config or headers. Inspect live deployed AudioController/Response hashes and relevant Nginx/FPM buffering/timeouts/rate limits/load read-only. Never print tokens or credentials. Obtain authorized probe access through the existing protected infrastructure mechanism; ordinary isolated CI must not receive production secrets or bypass its network restrictions. Hostinger remains rollback-only; do not enable/modify it for this audit. No new server source/config change or customer publication until actual evidence identifies the mismatch.
