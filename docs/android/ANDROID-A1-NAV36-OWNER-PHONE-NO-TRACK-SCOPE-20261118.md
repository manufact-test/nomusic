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

## Completed narrow static follow-up — no same-object edge; NO NAV37

The bounded signed-original investigation requested above is complete. Full result: [tCa birth/callsite static audit](ANDROID-A1-TCA-BIRTH-STATIC-CALLSITE-20261118.md).

- On the original signed 2025.10.4 #120.1gpr, one exact `tCa(String)` creator was found. Its String comes from a Track-typed field read on a parameter object; the parameter type matches that Track field's owner/writer.
- The creator is a non-private instance method, not a constructor, `Gp0.new`, `Fp0.invokeSuspend` or Kotlin `invoke`; its owner is neither Continuation nor Kotlin Function.
- No direct DEX invoke caller to the exact creator or to its Track-holder parameter method was found. One same-signature ancestor reference is static and has no receiver; no same-object virtual dispatch is proven. No exact method-handle / invoke-custom reference was found.
- The existing exact Player setter path has two callers passing the same `tCa` field reference, but neither constructs that same `tCa`. The Track field writer's two callers do not establish the exact owner/Track reference at birth.
- CI [#44335142995 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44335142995), read-only, all six signed DEX files scanned; original input deleted from ephemeral runner. No runtime hooks, APK, original Yandex binary, Player, decoder or audio changed.

**Interpretation:** NAV36 still proves only that the exact Player-scoped original `tCa` was born outside the observed synchronous `Gp0.new(...Track...)` scope. This static search did not prove an asynchronous cause or the same Track Java object. Do not widen into unrelated vendor methods, reflective guesses, media values, EOS/comparator work or new runtime hooks. Keep NAV36 unchanged, `IDENTITY_STATUS=STRUCTURAL_ONLY`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`. No NAV37 is justified by the current evidence.

## Release / rollback untouched
NAV36 signed exact source `8b9d91b7b1ba2b0df84ada516bab938f077cfab9`; protected backup `backup/android-a1-nav36-original-tca-birth-owner-signed-arm13-ci-green-20261118`. JVM CI #44311280846 SUCCESS, Android13 ARM13 CI #44311280892 SUCCESS. No code or APK changed during this phone diagnostic review. NAV36 Library package and hashes remain as recorded in `NEXT-CHAT.md` and NAV35→NAV36 release document.
