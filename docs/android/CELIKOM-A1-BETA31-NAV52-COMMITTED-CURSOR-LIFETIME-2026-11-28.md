# CELIKOM Android A1 — BETA31 NAV52 committed-cursor lifetime

Date: 2026-11-28  
Repository: `manufact-test/nomusic`  
Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## 1. Why this correction was made

NAV51 repaired the durable identity witness between the exact original Track/wrapper, Factory and live DataSource. The remaining lifecycle candidate was that the original source setter could start a new selection before the renderer closed the previous committed source. Calling `cancelForNext()` at setter time immediately reset the route and could close an already opened alternate cursor before the renderer finished reading it.

The phone-side TXT did not prove that this exact race caused the audible failure. The correction was a narrowly scoped, testable lifecycle fix rather than another broad diagnostic round.

## 2. Code change

- `NativeEarlySourceLifecycleBridge` now calls `nativeExoBytes.supersedeSelection()` when a new original source setter is observed.
- `NativeExoAlternateByteRoute.supersedeSelection()` retires the exact previous source and preserves only its already committed cursor for reads already in flight.
- The retired source cannot open a new cursor, obtain a new grant, or re-arm.
- The new source receives its own independent cursor and grant.
- Native close of the retired source closes only that source's cursor.
- Strict `cancelForNext()` remains available for an actual terminal cancellation and closes any retained draining cursors.

No second player, Yandex codec change, permission change, server/catalog change, Windows change, stable Android change or OTA change was made.

## 3. Focused regression

`NativeExoAlternateByteRouteTest` now exercises the overlap case:

- first exact source obtains an approved cursor and reads bytes;
- a new original source setter supersedes the first selection;
- the committed old cursor remains readable but cannot be reopened or re-armed;
- the next source opens an independent cursor and reads its own bytes;
- unrelated sources never receive alternate bytes;
- closing the old source retires only its cursor, and later reads fail closed.

The JVM workflow compiled and ran this test together with the existing lineage/proxy contracts. Observed pass markers include `RAMIL_AU_ORIGINAL_TRACK_ONLY_BETA_LINEAGE_PASS` and `NATIVE_EXO_SINGLE_PLAYER_ENCODED_BYTES_ROUTE_PASS`.

## 4. Build and verification

- Source commit: `ef661ce23da8c50367b9aaaf0d27c65aed160ba1`.
- Source/export workflow run: `46121780348`, attempt 1 — SUCCESS.
- JVM gate: SUCCESS.
- Fresh Android 13 ARM64 + ARMv7 native gate: SUCCESS.
- Native verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.

## 5. Signed APK

- Filename: `CELIKOM-A1-RAMIL-AU-BETA31-HONOR50-20261128.apk`.
- Size: `71602156` bytes.
- SHA-256: `fed4b9c150e45eadc6cc424b2a904f5ac5951160ef1e1e8c9227c039f37562fe`.
- Unpublished owner draft release ID: `461389699`.

The exact original signing certificate and package ID were independently verified during the delivery workflow.

## 6. Floki delivery

- Trusted spool workflow: `46122831604`, attempt 3.
- Job: `140919835283`, runner `celikom-floki-ci02`, SUCCESS.
- Root receipt: `a1-46121780348-1.json`, matching the exact filename, size and SHA-256; `https_verified=true`.
- Independent HTTPS readback: HTTP 200, expected Android APK content type, exact size and SHA-256.
- The unpublished owner draft was updated and read back with exactly one matching capability URL.

The direct owner URL was delivered privately and is deliberately omitted from this document.

## 7. Owner acceptance still required

Install BETA31 over BETA30 on the existing Honor 50. Do not uninstall CELIKOM or clear app data/cache. Confirm CELIKOM is `ВКЛ`, test Ramil / 10AGE «Ау», album `38902809`, track `144530503`, segment `00:43–00:54`, then test the second song with prior leading gaps. Export a fresh BETA31 TXT.

**This build is delivered, but audible replacement is not proven until the owner hears the alternate sound inside the original Yandex Music application.**
