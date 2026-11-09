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
