# CELIKOM Android — DEX sorted string_ids investigative gate, 09.11.2026

Real original works but clone fails loading YMApplication despite its class
being present in a structurally checksum-valid DEX.

Important Android DEX invariant: string_id entries MUST remain sorted.
The current bounded clone patch edits one fixed-length string literal
`com.yandex.preinstallsatellite.appmetrica.provider` to a test clone
authority `pro.celikom.nativeclonelab.appmetrica.provider.v01`,
recomputes SHA-1 / Adler32, but does NOT reorder the string_id table.
This can make the whole file fail ART verification while all prior
checksum and class-definition checks still PASS. Technical precedent:
REAndroid/APKEditor issue #46, and independent DEX string-ID ordering
pitfall documentation.

New signed-original, CI-only static A/B analysis checks the original and
modified value relative to immediate preceding/following DEX string_id
values; ONLY boolean metadata is printed. If the modified value violates
sorting, we have a concrete structural root cause candidate, not proof
of Android runtime until a disposable emulator control confirms it.

No APK distribution, key/token collection, LSPatch, root, protection
bypass, or changes to user's HONOR/Test.50.


## Confirmed signed #170gpr structural failure — 09.11.2026

[CI 42690904213](https://github.com/manufact-test/nomusic/actions/runs/42690904213) **SUCCESS read-only gate**: original `classes.dex` AppMetrica authority is in a correctly sorted `string_id` slot, but the current lab replacement `pro.celikom.nativeclonelab.appmetrica.provider.v01` lies AFTER the immediate next string, violating the DEX sorting invariant. This can explain ART rejecting the DEX and reporting `YMApplication` missing although checksum and class definitions look valid. The runtime cause is NOT yet experimentally proven.

[CI 42691145641](https://github.com/manufact-test/nomusic/actions/runs/42691145641) **SUCCESS read-only candidate scan**: several same-length alternate public authority names preserve the original ordered slot (e.g. `com.yandex.preinstallsatellite.appmetrica.provideq`). They are laboratory candidates only; no APK using them has been built, installed or run.

**DO NOT mark clone as fixed.** An attempt to update the clone's in-place DEX literal replacement was blocked before a GitHub commit. Current script still uses the old known-invalid candidate; no safe runtime PASS. Future modification must explicitly enforce original and modified `string_id` slot ordering, preserve permission boundaries and make no claims about Play Protect or login. The remaining native runtime decoder→source proof is independent of this.

## Safe CI guard after root-cause discovery (09.11.2026)
Legacy `patch_one_dex` now **rejects invalid replacement order before writing
the DEX** (`DEX_STRING_ID_ORDER_FAIL_CLOSED`), rather than emitting a
checksummed but unsorted DEX. The still-configured original legacy
AppMetrica replacement is KNOWN invalid and cannot be used for a runtime APK.
The existing structural CI workflow has been switched to the safe
`CELIKOM_MANIFEST_ONLY_ORIGINAL_DEX=1` control and PASS
[42697151607](https://github.com/manufact-test/nomusic/actions/runs/42697151607).
The safe runtime clone STILL has no MAIN/UI, see
[ANDROID-NATIVE-STRICT-MAIN-UI-GATE-2026-11-09.md](ANDROID-NATIVE-STRICT-MAIN-UI-GATE-2026-11-09.md).
