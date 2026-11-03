# Desktop 0.4.70: bounded native intro and mid-song adoption

Status: experimental; owner listening acceptance pending. Desktop only.

## Reference and isolation

Accepted desktop 0.4.68 remains frozen at `archive/desktop-0.4.68-accepted-20261103` (43f9ade7b8e7bb1668818f10a7086efd940bffd6).
This experiment starts from 0.4.69, remote parent 3e4371da38151f06cad52adbcf2317ef427ceee3.
Only `feature/desktop-070-bounded-intro-start-20261103` is published. No server deployment, stable branch update, Android edits or signing changes.

## Intro

Previous timings show original clock already advances while the asset resolves/loads. No reliable next-track queue is exposed by the adapter; catalog ordering must not be treated as queue order.
For a high-confidence, duration-matched, already guarded native beginning (0–250 ms), defer the native play invocation until the replacement is prepared, for at most 400 ms. This is an intentional bounded start delay, not a rewind or a global timestamp offset. The existing initial Yandex position is preserved.
A negative result or Stop restores original playback immediately; timeout restores original and keeps the same in-flight preparation. If a numeric preparation lease was released, renew its generation before later activation. Pause/load reject the pending play with AbortError. Identity/source changes cancel stale play. Ordinary mid-song play is not deferred.

## Owner report: approval while listening

Owner reports abrupt interruption when newly uploaded audio is approved during native playback. No new trace proving the particular approval failure was supplied. Code review found a relevant ordering hazard: guard acquisition preceded the first replacement decoder seek at the current native position. This can silence the original while the decoder is still seeking.
For an unguarded, playing mid-song master, position the replacement while it remains muted and original remains audible. Await decoder seek readiness before acquiring the guard. Bound preparation at 1200 ms; reject a join more than 300 ms behind the continuing native clock, preserving original playback and scheduling a bounded automatic retry. Track/operation ownership is rechecked after async preparation and fresh snapshot. Avoid forcing the same initial seek again after guard acquisition. Existing pause/seek synchronization and exact-ID authorization remain in place.
This changes join ordering; it does not claim an acoustically verified crossfade.

## Checks

Local extension suite: 354 passing tests; repository lint passing. New regressions cover bounded intro positive/negative, repeated play, pause/load, source change, Stop, deadline, valid late lease, and stale mid-song join after track change.
A separate workflow runs actual Chrome media tests for the native held clock and release, plus muted position preparation before mid-song adoption, alongside existing MP3/M4A, gain, pause, seek and fail-open checks. Delivery status and archive digest are recorded after workflow completion.

## Owner listening check

Reload this unpacked extension in chrome://extensions and refresh the Yandex Music tab. Check the opening of «тело» on several starts, an ordinary pause/seek, and approval of a newly uploaded version while its original is playing. One combined diagnostic after that is enough. Keep accepted 0.4.68 for rollback. Browser tests cannot prove the first phoneme is audible on real Yandex audio.
