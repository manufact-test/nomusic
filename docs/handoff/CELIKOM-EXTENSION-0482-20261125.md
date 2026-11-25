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
- Source commit: `2532f18acacfe246bf7c57bfb299338430b32754`.
- Floki build run `45666962945`, job `139391596431`, runner `celikom-floki-ci01`: SUCCESS, 387 extension tests, 4 spool tests, manifest/security and SHA validation. The receipt exactly matches the local ZIP. Primary private spool: `/srv/celikom/ci-runner/runner/celikom-build-spool/2532f18acacfe246bf7c57bfb299338430b32754-45666962945-1/`.
- The independent package job `139391595937` in run `45666962906` ran simultaneously on `celikom-floki-ci02` and produced the identical extension digest. The downstream Windows-hosted job failed before steps; do not claim the whole Windows workflow passed or modify Windows to address it.
- Full CI `45666962928` and protected publication `45667178751` failed before any runner steps. Provider reason is not exposed by the available job result. No publication command or privileged server modification executed. Do not claim full CI, a 0.4.82 website URL or owner browser acceptance.
- The prepared, fixed-input publication request is retained at `.github/scripts/floki-extension-0482-verified-promote.sh`. It independently checks primary spool receipt/size/SHA, safe ZIP/manifest/API, immutable destination, existing private Basic gate, nginx rollback and API health; it does not execute spool code. Run only through the existing protected administrative channel after that channel can start, not on either unprivileged CI runner.
- Website remains at the previously published 0.4.80; private conversation delivery of 0.4.82 is `libfile_721f6850ab9081918ec6296ba004e214`. Administrative request is reset to safe no-op after the failed publication.

## Delivery constraints

Use the existing `celikom-ci-smoke-only` shared runner label, so an eligible free runner can pick up the build. Do not grant either smoke runner deployment secrets. Runner spool is untrusted data until independently verified by the existing protected publication mechanism. The historical root path describes the primary runner; do not assume it describes a newly provisioned reserve runner.

Owner acceptance: install/reload 0.4.82, reopen the Yandex tab, then exercise ordinary Next, rapid Next during VPN reconnection, Pause/Play and Return original. Remaining network symptoms require fresh bounded diagnostics; automatic tests do not establish live audible quality.
