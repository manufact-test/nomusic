# Android A1 NAV40 — signed-original SLOT_B → timeline transition → Period UID lookup

19 November 2026. Static **read-only** inspection of the exact publisher-signed original **Yandex Music 2025.10.4 #120.1gpr** (six signed DEX). No app modifications, no NAV41 APK, no new owner-phone test. XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, base APK SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Research code in sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

## Last green verification

- [CI #44516354079 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44516354079), **27/27 fail-closed tests**, code commit `30bbb059b05f3dcd678c5fdb40c50ad04887c961`. The signed report remains `NATIVE_QUEUE_SLOT_ROLE_MAP_STATIC_ONLY`.
- The earlier exact PlaybackInfo-vs-Queue-front comparison: `e.break()` original PCs 1253–1276 compare `LCD7.LSl6$b` period UID against exact Queue `SLOT_A` front holder period UID via `Object.equals(v1,v2)`, branching to PC1303. [CI #44513983147 SUCCESS 23/23](https://github.com/manufact-test/nomusic/actions/runs/44513983147). Its outcome is not observed at runtime and **SLOT_A ≠ SLOT_B role**.
- Original PlaybackInfo `LCD7` period-ID field accessed by `e.break` at PC1262 matches the exact `d.M0` period-ID field at PCs 74/96/259, **not** the distinct `d.M0` field at PCs 138/257. Original engine and `d.M0` use the exact matching timeline field, not merely identical types. [CI #44513279643 SUCCESS 21/21](https://github.com/manufact-test/nomusic/actions/runs/44513279643).

## Newly verified exact signed-original facts

1. Original `e.break()V` reads the **same exact Queue `SLOT_B` field** at PCs **547** and **664**; an original direct write to that same field exists at PC **659**, between the reads in code order. The first read feeds renderer helpers at PCs 590/598 (previous structural-only proof); the second read can feed the period transition. The two reads do **not** guarantee the same holder object, nor prove PC659 actually ran.
2. The `Lxh6.Lyh6` holder-info field and the `Lyh6.LSl6$b` ID field read via those paths match the exact previously verified constructor-held fields. In original `e.break` the old and newer candidate period IDs are passed to `e.I(LTva;LSl6$b;LTva;LSl6$b;JZ)V` at PC **711**, together with timeline inputs. Eight bounded register spans were checked for overwrites: **8/8 clean** in signed DEX. This is method-local register provenance, not a synchronized runtime snapshot of what is audibly playing.
3. Inside the exact original `e.I` there are two separate typed PeriodID-UID-to-Timeline-period-record lookups: ID UID field `iget-object` PC **52** → original `LTva.goto(Object, LTva$b)` at PC **56**; and PC **99** → `LTva.goto` at PC **101**. Original `e.z(LTva;LSl6$b;)Z` similarly reads that same exact UID field at PC **13** and invokes the same Timeline lookup at PC **17**. All three calls have an exact typed PeriodID parameter and typed Timeline parameter, exact matching field reference, correct argument registers and no local intervening clobber.
4. The UID field in these three lookups is exactly the same original `LSl6$b.Object` field as the Player-vs-front comparison at `e.break` PC1264. The UID maps the period to a Timeline Period record; it does **not** uniquely determine the selected song edition, ad index, audible period or a fresh queue generation.
5. Previous signed-normal-CFG evidence still stands: old `LSl6$b.J` may be forwarded into **another** MediaPeriodId constructor, and `Lxh6` holder's `Lyh6` info may refresh while retaining the same Java PeriodID. Neither equal UID/J/holder reference nor invocation frequency is a safe generation counter.

## Non-negotiable fail-closed interpretation

- `CELIKOM_REPLACEMENT=NOT_CONNECTED`
- `IDENTITY_STATUS=STRUCTURAL_ONLY`
- `current_Player_selected_media_item_at_same_audio_read_proven=false`
- `NAV41_readonly_runtime_admission_proven=false`
- No runtime equality result, guaranteed SLOT_B object change, simultaneously captured original Player selection, edition, queued-vs-audible classification, or unique generation has been proved.
- No claimed suppression of exception paths or indirect/native/reflection mutation; no original Player, signed vendor code, decoder, renderer, audio path, NAV40 APK/ZIP or owner phone was modified.

## Next developer task

Keep examining original signed `e.I` and `e.z` *after* the verified Timeline UID lookups: establish whether original Timeline Period→Window→MediaItem can be linked by **exact original references** to the chosen current Player item and the particular actively used `SLOT_B` holder **at the same started-audio read**. Correlate with candidate original Track/edition identity without disclosing account/media values. Model same-track replay, previous stale period, prefetch/next period, holder/PeriodID refresh and timeline transitions as fail-closed counterexamples. Do **not** promote a static `SLOT_A` comparison, a Timeline UID match or a method-call count to selected-song identity. Only with positive signed-original proof and negative tests should a minimal read-only NAV41 be designed; no premature APK.

## Preserved signed runtime

- Last signed NAV40 code `34cb32c88a11743a64c9f4814fa71957223a1391`
- Protected signed backup `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`
- Protected signed period-info research backup `backup/android-a1-nav40-signed-slotb-period-info-readonly-ci-green-20261119` @ `5f057390503fa76f53e55cd2643897f815676349`
- Last owner-phone diagnosis `CELIKOM-A1-Diagnostics-1795077619261.txt`: exact late Flow Album SAME/MANY; negative categories NONE, but **not** selected edition or epoch.
- NAV40 signed APK and ZIP already in ChatGPT Library `/CELIKOM/Android/Native/`, no re-upload or re-build needed.
