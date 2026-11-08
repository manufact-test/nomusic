# Two bounded native-source trials, 2026-11-08

Scope: experiment/desktop-native-two-trials-20261108. Owner requested at most a couple of further experiments, followed by a decision against accepted 0.4.73. Do not enter repeated native rewrites. Android, server, production and accepted extension sources remain untouched.

## Owner evidence from experiment 001

The owner rejected daily use: no apparent speed advantage and an audible switching artifact. Diagnostic at approximately 14:17 UTC shows four successful native activations (IDs 42498653, 85025192, 78608850, 107389859), taking 2244/1540/1514/1332 ms from preparation start. These are not direct comparable end-to-end measurements against 0.4.73. No recorded access/API errors; recorded metadata API calls succeeded. Full audio download latency is not separately recorded, so fast metadata responses do not prove the media transport was fast.

Two same-track source replacement traces include emptied/loadstart, metadata/seek and playing. Extrapolating the previous continuously playing clock suggests about 0.49 and 0.40 seconds of replay. These estimates depend on uninterrupted progression between observations; source duration changes identify same-track original-to-replacement boundaries. A cross-track boundary must not be counted as replay. No PCM/audio recording is present: the exact cause of the owner's audible artifact is unproven.

The actual pinned Yandex ReloadCore.reload captures progress before asynchronous getMediaSource. A controlled run of that real class captured position 10, advanced the still-playing original to 10.5 during its source read, then applied position 10. This independently reproduces stale-position replay.

## Trial A: current position on late handoff

For an owned source only, optional livePosition updates corePlay position immediately before delegation, while the same original audio is still playing and not seeking. It does not affect independent native requests, paused setSrc or normal original restoration. Generation/binding/intent guards remain active; a user seek rejects the operation rather than being overwritten. NativeSession activation opts into this mode. No product code is changed.

Node regression verifies 500 ms replay is removed and user seek still wins. Browser comparison delays actual Yandex resource acquisition by 180 ms and compares stock reload with corrected reload. The second operation begins from settled playback: a queued seek event from the preceding test reload must not masquerade as a new user action.

This trial fixes a concrete defect in experiment 001. It does not itself remove a source reload, avoid whole-file download or establish an audible improvement over 0.4.73.

## Trial B: prepared next source

The real public queue class (module 28692, export Di) computes state.nextEntity from nextIndex/order/entityList. Test uses a different array order to prove ID selection is not a DOM/array guess. A known next MP3 is prepared before requesting that next source; real resource and source classes feed the same native audio through one source assignment, without an added late replacement reload.

Compare this prepared path with three ordinary 0.4.73 preparation samples on the same controlled media. Limits: not signed-in end-to-end listening, no claim about acoustic quality, and the laboratory next registration is NOT integrated with fresh entitlement admission, cancellation and eviction. It must not be shipped as a product path. Unknown next tracks and cold first startup cannot inherit this prepared-path benefit.

## Decision rule

Do not promote the native backend based on successful playback alone or on comparing a prepared file with an unprepared old path. Require a meaningful advantage over the accepted extension under comparable preparation, plus acceptable source transitions. A correctable defect in our prototype is not, by itself, a reason to replace accepted playback. If these bounded comparisons do not demonstrate an advantage, retain 0.4.73 and preserve research for reference; no additional owner installation is warranted just to test cleanup of prototype regressions.

## Results

Controlled browser run 42501132598 recorded the following before its position-test setup gate failed (stock comparison had begun before its original media clock settled):

| Browser | Prepared native next | 0.4.73 preparation samples | Corrected replay |
| --- | --- | --- | --- |
| Chrome | 4 ms | 5 / 5 / 3 ms | 0 ms |
| Brave | 7 ms | 5 / 4 / 7 ms | 0 ms |

The gate failure is not hidden or relabeled as a successful run. Final comparison sets BOTH original and corrected operations to settled playback before timing; final CI identifiers are appended below. Local suites: 48 experimental tests passed.

These tiny controlled preparation differences do not demonstrate a meaningful user-facing startup advantage, and cannot establish signed-in end-to-end latency. Prepared-next registration avoids an extra late reload in the laboratory, but requires additional real-account admission, cancellation, expiry and lifecycle integration before it could become a product path. Cold whole-file joining remains a known disadvantage of experiment 001.

**Decision: retain accepted 0.4.73. Stop this native-backend experiment after the two bounded trials.** Do not issue another owner build merely to remove a prototype defect while no product advantage has been shown. Keep the optional position correction and real queue-ID research isolated for reference. Prepared-next work, if later requested, should first be evaluated within the existing accepted architecture, without replacing its playback engine.

No new owner-facing build has been issued for these trials. Accepted source and installed artifacts have not been changed.

## Final verification

Source commit: `97f5a1cc52940e73230f87b7d8a2e046ec1d1cdf`. [CI 42501295185](https://github.com/manufact-test/nomusic/actions/runs/42501295185), job 128794409230: SUCCESS. Both comparisons begin from settled playback; no performance assertion was weakened to hide the earlier setup failure.

| Final browser run | Stock replay with 180 ms source delay | Corrected replay | Prepared native next | Prepared 0.4.73 samples |
| --- | --- | --- | --- | --- |
| Chrome 156.0.8078.79 | 180 ms | 0 ms | 4 ms | 4 / 5 / 4 ms |
| Brave 157.1.99.55 | 180 ms | 0 ms | 5 ms | 6 / 8 / 4 ms |

All 48 experimental Node cases and 360 accepted desktop regressions passed. Repository lint passed. Source comparison against accepted commit shows no changes under extension, android or server. These controlled results support fixing the prototype's stale-clock defect, but show no meaningful prepared-path speed advantage; the decision remains to retain 0.4.73 and stop further native-backend work under this experiment.
