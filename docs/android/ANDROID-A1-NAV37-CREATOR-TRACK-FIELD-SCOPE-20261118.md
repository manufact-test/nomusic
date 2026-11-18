# CELIKOM Android A1 — NAV37 exact tCa creator Track-field scope

18 November 2026. Scope: `manufact-test/nomusic`, sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

**Status:** NAV37 diagnostic candidate is implemented and CI-green. Owner-phone APK export and real-phone NAV37 diagnostic are still pending. This is not a product release and does not connect music replacement.

## Why this is the next minimal step

The real NAV36 owner-phone diagnostic established:
- strict live SLOT_B type1/state2 → original Lo96/Sl6 source → same original scoped Player setter source;
- the exact Player-scoped original tCa was present in bounded constructor history;
- `BIRTH_NO_TRACK_SCOPE=MANY` was the only positive of the six NAV36 birth reasons;
- NAV35 `WRAPPER_ABSENT=MANY` remained reproducible.

The signed-original DEX audit then found one exact `tCa(String)` creator whose String originates from a Track-typed field on a typed parameter object. The bounded static search did not find a direct callsite to that creator or prove the parameter's Track is the same Java object as the synchronous Gp0 scope. This was a completed negative static result, not an incomplete scan.

The next minimal test is to hook the exact creator method directly, not to invent a caller or broaden the static search. If it runs during normal playback, the constructor hook can read the Track field from the actual owner parameter that supplied the tCa String. This directly tests the missing birth-scope evidence.

## Runtime implementation

- CI generates a private target for the exact creator method and Track field from the pinned publisher-signed 2025.10.4 XAPK. The generated target is ephemeral and removed during cleanup; raw vendor symbols are not emitted.
- The read-only creator hook wraps the original method and holds a bounded owner scope only while the original method executes.
- The existing original `tCa(String)` constructor hook reads the Track field from that exact owner argument and pushes it as the active constructor Track scope.
- If owner/field/Track is null or unreadable, the constructor hook pushes a null scope that shadows any outer Gp0 scope. It never borrows an unrelated Track.
- After the original constructor succeeds, bounded weak-reference evidence records the relationship among the wrapper, Track, Flow and Album.
- Original method/constructor execution is preserved. No original Yandex binary, Player setter, audio pipeline, decoder or replacement behavior is modified.

## NAV37 marker and counters

Active marker: `NAV_V37_TCA_CREATOR_TRACK_FIELD_SCOPE_READONLY`.

Registration event: `AUDIO_NATIVE_TCA_CREATOR_HOOK` with `REGISTERED` or `NO_HOOK`.

New bounded counters:
- `TCA_CREATOR_OWNER_ENTER`, `TCA_CREATOR_OWNER_NULL`;
- `TCA_CREATOR_TRACK_FIELD_READ`, `TCA_CREATOR_TRACK_FIELD_NULL`, `TCA_CREATOR_TRACK_FIELD_FAILED`;
- `TCA_CREATOR_WRAPPER_CONSTRUCTED`, `TCA_CREATOR_WRAPPER_NO_TRACK`, `TCA_CREATOR_WRAPPER_NOT_FLOW`;
- `TCA_CREATOR_WRAPPER_FLOW_MATCH`, `TCA_CREATOR_WRAPPER_NO_ALBUM`, `TCA_CREATOR_WRAPPER_ALBUM_LINK`.

All NAV36 counters and the six original tCa birth categories are retained. The parser now includes the new creator hook in `stage_b_native_track_source_hooks` and accepts only the fixed `TRACK_CREATOR` origin. Unknown origins and other process IDs remain rejected. No names, IDs, URLs, PCM, media bytes, tokens or private field values are exported.

A positive `TCA_CREATOR_WRAPPER_ALBUM_LINK` is structural evidence only: the Track read from the exact creator owner belonged to the observed Flow and had an Album link. It does not prove the current selected edition, current queue generation, or acoustic output.

## CI evidence

- [ARM13 publisher-first owner pipeline #44349835364 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44349835364).
  - Publisher-first 75-second lifecycle passed before clone install.
  - Clone installed after publisher; 16 source splits accounted for; clone lifecycle stable for 25/25 observations.
  - `AUDIO_NATIVE_TCA_CREATOR_HOOK=REGISTERED`.
  - Owner signer verified; signer and known installed NAV36 signer SHA256: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`.
  - `owner_apk_install_mode=UPDATE_EXISTING`; fresh-install authorization false.
  - `owner_phone_touched=false`, `audio_or_account_tested=false`, `stage_a=NO_GO`, `stage_b_current_player_album_edition_attested=false`, `diagnostic_only_not_product_or_releasable=true`.
  - Push-triggered run intentionally did not export an APK.
- [JVM observer regressions #44350073072 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44350073072).
- [Clone-alone differential ARM13 #44349367581 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44349367581).
- [Parser/ARM13 run #44347371311 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44347371311) also reported the new hook as REGISTERED.

The old NAV36 one-shot workflow was changed to manual-only; it is no longer part of the automatic NAV37 CI gate.

## Package export and owner-phone check

The CI package is named:
- APK: `CELIKOM-A1-NAV37-Tca-Creator-Track-Field-ReadOnly-20261118.apk`;
- GitHub artifact: `CELIKOM-A1-NAV37-Tca-Creator-Track-Field-20261118`.

The package export is intentionally manual. Open [the NAV37 ARM13 workflow](https://github.com/manufact-test/nomusic/actions/workflows/android-a1-metrica-init-state-observer-arm13.yml), select the sole working branch, set `export_diagnostic_apk=true`, and leave `authorize_fresh_clone_install=false`. The workflow uses the known NAV36 installed signer SHA as fallback when the explicit installed-cert variable is unset, so the package is prepared as an in-place update.

After the manual run, retrieve the artifact, verify APK signer SHA256 and APK/ZIP SHA256, upload the ZIP to personal ChatGPT Library, download it back and byte-compare. Do not deliver an unverified GitHub artifact or sandbox path.

On the phone, install NAV37 over NAV36 without uninstalling CELIKOM or clearing data/cache. If Android reports signature mismatch or asks to remove NAV36, stop. Use Yandex normally for 2–5 ordinary tracks; no special seek/pause/Bluetooth tests are needed. Press `Сохранить диагностику` and send only the resulting TXT from `Загрузки/CELIKOM A1`.

## Current product status

`CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. Original Yandex 2025.10.4 #120.1gpr and its known-good playback remain untouched. NAV37 is a diagnostic step only; do not create NAV38 or connect replacement until the real-phone evidence is analyzed.
