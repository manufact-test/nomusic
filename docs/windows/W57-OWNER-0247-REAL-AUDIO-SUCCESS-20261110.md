# W57 — owner confirms real CELIKOM Windows 0.24.7 playback success (2026-11-10)

## Highest-confidence acceptance
The **owner directly reported** on the genuine installed Windows Yandex Music client after the 0.24.7 update: **«Охуеть, всё работает.)))»**. This is the first explicit owner confirmation that real approved substitution audio plays; W50 0.24.6 had failed with silent tracks and 7/7 native HTTP403. This is not just a simulated CI/network 206.

The owner also supplied the real post-update private 15-minute export **`CELIKOM-diagnostics-20261110-132656.txt`** (generated UTC `2026-11-10T10:26:59.4860217+00:00`). Its content is user evidence, **not** automatically stored as a GitHub repository attachment. Only the privacy-safe interpreted facts below are recorded.

## Post-upgrade real evidence
- `AppVersion=0.24.7.0`, `NativeModuleVersion=0.24.7`, `NativeModuleMatchesApp=true`, `NativeIntegration=ACTIVE`, `BridgeStarted=true`, `Enabled=true`, `SignedIn=true`; reinstall/upgrade native component produced `NATIVE_RESTORE_OK`, `NATIVE_INSTALL_OK`.
- True native signed resource Media GETs (not artificial probes), **both HTTP 206**: `resource_id=139` at 10:26:24.592 UTC and `resource_id=1` at 10:26:34.577 UTC. Each includes `PLAYER_URL_SIGNED_FIELDS_INTACT` with its matching ID. **0 native HTTP403**; export summary `NativeAudio403Observed=false`, `NativeMediaUrlQueryMismatchObserved=false`, `NativeMediaUrlSignedFieldsIntactObserved=true`, `PlayerNetworkCorsFailureObserved=false`.
- Native approved mapping: Yandex track `42498653` produced `GRANT_FOUND`, `SOURCE_MAPPED`, and resource 139 received HTTP206. Other granted/mapped tracks include `85025192` (`SOURCE_BATCH_MAPPED`) and `144530503` (`SOURCE_MAPPED`); no need to assert unverified exact mapping to resource 1.
- One `PLAYER_NET_FAILED|resource_id=139` occurs **after its confirmed HTTP206** and during a later track transition. Its exact reason is not available in redacted log. Do not equate it with HTTP403 or claim the transfer fully finished; might be cancellation/preloading.
- `PlayerAudibleEventObserved=false` and `ReplacementAudibleProof=NOT_AVAILABLE_FROM_NETWORK_OR_MAPPING` explicitly mean that **CDP cannot confirm audible output**. The missing CDP audio flag does **not** refute the owner's own successful hearing. The **owner report** is the audible proof.
- `EngineFastPauseObserved=true` is a summary of startup events at 10:26:09.688 UTC, **before the first approved mapping at 10:26:24**. Do not attribute startup Pause to a substituted song.
- `YandexVersion=unknown` in this TXT; do not infer actual owner desktop Yandex version from previously pinned disposable CI vendor version.
- Owner only said **"everything works"**; core substitution audio accepted. There is no separate explicit owner's evidence yet of long-run stability, fast Next/radio, Pause/Seek across many replaced tracks, all replacement IDs, or no playback artifacts. Keep those **UNVERIFIED**, not failures.

## Code root fix (W56)
Original vendor `DownloadInfoSource.src` appends `?vsid=...&source_index=...` to the signed CELIKOM URL. W56 `native-resource-adapter.mjs` adds one benign trailing `&celikom_native_query_guard=0` **only to approved native playback media URLs** (not the signed resolve grant and not non-replaced music) to absorb the native query suffix, preserving signed `token`, `expires`, `sid` and normal `#t` seek fragment. The first owner test strongly confirms this is the practical solution, closing the observed 403 blocker, even though the old 0.24.6 raw wire URL wasn't captured.

Security and compatibility proof: disposable PHP/MySQL session/entitlement/Range test #42796387968 SUCCESS; genuine Yandex disposable integration and restore #42796852849 SUCCESS; W20 0.24.7 installer #42796898660 SUCCESS; genuine 0.24.6 → 0.24.7 in-place DPAPI-state-preserving upgrade #42797545026 SUCCESS.

## Owner-accepted baseline and next
**Retain 0.24.7 as the first owner-accepted Windows AUDIO-PLAYABLE baseline. DO NOT blindly change or replace its native signed-query guard.** Exact source build commit `e6313ce5ed1099616a353fb59927847bb1db2beb`; exact internal unsigned installer SHA256 `cdd69637336045de8922c07fe4063f3b0e942e2e536d7d972469b921bf4f02f8`; real Library file `/CELIKOM/Windows/CELIKOM-W56-SIGNED-QUERY-GUARD-UNSIGNED.exe` ID `file_0000000029d08212a1e08d5efc34d6b0`. This is still an **unsigned private test build**; owner audio success does not amount to public release signing, security validation, or exhaustive controls QA.

Suggested next independent checks **without changing the accepted 0.24.7**: Pause/Seek on a substituted song; Next to another substituted song and to an original one; short radio/playlist run and check for clicks, 403s, clipping or wrong track. If they work, mark controls separately owner-accepted. Don't demand immediate repetition of songs just to prove already-accepted audible playback.

Do not touch Android/Test.50, public PHP production, original Yandex binaries or user account data. Preserve a frozen backup branch after W57 docs and verified 0.24.7 release state.
