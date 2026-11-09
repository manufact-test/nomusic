# W29 — owner audio diagnosis and safe Yandex metadata envelope (2026-11-09)

## Owner evidence: CELIKOM 0.24.1 diagnostic TXT
- NativeIntegration=ACTIVE, bridge started, enabled, signed in; YandexVersion=unknown.
- Four RESOLVE_APPROVED and renderer GRANT_DELIVERED events.
- At least three SOURCE_SYNTHETIC_RESPONSE events following NATIVE_FILEINFO_SLOW, with later NATIVE_FILEINFO_OK for the same IDs. One earlier original downloadInfo mapped successfully.
- MEDIA_REQUEST_SEEN but MEDIA_HTTP_UNVERIFIED; no observable MEDIA_PLAY / MEDIA_PAUSE / MEDIA_ERROR. This does not prove audio was decoded. Owner had previously reported a new track instantly pausing.
- Confirmed implementation risk: W26/W28 replaced the actual resource envelope with {responseTime:0,url:"",downloadInfo:...} if native getFileInfo waited past 130ms. That is not an authenticated native Yandex response. This is a plausible cause of pause but cannot be uniquely proven by these logs.

## Fix W29, version 0.24.2
- Never fabricate file-info envelope if Yandex takes longer than 130ms. Wait for original getFileInfo; log NATIVE_FILEINFO_WAIT at 130ms for diagnosis, not as a source switch timeout.
- Apply CELIKOM approved source only to an existing non-null native fileInfo/downloadInfo object; preserve original envelope fields exactly. If no supported field exists, return the Yandex response unchanged. Propagate official errors unchanged.
- For getFileInfoBatch, no fake outer result on native error, no fabricated list, no appended tracks absent from original result; only overlay exact-ID existing entries. Keep native queue and player controls untouched.
- GUI fix: DockStyle.Fill for both visible bottom buttons — «Открыть Яндекс.Музыку» and «Скачать диагностику» no longer use WinForms default 75px button width.
- Tests cover delayed native response, unknown envelope, native errors, batch errors, absent records. No auth / Yandex-account secrets logged.

## Safety and verification
- Pre-change backup: backup/windows-w29-before-owner-audio-fix-20261109 at 7c1858e634a91c7c5516353fd7010aa822bf73d0.
- Working branch: experiment/windows-companion-integration-20261108; internal unsigned installer 0.24.2 only after W22/W23/W20 CI pass.
- Original Yandex recovery flow untouched. No change to Android, extension, server or production.
- CI real Yandex uses disposable runner but has no authorized music account; never claim audio fixed without owner hearing a successful CELIKOM substitution and native pause/seek/next.
- Owner install path: press «Восстановить Яндекс» in old CELIKOM; uninstall old application; install ONE new 0.24.2 EXE from completed artifact; connect CELIKOM in GUI once. Do not manually edit Yandex or disable Defender. Audio still unverified pending test.

## Verified CI after W29 functional commit
- Functional code SHA: `bceb51b51f8c32da51c0f5cf98ec39679f166173`.
- [W22 adapter/source CI #42638433704](https://github.com/manufact-test/nomusic/actions/runs/42638433704): SUCCESS.
- [W23 genuine-Yandex disposable Windows CI #42638433590](https://github.com/manufact-test/nomusic/actions/runs/42638433590): SUCCESS; 43 JS/native source/renderer tests; 66 .NET bridge checks; native host install/restore, owner diagnostic log, and original bytes/signature restoration verified. Report error="".
- [W20 one-installer CI #42638433588](https://github.com/manufact-test/nomusic/actions/runs/42638433588): SUCCESS, including real Windows installation/uninstallation smoke.
- [Companion Preview CI #42638433646](https://github.com/manufact-test/nomusic/actions/runs/42638433646): SUCCESS.
- Owner-downloadable **single internal installer ZIP**: [CELIKOM-W29-NATIVE-SAFE-UNSIGNED artifact #13683048267](https://github.com/manufact-test/nomusic/actions/runs/42638433588/artifacts/13683048267), contains one EXE, version 0.24.2; archive download from GitHub Actions.
- Genuine owner-account audio=NOT_TESTED_NO_ACCOUNT. No claim that actual Yandex track play, pause, seek, Next now work; owner must test. Existing 0.24.1 diagnostic retains its value.
