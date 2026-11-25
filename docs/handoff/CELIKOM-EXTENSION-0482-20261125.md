# CELIKOM extension 0.4.82 — 25 November 2026

Extension-only follow-up to the owner's 0.4.81 VPN/Next report. Android, Windows, backend, access deadlines and the accepted playback architecture are not changed.

## Findings and changes

- Reproduced on 0.4.81: a newly visible CURRENT player title did not invalidate the preceding MediaSession identity until the new song entered the catalog. A direct conflict now suspends the old replacement without guessing the new Track ID from arbitrary page text.
- A private assigned/current source pair now yields a numeric resource revision. It is included in snapshot changes, preparation ownership, MAIN guard admission and intro binding. Late work from a previous resource cannot engage a new resource even when the track and media IDs are reused. Raw stream URLs are not added to diagnostics.
- A new resource clears recovery blocks belonging to the previous resource; manual Return original intent for the same track remains in force. A canceled resolve cannot reset a newer operation's fresh-resolution flag.
- The 0.4.81 bounded grant handling, same-Range retries and complete-file late alignment remain covered. No MediaSource live-join from withdrawn 0.4.71 is reintroduced.

The owner's roughly ten-second old-song incident is not fully retained in the bounded diagnostic trace; these reproductions identify real stale-binding paths, not proof that every reported interruption had one cause.

## Verification

- Local extension suite: 387/387, including packaged MAIN/ISOLATED lifecycle, continued stale metadata polling, same-ID resource reuse and delayed A/B/C resolution.
- Manifest validation and client security build gate pass.
- ZIP: `celikom-extension-0.4.82.zip`, 2,491,981 bytes.
- SHA-256: `f8c03532c26d6465191779229f414554b86ff01b19fa71cb849f4fdc0992d3ac`.
- API: `https://api.celikom.com`; browser host permissions remain this API and `https://music.yandex.ru/*` only.
- Floki runner build / private publication results must be recorded after execution. This checkpoint alone does not assert owner browser acceptance or a working website download.

## Delivery constraints

Use the existing `celikom-ci-smoke-only` shared runner label, so an eligible free runner can pick up the build. Do not grant either smoke runner deployment secrets. Runner spool is untrusted data until independently verified by the existing protected publication mechanism. The historical root path describes the primary runner; do not assume it describes a newly provisioned reserve runner.

Owner acceptance: install/reload 0.4.82, reopen the Yandex tab, then exercise ordinary Next, rapid Next during VPN reconnection, Pause/Play and Return original. Remaining network symptoms require fresh bounded diagnostics; automatic tests do not establish live audible quality.
