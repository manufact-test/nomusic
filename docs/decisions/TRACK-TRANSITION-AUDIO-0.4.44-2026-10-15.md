# Track transition audio leak — 0.4.44 (2026-10-15)

Owner reports a short fragment of another replacement when entering Зануда —
«Всё пиздато» (Yandex1944611, replacement10) from another song. The supplied
0.4.43 snapshot is already after the transition and cannot establish which
recording was audible. It shows healthy API/bridge and a preceding
replacement-play-blocked restore; no live audio asset has been changed.

## Reproduced failure and fix

A reused native media element can expose a new stream and the preceding Media
Session title at the same time, including songs of equal duration. Before the
fix the adapter confidently selected the previous Track ID. Separately, media
method observation waited for a microtask and metadata changes waited for
polling, allowing the old replacement to remain audible during transition.

Observe native play/load before calling the original method, still observe
afterwards, and observe Media Session metadata assignment synchronously. Keep
native loadstart in the normalized metadata events. New stream + unchanged old
identity is withheld until identity metadata refreshes; player DOM and Media
Session resolving to different known tracks also withhold admission. Duration
changes alone are not identity refresh. Metadata arriving before the new stream
is covered separately. The pending resource identity survives intermediate
DOM/session conflicts and is renewed for the next transition (A to B to C). Raw resource URLs stay inside MAIN and are not added to
diagnostics. Resource-change guard reason retains precedence over deliberately
withheld track identity, preserving existing recovery behavior.

A cancelled native play (AbortError) and a rejection from a superseded pause/play
attempt no longer produce replacement-play-blocked. Actual current autoplay
rejection still fails open. Ordinary seek, volume/mute and gain DSP are preserved.

If a stream is rebound with entirely unchanged identity metadata, the adapter
keeps original playback until a fresh identity update rather than guessing. No
fixed delay or song-specific exception is used.

## Validation and delivery

236 extension tests PASS locally, including equal-duration stale metadata,
conflicting identities, synchronous setter/play observation, normal seek,
metadata-before-stream, actual controller teardown/re-admission, cancelled vs
real autoplay failures, and the existing two-world packaged recovery cases.
New native Chromium regression uses decoded MP3, a real Media Session setter
and two blob resources to verify the previous replacement is muted/destroyed
before new native play and that fresh identity is delivered synchronously.
Private Chrome workflow38709031363 PASS, including the real native transition
regression, saved gain DSP/admin and support flow. Local lint/validation/security
and17 PoC tests PASS. Full PHP/MySQL CI38709036919 PASS, including signed Range native playback.

Complete configured archive CELIKOM-0.4.44-full.zip saved; SHA256
7a72f4a9763d529eabdfb3a37471ed9ce7681f65ccbe906ed1259fc37fca6e99.
Install in place over the existing unpacked extension, reload it and the Yandex
page, then test entering1944611 from several other songs.

Client-only update; live backend remains0.4.43-d7c2ab8b6ce142a2595573dcfb34d673b377e68d.
No server deployment, migration, music/gain/moderation mutation. PR6 remains open.
Owner confirmed the previous admin refinements are good. Listening verification
of the reported song with0.4.44 remains for the owner after installation.
