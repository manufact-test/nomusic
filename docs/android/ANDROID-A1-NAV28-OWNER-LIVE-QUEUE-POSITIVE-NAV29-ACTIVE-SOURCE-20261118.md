# CELIKOM Android A1 — NAV28 owner real-phone live queue positive / NAV29 active period source investigation

18 November 2026, only `manufact-test/nomusic` / `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

## Private NAV28 phone facts (not release smoke and not static inference)
The actual owner TXT `CELIKOM-A1-Diagnostics-1794993804107.txt` was parsed in this conversation; raw contents NOT committed. The file preserves stale NAV26 and NAV27 log sections, but its explicit export snapshot identifies `NAV_V28_LIVE_QUEUE_SLOT_B_RENDERER_READONLY;ACTIVE`.

At export `LIVE_QUEUE_SLOT_B=REGISTERED`; `LIVE_QUEUE_SLOT_B_ATTACH_MATCH=FEW`; ATTACH_OTHER=NONE, ATTACH_UNAVAILABLE=NONE. Independently `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW` and no DIFFERENT/UNAVAILABLE. At original renderer type=1 state=2 sample read, `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`, OTHER=NONE, UNAVAILABLE=NONE; sampled original b.g return -4 MANY. Old `READ_RETURN_LINK_LOST=NONE`; audio renderer holder/read MANY. Therefore an **actual active renderer/stream object** is linked to the **currently live exact e.h.SLOT_B queue holder** by identical Java references at sampled reads. No Track/Album edition/duration/generation, acoustic PCM, entitlement or replaced media identity is proven. `IDENTITY_STATUS=STRUCTURAL_ONLY`; `CELIKOM_REPLACEMENT=NOT_CONNECTED`.

`RENDERER_COMPARATOR_FALSE=MANY` and `COMPARATOR_AT_CALL_ENGINE_MATCH/ATTACHED_STREAM=MANY` in this session, comparator strict-to-read both NONE; do not speculate on FALSE or use comparator as mandatory selected-item gate. Prior NAV27 phone had comparator events NONE but was a different session. `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/FEW` not a reported crash; original playback not reported broken. Old `BUFFER_EOS_ACCESS=NO_HOOK` remains. Existing Stage B `TRACK_WRAPPER_LINK=MANY`, `TRACK_WRAPPER_ALBUM_LINK=MANY`, `FLOW_TRACK_SAME_OBJECT=FEW` but source request to stream continuous link NONE.

## Narrow NAV29 native TrackWrapper original source → active original period
Previously signed original static:
`LcA9.extends(...LtCa...)` passes exact `LiLb` source to Player setter (CI `lca9_exact_source_player_identity.py`);
`ExoPlayer.d.e(LSl6;J)` accepts original same media source, creates singleton playlist;
`Lp96.transient` reads original `LuIb` source field to construct `Lo96`, storing exact original source on the Lo96 period (CI `lp96_media_period_entry_exact.py`);
`Lxh6` creates/stores `Lup1` wrapper field, `Lup1` holds underlying `Lwh6` MediaPeriod, and its holder stream array attaches to renderer (CI `holder_stream_origin_exact.py`).

NAV29 optional read-only observer connects these exact previously separate facts: retain only weak Java refs from source setter executed under specific TrackWrapper-bearing call; at NAV28-proven live slot/read, follow exact signer-verified holder→wrapper→period→source private fields and test source Java `==`, nothing more. Different source, missing source, conflicting wrapper, changed slot, detach, reflection failure never promote. No original media/audio/payload changes or track text/IDs/URLs/tokens leaked.

NAV29 model/fixtures `b6b8442f...`; owner hook/private exact 2025 signed-Dex generator `bef2e523...`; JVM `#44276987119 SUCCESS`. Initial private CI `#44276987005` pending; must succeed before any release. Signed original module private field code is ephemeral and excluded from GitHub. No APK installation on owner phone in this investigation yet.

**Protection:** `backup/android-a1-nav28-owner-phone-live-slot-read-match-pre-nav29-20261118` @ `6603fefee19b1d7be319901998d8eae441e6786a`, accepted owner NAV28 signed source backup `backup/android-a1-nav28-live-queue-slot-owner-signed-arm13-ci-green-20261118` @ `4463297d81e5476fb1f3b2724391127b076b4828`. Preserve previous owner Library builds.

**Next required:** get successful signed exact publisher-private target proof and Android13 ARM owner smoke; verify SHA, owner signer v2/v3 and embedded original Yandex, upload personal Library, list+readback. Only then accept NAV29 phone evidence. A positive source link would not prove selected exact Album/edition/duration/generation, authorization or sound replacement; Stage B still NOT_CONNECTED.
