# CELIKOM Android A1 — BETA11 owner TXT handoff, 21.11.2026

## Pinned source / scope
- Repo `manufact-test/nomusic`; ONLY branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Latest **functional** commit: `5d2d21279fa09728aed9c11bbcc641e21d7c9d37` — BETA11. Later docs HEAD might differ.
- Preserve existing architecture, stock original Yandex signed assets, owner single session, top-right `CELIKOM: ВКЛ · TXT`, single player, Test.50/NAV40/NAV45, backend, desktop Windows. Do not add a separate beta login/button. No device/ADB requirement. All BETA9/BETA10 tests were from owner-selected **ALBUM**, never MyWave.
- HONOR 50 Android 13 owner test track: Ramil' «Ау» original allowlist ID `144530503`, 00:43–00:54.

## BETA10 owner evidence (user's latest file)
- `CELIKOM-A1-Diagnostics-1795253330036.txt`: `DIAGNOSTIC_BETA_BUILD=A1_TRACKID_BETA10_CACHED_ORIGINAL_CREATOR_20261121`, owner enabled; ID observed, `ISSUER_VALUE_TARGET_ALLOWLISTED=ONE`, `ISSUER_ASYNC_ID_OBSERVED=ONE`, `ORIGINAL_CREATOR_KEY_CONFIRMED=ONE`, `ORIGINAL_SETTER=ONE`, `PREFETCH_STARTED=FEW`, `OWNER_RESOLVE_REQUEST=ONE`.
- No alternative: `SIGNED_MPEG_READY=NONE`, `GRANT_ADMITTED=NONE`, `DECISION_ALTERNATE=NONE`, `DATASOURCE_ARMED=NONE`, `AUDIO_OPEN=NONE`, `AUDIO_READ=NONE`; `CELIKOM_REPLACEMENT=NOT_CONNECTED`. Original Exo `EXO_OPEN_OK` and `EXO_READ_POSITIVE` do NOT count as alternate playback.
- Original direct source lineage also missing: `NATIVE_MAIN_SOURCE_ENTER=NONE`, `WRAPPER_MAIN_SOURCE=NONE`, `TRACK_DESCRIPTOR_FACTORY_LINK=NONE` even though `EXO_FACTORY_CREATED=FEW`, `EXO_SOURCE_INSTANCE=MANY`. This may be a **separate further blocker**, do not gloss over it.
- Diagnostic is `LOG_TRIMMED`; counters are one process snapshot. No actual server response body/status, no proof that approved catalogue contains this ID or that signed MPEG was reachable.

## BETA11 client changes
- First BETA11 commit `0d910119`: original Exo non-main-thread worker bounded grant wait 450ms→3000ms. Added privacy-safe summary marks:
  `OWNER_RESOLVE_APPROVED`, `OWNER_RESOLVE_NOT_APPROVED`, `OWNER_RESPONSE_INVALID`, `OWNER_SIGNED_GRANT_VALID`, `OWNER_AUDIO_RANGE_VALID`, `OWNER_AUDIO_RANGE_REJECTED`, `OWNER_PREFETCH_SUPERSEDED`, `OWNER_SOURCE_WINDOW_CLOSED`, `OWNER_OFFER_REJECTED`, `OWNER_NETWORK_OR_RESPONSE_ERROR`.
- Crucial **proven bug**: native source admission `NativeReplacementLifecycle` had independent **850ms** expiry, so raising wait alone would fail after 850ms. Final BETA11 functional commit `5d2d21279fa09728aed9c11bbcc641e21d7c9d37` makes this one original source budget match 3000ms; JVM regression accepts valid signed grant at 2500ms, rejects after 3100ms, and invalidates old generation on Next. Strict track/album/source identities and fail-closed grant validation retained. Server/stock Yandex untouched.
- CI validated: [JVM pure model #44890319497 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44890319497), [clone-only Android 13 #44890319270 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44890319270), [publisher-first paired native Android 13 #44890319418 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44890319418). This is **NOT acoustic proof**.
- One signed owner update APK: `CELIKOM-A1-RAMIL-AU-BETA11-HONOR50-20261121.apk`, 71,577,580 bytes, SHA256 `d4a479170cca73c8866ee24c66964f56a9292d3b6b1968911d2c006e204f3815`. Actual APK ZIP structure and nested module's `A1_TRACKID_BETA11_OWNER_GRANT_WINDOW_20261121` verified. ChatGPT **Library upload SUCCESS** at `/CELIKOM-A1-RAMIL-AU-BETA11-HONOR50-20261121.apk`, `library_file_id=libfile_c950fbe1dff08191b5cc1b0b73154254`. GH fallback [artifact #14702021902](https://github.com/manufact-test/nomusic/actions/runs/44890319418/artifacts/14702021902).
- APK is update-existing: install OVER BETA10 (do not uninstall, clear data/cache or relog). Signature/cert maintained by CI; stop if Android rejects update rather than wiping.

## Next action
- **Owner has NOT YET tested BETA11 on device**. Do not say alternate works. Request only **one** album playback check with existing Ramil' «Ау» 00:43–00:54; if still original, owner sends ONE BETA11 TXT.
- First verify `DIAGNOSTIC_BETA_BUILD=A1_TRACKID_BETA11_OWNER_GRANT_WINDOW_20261121`, then new resolve/response/range/window/offer categories, `GRANT_ADMITTED`, `DECISION_ALTERNATE`, `DATASOURCE_ARMED`, `AUDIO_READ` and native original source lineage.
- If `OWNER_RESOLVE_NOT_APPROVED`, check exact approved active backend catalogue entry by authorized server/admin means; do not loosen or guess ID, do not modify backend without separate owner instruction. If `OWNER_SOURCE_WINDOW_CLOSED`, adjust only timing with verified evidence. If grant admitted but DataSource absent, next task is proving direct original source lineage; do not activate generic/global source injection.
- Do not produce counter-only APKs, claim green CI means audio, or return to NAV explorations. Fail closed to original.
