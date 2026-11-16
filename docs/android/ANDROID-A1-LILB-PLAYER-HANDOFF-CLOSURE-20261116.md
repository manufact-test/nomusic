# CELIKOM Android A1 — LiLb exact MediaItem-to-Player handoff closure

**Date:** 16 November 2026  
**Repository:** `manufact-test/nomusic`  
**Working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
**CI-green code checkpoint:** `46defb7d0d7384f40722ebb37c32899599838778`  
**Audit implementation commit:** `aa000e758d4710c6b4f4eccb56f4b80b0d7c3e1b`  
**CI #216:** [SUCCESS, 129/129 tests](https://github.com/manufact-test/nomusic/actions/runs/43877551279)  
**Exact green backup:** `backup/android-a1-li-lb-handoff-ci-green-20261116` @ `46defb7d0d7384f40722ebb37c32899599838778`.

## Scope

One bounded read-only scan over all six DEX files in the exact pinned issuer-signed Yandex Music 2025 split set. The scan matched only these two exact method references:

- Constructor: `LiLb.<init>(LdA9;LgA9;LJI7;LOf6;LFq1;LHy9$a;LPAa;)V`
- MediaItem getter: `LiLb.for()LOf6;`

For the immediate callers only, identity provenance was captured for the exact known Player mutators:

- `LsO7.C/V/Z`
- `LBs4.C/V/Z`
- `LfH7.C/V/Z`

No generic List/Object expansion, competitor sweep, new Media3 ancestry scan, runtime hook, APK operation, login, media access, private field-value read, URL/DataSpec/token read, or audio-byte read was performed.

## Exact result

| Evidence | Result |
|---|---:|
| Direct `invoke-*` callsites to exact `LiLb.<init>` | 2 |
| Direct `invoke-*` callsites to exact `LiLb.for()LOf6;` | 0 |
| Distinct immediate caller methods | 2 |
| Exact Player mutator callsites inside those immediate callers | 0 |
| Same-object edges from LiLb to a Player mutator | 0 |
| Caller traces complete | Yes |
| Complete for the bounded direct-caller absence claim | Yes |

### The two constructor callers

1. `LcA9.extends(LcA9;LA14;LtCa;Ljava/lang/Long;JJZLn26;Lnk0;Ljava/lang/String;)V`
   - Direct `invoke-direct` to the exact LiLb constructor at instruction ordinal 97.
   - The holder instance is the `new-instance LiLb` created at ordinal 80.
   - Constructor argument position 4 is the exact `LOf6.new(Landroid/net/Uri;)LOf6;` result produced at ordinal 25.
   - This is the previously established TrackWrapper → URI → MediaItem → LiLb source-side chain.

2. `Lwq2.x0(Lqe5;LgA9;LFq1;LHy9$a;LJI7;)LiLb;`
   - Direct `invoke-direct` to the exact LiLb constructor at instruction ordinal 118.
   - The holder instance is the `new-instance LiLb` created at ordinal 114.
   - Constructor argument position 4 is the exact `LOf6.new(Landroid/net/Uri;)LOf6;` result produced at ordinal 75.
   - The URI's upstream source is not inferred here.

Neither immediate caller contains a direct call to `LsO7`, `LBs4`, or `LfH7` MediaItem mutators. The bounded caller trace found no same-object Player handoff.

### Constructor/getter identity

The holder's internal object handling is proven:

- `LiLb.<init>` stores its exact `LOf6` constructor parameter into an instance field on `this`.
- `LiLb.for()LOf6;` reads an `LOf6` field from `this` and returns that same field-read object.
- This proves construction, storage, and getter identity inside the holder. It does **not** prove that the getter is called or that the object reaches Player.

The exact getter has zero direct `invoke-*` callsites across the six signed DEX files. The existing bounded Media3 source/timeline getter candidate list also remains empty.

## Decision

**Close the LiLb route. Do not continue tracing this holder.**

The requested direct-call investigation is complete: there are two constructor callers, no direct getter callers, no Player mutator calls in either immediate caller, and no same-object edge into Player. This is sufficient to close this bounded route without broadening the search.

The negative result is deliberately scoped to direct DEX invoke references and the immediate constructor-caller methods. It is not a claim that every possible reflective, virtual, or otherwise indirect runtime route has been disproven. No such route should be explored without a new exact evidence point.

## Product gates remain unchanged

- Stage A / NAV17: PASS by owner confirmation.
- Stage B: NOT CONNECTED / NO-GO.
- `active_selected_item_proven=false`
- `same_native_item_to_decoder_proven=false`
- `same_track_album_edition_generation_owner_proven=false`
- `codec_output_object_to_audio_sink_proven=false`

## Safety and artifact status

CI #216 verified the exact pinned archive SHA and issuer signature across the 16 signed split APKs containing six DEX files. The audit ran read-only in memory. The workflow's final guard passed:

- Original binary not modified or exported.
- No user login or media access.
- No decoder source changed.
- No APK built, patched, installed, or released.
- Runtime hooks unchanged; last runtime-hook change remains `a655712d210189f3bc611847235de3ed4d985c1a`.

## Next-chat instruction

Do not reopen `LiLb`, `LXk6.if(...)`, the broad List/Object route, competitor review, full Media3 ancestry, or ByteBuffer sink census. No further static route is authorized by this result. Wait for a new exact identity-bearing path or a concrete owner-provided runtime measurement before starting another bounded investigation.

