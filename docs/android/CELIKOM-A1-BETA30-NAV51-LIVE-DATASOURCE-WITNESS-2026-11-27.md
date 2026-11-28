# CELIKOM Android A1 — BETA30 NAV51 live DataSource identity witness

Date: 2026-11-27  
Repository: `manufact-test/nomusic`  
Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## 1. BETA29 phone result and NAV50 evidence

The owner supplied `CELIKOM-A1-Diagnostics-1795806916651.txt` and reported that audible replacement still did not work.

NAV50 counters:

| Counter | Result |
|---|---:|
| `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS` | NONE |
| `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_EOS_UNKNOWN` | NONE |
| `LIVE_RENDERER_ALT_SOURCE_DIFFERENT_CURRENT_PERIOD` | NONE |
| `LIVE_RENDERER_ALT_SOURCE_ARMED_NO_READ_CURRENT_PERIOD` | NONE |
| `LIVE_RENDERER_ALT_SOURCE_NO_ROUTE_CURRENT_PERIOD` | FEW |
| `LIVE_RENDERER_ALT_SOURCE_DATASOURCE_UNRESOLVED_CURRENT_PERIOD` | FEW |
| `LIVE_RENDERER_ALT_SOURCE_SLOT_OR_PERIOD_CHANGED` | NONE |

The diagnostic also showed an approved alternate route and positive alternate DataSource reads. However, it did not prove that the DataSource returning those bytes was the one used by the current renderer period. The counters were process-wide and could not be attributed to each song/selection generation.

## 2. Code inconsistency found

In `StageBAudioEvidence.java`, the first-open/touched-source path releases the temporary strong descriptor pin. The live NAV50 resolver nevertheless required both the Descriptor and Factory weak references to still resolve, even after the exact DataSource had already been attached to the same wrapper.

That creates an unnecessary lifetime dependency: collection of a vendor Descriptor or Factory object can make the live DataSource mapping unresolved even while the DataSource itself remains live.

This was a concrete code path capable of producing NAV50 `DATASOURCE_UNRESOLVED`. The BETA29 TXT did not prove that garbage collection was the actual cause on the phone; NAV51 adds counters to distinguish it from other identity failures.

## 3. NAV51 change

The current branch adds a value-free boolean witness:

`factorySourceIdentityBound`

It is set only when the exact Descriptor → Factory → DataSource identity chain is verified, including the accepted exact first-open path. It is reset whenever the Track wrapper, Descriptor or Factory lineage is rebound.

The live resolver now:
- requires the exact creator Track and wrapper;
- requires the durable factory-to-source witness;
- requires the current weak DataSource instance;
- rechecks the reverse DataSource-to-link identity;
- revalidates the Beta creator token or exact Album identity;
- does not require the vendor Descriptor/Factory weak references to remain alive after OPEN.

No strong reference to vendor Descriptor/Factory is retained. The change does not alter audio routing, player, Yandex codecs, server, grants, authorization, Windows, stable Android or OTA.

### New diagnostic counters

1. `LIVE_PERIOD_SOURCE_LOOKUP_CALL`
2. `LIVE_PERIOD_SOURCE_CREATOR_MATCH`
3. `LIVE_PERIOD_SOURCE_CREATOR_MISSING`
4. `LIVE_PERIOD_SOURCE_WRAPPER_LINK_MISSING`
5. `LIVE_PERIOD_SOURCE_LINK_MISMATCH`
6. `LIVE_PERIOD_SOURCE_FACTORY_LINK_UNBOUND`
7. `LIVE_PERIOD_SOURCE_INSTANCE_NOT_LINKED`
8. `LIVE_PERIOD_SOURCE_INSTANCE_WEAK_LOST`
9. `LIVE_PERIOD_SOURCE_REVERSE_LINK_MISMATCH`
10. `LIVE_PERIOD_SOURCE_BETA_RECHECK_FAILED`
11. `LIVE_PERIOD_SOURCE_ALBUM_MISMATCH`
12. `LIVE_PERIOD_SOURCE_LOOKUP_RESOLVED`

## 4. Regression test

`NativeRamilTrackOnlyLineageTest` now deterministically clears the weak Descriptor and Factory references after the source has been opened/read and verifies that the exact live DataSource still resolves. It also verifies:
- no resolution before a Factory product exists;
- no resolution before a DataSource exists;
- old identity is invalidated on Descriptor rebind;
- a replacement Factory/DataSource chain resolves;
- an unrelated wrapper is never guessed.

The test passed in BETA30's owner JVM gate. Its output included `RAMIL_AU_ORIGINAL_TRACK_ONLY_BETA_LINEAGE_PASS`.

## 5. BETA30 build and artifact

- APK source commit (not current documentation branch head): `aef40439586304fd57dabcbf20dfcce3af52a181`.
- Owner/export workflow: `46070081916`, attempt `1` — SUCCESS.
- Owner JVM contract and NAV51 regression — SUCCESS.
- Fresh Android 13 ARM64 + ARMv7 native gate — SUCCESS.
- Native verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- Private unpublished owner draft release ID: `461085315`.
- Release tag: `celikom-a1-owner-46070081916-1`.
- APK: `CELIKOM-A1-RAMIL-AU-BETA30-HONOR50-20261127.apk`.
- Size: `71,602,156` bytes.
- SHA-256: `e33c3e31721d76ee82df7554f0eddb311202566328eafcb50f3f0958b7b53dfe`.

The artifact is a diagnostic build. No audible replacement is claimed.

## 6. Trusted delivery status — COMPLETE (2026-11-28)

CI02 was recovered by restarting its existing service after confirming no active worker (maintenance run `46084579328`, SUCCESS). The original trusted Floki run `46070217462`, attempt 5, job `140793123974` on CI02 completed SUCCESS. The exact BETA30 APK passed provenance, signer/package, size/hash, root receipt/live HTTPS and unpublished draft URL readback checks. Draft `461085315` remains unpublished. Direct owner URL was sent privately; do not record it here. No rebuild or source change. No further delivery work is needed for BETA30.

## 7. Next owner test

BETA30 has already been delivered. Install over BETA29 if not already done. Do not uninstall CELIKOM or clear app data/cache.

1. Check CELIKOM status is `ВКЛ`.
2. Test Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, segment `00:43–00:54`.
3. Test the second song that previously had leading gaps.
4. Export a fresh TXT after both tests.
5. Report separately whether the alternate sound was actually heard.

The NAV51 same-DataSource result would establish source-path identity, not audible output. The phone listening test remains mandatory.

## 8. Owner-directed next development step (2026-11-28)

Fresh BETA30 TXT and listening result are pending in this checkpoint. The next chat should use those existing results to implement a justified functional fix, not automatically add telemetry. Follow the decision branches in NEXT-CHAT.md. Investigate only the concrete unresolved boundary; use targeted tests and required release gates, then deliver a corrected APK. If the same-period witness resolves, investigate downstream audio; if route/period mismatch is shown, investigate lifecycle/source selection; if resolution still fails, use existing NAV51 reason counters. Avoid redundant diagnostics and do not claim audible success without the phone test.
