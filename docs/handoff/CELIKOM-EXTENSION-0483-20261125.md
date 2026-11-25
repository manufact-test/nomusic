# CELIKOM extension 0.4.83 — repair of the 0.4.81/82 full-file restart

## Owner finding

Installed 0.4.82 diagnostic, `Вставленный текст(20261125-184645).txt`: zero successful activations, healthy MAIN/ISOLATED bridge, access not suspended, auth/entitlement/resolve HTTP200. On the final track144530503 the controller reports `loading-complete-file`,17,797ms preparation, first524,288bytes received and HTTP206 continuation reading. Earlier positive tracks were canceled by Next while still preparing. Resource revisions are stable per track. Body progress within the continuation was not exported, so the trace does not prove the server sent zero bytes or a specific server failure.

The controller introduced in0.4.81 broadened full-file MP3 preparation to ordinary late resolves and replaced an already prepared MSE decoder after native intro timeout. This discards verified stream bytes and requires a second download of the complete file.0.4.82 inherited this regression. The existing tests asserted that conversion rather than protecting ordinary delayed adoption. Parallel main work since0.4.82 did not change extension playback sources; live host changes have not been independently audited in this repair.

## Narrow correction

- Restore the pre0.4.81 ordinary MP3 guard/sync route, preserving its current streamed decoder when resolve or initial decode is late. No whole-file conversion/restart for an ordinary delayed intro.
- Keep accepted complete-file alignment for the pre-existing newly-approved-mid-song case only. Keep0.4.81 bounded Range/network retries and grant deadlines, plus0.4.82 track/resource fences and manual Original behavior.
- No0.4.71 prepareJoin/live-join reintroduction, no Android/Windows/backend/production data changes, no central publication service changes.

## Verification

Three regression scenarios fail on0.4.82 before correction: delayed resolve, delayed decoder at2.4s, delayed decoder at17.7s, with complete-file preparation held pending. Additional test runs the actual ReplacementController and ReplacementPlayer classes together with a simulated media/206 transport and checks one decoder and one byte-zero request. It also fails against the archived0.4.82 controller. These are automatic component/integration tests, not live native Chromium audible proof.

Local full extension suite389/389 PASS; manifest/security pass. ZIP `celikom-extension-0.4.83.zip`,2,491,815bytes, SHA256 `647c1d2d694bb529568c85139c55f15f7d5c9747d5ced3e80f1f8bb4a45cad23`.

0.4.82 was removed from `.github/release/extension-owner-promotions.json` in33de3505041c3abbeaa3127d7ce2f3c481d16b3a after the owner failure. Do not restore its approval. This did not delete already delivered files or change an existing site latest pointer. Approve0.4.83 only after its exact Floki build succeeds. Record CI source/run/receipt and delivery after execution; do not assert a website link or owner acceptance from this checkpoint alone.

Owner next check: reload the same unpacked extension and Yandex tab, ordinary positive tracks first, then VPN/Next. A slower connection may still delay initial verified bytes; this correction removes the unnecessary second full download rather than promising zero network latency.
