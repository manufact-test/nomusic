# CELIKOM Android A1 — real owner NAV36: exact live Player tCa born outside observed Track scope
18 November 2026. Scope: `manufact-test/nomusic`, sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Diagnostic is private, never commit full TXT.

## Grounded owner-phone artifact
- Owner upload: `CELIKOM-A1-Diagnostics-1795009674955.txt`, 117,037 bytes / 1,634 physical text lines; SHA256 `7701f459618aa3306dff153b200330a2f6e5a58edff4fa24efdf26f680e4f33d`.
- Latest capture and export marker both `NAV_V36_TCA_CONSTRUCTOR_SCOPE_READONLY;ACTIVE`. Older NAV35 build marker earlier in the retained multi-session log is historical, not the active export.
- `LOG_TRIMMED=KEEP_LAST_32KB`; do not turn capped counters into absolute counts of distinct tracks or extrapolate missed trace events.

## Strict live source guard and NAV36 answer
- Current original live `SLOT_B` stream attach and renderer type1/state2 read match `MANY`, OTHER/UNAVAILABLE `NONE`.
- Direct original live `Lo96` period source present and resolved `MANY`; source null/reflective failures `NONE`.
- `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY`, OTHER/NO_LINK `NONE`: same original live source Java ref as the unique previously scoped original Player setter source. This guard is required for every following conclusion.
- `LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_MATCH=NONE`, `NO_LINK=MANY`, `CONFLICT=NONE`.
- NAV35 reason remains `LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_WRAPPER_ABSENT=MANY`; all seven other NAV35 NO_LINK reasons `NONE`.
- Under that exact guard, NAV36 six birth reasons:
  - `LIVE_PERIOD_SCOPED_TCA_BIRTH_NOT_IN_WINDOW=NONE`
  - `LIVE_PERIOD_SCOPED_TCA_BIRTH_NO_TRACK_SCOPE=MANY` **(unique positive)**
  - `LIVE_PERIOD_SCOPED_TCA_BIRTH_TRACK_NOT_IN_FLOW=NONE`
  - `LIVE_PERIOD_SCOPED_TCA_BIRTH_FLOW_NO_ALBUM=NONE`
  - `LIVE_PERIOD_SCOPED_TCA_BIRTH_FLOW_ALBUM_LINK_MISSING=NONE`
  - `LIVE_PERIOD_SCOPED_TCA_BIRTH_DUPLICATE_AMBIGUOUS=NONE`

**Meaning, verified against NAV36 Java at signed SHA `8b9d91b7b1ba2b0df84ada516bab938f077cfab9`:**
`StageBAudioEvidence.onNativeTrackWrapperCreated` is called after original `tCa(String)` constructor proceed, and its category 11 means `currentScope(activeTrackScopes)==null` at the constructor hook. Weak last-64 history found the **exact** `tCa` Java ref used in original scoped Player source setup, rather than a guessed tCa. `activeTrackScopes` is currently pushed only by `Gp0.new(Gp0,Track,Oe2)` interception, balanced in finally; therefore category 11 proves absence of this **observed synchronous Gp0 Track scope at birth**, not absence of a real Track/Album or a vendor metadata relation. Asynchronous/coroutine construction, an alternate creation path or a missed exact context are hypotheses, NOT proven causes. Do not read IDs, names, URLs, private values or media.
- Other Stage B `TRACK_ALBUM_CONSTRUCTOR_LINK=MANY`, `FLOW_TRACK_ALBUM_LINK=FEW`, `TRACK_WRAPPER_ALBUM_LINK=MANY`, `NATIVE_TRACK_SOURCE_REQUEST=FEW` and `TRACK_WRAPPER_LINK=MANY` demonstrate independent links, NOT a link to the exact Player-scoped tCa.
- `EXO_IO_FAILURE=NONE`, `EXO_READ_POSITIVE=MANY`; original playback behavior is not reported as faulty. `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`.

## Metrica caveat
`METRICA_EXCEPTION_SUMMARY;origin=MUSIC_APP;error=FEW`. In the retained NAV36 portion, MUSIC_APP exceptions include `EXC_AUTH` (two visible entries) and `EXC_OTHER` (one visible entry); old NAV35 retained history also contains MUSIC_APP entries. The log is trimmed and categorical. No evidence proves a causal connection to CELIKOM/NAV36, player/audio failure or a regression. `PREVIOUS_PROCESS_EXIT=USER_REQUESTED` appears in the retained export; no attributable crash established. Do not change push/auth because of this summary alone.

## Narrowest next technical step — NO NAV37 yet
1. **Static-only** issuer-signed original 2025.10.4 #120.1gpr DEX investigation: enumerate **direct producers and callers only on the already-proven `LcA9.extends(LcA9;LA14;LtCa;...)` original Player source path**, trace the exact `LtCa` parameter backward to its `tCa(String)` construction or guarded handoff, and look for a concrete `Track`/Flow/Album object-reference association or a coroutine boundary. Existing `lca9_exact_source_player_identity.py` and its 2025-signed checks are the starting point. Do not widen into unrelated candidate sources, EOS, comparator, or NAV25–NAV35 probes.
2. If and ONLY if signed static evidence identifies one narrow original read-only scope/continuation edge capable of associating the exact `tCa` object with original `Track` object by Java reference, propose minimal instrumentation (a NAV37 would then require backup, regression JVM and ARM13 CI, unchanged publisher/owner cert, verified personal Library delivery and real owner TXT). No new runtime build just to add more counter names.
3. Even a verified historical Track/Album association still would **not** prove current selected edition, duration, queue generation, entitlement or audio substitute. Maintain fail-closed `STRUCTURAL_ONLY` and `NOT_CONNECTED`.

## Release / rollback untouched
NAV36 signed exact source `8b9d91b7b1ba2b0df84ada516bab938f077cfab9`; protected backup `backup/android-a1-nav36-original-tca-birth-owner-signed-arm13-ci-green-20261118`. JVM CI #44311280846 SUCCESS, Android13 ARM13 CI #44311280892 SUCCESS. No code or APK changed during this phone diagnostic review. NAV36 Library package and hashes remain as recorded in `NEXT-CHAT.md` and NAV35→NAV36 release document.
