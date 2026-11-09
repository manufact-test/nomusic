# CELIKOM Android — verified native clone loader blocker (09.11.2026)

## Confirmed in genuine Android runtime, not synthetic smoke

- **Original authentic signed Yandex + parallel separate clone install together:** Android 11 API30 x86 Google APIs emulator with ARMv7 translation, exactly **5 + 5 split APKs** installed in PackageManager ([CI 42681460403](https://github.com/manufact-test/nomusic/actions/runs/42681460403)). No original package removed.
- **Important correction:** earlier "original process not alive" was a false result from an incorrect adb `shell sh -c` PID probe. Direct shell `pidof` fixed this. **Unmodified publisher-signed original now proven PROCESS_ALIVE_AFTER_LAUNCH**, [CI 42686813136](https://github.com/manufact-test/nomusic/actions/runs/42686813136).
- **Clone:** same emulator, 5 split APKs installed but **PROCESS_NOT_ALIVE** after direct launcher startup; AndroidRuntime reports **`ClassNotFoundException` or `NoClassDefFoundError` for `ru.yandex.music.YMApplication`**, [CI 42686813136](https://github.com/manufact-test/nomusic/actions/runs/42686813136). The class name is public; no raw logs, private data or auth were exported.
- **Artifact sanity gate:** verified signed clone contains `YMApplication` in `classes.dex`, same class-definition count as original, six base DEX filenames and byte lengths unchanged, all DEX compression methods STORED (0), source and cloned compiled loader flags equal, DEX standard header file-size/SHA-1/Adler32 integrity checks PASS. [CI 42689510730](https://github.com/manufact-test/nomusic/actions/runs/42689510730).
- **Installed runtime flags:** both packages show `HAS_CODE=true`, codePath and base.apk present. Clone's exception DexPathList also refers to clone's base.apk ([CI 42688277066](https://github.com/manufact-test/nomusic/actions/runs/42688277066)).
- Original launcher `ru.yandex.music.main.MainScreenActivity` and application `ru.yandex.music.YMApplication` are explicit and class names preserved. No relative manifest class names.
- Original and clone permission authority collision removed only in **temporary test clone**: the two publisher-owned `signature` permission *declarations* were omitted (requests retained; no cross-signature privilege granted), and original retains ownership. Not a production authentication plan.
- **Still UNKNOWN:** Why Android's classloader cannot resolve the class from seemingly valid cloned DEX. DexPathList presence and header integrity are insufficient to prove ART acceptance. Possibilities include dexopt/ART loading failure or package-specific component setup. Do NOT assert an anti-tamper/signature check or bypass one without evidence.

## Next safe technical gate

On the existing disposable ARMv7-translated emulator, compare package dexopt verification status and sanitized ART/dex loader error **categories** for original and clone, without changing protection, acquiring auth or publishing APK. If normal system verification still yields no explanation, pause clone changes and reconsider a legally authorized original-client integration approach rather than endless re-signing.

Track ID evidence stands separately: signed #170gpr FileInfoApi and OldFileInfoApi parameter 0 is `trackId`, param 1 `codecs`, param 3 `quality` ([CI 42677831933](https://github.com/manufact-test/nomusic/actions/runs/42677831933)). Native runtime ID→edition→decoder-before-prepare still **NOT PROVEN**.

## No-go / unchanged

No Play Protect bypass or override, no publisher credential/token collection, no modified vendor APK release, no changes to HONOR 50 installed original, accepted CELIKOM Test.50, Windows, extension, database, backend or production. No real native audio swap or RASKOL/«Дым» validation yet.
