# CELIKOM Android single-player Gate 0/1 precursor

Isolated, **offline pure-Java source-selection gate**, not a functioning Yandex patch, not an APK and not evidence of access to Yandex internals.

Run: `bash android/one-player-prototype/run-tests.sh` (JDK 8+).

- One decision per track **before** host player load. Caller owns **one** player and the original source.
- Candidate must be approved, entitled, fully cached, integrity-checked, edition-exact, and within a 1.5s duration tolerance. Only a narrow `content://` URI is eligible for a replacement; actual granting and readability must be checked by authorized host.
- No catalog identity inferred from aliases or title matching. Without verified **internal** catalog + edition identity, the original is used unchanged.
- No credentials, login, network requests, proprietary APK, playback interception, root, accessibility, notification listener or second MediaPlayer.
- The reference catalog ID 42884423 for RASKOL is taken from CELIKOM's previous external diagnostics. It does **not** prove an internally retrieved Yandex catalog ID; edition labels here are synthetic test data.
- Integration prerequisite: a legally distributable, auditable host/client with a documented API for catalog identity and pre-load source selection. Without such a host, Gate 1 is **BLOCKED**, not passed.
