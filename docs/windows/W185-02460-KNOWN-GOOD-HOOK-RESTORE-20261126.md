# CELIKOM Windows W185 — restore accepted W174 source hook and deliver 0.24.60 (26.11.2026)

## Finding

The last personally accepted Windows version was 0.24.54 (W174), and it already ran with official Yandex Music 5.128.0. Its renderer discovered the file-info endpoint dynamically by scanning webpack modules containing `"get-file-info"` or `"resources/v2/file-info"`, then attached the adapter to an exported class exposing `getFileInfo`.

W182 replaced this proven discovery path with a live-player-prototype assumption. W183 replaced it again with module 7695 export `SonataProvider`. The W183 static ASAR report showed module 7695 contained a SonataProvider export and several method names, but did not prove that the real playback call chain invoked `SonataProvider.prototype.getFileInfo`.

The W183 test was invalid as a runtime proof: it explicitly instantiated `new SonataProvider()` as a fake player's `resourceProvider`, then made fake `reloadEntity` call that method. It verified the invented test path, not Yandex's live path.

Owner W54 for 0.24.58 showed a grant delivered for track 144530503 and a successful native `reloadEntity`, but no `NATIVE_FILEINFO_REQUEST`. That is consistent with the source adapter being attached to a method the live player did not call.

## W185 change

Commit `adc09cf73e8deba417c77f7eae00727e894572d7` restores the W174 endpoint discovery logic in `windows-companion/w23/renderer-entry.mjs`. The 7123.VE state observer remains separate and is used only for current-player state and in-place reload.

The W22 adapter keeps the broadened argument extraction for both `trackId` and `id`, including the two-argument endpoint call `getFileInfo(context, {trackId})`.

The synthetic SonataProvider playback path was removed from the W183 renderer fixture. W185 now tests the accepted endpoint discovery route, verifies `NATIVE_FILEINFO_REQUEST` and `SOURCE_MAPPED`, and asserts the unverified SonataProvider is not patched.

## Candidate identity

- Source/release commit: `863abfd3a7eb7838128aecf54fb1c873bcc30813`
- W185 source fix: `adc09cf73e8deba417c77f7eae00727e894572d7`
- Version: **0.24.60**
- P-256 sequence: **7**
- EXE SHA-256: `986294eb51337d1246874c1ffb8e9fac70d368b1ea5e13cb68275d81f2c257e8`
- Versioned owner download: https://celikom.com/downloads/windows/CELIKOM-Windows-0.24.60.exe
- Owner latest: https://celikom.com/downloads/windows/CELIKOM-Windows-latest.exe

## Evidence

- Isolated Floki cross-build [45847863878](https://github.com/manufact-test/nomusic/actions/runs/45847863878): **SUCCESS**. 99 renderer/native tests passed, zero failed; W185 endpoint-hook test passed; Windows Companion and Update Supervisor cross-compile passed.
- Signed release [45847863957](https://github.com/manufact-test/nomusic/actions/runs/45847863957): **SUCCESS**. P-256 manifest and owner package passed.
- Manifest `package_sha256=986294eb51337d1246874c1ffb8e9fac70d368b1ea5e13cb68275d81f2c257e8`, sequence 7.
- Transport artifact ID `15132094218`, size 84,679,085 bytes, digest `sha256:e1fd1bcc3952b424c1c655bc76492c16e3af04c1e4d34d63a5ddb0da397f10dc`.
- Floki private-stage job [140008023675](https://github.com/manufact-test/nomusic/actions/runs/45847863957/job/140008023675): **SUCCESS**. Transfer SHA-256 `6eb656b329936c50f449403a9d428b23246276097f1de52d09a497b2a34f0686`, 85,161,131 bytes.
- Root HTTPS receipt check [45848612472](https://github.com/manufact-test/nomusic/actions/runs/45848612472): **SUCCESS**. `WINDOWS_OWNER_ROOT_HTTPS_SHA256_CONFIRMED 986294eb51337d1246874c1ffb8e9fac70d368b1ea5e13cb68275d81f2c257e8`. Root receipt is written only after authenticated HTTPS 200, exact byte-size and full SHA-256 verification of both owner download routes.
- Windows integration CI [45847864002](https://github.com/manufact-test/nomusic/actions/runs/45847864002) did not complete: GitHub-hosted runner ran out of disk (`ENOSPC`) during W113/W148 temp-file tests; dependent Windows job skipped. Do not describe this as an application assertion failure. The separate isolated Floki test/build above passed.

## Release boundary

Owner-only test candidate; not client stable. Customer manifest remains `approved:null`; customer baseline remains 0.24.55 / sequence 2; production publish job skipped. No mass OTA. Audible replacement has not been personally accepted.

## Owner test

Install 0.24.60 over the existing installation. Test mapped track 144530503 («Ау»), another mapped track, an unmapped/original track, Next, Play/Pause and resume. Confirm actual audible replacement, not UI labels. If it fails, export a new W54 from 0.24.60 and inspect `RESOURCE_HOOK_ATTACHED_ENDPOINT_FALLBACK`, `NATIVE_FILEINFO_REQUEST`, `SOURCE_MAPPED`. The previously supplied W54 belongs to 0.24.58 and cannot verify 0.24.60.
