# CRITICAL OWNER DELIVERY RULE — READ BEFORE ANY FUTURE APK DELIVERY

The owner **cannot download APKs from GitHub on his phone**. This is a repeated, explicit constraint. For every future Android APK that the owner must install on the phone, provide a **direct non-GitHub HTTPS download URL from `https://celikom.com`**. A GitHub release page, GitHub asset URL, Actions artifact, ChatGPT attachment, or instructions to download from GitHub on the phone are NOT acceptable substitutes.

Use only the trusted-main signed Floki spool:
- Workflow: `.github/workflows/android-a1-owner-floki-spool.yml` (trusted `main`, data-only stage).
- Update `.github/deploy/a1-owner-download-request.json` with the exact successful Android source workflow `run_id`, `attempt`, and its exact unpublished owner draft `release_id`; the currently stored request is stale and points to the older run `45959535273` / release `460295768`. Never trigger it unchanged.
- Commit/push the updated request JSON to `main` to trigger the trusted spool workflow's `push.paths` route. Do not rely on its `workflow_run` filter: it still names an older BETA13 workflow name, while the current source workflow is named BETA24.
- Wait for the isolated Floki runner to stage the exact APK as data and for the independent root consumer to create the matching receipt. Verify exact run/attempt, APK filename, size, SHA-256, original package/signing certificate, `https_verified=true`, and the HTTPS readback. The workflow must also write the owner URL to the unpublished draft and read it back.
- Only then retrieve the **actual** `A1_OWNER_DOWNLOAD_URL` from the unpublished draft and send that exact URL privately in chat. URL shape is `https://celikom.com/downloads/a1/<48-hex-token>/<APK filename>`; never guess or fabricate it.
- Never put the capability token/URL, private owner diagnostics, secrets, or root receipts into Git, public Actions logs/summaries, or documentation.
- Old direct-SSH workflow `.github/workflows/android-a1-owner-floki-download.yml` is disabled and MUST NOT be re-enabled. Do not bypass the isolated runner or weaken host/root/SSH security.

The current BETA24 is a one-off exception: the owner already downloaded it to his PC and will transfer it to the phone. No Floki URL has been verified for this already-downloaded build. **All subsequent builds must use the direct `celikom.com` link.**

---

# CURRENT HANDOFF — CELIKOM A1 BETA24 per-wrapper source-lineage repair — 2026-11-27

## Current owner-test status

The previous BETA23 owner diagnostic still showed no audible replacement:

- Server-side owner resolve, signed audio, alternate decision and grant admission were positive.
- The original player DataSource was not armed/opened/read: `DATASOURCE_ARMED=NONE`, `AUDIO_OPEN=NONE`, `AUDIO_READ=NONE`.
- `TRACK_DESCRIPTOR_FACTORY_LINK` and `TRACK_FACTORY_SOURCE_LINK` were absent.
- `ORIGINAL_CHILD_WRAPPER_LINK_MISSING` was present.

## Root cause fixed in BETA24 source

`StageBAudioEvidence.onNativeTrackWrapperCreated()` reused a bounded `NativeTrackSourceLink` by Track identity, then rebound the existing link to a newer wrapper and cleared descriptor/factory/source state. Yandex can create several live `tCa` wrappers for one Track. A sibling wrapper could therefore erase the exact wrapper lineage belonging to the original source chain.

## Implemented code repair

Branch:
`experiment/android-a1-metrica-init-state-observer-arm13-20261112`

Android source commit used by the delivered APK:
`901a421e461311de4b2fbba42c1c7ec78f55cb93`

Current documentation commit before this update:
`dd5abc033d228f9059a95393f8299bb60f49fcdf`

Changes in `StageBAudioEvidence.java`:

- Keep an independent source-lineage record for each exact wrapper object; never rebind by Track alone.
- A second wrapper for the same Track is a sibling lineage, not a replacement and not a reason to clear the first wrapper's descriptor/factory/source.
- Repeated observation of the same wrapper/Track/Album is idempotent and preserves its touched/open state.
- If the bounded link table evicts a wrapper link, restore it only from that exact wrapper's unique creator-birth record and the same live Track+Album objects still in Flow.
- Reject ambiguous/conflicting reuse of the same wrapper identity and mismatched Track/Album; remain fail-closed.
- Added privacy-safe counters:
  - `TRACK_WRAPPER_SAME_TRACK_PARALLEL`
  - `TRACK_WRAPPER_SAME_IDENTITY_REFRESH`
  - `TRACK_WRAPPER_IDENTITY_CONFLICT`
  - `TRACK_WRAPPER_LINK_RESTORED_WITH_SAME_TRACK_SIBLING`

Regression coverage exercises parallel wrappers for one Track, duplicate same-wrapper callbacks, link eviction/restoration with same-Track siblings, and conflicting wrapper identities.

## CI and native validation — completed

- JVM / issuer-proxy / source-lineage regression: PASS, owner run `45969190985`.
- Clone-alone differential ARM13: PASS, run `45968602583`.
- Publisher-first original-Yandex + CELIKOM Android 13 native side-by-side 75-second launch gate: PASS, owner run `45969190985`.
- A separate paired native run `45968602446` also completed successfully.

Important limitation from the actual owner-run receipt/log:

- Verdict is `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- `stage_a=NO_GO`.
- `acoustic_replacement_proven=false`.
- `owner_handset_touched=false`.
- The CI pass proves the native launch/compatibility gate, **not** that alternate audio reached the original DataSource or was heard. Hook registration alone is not audio replacement.

## Delivered owner APK — use this exact draft

Private owner-only draft release ID: `460365440`.

Source unpublished owner draft release ID: `460365440` (internal build record only).
The owner has already downloaded this BETA24 APK to his PC and will transfer it to the HONOR 50 manually. This particular build was **not** published through FlokiNET; no `celikom.com` capability URL exists/has been verified for it. Do not send the owner a GitHub download URL or tell him to download APKs from GitHub on the phone.

Filename: `CELIKOM-A1-RAMIL-AU-BETA24-HONOR50-20261127.apk`

Size: `71,598,060` bytes.

SHA-256:
`e8208201d2c06c107a9a0c996b9bb7fd8f3b7a3ce7d1a240640d045bc9c84e4c`

This is the new package from source commit `901a421e461311de4b2fbba42c1c7ec78f55cb93`. Do not use the older BETA24 draft release `460295768` (it contains the previous package).

## Next action — real HONOR 50 owner test

1. Install this APK **over the existing CELIKOM BETA23**. Do not uninstall CELIKOM, clear app data, or clear cache.
2. Open the original Yandex Music app and play Ramil / 10AGE — `Ау` directly from album `38902809`, original track ID `144530503`. Do not use MyWave.
3. Listen to `00:43–00:54`.
4. Export a fresh CELIKOM diagnostics TXT from that same test session and attach it here, whether the sound changes or not.

The diagnostic chain to inspect is:

`TRACK_WRAPPER_LINK_RESTORED` → `TRACK_DESCRIPTOR_FACTORY_LINK` → `TRACK_FACTORY_SOURCE_LINK` → `AUDIO_EXO_FIRST_OPEN_ARM` → `DATASOURCE_ARMED` → `AUDIO_OPEN` → `AUDIO_READ`.

Also inspect the four new `TRACK_WRAPPER_*` counters above. If the chain stops, fix the first missing link; do not jump to unrelated codec/server changes. If all counters pass but the sound remains original, the TXT must show the next break before another patch is chosen.

## Working rules

- Continue only in the existing repository and branch above; do not create a replacement project or branch.
- Read this handoff before changing code and update it after each accepted milestone.
- Do not claim audible replacement from JVM, CI, hook registration, or native launch alone.
- Do not disable original Yandex protections, alter its package, or bypass owner-signature checks.
- Do not change server catalogue, signed grant, Range/HMAC, Windows, stable Android, or OTA unless the new owner diagnostic proves that area is the first failing stage.

---

# CURRENT HANDOFF — 26.11.2026, BETA18 source-factory bridge

## Latest owner test: BETA17 still does not replace audio

Owner diagnostic: `CELIKOM-A1-Diagnostics-1795698832394.txt` (BETA17).

- Owner resolve/grant path is positive: `OWNER_RESOLVE_APPROVED=ONE`, `SIGNED_AUDIO_READY=ONE`, `GRANT_ADMITTED=ONE`, `DECISION_ALTERNATE=ONE`.
- Actual byte source is not armed: `DATASOURCE_ARMED=NONE`, `AUDIO_OPEN=NONE`, `AUDIO_READ=NONE`.
- The decisive source-lineage counters: `TRACK_DESCRIPTOR_FACTORY_LINK=ONE`, but `TRACK_FACTORY_SOURCE_LINK=NONE`; no track source open/read links.
- This identifies the break between the exact descriptor-returned factory and the concrete Exo DataSource instance. Do not change server catalogue, signed grant, Range transport, original Yandex package, stable Android or Windows.

## BETA18 patch committed to the existing experiment branch

Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

- Added `NativeExoFactoryProductWitness`: resolves the unique zero-argument product method on the exact factory object returned by the signed original descriptor factory. It accepts only the concrete `RetryingBalancingDataSource` return or the exact Media3/legacy Exo DataSource contract, rejects missing/ambiguous/static methods, and never logs private vendor symbols.
- Hooks the exact method on that descriptor-returned factory instance. Its receiver identity is then used by the existing Stage B descriptor→factory→DataSource lineage. The old pinned nested-factory hook remains and shares the method registry to prevent double-hooking.
- Added privacy-safe event `AUDIO_EXO_FACTORY_PRODUCT_HOOK`: `REGISTERED`, `NO_EXACT_METHOD`, `AMBIGUOUS`, or `NO_HOOK`.
- Added JVM regression tests for unique/inherited/overridden methods, interface return types, default methods, ambiguity, static and wrong-return rejection. Local run: `NATIVE_EXO_FACTORY_PRODUCT_WITNESS_PASS assertions=14`.
- Updated owner marker/output/instructions to BETA18. BETA18 is to install over the owner's BETA17 test build; no app data wipe.

## BETA18 build and Floki delivery — CONFIRMED 26.11.2026

- Owner APK source workflow: run `45833293758`, attempt `1`, source commit `22f217ad0f69af69cd0cf09149146558d7379eda`. JVM and publisher-first native ARM13 jobs both **SUCCESS**; the owner export step completed and created the unpublished draft release `459494184`.
- Package: `CELIKOM-A1-RAMIL-AU-BETA18-HONOR50-20261126.apk`, 71,589,868 bytes, SHA-256 `b9371ef319ff2c03e1b34106dee95d96ee67f4a6ac73034aeaa0b3ef16cb7ecf`.
- Trusted-main Floki spool run: `45835668712` — **SUCCESS**. The runner independently verified the persistent signing certificate and package identity, staged the exact APK, received matching root receipt with `https_verified=true`, and read back the owner-only HTTPS URL in the unpublished release draft.
- The owner-only capability URL is deliberately NOT copied into Git, docs, or logs. It is present only in the unpublished owner draft.
- BETA18 instructions: install over BETA17, do not clear app data; play Ramil `144530503` from album `38902809`, listen at 00:43–00:54, then export the CELIKOM TXT.
- **Audio replacement is still unproven.** BETA18 is delivered for owner testing, not product acceptance. The next diagnostic must show whether `TRACK_FACTORY_SOURCE_LINK` now appears, followed by `DATASOURCE_ARMED`, `AUDIO_OPEN`, and `AUDIO_READ`. Owner listening confirmation is still required.
- BETA16 stable and all other channels remain untouched. Never publish the owner draft or copy its capability URL into Git/docs/logs.

---

> **BETA11 OWNER TEST — STILL NO SWAP (21.11.2026), diagnostic `CELIKOM-A1-Diagnostics-1795254709741.txt`:** Installed `A1_TRACKID_BETA11_OWNER_GRANT_WINDOW_20261121`; owner auto-enabled. `PREFETCH_STARTED=ONE`, `OWNER_RESOLVE_NOT_APPROVED=ONE`, `OWNER_RESOLVE_APPROVED=NONE`, `OWNER_NETWORK_OR_RESPONSE_ERROR=NONE`, `OWNER_RESPONSE_INVALID=NONE`, `SIGNED_MPEG_READY=NONE`, `GRANT_ADMITTED=NONE`, `DECISION_ALTERNATE=NONE`, `DATASOURCE_ARMED=NONE`, `AUDIO_OPEN/READ=NONE`. The **authenticated HTTP resolve returned valid JSON but did not meet found+approved+entitled+audio/mpeg**. Exact cause (found=false due to no active replacement/file; entitlement=false; other format) not differentiated by BETA11 counters; do NOT assert a specific cause. Separately `ISSUER_VALUE_TARGET_ALLOWLISTED=NONE`, `ISSUER_VALUE_OTHER_NUMERIC=FEW`, `ISSUER_VALUE_SCOPE_ABSENT=FEW`, `ORIGINAL_SETTER=NONE`, `EXACT_PREPARE=ONE`, `WRAPPER_MAIN_SOURCE=NONE`, `TRACK_DESCRIPTOR_FACTORY_LINK=NONE`. **Prefetch can be triggered by first-party tCa(String) constructor even without issuer Retrofit allowlist counter** (`StageBAudioEvidence.java:960-969`); this explains otherwise apparently conflicting metrics. `LOG_TRIMMED` and multiple user-requested process restarts: snapshot is per most recent process, not proof same track was present throughout. **Next action is NOT another timeout tweak/APK:** verify server ACTIVE approved MP3 asset mapped by `service=yandex`, `track_id=144530503` through authenticated catalogue/DB (`PdoCatalogRepository.findActive`, status approved, is_active=1, disabled_at NULL, storage file exists, audio/mpeg; verify album-played exact original publisher ID separately, do not blindly allowlist 38436680). Only after backend data matches, fix exact source/creator chain, because direct wrapper → descriptor → factory source remains unproven. No authenticated backend access from this chat; no server changes or APK made. Owner tested from ALBUM, never ask MyWave. Functional code HEAD remains `5d2d21279fa09728aed9c11bbcc641e21d7c9d37`.

> **BETA11 SIGNED/CI-GREEN OWNER APK in Library 21.11.2026:** owner BETA10 TXT `1795253330036` showed target ID and original setter confirmed, but no signed MPEG grant or alternate audio. Fixed both mismatched Exo waiting **and** separate native admission deadline (old 450ms/850ms, now bounded 3000ms); privacy-safe resolve/Range/rejection diagnostics added. Functional HEAD `5d2d21279fa09728aed9c11bbcc641e21d7c9d37`. JVM `44890319497`, clone `44890319270`, paired `44890319418` all SUCCESS. APK `/CELIKOM-A1-RAMIL-AU-BETA11-HONOR50-20261121.apk` uploaded to Library (libfile_c950fbe1dff08191b5cc1b0b73154254), SHA256 d4a479170cca73c8866ee24c66964f56a9292d3b6b1968911d2c006e204f3815. **No acoustic proof**; next owner checks same track FROM ALBUM. See [full handoff](./CELIKOM-A1-BETA11-OWNER-GRANT-WINDOW-HANDOFF-2026-11-21.md).

> **BETA11 real deadline bug fixed:** The original 450ms Exo wait was raised to 3000ms, but the same `NativeReplacementLifecycle` was still hard-coded to 850ms and would reject later grants even while Exo waited. A1-only instance now uses the matching 3000ms, with Java regression checking acceptance at 2500ms, refusal at 3100ms and Next invalidation. Previous `0d910119` CI/export is superseded; only the following final BETA11 commit is deliverable. Still no sound proof. 

> **BETA11 OWNER GRANT WINDOW (21.11.2026):** New HONOR 50 BETA10 TXT `1795253330036` confirms owner enabled, issuer allowlisted ID, original first-party creator key and original Player setter! `ORIGINAL_CREATOR_KEY_CONFIRMED=ONE`, `ORIGINAL_SETTER=ONE`, `PREFETCH_STARTED=FEW`, `OWNER_RESOLVE_REQUEST=ONE`, yet `SIGNED_MPEG_READY=NONE`, `GRANT_ADMITTED=NONE`, `DATASOURCE_ARMED=NONE`, `AUDIO_READ=NONE`. `NATIVE_MAIN_SOURCE_ENTER=NONE`, descriptor/factory/source lineage absent; **second independent blocker potentially exists**, do NOT promise playback. Existing pre-prepare network grace only 450ms vs two HTTPS requests and single-thread async queue, an observed deterministic race risk. BETA11 extends this *only on owner allowlisted, non-main Exo worker* to capped 3000ms, and adds privacy-safe bucket counters separating HTTP/resolve/eligibility/signed grant/Range/stale window/bridge offer; does not change backend, architecture, signed original APK, or allowlist. BETA11 needs JVM/native paired/clone CI and one signed APK before owner test. Next owner TXT must pinpoint first rejecting stage; if resolve returns not-approved, do NOT retry APK changes: verify exact backend active catalogue mapping with authorized server tooling; if grant ready but source lineage absent, fix exact original source path. Original user test came FROM ALBUM, never suggest MyWave.

> **BETA10 SIGNED OWNER APK ГОТОВ, 21.11.2026:** sole functional commit `58f66bfad0a1e22c5cdb2498368f20d13b9ebc42` (cached first-party creator-key fallback). JVM `44888308302`, clone-only `44888308304`, publisher-first paired `44888308310` all **SUCCESS**; actual APK SHA256 `aca6275e0c4426eaca7e9741a85890e62177ce625d1cd7a4a669e72beb46b350`, 71,577,580 bytes, embedded marker `A1_TRACKID_BETA10_CACHED_ORIGINAL_CREATOR_20261121`. **Library successfully uploaded**: `/CELIKOM-A1-RAMIL-AU-BETA10-HONOR50-20261121.apk` (`libfile_c43af66665848191b38ce7dcf69a6646`); fallback GitHub artifact `14700897194`. **SOUND NOT CONFIRMED**, next user TXT or explicit listening acceptance required. BOTH BETA9 tests were directly FROM ALBUM, not MyWave. [Full BETA10 handoff](./CELIKOM-A1-BETA10-CREATOR-CACHE-HANDOFF-2026-11-21.md).

> **21.11.2026: BETA9 OWNER #2 ИЗ АЛЬБОМА, НЕ MYWAVE.** TXT `1795251788487` подтверждает `ISSUER_VALUE_TARGET_ALLOWLISTED=NONE`, `OTHER_NUMERIC=FEW`, `ISSUER_ASYNC_ID_OBSERVED=NONE` и отсутствие подмены. Никогда больше не просить владельца искать трек или повторять тот же тест: он оба раза выбирал «Ау» непосредственно из альбома. Сделан функциональный BETA10 first-party original tCa creator-key cached fallback, только при точном allowlisted ключе и той же оригинальной Track/Flow/Wrapper/Album/Player setter линии; stale issuer ticket fail-closed; prefetch до setter. Это **гипотеза исправления кеш-пути**, не доказанный звук. Следующий шаг: дождаться CI publisher-first+clone-only, выдать один подписанный BETA10, проверить на HONOR 50. [BETA9 и BETA10 детали](./CELIKOM-A1-BETA9-OWNER-TXT-NEXT-CHAT-2026-11-21.md).

> **BETA9 OWNER TXT ПОЛУЧЕН 21.11.2026:** `CELIKOM-A1-Diagnostics-1795251151619.txt` подтвердил `A1_TRACKID_BETA9_EXACT_ASYNC_ISSUER_CREATOR_20261121`, но `ISSUER_VALUE_TARGET_ALLOWLISTED=NONE`, `ISSUER_VALUE_OTHER_NUMERIC=FEW`, `ISSUER_ASYNC_ID_OBSERVED=NONE`, `ORIGINAL_SETTER=NONE`, `DATASOURCE_ARMED=NONE`. Owner сообщает: альтернативы нет. Главное — target issuer ID не зафиксирован в текущем снимке (лог частично обрезан, есть previous process exits), а не доказанная ошибка creator join. Сначала focused cold process replay EXACT `144530503` и TXT без перезапуска. Никаких counter-only BETA10 или ослабления allowed ID. [Полный BETA9 handoff](./CELIKOM-A1-BETA9-OWNER-TXT-NEXT-CHAT-2026-11-21.md). Функциональный код прежний `7fac727c`; правки только документационные.

> **НОВАЯ ТОЧКА ПЕРЕДАЧИ 21.11.2026:** [BETA9 — ожидание реальной диагностики владельца](./CELIKOM-A1-BETA9-OWNER-TXT-NEXT-CHAT-2026-11-21.md). BETA9 APK загружен в ChatGPT Library (`/CELIKOM-A1-RAMIL-AU-BETA9-HONOR50-20261121.apk`, upload confirmed), поскольку sandbox-ссылка у владельца не скачивается. Записать следующий TXT только после проверки его `DIAGNOSTIC_BETA_BUILD`. Код BETA9 `7fac727c`; CI green, звук владельцем ещё не подтверждён. **Начинать со свежего owner TXT, не с архивных разделов ниже.**

# АКТУАЛЬНАЯ ТОЧКА — 21.11.2026, BETA9 original issuer async ID → signed creator

- Единственный repo/branch: `manufact-test/nomusic` / `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- **Реальный владелец установил BETA8 и прислал TXT `CELIKOM-A1-Diagnostics-1795247871997.txt`**. Результат: подмена всё ещё не работает. `DIAGNOSTIC_BETA_BUILD=A1_TRACKID_BETA8_ISSUER_VALUE_SCOPE_20261121`, `OWNER_ENABLED=ONE`, `ISSUER_METHOD_SELECTED=ONE`, `ISSUER_HANDLER_INVOKE=FEW`, `ISSUER_HANDLER_ARGS_PRESENT=FEW`, `ISSUER_VALUE_TARGET_ALLOWLISTED=ONE`, `ISSUER_VALUE_OTHER_NUMERIC=FEW`, `ISSUER_VALUE_KNOWN_OTHER_VERSION=NONE`, `ISSUER_VALUE_SCOPE_PRESENT=NONE`, `ISSUER_VALUE_SCOPE_ABSENT=FEW`, `ISSUER_TRACK_SCOPE_MISSING=ONE`, `ISSUER_PROCESSING_EXCEPTION=NONE`, `ISSUER_TRACKID=NONE`, `ORIGINAL_SETTER=NONE`, `PREFETCH_STARTED=NONE`, `GRANT_ADMITTED=NONE`, `DATASOURCE_ARMED=NONE`, `AUDIO_READ=NONE`. FileInfo API method is selected, all ClassLoaders equal and proxy matched, Exo original reading is active; CELIKOM replacement is `NOT_CONNECTED`.
- **Важная точная причина:** настоящий @Query("trackId") от Яндекса сообщает допущенный ID, но выполняется за пределами синхронной Track ThreadLocal рамки Gp0, из-за чего `StageBAudioEvidence.onPublisherAnnotatedTrackId` неизбежно отбрасывает ID. Это не проблема отсутствующего ID, неправильной аннотации или CELIKOM owner enable. Конкретная нить/временная очередность относительно setter всё ещё неизвестна, не угадывать.
- **Код BETA9 commit `7fac727c70085a51ce35e8f35c9fa3b2387ffdf5`** (точечная функциональная попытка). `StageBAudioEvidence` сохраняет только allowlisted исходный issuer ID в RAM на 30 секунд при отсутствующей ThreadLocal scope, запускает уже существующий authenticated prefetch (сам проверяет `enabled`), а при точном оригинальном tCa(String) constructor key и уникальном original Track/Album/Wrapper или Track+wrapper без Album связывает его с **тем самым original Player source setter**. Strict = Java object identity + issuer signed key, без глобального latest track и без подмены исходных Retrofit вызовов. Проверяет сроки, совпадение оригинального ключа/объектов, конфликт/отсутствие подтверждения — fail closed. Сохраняет прежние проверки signed CELIKOM grant, original Exo DataSource, prepare.
- Новые категории: `ISSUER_ASYNC_ID_OBSERVED`, `ISSUER_ASYNC_CREATOR_BOUND`, `ISSUER_ASYNC_CREATOR_STALE`; `ISSUER_TRACKID` теперь загорается при успешном оригинальном creator-join даже если issuer handler был вне threadlocal.
- **BETA9 CI полностью зелёная:** JVM + publisher-first Android13 [#44883122288 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44883122288), clone-only Android13 [#44883122281 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44883122281). JVM regression checked creator scopes 12/14, no-Album late Flow, mismatched key, expired ticket, absent ticket, Album conflict. Original publisher preserved, original first (16 splits), clone stable 75s, signer VERIFIED `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`, mode `UPDATE_EXISTING`. **CI does not check audio**: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`; `stage_a=NO_GO` is old non-audio gate label.
- **BETA9 signed APK** [artifact #14698319574](https://github.com/manufact-test/nomusic/actions/runs/44883122288/artifacts/14698319574): `CELIKOM-A1-RAMIL-AU-BETA9-HONOR50-20261121.apk`, 71,577,580 bytes, SHA256 `d17ef52602cb4d8bd4978e71cffbbd6085789162ff5ecab234678842d3ac37f6`; ZIP `CELIKOM-A1-RAMIL-AU-BETA9-HONOR50-20261121.zip`, SHA256 `58e84e25171c5286f3f355818a5bc8faa95c5a8e0d3a0fa90a7ce5f12872f7e7`, verified local. Embedded original publisher APK sha `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged.
- Следующий тест владельца: установить BETA9 **поверх BETA8 без удаления/очистки**, Ramil' «Ау» ID `144530503`, 00:43–00:54; при оригинале — TXT. Диагностика нового участка `ISSUER_ASYNC_ID_OBSERVED → ISSUER_ASYNC_CREATOR_BOUND → ISSUER_TRACKID → ORIGINAL_SETTER → PREFETCH_STARTED/SIGNED_MPEG_READY → OWNER_RESOLVE_REQUEST → GRANT_ADMITTED → EXACT_PREPARE → DATASOURCE_ARMED → AUDIO_OPEN/READ`. Никаких фальшивых аудиодоказательств.

Ниже архивные BETA8/BETA7 handoff, не считать их текущим состоянием.

---





# CURRENT 20.11.2026 — real original Exo encoded-byte route, exact signed seek position, approval handoff

**Working executable HEAD:** [745179b1](https://github.com/manufact-test/nomusic/commit/745179b11b0f837d1cdf9d46cbe142f225c2ffe3); do not restart architecture or touch NAV40/NAV45/Test.50/Windows/backend. Sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

**Real audio work completed:** The scoped original 2025 `RetryingBalancingDataSource.if(UC2)/read/close` hooks now contain actual signed HTTPS Range encoded-byte routing `NativeExoAlternateByteRoute`. When and ONLY when a specific original unopened DataSource is equipped with an entitlement-validated approved CELIKOM grant, the original ExoPlayer can read alternate encoded bytes on its existing loader, decoder, media clock and controls. It does **not** create a second player or intercept PCM. The original untouched method executes normally on all unknown/unapproved sources. First alternate open failure returns to original before any alt byte; after any alt open, a failed read/reopen or cancelled Next never substitutes original bytes into the same decoder.

**Confirmed publisher 2025 DataSpec offset:** signed private [CI #44728951933 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44728951933) corroborates `UC2` long fields `for` (uri offset), `else` (**original byte position**), `goto` (length) from exact constructor, `toString`, subrange and length getter. The hook reflects only that pinned original position field; no guessed seek/bitrate mapping.

**Admission wired in code:** Existing `NativeEarlySourceLifecycleBridge` now connects real publisher source setter and original concrete MediaPeriod before-prepare to the canonical `NativeReplacementLifecycle`, strict `NativeGrantContract`, and SAME native byte route. It has explicit methods for owner enable, independently source-bound publisher FileInfo triple and authenticated approved CELIKOM grant. Positive and negative synthetic JVM tests cover strict grant, original source, correct audio bytes, no other prefetch source, seek and cancelled in-flight Next. **Verified JVM: [#44730902321 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44730902321), [#44730740420 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44730740420).** New ARM13 on earlier code [#44730740418](https://github.com/manufact-test/nomusic/actions/runs/44730740418) and [#44730740525](https://github.com/manufact-test/nomusic/actions/runs/44730740525) were pending at last check.

**HARD BLOCKER for actual playback:** Both signed-original FileInfoApi/DownloadInfoApi Retrofit interface annotated parameters include **only** `trackId` (private [CI #44729237330 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44729237330)), not `albumId` / `editionId`. The exact original native selection album/edition STRING semantics still need real proof. Also no production on-device owner-authenticated CELIKOM resolve callback currently calls `onSourceBoundPublisherFileInfo` / `offerAuthenticatedApprovedAudio`, and owner activation isn't connected. The native byte data plane is real; the approval/semantic identity control plane remains OFF. No actual alternate playback/live sound has been observed. **NO APK for owner and NO product PASS.** Do not claim the network transport has run on the phone.

Next: connect authenticated owner CELIKOM grant and independently source-bound original Album+Edition on the existing preprepare callback, then test ONE approved fixed song audibly on HONOR 50 before any polish/VPN.

---

# CURRENT 20.11.2026 — ORIGINAL publisher annotated trackId -> exact native source frame

**Last executable code:** [a4d4af4b](https://github.com/manufact-test/nomusic/commit/a4d4af4b0671c683b37346b255b610196415ca25). Current branch HEAD (docs/static checks): [6cfe352c](https://github.com/manufact-test/nomusic/commit/6cfe352c1dc35af1f0a2112f82b595b29d491c89). No architectural restart, NAV40/NAV45/Test.50/Windows and issuer-signed original untouched.

**Meaningful forward step:** `FileInfoApi` and `DownloadInfoApi` annotated `trackId` interface methods in publisher-signed original are abstract, so hooking them directly cannot work. A runtime original clone-only interceptor now recognizes a genuine *concrete* Java Retrofit Proxy method generated for one of those exact interfaces, checks its signed `@Query/@Path("trackId")` parameter, observes the original argument **only inside the existing original Gp0 Track request scope**, and executes the publisher request exactly once unchanged. `StageBAudioEvidence` requires the same exact original Track+Album Java references plus the original `tCa(String)` numeric constructor argument; conflicts, unscoped/late requests, missing proxy or different ID deny. A qualifying in-memory trackId is delivered into the exact original `Player.e(Sl6,long)` setter frame, without persisting or logging ID. Synthetic JVM regression checks wrong Track, Album, ctor key, unscoped request, conflicting ID, and absence of ID at native setter. It never declares an unknown ID to be proven.

**Verified:** [JVM #44723797992 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44723797992) (new setter handoff); previous [JVM #44723521193 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44723521193). Earlier ARM13 on code before this hook [#44719300481 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44719300481), [#44719300477 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44719300477). New ARM13 [#44724024881](https://github.com/manufact-test/nomusic/actions/runs/44724024881) clone and [#44724024831](https://github.com/manufact-test/nomusic/actions/runs/44724024831) paired are pending at last check; older ARM13 failures #44723521310/#44723521168 stemmed from static assertion against the old constructor observation signature, which was corrected in `6cfe352c`. Check new conclusions.

**Critical reality check:** This is a concrete *possible* runtime issuer-API intercept, **NOT verified to fire with user account / actual music on HONOR 50**, and a numeric `trackId` alone is not `trackId+albumId+editionId`. There is NO approved grant, alternate source byte routing or audible replacement, no owner APK. Current `CELIKOM_REPLACEMENT=NOT_CONNECTED`. Do not spend new cycles on generic static DEX scans/diagnostic-only APKs. Next essential implementation: independently source-bound Album/edition, approved CELIKOM signed grant and actual one-player source installation at the original native playback boundary, verified in audible live playback. Unknown -> original.

---

# CURRENT 20.11.2026 — exact original creator-before-Flow source path + signed ID API limit

**Working code HEAD:** `ecd039f2edbbfa76c9f5d8b6a27a77aff9930c83` ([commit](https://github.com/manufact-test/nomusic/commit/ecd039f2edbbfa76c9f5d8b6a27a77aff9930c83)). Kept a weak original `Track+Album -> creator-owned tCa -> Exo descriptor/factory/unused DataSource` lineage even when the native creator runs **before** matching Track Flow. NAV40 historic classification `12 -> 16` remains unchanged; no new authoritative ID, source change or separate player. The initial patch `5fd10b57` had a Java compile-scope error, fixed immediately in `ecd039f2edbbfa76c9f5d8b6a27a77aff9930c83`; do NOT treat initial failed runs as green. [JVM #44719300473 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44719300473). ARM13 clone [#44719300481](https://github.com/manufact-test/nomusic/actions/runs/44719300481) and paired [#44719300477](https://github.com/manufact-test/nomusic/actions/runs/44719300477) were still in progress when checked.

**Focused original signed 2025 semantic blocker, [CI #44718767016 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44718767016):** both the single `trackId`-annotated `FileInfoApi` and `DownloadInfoApi` entrypoints are **abstract interface methods, with zero concrete original method bodies**. Direct in-process method interception at those annotated interface declarations cannot produce a trusted original Track/Album/edition binding. Do NOT implement a fake Xposed hook on abstract Retrofit methods; it will not observe the active file request. The one-hop source creator register provenance remains `CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN`. The exact semantic triple and signed CELIKOM grant/alternate bytes remain missing.

**Product status:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`, no audible alternate, no owner APK. Future work must obtain an *actual concrete source-bound producer/consumer* for semantic identity before the original pre-prepare decision, not another method-name scan or generic UI mapping. Keep NAV40, NAV45, Test.50, Windows and publisher APK untouched.

---

# CURRENT 20.11.2026 — exact original creator before Track Flow can follow native Exo source

Fixed a real order gap at the publisher's source creator: when `Gp0` creates `tCa` from a verified original Track+Album **before** that Track reaches its Flow, the existing original descriptor/factory/DataSource source identity was previously discarded. `StageBAudioEvidence` now keeps one weak creator-only source link (same exact original track/album/wrapper, no title/ID guess) that is eligible for pre-prepare source evidence. Historical protected NAV40 classifications remain exactly `12` before Flow and `16` after the same Track flows; conflicting Album still classifies `17`. No new player, source mutation or metadata read. JVM test covers both orderings and negatives. No semantic track/album/edition strings or approved grant yet; no user APK.

The prior [41146c6a JVM #44717158094 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44717158094); [clone ARM13 #44717158107 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44717158107); paired ARM13 #44717158096 pending at verification. A focused signed API entrypoint-shape check (904fe47c) is running separately; do not infer IDs from its existence.

---

# VERIFIED SOURCE CHECKPOINT 20.11.2026

Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Latest **code**: [41146c6a](https://github.com/manufact-test/nomusic/commit/41146c6acd9a3b1c2981c95905101cd9a5d8a722); previous source freshness patch [87e4ad3f](https://github.com/manufact-test/nomusic/commit/87e4ad3fbe1416ccb26c3a7d4383e1ea63232481). Java checks: [#44717158094 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44717158094) on 41146c6a, [#44716130564 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44716130564) on 87e4ad3f. Clone-only ARM13 on 87e4ad3f: [#44716130433 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44716130433). Paired ARM13 on 87e4ad3f: [#44716130607 FAILURE](https://github.com/manufact-test/nomusic/actions/runs/44716130607) at **fresh Android guest boot** (`CONTAINER_ARM_ANDROID_TWO_CLEAN_BOOT_ATTEMPTS_FAILED`, original APK never installed); this is a test-environment boot failure, not evidence of code failure or successful playback. On 41146c6a, clone [#44717158107](https://github.com/manufact-test/nomusic/actions/runs/44717158107) and paired [#44717158096](https://github.com/manufact-test/nomusic/actions/runs/44717158096) were still in progress when checked; verify final results.

Product contract unchanged: `CELIKOM_REPLACEMENT=NOT_CONNECTED`. Even with bounded original Source/Period/DataSource continuity, exact source-bound semantic `trackId+albumId+editionId`, signed approved candidate and native byte-source installer are missing. No audio-substitution build is authorized on these facts. Immutable NAV40/NAV45/Test.50/Windows and official publisher remain untouched. Next essential work: a publisher-attested triple on the SAME original source before the first prepare; then an actual single-player source installation, validated on live playback with Pause/Seek/Next/MyWave.

---

# CURRENT 20.11.2026 — unique first original prepare, no unlinked/duplicate admission reuse

The canonical original pre-prepare bridge now **revokes** period/source candidate identity on any unrelated original MediaPeriod preparing within the same generation (not merely seals the source selection). Repeated prepare on the SAME period also consumes/revokes the first preopen DataSource candidate: later descriptor/factory links cannot falsely turn it into a new offer. New JVM assertions cover original-first, duplicate, foreign-before-current and later same-source failure paths. No change to Yandex playback, no source byte swap or semantic triple; original is mandatory.

Last JVM #44716130564 SUCCESS, ARM13 #44716130433/#44716130607 pending at writing. Check this commit's own CI before claiming success.

---

# CURRENT 20.11.2026 — one-source pre-prepare freshness race closed

The exact original pre-prepare DataSource candidate is revoked on open entry, read entry, failed open, close, reissued factory referencing the SAME old Java source instance, and nonunique source mapping across tracks. Weak identity-only history is bounded and fails closed on saturation; common hot-path reads skip repeated scans once the source is already marked. Original publisher open/read/close still run exactly once, bytes not mutated.

**Still no semantic trackId+albumId+editionId from this same source; no approved grant/alternate routing; replacement OFF, no owner APK.** The preceding HEAD 69ab6ebe had JVM + both ARM13 SUCCESS (44710291864, 44710292001, 44710291805). Check new CI after this commit.

---

# CURRENT 20.11.2026 — original pre-prepare tied to exact fresh Exo DataSource instance (structural, no swap)

The existing original `Track+Album -> tCa wrapper -> descriptor -> Exo factory -> DataSource instance` lineage can now supply **one weak, not-yet-opened original DataSource candidate** when the same original source generation enters the exact original MediaPeriod prepare observer. Any mismatched original Track/Album, opened source, other period, multi-period prefetch or Next cannot retain this candidate. The supplier is wired from the existing `StageBAudioEvidence` into the same `NativeRendererStreamEvidence`/canonical bridge; no new player or listener. Dedicated Java model regression checks positive/negative cases.

**This is still not decoder-source-selection proof**, and no semantic original trackId+albumId+editionId, approved CELIKOM grant or alternate byte routing is connected. Replacement stays OFF and original audio is unmodified. CI pending for this commit; no owner APK. Signed NAV40/NAV45/Test.50/Windows untouched.

---

# CURRENT 20.11.2026 — unlinked original period pre-prepare closes pending admission

The **same concrete, already installed original period prepare hook** now closes unresolved canonical native selection to ORIGINAL even when the original period/source cannot be associated with the successful Track/Album/source lineage. It never infers selected edition from prefetch. An async ID/grant after any unknown publisher prepare cannot upgrade the playing original. A subsequent Next begins a fresh independent selection; known periods still record structural evidence without reopening admission. Test-only enabled lifecycle exercises this failure path. JVM and ARM13 status require checking on the new commit; default feature OFF, no source byte routing, no APK.

Previous paired ARM13 44704827138 / 44704633500 SUCCESS. NAV40/NAV45/Test.50/Windows/publisher original untouched.

---

# CURRENT 20.11.2026 — actual original prepare seals ORIGINAL if semantic identity is absent

In the existing in-process ORIGINAL MediaPeriod before-prepare callback, `NativeEarlySourceLifecycleBridge` now calls the **canonical** `NativeReplacementLifecycle.atNativePrepare` once for the exact original setter generation with *unproven descriptor IDs*, yielding ORIGINAL and closing the late-certification window before the publisher method proceeds. A second prepare of the same period cannot reopen it; a conflicting period remains ambiguous. Hook and the original proceed are unchanged. Default CELIKOM admission remains OFF; **no audio substitution, no grant transport or owner APK**. Added JVM regression with test-only enabled lifecycle proving late exact-looking IDs cannot upgrade an already prepared original. CI result must be checked after this commit.

Paired publisher-first ARM13 check: [#44704827138 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704827138) and [#44704633500 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704633500), conclusively checked 20.11.2026. These are 2025 original/clone runtime controls, not signed semantic identity, selected audio, or a functioning alternative.

**Next:** same-original-source semantic trackId+albumId+editionId *before* prepare, selected-period attestation, signed approved candidate; only then replace the placeholder ORIGINAL admission with a verified source/decoder decision in the existing native player. No shotgun research or diagnostic APK; NAV40/NAV45/Test.50/Windows/original untouched.

---

# CURRENT 20.11.2026 — saved handoff original MediaPeriod BEFORE prepare; no APK

**Текущий этап после кода `f379dc623fc6e312e307cd5c1c94b7b28d3662fa`:** каноническая передача [HANDOFF-A1-ORIGINAL-PERIOD-PREPREPARE-20261120.md](HANDOFF-A1-ORIGINAL-PERIOD-PREPREPARE-20261120.md). Signed original exact `wh6/o96` concrete `prepare(callback,long)` найден с одним nested interface callback и одним override: [#44705531667 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44705531667). Код до реального prepare установлен как optional read-only original-only hook; **не** доказан вызов во время реальной музыки. [JVM #44704827184 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704827184); clone-only ARM13 [#44704827181 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44704827181). Paired ARM13 [#44704827138](https://github.com/manufact-test/nomusic/actions/runs/44704827138), [#44704633500](https://github.com/manufact-test/nomusic/actions/runs/44704633500) **проверить финальный статус**. Подмена всё ещё **NOT_CONNECTED**, `IDENTITY_STATUS=STRUCTURAL_ONLY`; exact semantic trackId+albumId+editionId, active selected generation и approved grant к источнику не доказаны. NAV40/NAV45/Test.50/Windows и оригинал не трогать. Не выдавать декоративный APK; продолжать только к рабочему source admission.

---

# CURRENT 20.11.2026 — связана реальная ранняя original source generation с текущим PlaybackInfo/SLOT_B

**Реальный исполняемый code commit:** [f2333c94](https://github.com/manufact-test/nomusic/commit/f2333c947d29fb424ec7ff5452837c294b739446). Без расширения архитектуры `NativeEarlySourceLifecycleBridge` теперь принимает уже имеющийся *строго подтверждённый* callback текущего оригинального `PlaybackInfo.PeriodID + SLOT_B + live original source + renderer -4` и сопоставляет его с более ранним успешным `Player.e(Sl6,long)` setter **того же Java Track/Album/source/поколения**. Связь ревокируется при Next/новом setter или конфликте. Это реальный original early→current source continuity path, а не предположение по названию трека. [JVM #44702153647 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44702153647); clone-only ARM13 [#44702153678](https://github.com/manufact-test/nomusic/actions/runs/44702153678), paired publisher-first ARM13 [#44702153622](https://github.com/manufact-test/nomusic/actions/runs/44702153622) — проверить заключения (на момент записи ещё шли). Предыдущее original setter hardening проверено полностью на паре [#44700743688 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44700743688) и standalone [#44700743677 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44700743677).

**Ключевое ограничение:** current `-4` renderer callback поздний; факт source continuity **не превращается в допуск до prepare**, не подтверждает semantic `trackId+albumId+editionId`, декодер или право на альтернативу. `NativeReplacementLifecycle` подключён к setter, но остаётся OFF до отдельного разрешения и подлинных ID/edition. `IDENTITY_STATUS=STRUCTURAL_ONLY`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`. Никакого нового APK: NAV40/NAV45/Test.50/Windows/original Yandex не менять. Следующая практическая задача без очередных широких сканов — **семантически достоверная тройка ID/edition на том же раннем original Track/Album/source и реальный момент original prepare, затем approved CELIKOM grant к одному native player**. Unknown → оригинал.

---

# CURRENT 20.11.2026 — исправлен реальный failed/unknown original-setter lifecycle, JVM зелёный

**Последний код:** [bdf7c577](https://github.com/manufact-test/nomusic/commit/bdf7c57749faa758c2d1c786a12c3c6fbd650adf). В действующем `NativeRendererStreamEvidence` добавлен `EarlyOriginalSourceObserver.rejected(generation)` для **всех попыток** оригинального native Player setter, которые завершаются до `finish`: неизвестный/NULL source, отсутствие оригинального creator Track/Album, исключение получения pair, nested/overlap. `NativeEarlySourceLifecycleBridge.rejected` теперь немедленно отменяет через canonical `NativeReplacementLifecycle.cancelPendingNativeSelection` и повышает поколение, чтобы неизвестный source не оставил пригодный pending token. Неизменённый original `chain.proceed()` выполняется как и раньше, новое поведение касается только CELIKOM gate. Новые JVM тесты: nested original setter и NULL source не могут оставлять старую заявку; [CI #44700743780 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44700743780). Новый ARM13 [#44700743688](https://github.com/manufact-test/nomusic/actions/runs/44700743688), [#44700743677](https://github.com/manufact-test/nomusic/actions/runs/44700743677) запущены, конечный статус проверить.

**Остальное:** previous code [b736c6c1](https://github.com/manufact-test/nomusic/commit/b736c6c1bb36f6deb10a7a417107122424213a40) действительно подключил existing `NativeReplacementLifecycle` к original Player source setter, [350d0a07](https://github.com/manufact-test/nomusic/commit/350d0a071ab5870b676cb3328d5dc8c123fbeafe) отменяет pending при исключении оригинала. Все guards ORIGINAL-only до подлинного semantic `trackId+albumId+editionId` + current generation + verified pre-prepare decoder/source + approved grant. Не менять архитектуру, NAV40/NAV45/Test.50/Windows/подписанный оригинал, не выпускай диагностический APK ради счётчиков. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Нужно продолжать **к настоящему source substitution**, а не опять год исследовать.

---

# CURRENT 20.11.2026 — A1 original early setter реально подключён к NativeReplacementLifecycle

**Продолжение к работающей версии без смены архитектуры.** Runtime-код [b736c6c1](https://github.com/manufact-test/nomusic/commit/b736c6c1bb36f6deb10a7a417107122424213a40) теперь **подключает** существующий canonical pure-Java `NativeReplacementLifecycle` в исходном in-process `androidx.media3.exoplayer.d.e(Sl6,long)` source setter через `NativeEarlySourceLifecycleBridge`. При *каждой* попытке оригинального setter старое поколение сбрасывается (включая неизвестный source, повтор, Next, вложенный вызов), если creator Track/Album/source совпадают, запоминается только weak original reference identity, и только после успешного original `chain.proceed()` подтверждается его завершение. Оригинальный метод не изменён, вторых плееров нет. Gradle собирает **канонические** `NativeReplacementLifecycle/PrePrepare/Grant/SourceGate/IdentityGate` напрямую из существующего native-hooklab без копирования/форка. Функция по умолчанию OFF, замену всё ещё нельзя включить, пока semantic IDs/edition/real decoder pre-prepare НЕ доказаны.

Fail-closed фикс [350d0a07](https://github.com/manufact-test/nomusic/commit/350d0a071ab5870b676cb3328d5dc8c123fbeafe): `cancelPendingNativeSelection` гасит как unresolved, так и уже validated-pending grant, если **оригинальный** setter бросил исключение. После issued source отменить/переделать звук нельзя. JVM [renderer #44700000244](https://github.com/manufact-test/nomusic/actions/runs/44700000244) SUCCESS, [native identity #44700000317](https://github.com/manufact-test/nomusic/actions/runs/44700000317) SUCCESS; Android13 ARM пара [#44700000212](https://github.com/manufact-test/nomusic/actions/runs/44700000212), [#44700000240](https://github.com/manufact-test/nomusic/actions/runs/44700000240) запущена — проверить итог, не заявлять success заранее.

**Статус неизменен:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Реальный in-process gate wiring есть, но **никакого аудио-mapping** ещё нет. Следующее действие только по прямой дороге: удостоверить `trackId+albumId+editionId` на исходных early Track/Album и актуальное native поколение на том же **доказанном pre-prepare decoder** источнике; затем безопасно разрешить `offerValidated/atNativePrepare` по approved CELIKOM grant. Нет proof → ORIGINAL. Не возобновлять широкие DEX/MediaItem сканы, не выпускать бесполезный APK. NAV40, NAV45, Android Test.50, Windows и оригинал подписанного Яндекса не трогать.

---

# CURRENT 20.11.2026 — source-bound generation + pending-to-certify lifecycle, no decorative APK

**Code-only continuation in sole branch:** [50f6d6c2](https://github.com/manufact-test/nomusic/commit/50f6d6c267e8250cff1911195cd663d4957bacf8) extends the already verified ORIGINAL pre-source-setter Track+Album seam: both creator-at-birth cases (Flow before and after tCa) now work, a successful original setter retains only **weak** exact Track+Album+source identity for its own monotonic original selection generation; failed/nested setter, Next/replay, wrong source/Album or changed generation erase/deny. **Not selected decoder identity**. [JVM #44697491917 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44697491917); [clone-only ARM13 #44697491867 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44697491867). Publisher-first [#44697491883](https://github.com/manufact-test/nomusic/actions/runs/44697491883) — check final status.

**Existing source gate lifecycle hardened**, no architecture replacement: [355af97a](https://github.com/manufact-test/nomusic/commit/355af97aeee6819c0505eda7306a6b25ae243acf) + [5cabef07](https://github.com/manufact-test/nomusic/commit/5cabef071afa6e474eba3883b39ab8331ec232d0). `NativeReplacementLifecycle.beginUnresolvedNativeSelection` reserves a real original generation **before** IDs can be certified; `certifyNativeIdentity` can fill *only that same unprepared and enabled generation* when verified semantic triple arrives within original 850ms budget. Unknown original prepare seals ORIGINAL permanently; later FileInfo/grant may not convert a playing track. Duplicate/Next/Stop/timeout/invalid ID fail closed. [isolated JVM #44698320436 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44698320436); clone ARM13 [#44698320481](https://github.com/manufact-test/nomusic/actions/runs/44698320481) — check final status.

**Still blocked:** `trackId+albumId+editionId` semantic proof from that exact original creator/source, real pre-prepare binding to the same decoder and actual single-player source selection/byte routing. **No hook consumer has been installed and no audio swap attempted.** `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`; NAV40/NAV45/Test.50/Windows and signed original unchanged. Do NOT ship NAV46 on these tests; next task is connecting exact semantic triple + original pre-prepare descriptor to this existing lifecycle, only then approved alternate source, unknown -> original. No more MediaItem/shotgun DEX/diagnostic phone APK.

---

# CURRENT 20.11.2026 — early original Player source-setter binding (CODE, no APK)

**Реальное runtime-изменение:** [ANDROID-A1-EARLY-CREATOR-TRACK-ALBUM-ORIGINAL-SOURCE-SETTER-20261120.md](ANDROID-A1-EARLY-CREATOR-TRACK-ALBUM-ORIGINAL-SOURCE-SETTER-20261120.md). Код [55c73a2e](https://github.com/manufact-test/nomusic/commit/55c73a2e2eeed9c5050302c2bd4e086a94610033): уникальный исходный creator Track+Album теперь fail-closed разрешается **перед оригинальным** `androidx.media3.exoplayer.d.e(Sl6,long)` setter, не ожидая позднего Flow/renderer. Вводится одно pending поколение setter на вызов с отменой при вложении/смене поколения/исключении; исторический PlayerSource связывается **только после успешного оригинального вызова**, а не до него. Оригинальный setter вызывается один раз, без изменений аргументов. Consumer НЕ установлен и ID не читаются. [JVM #44694252227 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44694252227), [publisher-first ARM13 #44694252239 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44694252239), [clone-alone ARM13 #44694252308 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44694252308); проверено 20.11.2026.

**НЕ доказывает** `trackId+albumId+editionId`, выбранную редакцию, текущий decoder pre-prepare или право на alternate. Источник остаётся ORIGINAL. `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. **NAV46 не выпускать** только ради этого plumbing; NAV40/NAV45/Test.50/Windows untouched. Следующая точка: доказанное совпадение того же original TrackWrapper/descriptor/source с семантическими ID и актуальным native period generation **до реального source prepare**. Не повторять широкие DEX/MediaItem пробы.

---

# CURRENT 19.11.2026 — завершающий targeted `trackId` CFG заход, передача следующему чату

**Один дополнительный заход закончен.** Канонический handoff: [HANDOFF-A1-AFTER-TRACKID-CFG-20261119.md](HANDOFF-A1-AFTER-TRACKID-CFG-20261119.md); точный отчёт: [ANDROID-A1-TRACKID-BRANCH-CFG-ALL-PATH-NO-GO-20261119.md](ANDROID-A1-TRACKID-BRANCH-CFG-ALL-PATH-NO-GO-20261119.md).

**Изменено только read-only static research:** настоящий 2025 original `FileInfoApi(trackId)` / `DownloadInfoApi(trackId)` и `LGp0` String field receiver проверены через точный bounded DEX all-branch must-alias CFG, включая packed/sparse switch. **10 synthetic CFG unit tests PASS**, signed original issuer 16/16 splits / 6 DEX: [CI #44578410987 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44578410987). Важно: `exact_creator_branch_aware_receiver_cfg_verdicts=[CFG_ORIGINAL_TRACK_ALIAS_NOT_PROVEN]`, `same_formal_track_source_to_trackid_api_candidate_count=0`. Это уже **не** просто unsupported switch: код способен пройти switch, но исходное String-поле не удостоверено как из *того же* формального Track по всем путям. Невозможно повышать до настоящего `trackId` активной редакции/источника. Не означает, что trackId не существует.

**Актуальная Android реализация из предыдущего захода сохраняется**: точные исходные `Track`+`Album`+`source` в same-callback текущего `SLOT_B` renderer, [JVM #44574303898 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44574303898), [ARM13 #44572917325 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44572917325). Но renderer callback слишком поздний для оригинального source pre-prepare. Следующему чату нужна **ранняя** доказанная native original source/creator identity+edition+generation pre-prepare точка, а не ещё одна серия MediaItem/DTO/String identity сканов. Существующие `NativeReplacementLifecycle` / gates — только fail-closed модель, НЕ подключенная к аудио.

`CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. Нового NAV46 APK/ZIP нет: Android runtime в этом заходе не изменяли, оригинальное воспроизведение не меняли. Подписанные NAV40 `34cb32c8`, NAV45 `c95c0bf2`, Test.50, Windows и original Yandex неизменны. **Единственная ветка:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; проверить её текущий HEAD при продолжении.

---

# CURRENT 19.11.2026 — post-NAV45 actual original Track/Album callback at live native source, JVM + ARM13 green

**Сделано в коде**, не диагностический отчёт: `StageBAudioEvidence.exactOriginalTrackAlbumForWrapper` возвращает только точные исходные Java Track+Album из creator-owned wrapper/Flow (согласованность и отсутствующие конфликты), а `NativeRendererStreamEvidence` теперь способен доставлять эту пару **в том же** original renderer -4 / PlaybackInfo.PeriodID UID+2 ints / SLOT_B / точно того же исходного `LiLb` source callback. Провайдер подключен в `ExitCallsiteWitness`. Нет ID values, подмены/второго плеера/аудио-мутаций, consumer пока null. Специальные JVM тесты исключают изменённое поколение повторного трека, source rebinding, Album conflict, EOS, другую очередь. [JVM #44574303898 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44574303898), [publisher-first ARM13 #44572917325 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44572917325), [clone-alone #44572917099 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44572917099). Полный точный отчёт: [ANDROID-A1-POST-NAV45-LIVE-TRACK-ALBUM-SOURCE-CALLBACK-20261119.md](ANDROID-A1-POST-NAV45-LIVE-TRACK-ALBUM-SOURCE-CALLBACK-20261119.md).

**Исходный semantically annotated `FileInfoApi(trackId)` найден и в том же подписанном оригинале есть прямой `LGp0` creator caller**, но у String-field receiver был branch; ссылку на **тот же** Track **не доказали**. [Exact signed CI #44574897138 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44574897138), category `TRACK_RECEIVER_BRANCH_UNPROVEN`; `albumId`/`editionId` и source generation не установлены. Этот маршрут не разрешает аудиоподмену. **Не застревать в ещё одной серии статических негативных сканов, не угадывать идентификаторы**.

**Статус:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`; никакого NAV46 APK не создано, поскольку ещё нет доказанного source-before-prepare track+album+edition bridge. Последний подписанный NAV45 исходник `c95c0bf2`, неприкосновенная NAV40 `34cb32c8`, Test.50 и Windows не тронуты. Только единственная ветка `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

---

# CURRENT 19.11.2026 — signed 2025 FileInfo API TrackID route: no proven active Track/source/edition

**Новая узкая исходная проверка закончена:** [ANDROID-A1-NAV45-SIGNED-FILEINFO-TRACKID-API-ORIGIN-20261119.md](ANDROID-A1-NAV45-SIGNED-FILEINFO-TRACKID-API-ORIGIN-20261119.md). [CI #44569443742 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44569443742). В настоящем signed Yandex 2025 FileInfoApi и DownloadInfoApi имеют `trackId`-аннотированный параметр (по 1 direct callsite), но его источник в API — отдельное String поле; один точный field writer получает параметр String; у него 21 inbound caller, включая структурные Track.String candidates, **0** доказанных same-formal-Track receiver paths. Поэтому semantic `trackId` API подтверждён, его принадлежность нынешнему Track/active SLOT_B/source и редакции **нет**. `Album.if()` String не удостоверен как albumId, `Track.super()` String не удостоверен как trackId. Нельзя выдавать за рабочую подмену.

**Никакого нового owner APK нет:** это были две CI-only static Python проверки + docs, исходный звук/архитектура/подписанные NAV40/NAV45/Test.50/Windows не изменялись. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Не запускать ещё одну серию MediaItem, Album String или широких DEX-сканов ради искусственного прогресса. Разрешён только same-original-source+edition+generation доказанный шаг.

---

# CURRENT 19.11.2026 — после NAV45: подписанный семантический Track/Album identity NO-GO

**Точечный источник проверен, приложение НЕ пересобирали.** Оригинальный publisher-signed Yandex 2025.10.4 #120.1gpr (16 verified splits, six DEX), exact Track `ru.yandex.music.data.audio.o` (51 instance fields) и Album (37 fields) проверены по **четырём явно разрешённым сериализационным аннотациям** на instance fields и ctor parameters. Не найдено доказанных `trackId`, `albumId`, `editionId` через эти аннотации. [Статический CI #44562209490 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44562209490); отчёт: [ANDROID-A1-NAV45-SIGNED-TRACK-ALBUM-ANNOTATION-NO-GO-20261119.md](ANDROID-A1-NAV45-SIGNED-TRACK-ALBUM-ANNOTATION-NO-GO-20261119.md). Отсутствие этих аннотаций **не означает** отсутствия ID в оригинальной модели вообще. При этом копируемый `long` и `Ldjv.a()` не аттестованы как ID в актуальном original source.

**Результат:** `NO_GO_EXACT_ID_AND_EDITION_NOT_SEMANTICALLY_ATTESTED`. Запрет на выпуск очередной пустой диагностики и включение подмены остаётся: `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. Не возобновлять бесполезные MediaItem-пробы. Оригинальный player, Play/Pause/Seek/Next/MyWave не изменены. Работали только 2 новых CI-only файла и документация; NAV40 `34cb32c8`, owner-signed NAV45 `c95c0bf2`, Test.50, Windows и APK/ZIP не тронуты. Единственная ветка `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

---

# 19.11.2026 — передача новому чату после NAV45 (сохранено)

**Каноническая короткая передача:** [HANDOFF-A1-NAV45-TO-NEXT-CHAT-20261119.md](HANDOFF-A1-NAV45-TO-NEXT-CHAT-20261119.md). Последний owner TXT `CELIKOM-A1-Diagnostics-1795102532842.txt`: NAV45 `CURRENT_MEDIAITEM_LOGICAL_ID=REGISTERED`, но `MATCH=NONE`, `DIFFERENT=NONE`, `BLANK=FEW`; больше **не искать ID через MediaItem**. Прежняя исходная связка TrackWrapper/late Flow ↔ original source/PeriodID `MANY`, часть `NO_LINK=MANY`; подмена `NOT_CONNECTED`. Следующая работа: доказанный Track ID + album/edition + playback generation в **том же** исходном источнике; не выпускать очередной read-only APK без оправданной новой точки. Signed NAV40, NAV43/44/45 не менять.

---

# CURRENT — NAV45 OWNER PHONE CHECKED; MediaItem STRING ID BLANK (19 November 2026)

**New owner TXT**: `CELIKOM-A1-Diagnostics-1795102532842.txt` (2066 lines). Actual `NAV_V45_CURRENT_MEDIAITEM_LOGICAL_ID_READONLY` summary: hook `CURRENT_MEDIAITEM_LOGICAL_ID=REGISTERED`; `PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_MATCH=NONE`, `DIFFERENT=NONE`, `BLANK=FEW`, `UNAVAILABLE=NONE`. The source/current Window MediaItem objects are distinct (`...SAME_REF=NONE`, `...DIFFERENT=FEW`), but **at least one immutable String is blank** for all classified probes. It does **not** prove different songs and is NOT a usable identity gate. Earlier NAV44 process sections in same file are not the NAV45 summary.

NAV43 structural proof remains `PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS=MANY`, `...LATE_FLOW_SAME_CALLBACK=MANY`, `...NO_LINK=MANY`, `...SLOT_CHANGED=NONE`, active SLOT_B and original TrackWrapper source links MANY. Occasional missing Flow links mean no universal per-read proof. `METRICA_EXCEPTION_SUMMARY/MUSIC_APP=FEW` is an unassigned error category, not proof of an observer crash. `BUFFER_EOS_ACCESS=NO_HOOK`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`.

**Stop chasing MediaItem id/reference.** Instead, use already owner-confirmed original `ru.yandex.music.data.audio.o` Track from creator-owned `tCa` TrackWrapper and its Flow/active original source, and seek *publisher-signed* field/provenance for exact Track ID + edition + generation. Existing `StageBAudioEvidence.classifyNativeTrackAlbumForWrapper` returns structural classification, not actual ID. Track copy method's `long` parameter is **NOT yet proven as track ID**, and a separate download API `Ldjv.a()` string cannot be assumed equivalent. Do not invent identity or connect audio/ship NAV46 without a verified narrow source target. [Complete NAV45 phone report](ANDROID-A1-NAV45-OWNER-PHONE-BLANK-MEDIAITEM-ID-20261119.md).

**No source, APK or tests changed after signed NAV45**. Signed release `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8` / Android13 [#44552661805 27/27 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44552661805); NAV45 Library upload previously blocked by quota, direct downloads offered in prior chat. NAV40 code/backup and owner signed NAV43/44/45 untouched.

---

# LATEST — NAV45 owner-signed Android13 27/27 SUCCESS; APK/ZIP verified; Library FULL, upload blocked (19 November 2026)

**Signed release source commit:** `c95c0bf27157c9f3ff8bd4aa13f6ed6eabe222f8`. [ARM13 owner-signed release CI #44552661805 SUCCESS (27/27)](https://github.com/manufact-test/nomusic/actions/runs/44552661805); private artifact id **14545670017** `CELIKOM-A1-NAV45-Nonempty-MediaItem-ID-20261119`. Static signed field gate [#44551508431 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44551508431), JVM exact model [#44552192680 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44552192680).

**Exactly verified release files (generated owner artifacts, NOT uploaded to personal Library due quota):**
- APK `CELIKOM-A1-NAV45-Nonempty-MediaItem-ID-ReadOnly-20261119.apk` — **71,495,660 bytes**; SHA256 **`8254721d6ac19221aecff389615b8fcf08e62cb29a4c5843096be1588aec0c27`**.
- ZIP `CELIKOM-A1-NAV45-Nonempty-MediaItem-ID-20261119.zip` — **51,626,477 bytes**; SHA256 **`07b6a2e84568ff59181bf06217b430e47ebacb08ef77313792f9d2055d3ba9d9`**. Contains exactly that APK + `README-RU.txt`; ZIP CRC, APK CRC and embedded LSPatch module CRC verified. Nested `assets/lspatch/modules/pro.celikom.a1exitwitness.apk` contains correct NAV45 marker, `CURRENT_MEDIAITEM_LOGICAL_ID`, `ITEM_LOGICAL_ID` and nonempty-ID match/different counters.
- **Library upload attempted for BOTH** under `/CELIKOM/Android/Native/`, both returned: **"You've reached your Library storage limit. Delete files to free up space before saving more."** No Library success; do NOT claim upload success. User needs to clear approximately 124 MB; do not delete any older signed APK/ZIP on user's behalf. Direct sandbox files existed in this conversation: `/mnt/data/CELIKOM-A1-NAV45-Nonempty-MediaItem-ID-ReadOnly-20261119.apk`, `/mnt/data/CELIKOM-A1-NAV45-Nonempty-MediaItem-ID-20261119.zip`. If next chat cannot see those files, re-download from GitHub artifact **14545670017** (retention 7 days), verify hashes, then upload when space free. Never invent sandbox link in next chat.

**Owner phone NAV45 TXT STILL PENDING.** Install over NAV44, no uninstall/data reset; 2–5 songs, MyWave, Next/seek/pause/repeat, export TXT. Key `PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_{MATCH,DIFFERENT,BLANK,UNAVAILABLE}` alongside original NAV44 `PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_*`, NAV43 late-Flow same callback and SLOT_B guard. Even ID MATCH is only logical item candidate, NOT track edition/PCM/replacement.

**Hard state:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`; `BUFFER_EOS_ACCESS=NO_HOOK`. Signed NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391`, its backup, signed NAV43/44 packages unchanged. Single branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Full report [NAV45](ANDROID-A1-NAV45-NONEMPTY-MEDIAITEM-ID-READONLY-20261119.md). No NAV46 until phone TXT and exact necessity.

---

# LATEST — NAV45 signed-original immutable MediaItem ID candidate; owner APK export requested (19.11.2026)

**Owner NAV44 TXT received and analyzed:** `CELIKOM-A1-Diagnostics-1795100702186.txt`. Exact `NAV_V44_CURRENT_MEDIAITEM_SOURCE_READONLY` marker + hook `CURRENT_MEDIAITEM_SOURCE=REGISTERED`. `PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_SAME_REF=NONE`, `DIFFERENT=FEW`, `UNAVAILABLE=NONE`, `SLOT_CHANGED=NONE`; `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK=MANY`, `...NO_LINK=MANY`, `PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS=MANY`. A distinct Java MediaItem reference is **not** proof of different songs, TrackIDs or editions; never alter original playback just to force Java reference identity.

**NAV45 narrow next step:** original signed 2025 MediaItem `LOf6;` has **exactly one immutable final instance String field** (publisher-signed private CI [#44551508431 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44551508431)). Compare only two nonempty String field values from NAV44-qualified same-read selected Window MediaItem and actual source MediaItem; field contents are not stored or logged. Distinct refs and same logical ID now classify `PLAYER_MEDIAITEM_NONEMPTY_ID_SAME_CALLBACK_MATCH`. `DIFFERENT`, `BLANK`, `UNAVAILABLE` remain fail-closed; old SLOT_B/Period/Flow gates stay in place. [JVM new ref/id tests #44552192680 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44552192680). See [NAV45 target report](ANDROID-A1-NAV45-NONEMPTY-MEDIAITEM-ID-READONLY-20261119.md).

**Status:** owner-signed NAV45 APK + ZIP are **not yet certified** until final ARM13 release CI; expected artifact names `CELIKOM-A1-NAV45-Nonempty-MediaItem-ID-ReadOnly-20261119.apk`, `CELIKOM-A1-NAV45-Nonempty-MediaItem-ID-20261119.zip`. Same sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Signed NAV40, signed NAV43, signed NAV44 remain immutable. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`, `BUFFER_EOS_ACCESS=NO_HOOK`; no audible PCM or selected edition proof.

---

# LATEST — NAV44 signed ARM13 27/27 SUCCESS; APK + ZIP verified and in Library (19 Nov 2026)

**Signed final release:** source/export commit `e7b7dc1d0272cbf354876ff23d347917e815560a`. [Owner-signed Android13 ARM run #44547529479 — SUCCESS, all 27/27 steps](https://github.com/manufact-test/nomusic/actions/runs/44547529479); [preceding ARM preflight #44547059680 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44547059680); [JVM #44546865739 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44546865739); [exact publisher-signed private field compiler CI #44545043886 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44545043886).

**Both files uploaded SUCCESS to ChatGPT Library `/CELIKOM/Android/Native/` and locally byte/hash inspected:**
- `CELIKOM-A1-NAV44-Current-MediaItem-Source-ReadOnly-20261119.apk` — **71,495,660 bytes**, SHA-256 `9d24147caa5f67a4251026b3d5bbfad814e3a090c4166e4e4a2d34e33990ab5d`.
- `CELIKOM-A1-NAV44-Current-MediaItem-Source-20261119.zip` — **51,625,612 bytes**, SHA-256 `196021eeb6a2f5ccaafd3571bcff99e1d8bf7e33afe2d473325dbb89a7c9caa3`; ZIP contains only the expected APK + README-RU.txt.
- Independently inspected embedded `assets/lspatch/modules/pro.celikom.a1exitwitness.apk` inside final signed owner APK; private `PrivateNativeCurrentMediaItemTarget` and new diagnostic marker/counters present in embedded module DEX. No stale NAV43 module accepted.

**NEXT:** owner installs NAV44 **over NAV43**, no uninstall/data reset, 2–5 tracks, MyWave, Next/seek/pause/repeat, sends one TXT. Check new exact `PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_{SAME_REF,DIFFERENT,UNAVAILABLE,SLOT_CHANGED}` counters together with NAV43 same-callback positives. Missing or mismatched MediaItem is an explicit fail-closed result; even SAME_REF is structural and not selected exact Track ID/edition/generation or confirmed PCM.

**Hard product status unchanged:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`, `BUFFER_EOS_ACCESS=NO_HOOK`. No NAV45 until NAV44 owner TXT and a justified next gate; protect signed NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391` and backup, old binaries untouched. [Full NAV44 report](ANDROID-A1-NAV44-CURRENT-MEDIAITEM-SOURCE-READONLY-20261119.md).

---

# LATEST — NAV44 selected original Timeline↔source MediaItem candidate: signed static + JVM PASS, ARM owner APK PENDING (19 November 2026)

**Do not restart; only one branch.** NAV43 owner-phone TXT `CELIKOM-A1-Diagnostics-1795097798424.txt` confirmed `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK=MANY` with `NO_LINK=NONE` and `SLOT_CHANGED=NONE`. This joined active current PlaybackInfo PeriodID, live SLOT_B, and uniquely scoped original source→TrackWrapper→late SAME Flow Album in the same original -4 callback; still structural only.

**NAV44 code candidate:** current-period UID→original Timeline Period→Window MediaItem `==` current original source LiLb MediaItem, only after NAV43's same-callback guard and after live SLOT_B+PeriodID rechecks, plus source-after-read recheck; enum-only `PLAYER_MEDIAITEM_SOURCE_SAME_CALLBACK_{SAME_REF,DIFFERENT,UNAVAILABLE,SLOT_CHANGED}`. The signed private target compiler checks exact original 2025 field PCs and pure LiLb.for source getter. [Signed issuer preflight CI #44545043886 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44545043886); [JVM owner model CI #44546865739 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44546865739). Android ARM source/build/signature/export **not yet accepted** until full green and verified Library files. See [NAV44 exact report](ANDROID-A1-NAV44-CURRENT-MEDIAITEM-SOURCE-READONLY-20261119.md).

**No inference:** equal MediaItem Java references do NOT prove selected original Track ID/edition, queue generation, PCM or replacement; `BUFFER_EOS_ACCESS=NO_HOOK`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Signed NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391` and protected backup are unchanged. No NAV45 without NAV44 phone TXT and exact next necessity.

---

# LATEST — NAV43 owner-phone same-callback PASS, selected Track/edition remains UNPROVEN (19 November 2026)

**Actual owner TXT** `CELIKOM-A1-Diagnostics-1795097798424.txt` (122007 bytes, 1685 lines) contains confirmed active `NAV_V43_PERIOD_FLOW_UID_INTS_SAME_CALLBACK_READONLY`. **PASS:** `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK=MANY`, `...NO_LINK=NONE`, `...SLOT_CHANGED=NONE`; `PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS=MANY`; live type1/state2/-4 SLOT_B and late tCa Flow Album SAME are MANY. This upgrades NAV42's separate aggregate structural witnesses to one sampled callback with final SLOT_B recheck; it **does not identify the selected original Track ID/edition**, distinct replay generation, or audible PCM. `BUFFER_EOS_ACCESS=NO_HOOK`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`.

**Next ONLY:** use the already confirmed NAV43 source/period callback, seek a **specific original, publisher-signed read-only current-selected Track+edition identity at that same active read**, fail closed for Next, prefetch, stale and repeated composition. No blanket static study, no NAV44 until an exact independent provenance route is verified, no audio mutation or new Player. **NAV40 and all signed binaries untouched.** [Detailed NAV43 real-phone report](ANDROID-A1-NAV43-OWNER-PHONE-SAME-CALLBACK-20261119.md). Code and release references below remain applicable.

---

# LATEST — NAV43 signed phone diagnostic READY in Library (19 November 2026)

**Owner NAV42 diagnostic `CELIKOM-A1-Diagnostics-1795096092342.txt`:** `PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS=MANY`, `DIFFERENT=NONE`, `UNAVAILABLE=NONE`, and exact live `SLOT_B`, scoped tCa source, late SAME Flow Album each MANY. Original EOS accessor still NO_HOOK. All only structural, no selected edition/PCM and no audio replacement.

**NAV43 exact same-callback classifier:** code `24a6a2dfcce86e7514fccd8253bc4eae440de5d4`; read-only joint witness checks current Player PeriodID versus live SLOT_B and unique exact original scoped source → tCa wrapper → SAME late Flow Album at a single -4 callback, then rechecks SLOT_B; separate no-link/slot-changed counters. Signed release source commit `3cc409d9e7879abf91783109fd28f66586881bdc`; [JVM #44538897528 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44538897528), [final owner-signed Android13 ARM CI #44538897470 SUCCESS (27 steps)](https://github.com/manufact-test/nomusic/actions/runs/44538897470).

**Verified released artifact in ChatGPT Library `/CELIKOM/Android/Native/` (both UPLOAD SUCCEEDED):**
- `CELIKOM-A1-NAV43-Period-Flow-SameCallback-ReadOnly-20261119.apk` 71,491,564 bytes SHA256 `5bda3ddea77e94f1bc6f87e8224c7838a0f8ae7dd05d0c466866e8f321b758e6`.
- `CELIKOM-A1-NAV43-Period-Flow-SameCallback-20261119.zip` 51,621,360 bytes SHA256 `04e1a60fd4ce93e3576965e281f0acda63e8cd69999f9c88f1929fe5850a4350`, contains only APK + README-RU.txt.

**NEXT:** user installs NAV43 *over NAV42*, no delete/data wipe. Play 2–5 tracks and MyWave; Next/seek/pause/repeat; send TXT. Inspect `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK`, `...NO_LINK`, `...SLOT_CHANGED`. Until then `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Do not touch signed NAV40 code `34cb32c88a11743a64c9f4814fa71957223a1391` or backups; no broad static scans, no NAV44 without new phone proof.

---

# CURRENT — NAV42 owner phone proof → NAV43 same-callback source/period witness (19 Nov 2026)

**Phone TXT:** `CELIKOM-A1-Diagnostics-1795096092342.txt` (118623 bytes, 1637 lines) confirms `NAV_V42_PLAYER_PERIOD_SLOTB_EOS_UNKNOWN_READONLY` ACTIVE. `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MINUS4=MANY`, original `PLAYER_PERIOD_EOS_UNKNOWN_UID_INTS=MANY`, `...SAME_REF=NONE`, `...UID_ONLY=NONE`, `...DIFFERENT=NONE`, `...UNAVAILABLE=NONE`. Original `BUFFER_EOS_ACCESS=NO_HOOK`, so the NON-EOS category remains NONE and no physical PCM/audible proof is allowed. In that run `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY`, `LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME=MANY`, neither scoped source conflict nor late-flow conflict observed. `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY` remains.

**Code progress:** source `24a6a2dfcce86e7514fccd8253bc4eae440de5d4`, [JVM #44538226134 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44538226134): strict -4/type1/state2/SLOT_B/EOS-unknown sampled callback now requires a **same-callback** increment of current Player PeriodID match (UID+2 ints or exact reference) **AND** uniquely scoped original source → same tCa wrapper + late SAME Flow Album, with final live SLOT_B reread. Three isolated counters: `PLAYER_PERIOD_EOS_UNKNOWN_LATE_FLOW_SAME_CALLBACK`, `...NO_LINK`, `...SLOT_CHANGED`; tests reject EOS true, wrong current ID, absent flow, wrong source, changed slot inside source classification. No new hook and no sound path.

**Release candidate NAV43:** commit `3cc409d9e7879abf91783109fd28f66586881bdc` requests [JVM #44538897528](https://github.com/manufact-test/nomusic/actions/runs/44538897528) and owner-signed [Android13 export #44538897470](https://github.com/manufact-test/nomusic/actions/runs/44538897470). **CI and APK not yet accepted until SUCCESS.** Intended APK `CELIKOM-A1-NAV43-Period-Flow-SameCallback-ReadOnly-20261119.apk` and ZIP `CELIKOM-A1-NAV43-Period-Flow-SameCallback-20261119.zip`. Previously Library quota full; do not claim files in Library unless confirmed. Final phone test if accepted must check same-callback category and source rejection after Next/Wave/replay. One Android player, no replacement yet, `STRUCTURAL_ONLY`.

**Absolute protection:** NAV40 signed code `34cb32c88a11743a64c9f4814fa71957223a1391` and backup `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119` are untouched; NAV41 and NAV42 release binaries untouched. No fresh static scans, no audio rearchitecture, no installation/data delete.

---

# CURRENT — NAV42 owner-signed diagnostic PASS; Library storage blocked (19 Nov 2026)

**NAV42 final owner-signed CI:** [#44534038483 SUCCESS, 27 steps](https://github.com/manufact-test/nomusic/actions/runs/44534038483), HEAD source/export commit `531c165f7f68ef0cf45de91b8a6d6c9895008158`. Artifact `14535881448` downloaded and verified: ZIP `CELIKOM-A1-NAV42-Period-EosUnknown-SlotB-20261119.zip` (51,620,783 bytes; SHA256 `81471abd2a38cc0d80336694dd0356bdc6089d3f31c2b49149ac64fe5d555cf4`), containing exactly APK `CELIKOM-A1-NAV42-Period-EosUnknown-SlotB-ReadOnly-20261119.apk` (71,491,564 bytes; SHA256 `1b4fac49a5508413cd9d6c05a7fa796e2d1534dfd90f897560fde6430ed707ab`) and `README-RU.txt`.

**Library BLOCKED:** both `files.manage_library` uploads into `/CELIKOM/Android/Native/` failed `library_storage_limit_exceeded`; do not claim the files are in Library or silently delete old builds. Verified files are in current conversation `/mnt/data` sandbox (exact paths above). User needs to free >=~72MB to save APK, preferably >=~124MB for APK+ZIP, or take direct sandbox download.

**Next:** install NAV42 directly over NAV41, without uninstall/data wipe, check 2–5 songs including MyWave, Next/seek/pause/repeat, send CELIKOM TXT. At original `-4` / live SLOT_B with EOS null, check five `PLAYER_PERIOD_EOS_UNKNOWN_*` counters. These are *only structural*, NOT selected song/audio/PCM. NAV40 backup and NAV41 Library artifacts untouched, `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. Do not broaden static study or issue audio-changing APK without proof.

---

# CURRENT — NAV42 targeted response to owner NAV41 EOS blocker (19 Nov 2026)

Owner phone diagnostic `CELIKOM-A1-Diagnostics-1795094518695.txt` confirms `NAV_V41_PLAYER_PERIOD_SLOTB_NON_EOS_READONLY` ACTIVE; `PLAYER_PERIOD_AT_AUDIO_READ=REGISTERED`; `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`, `...MINUS4=MANY`; `BUFFER_EOS_ACCESS=NO_HOOK`. All original 5 period counters NONE solely because unknown EOS was excluded by `Boolean.FALSE.equals(endOfStream)`. The vendor still plays, `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY` and `LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME=MANY`. None of this proves selected edition, `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`.

NAV42 implemented strictly in existing read observer, no new hook, no vendor mutation. Unknown EOS gets five separate structural `PLAYER_PERIOD_EOS_UNKNOWN_{SAME_REF,UID_INTS,UID_ONLY,DIFFERENT,UNAVAILABLE}` at strict type1/state2/-4/SLOT_B original stream read. Proven non-EOS cohorts unchanged; EOS true rejected. PlaybackInfo + holder IDs/UIDs/two ints and queue pointer rechecked, all enum-only. No raw media IDs/content. [JVM #44533352224 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44533352224), [JVM versioned #44533945905 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44533945905). New export request [ARM owner-signed #44534038483](https://github.com/manufact-test/nomusic/actions/runs/44534038483) PENDING until completed, **do not claim release yet**.

NAV42 owner artifact once accepted: `CELIKOM-A1-NAV42-Period-EosUnknown-SlotB-ReadOnly-20261119.apk`, ZIP `CELIKOM-A1-NAV42-Period-EosUnknown-SlotB-20261119.zip`. Existing NAV40 signed backup and NAV41 signed APK remain unchanged. Next: one NAV42 phone test, send TXT with new 5 EOS_UNKNOWN counters; no further broad source scans, no NAV43 without measured evidence. Work in only `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

---

# CURRENT — NAV41 signed diagnostic exported to Library; owner phone run is next (19 Nov 2026)

**Completed:** exact signed original field compiler [CI #44527901915 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44527901915), JVM fail-closed witness [CI #44529331046 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44529331046), owner Android 13 ARM test [CI #44529331360 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44529331360) and **final owner-signed NAV41 release [CI #44529576455 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44529576455)**. Export commit `c8e73015493c50c05fa97aaf9febdf802c48c864`, final code `74df48624f79051276924326a8bd77dc1afe4174`.

**Library files verified in `/CELIKOM/Android/Native/`:**
- `CELIKOM-A1-NAV41-Player-Period-SlotB-NonEos-ReadOnly-20261119.apk` — 71,491,564 bytes, SHA-256 `a584e84cb4462f1865d916d83de9de59f4d7168e09a26d7617b45d5e7b64fc26`.
- `CELIKOM-A1-NAV41-Player-Period-SlotB-NonEos-20261119.zip` — 51,620,702 bytes, SHA-256 `b4ae351e49c37d48eb2157b7224f5427bbc7623ab5d5435bb6a57722c2050ab2`, contains exactly the APK and `README-RU.txt`.

**Safety/goal:** NAV40 signed source `34cb32c88a11743a64c9f4814fa71957223a1391`, backup `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119` and NAV40 Library APK/ZIP are untouched. **`CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`.** NAV41 only observes exact original PlaybackInfo PeriodID against active renderer SLOT_B at type1/state2/-4/non-EOS with repeated field and slot safety checks; no new audio hook or second player. Same ID/UID/index is not selected Track edition, new generation or replacement sound.

**Next and only useful action:** owner installs new NAV41 over NAV40 without deleting data, checks 2–5 tracks, MyWave, Next, pause, seek and same-track replay on HONOR 50 Android 13; sends CELIKOM TXT. Then evaluate those exact NAV41 bins together with NAV40 live TrackWrapper→source and late Flow Album. If no positive live identity, fail closed. No broad static scans, no NAV40 rebuild, no NAV42 without evidence. [Detailed NAV41 handoff](ANDROID-A1-NAV41-PLAYER-PERIOD-SLOTB-NON-EOS-READONLY-20261119.md).

---

# CURRENT — CI recovered, strict issuer signer preserved, stop static expansion (19 Nov 2026)

**Latest verified CI:** [#44523003641 SUCCESS, **35/35**](https://github.com/manufact-test/nomusic/actions/runs/44523003641), green code `e801787ef6a6c13c7d0c1d2e7916da6b622fe460`. Replaced broken Ubuntu apt-based signed-APK tool installation with preinstalled SDK, strictly verified unchanged original 16-split publisher signature using both historical and SDK 0.9 modern `apksigner` text formats. Fail-closed tests reject incorrect certificate, missing APK signer or multiple signers. The separate Source Stamp is **not** accepted as issuer. No original signature gate bypass. Original scan SUCCESS on exact 2025.10.4 #120.1gpr.

**Final narrow negative result:** verified exact original `LrD0.E()LOf6;` getter uses MediaItem-typed `LTva$d.LOf6;` field at getter PC24; the `e.I` Window PC67 reads **different exact field type** `LOf6$f;`, so it cannot be used as selected MediaItem identity. This rejects a false NAV41 basis. It does not establish same Player/Window instance or currently audible period. Prior exact Period→Window and post-UID comparisons remain green.

**Product focus:** do not continue generic static scans, broad UID/J/Timeline re-exploration or extra test count accumulation. The ONLY remaining gate is a verified **same-live-audio-read** selected original Player MediaItem/Track/edition ↔ active SLOT_B renderer period (distinguish stale, prefetched, repeat). Next action should be a minimal targeted plan for a runtime read-only proof using already pinned hooks and getter only if concrete non-invasive test basis is verified, then owner phone feedback and sound replacement. If not verifiable, fail closed; no unjustified NAV41 release. Keep the working native one-player architecture. `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. Signed NAV40 source `34cb32c88a11743a64c9f4814fa71957223a1391`, protected backups, owner APK/ZIP Library unchanged.

---

# CURRENT — original Player/front post-UID ID guards plus exact Period→Window index (19 Nov 2026)

**Latest signed-original STATIC research code:** `bac9dfcca42d23d5bd82ea21bbf5836c6695a8d5`; [CI #44519254855 SUCCESS, **32/32**](https://github.com/manufact-test/nomusic/actions/runs/44519254855). Earlier `14bb3a753661b689c5928acbd05b74b41d57262e` [CI #44518516341 SUCCESS 30/30](https://github.com/manufact-test/nomusic/actions/runs/44518516341). Pinned issuer-signed original Yandex Music 2025.10.4 #120.1gpr, read-only exact DEX; all 16 signed splits checked. No APK/owner-phone/runtime changes.

**New guards:** after `e.break`'s UID comparison branch PC1276, two original `MediaPeriodId` int fields are checked: both sides of the first exact field against `-1` with conditional branches at PC1285/1293, and the second *distinct* exact int field is compared at PC1299. All three branches target PC1303; the second comparison uses original `if-eq` (not `if-ne`). These tests cannot be reduced to UID equality, and the runtime path is not observed. Also now pinned three typed original `Period UID lookup → returned LTva$b → exact I index → LTva Window` calls in `e.I` (PC56→59→60→64, PC101→104→105→109) and `e.z` (PC17→20→21→25). Original Period and Window scratch fields match across both engine methods; the matching period index field was verified across all three paths. [Full exact report](ANDROID-A1-NAV40-SIGNED-FRONT-ID-GUARD-PERIOD-WINDOW-20261119.md).

**Hard NO-GO:** `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`; selected original Player MediaItem/Track/edition at the **same SLOT_B started-audio read** not proven; active/prefetched/stale/repeated-track disambiguation not proven. The Window typed field read at PC67 is not proven to identify selected Track/edition. **No NAV41 build/approval**, original Yandex/Nav40 and protected backups untouched. Owner NAV40 last phone evidence remains `CELIKOM-A1-Diagnostics-1795077619261.txt`.

**NEXT:** inspect exact original Window-to-Player selected MediaItem/Track/edition link and live queue/current-renderer period, not just UID or `LTva$b.I`. Require branch-sensitive and same-read evidence with explicit counterexamples for prefetch, stale and repeated instances; add fail-closed tests or hold structural-only.

---

# CURRENT — NAV40 original SLOT_B → Timeline two-ID transition / exact UID lookups, 27/27 CI SUCCESS (19 Nov 2026)

**Last signed-original static code:** `30bbb059b05f3dcd678c5fdb40c50ad04887c961`; [CI #44516354079 SUCCESS, **27/27**](https://github.com/manufact-test/nomusic/actions/runs/44516354079). Original `e.break()` reads same exact `SLOT_B` field at PC547 and PC664, with direct write site at PC659 between them; no proof write executed or holder changed. Exact old/new candidate PeriodID paths and Timeline inputs reach original `e.I` at PC711 (eight clean no-clobber register spans). Inside `e.I`, ID UID PC52→Timeline `LTva.goto` PC56 and PC99→PC101; in `e.z`, UID PC13→Timeline lookup PC17. All 3 use exact same signed UID field as original PlaybackInfo/front comparator, and typed ID/Timeline parameters. [New canonical detailed handoff](ANDROID-A1-NAV40-SIGNED-TWO-SLOTB-UID-TIMELINE-LOOKUPS-20261119.md).

**Critical NO-GO:** this proves *structural* original period-to-Timeline lookup, **NOT** the selected original Player Track/edition at the same started audio read or active-vs-prefetch/stale period, and NOT a queue-generation/monotonic epoch. `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`; `NAV41_readonly_runtime_admission_proven=false`. **No NAV41 APK**, no vendor modifications. Signed NAV40 `34cb32c88a11743a64c9f4814fa71957223a1391`, both protected backups and personal Library NAV40 APK/ZIP untouched.

**NEXT:** inspect pinned original `e.I`/`e.z` Timeline Period/Window mapping and distinguish currently selected Player media item vs queued/old/prefetched periods; tie exact original Track/edition to **same live SLOT_B started audio read** with branch-sensitive identity and negative tests, not counts/UID equality alone. Work ONLY in `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; don't rebuild NAV40 or release NAV41 without independent signed-source positive proof.

---

# CURRENT — pinned original PlaybackInfo period UID vs Queue SLOT_A front, exact comparator CI GREEN (19 Nov 2026)

**New exact signed-original boundary:** `e.break()V` PCs1253–1276 obtains original Queue `h.if()` front holder `SLOT_A`, reads exact engine `LCD7` ID UID and exact returned holder `Lyh6 → LSl6$b` UID, calls original `Object.equals(v1,v2)`, branches on its result to PC1303. The `LCD7` period-id field matches `d.M0` PC74/96/259 and is DISTINCT from `d.M0` PC138/257. Exact timeline fields and original constructor-anchored holder/period-info fields match. [CI #44513983147 SUCCESS 23/23](https://github.com/manufact-test/nomusic/actions/runs/44513983147), code `549c6d332734327f5395075d431b58b1f7c736ae`; [detailed field/comparison proof](ANDROID-A1-NAV40-SIGNED-PLAYBACKINFO-FRONT-UID-COMPARISON-20261119.md).

**HARD NO-GO remains:** this is `SLOT_A` front UID check, not the current selected Track/edition at the exact started audio read of `SLOT_B`. Runtime equality result, current vs stale/prefetch and queue generation still unproved. Original holder/periodID/J may be retained/reused; don't mistake equality for epoch. NAV40 runtime `34cb32c88a11743a64c9f4814fa71957223a1391` and backups/Library untouched; no NAV41. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`.

**NEXT:** original period ID additional conditional field comparisons PCs1278–1303 and transition `e.I` PC711, then original selected Timeline/Track-vs-SLOT_B same-read link with strict fail-closed negative cases. Do not build without verified selection boundary.

---

# CURRENT — NAV40 old MediaPeriodId.J forwarded into two Queue constructors, static CI GREEN (19 Nov 2026)

**Latest signed-original proof:** eight exact direct callers of the Queue's three ID builders, all pinned; original `h.case` reads the **same exact old `LSl6$b.J` field as the pinned constructor** at PCs 13/30 and passes it via two independent normal-CFG paths to `h.else` (PC25, second J) and `h.goto` (PC40, third J). Those exact inputs in turn reach new ID constructors at PCs 11/103. Dominance, typed input ID receiver and wide-register non-overwrite proven; **no assumption from equal Long values**. Code `6fe28f562089852025793eb5e2e52d7fbd34382e`; [CI #44510497627 SUCCESS, 19/19](https://github.com/manufact-test/nomusic/actions/runs/44510497627). See [NAV40 old ID J reuse normal-CFG report](ANDROID-A1-NAV40-SIGNED-OLD-PERIOD-ID-J-REUSE-CFG-20261119.md).

**This is NOT** proof that another selected song or playback generation occurred. It is evidence that original J may be propagated into other ID constructors, so **J cannot be promoted to a reliable queue epoch**. Original selected Player item/edition at the **same started-audio read** still missing. No runtime changes, no NAV41 APK, no original Player/audio/decoder modifications. Original signed NAV40 runtime `34cb32c88a11743a64c9f4814fa71957223a1391` and signed backup untouched. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`.

**NEXT:** tie exact current renderer `SLOT_B`/MediaPeriod to independent original Player current selected playlist item/timeline window and repeated-track queue identity, fail closed on prefetch/old period/ambiguous snapshots. No synthetic call counter/epoch and no NAV41 before positive signed source+runtime target.

---

# CURRENT — NAV40 signed-original MediaPeriodId ctor J parameter provenance; 15/15 CI GREEN (19 Nov 2026)

**New static proof, no new APK:** enumerated **all 15 direct signed DEX `LSl6$b` constructor call sites** across six DEX and pinned exact method+PC+descriptor+opcode. Four original Exo Queue constructor J arguments proved to come from a typed incoming J parameter through a dominating `move-wide/from16` on all **normal CFG** paths, with wide-register overwrite guards. [CI #44507724826 SUCCESS, 15/15](https://github.com/manufact-test/nomusic/actions/runs/44507724826); last static code commit `b6de25c7f146610e7f25ad7838d11529edca07b2`. Report [NAV40 signed period-ID constructors and J CFG](ANDROID-A1-NAV40-SIGNED-PERIOD-ID-CTOR-J-NORMAL-CFG-20261119.md).

**Hard limit:** a constructor site and a J caller parameter do NOT prove the original Player's selected track/edition or unique active queue generation. Exceptional CFG / indirect creation excluded from positive claims. Runtime NAV40 unchanged `34cb32c88a11743a64c9f4814fa71957223a1391`, protected backup and Library APK/ZIP untouched. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`.

**NEXT:** branch-sensitive source of these exact Queue J caller arguments and independently verified current original Player selected item/window linked to the **same started audio read**. Distinguish repeated same Track, stale holder and prefetch. No synthetic generation counter and **no NAV41 build** without proof.

---

# CURRENT — NAV40 exact signed SLOT_B transitions and mutable period-ID chain, STATIC CI GREEN (19 Nov 2026)

**Sole working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Latest owner-signed **runtime** NAV40 unchanged `34cb32c88a11743a64c9f4814fa71957223a1391`, protected signed backup `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`. Protected pre-static-audit backup `backup/android-a1-nav40-owner-phone-signed-slotb-pre-readonly-census-20261119` @ `86addd96de8af868ca9da41b14540d86b6e8505a`.

**Real NAV40 owner-phone latest (19 Nov):** `CELIKOM-A1-Diagnostics-1795077619261.txt` confirms strict live original source + `LATE_FLOW_ALBUM_SAME=MANY`, negative 3 categories NONE; details below and [NAV40 phone report](ANDROID-A1-NAV40-OWNER-PHONE-LATE-FLOW-SAME-20261119.md). `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`.

**New exact signed ORIGINAL static proof:** added narrow fail-closed direct DEX writer census to existing `ci/exo_queue_slot_role_exact.py`, fixture tests. Across ALL SIX original signed DEX, exact `h.SLOT_B` field has exactly five direct `iput-object` write sites: engine `e.break` PCs **307/659** and queue `h.if` PC **12**, `h.while` PC **25**, `h.for` PC **35**. No other directly referenced DEX writers. New static code SHA `ea2dfb08092a4a468c6b7b8e6c98f74cc363b4d3`, [read-only CI #44494854641 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44494854641). Tests cover missing/extra/duplicate/shifted sites; original XAPK hash + publisher signature pinned by existing CI. No APK built, original Yandex untouched.

**Critical distinction:** direct DEX writer census does **not** exclude reflective/native mutation; `e.break()` has TWO write sites, so method entry/exit ≠ exact field-write epoch. Runtime holder/same historical Track/Album identity still does not prove unique current selected edition or queue generation. Do not invent one or treat the new writer count as a NAV41 green light.

**NEW validated signed-original findings (not NAV41):** the *local original reference provenance* of all five SLOT_B writes is exactly verified: initial shared holder, engine successor, queue front successor, conditional SLOT_A reference, null clearing. The signed current holder points to a **mutable** Lyh6 period-info reference (8 direct DEX writers), Lyh6 retains an LSl6$b period ID (1 direct writer), and that ID retains a long component (1 writer). Moreover the **same original Lxh6 holder can refresh its Lyh6 while preserving the same exact LSl6$b Java reference**. Hence SLOT_B same-reference, Lyh6, period ID or J alone are **not** a proven fresh selected track/edition/generation. Detailed [new static period-info report](ANDROID-A1-NAV40-SIGNED-SLOTB-PERIOD-INFO-REFRESH-20261119.md). All **10/10** scoped fixtures passed on exact signed-original: [CI #44500312807 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44500312807), tested static code SHA `5f057390503fa76f53e55cd2643897f815676349`. Protected static green backup `backup/android-a1-nav40-signed-slotb-period-info-readonly-ci-green-20261119`.

**NEXT:** look only for the actual signed **original Player current playlist item/edition + current MediaPeriod sequence** identity boundary at the SAME NAV40 started-audio read. Do not add an artificial counter/epoch based on method calls, holder or period-id equality. Require independently verified semantic selector before any NAV41 runtime hook. Otherwise STOP at structural-only. No APK build or vendor modification.

**Detailed reports:** [SLOT_B five writer locations](ANDROID-A1-NAV40-SIGNED-SLOTB-DIRECT-WRITES-20261119.md); [local origin and mutable period-ID proof](ANDROID-A1-NAV40-SIGNED-SLOTB-PERIOD-INFO-REFRESH-20261119.md).

---

# CURRENT — NAV40 owner phone CONFIRMED exact late Flow Album SAME; Stage B remains structural-only (19 Nov 2026)

**Sole GitHub working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Latest NAV40 signed **runtime/source unchanged** `34cb32c88a11743a64c9f4814fa71957223a1391`. Protected rollback `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119`. New changes are **documentation only**.

**New real owner-phone TXT:** `CELIKOM-A1-Diagnostics-1795077619261.txt` (122,665 bytes / 1,715 lines / SHA256 `c0a5c30994d3e533db41618b7b1b4c880f6a42cf6bd513449adf28d5f114ad51`). Raw TXT not committed. Active marker `NAV_V40_TCA_CREATOR_LATE_FLOW_LIVE_WRAPPER_READONLY` (old NAV39 lines are retained trimmed history).

- `LIVE_QUEUE_SLOT_B=REGISTERED`, `LIVE_PERIOD_ORIGINAL_SOURCE=REGISTERED`; strict live `SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`, original `Lo96` source resolved MANY, `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY`. Original source OTHER/NO_LINK NONE.
- `TCA_CREATOR_WRAPPER_NOT_FLOW=MANY` **at birth**, same creator Track **later** emitted to Flow MANY with Album observed MANY.
- **NAV40 new result:** `LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME=MANY`; MISSING/DIFFERENT/REFERENCE_LOST all NONE; Track/Album conflicts NONE.
- Legacy `LIVE_PERIOD_SCOPED_WRAPPER_FLOW_ALBUM_NO_LINK=MANY` is compatible with new SAME: the latter classifies an original wrapper born **before** Flow emission, without retroactive birth-time links. Previous NAV39 `LIVE_PERIOD_SCOPED_TCA_BIRTH_TRACK_NOT_IN_FLOW=MANY` becomes NONE under this more specific classifying outcome, **not** because birth-time order changed.
- Active `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/NONE`; separate Push SDK exception and historic MUSIC_APP exceptions do not prove CELIKOM fault. `EXO_IO_FAILURE=NONE`. No invented playback/seek/BT bugs.
- `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. Repeated MANY counters are **not** distinct songs, epochs or selected editions.

**Important distribution correction:** user freed personal Library space; NAV40 **ZIP and owner-signed APK now both uploaded successfully** to `/CELIKOM/Android/Native/`. Personal Library ZIP `libfile_f229652c7cd0819196f625c9c2ea3192`; APK `libfile_75f63719768481918fc14d9b86cff309`. Readback materialization size verified: ZIP 51,618,241 bytes, APK 71,491,564 bytes. Existing release SHA-256/owner certificate/original APK are documented below; no new NAV41 artifacts.

**NEXT minimal technical work, no build on guesses:** inspect only pinned signed-original `ExoPlayer/h.SLOT_B` queue mutation / currently selected item boundary to establish **original player selection+generation** for the exact read-time holder/source. The historical Track/Flow/Album SAME does NOT supply this. Require independently verifiable signed DEX/static semantics and strict fail-closed classification before any NAV41 read-only hook. Don't change player/decoder/audio or claim replacement.

**Detailed new handoff:** [NAV40 owner-phone exact SAME and limits](ANDROID-A1-NAV40-OWNER-PHONE-LATE-FLOW-SAME-20261119.md).

---

# PRIOR CHECKPOINT — NAV40 signed CI-GREEN; Library limit at time of first delivery (19 Nov 2026)

**GitHub:** `manufact-test/nomusic`. Sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
**NAV40 signed source:** `34cb32c88a11743a64c9f4814fa71957223a1391`; **protected signed backup:** `backup/android-a1-nav40-late-flow-live-wrapper-owner-signed-arm13-ci-green-20261119` at that SHA.
**Previous NAV39 pre-change backup:** `backup/android-a1-nav39-owner-phone-live-source-pass-pre-nav40-late-flow-20261119` at `d137f45238e6ca331952058d314eecc89db59f21`; original signed NAV39 rollback unchanged.

**Real NAV39 owner-phone TXT:** `CELIKOM-A1-Diagnostics-1795075324697.txt`, 107,919 bytes / 1,499 lines / SHA256 `3ba0cba6c6d34dd9e46862f89628652ab451af13a6ddf97f662053d5d1164ef8`. Original private phone file not committed; actual active NAV39 marker in export (earlier NAV38 local event history retained).
Real phone confirms exact live original chain `LIVE_QUEUE_SLOT_B=REGISTERED`, `LIVE_PERIOD_ORIGINAL_SOURCE=REGISTERED`, `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`, `LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED=MANY`, `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY`; source OTHER/NO_LINK NONE. Original creator's Track is NOT in retained Flow at tCa birth (MANY), exact SAME Track later Flow (FEW) + Album (FEW). No selected edition/queue-generation evidence; do not enable replacement. `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/FEW`; attribution unproven.

**NAV40 small read-only change:** weak 64 original ctor tCa wrapper/creator Track/birth Album refs and explicit later exact Flow ref. Only classify historical `LIVE_PERIOD_SCOPED_TCA_LATE_FLOW_ALBUM_SAME/MISSING/DIFFERENT/REFERENCE_LOST` under the already strict live original source & setter match. No Track/Album identifiers, URLs, PCM, tokens or media content exported; no original player/audio changes; `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`.

## NAV40 built and verified
- JVM [#44485488863 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44485488863).
- Clone-alone native ARM13 [#44485488606 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44485488606).
- Publisher-first, original+clone owner-signed ARM13 test and artifact [#44485488053 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44485488053); GitHub artifact `14511350924`, exact source SHA `34cb32c88a11743a64c9f4814fa71957223a1391`.
- **Owner-signed APK** `CELIKOM-A1-NAV40-Creator-Late-Flow-Live-Wrapper-ReadOnly-20261119.apk`: 71,491,564 bytes; SHA256 `0914bc4ac4fd498b3e8ff16a0cb64b12372cb0278e1649d0171c913321c53a6e`. Cryptographic RSA-SHA256 v2/v3 verification including full APK content digest passes; signer certificate SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` is SAME as verified NAV39.
- Embedded publisher original `assets/lspatch/origin.apk` SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` matches signed NAV39 exact original bytes, publisher Yandex 2025.10.4 #120.1gpr unchanged.
- Inner owned module SHA256 `9d61809aeb03823ba168840460080ce2e40db2834a1a0b07ef6cd4e87ff3eee2`. Verified DEX contains NAV40 marker, all 4 new categories and exact three private target classes.
- GitHub artifact ZIP `CELIKOM-A1-NAV40-Creator-Late-Flow-Live-Wrapper-20261119.zip`: 51,618,241 bytes, SHA256 `8abee5ec924d1f1920ef27b5a38ca09ff7dbdbbf56b9db0f605d324b80a935cc`, exact GitHub artifact digest. ZIP contains APK and `README-RU.txt` with NAV40 marker.

## Library distribution BLOCKED, not missing APK
- Attempted upload BOTH NAV40 ZIP and APK into personal `/CELIKOM/Android/Native/`; **both returned `library_storage_limit_exceeded`** with `You've reached your Library storage limit. Delete files to free up space before saving more.`
- **Do NOT claim either NAV40 file is in Library.** Do not delete old Library builds without explicit user approval. User was told clearly of quota and given direct current-chat verified `sandbox:/mnt/data/` download links for APK and ZIP as interim option.
- If user frees space or authorizes cleanup, upload preferred NAV40 ZIP first, then APK only if space, read back and hash compare before giving a Library link.

**NEXT:** owner installs NAV40 *over NAV39* with no uninstall/data wipe or change to original publisher Yandex; listens to 2–5 tracks, sends `CELIKOM-A1-Diagnostics-...` TXT. Analyse new late-Flow/strict live source summaries. No NAV41 without actual owner phone evidence. Historic Track/Album identity must never be claimed as currently selected edition/queue generation.

**Detailed report:** [NAV39 owner phone→NAV40](ANDROID-A1-NAV39-OWNER-PHONE-NAV40-LATE-FLOW-LIVE-WRAPPER-20261119.md).

---

# CURRENT — NAV39 signed & delivered in personal Library; owner TXT next (19 Nov 2026)

**GitHub:** `manufact-test/nomusic`; sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
**NAV39 signed source HEAD:** `9e5e462773cdc39ea0c2077dd24e47a3d6b9174e` (NAV39 target packaging fix from `694f0efa1616560d814de60de2906446aad7e3d0` plus exact regression marker assertions).
**NAV39 signed rollback backup:** `backup/android-a1-nav39-live-private-hooks-owner-signed-arm13-ci-green-20261119` @ `9e5e462773cdc39ea0c2077dd24e47a3d6b9174e`.
**NAV38 pre-change backup:** `backup/android-a1-nav38-phone-late-flow-before-nav39-hooks-repair-20261119` @ `fb2463ff7dbe48441bcb96ee89fdf4d8df9d1169`.

## Release and delivery verified
- JVM CI [#44480016827 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44480016827).
- Clone-alone ARM13 CI [#44479658036 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44479658036) for same functional runtime (subsequent source change only regression marker assertion).
- Original-first owner-signed ARM13 CI and APK export [#44480016738 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44480016738). GitHub artifact `14508004348`.
- Signed APK `CELIKOM-A1-NAV39-Creator-Flow-Live-Hooks-ReadOnly-20261119.apk`: 71,491,564 bytes; SHA256 `9c84583b63a5d93b8ae6118874ee7acbd649fa3408748c72b2aa06bd1498f50a`. v2/v3 signatures independently cryptographically verified with content digests and SAME owner signing certificate SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`. Verified inner owned module contains exact NAV39 marker and all 3 private classes (`PrivateNativeQueueSlotTarget`, `PrivateNativeActivePeriodTarget`, `PrivateTcaTrackCreatorTarget`).
- Embedded original origin.apk SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` — exact byte match NAV38 embedded original, 29,803,070 bytes. Original Yandex 2025.10.4 #120.1gpr untouched.
- GitHub ZIP `CELIKOM-A1-NAV39-Creator-Flow-Live-Hooks-20261119.zip`: 51,618,102 bytes; SHA256 `93813ad4060cc74863783ebdf0f779d80773f06ce8198f1f45944ddac61ae53f` equals published artifact SHA256. Contains exact signed APK and NAV39 README-RU.txt.
- **Personal Library**: `/CELIKOM/Android/Native/CELIKOM-A1-NAV39-Creator-Flow-Live-Hooks-20261119.zip`, `libfile_3b1b6b3309dc81919973ea0a5c6ba17b`; direct APK `/CELIKOM/Android/Native/CELIKOM-A1-NAV39-Creator-Flow-Live-Hooks-ReadOnly-20261119.apk`, `libfile_0744232fcb20819185900663cdf07aba`. Both materialized back into container from Library and compared byte-for-byte equal to GitHub-sourced verified files. User links were delivered in chat from verified local files.

## Real owner phone evidence driving this change
- NAV38 actual private owner TXT `CELIKOM-A1-Diagnostics-1795072687109.txt`: 126,763 bytes/1,783 lines, SHA256 `5282b02a1fe32407043fd6b7c3d6c21d496236787342c85212e9047c794467d8`. Do not commit raw TXT.
- `NAV_V38_TCA_CREATOR_FLOW_TIME_ORDER_READONLY` active; `TCA_CREATOR_FLOW_LATER_SAME_TRACK=FEW` and `TCA_CREATOR_FLOW_LATER_ALBUM_OBSERVED=FEW`. Proven: some exact creator-owned Java Track references appear in Flow later, not necessarily a different Track object. This proves historical structural link ONLY.
- NAV38 private build omitted signed-original exact queue/active-period Java target classes: phone `LIVE_QUEUE_SLOT_B=NO_HOOK`, `LIVE_PERIOD_ORIGINAL_SOURCE=NO_HOOK`; NAV39 restores generators, private targets, DEX packaging; actual on-phone REGISTERED/strict live source chain must STILL be verified from NAV39 owner TXT.
- No new source/audio/player changes. `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. Metrica exceptions `MUSIC_APP/NONE`; `EXO_IO_FAILURE=NONE`. No invented seek/pause/BT bugs.

**NEXT:** owner installs exact NAV39 over NAV38 without uninstall, wiping data, or changing original Yandex. Listen to 2–5 tracks and send NAV39 TXT. Confirm marker `NAV_V39_TCA_CREATOR_FLOW_LIVE_RECHECK_READONLY`, `LIVE_QUEUE_SLOT_B=REGISTERED`, `LIVE_PERIOD_ORIGINAL_SOURCE=REGISTERED`, then strict current SLOT_B type1/state2→ original Lo96/Sl6 → same original scoped Player setter source, and independent creator-owned Track→Flow/Album reference evidence. If registration/chain absent, diagnose actual phone data, no blind NAV40. Historical Track/Album equality does not prove current selected edition and queue generation and NEVER authorizes replacement.

**Detailed source:** [NAV38 owner phone → NAV39 protected restoration](ANDROID-A1-NAV38-OWNER-PHONE-NAV39-RESTORE-LIVE-PRIVATE-TARGETS-20261119.md).

---

# CURRENT — NAV38 exact Track/Flow time-order diagnostic; SIGNED AND LIBRARY-VERIFIED; CI GREEN (19 Nov 2026)

**Repository:** `manufact-test/nomusic`. **Sole working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.

**NAV38 source commit:** `72d5c42f1678d7b6839202a52712e5e80bf8a019`.
**NAV37 protected pre-NAV38 backup:** `backup/android-a1-nav37-owner-phone-not-flow-pre-nav38-20261119` @ `211460b4143bd3f775ccc0001a65afb5ce75b640`.
**NAV36 signed rollback:** `backup/android-a1-nav36-original-tca-birth-owner-signed-arm13-ci-green-20261118` @ `8b9d91b7b1ba2b0df84ada516bab938f077cfab9`.

`CELIKOM_REPLACEMENT=NOT_CONNECTED`. `IDENTITY_STATUS=STRUCTURAL_ONLY`. Original Yandex Music `2025.10.4 #120.1gpr` unchanged. No original Player/audio/decoder changes; don't invent playback/seek/pause/BT problems or modify architecture.

## Latest real owner phone: NAV37

- Private input: `CELIKOM-A1-Diagnostics-1795038626276.txt`, **94,207 bytes, 1,300 lines**, SHA256 `83a0a18170bfdebdc6f981068e8642eee0e6fc1c513979b830ecbe95899c6352`. Never commit raw diagnostic.
- Active `NAV_V37_TCA_CREATOR_TRACK_FIELD_SCOPE_READONLY` confirmed.
- `TCA_CREATOR_OWNER_ENTER=MANY`, `TRACK_FIELD_READ=MANY`, `WRAPPER_CONSTRUCTED=MANY`; owner null, Track field null/failed, wrapper no Track all NONE.
- **Single positive boundary:** `TCA_CREATOR_WRAPPER_NOT_FLOW=MANY`. `TCA_CREATOR_WRAPPER_FLOW_MATCH=NONE`, `TCA_CREATOR_WRAPPER_ALBUM_LINK=NONE`.
- Independently, `NATIVE_TRACK_FLOW_EMIT=FEW`, `FLOW_TRACK_ALBUM_LINK=FEW`, `TRACK_WRAPPER_ALBUM_LINK=MANY`; these are other observed paths, not proof the exact creator-owned Track was in Flow.
- `LIVE_PERIOD_SCOPED_*=NONE` in THIS export, and `LIVE_QUEUE_SLOT_B=NO_HOOK`: **no fresh strict live Player/queue witness** in this phone capture. Historical NAV36 SLOT_B → original Lo96/Sl6 → Player setter ref evidence remains historical only; do not carry it forward as a current attestation.
- `EXO_IO_FAILURE=NONE`; `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/NONE`. A retained SDK Push exception is not evidence of CELIKOM fault.
- This separates missing Track scope at NAV36 birth from NAV37's successfully read Track not found in *bounded current Flow history* at wrapper birth. It does not prove distinct Track identity, chronology, selected edition or current queue generation.

## NAV38 narrow read-only implementation

Based strictly on NAV37, do NOT redo NAV25–NAV36 probes or static caller searches. Retain max **32 weak Java Track references** when the exact tCa creator owns a Track that is not yet observed in the bounded Flow history. On later `onNativeTrackFlowEmission`, compare **the same Java reference using ==**, dedupe once per retained Track. Emit new bounded categories:
- `TCA_CREATOR_NOT_FLOW_ALBUM_OBSERVED`, `TCA_CREATOR_NOT_FLOW_ALBUM_UNOBSERVED`: distinguish historical Album link observation at birth (not evidence of current edition).
- `TCA_CREATOR_FLOW_LATER_SAME_TRACK`, `TCA_CREATOR_FLOW_LATER_ALBUM_OBSERVED`: later exact same-ref Flow event and independently observed Album link.

**Active NAV38 marker:** `NAV_V38_TCA_CREATOR_FLOW_TIME_ORDER_READONLY`.
No retroactive Track→wrapper→Player link is created; no active queue inference, no media substitution, no exported titles, IDs, URL, tokens, PCM or raw field values. Negative results are limited by weak refs and 32-item history.

**JVM CI:** [#44407443841 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44407443841).
**Owner ARM13 CI + automatic one-time signed APK export:** [#44407443952](https://github.com/manufact-test/nomusic/actions/runs/44407443952), SUCCESS.
**Clone-alone differential ARM13:** [#44407443848](https://github.com/manufact-test/nomusic/actions/runs/44407443848), SUCCESS.

## NAV38 signed artifact — DELIVERED TO PERSONAL LIBRARY

- Protected NAV38 signed source: `72d5c42f1678d7b6839202a52712e5e80bf8a019`; backup `backup/android-a1-nav38-flow-time-order-owner-signed-arm13-ci-green-20261119` at that exact commit. NAV37 pre-NAV38 backup remains untouched.
- CI: JVM [#44407443841 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44407443841); clone-alone ARM13 [#44407443848 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44407443848); owner publisher-first ARM13 [#44407443952 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44407443952).
- Signed APK `CELIKOM-A1-NAV38-Creator-Flow-Time-Order-ReadOnly-20261119.apk`: 71,491,564 bytes, SHA256 `3b4aa30dff47a44ca2e052c0a3bb9c44bcd6f0c6479720312ed670d56fec2378`. v2/v3 APK signing owner cert SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` unchanged.
- ZIP `CELIKOM-A1-NAV38-Creator-Flow-Time-Order-20261119.zip`: 51,618,089 bytes, SHA256 `e216f81839b3fe59b98f47d1850dcad4f706574ccc15da7cde2624ea67d7ef62`, matches GitHub artifact `14475253638`; ZIP CRC good, includes correct APK and NAV38 instruction.
- **Personal Library upload succeeded**, path `/CELIKOM/Android/Native/CELIKOM-A1-NAV38-Creator-Flow-Time-Order-20261119.zip`, Library ID `libfile_ad79f587f2208191a729d7774d251173`. File listed, materialized back, same size and SHA256; readback is byte-identical.
- **Next manual action:** owner installs NAV38 in place over NAV37 without uninstall or data clearing, listens to 2–5 ordinary tracks and returns private NAV38 diagnostic TXT. Stop if Android reports signature incompatibility. Do NOT build NAV39 or connect music replacement without new owner evidence.

## Context / archive

- [NAV37 implementation and prior CI](ANDROID-A1-NAV37-CREATOR-TRACK-FIELD-SCOPE-20261118.md)
- [NAV38 owner-phone evidence, experiment, CI](ANDROID-A1-NAV38-OWNER-PHONE-FLOW-TIME-ORDER-20261119.md)
- [NAV36 phone diagnosis](ANDROID-A1-NAV36-OWNER-PHONE-NO-TRACK-SCOPE-20261118.md)
- [Original signed DEX static audit](ANDROID-A1-TCA-BIRTH-STATIC-CALLSITE-20261118.md)

---

# ARCHIVED — NAV37 prior canonical checkpoint — — NAV37 exact tCa creator Track-field scope; CI GREEN; owner APK export pending (18 Nov 2026)

**Project:** CELIKOM Android A1 only, `manufact-test/nomusic`. **Only working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. No project restart, no architecture change, no Windows/extension work. Original signed Yandex Music **2025.10.4 #120.1gpr** remains unchanged. Original playback is known-good; do not invent seek/pause/Bluetooth faults or modify Player/audio.

**NAV37 runtime/package source commit:** `70b5f74485e92c7f0e6bd2ee86c910e4bd9ad8e6`.
**Protected CI-green checkpoint including workflow housekeeping:** `b4e9e9ee42c63efebe929cb415999e0cfe5dd861` (no runtime/package changes after the source commit).
**After the runtime/package checkpoint:** subsequent commits are documentation-only; fetch the live branch ref for the current docs HEAD. Runtime/package code remains at the checkpoint above.
**NAV36 protected code:** `8b9d91b7b1ba2b0df84ada516bab938f077cfab9`.
**NAV36 rollback:** `backup/android-a1-nav36-original-tca-birth-owner-signed-arm13-ci-green-20261118`.
**NAV37 pre-package source backup:** `backup/android-a1-nav37-exact-tca-creator-track-field-pre-owner-package-20261118` @ `099378e53412d09d20c0d3c9f01aaccffeafbdcc`.
**NAV37 CI-green checkpoint backup:** `backup/android-a1-nav37-creator-track-field-arm13-ci-green-20261118` @ `b4e9e9ee42c63efebe929cb415999e0cfe5dd861`.

`CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`.

## 1. Last real owner-phone evidence — NAV36 remains the baseline

- Private `CELIKOM-A1-Diagnostics-1795009674955.txt`, **117,037 bytes, 1,634 lines**, SHA256 `7701f459618aa3306dff153b200330a2f6e5a58edff4fa24efdf26f680e4f33d`. Never commit the raw TXT.
- NAV36 active marker at capture: `NAV_V36_TCA_CONSTRUCTOR_SCOPE_READONLY`.
- Strict live chain was confirmed: SLOT_B type1/state2 → original live Lo96/Sl6 source → the same original scoped Player setter source.
- The exact live Player-scoped `tCa` was in the bounded last-64 constructor history, but `BIRTH_NO_TRACK_SCOPE=MANY` was the **only positive** of the six NAV36 birth categories. The other five were NONE.
- This meant the existing synchronous `Gp0.new(...Track...)` scope was absent at that constructor birth. It did **not** prove Track/Album absence, a coroutine cause, the selected edition, current queue generation, or an audio problem.
- NAV35 `WRAPPER_ABSENT=MANY` was reproduced. See [NAV36 owner-phone evidence](ANDROID-A1-NAV36-OWNER-PHONE-NO-TRACK-SCOPE-20261118.md) and [NAV35/NAV36 checkpoint](ANDROID-A1-NAV35-OWNER-PHONE-WRAPPER-ABSENT-NAV36-TCA-CONSTRUCTOR-20261118.md).
- `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/FEW` remains unassigned to CELIKOM; do not attribute it without evidence.

## 2. NAV37 — the minimal new diagnostic step

The completed signed-original DEX audit found one exact `tCa(String)` creator whose String originates from a Track-typed field on a typed parameter object. The static search did not find a direct callsite to that creator, so it did not prove a same-object edge to the synchronous Gp0 scope.

The next minimal experiment does **not** invent a caller or broaden the static search. It hooks that exact creator method directly using a private target generated from the pinned signed XAPK during CI:

1. Enter a bounded creator-owner scope around the original method call.
2. In the existing original `tCa(String)` constructor hook, read the Track field from that exact owner argument.
3. Push that Track as the active constructor scope only for the original constructor execution.
4. If the owner/field/Track is null or unreadable, push a null scope that shadows any outer scope; never borrow an unrelated Track from Gp0.
5. After the original constructor succeeds, record only bounded weak-reference Track/Flow/Album/wrapper relationships.

The generated private Java target is ephemeral CI input and is removed during cleanup. The runtime observer does not change the original Yandex binary, original Player setter, audio pipeline, decoder, or replacement behavior. Original constructor/method execution is preserved.

**Active NAV37 marker:** `NAV_V37_TCA_CREATOR_TRACK_FIELD_SCOPE_READONLY`.

**New categorical evidence:**
- `AUDIO_NATIVE_TCA_CREATOR_HOOK` — `REGISTERED` / `NO_HOOK`.
- `TCA_CREATOR_OWNER_ENTER`, `TCA_CREATOR_OWNER_NULL`.
- `TCA_CREATOR_TRACK_FIELD_READ`, `TCA_CREATOR_TRACK_FIELD_NULL`, `TCA_CREATOR_TRACK_FIELD_FAILED`.
- `TCA_CREATOR_WRAPPER_CONSTRUCTED`, `TCA_CREATOR_WRAPPER_NO_TRACK`, `TCA_CREATOR_WRAPPER_NOT_FLOW`.
- `TCA_CREATOR_WRAPPER_FLOW_MATCH`, `TCA_CREATOR_WRAPPER_NO_ALBUM`, `TCA_CREATOR_WRAPPER_ALBUM_LINK`.

All NAV36 evidence and all six NAV36 birth reasons remain. No track/album names, IDs, URLs, PCM, media bytes, tokens, or private field values are exported.

A positive `TCA_CREATOR_WRAPPER_ALBUM_LINK` is still only structural evidence that the Track read from the exact creator owner belonged to the observed Flow and had an Album link. It does **not** prove the currently selected edition or queue generation, and does not mean music replacement is connected.

## 3. CI result — candidate green, not product acceptance

- [ARM13 publisher-first owner pipeline #44349835364 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44349835364), source commit `70b5f74485e92c7f0e6bd2ee86c910e4bd9ad8e6`.
  - Original publisher installed first; its 75-second lifecycle passed before clone installation.
  - The clone installed after the original, all 16 source splits were accounted for, and clone lifecycle was stable for 25/25 observations.
  - `AUDIO_NATIVE_TCA_CREATOR_HOOK=REGISTERED`.
  - Persistent owner signer verified; signer SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`.
  - `owner_apk_install_mode=UPDATE_EXISTING`; fresh-install authorization false.
  - `audio_or_account_tested=false`, `owner_phone_touched=false`, `stage_a=NO_GO`, `stage_b_current_player_album_edition_attested=false`, `diagnostic_only_not_product_or_releasable=true`.
  - Push run did not export an APK; artifact export is intentionally manual.
- [JVM observer regressions #44350073072 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44350073072), NAV37 marker contract and model tests.
- [Clone-alone differential ARM13 #44349367581 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44349367581).
- [Parser/ARM13 run #44347371311 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44347371311) also surfaced `AUDIO_NATIVE_TCA_CREATOR_HOOK=REGISTERED`.
- The old NAV36 one-shot workflow was switched to manual-only so it no longer runs against the NAV37 marker. Its already-started stale run is not part of the active NAV37 gate.

## 4. APK packaging status — not yet exported to Library

The package and Russian instructions are now versioned as NAV37:
- APK name: `CELIKOM-A1-NAV37-Tca-Creator-Track-Field-ReadOnly-20261118.apk`.
- GitHub artifact name: `CELIKOM-A1-NAV37-Tca-Creator-Track-Field-20261118`.
- The CI falls back to the known NAV36 installed signer SHA only when the explicit installed-cert variable is unset, allowing an in-place NAV36 update. Fresh-install authorization remains false.

**One manual GitHub action is required** because the pipeline intentionally skips artifact publication on ordinary pushes:
[Open the NAV37 ARM13 workflow](https://github.com/manufact-test/nomusic/actions/workflows/android-a1-metrica-init-state-observer-arm13.yml), select branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`, click **Run workflow**, set `export_diagnostic_apk=true`, and leave `authorize_fresh_clone_install=false`.

After that run completes, retrieve the artifact, verify APK signer SHA256 and APK/ZIP SHA256, upload the ZIP to the personal ChatGPT Library, download it back, and compare byte-for-byte. Do not send a GitHub artifact or an unverified sandbox path as the final delivery.

## 5. Required owner-phone check after Library delivery

- Install NAV37 **over the installed NAV36** as a normal update. Do not uninstall CELIKOM, clear data/cache, or reinstall Yandex.
- If Android says the signature is incompatible or asks to remove NAV36, stop and report the exact error; do not uninstall.
- Use Yandex normally for 2–5 ordinary tracks. No special seek, pause, Bluetooth, or stress tests are needed.
- Press `Сохранить диагностику` and send only the resulting TXT from `Загрузки/CELIKOM A1`.

The next engineering action after the phone TXT is to analyze whether the exact live Player-scoped wrapper now has the creator Track/Flow/Album link, and whether any stronger current-edition/queue-generation evidence exists. Do not create NAV38 or connect replacement speculatively.

## 6. Non-negotiable constraints

- Original Yandex Music `2025.10.4 #120.1gpr` stays unchanged; original playback is known-good.
- No player/audio/decoder intervention and no invented seek/pause/Bluetooth bugs.
- No repeated NAV25–NAV36 probes, old EOS/comparator checks, unrelated DEX searches, or architecture changes without new evidence.
- Never export track/album names, IDs, URLs, PCM, media bytes, tokens, raw private field values, or raw phone diagnostics.
- `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. NAV37 is a diagnostic candidate, not a working replacement or product release.

# ARCHIVED — previous NAV36 release checkpoint (superseded by current owner-phone handoff)

**CELIKOM Android A1 only**, repository `manufact-test/nomusic`, sole work branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Signed original Yandex Music 2025.10.4 unchanged. No original playback methods altered; CELIKOM_REPLACEMENT=NOT_CONNECTED, IDENTITY_STATUS=STRUCTURAL_ONLY. NEVER uninstall/clear owner data, invent playback bugs, redo EOS/comparator, or provide GitHub Actions/sandbox APK download links.

**REAL NAV35 OWNER PHONE** private `CELIKOM-A1-Diagnostics-1795006986945.txt`, 128,352 bytes / 1,813 lines, SHA256 `b34389ccc8813d61e2b479f0111160892e107a38aa855440b430b05fec9ca1a8`; NEVER commit raw. Exact live original Lo96 Sl6 source and scoped native Player setter source ref MATCH=MANY; exact original Player tCa `WRAPPER_ABSENT=MANY` from retained Stage B Flow/Track/Album links; all other NAV35 NO_LINK causes NONE. Independent constructor tCa=MANY, Flow Album=FEW, Track Wrapper Album=MANY; reason still uncertain. MUSIC_APP exception summary FEW, no owner playback complaint; cannot attribute.

**NAV36 exact SIGNED SOURCE** `8b9d91b7b1ba2b0df84ada516bab938f077cfab9`, protected backup `backup/android-a1-nav36-original-tca-birth-owner-signed-arm13-ci-green-20261118`. Pre-NAV36 backup `backup/android-a1-nav35-phone-wrapper-absent-pre-nav36-20261118` @ `b6c6a2f4ab6523481a499cc5b3958ac5bfbbd71c`. Marker `NAV_V36_TCA_CONSTRUCTOR_SCOPE_READONLY`. Existing original tCa(String) constructor hook retains weak last 64 original tCa refs with categorical construction context. Under strict live source match classify NAV35 WRAPPER_ABSENT into BIRTH_NOT_IN_WINDOW / NO_TRACK_SCOPE / TRACK_NOT_IN_FLOW / FLOW_NO_ALBUM / FLOW_ALBUM_LINK_MISSING / DUPLICATE_AMBIGUOUS. JVM tests cover all six and wrong original source. Original audio, values, methods and player unchanged. See [NAV35 phone→NAV36 code and release](ANDROID-A1-NAV35-OWNER-PHONE-WRAPPER-ABSENT-NAV36-TCA-CONSTRUCTOR-20261118.md).

**CI VERIFIED:** exact JVM `#44311280846 SUCCESS`, issuer-first signed original Android13 ARM13 `#44311280892 SUCCESS`; this is NOT phone playback proof. Signed APK `CELIKOM-A1-NAV36-tCa-Constructor-Scope-ReadOnly-20261118.apk` 71,487,468 bytes SHA256 `16329086e7b2ec2d3b976bbab2334993be68bb32c9a401c7551e0b6c4ffd93e3`. APK v2/v3 owner cert DER SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` unchanged NAV35. Embedded original Yandex APK SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged.

<badge>DELIVERED</badge> **Personal Library package now uploaded, listed, materialized and byte-verified:** `/CELIKOM/Android/Native/CELIKOM-A1-NAV36-Подписанный-APK-и-Инструкция-20261118.zip`, 51,090,129 bytes, SHA256 `4019d2a972b88542970eb5ea224a1209f85bf83fbf55f93366409fa6cfe5ff40`, Library ID `libfile_5d5fae68121081918df9d84108f29716`. Materialized copy is byte-identical. Earlier quota failure cleared/retry succeeded. A separate NAV36 instruction also remains in Library `libfile_dad077a6fecc81919faad34126439e94`. Do not use stale NAV24 CI README.

**NEXT:** give owner the PERSONAL Library package card. Owner extracts APK from ZIP, installs NAV36 IN PLACE over NAV35 (no uninstall, no clear data), listens 2–5 tracks, and exports private NAV36 diagnostic TXT. Then inspect that TXT and only then decide next instrumentation. No NAV37 before actual owner phone evidence.

---

# ARCHIVED — NAV36 signed release awaiting Library quota (18 NOV 2026)

**CELIKOM Android A1 only**, repository `manufact-test/nomusic`, sole work branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Signed original Yandex Music 2025.10.4 unchanged. No original playback methods altered; CELIKOM_REPLACEMENT=NOT_CONNECTED, IDENTITY_STATUS=STRUCTURAL_ONLY. NEVER uninstall/clear owner data, invent playback bugs, redo EOS/comparator, or provide GitHub Actions/sandbox APK download links.

**REAL NAV35 OWNER PHONE** private `CELIKOM-A1-Diagnostics-1795006986945.txt`, 128,352 bytes / 1,813 lines, SHA256 `b34389ccc8813d61e2b479f0111160892e107a38aa855440b430b05fec9ca1a8`; NEVER commit raw. Exact live original Lo96 Sl6 source and scoped native Player setter source ref MATCH=MANY; exact original Player tCa `WRAPPER_ABSENT=MANY` from retained Stage B Flow/Track/Album links; all other NAV35 NO_LINK causes NONE. Independent constructor tCa=MANY, Flow Album=FEW, Track Wrapper Album=MANY; reason still uncertain. MUSIC_APP exception summary FEW, no owner playback complaint; cannot attribute.

**NAV36 exact SIGNED SOURCE** `8b9d91b7b1ba2b0df84ada516bab938f077cfab9`, backup `backup/android-a1-nav36-original-tca-birth-owner-signed-arm13-ci-green-20261118`. Pre-NAV36 backup `backup/android-a1-nav35-phone-wrapper-absent-pre-nav36-20261118` @ `b6c6a2f4ab6523481a499cc5b3958ac5bfbbd71c`. Marker `NAV_V36_TCA_CONSTRUCTOR_SCOPE_READONLY`. Existing original tCa(String) constructor hook retains weak last 64 original tCa refs with categorical construction context. Under strict live source match classify NAV35 WRAPPER_ABSENT into BIRTH_NOT_IN_WINDOW / NO_TRACK_SCOPE / TRACK_NOT_IN_FLOW / FLOW_NO_ALBUM / FLOW_ALBUM_LINK_MISSING / DUPLICATE_AMBIGUOUS. JVM tests cover all six and wrong original source. Original audio, values, methods and player unchanged. See [NAV35 phone→NAV36 code and release](ANDROID-A1-NAV35-OWNER-PHONE-WRAPPER-ABSENT-NAV36-TCA-CONSTRUCTOR-20261118.md).

**CI VERIFIED:** exact JVM `#44311280846 SUCCESS`, issuer-first signed original Android13 ARM13 `#44311280892 SUCCESS`; this is NOT phone playback proof. Signed APK `CELIKOM-A1-NAV36-tCa-Constructor-Scope-ReadOnly-20261118.apk` 71,487,468 bytes SHA256 `16329086e7b2ec2d3b976bbab2334993be68bb32c9a401c7551e0b6c4ffd93e3`. APK v2/v3 owner cert DER SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` unchanged NAV35. Embedded original Yandex APK SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. Nested own DEX marker and counters verified. Private CI artifact `14430114939` expires `2026-11-25T13:20:55Z`; currently downloaded in this conversation runtime at `/mnt/data/CELIKOM-A1-NAV36-tCa-Constructor-Scope-ReadOnly-20261118.apk`, NOT Library.

**IMPORTANT BLOCKER — personal Library STORAGE LIMIT:** upload of full APK 71.49 MB FAILED (quota); attempted smaller 51.09 MB ZIP with same APK also FAILED. Do not falsely claim NAV36 owner APK is available in personal Library. No older user files deleted or overwritten. Separate correct `/CELIKOM/Android/Native/CELIKOM-A1-NAV36-Инструкция.txt` (2,982 bytes SHA256 `de020b440b82ba270032ad791b461e3a334c3758bd436425b41ea5a07e68d31d`) uploaded/listed/materialized and byte-verified Library `libfile_dad077a6fecc81919faad34126439e94`. CI-generated README-RU.txt was STALE NAV24; do not distribute it. A correct 51.09 MB ZIP also exists in this conversation runtime, but quota prevents its Library upload. No user download link until Library owner APK is verified.

**NEXT ACTION:** user must free enough personal Library storage or explicitly authorize deletion of particular old files; DO NOT silently delete/overwrite NAV35/34 rollback files. After storage is freed, upload exact signed NAV36 APK (or same signed ZIP) to `/CELIKOM/Android/Native/`, list it, materialize/readback SHA256 byte-verify, then provide PERSONAL Library file card, NOT sandbox/Actions. Only then ask user to install in place over NAV35 without uninstall/wipe, listen 2–5 tracks and export new private TXT. No NAV37 before real NAV36 diagnostics.

---

# ARCHIVED — NAV36 CI PENDING checkpoint before signed release

Only CELIKOM Android A1 in `manufact-test/nomusic` sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; original signed Yandex Music 2025.10.4 untouched. No architecture, player, PCM or audio changes; no uninstall/clear data, no invented seek/BT/VPN issues, no comparator/EOS repeat, replacement NOT_CONNECTED and identity STRUCTURAL_ONLY. Deliver APK exclusively as verified personal ChatGPT Library file card, not Actions/sandbox.

**REAL NAV35 owner TXT** `CELIKOM-A1-Diagnostics-1795006986945.txt`, 128,352 bytes/1,813 lines/SHA256 `b34389ccc8813d61e2b479f0111160892e107a38aa855440b430b05fec9ca1a8` private, NEVER commit. NAV35 ACTIVE; live original Lo96 Sl6 source MATCH=MANY against original scoped Player setter, live SLOT_B MATCH=MANY, absent/error NONE. New reason: `LIVE_PERIOD_SCOPED_ALBUM_NO_LINK_WRAPPER_ABSENT=MANY` uniquely, other reasons NONE. The exact Player scoped tCa object is missing from bounded Stage B Flow Track/Album links, even though independent Track Wrapper Album links=MANY and Flow Album=FEW. This is **NOT** proof no album or selected edition. EXO_IO_FAILURE NONE; MUSIC_APP exceptions FEW (not attributed to our module); USER_REQUESTED exits, no owner playback bug report.

**NAV36 proposed read-only code (CI pending):** use existing original tCa constructor hook and last 64 weak original tCa instances, categorizing the exact Player scoped tCa at construction as NOT_IN_WINDOW, NO_TRACK_SCOPE, TRACK_NOT_IN_FLOW, FLOW_NO_ALBUM, FLOW_ALBUM_LINK_MISSING or DUPLICATE_AMBIGUOUS only under same strict live original source guard. No new vendor hooks or media reads, no original behavior changes. NAV34/35 bins retained, tests verify all 6 categories and wrong source. Docs: [NAV35 phone → NAV36](ANDROID-A1-NAV35-OWNER-PHONE-WRAPPER-ABSENT-NAV36-TCA-CONSTRUCTOR-20261118.md). Protected backup pre-NAV36: `backup/android-a1-nav35-phone-wrapper-absent-pre-nav36-20261118` @ `b6c6a2f4ab6523481a499cc5b3958ac5bfbbd71c`.

**RELEASE GATE:** exact JVM+Android13 ARM13 signed CI GREEN, verify owner cert/signature v2/v3 unchanged and embedded original publisher SHA unchanged, nested NAV36 marker, upload own APK+short instruction to personal Library and readback hashes byte-identical. Then ONLY owner in-place NAV36 install over NAV35 without clearing data, listen 2–5 tracks and send private TXT. No NAV37 before real NAV36 phone evidence.

---

# ARCHIVED — NAV35 signed release before real owner NAV35 TXT (18 NOV 2026)

**SCOPE:** CELIKOM Android A1 only, repo `manufact-test/nomusic`, sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; original signed Yandex 2025.10.4 and its player unchanged. Replacement `NOT_CONNECTED`, identity `STRUCTURAL_ONLY`. Never attribute playback/seek/pause/BT problems without owner report. Never reinstall/wipe data, change architecture, rerun EOS/comparator or use unverified APK. APK to owner exclusively from PERSONAL ChatGPT Library, not GitHub Actions/sandbox.

**LATEST REAL OWNER PHONE — NAV34:** `CELIKOM-A1-Diagnostics-1795004556515.txt` (112,770 bytes, 1,585 lines, private, DO NOT commit); active `NAV_V34_SCOPED_TRACK_ALBUM_SOURCE_READONLY`. Strict live e.h.SLOT_B+type1/state2 renderer confirms original direct Lo96 Sl6 SOURCE_PRESENT=MANY, SOURCE_RESOLVED=MANY, same Java-ref as scoped original Player source setter `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH=MANY`, NO_LINK/OTHER=NONE. NEW historical scoped tCa→Track/Album categories: MATCH=NONE, NO_LINK=MANY, CONFLICT=NONE, although independent Stage B Track Album constructor/wrapper=MANY and Flow Album=FEW. This **does not prove missing album or mismatch**; NAV34 collapsed all missing/weak/ambiguous reasons. EXO_IO_FAILURE=NONE, METRICA_EXCEPTION_SUMMARY=MUSIC_APP/NONE. No reported playback defect.

**NAV35 SIGNED EXACT SOURCE:** `4e1ad33c717b2a4199c680bb438e1b3d1068d414` (backup `backup/android-a1-nav35-no-link-reasons-owner-signed-arm13-ci-green-20261118`). Pre-NAV35 protected `backup/android-a1-nav34-owner-phone-no-link-pre-nav35-20261118` @ `9620572d08e7abd16605f46680fb0d6560edbfde`. Marker `NAV_V35_SCOPED_ALBUM_NO_LINK_REASON_READONLY`. Only owned read-only `StageBAudioEvidence` and `NativeRendererStreamEvidence` categorical classification under **same strict live original source equality guard**. The historical Album NO_LINK reason is separated into WRAPPER_ABSENT, WRAPPER_AMBIGUOUS, TRACK_WEAK_LOST, ALBUM_UNSET, ALBUM_WEAK_LOST, FLOW_MISSING, TRACK_ALBUM_MISSING, UNKNOWN. Preserves existing NAV34 MATCH/NO_LINK/CONFLICT bins; no vendor value reads, IDs, content, metadata, PCM or original playback modifications. JVM negative cases: unrelated wrapper, absent album, duplicate wrapper, wrong original source.

**CI VERIFIED:** JVM `#44304008995 SUCCESS`; issuer-first owner-signed Android13 ARM13 `#44304008147 SUCCESS` on exact source SHA. Android13 guest verdict is PASS_NOT_AUDIO, not actual owner phone playback or music substitution proof. APK `CELIKOM-A1-NAV35-Album-No-Link-Reasons-ReadOnly-20261118.apk` 71,487,468 bytes; SHA256 `3b7832a383e75575d5abe5b47054f8cfe5f289775d43964986a50ae58bf95d00`, verified as signed CI ZIP output. APK Signing Block v2/v3 owner DER cert SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` unchanged from NAV34. Embedded original issuer Yandex APK SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. Own nested module DEX exact NAV35 marker + new counter names verified.

**PERSONAL LIBRARY FILES BYTE-VERIFIED AFTER MATERIALIZE READBACK:** `/CELIKOM/Android/Native/CELIKOM-A1-NAV35-Album-No-Link-Reasons-ReadOnly-20261118.apk` — Library ID `libfile_d43f8e3454a08191940f5f9d609cb831` (APK hash above). `/CELIKOM/Android/Native/CELIKOM-A1-NAV35-Инструкция.txt` — Library ID `libfile_cbc66c2f59b08191bcd6eea151700654` (2,176 bytes, SHA256 `52b7fc0f6aa5a78ebca873dc3e2d257723df784e8f6a2db456fcb303e8d6b066`). Both listed, materialized back and exact bytes compared; NAV34 retained for rollback.

**ONLY NEXT ACTION:** owner installs NAV35 APK from personal Library **in place** over NAV34 without uninstall/data/cache/account wipe (STOP if denied), listens 2–5 normal tracks, exports fresh private TXT. Analyze active NAV35 and exact NO_LINK reason under original source MATCH, check original playback remained stable. No NAV36 before real owner NAV35 evidence. Even historical Track Album MATCH is not currently selected track edition/duration/queue-generation; replacement stays NOT_CONNECTED. Detailed signed NAV35 proof: [NAV34 phone → NAV35 release](ANDROID-A1-NAV34-OWNER-PHONE-ALBUM-NO-LINK-NAV35-REASONS-20261118.md).

---

# ARCHIVED — previous NAV33 phone / NAV34 CI-pending handoff (superseded by CURRENT above)



**NAV32 actual owner phone:** private `CELIKOM-A1-Diagnostics-1795000688077.txt`, 116,173 bytes / 1,643 lines, never commit. New NAV32 marker ACTIVE at capture/export, NAV31 historical. `HOLDER_OTHER_WH6_SELECT_ENTER/EXIT/ATTACH/AT_READ=MANY`; `HOLDER_OTHER_LO96_AT_READ=MANY`; both `HOLDER_OTHER_SELECT_SAME_AT_READ=MANY` and `HOLDER_OTHER_ATTACH_SAME_AT_READ=MANY`, corresponding DIFFERENT/WEAK_LOST/NO_HISTORY=NONE. Real live SLOT_B+renderer/stream read MATCH=MANY. **The holder contains exact direct Lo96 original MediaPeriod, same Java reference through select→attach→started audio read.** Previous non-Lup1 "MISSING" was a diagnostic early-return, not proof of missing source. `LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED=NONE` in NAV32 must not be interpreted as null. Track→Album descriptor/source/edition/queue-generation identity still not established, replacement NOT_CONNECTED.

**NAV33 source-only witness:** code `d2925a9479f325293bed6dfb5540ebf02015b560` on same branch, private original direct Lo96 → pinned Sl6 source Field, only within strict already-live SLOT_B+type1/state2 renderer guard. Distinguishes `LIVE_PERIOD_DIRECT_HOLDER_LO96_SOURCE_PRESENT/NULL` and existing source-resolved + original Player setter scoped Java-reference MATCH/NO_LINK/OTHER. Non-Lo96 fail closed, Lup1 and adapter route intact. Original Yandex audio/methods/results untouched; no alternative music. JVM #44295498699 SUCCESS; publisher-first owner-signed Android13 ARM13 #44295498745 SUCCESS at exact code SHA; runtime verdict PASS_NOT_AUDIO, not real phone test. APK SHA256 `b7d06a81e10cb3d8c9f93c9ce3f59fd97600b4eaf1f2ace6f83be5192e510c13`; 71,483,372 bytes; signer v2/v3 original owner DER `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`; unchanged embedded issuer Yandex SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. CI APK SHA independently verified; both Library files byte-verified after materialize-back. `IDENTITY_STATUS=STRUCTURAL_ONLY`; source equality is not selected Track+Album+edition/queue-generation proof. Details: [NAV32 phone → NAV33](ANDROID-A1-NAV32-OWNER-PHONE-DIRECT-LO96-NAV33-SOURCE-20261118.md).

**NAV33 VERIFIED PERSONAL LIBRARY:** `/CELIKOM/Android/Native/CELIKOM-A1-NAV33-Direct-Lo96-Source-ReadOnly-20261118.apk` — `libfile_f84cdebbd82c8191bc605166e087c4e2`, SHA256 `b7d06a81e10cb3d8c9f93c9ce3f59fd97600b4eaf1f2ace6f83be5192e510c13`; `/CELIKOM/Android/Native/CELIKOM-A1-NAV33-Инструкция.txt` — `libfile_26d3cb6111c88191b0066c9800387665`, 2,858 bytes, SHA256 `bb9ca4ec8f1e5a72ffa9558dbb3bb5d1e15ce504f83720b12cc0f4cd5f302368`. Both uploaded, listed, materialized back and byte-identical. Signed exact code backup `backup/android-a1-nav33-direct-lo96-owner-signed-arm13-ci-green-20261118` @ `d2925a9479f325293bed6dfb5540ebf02015b560`. Pre-NAV33 backup `backup/android-a1-nav32-owner-phone-direct-lo96-pre-nav33-20261118` @ `66e0dfb985b260fb4d5cc4b69b357ef4b95257dd`.

**ONLY NEXT OWNER TEST:** install NAV33 Library APK over NAV32 without uninstall/cache/data clearing; if denied STOP. Listen 2–5 normal tracks, export fresh private TXT. Check active NAV33 marker, new direct Lo96 source PRESENT/NULL, original SOURCE_RESOLVED and scoped TRACK_WRAPPER_SOURCE_MATCH/NO_LINK/OTHER against live SLOT_B. Even MATCH is only original source Java identity, not selected Track+Album/edition/queue-generation or audio replacement. CELIKOM_REPLACEMENT remains NOT_CONNECTED. No NAV34 without owner NAV33 evidence.

**NAV33 owner actual phone TXT received:** private `CELIKOM-A1-Diagnostics-1795003154029.txt` (97,897 bytes; 1,365 lines). ACTIVE NAV33 on capture/export, NAV32 historical. Live strict SLOT_B type1/state2 read=MANY, original direct Lo96 Sl6 SOURCE_PRESENT=MANY, SOURCE_RESOLVED=MANY, scoped original Player setter source Java ref MATCH=MANY, SOURCE_NULL/UNAVAILABLE/NO_LINK/CONFLICT NONE. This is now a proven real-phone original source alias, not current selected Track+Album/edition/queue-generation. Stage B Track Album wrapper=MANY but descriptor/factory/source links NONE. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, IDENTITY_STATUS=STRUCTURAL_ONLY; no user playback fault. 

**NAV34 bounded next witness (CI pending):** only after strict live original source equality to unique scoped original Player setter, pass the exact same tCa wrapper to existing Stage B Track Flow→Track/Album→tCa weak-reference model and classify MATCH/NO_LINK/CONFLICT. No selected edition/queue generation claim or audio modification, negative guards included. New detailed [NAV33 phone → NAV34](ANDROID-A1-NAV33-OWNER-PHONE-SOURCE-MATCH-NAV34-TRACK-ALBUM-WRAPPER-20261118.md). Do NOT issue owner APK until signed JVM+ARM13 CI, signature/hash, personal Library byte-verification. Backup pre-NAV34 @ `63dbc56cae3c827fc538c2fbff525db7c15abc7c` (`backup/android-a1-nav33-owner-phone-source-match-pre-nav34-20261118`). 

## Windows engineering lessons for Android (reference only)

Before changing Android network/player/source-recovery logic, read [ANDROID-WINDOWS-LESSONS-AND-PORTING-PLAYBOOK-20261118.md](ANDROID-WINDOWS-LESSONS-AND-PORTING-PLAYBOOK-20261118.md). It consolidates Windows VPN continuity, Next/Stop generation fencing, signed URL 403, source proof, stale source-left, track UI handoff, Yandex lifecycle/restart guards, module/update rollback and unresolved gain/hiss cases with exact Windows files/commits. **Transfer design invariants only. Do not port Windows Electron/CDP/WinForms APIs or assume Android source substitution works.** This reference does not change the current NAV33 diagnostic task or the NOT_CONNECTED Stage B boundary above.


**Only** Android A1, repo `manufact-test/nomusic`, sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; no architecture, original Yandex 2025.10.4, Windows/backend or playback changes. Stage B `CELIKOM_REPLACEMENT=NOT_CONNECTED`; `IDENTITY_STATUS=STRUCTURAL_ONLY`. Never claim a seek/pause/Next/BT playback bug unless the owner reports one. APK only via personal ChatGPT Library, after exact signed CI + file/hash/readback verification. Do NOT give GitHub Actions/sandbox download links.

---

# ARCHIVED — NAV32 pre-phone handoff (superseded by CURRENT NAV33 above)

**NAV31 owner phone TXT RECEIVED:** private `CELIKOM-A1-Diagnostics-1794999303715.txt`, 100,645 bytes / 1,418 lines. Active `NAV_V31_HOLDER_SELECT_LIFECYCLE_READONLY` at capture/export, older NAV30 historical only; hook `HOLDER_SELECT_PHASE=REGISTERED`. At exact original selection ENTER/EXIT: `OTHER=MANY`, `EXACT/NULL/FAILED=NONE`. At live SLOT_B attach: `HOLDER_ATTACH_OTHER=MANY`, other bins NONE. At strict type1/state2 started-read `LIVE_PERIOD_HOLDER_WRAPPER_OTHER_AT_READ=MANY`, `NULL_AT_READ=NONE`. The NAV30 "MISSING" bucket **is definitively NON-NULL WRONG-CLASS in this session**, not cleared/null. The OTHER class and selected Track/Album identity are NOT known; historical prior exact Lup1 bins NONE as expected. `LIVE_QUEUE_SLOT_B_ATTACH_MATCH` and `TYPE1_STATE2_READ_MATCH=MANY`, source/period resolved NONE; Track→Album still partial, comparator FALSE-only not identity. Exo I/O failure NONE, no confirmed owner playback failure. Complete new forensic: [NAV31 owner phone and NAV32 exact next diagnostic](ANDROID-A1-NAV31-OWNER-PHONE-OTHER-CLASS-NAV32-PERIOD-REF-20261118.md).

**NAV32 FINAL signed owner code:** `2f7feb8d7f8b3708925cc2c68ebe523f031930ad`, `NAV_V32_HOLDER_OTHER_TYPE_REF_READONLY`. Actual NAV31 private phone evidence motivated *only* finite known-MediaPeriod `Lwh6`/`Lo96` class and strict original Object Java-ref comparisons (select EXIT → attach → started type1/state2 read on same live SLOT_B holder). No current Track/Album identity or music substitution. JVM model/tests `#44290883730 SUCCESS` on exact identical runtime Java (later commits changed only workflow/CI Python); **owner signed Android13 ARM13** `#44290896479 SUCCESS` on final source SHA. Native verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO` is not an owner phone/audio substitution test.

**NAV32 APK VERIFIED independently:** `CELIKOM-A1-NAV32-Other-Holder-Identity-ReadOnly-20261118.apk`, size **71,483,372 bytes**, SHA256 `c956e5bb4dc03ae6c368e0fb0850c2eb6e16aeed84a5b7ac850d59bbdd875548`. APK Signing Block v2/v3 DER cert SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` (same owner NAV31), embedded original publisher APK SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. Exact own-module DEX contains NAV32 marker and new bins. Native CI zip generic README stale; separate current instruction created.

**PERSONAL ChatGPT LIBRARY VERIFIED (upload, list, materialize back, byte equality):**
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV32-Other-Holder-Identity-ReadOnly-20261118.apk` — `libfile_4f720b0b77a88191a909ff8f92e474dc`, checksum above.
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV32-Инструкция.txt` — `libfile_830d55cb95d88191be79cf2b9cfe6e5e`, 2827 bytes, SHA256 `9fa963e79f76c50a6236dc68985819cf7c3fd373b82b3be579060cae570e22cc`.
Previous Library NAV31/30 signed APKs preserved. Protected exact signed NAV32 code backup `backup/android-a1-nav32-other-holder-owner-signed-arm13-ci-green-20261118` @ `2f7feb8d7f8b3708925cc2c68ebe523f031930ad`. Pre-NAV32 phone baseline backup `backup/android-a1-nav31-owner-phone-other-class-pre-nav32-20261118` @ `8c3a5b2659947a6301fa76a19b526ddeee7478de`.

**NEXT OWNER PHONE:** install Library NAV32 APK IN PLACE over NAV31 with no uninstall/data/cache wipe. If installation refuses, STOP and preserve NAV31. Play 2–5 normal tracks and export new PRIVATE TXT. Verify active NAV32 marker and hooks, read `HOLDER_OTHER_WH6_SELECT_ENTER/EXIT/ATTACH/AT_READ`, `HOLDER_OTHER_NON_WH6_AT_READ`, `HOLDER_OTHER_LO96_AT_READ`, `HOLDER_OTHER_UP1_NAME_DIFFERENT_LOADER_AT_READ`, `HOLDER_OTHER_SELECT/ATTACH_*_AT_READ`, correlating strictly with same started SLOT_B and `TRACK_PLAYER_SOURCE_*`. **Do not promote a positive WH6 flag or same Object to selected Track+Album/edition/queue generation or replacement audio.** Do not repeat comparator/EOS investigations, do not invent NAV33 before NAV32 phone TXT. Details [NAV31 real phone + NAV32 signed owner release](ANDROID-A1-NAV31-OWNER-PHONE-OTHER-CLASS-NAV32-PERIOD-REF-20261118.md).

---

# ARCHIVED — NAV31 OWNER-SIGNED ARM13 GREEN; OWNER PHONE TXT ALREADY RECEIVED (18 NOV 2026)

**Only CELIKOM Android A1**: `manufact-test/nomusic`, sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Stage B CELIKOM_REPLACEMENT **NOT_CONNECTED**; current signed APK is diagnostic ONLY, no audio substitution. Do not invent user playback/seek/Next bugs, do not restart architecture, change vendor signed original or Windows/backend. Never send owner sandbox/GitHub Actions artifact URLs: **personal ChatGPT Library entries only**. Preserve old signed APKs/backup and NEVER uninstall/clear data to update.

**Latest actual owner phone evidence is NAV30, NOT NAV31**: private uploaded `CELIKOM-A1-Diagnostics-1794997032172.txt` (NEVER put raw TXT in GitHub). Old NAV29 marker in historical lines but NAV30 marker `NAV_V30_NATIVE_PERIOD_ADAPTER_READONLY` ACTIVE at capture and export. Real original live `h.SLOT_B → holder → audio renderer/stream` maintained: `LIVE_QUEUE_SLOT_B_ATTACH_MATCH=FEW`, `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY` with no OTHER/UNAVAILABLE, `READ_RETURN_LINK_LOST=NONE`. `TRACK_PLAYER_SOURCE_SAME_SCOPE=FEW`, UNSCOPED=ONE, CONFLICT=NONE. New failure `LIVE_PERIOD_HOLDER_WRAPPER_MISSING=MANY`, which in NAV30 meant **either NULL OR wrong-class Object field**, not proof field is null. `LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED=NONE`, all source matches NONE. Original `Lp96.goto` and `Lp96.transient` hooks REGISTERED but both `NATIVE_PERIOD_ADAPTER_SCOPE_ENTER` and `FACTORY_IN_SCOPE` NONE in this session. Comparator FALSE=MANY, no strict audio-read comparator outcome; do not use comparator as prerequisite. EXO_IO_FAILURE FEW and METRICA_EXCEPTION SUMMARY MUSIC_APP/FEW not owner-verified playback failures.

**NAV30 forensic addendum:** full private TXT re-read (84,521 bytes; raw file stays private). Track→Album is partial only: constructor=MANY, flow/wrapper=FEW, descriptor/factory/source/open/read links=NONE; no edition or selected queue-generation identity. Renderer proof remains real (SLOT_B attach=FEW, type1/state2 read=MANY), but queue-scoped read-return bins are NONE while unscoped attached-stream read-match=MANY. Comparator is FALSE=MANY / TRUE=NONE despite being called with Engine Match + Attached Stream; it is not a Track-identity predicate. Period wrapper-missing=MANY still conflates NULL and wrong-class; original period source resolved=NONE; adapter/factory in-scope=NONE. Full counter interpretation and boundaries: [NAV30 full-export forensic supplement](ANDROID-A1-NAV30-OWNER-PHONE-MISSING-WRAPPER-NAV31-SELECT-20261118.md#nav30-full-export-forensic-supplement-private-owner-txt-18-nov-2026). Do not repeat comparator/EOS probes; NAV31 is already signed/CI-green/Library-verified and awaits owner phone TXT.

**Documentation checkpoint:** the complete NAV30 owner TXT was re-read and the detailed handoff now records the Track→Album counter limits, comparator false-only behavior, unscoped renderer-read caveat, and exact period-wrapper blocker. Stale NAV31 pending-CI wording in the detailed handoff has been reconciled with the already green CI and verified Library release. These are documentation-only changes; signed NAV31 runtime code is unchanged.

**NAV31 new signed read-only witness:** Exact signed original `Lxh6.if(LRFa;JZ[Z)J` reads same holder Object field at original DEX PC61 as constructor wrote unique Lup1 at PC136 (pinned signed existing CI proof). Optional hook captures finite type/null/reflection outcome *before and after exact original call (proceed exactly once)*, at live SLOT_B audio attach, and at current strict type1/state2 audio read. Distinguishes `HOLDER_SELECT_ENTER/EXIT_EXACT/NULL/OTHER/FAILED`, `HOLDER_ATTACH_EXACT/NULL/OTHER/FAILED`, `LIVE_PERIOD_HOLDER_WRAPPER_NULL_AT_READ/OTHER_AT_READ`; bounded weak historical links `LIVE_HOLDER_PRIOR_SELECT_EXACT_CLEARED/PRESENT/WEAK_LOST` never imply active track/edition/PCM/authorization. Strong prior NAV28/29/30 evidence still required. No metadata, IDs, tokens, URLs, audio bytes or private field names logged. **No owner NAV31 phone TXT yet.**

**Signed exact source checkpoint:** `a8257a6f456bd897bbf4bef6bb8d823713a56dd5`; signed protected backup `backup/android-a1-nav31-holder-select-lifecycle-owner-signed-arm13-ci-green-20261118` @ exact SHA. Pre-NAV31 owner phone/accepted NAV30 backup `backup/android-a1-nav30-owner-phone-holder-wrapper-missing-pre-nav31-20261118` @ `c24cc9e8b693f481db3b1a4555522f99a898810c`. Last working branch HEAD after signed code **DOCS-ONLY**; source protected.

**CI VERIFIED:** NAV31 model JVM `#44284890154 SUCCESS` (same signed code SHA); publisher-first signed original Yandex 2025.10.4 16-split native Android13 ARM13 `#44284890144 SUCCESS`, owner artifact `14419072970`. Original publisher+clone launched; output verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`: **not** owner-phone playback or alternative-audio test. CI `owner_apk_signer_verified=true` and original issuer-signed XAPK verified.

**OWNER APK VERIFIED:** `CELIKOM-A1-NAV31-Holder-Select-Lifecycle-ReadOnly-20261118.apk`; exact size **71,483,372 bytes**, SHA256 **`394a0d67a4d25c0975d19263510781484cf129468fbee84477bcbb3c392c977f`**, equals signed CI output. Independently verified APK signing block v2/v3 DER cert SHA256 **`048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`** (same signed owner NAV30). Embedded publisher original `assets/lspatch/origin.apk` SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. Nested own module DEX contains active NAV31 marker and exact new finite evidence counters. Generic README included in CI ZIP STALE; user gets separately authored current NAV31 instruction.

**VERIFIED PERSONAL ChatGPT LIBRARY** both individually uploaded, listed, downloaded BACK and byte-for-byte compared:
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV31-Holder-Select-Lifecycle-ReadOnly-20261118.apk` (SHA above)
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV31-Инструкция.txt`, 2,763 bytes SHA256 `49bcc19cc026a751f82b841ba6da1d68d31676ec98508bee072ab142baa16c81`.
Exact Library APK entry `libfile_c10b7184d6008191b1d8e990c5642302`, instruction `libfile_d567085752f88191952dc1927cde0e8b`. Download MUST use Library file card/entry (do not invent URLs or sandbox). Older signed NAV30/29/28 Library APK preserved.

**NEXT OWNER ACTION:** install Library NAV31 APK **OVER NAV30** without uninstall/cache/data clear; if Android refuses, STOP and preserve NAV30. Play 2–5 usual tracks, export fresh private TXT. Analyze active NAV31 marker, HOLDER_SELECT_PHASE registration, new select-entry/exit/attach/read null-vs-other lifecycle bins, prior selected-link historical bins, then strict SLOT_B and original `TRACK_PLAYER_SOURCE_*` and `CELIKOM_REPLACEMENT`. Even an early positive `Lup1` is NOT selected Track+Album/edition/duration/generation nor license/entitlement or proof of replacement audio. No repeated EOS/comparator loops.

Detail: [NAV30 phone actual + NAV31 signed and Library](ANDROID-A1-NAV30-OWNER-PHONE-MISSING-WRAPPER-NAV31-SELECT-20261118.md).

---

# ARCHIVED — NAV30 PHONE HOLDER WRAPPER MISSING; NAV31 EARLY SELECTION PHASE IN CI (18 NOV 2026)

**Only:** CELIKOM Android A1; repo `manufact-test/nomusic`; sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Do NOT restart architecture, edit signed original Yandex, change Windows/backend, invent playback bugs or claim an audible CELIKOM replacement. Current `CELIKOM_REPLACEMENT=NOT_CONNECTED`. Download APK ONLY from verified personal ChatGPT Library (no GitHub Actions/sandbox links), preserve older signed APKs.

**ACTUAL LATEST OWNER PRIVATE PHONE TXT** `CELIKOM-A1-Diagnostics-1794997032172.txt` (never commit). Contains OLD NAV29 event at file line ~78, but ACTIVE `NAV_V30_NATIVE_PERIOD_ADAPTER_READONLY` at capture ~196 and current export ~485. Actual NAV30 hook registrations: `LIVE_PERIOD_ORIGINAL_SOURCE`, `NATIVE_PERIOD_ADAPTER`, `NATIVE_PERIOD_FACTORY`, `LIVE_QUEUE_SLOT_B`, original Player source setter all REGISTERED. **Crucial positive evidence:** `LIVE_QUEUE_SLOT_B_ATTACH_MATCH=FEW`; `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY` and OTHER/UNAVAILABLE=NONE; `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW`; `READ_RETURN_LINK_LOST=NONE`. `TRACK_PLAYER_SOURCE_SAME_SCOPE=FEW`, `TRACK_PLAYER_SOURCE_UNSCOPED=ONE`, CONFLICT=NONE. Active source still `LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED=NONE`, `UNAVAILABLE=MANY`. **Exact measured failure phase** `LIVE_PERIOD_HOLDER_WRAPPER_MISSING=MANY`; all other finer NAV30 phase bins NONE. WARNING: in NAV30 source this label conflates **null field and non-Lup1 instance**, so cannot claim actual null before NAV31. `NATIVE_PERIOD_ADAPTER_SCOPE_ENTER=NONE`, `NATIVE_PERIOD_FACTORY_IN_SCOPE=NONE`, LINK_CREATED=NONE; although both hooks REGISTERED, they were not called in this user's session. Do not promote NAV30 temporal alias to identity. `IDENTITY_STATUS=STRUCTURAL_ONLY`; CELIKOM audio replacement remains NOT_CONNECTED. `RENDERER_COMPARATOR_FALSE=MANY` but no same started-audio read comparator result; do not use comparator as mandatory. `EXO_IO_FAILURE=FEW` differs from NAV29; it is a counter, **not a user-reported audio fault**. `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/FEW` plus historical `USER_REQUESTED` exits do NOT prove a playback crash.

**NAV31 code already pushed** `a8257a6f456bd897bbf4bef6bb8d823713a56dd5`, based on live original source `c24cc9e8b693f481db3b1a4555522f99a898810c`; pre-NAV31 safety backup `backup/android-a1-nav30-owner-phone-holder-wrapper-missing-pre-nav31-20261118` @ `c24cc9e8b693f481db3b1a4555522f99a898810c`. NAV31 hooks only **signed-proven original** `Lxh6.if(LRFa;JZ[Z)J` (existing pinned exact original DEX holder selection reads the same `Lxh6.Object` private field at PC61 as written by exact constructor). Intercepts **before and after one original unchanged** selection call, classifies original field as exact `Lup1` / NULL / other object / exception. At strict live SLOT_B attach classifies same field. At original started-audio read splits NAV30 combined missing into explicit NULL vs OTHER. Stores only bounded weak early holder+exact wrapper references as **historical phase-only** correlation. A previously seen wrapper, if cleared at read, is NEVER promoted to current-period/source/Track identity; changed queue, source, edition/generation unresolved. All generated diagnostics finite category counts, no class names, private names, track IDs, URLs, tokens, media or audio bytes. Existing NAV28/29/30 read-only hooks and original source unchanged. JVM regressions explicitly test exact-before/null-after, wrong class, hook disabled; no unsound positive source match.

**CIs at documentation:** NAV31 owner signed publisher-first original Android13 ARM13 `#44284890144` queued/running; JVM workflow triggers on model/owned code `#<check current run>`. Do not mark PASS, upload any APK, or tell owner to test until both green and actual owner signer v2/v3, original pinned `assets/lspatch/origin.apk`, APK hash and full personal Library readback verified. Old NAV30 signed APK in Library still valid and preserved.

**Next:** check NAV31 CI; if failure, fix source and retest new exact source, preserve backups. Once signed CI green, upload APK and accurate fresh Russian NAV31 instruction to personal ChatGPT Library and list + materialize back + byte-compare. Only then request owner in-place update over NAV30 (no uninstall/data wipe), play 2–5 tracks and privately send TXT. Inspect `HOLDER_SELECT_PHASE` registration, `HOLDER_SELECT_ENTER/EXIT_EXACT/NULL/OTHER/FAILED`, `HOLDER_ATTACH_*`, `LIVE_PERIOD_HOLDER_WRAPPER_NULL_AT_READ/OTHER_AT_READ` and `LIVE_HOLDER_PRIOR_SELECT_EXACT_CLEARED/PRESENT/WEAK_LOST` with retained live SLOT_B and original source bins. If selector not called or wrapper not available, follow evidence rather than repeat old EOS/comparator loops. Even positive early wrapper does NOT prove selected Track+Album/edition/duration/generation or CELIKOM entitlement/alternate music.

Details [NAV30 owner phone and NAV31 exact holder-select lifecycle](ANDROID-A1-NAV30-OWNER-PHONE-MISSING-WRAPPER-NAV31-SELECT-20261118.md).

---

# ARCHIVED — NAV30 SIGNED ARM13 GREEN, PERSONAL LIBRARY READBACK VERIFIED; OWNER PHONE TXT NEXT (18 NOV 2026)

**Only:** CELIKOM Android A1, `manufact-test/nomusic`, sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Original Yandex audio untouched. **CELIKOM_REPLACEMENT=NOT_CONNECTED** (no connected replacement source, no audible alternative). Do NOT invent user playback/seek/Next defects; owner phone NAV29 did not prove any new crash. Never ask owner to uninstall/clear data; signed APK download must be via personal ChatGPT Library, not sandbox or GitHub Actions.

**NAV29 real owner phone:** PRIVATE `CELIKOM-A1-Diagnostics-1794995459271.txt`, raw TXT never committed. Active export `NAV_V29_TRACK_SOURCE_ACTIVE_PERIOD_READONLY`, previous NAV28 marker in old retained lines. New `TRACK_PLAYER_SOURCE_SCOPE`, `NATIVE_PLAYER_SOURCE_SETTER`, `LIVE_PERIOD_ORIGINAL_SOURCE` all REGISTERED; same synchronous TrackWrapper-to-original Player-source context `TRACK_PLAYER_SOURCE_SAME_SCOPE=FEW`, UNSCOPED=NONE, CONFLICT=NONE. Previously owner-confirmed live renderer `LIVE_QUEUE_SLOT_B_ATTACH_MATCH=FEW`, `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY` and no OTHER/UNAVAILABLE. **But** `LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED=NONE` / `LIVE_PERIOD_ORIGINAL_SOURCE_UNAVAILABLE=MANY`, all `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_*=NONE`. No selected source proven. Old `IDENTITY_STATUS=STRUCTURAL_ONLY`, Stage B still `NOT_CONNECTED`. Do not infer crash from `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/FEW` or historical user-requested exit-info.

**NAV30 strict read-only follow-up:** separately classifies exact unavailable reason `LIVE_PERIOD_HOLDER_WRAPPER_MISSING`, `LIVE_PERIOD_WRAPPED_PERIOD_MISSING`, `LIVE_PERIOD_WRAPPED_NON_LO96`, `LIVE_PERIOD_DIRECT_LO96`, `LIVE_PERIOD_ADAPTER_UNMAPPED/MAPPED`, `LIVE_PERIOD_SOURCE_NULL`, `LIVE_PERIOD_REFLECTION_FAILED`. Optional hooks only on exact already signed-native `Lp96.goto(...):Lwh6` and `Lp96.transient(...):Lo96`. Captures one factory `Lo96` and original returned `Lwh6` within same receiver/thread frame. **Critically fixed after first NAV30 iteration:** matching *time/frame alone is NOT identity*. Retains weak link ONLY when original return is identical Java reference to factory `Lo96`, or original return is the **exact previously publisher-verified `Lup1` wrapper** whose signed exact `Lwh6` field equals the same factory `Lo96` by Java `==`. Unrelated factory/adapter, duplicate results, weak ref loss, stale queue, detached renderer NEVER match. Same original `e.h.SLOT_B`+renderer/stream type=1,state=2 guard must succeed before any source observation. Bounded finite counters only; no private field names, track IDs, metadata, tokens, URLs or audio data exported, and original vendor calls/results unchanged. Even future positive match is *only original source object equality*, not selected Album/edition/duration/generation or substitute audio.

**Exact signed NAV30 immutable code:** `e96066a33b2386f84208da7b0affa24c59b2b6d9`; previous in-progress NAV30 `f4c5601...` superseded by this tighter source. JVM strict positive/negative fixture `#44281341168 SUCCESS` at exact final code. Owner signed publisher-first native Android13 ARM13 `#44281341301 SUCCESS` on the SAME code SHA, final verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO` (publisher and clone stable; NOT a real phone/audio acceptance test). All 16 publisher-signed original 2025.10.4 splits and private exact fields verified in CI. Artifact ID `14417566955`; CI ZIP bundled stale README, don't share the ZIP.

**Verified owner APK:** `CELIKOM-A1-NAV30-Native-Period-Adapter-ReadOnly-20261118.apk`, **71,483,372 bytes**, SHA-256 `c51557a09f620f41d10825193453dc37b505cfb83f1cd191540cc635c90a3a9a` exactly matches job. Independently extracted v2 and v3 APK signing block DER cert SHA-256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` (same NAV29 owner signer, CI owner_apk_signer_verified=true). Embedded original `assets/lspatch/origin.apk` unchanged SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Extracted own nested module DEX has actual `NAV_V30_NATIVE_PERIOD_ADAPTER_READONLY` marker, new counters and exact private period target.

**PERSONAL ChatGPT Library (both uploaded, listed, materialized back and BYTE-IDENTICAL verified):**
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV30-Native-Period-Adapter-ReadOnly-20261118.apk` (71,483,372 bytes, SHA above).
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV30-Инструкция.txt` (2,839 bytes, SHA-256 `c7833be5545224be0e2cfdf97509377b4235a4b198569d8ef25856713c947543`).
Old NAV29/NAV28 Library APKs and signed originals preserved. **Never substitute Actions download, direct sandbox, stale ZIP README.**

**Backups:** pre-NAV30 NAV29 real phone `backup/android-a1-nav29-owner-phone-period-unavailable-pre-nav30-20261118` @ `7388390b9b329ba3fead134450e2fc836040d2bf`. Exact signed NAV30 final `backup/android-a1-nav30-exact-wrapper-ref-owner-arm13-ci-green-20261118` @ `e96066a33b2386f84208da7b0affa24c59b2b6d9`. Last HEAD after signed code is docs-only. Documentation [NAV29 owner evidence + NAV30 signed release](ANDROID-A1-NAV29-OWNER-PHONE-UNAVAILABLE-NAV30-ADAPTER-20261118.md).

**NEXT OWNER TEST:** install NAV30 Library APK **OVER NAV29**, without uninstall or data/cache clear. If Android refuses upgrade, STOP and preserve NAV29. Play 2–5 ordinary songs, export new PRIVATE TXT. Check active NAV30 marker and registration of `NATIVE_PERIOD_ADAPTER`, `NATIVE_PERIOD_FACTORY`; breakdown `LIVE_PERIOD_HOLDER_WRAPPER_MISSING/WRAPPED_PERIOD_MISSING/WRAPPED_NON_LO96/DIRECT_LO96/ADAPTER_MAPPED/ADAPTER_UNMAPPED/SOURCE_NULL/REFLECTION_FAILED` and `NATIVE_PERIOD_*_IN_SCOPE/LINK_CREATED/CONFLICT`, plus old live slot, source scoped and final `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_*`. A positive match is NOT an automatic go for audio swapping — still selected Track+Album/edition/duration/generation and existing authorized CELIKOM entitlement needed.

---

# ARCHIVED — NAV29 OWNER PHONE LIVE PERIOD SOURCE UNAVAILABLE; NAV30 BOUNDED ADAPTER ALIAS IN OWNER CI (18 NOV 2026)

**Only:** CELIKOM Android A1, repo `manufact-test/nomusic`, sole branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; no architecture changes, no original vendor media modification, no metadata/account/audio byte export. CELIKOM replacement **NOT_CONNECTED**. Never claim a playback bug not reported; user wants autonomous completion, signed APK via **personal ChatGPT Library**, never Actions/sandbox direct links.

**Latest owner's actual private NAV29 diagnostics:** `CELIKOM-A1-Diagnostics-1794995459271.txt`, never copy raw TXT to GitHub. File retains historical NAV28 marker in prior log (line 21) but NEW active `NAV_V29_TRACK_SOURCE_ACTIVE_PERIOD_READONLY` at capture line 235 and current summary line 525. New hooks `TRACK_PLAYER_SOURCE_SCOPE`, `NATIVE_PLAYER_SOURCE_SETTER`, `LIVE_PERIOD_ORIGINAL_SOURCE` all REGISTERED. `TRACK_PLAYER_SOURCE_SCOPE_ENTER=FEW`, `TRACK_PLAYER_SOURCE_SAME_SCOPE=FEW`, UNSCOPED=NONE, CONFLICT=NONE: **real current native original source setter was observed within same TrackWrapper owner-frame**. Previous phone NAV28 queue/audio proof persists: `LIVE_QUEUE_SLOT_B_ATTACH_MATCH=FEW`, `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`; OTHER/UNAVAILABLE=NONE; `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW`, `ENGINE_HOLDER_TYPE1_STATE2=MANY`, `READ_RETURN_LINK_LOST=NONE`.

**Actual blocker:** `LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED=NONE`, `LIVE_PERIOD_ORIGINAL_SOURCE_UNAVAILABLE=MANY`. Therefore new source-to-active-period identity was NOT proven; `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH/OTHER/NO_LINK=NONE`; `IDENTITY_STATUS=STRUCTURAL_ONLY`, CELIKOM replacement NOT_CONNECTED. NAV29 collapsed all reasons under UNAVAILABLE. Exact private fields registered, but runtime holder's `Lup1`-held `Lwh6` may be non-`Lo96`, or holder/wrapper/source missing or reflection exception; do not assert which cause before NAV30 bins. No audio regression proven from METRICA_EXCEPTION summary; historical ANDROID_EXIT_INFO USER_REQUESTED ≠ automatic crash.

**Saved pre-NAV30 owner evidence:** `backup/android-a1-nav29-owner-phone-period-unavailable-pre-nav30-20261118` @ `7388390b9b329ba3fead134450e2fc836040d2bf`. Existing signed NAV29 `backup/android-a1-nav29-active-track-source-period-owner-arm13-ci-green-20261118` @ `bef2e523d063bb90cd0606e7041716ed4c45eb11`, owner NAV29 personal Library APK unchanged. Old NAV28 accepted Library build unchanged.

**NAV30 read-only continuation** (no new source replacement): first code `dc2939decedfe2af0839a99b65beeb6e24956ac2`, exact hooked source `f4c5601eeeea525d14fe33c52d189db60a8209d8`. Keep the NAV29 source-to-player and NAV28 live queue/render guard. Add finite privacy-safe phase reason counters `LIVE_PERIOD_HOLDER_WRAPPER_MISSING`, `LIVE_PERIOD_WRAPPED_PERIOD_MISSING`, `LIVE_PERIOD_WRAPPED_NON_LO96`, `LIVE_PERIOD_DIRECT_LO96`, `LIVE_PERIOD_SOURCE_NULL`, `LIVE_PERIOD_REFLECTION_FAILED`. **One narrow optional original-source alias** for `Lp96.goto(...):Lwh6` + `Lp96.transient(...):Lo96`: when exact same owner receiver's factory returned exactly one original `Lo96` within synchronous `goto` frame, weak-map only the returned original `Lwh6` object reference to that original `Lo96`; count `NATIVE_PERIOD_ADAPTER_SCOPE_ENTER`, `NATIVE_PERIOD_FACTORY_IN_SCOPE`, `NATIVE_PERIOD_ADAPTER_LINK_CREATED` and `LIVE_PERIOD_ADAPTER_MAPPED/UNMAPPED`. Original calls always proceed once; conflict, null, GC, stale/changed queue, detach fail closed; no IDs, source values or media. This can only bridge **exact original reference equality**, never infer Track/Album/edition/decoder/entitlement. All old categories retained.

**CI:** NAV30 JVM exact model `#44280642232 SUCCESS`; signed original publisher-first Android13 ARM13 `#44280642191` **in progress** at documentation time; do not claim release until success, actual owner certificate v2/v3 and original pinned hash verified, user-approved signer, Library upload + independently listed + materialized byte-identical. Old signed NAV29 and NAV28 Library APKs preserved.

**Next:** verify NAV30 signed CI; if success upload owner APK and fresh Russian NAV30 instruction in personal ChatGPT Library and provide Library file entries. Owner then installs over NAV29 without uninstall/data/cache wipe, listens 2–5 ordinary songs, exports TXT. Need see explicit unavailable phase and/or original adapter match. A MATCH alone is still not selected Track+Album/edition/duration/generation or permission to swap audio. Do not repeat NAV25 EOS, NAV26 comparator or broad generic MediaItem scans. For detail see [NAV29 phone unresolved & NAV30 adapter](ANDROID-A1-NAV29-OWNER-PHONE-UNAVAILABLE-NAV30-ADAPTER-20261118.md).

---

# ARCHIVED — NAV29 OWNER-SIGNED ARM13 GREEN + VERIFIED PERSONAL LIBRARY; OWNER PHONE TXT NEXT (18 NOV 2026)

**Scope:** only CELIKOM Android A1 `manufact-test/nomusic`, only branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Do not restart architecture, change original publisher Yandex, touch Windows/browser/backend/credentials, or invent playback bugs. CELIKOM alternative-audio replacement still **NOT_CONNECTED**, all new hooks strictly read-only.

**Latest REAL OWNER PHONE proof is NAV28, NOT NAV29:** private `CELIKOM-A1-Diagnostics-1794993804107.txt`, never commit/upload. The actual export snapshot `NAV_V28_LIVE_QUEUE_SLOT_B_RENDERER_READONLY;ACTIVE` (older NAV26/NAV27 markers retained historically). `LIVE_QUEUE_SLOT_B=REGISTERED`, `LIVE_QUEUE_SLOT_B_ATTACH_MATCH=FEW`, `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`, OTHER/UNAVAILABLE=NONE at both attach and read, `READ_RETURN_LINK_LOST=NONE`, `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW`, `ENGINE_HOLDER_TYPE1_STATE2=MANY`. Thus same live `e.h.SLOT_B` holder ↔ active original type1/state2 renderer+stream is **verified on phone**, NOT just static; it still DOES NOT prove selected Track/Album/edition, decoded PCM or substitute audio. Original comparator FALSE=MANY this session but strict comparator-to-audio read remains NONE; do not use comparator as mandatory condition. Stage B `TRACK_WRAPPER_ALBUM_LINK=MANY`, `WRAPPER_MAIN_SOURCE=NONE`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/FEW` is an exception-constructor summary, not a verified playback crash. Old owner NAV28 Library APK remains accepted and untouched.

**NAV29 new read-only witness:** From exact issuer-signed 2025.10.4 DEX original private fields, observes `LcA9.extends(...LtCa...)` TrackWrapper within same frame as native Player `d.e(LSl6;J)` source setter (only weak reference equality, source conflicts fail closed). Only when NAV28 current live-slot plus same started audio renderer/holder/stream proof succeeds, reads original `Lxh6.Object → Lup1.Lwh6 → Lo96.LSl6` field chain and categorizes SAME/OTHER/NO_LINK versus scoped native original source. Does not log private field names, source, media/title/IDs/URLs/tokens/audio; no method results changed, no substitution. New categories `TRACK_PLAYER_SOURCE_SCOPE/SAME_SCOPE/UNSCOPED/CONFLICT`, `LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED/UNAVAILABLE`, `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH/OTHER/NO_LINK`. Even a positive MATCH would *only* establish active original source object matched selected-side wrapper source; still need strict selected Track+Album/edition/duration/generation and grants.

**SIGNED CI PASS:** Java JVM strict evidence regression `#44276987119 SUCCESS`. Signed original publisher-first Android13 ARM13 owner `#44276987005 SUCCESS` at exact source commit `bef2e523d063bb90cd0606e7041716ed4c45eb11`. Cryptographically verified all 16 original signed 2025 XAPK splits; exact private source/period field derivation `NAV29_PUBLISHER_SIGNED_TRACK_TO_ACTIVE_PERIOD_PRIVATE_FIELDS_PASS` in CI logs. Original publisher app and native clone run side-by-side; verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`, this is NOT acoustic replacement proof. CI ZIP artifact `14415731780` contains APK but a stale generic README: **do not deliver ZIP or its README**, use fresh NAV29 Library instruction.

**Owner APK VERIFIED:** `CELIKOM-A1-NAV29-Active-Track-Source-Period-ReadOnly-20261118.apk`, 71,479,276 bytes, SHA256 **`bd48d0225e9667a0a34212a788d949a634f2a7c570a825181cbb35db3a2894cc`**. Actual v2/v3 APK signer certificate SHA256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`, same NAV28 owner certificate and `owner_apk_signer_verified=true` in CI. Unmodified embedded publisher Yandex `assets/lspatch/origin.apk` SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Independently extracted nested own module DEX and confirmed NAV29 diagnostic marker, new counters and private exact original period target.

**PERSONAL ChatGPT Library (both uploaded, separately listed, downloaded back & BYTE-BY-BYTE VERIFIED):**
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV29-Active-Track-Source-Period-ReadOnly-20261118.apk` (SHA above).
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV29-Инструкция.txt` (2,611 bytes, SHA256 `c85982afce6b032af866440c3dfe7faccf7c1b145d449dbffffa5e455ac28fce`).
**Download must be Library entry/card**, never sandbox or GitHub Actions URL. Old NAV28/NAV27 Library APKs preserved.

**Protected source:** pre-NAV29 real owner NAV28 `backup/android-a1-nav28-owner-phone-live-slot-read-match-pre-nav29-20261118` @ `6603fefee19b1d7be319901998d8eae441e6786a`; EXACT SIGNED NAV29 `backup/android-a1-nav29-active-track-source-period-owner-arm13-ci-green-20261118` @ `bef2e523d063bb90cd0606e7041716ed4c45eb11`. Working HEAD after signed source has docs only; preserve backup and old signed builds.

**NEXT owner action:** install NAV29 from personal Library **ON TOP of NAV28**, NO uninstall or data/cache clear. If Android declines update, stop and preserve NAV28. Listen 2–5 ordinary songs, export private TXT. Need not repeat seek/pause testing; no owner-reported issues there. Analyze ACTIVE `NAV_V29_TRACK_SOURCE_ACTIVE_PERIOD_READONLY`, new hook statuses, counters `TRACK_PLAYER_SOURCE_*`, `LIVE_PERIOD_*` and old live slot/type1 state2/read link, plus replacement. **No NAV29 owner-phone result yet**. If strict source match positive, next gate selected Track/Album/edition/duration/queue generation and existing authorized CELIKOM resolver/entitlement before any source swap.

Detailed evidence: [NAV28 owner real phone + NAV29 signed and personal Library](ANDROID-A1-NAV28-OWNER-LIVE-QUEUE-POSITIVE-NAV29-ACTIVE-SOURCE-20261118.md).

---

# ARCHIVED — NAV28 OWNER PHONE LIVE QUEUE/STARTED AUDIO MATCH; NAV29 TRACK SOURCE TO ACTIVE PERIOD IN CI (18 NOV 2026)

**Scope:** CELIKOM Android A1 ONLY, `manufact-test/nomusic`, sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Keep original Yandex behavior, original publisher signed 2025.10.4 unchanged, no unauthorized audio switching. Original playback last reported working; do not invent pause/seek/Next defects. CELIKOM audio substitution **NOT_CONNECTED**. User expects personal ChatGPT Library files, not sandbox/GitHub Actions download.

**Actual owner NAV28 TXT received and analyzed:** `CELIKOM-A1-Diagnostics-1794993804107.txt` (PRIVATE; NEVER commit raw). Earlier retained log contains NAV26/NAV27 build markers; **CURRENT** near file line 936 `NAV_V28_LIVE_QUEUE_SLOT_B_RENDERER_READONLY;ACTIVE`. Key NAV28 phone snapshot:
- `LIVE_QUEUE_SLOT_B=REGISTERED`, `ENGINE_HOLDER_SCOPE=REGISTERED`, `RENDERER_TYPE_STATE_ACCESS=REGISTERED`, others original renderer hooks REGISTERED, `BUFFER_EOS_ACCESS=NO_HOOK` unchanged.
- `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW` with DIFFERENT=NONE, UNAVAILABLE=NONE; live queue at attach `LIVE_QUEUE_SLOT_B_ATTACH_MATCH=FEW`, OTHER=NONE, UNAVAILABLE=NONE.
- **`LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH=MANY`**, OTHER=NONE, UNAVAILABLE=NONE, MINUS4=MANY. **Real phone current live e.h.SLOT_B holder == active type1/state2 renderer/stream holder identity at sampled original audio reads**. This closes live queue-slot vs active renderer *structural* gate, not current Track+Album+edition, PCM or source substitution.
- `READ_RETURN_LINK_LOST=NONE`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH=MANY`, `ENGINE_HOLDER_TYPE1_STATE2=MANY`, `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4=MANY`. Existing alternate helper QUEUE_SCOPE_ENTER=NONE does not negate independent exact engine route.
- Original comparator this session FALSE=MANY, at-call engine MATCH=MANY, attached stream MANY but strict comparator-to-later started read NONE; comparator not required for NAV29, raw FALSE semantics not inferred. Prior NAV27 session comparator NONE, correct session-specific observation.
- Stage B selected source path: FLOW_TRACK_SAME_OBJECT=FEW, TRACK_WRAPPER_LINK=MANY, TRACK_WRAPPER_ALBUM_LINK=MANY; `WRAPPER_MAIN_SOURCE=NONE`, `NATIVE_MAIN_SOURCE_ENTER=NONE`, `TRACK_SOURCE_READ_LINK=NONE`. These are prior source-chain holes; do not pretend resolved. `CELIKOM_REPLACEMENT=NOT_CONNECTED`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/FEW` says only sampled exception constructors; no proven new user-visible playback crash.

**Protected before NAV29:** `backup/android-a1-nav28-owner-phone-live-slot-read-match-pre-nav29-20261118` @ `6603fefee19b1d7be319901998d8eae441e6786a`. NAV28 exact signed code backup `backup/android-a1-nav28-live-queue-slot-owner-signed-arm13-ci-green-20261118` @ `4463297d81e5476fb1f3b2724391127b076b4828`; NAV28 user-verified Library APK untouched.

**NAV29 read-only proposed gate:** Use already publisher-signed proven `LcA9.extends(...LtCa...)` TrackWrapper → exact `LiLb` source → native Player `d.e(LSl6;J)` same-original-object, and `Lp96.transient` Lo96 original source, `Lxh6` holder-stored exact `Lup1` wrapper. The current NAV28 live e.h.SLOT_B holder→renderer/stream match is the ONLY time the new proof can count. New Stage B hooks/counters (no metadata/files/track IDs/tokens/URLs or audio bytes):
- `TRACK_PLAYER_SOURCE_SCOPE_ENTER`, `TRACK_PLAYER_SOURCE_SAME_SCOPE/UNSCOPED/CONFLICT`: bounded weak TrackWrapper–original source link only when exact synchronous source setter in precise TrackWrapper-bearing original method. A source belonging to two wrappers is conflicted, never promoted.
- `LIVE_PERIOD_ORIGINAL_SOURCE_RESOLVED/UNAVAILABLE`: exact original `Lxh6.Object → Lup1.Lwh6 → Lo96.LSl6` fields from cryptographically verified signed original, only on NAV28 live slot audio sample.
- `LIVE_PERIOD_TRACK_WRAPPER_SOURCE_MATCH/OTHER/NO_LINK`: strict Java reference equality between original active period source and previously observed scoped player original source. This is a **source object match**, not Track/Album edition or correct audible CELIKOM substitution.
- New hook status `TRACK_PLAYER_SOURCE_SCOPE`, `NATIVE_PLAYER_SOURCE_SETTER`, `LIVE_PERIOD_ORIGINAL_SOURCE`; optional if any exact field cannot be proven/loaded; no fallback to weaker. Original methods unchanged, fail closed.

**Source:** new owned Java model and three JVM negative/positive fixtures commit `b6b8442f5dcc285f6f0e626b5d2dbd6cd0d91660`. New owner hooks and exact publisher-private signed field generator and NAV29 CI workflow commit `bef2e523d063bb90cd0606e7041716ed4c45eb11`. NAV29 model JVM CI **#44276987119 SUCCESS**. Original issuer XAPK full ARM13 signing/functional CI **#44276987005 IN PROGRESS** at handoff drafting; do NOT claim signed owner APK, and do NOT send user to install unless native CI SUCCESS, read-only module marker and cryptographic signer & original verified, personal Library upload independently listed & materialized back byte-identical. If source generator exact field proof fails, do not bypass; use static DEX to fix the exact gap or mark NO_GO.

**Next:** Continue NAV29 ARM CI; resolve fail-closed static proof issues only, do not replace vendor audio and do not ask owner for another TXT until verified Library NAV29 release. Then owner can install over NAV28 without clearing data and send NAV29 TXT. Selected Track, Album, edition, duration and queue generation still need explicit same-lineage proof; only after that connect authorized CELIKOM resolver and source swap. Docs: [NAV28 owner + NAV29 exact-source gate](ANDROID-A1-NAV28-OWNER-LIVE-QUEUE-POSITIVE-NAV29-ACTIVE-SOURCE-20261118.md).

---

# ARCHIVED — NAV28 OWNER-SIGNED ARM13 GREEN AND PERSONAL LIBRARY VERIFIED (18 NOV 2026)

**Only** CELIKOM Android A1, GitHub `manufact-test/nomusic`, branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Original Yandex Music works by earlier owner reports; NO NEW owner playback bug reported. CELIKOM replacement **NOT_CONNECTED**. No architecture changes, vendor modifications or user account/credentials logged.

**NAV27 owner's phone:** private `CELIKOM-A1-Diagnostics-1794991540152.txt` (never commit). NAV27 ACTIVE marker at export; comparator hook REGISTERED but TRUE/FALSE/UNAVAILABLE and all NAV27 timing bins NONE *this session*; NAV26 previously FALSE=MANY on a separate session. Engine-holder stream equality FEW, active type1/state2 sampled reads MANY, READ_RETURN_LINK_LOST=NONE; IDENTITY_STATUS STRUCTURAL_ONLY. Comparator is not a reliable mandatory selected-track gate.

**NAV28:** the already signed original 2025.10.4 CFG proof uniquely anchors h.SLOT_B and e.catch holder. New read-only NAV28 checks exact live `e.h.SLOT_B==holder` at renderer attach and checks again during original type1/state2 sample read; reports MATCH/OTHER/UNAVAILABLE separately. Stale, detached, changed slot never promotes. This is **only** live queue-slot identity, NOT selected song/album/edition, audible PCM, or working CELIKOM substitution. Original vendor method/return and audio unchanged. Signed-original private DEX generates exact field name in ephemeral CI only; if runtime e→h field ambiguous/missing, new hook fails closed with NO_HOOK while prior audio observer works.

**Signed source / checks:** JVM #44271011147 SUCCESS; native Android13 ARM13 owner signed publisher-first #44271711454 SUCCESS, exact checked source `4463297d81e5476fb1f3b2724391127b076b4828`. CI signed original 16 splits, verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`; NAV28 private exact field derivation PASS. APK 71,475,180 bytes, SHA-256 **`d336ee0d616c809cfa8017e24a489ba6a2e5f0285407595811807efc43479943`**. APK v2/v3 certificate SHA256 independently extracted and CI-verified owner signer `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` (same NAV27). Embedded original Yandex `assets/lspatch/origin.apk` SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. Own nested module DEX contains NAV28 marker and new exact queue categories. CI artifact #14412264159 downloaded and privately verified; do NOT give Actions link.

**Personal ChatGPT Library — both uploaded, listed, read back and byte-compared:**
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV28-Live-Queue-Slot-B-ReadOnly-20261118.apk` (SHA above).
- `/CELIKOM/Android/Native/CELIKOM-A1-NAV28-Инструкция.txt`, 2507 bytes, SHA256 `e891d667d504c4c185fef3a7d8c68643735d3737b44d27434c8c23d1bff25206`.
**Use Library entries/cards, not sandbox/GitHub Actions.** NOTE: raw CI ZIP bundled **stale NAV24** generic README; DO NOT share it. Correct NAV28 owner instructions are in Library.

**Backups:** pre-NAV28 real-phone NAV27 `backup/android-a1-nav27-owner-phone-comparator-no-calls-pre-nav28-20261118` @ `aa32602e87d216afbfcfd5d83c731147464d58cb`. Exact signed NAV28 code `backup/android-a1-nav28-live-queue-slot-owner-signed-arm13-ci-green-20261118` @ `4463297d81e5476fb1f3b2724391127b076b4828`. Older accepted NAV26/NAV27 APKs in Library unchanged.

**NEXT phone step:** install NAV28 **OVER NAV27** WITHOUT uninstall/clear data or cache; if Android rejects, stop and preserve NAV27. Listen to 2–5 ordinary songs, export TXT; no special pause/seek bug testing. Analyze ACTIVE NAV28 marker; `LIVE_QUEUE_SLOT_B` hook REGISTERED/NO_HOOK, attach MATCH/OTHER/UNAVAILABLE, type1/state2 read MATCH/OTHER/UNAVAILABLE/MINUS4, engine-holder and read return, IDENTITY_STATUS, CELIKOM_REPLACEMENT. No selected Track/queue generation or Album/edition proof yet. Next after phone evidence: connect current selected Track→queue generation→Album edition to exact active audio renderer before resolver/entitlement. Do not repeat NAV25 EOS or NAV26 comparator-only loops.

[Details of NAV27 owner evidence and NAV28 signed/Library release](ANDROID-A1-NAV27-OWNER-PHONE-NO-COMPARATOR-NAV28-LIVE-QUEUE-SLOT-20261118.md).

---

# ARCHIVED — NAV27 OWNER PHONE PARSED; NAV28 LIVE QUEUE SLOT READ-ONLY CI COMPLETED (18 NOV 2026)

**Project:** CELIKOM Android A1 ONLY; sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112` in `manufact-test/nomusic`. Do not restart/rebase or change architecture. The owner original Yandex playback is known-good from earlier reports; no new pause/seek/Next bug was reported. CELIKOM replacement **NOT_CONNECTED**, no active substitution.

**Latest owner private diagnostics:** `CELIKOM-A1-Diagnostics-1794991540152.txt` (NAV27). Raw TXT remains private, NEVER commit/copy to GitHub. Although retained log includes old NAV26 marker, **current build marker** at export is `NAV_V27_COMPARATOR_ATTACH_PHASE_DISCRIMINATOR_READONLY;ACTIVE`. All eight audio hooks including comparator REGISTERED, `LIVE_QUEUE_SLOT_B` is NAV28 and not yet on owner phone.

**NAV27 real phone key:** `RENDERER_COMPARATOR_TRUE=NONE`, `FALSE=NONE`, `UNAVAILABLE=NONE`, all new `COMPARATOR_AT_CALL_*` and `COMPARATOR_CLEARED_ATTACH_*` = NONE. NO comparator call observed **in this session**; this does not contradict prior NAV26 `FALSE=MANY` in its different session. Existing `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW`, `ENGINE_HOLDER_TYPE1_STATE2=MANY`, `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4=MANY`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH=MANY`, `READ_RETURN_LINK_LOST=NONE`, no buffer EOS accessor, `IDENTITY_STATUS=STRUCTURAL_ONLY`, replacement NOT_CONNECTED. Comparator is not dependable as a mandatory runtime gate. Explicit screen logs alone do not establish a new crash; avoid claiming playback regression.

**NAV28 scoped response:** before writing, protected NAV27 phone evidence in `backup/android-a1-nav27-owner-phone-comparator-no-calls-pre-nav28-20261118` @ `aa32602e87d216afbfcfd5d83c731147464d58cb`. Own read-only `NativeRendererStreamEvidence` now requires exact live `e.h.SLOT_B==holder` at renderer attach, and checks the same field AGAIN at started type1/state2 audio read with same renderer/stream. Distinguishes MATCH/OTHER/UNAVAILABLE; does not promote stream to selected track, album/edition, PCM or entitlement. If live slot switches, previous snapshot not promoted. Attach/detach fail closed; original vendor calls/results unchanged, no audio modification. New exact field name derived only from signed issuer original 2025.10.4 16 splits and prior branch-sensitive proven PC547 / e.break PC1051→1183 and e.class PC2→51, generated Java in ephemeral CI; if original changes or engine queue field ambiguous, observer NO_HOOK only (old renderer hook retained).

**NAV28 code:** `36c5433fc7160eeb38fbcb20eafc41d62fadd0ac` (owned model + JVM fixtures); `6146b72f027b924b37febb25ea02fbc6b92a0da1` (owned hook/CI private XAPK field source & signed ARM workflow); `161c4071d2ca07a1094e1b707e6eab8d63c154cd` (private-generator regex and Java newline fix); `e647078188fcc9985e01ccd62161815d7fce62e3` (retrigger latest exact workflow). NAV28 JVM CI `#44271011147 SUCCESS` at first NAV28 source; private original + signed ARM13 NAV28 run `#44271273776` **IN PROGRESS at this note**. **Do not ship unverified APK**, do not send Actions or sandbox link. Need signed-run SUCCESS, owner certificate same NAV27, publisher original same SHA256, file SHA, upload to PERSONAL ChatGPT Library, list+materialize+byte compare; only then owner phone test, no uninstall/data clear.

**Interpret next NAV28 owner TXT:** status `LIVE_QUEUE_SLOT_B`; `LIVE_QUEUE_SLOT_B_ATTACH_MATCH/OTHER/UNAVAILABLE`, `LIVE_QUEUE_SLOT_B_TYPE1_STATE2_READ_MATCH/OTHER/UNAVAILABLE/MINUS4` plus prior engine holder, stream alias, read link and replacement. These prove only live SLOT_B alias at a bounded sample, *not selected Track/Album/edition* or audible CELIKOM content; next step is exact current selected Track+queue generation, album/edition, then existing resolver/entitlement. Do not repeat NAV25 failed EOS getter or NAV26/27 comparator loop. Protect old NAV26, NAV27 signed APKs in Library, backups.

**Source detail:** [NAV27 owner result and NAV28 exact queue probe](ANDROID-A1-NAV27-OWNER-PHONE-NO-COMPARATOR-NAV28-LIVE-QUEUE-SLOT-20261118.md).

---

# ARCHIVED — NAV27 SIGNED ARM13 + VERIFIED PERSONAL LIBRARY; OWNER PHONE TXT RECEIVED (18 NOV 2026)

**Latest state / DO NOT restart studies:** Only Android A1 in `manufact-test/nomusic`, sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Original Yandex Music 2025.10.4 works normally by previous owner reports; no user-reported pause/seek/Next bug. CELIKOM alternative-audio replacement **NOT_CONNECTED**. Read [NAV26 real-phone false comparator / NAV27 phase diagnostic and final signed release](ANDROID-A1-NAV26-OWNER-PHONE-FALSE-COMPARATOR-NAV27-PHASE-20261118.md) first.

**NAV26 owner real-phone diagnostic analyzed:** private `CELIKOM-A1-Diagnostics-1794990212006.txt`, never commit raw file. Actual NAV26: `RENDERER_COMPARATOR=REGISTERED`, `FALSE=MANY`, `TRUE=NONE`, `UNAVAILABLE=NONE`. Both strict comparator to later started-audio read result categories TRUE/FALSE = NONE. Independent same holder→stream engine link FEW and type1/state2 read MANY remain; `READ_RETURN_LINK_LOST=NONE`, `IDENTITY_STATUS=STRUCTURAL_ONLY`, replacement NOT_CONNECTED. FALSE semantics remain uninterpreted.

**NAV27 release completed:** new READ-ONLY comparator/attach phase counters in owned module; original comparator executed once unchanged, no audio swap, metadata or credential collection. Exact JVM `#44267549038 SUCCESS`; exact owner-signed Android13 ARM `#44267549027 SUCCESS` at `b287492d600c8b01ac32a0401c5e61db2d9b63c1`. Signed APK 71,475,180 bytes, SHA-256 `a051e795c9123447018ece88b6dc88d2e69e736177d001d60e289c8c47e314ab`. Owner signer v2/v3 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` matches NAV26. Embedded publisher original Yandex APK `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. The NAV27 build marker and new counter names independently confirmed inside module DEX. GitHub Actions ZIP artifact ID `14411526799` analyzed; **owner APK and matching instructions uploaded to personal ChatGPT Library, separately listed, materialized back and SHA-256/byte-comparison verified**.

**Canonical personal Library entries:** `/CELIKOM/Android/Native/CELIKOM-A1-NAV27-Comparator-Attach-Phase-ReadOnly-20261118.apk` and `/CELIKOM/Android/Native/CELIKOM-A1-NAV27-Инструкция.txt`. Use Library entry/card for owner download, NO GitHub Actions URL or sandbox link. Owner next installs NAV27 directly **over NAV26**, NO uninstall/data clear. If signer/update rejected, STOP; preserve NAV26. Listen to 2–5 ordinary tracks, export TXT with in-app button; no special pause/seek/Next tests. Old accepted APKs remain in Library. NAV27 is NOT yet tested on owner's phone.

**New NAV27 summary bins:** `COMPARATOR_AT_CALL_ENGINE_MATCH/ENGINE_OTHER/NO_ENGINE`, `COMPARATOR_AT_CALL_ATTACHED_STREAM/NO_ATTACHED_STREAM`, `COMPARATOR_CLEARED_ATTACH_SAME_TRIO/DIFFERENT_STREAM/DIFFERENT_HOLDER/UNSCOPED`. Analyze with older `RENDERER_COMPARATOR_TRUE/FALSE`, strict `ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE/FALSE`, `ENGINE_HOLDER_STREAM_ARRAY_MATCH`, `ENGINE_HOLDER_TYPE1_STATE2`, `READ_RETURN_LINK_LOST`, `IDENTITY_STATUS`, `CELIKOM_REPLACEMENT`. Same-trio before attach is only a lifecycle/alias witness, NOT proof of selected Track, queue generation, edition, audible PCM, or replacement.

**Backups:** pre-NAV27 NAV26 owner-phone baseline `backup/android-a1-nav26-phone-false-no-correlation-before-nav27-20261118` @ `2faf55dee641971c4d4e422b9e795942b4047476`; owner-signed NAV27 exact code backup `backup/android-a1-nav27-comparator-attach-phase-owner-ci-green-20261118` @ `b287492d600c8b01ac32a0401c5e61db2d9b63c1`. Future step after NAV27 phone evidence: ground *current selected* Track and queue generation → same Track/Album/edition → exact active audio renderer, then existing authorized CELIKOM resolver/entitlement path. Don't repeat static TrackWrapper chain or failed NAV25 EOS accessor; don't touch original Yandex, other platforms, or account/Passport contents.

---

# ARCHIVED — NAV26 OWNER PHONE FALSE COMPARATOR; NAV27 PHASE DIAGNOSTIC IN CI COMPLETED (18 NOV 2026)

**Read first:** [NAV26 real-phone comparator result and NAV27 exact phase observer](ANDROID-A1-NAV26-OWNER-PHONE-FALSE-COMPARATOR-NAV27-PHASE-20261118.md). Last owner private TXT `CELIKOM-A1-Diagnostics-1794990212006.txt` (NEVER commit raw TXT). Current NAV26 marker `NAV_V26_EXACT_LMQ8_RENDERER_COMPARATOR_OUTCOME_READONLY` ACTIVE. Original Yandex playback is owner-accepted; no newly reported playback defect. **Only missing product feature: CELIKOM replacement NOT_CONNECTED.**

**NAV26 real phone:** RENDERER_COMPARATOR REGISTERED; TRUE=NONE, FALSE=MANY, UNAVAILABLE=NONE. Both exact `ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE/FALSE` and `*_MINUS4`=NONE. Meanwhile `ENGINE_HOLDER_STREAM_ARRAY_MATCH=FEW`, no different/unavailable, `ENGINE_HOLDER_TYPE1_STATE2=MANY`, `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4=MANY`, `READ_RETURN_LINK_LOST=NONE`, `IDENTITY_STATUS=STRUCTURAL_ONLY`. FALSE is the original raw comparator result: no meaning inferred. An aggregate NONE on strict comparator-to-audio correlation is not a claim of broken playback.

**Narrow next gate justified by that phone evidence:** diagnostic phase relative to renderer attach. In NAV26, every attach deliberately invalidates earlier comparator weak references; thus the zero correlation may be timing, a different holder/stream, or another observer boundary — not yet known. NAV27 observes comparator-at-call engine/attached-stream cohorts and any comparator witness cleared on subsequent attach as distinct, privacy-safe finite counters. No payload, IDs, URLs, credentials or audio bytes. Existing comparator-to-started-read fail-closed gate unchanged. No source replacement, audio modifications, original app patches, or new architecture.

**Code & safeguards:** working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; signed, proven NAV26 observer/source `19c73c433eee23359566c3df2a3a0e5e52756b9c`; NAV26 owner APK SHA256 `1acd57a45dd025e144c4aaedfb43730b819806b1150eedff69274a3ae94d23a6` in verified personal Library. Protected pre-NAV27 phone-evidence backup `backup/android-a1-nav26-phone-false-no-correlation-before-nav27-20261118` @ `2faf55dee641971c4d4e422b9e795942b4047476`; NAV27 model/test/marker commit `e6988bb7bc73fa429d44a9e7ad0941b1ccba10cc`, CI-fixture/workflow correction `b287492d600c8b01ac32a0401c5e61db2d9b63c1`. NAV27 JVM #44267549038 **SUCCESS**; signed Android13 ARM NAV27 #44267549027 **RUNNING when written**. Not yet a release; do not send owner to install until exact signed CI success, hash/signer/original publisher Yandex verification, personal ChatGPT Library upload and byte-identical Library readback.

**After NAV27 real phone:** Interpret the phase bins, ground current selected Track+queue generation→Album→edition→actual renderer. Only then use existing authorized CELIKOM resolver/entitlement. Do not repeat NAV25 EOS probe or prior static chain. Do not touch account/Passport credentials, Windows, browser, server, Test.50.

---

# ARCHIVED — NAV26 SIGNED ANDROID13 ARM CI GREEN; OWNER PHONE TXT ALREADY RECEIVED (18 NOV 2026)

**Latest owner file:** private `CELIKOM-A1-Diagnostics-1794984522604.txt` (NAV25) analyzed; never commit raw TXT. Owner confirms ordinary original Yandex playback works normally. Only missing feature remains CELIKOM audio replacement.

**NAV26 is now built and released to the owner's personal Library.** Exact signed Android13 ARM CI **#44259704834 SUCCESS** at source/workflow HEAD `19c73c433eee23359566c3df2a3a0e5e52756b9c`; JVM regression CI **#44259704837 SUCCESS**. The CI artifact `CELIKOM-A1-NAV26-Owner-Renderer-Comparator-20261118` (#14406884183) was downloaded and inspected. APK SHA-256 `1acd57a45dd025e144c4aaedfb43730b819806b1150eedff69274a3ae94d23a6`, size 71,475,180 bytes. Owner signer SHA-256 `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` matches NAV25; embedded original publisher Yandex SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. APK independently listed and downloaded from personal Library; downloaded Library APK SHA-256 matches CI byte-for-byte. Canonical path: `/CELIKOM/Android/Native/CELIKOM-A1-NAV26-Renderer-Comparator-ReadOnly-20261118.apk`. A duplicate-safe `(1)` copy also exists; use the unsuffixed canonical entry. Instructions: `/CELIKOM/Android/Native/CELIKOM-A1-NAV26-Инструкция.txt`.

**NAV26 implementation:** exact signed `LmQ8.try(Lxh6,k)Z` comparator hook; original called once and boolean preserved unchanged. TRUE/FALSE recorded neutrally, never assume TRUE proves selected-track identity. Correlates only exact same weak holder/renderer/attached-stream references with later type1/state2 original renderer read. Detach and reattach invalidate old comparator evidence. No object values, metadata, account data, URLs or audio bytes exported. Passive diagnostics only; CELIKOM replacement remains **NOT_CONNECTED**.

**Next owner action:** install NAV26 over NAV25, do not uninstall or clear data. If Android refuses or signer mismatch appears, stop and do not remove NAV25. Open CELIKOM normally, listen to 2–5 ordinary tracks, export TXT. No special pause/seek/Next tests are needed. Original Yandex playback is known-good; do not invent playback defects. Analyze active NAV26 marker and `RENDERER_COMPARATOR`, `RENDERER_COMPARATOR_TRUE/FALSE/UNAVAILABLE`, `ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE/FALSE`, corresponding `*_MINUS4`, prior type/state/holder counters, `READ_RETURN_LINK_LOST`, and `CELIKOM_REPLACEMENT`.

**After phone evidence:** ground current selected Track + queue generation identity, then same Track → Album → edition/generation → active renderer. No source swap until exact identity is proved. Type1/state2 and comparator/read correlation alone do not prove selected song, album, edition, audible PCM or working replacement. Do not repeat static chain or NAV25 EOS accessor probe. Preserve original Yandex behavior and existing architecture.

**Code/checkpoints:** current working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`; verified working-branch HEAD when this handoff was resumed: `0d70b251985b8eafd49e54a8b5f2d36d26d0c159` (documentation-only handoff commit). NAV26 observer / signed APK source checkpoint `19c73c433eee23359566c3df2a3a0e5e52756b9c`. Saved owner-signed ARM backup ref `backup/android-a1-nav26-owner-signed-arm13-ci-green-pre-handoff-20261118` currently resolves to `9916ac13c6a862f9fbe485c281c141879164806f`; compared with the source checkpoint it contains only a 20-line JVM test-fixture hardening change and docs, not production-source changes. At handoff resumption, the working branch was three documentation-only commits ahead of this backup. NAV26 JVM-green backup `backup/android-a1-nav26-comparator-identity-guard-jvm-green-20261118`. Pre-NAV26 accepted NAV25 backup `backup/android-a1-nav25-owner-signed-library-verified-final-20261118`. Full detail: `docs/android/ANDROID-A1-NAV26-OWNER-COMPARATOR-REALPHONE-HANDOFF-20261118.md`.

**Read next:** this current section; then `ANDROID-A1-NAV26-OWNER-COMPARATOR-REALPHONE-HANDOFF-20261118.md`; then `ANDROID-A1-NAV25-OWNER-NAV24-REALPHONE-EOS-BOUNDARY-20261118.md`, `ANDROID-A1-NAV24-EXACT-AUDIO-RENDERER-STATE-20261118.md`, and `ANDROID-A1-NAV23-OWNER-REALPHONE-ENGINE-HOLDER-MATCH-20261118.md`. Do not commit raw owner TXT or inspect credential contents.
# ARCHIVED — NAV24 SIGNED, VERIFIED LIBRARY, OWNER PHONE TXT NEXT (18 NOV 2026)

**Do not restart or change the Android architecture.** The owner confirms ordinary original native Yandex Music works normally, including pause/seek/Next. Only missing feature is CELIKOM alternative audio replacement. **No playback bugs were reported.** Same only working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112` in `manufact-test/nomusic`.

**Read [NAV24 exact signed gate and release notes](ANDROID-A1-NAV24-EXACT-AUDIO-RENDERER-STATE-20261118.md) first.** The last actual phone TXT was NAV23 `CELIKOM-A1-Diagnostics-1794952135309.txt`; analyzed and documented in [NAV23 owner evidence](ANDROID-A1-NAV23-OWNER-REALPHONE-ENGINE-HOLDER-MATCH-20261118.md). NAV23 real phone confirmed `ENGINE_HOLDER_STREAM_ARRAY_MATCH=MANY`, `ENGINE_HOLDER_READ_RETURN_MINUS4=MANY`, other original return codes present; `IDENTITY_STATUS=STRUCTURAL_ONLY`, replacement NOT_CONNECTED.

**New signed 2025 static CI #44187962678 SUCCESS:** original `androidx.media3.exoplayer.b.default()I` is exact int field read of constructor `b.<init>(I)V` input (obfuscated `getTrackType`); `b.getState()I` exact int field read; unique engine `e.h` queue ref and exact same `h.SLOT_B` at `e.break PC547/1051` and `e.class PC2`. Avoid guessing generic `getTrackType` names. Existing queue holder→`e.catch` CFG CI #44185115155 SUCCESS.

**NAV24 change:** six new fail-closed JVM cases plus existing all, **JVM CI #44188648112 SUCCESS**. The original NAV23 read-only `b.g` hook now additionally reads original `b.default()` and `b.getState()` **after** `chain.proceed()`, only within the existing bounded sample budget. New summary bins are `ENGINE_HOLDER_RENDERER_TYPE1`, `ENGINE_HOLDER_RENDERER_TYPE_OTHER`, `ENGINE_HOLDER_TYPE1_STATE2`, `ENGINE_HOLDER_TYPE1_STATE_NOT2`, `ENGINE_HOLDER_TYPE_STATE_UNAVAILABLE`, `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4/-5/-3/OTHER`. All require same holder/renderer/stream identity. Numeric track type=1 and state=2 still **do not prove audible PCM or selected track/edition/entitlement**. Stage B NO-GO, no substitution.

**Pre-NAV24 backup:** `backup/android-a1-nav23-owner-accepted-pre-nav24-active-audio-20261118` @ `f1fe9e052660d62eaa9cacb447eca4e577b291cd`. Original accepted signed NAV23 APK preserved in personal Library, SHA256 `376d3212a3802cf40e905eb434699d6999202086129eb9affc0c66bd4f8ea6a8`. **NAV24 one-shot original-publisher-first ARM13 CI #44188930346 SUCCESS**, exact signed code/workflow commit `230ad06e91b7b2fc8e77eedfb0686eff92caf228`. Persistent accepted owner signer `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf` verified, embedded original Yandex SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. Owner NAV24 signed APK 71,471,084 bytes, SHA-256 `b1cd871c76b9e514b212d67eab19314e23b73fb09ca5e7f24e3fd18b26eb74ac`. Uploaded and listed in PERSONAL CHATGPT LIBRARY `/CELIKOM/Android/Native/CELIKOM-A1-NAV24-Audio-Renderer-Type1-State2-ReadOnly-20261118.apk` plus `CELIKOM-A1-NAV24-Инструкция.txt`. Library APK downloaded back and verified **LIBRARY_NAV24_BYTES_IDENTICAL** to signed CI output. Exact protected source `backup/android-a1-nav24-audio-type1-state2-owner-ci-green-20261118`. **No real owner-phone NAV24 results yet**, no CELIKOM replacement. NAV23 remains available in Library.

**Next step:** owner installs verified NAV24 **over NAV23** without uninstall/data clear, listens to regular Yandex Music for a few songs, exports NAV24 TXT; no special seek/pause repro required. Parse `RENDERER_TYPE_STATE_ACCESS`, `ENGINE_HOLDER_RENDERER_TYPE1/OTHER`, `ENGINE_HOLDER_TYPE1_STATE2/NOT2/UNAVAILABLE`, `ENGINE_AUDIO_TYPE1_STATE2_RETURN_MINUS4/MINUS5/MINUS3/OTHER` alongside still-proven NAV23 strict engine holder link. Determine whether original active Type1/State2 renderer reads are observed without identity mismatch; **do not** mistake it for selected track/album/edition or audible CELIKOM substitution. No new speculative APK until owner evidence; avoid restarting research or touching original Yandex/Windows/browser/server/Test.50.

---

# ARCHIVED — NAV23 OWNER TXT CONFIRMED (18 NOV 2026)

**Owner's private NAV23 real-phone diagnostic received and analyzed:** `CELIKOM-A1-Diagnostics-1794952135309.txt`. Read [exact device result and new static CFG proof](ANDROID-A1-NAV23-OWNER-REALPHONE-ENGINE-HOLDER-MATCH-20261118.md) FIRST. Never commit raw owner TXT. Historical NAV22 marker in rotated local lines is not the current build; the active build is `NAV_V23_EXACT_ENGINE_HOLDER_STREAM_ARRAY_READONLY`.

**Real NAV23 result:** six 2025-native hooks REGISTERED, `ENGINE_HOLDER_SCOPE_ENTER=MANY`, **`ENGINE_HOLDER_STREAM_ARRAY_MATCH=MANY`**, `DIFFERENT=NONE`, `UNAVAILABLE=NONE`, **`ENGINE_HOLDER_READ_RETURN_MINUS4=MANY`, `MINUS5=FEW`, `MINUS3=MANY`**, no lost read links. `SECONDARY_CALLER_ENTER/MATCH=MANY`. Old `QUEUE_SCOPE_ENTER=NONE`, which is a *different helper*; no issue with the new confirmed route. `IDENTITY_STATUS=STRUCTURAL_ONLY`, **`CELIKOM_REPLACEMENT=NOT_CONNECTED/NO-GO`**. Ordinary Yandex original playback remains owner-accepted; no observed playback bugs reported. `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/MANY` does **not** prove a Java crash.

**New exact original signed six-DEX CFG audit:** `e.break()V` at PC 1051 reads **`h.SLOT_B Lxh6`**, carries identical reference into `e.catch(Lxh6;IZJ)V` at PC **1183**. `e.class([ZJ)V` reads the *same exact field ID* at PC **2**, passes the same reference into `e.catch` at PC **51**. Both pass source-dominance and 1/1 alias CFG checks, **CI #44185115155 SUCCESS**, audited code commit `2fd5b5d8ee6fef997079c92966eac30a21467b6c`. A third `e.break` invocation at PC510 exists but is NOT proved to originate from SLOT_B; do not promote it. This is *static* source equality; cannot infer live audible/current track from it alone.

**Working branch only:** `manufact-test/nomusic` `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. NAV23 owner-signed CI #44180557905 SUCCESS, JVM #44180395176 SUCCESS; signed APK code `b53af8291c38ac9e7141a186bb48ab682eb30e25`; Library verified owner APK `/CELIKOM/Android/Native/CELIKOM-A1-NAV23-Engine-Holder-Stream-ReadOnly-20261118.apk`, SHA256 `376d3212a3802cf40e905eb434699d6999202086129eb9affc0c66bd4f8ea6a8`. Exact older signed reserve `backup/android-a1-nav23-owner-signed-library-verified-final-20261118` @ `3c2146092e29e58d32415e3a43a2c431e896bc60`. No NAV24 APK built; original signed Yandex 2025 untouched.

**Next engineering gate:** verify audio-only renderer identity/started decoder and **runtime selected holder from queue SLOT_B**, distinguishing current audible output vs prefetch/Next. Start with bounded exact 2025 signed static audit for safe hook signatures, not generic restarts. Only then potentially prepare a minimal passive NAV24 experiment with JVM/native CI, same owner signer, and verified personal Library delivery. Do not enable CELIKOM alternative-audio substitution without a verified active-source/selected-track/album/entitlement route. Do NOT change stock Yandex, architecture, Test.50, Windows, extension, server; no data wipe. No need to ask for another NAV23 TXT — this one is already analyzed.

---

# ARCHIVED — NAV23 SIGNED; OWNER TXT SUBSEQUENTLY RECEIVED (18 NOV 2026)

**Owner-facing reality:** Native original Yandex Music works normally, including playback, Next, pause and seek, with **no reported bugs**. The sole outstanding function is CELIKOM alternative-audio substitution. **Do not claim there is a playback problem.**

**New owner NAV22 TXT already analyzed:** [NAV22 actual phone result](ANDROID-A1-NAV22-OWNER-PHONE-RESULT-SECONDARY-CALLER-20261118.md). It confirms `b.super` secondary attachment with many same-reference renderer reads; `QUEUE_SCOPE_ENTER=NONE` and `CELIKOM_REPLACEMENT=NOT_CONNECTED`. Read [NAV23 strict engine holder array witness](ANDROID-A1-NAV23-ENGINE-HOLDER-STREAM-ARRAY-READONLY-20261118.md) for code and gates.

**Exact signed 2025 static proof:** `e.catch(Lxh6;IZJ)V` invokes renderer `k.super` at PC 131/144; the same method reads `Lxh6.[LR29;` stream array at PC 67. CI #44179471641 SUCCESS. This is the proven alternative to the earlier missing queue path. The structural link to the audible current track remains unproven. NAV23 adds a passive `e.catch` lifetime scope and exact `holder.[LR29` Java-identity check on the existing `b.super → b.package → b.g` path. No payload, track ID, URLs or account values logged, no replacement enabled.

**Working branch only:** `manufact-test/nomusic` `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Pre-NAV23 backup: `backup/android-a1-nav22-owner-secondary-proven-before-nav23-engine-holder-20261118` @ `892758105a130e496161aef9f1c146e78184923a`. Previous signed NAV22 APK is in verified personal Library. JVM NAV23 observer CI #44180395176 **SUCCESS**. Owner-only one-time native/signer CI **#44180557905 SUCCESS**, exact code `b53af8291c38ac9e7141a186bb48ab682eb30e25`; same accepted owner cert `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`; unchanged embedded publisher Yandex base SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. APK SHA-256 `376d3212a3802cf40e905eb434699d6999202086129eb9affc0c66bd4f8ea6a8`, 71,471,084 bytes. **Verified personal ChatGPT Library** `/CELIKOM/Android/Native/CELIKOM-A1-NAV23-Engine-Holder-Stream-ReadOnly-20261118.apk` and `CELIKOM-A1-NAV23-Инструкция.txt`. Library APK listed, read back and checked exactly byte-identical to signed CI artifact. Protected signed-code backup `backup/android-a1-nav23-engine-holder-signed-code-ci-green-20261118`. This is **not** owner real-phone playback evidence nor CELIKOM substitution.

**Next:** owner installs already verified NAV23 in place over NAV22 (NO uninstall/data clear) and sends new private TXT after normal music listening. Parse `ENGINE_HOLDER_SCOPE`, `ENGINE_HOLDER_STREAM_ARRAY_MATCH/DIFFERENT/UNAVAILABLE` and `ENGINE_HOLDER_READ_RETURN_*` separately from legacy queue/weak counters. Do not change original Yandex, architecture, Test.50, server, Windows, extension or protection settings. Stage B remains NO-GO, original app not patched.

---

# ARCHIVED — NAV22 SIGNED; OWNER-PHONE TEST COMPLETED (17 NOV 2026)

**Authoritative current handoff.** Owner confirmed ordinary Yandex music, Next, pause and seek work flawlessly, with **NO observed playback bugs**. Our ONLY outstanding product capability is CELIKOM alternative-audio substitution. Do not invent crashes or regressions from diagnostic categories.

**Read first:** [NAV22 exact secondary caller witness + green signed release](ANDROID-A1-NAV22-SECONDARY-ATTACH-CALLER-DIAGNOSTIC-20261117.md). Previous [NAV21 actual owner phone evidence](ANDROID-A1-NAV21-OWNER-REALPHONE-TXT-RESULT-20261117.md) explains why the separate caller was added. Historical documents below remain archival.

**Only working branch:** `experiment/android-a1-metrica-init-state-observer-arm13-20261112` in `manufact-test/nomusic`. Signed owner NAV22 source commit `50078f012a57b7fc13060c3205f2757b4a2894a7`; ARM13 full publisher-first signed CI **#44174172281 SUCCESS**; JVM **#44174039648 SUCCESS**. Exact pre-change NAV21 backup `backup/android-a1-nav21-owner-accepted-original-before-nav22-caller-witness-20261117`; verified NAV22 source snapshot `backup/android-a1-nav22-second-caller-signed-code-ci-green-20261117`.

**Library verified owner NAV22 APK:** `/CELIKOM/Android/Native/CELIKOM-A1-NAV22-Secondary-Attach-Caller-ReadOnly-20261117.apk`, SHA-256 `06e7dd168f82db2052d8421a050c5d2bf22f12ff250918d4bd943e7b1cdebf86`, 71,471,084 bytes, same accepted v2/v3 owner signer cert `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`. Embedded original Yandex 2025.10.4 SHA `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` unchanged. Matching Library instruction `CELIKOM-A1-NAV22-Инструкция.txt`, re-downloaded APK matches CI bytes exactly. No sandbox or Actions download links to user. Previous APKs preserved.

**What NAV22 does:** read-only observation of exact second 2025 native caller `b.super(lQ8,[Sr4],R29,ZZJJ,Sl6$b)`, distinguishing weak renderer attachment inside this caller, different stream and outside caller; existing queue scope and original `b.g` return counters unchanged. The CELIKOM replacement remains **NOT_CONNECTED/NO-GO**. The new NAV22 build is **NOT YET real-phone-tested**.

**Next action:** Owner installs NAV22 in place without data clear/uninstall and listens to ordinary music as usual, then sends NAV22 diagnostic TXT. Analyze `SECONDARY_CALLER` hook status, `SECONDARY_CALLER_ENTER`, `SECONDARY_CALLER_STREAM_MATCH`, `UNSCOPED_ATTACH_SECONDARY_MATCH`, `UNSCOPED_ATTACH_OUTSIDE_SECONDARY` alongside `QUEUE_SCOPE_ENTER` and original scoped/weak read returns. Identify exact selected-audio linkage by evidence before implementing replacement; no invention of user playback problems, no further speculative APK, no original app modifications, no new architecture or Test.50/Windows/browser/server changes.

---

# ARCHIVED — NAV21 OWNER PHONE TXT ANALYZED (17 NOV 2026)

**Latest evidence supersedes the older 'await NAV21 TXT' handoff below.** The user supplied private NAV21 owner diagnostic `CELIKOM-A1-Diagnostics-1794944332422.txt`. Start with [NAV21 ACTUAL OWNER PHONE RESULT](ANDROID-A1-NAV21-OWNER-REALPHONE-TXT-RESULT-20261117.md) BEFORE older handoff docs. Do **not** upload private TXT to GitHub.

**Key new facts:** confirmed NAV21 active marker; all four hooks REGISTERED; `QUEUE_SCOPE_ENTER=NONE`, `QUEUED_HOLDER_ATTACHED=NONE`, all `QUEUE_SCOPED_READ_RETURN_*=NONE`. The real renderer/stream weak `UNSCOPED_READ_RETURN_MINUS4=MANY`, `MINUS5=FEW`, `MINUS3=ONE`; no reference conflicts, `READ_RETURN_LINK_LOST=NONE`. NAV20 had `QUEUE_SCOPE_ENTER=MANY`, `QUEUED_HOLDER_ATTACHED=ONE`, `ATTACHED_STREAM_READ_MATCH=FEW`. NAV21 queue observer itself has NOT changed from NAV20: cannot infer a code regression from one differing session. Fresh MAIN-process `METRICA_EXCEPTION_SUMMARY=MUSIC_APP/MANY` (not just rotated old log); no confirmed Java crash or owner listening report. Stage B is **NOT_CONNECTED / NO-GO**.

**Next justified step:** owner reuses existing NAV21 (no new APK) to run a controlled original song → Next → pause/seek → optional My Wave sequence, exports new TXT before process exits, and reports original audio/restarts. If queue scope stays NONE despite that sequence, a precisely bounded read-only exact-2025 attach-caller discriminator may be warranted. No new APK, architecture change, sound substitution, data reset or private TXT upload now. Prior signed code `def5f4ff` and verified Library APK remain unchanged.

---

# CURRENT — NAV21 FROZEN; NEXT CHAT RECEIVES OWNER TXT (17 NOV 2026)

**This is the authoritative starting point, no additional build or code work required now.** The owner requested a saved checkpoint and will provide the new **NAV21 on-device TXT directly to the NEXT chat**. NAV21 TXT has **NOT** been received or analyzed in this chat. Do not claim it has. Older NAV18/NAV19/NAV20 wait notes below are archived.

**READ THESE IN ORDER:**
1. [Final NAV21 handoff awaiting owner's private diagnostic](ANDROID-A1-NAV21-FINAL-HANDOFF-AWAIT-OWNER-TXT-20261117.md) — canonical task boundaries.
2. [NAV21 signed owner test release](ANDROID-A1-NAV21-OWNER-SCOPED-READ-RESULT-RELEASE-20261117.md) — exact APK, CI, signer, Library.
3. [NAV20 REAL phone evidence and reason for NAV21](ANDROID-A1-NAV20-REALPHONE-QUEUE-SCOPED-READ-RESULT-AND-NAV21-20261117.md).
4. [First message to paste in next chat](NAV21-FIRST-MESSAGE-FOR-NEXT-CHAT-20261117.md).

**Work only on** `manufact-test/nomusic` branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. **Final precise no-code-change handoff rollback**: `backup/android-a1-nav21-final-await-owner-txt-handoff-20261117` (to be created at the exact final docs HEAD). Earlier protected exact NAV21 branch `backup/android-a1-nav21-owner-scoped-readresult-library-verified-final-20261117` @ `886089b89e87fb8bfc5bf290eb421fcfbca13069`; pre-NAV21 code branch `backup/android-a1-nav20-owner-strong-read-before-nav21-20261117`.

**NAV21 CI GREEN:** signed Android13/ARM13 75s #44140575566 SUCCESS; JVM #44140534551 SUCCESS; compiled APK code commit `def5f4ff420ec3b285ee1853009882a8f991ec1f`. Documents-only changes after that code commit **do not change the APK**. Signed owner APK in **verified personal ChatGPT Library** `/CELIKOM/Android/Native/CELIKOM-A1-NAV21-Queue-Scoped-ReadResult-ReadOnly-20261117.apk`, SHA256 `581077a18ea8310d12b0e8049e10fe6d25089ed3043cb8340e0e304b2d0d10ce`, original 2025.10.4 Yandex source and accepted NAV17/NAV18/NAV19/NAV20 preserved.

**Real owner NAV20 diagnosis already analyzed:** four native renderer hooks registered, `QUEUE_SCOPE_ENTER=MANY`, `QUEUED_HOLDER_ATTACHED=ONE`, `ATTACHED_STREAM_READ_MATCH=FEW`, `UNSCOPED_ATTACHED_STREAM_READ_MATCH=MANY`; `b.g` returned `-4=MANY` aggregated **across both strong queue-scoped and weak unscoped renderer connections**. NAV21 separates `QUEUE_SCOPED_READ_RETURN_*` vs `UNSCOPED_READ_RETURN_*`; **wait for actual NAV21 TXT to know these categories**. A `-4` may be EOS; no audible track/album/edition or decoded PCM proof. Stage A original native Yandex user-accepted on NAV17; Stage B **CELIKOM substitution NOT_CONNECTED, NO-GO**. Do NOT enable replacement or infer success from diagnostic-only signals.

**NEXT ACTION:** analyze new owner's NAV21 diagnostic and any listening results (Next/pause/seek/My Wave/restarts), identify grounded missing exact link or regression, then do bounded work with exact backup, native/JVM CI, and upload/verifiable APK **only to personal ChatGPT Library** if actually needed. **No new work until the owner's NAV21 TXT**, no new architecture, no stock Yandex changes or owner data wipes, no unrelated 2026.10.3 HookSpec paths, no unsolicited APK release.

---

## ARCHIVED HANDOFF NOTES BELOW — historical references only

# CURRENT — NAV19 SIGNED OWNER RELEASE READY, AWAIT OWNER PHONE TXT (17 NOV 2026)

**Read [NAV19 final owner release](ANDROID-A1-NAV19-OWNER-READONLY-RELEASE-20261117.md) FIRST.** NAV18 owner's actual diagnostic TXT has already been examined in [NAV18 owner diagnostic](ANDROID-A1-NAV18-OWNER-TXT-READONLY-OBSERVATION-20261117.md). Do **not** follow older `WAIT FOR NAV18 TXT` instruction below; it is retained as history only.

**Stage A** accepted NAV17 native original audio/login/UI **PASS**; **Stage B CELIKOM replacement NO-GO / NOT_CONNECTED**. NAV19 observes only exact-2025 native renderer hook status and unscoped same-reference stream reads, no sound replacement. **Owner has not yet tested NAV19.** No new static work needed. Do not conflate stream read entry with currently selected audible audio or final decoder.

**Latest code & private signed APK release**: branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. NAV19 signed ARM13 owner export **CI #44132767915 SUCCESS**, native 75s gate, additional ARM13 **#44132738954 SUCCESS**, JVM **#44129950827 SUCCESS**. Exact NAV19 owner APK SHA256 `d55d7194c1c490481bfc4c184030e198f28827caa18ebf0aa2d116de6932e561`, signer same as NAV17/NAV18; original publisher 2025 nested APK unchanged. Verified personal Library `/CELIKOM/Android/Native/CELIKOM-A1-NAV19-Renderer-HookStatus-ReadOnly-20261117.apk` and `CELIKOM-A1-NAV19-Инструкция.txt`. Existing NAV17 and NAV18 also retained. No fresh installs/wipes/Play Protect bypass.

**Final protected documentation-and-APK-identical branch rollback:** `backup/android-a1-nav19-owner-signed-readonly-final-handoff-20261117` (same HEAD as this updated handoff). The owner APK itself was exported from successful earlier code CI; later docs-only changes do not affect those signed bytes.

**First next action**: owner installs NAV19 *in place* and sends new `NAV_V19_RENDERER_HOOK_STATUS_UNSCOPED_READONLY` TXT with original sound/Next/pause/seek/My Wave notes; analyze persisted `AUDIO_NATIVE_RENDERER_HOOK_STATUS` plus weak unscoped/strong queue-holder stream read categories. Do not fabricate NAV20 without that evidence. Prior rollback before NAV19: `backup/android-a1-nav18-owner-txt-readonly-observer-jvm-green-20261117` @ `971aef7cf9339ab1ad13471e4320a4b6da21c89b`.

---

# NEW CURRENT STATE — OWNER NAV18 TXT ARRIVED (17 NOV 2026)

**Start here, not the old "WAIT FOR NAV18 TXT" heading below.** Owner report `CELIKOM-A1-Diagnostics-1794933581039.txt` has been analyzed; the compact authoritative findings and subsequent in-branch read-only code/test changes are documented in [ANDROID-A1-NAV18-OWNER-TXT-READONLY-OBSERVATION-20261117.md](ANDROID-A1-NAV18-OWNER-TXT-READONLY-OBSERVATION-20261117.md). Confirmed NAV18 marker active; replacement `NOT_CONNECTED` by design; native queue scope `NONE`, unscoped renderer attaches and unmatched sample reads `FEW`, identity `STRUCTURAL_ONLY`. **No replacement and no audible renderer identity claim**. No live owner proof beyond this diagnostic.

**Protected baseline:** the accepted NAV17 and delivered signed NAV18 APK are unchanged; backup `backup/android-a1-nav18-owner-diagnostics-before-observer-fix-20261117` points to the prior exact `a8d6dbc9` HEAD. On the *same single working branch* added persistent `AUDIO_NATIVE_RENDERER_HOOK_STATUS` plus independently labeled unscoped attach/read alias witness; bounded read checks rearm after unscoped attach. **JVM CI #44129950827 SUCCESS** for code through `089ea2d1`. Native ARM13 checks were auto-triggered and have not yet been marked accepted at this doc update. **No new APK built/exported or owner-tested.** Continue with CI verification and exact focused diagnostic gates, not broad source research or speculative audio substitution. Stage B stays NO-GO.

---

# CELIKOM Android A1 — CANONICAL CURRENT HANDOFF

## FIRST ACTION IN NEXT CHAT — WAIT FOR NAV18 PHONE TXT (17 NOV FINAL)

**This is the newest authoritative instruction.** The ready-to-copy Russian opening for the successor is in [NAV18-FIRST-MESSAGE-FOR-NEXT-CHAT-20261117.md](NAV18-FIRST-MESSAGE-FOR-NEXT-CHAT-20261117.md). Final documentation-only backup: `backup/android-a1-nav18-final-owner-diagnostics-handoff-20261117`. The owner's next message will contain the NAV18 real-phone diagnostic TXT and listening results. **Read [ANDROID-A1-NAV18-FINAL-HANDOFF-AWAIT-OWNER-DIAGNOSTICS-20261117.md](ANDROID-A1-NAV18-FINAL-HANDOFF-AWAIT-OWNER-DIAGNOSTICS-20261117.md) FIRST, plus this document and [NAV18 binary release details](ANDROID-A1-NAV18-EXACT-NATIVE-RENDERER-READONLY-OWNER-TEST-20261117.md).** Do NOT resume static audits before interpreting that diagnostic, and do NOT manufacture new APK until a concrete device issue/gate warrants it.

**Actual state:** Stage A native real Yandex original playback passed on NAV17; Stage B replacement still NO-GO. **NAV18 APK delivered and owner is about to test, but no NAV18 phone diagnostic/reliable live result exists in this chat.** Original vendor 2025.10.4 #120.1gpr (not repository HookSpec 2026.10.3). Original NAV17 backup and new NAV18 APK both saved and verified in user's **ChatGPT Library → /CELIKOM/Android/Native/**. Native signed full-owner export CI **#44122921119 SUCCESS**. The test's exact signed NAV18 APK SHA256 **`647cbbc348e128ff10e79f50a6a04964cf9253a5e4cacd08f5949fe892793212`**, and persistent owner cert **`048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`** match prior NAV17 signer. The original nested Yandex APK bytes are unchanged. DO NOT uninstall/clear data or bypass Android protections.

**The 17 November signed static trace is COMPLETE through native `LR29` sample-read method entry.** New read-only NAV18 hook observes `mQ8.catch → b.package → b.g → b.case` and exports finite categories on owner tap; it does not select/replace audio or prove final PCM or current album/edition. For diagnostics, find latest `DIAGNOSTIC_BUILD=NAV_V18_NATIVE_RENDERER_STREAM_READONLY` emitted as `event=DIAGNOSTIC_BUILD;origin=NAV_V18_NATIVE_RENDERER_STREAM_READONLY;error=ACTIVE`; check hook `REGISTERED/NO_HOOK` and audio summary `QUEUED_HOLDER_ATTACHED`, `ATTACHED_STREAM_READ_MATCH`, `IDENTITY_STATUS` alongside owner sound/Next/seek/My Wave. No sensitive data, song IDs or audio in report. Interpret `NONE/ONE/FEW/MANY` strictly as coarse bins, not exact counts.

**Branch safety:** only `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. The exact owner APK's signed content does not change when documenting. There is a pre-live backup `backup/android-a1-pre-live-readonly-witness-20261117` @ `4a1caf93bff6e06fb99669693fc346321b89d509`, plus final green NAV18 backup below. Code and APK are NOT to be changed in this last handoff; only documentation. Keep all previous static proof docs; they are history, not new to-do.

**Updated:** 17 November 2026. This file takes precedence over earlier Android NEXT-CHAT/HANDOFF documents.

## 17 Nov — FINAL SAVED HANDOFF: NAV18 released, phone evidence is NEXT

**Mandatory live-test handoff: [ANDROID-A1-NAV18-EXACT-NATIVE-RENDERER-READONLY-OWNER-TEST-20261117.md](ANDROID-A1-NAV18-EXACT-NATIVE-RENDERER-READONLY-OWNER-TEST-20261117.md).** Owner approved one *diagnostic-only* in-place APK; **NAV18 signed APK is now verified in personal Library**. NAV17 remains preserved as accepted baseline. **Stage B NO-GO, no CELIKOM replacement audio**.

- On the **same working branch** added privacy-bounded `NativeRendererStreamEvidence.java`, four exact signed-**2025.10.4** LibXposed observation hooks to existing `ExitCallsiteWitness.java` (`mQ8.catch→b.package→b.g→b.case`), model tests and owner-on-tap TXT summary; code never reads/export audio, IDs, URLs, account data, object values, names, or buffers. `DIAGNOSTIC_BUILD = NAV_V18_NATIVE_RENDERER_STREAM_READONLY`. Every original `chain.proceed()` invoked unmodified once. Does NOT claim b.g result decodes successful audio or that currently selected album/edition is known.
- [Independent Java JVM model CI #44120467198 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44120467198). Full publisher-signed 2025 Android13 native ARM publisher-first+clone CI **#44121349850 SUCCESS**; dedicated signed owner export **#44122921119 SUCCESS**, accepted in-place update only.
- Archived exact owner NAV17 APK **SHA-256 8d7c1570367360c12ba11f3972fa72477aca4dcc33f30dce78b381aee939b20d** to verified personal Library `/CELIKOM/Android/Native/CELIKOM-A1-NAV17-OWNER-ACCEPTED-BACKUP-20261114.apk`. Independently confirmed its v2/v3 signer **048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf** and nested vendor original SHA **1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56**.
- Working backup BEFORE live changes: `backup/android-a1-pre-live-readonly-witness-20261117` @ `4a1caf93bff6e06fb99669693fc346321b89d509`. Owner's NAV17 original binary unchanged. Last runtime-hook edit now **NAV18 preparation** (`ExitCallsiteWitness.java`), NOT older `a655712d...`; historical prior-runtime checkpoint remains documented below.
- One-shot owner export workflow `.github/workflows/android-a1-nav18-owner-renderer-diagnostic-export-once.yml`. Its first run **#44121652525 failed closed on missing INSTALLED_CERT variable**: no artifact published. The independently verified NAV17 signing cert is now pinned as expected installed cert in **`ec559b537d52b5c9335452d7a24b7111e423f364`**, **run #44122921119 SUCCESS** is the completed owner export gate. No fresh install; true owner signed in-place update only.
- **Owner installation approved for diagnostic trial now**: private signed APK **SHA256 `647cbbc348e128ff10e79f50a6a04964cf9253a5e4cacd08f5949fe892793212`**, v2/v3 **same owner NAV17 cert** `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`, unchanged nested original signed Yandex SHA `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`. Independent checks passed. Verified Library paths `/CELIKOM/Android/Native/CELIKOM-A1-NAV18-NativeRenderer-ReadOnly-20261117.apk` and `/CELIKOM/Android/Native/CELIKOM-A1-NAV18-Инструкция.txt`. Prior NAV17 backup in same folder. **Do not uninstall/clear data or disable Play Protect.**
- Once owner-tested, need **actual read-only event report with source/queue/current audible distinction**. Static source→MediaPeriod→Lup1$a→Lxh6→native renderer attach→LR29 read entry is previously verified; no need to re-audit it.

## Protected checkpoints

- Only working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- **PRIOR signed static read-only native queue→renderer attachment→sample-read code:** `a5b6861ed17252bf67ce35bad8dbd64842dcf1d1`, backup `backup/android-a1-attached-native-samplestream-read-ci-green-20261117` (17 Nov 2026). **CI #44117163552 SUCCESS**, exact publisher-signed 2025 NAV17 original. **Static sample-read route, NOT a current audible decoder claim.**
- Prior queue→renderer exact attached stream code `9fa89edd75692d0373d43791f422453f2d79b2bc`, backup `backup/android-a1-queue-to-renderer-attachment-same-ref-ci-green-20261117`, CI #44116451280 SUCCESS.
- Prior exact child MediaPeriod stream adapter code: `a63a900b16af8a998fc78dde4b111741bbf8390a`, backup `backup/android-a1-verified-stream-adapter-cfg-final-ci-green-20261117`, CI #44106916503 SUCCESS.
- Prior same bridge checkpoint: `c7cbdfcdae09c66c80742a3a83d037d8348ddb75`, backup `backup/android-a1-exact-child-stream-adapter-to-renderer-ci-green-20261117`, CI #44105627930 SUCCESS.
- Prior queue→native renderer reference-comparator code: `29d031ae74a7e21975b01784ce53f43c7ac981cf`, backup `backup/android-a1-render-stream-identity-route-ci-green-20261117` (CI #44100887314).
- Previous signed native engine-holder code: `762088f55114553bacb96b324530ee241ce72dcd`, backup `backup/android-a1-exoplayer-engine-period-holder-ci-green-20261117`.
- Previous same-source→MediaPeriod checkpoint: `24c37a59d454cc5ec0b69f9e548fbe3349108673`, backup `backup/android-a1-exact-source-to-lo96-mediaperiod-ci-green-20261117`.
- Previous signed source-to-internal-playlist-holder code: `dca9e8e5c6ac7503a2f307411c6a495fe8b74093`, backup `backup/android-a1-source-into-internal-playlist-holder-ci-green-20261117`.
- Previous exact TrackWrapper→native Player setter code checkpoint: `a9408608562b3d70a51f8d01c8be17aa4a73589b`, backup `backup/android-a1-lca9-wrapper-mediasource-player-identity-ci-green-20261117`.
- Older exact named-type MediaSource negative-audit checkpoint: `433191c0b6e5f2a2eabef8589aa01c02f326e3b1`, backup `backup/android-a1-direct-mediasource-contract-ci-green-20261117`.
- Prior completed LfT2 code audit checkpoint: `e6bf9b6933d17d503b4f3b1d4f7d460df4b52f6a`, backup `backup/android-a1-lft2-class-structure-ci-green-20261116`.
- Prior code/runtime baseline: `27ccbe8348d598fead0386e70ef68573b04270c4`, backup `backup/android-a1-lft2-trackwrapper-continuation-ci-green-20261116`.
- Last historical runtime-hook checkpoint BEFORE NAV18: `a655712d210189f3bc611847235de3ed4d985c1a`. **New NAV18 read-only hooks now exist in `ExitCallsiteWitness.java`; owner test APK produced/verified as above.**
- Pre-audit safety backup: `backup/android-a1-target-resolved-pre-lft2-class-inspection-20261116` @ `0143f904400d5ddd17a8d4469aa3c777adfe8f04`.
- CI #229: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43888792139), old constructor identity proof.
- CI #230: [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43893294101), compact logs.
- Exact class and branch-sensitive TrackWrapper audit **CI #12 [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43909098407)**, 16 publisher-signed splits / 6 DEX.
- Direct MediaSource-typed Player contract audit **CI #2 [SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44049682525)** on 17 Nov (3/3 unit tests, exact 2025 signed input); CI #1 was blocked by private draft release access, not by the static scan.

## Product status

**Stage A / NAV17 PASS** (owner confirmation on 14 Nov): native Yandex login/UI and original music audible.

**Stage B NO-GO**: CELIKOM replacement audio not connected/proven; no selected native Track → active source/decoder same-object chain.

Goal remains one standalone CELIKOM APK with native Yandex UI/player and original native playback path, no second Player/decoder/AudioTrack. Never infer product packaging from the `pro.celikom.nativeprobe` diagnostic manifest or `<queries>` visibility declarations.

## Definitive *NAV17 tested artifact* origin (not a production-forward pin)

- Owner-installed `CELIKOM-A1-NAV17-PassportProviderFix-20261114.apk`: SHA-256 `8d7c1570367360c12ba11f3972fa72477aca4dcc33f30dce78b381aee939b20d`.
- Its embedded original `assets/lspatch/origin.apk`: SHA-256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56` = Yandex Music **2025.10.4 #120.1gpr**, code `24025542`. This is grounded in the [NAV17 input audit](ANDROID-A1-NAV17-STAGE-B-PINNED-2025-FILEINFO-SOURCE-AUDIT-20261114.md).
- Exact original verified XAPK SHA-256 `8e43be8900d28ee92c8e315ed07069568858bfd4a593757fba9d276bd0c54053`, 45,961,661 bytes, 16 splits / 6 DEX. Publisher signature and base SHA reconfirmed in CI #12.
- Yandex **2026.10.3 #170gpr**, code `24026531`, XAPK SHA `918bd50599dc6a942e190a409303e843b83dcb6d11b90b03c00240331333cf84`, five splits: original-only ARM13 verification CI #42990078186; separate structural clone experiment; **not** the proven NAV17 original.
- Yandex **2026.09.5 #167gpr / #167.1gpr**: formerly reported phone installation, no exact pinned signed package; **not** the proven NAV17 original.

The NAV17 source question is now resolved for the owner-tested artifact. The *future production target* remains a distinct owner/build decision and is not automatically pinned by a previous test. Never transfer obfuscated identifiers across versions.

## LfT2 closure — do not investigate again

Read only [ANDROID-A1-LFT2-EXACT-CLASS-CLOSURE-20261116.md](ANDROID-A1-LFT2-EXACT-CLASS-CLOSURE-20261116.md) for exact structural evidence.

- Earlier chain `LIEa.new → Lqj8.if → Lxj8.if → Lvj8 → Lxj8.for → LfT2.<init>` carries and stores same `LtCa;` TrackWrapper, only on exact 2025 signed DEX.
- `LfT2;` is `PUBLIC FINAL extends Object` with no interfaces; fields of types `LdA9; LtCa; LgA9;`.
- Only constructor, `equals`, `hashCode`, `toString`. **No invokeSuspend** and no executable continuation method.
- Branch-sensitive complete audit of all its TrackWrapper field reads finds only equality and string formatting operations; **no** same-object playback handoff to MediaSource, MediaPeriod, DataSource, Extractor or Player. **This route is CLOSED.**
- Closed old routes: `LiLb`, `LXk6`; don't repeat Media3 ancestry, global List/Object tracing or ByteBuffer sink census.

## Recovered Yandex/Media3 research (documentation only, 16 Nov)

The previous developer's useful research **was already saved**: [YANDEX-MEDIA3-RESEARCH-RECOVERED-20261116.md](ANDROID-A1-YANDEX-MEDIA3-RESEARCH-RECOVERED-20261116.md) is a concise index to exact existing facts, not a new experiment.

- Official Android Media3/ExoPlayer exposes **direct** `setMediaSource`, `setMediaSources`, `addMediaSource`. This prevents an incorrect *MediaItem-only* assumption; it does **not** prove how signed Yandex dispatches into the player.
- Signed 2025 Yandex static [RAa continuity](ANDROID-A1-RAA-SOURCE-RESUME-IDENTITY-20261115.md), [CI #43696198020 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/43696198020): real `RAa.invokeSuspend` resumes with the **same continuation instance** but an explicitly null TrackWrapper argument. Existing bounded weak-reference RAa recovery is a historical research result, not active-selected playback proof. `RAa` is **not** `LfT2`: the latter has no continuation methods and stays CLOSED.
- Native descriptor→Exo factory→source→open/read lifecycle already has source-instance evidence and read-only hooks in [NAV17 Stage B source audit](ANDROID-A1-NAV17-STAGE-B-PINNED-2025-FILEINFO-SOURCE-AUDIT-20261114.md); these can also reflect **prefetch/download**. Even a positive source read cannot attest the selected current track, album/edition/generation, nor an audible CELIKOM replacement.
- The official Yandex playback-support article mentions VPN/network stability, **not** a public signed-app playback call graph. Third-party clients/plugins are not evidence of official Yandex Android internals.
- This recovery changed **documentation only**. Safety snapshot before updates: `backup/android-a1-before-yandex-media3-research-handoff-20261116` @ `a324963b84876a88513bc1d208a42519489c397f`. No runtime hooks, APK, original Yandex or production changes; no new CI was requested.

## 17 Nov — exact direct MediaSource-to-Player API check, CI #2 SUCCESS

- Source: `android/native-yandex-hooklab/ci/direct_media_source_player_contract.py`; CI `.github/workflows/android-a1-direct-media-source-player-readonly.yml`. Before-work backup: `backup/android-a1-pre-direct-mediasource-contract-audit-20261117` @ `a142f5fe48f92d68727f4c9873a4a6cfda56b156`. Successful audit code backup: `backup/android-a1-direct-mediasource-contract-ci-green-20261117` @ `433191c0b6e5f2a2eabef8589aa01c02f326e3b1`.
- Bounded to **11 previously known Player interface/implementation owners** and **exact declared parameter type** `Landroidx/media3/exoplayer/source/MediaSource;` on the signed 2025.10.4 XAPK (16 issuer-signed splits / 6 DEX, NAV17 origin SHA confirmed).
- Result: `exact_media_source_class_defined=false`, `exact_direct_media_source_player_contract_count=0`, `direct_source_player_callsite_count=0`. 3/3 fail-closed tests PASS; original input deleted ephemerally. Runtime hooks, native code, APK, accounts and audio unchanged.
- **Interpretation:** This closes only the **named exact-typed direct MediaSource Player call** hypothesis in the listed owners. It does **not** disprove obfuscated MediaSource types, indirect dispatch, runtime selected item, or the public Media3 APIs. No negative inference beyond that scope. **Do not rerun a global census to compensate.**
- No selected Track + album/edition/duration/generation → active source/decoder same-object proof; Stage B remains NO-GO. Future candidate must have a separately grounded exact source-side or selected-player-owner link, otherwise do not expand tracing.

## 17 Nov — NEW proven TrackWrapper → native ExoPlayer source object handoff

**Read [exact source-to-Player signed proof](ANDROID-A1-EXACT-SOURCE-PLAYER-HANDOFF-20261117.md)** before any further Stage B work. Unlike previously closed MediaItem/List routes, this is a **specific verified source-side object identity into the native Player setter**:

- [Signed factory CI #5 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44069492927): `LgLb.for()` carries the identical `LOr2$a` result from Yandex Exo factory to `Las2(MediaItem,LOr2$a)`. `LZB3` is a distinct lifecycle interface, not the MediaSource type.
- [Signed media-source CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44069978477): `LIr8 extends LdC0 implements LSl6` (via superclass); `LiLb extends LWT1 extends LdC0 implements LSl6`. Within `LiLb$a.invokeSuspend`, `LlLb.if(...)` yields an `LIr8` which is passed as the same object to `LWT1.strictfp(Object,LSl6)`. These establish source-side nesting, not active audio.
- [Signed Player setter CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44070516863): exact `LA14.e(LSl6;J)V` forwards the identical source parameter to native `ExoPlayer.e(LSl6;J)`; `LcA9.extends(...LtCa...)` directly calls `LA14.e`.
- **Critical [branch-sensitive CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44070976535)**, signed 2025 NAV17, 4/4 fail-closed tests: exact `LcA9.extends(...LtCa...)` passes same TrackWrapper argument to `Lbq0.this` (PC 14), constructs the unique `LiLb` source with a MediaItem (PC 97), and passes the **exact same allocated LiLb instance** to `LA14.e(LSl6;J)` (PC 112), across 55 path states and 2 branches. Verdict **`LCA9_ONE_NATIVE_PLAYER_SOURCE_SAME_OBJECT_STATIC_PROVEN`**. This is the actual new static handoff result. No re-audit of this exact route.

**Precise boundary:** It proves source selection *call into ExoPlayer* on a TrackWrapper-bearing route, **not** that the setter receiver is the currently audible player, nor correct album/edition/duration/generation, active MediaPeriod/decoder, or CELIKOM bytes. Stage A NAV17 PASS; **Stage B NO-GO**. No runtime hooks or APK touched. Verified code at `a9408608...`, protected backup above.

## 17 Nov — NEW proven source accepted and retained in native ExoPlayer playlist

**Read [exact signed playlist source-holder handoff](ANDROID-A1-EXOPLAYER-PLAYLIST-HOLDER-IDENTITY-20261117.md)**. This extends the proven TrackWrapper→LiLb→LA14.e→ExoPlayer.e same-object proof *into internal Player state*, not merely a factory or source read.

- [Signed implementation CI #2 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44074575554): concrete `androidx.media3.exoplayer.d.e(LSl6;J)` receives the source and calls `Collections.singletonList(source)` → `d.T0(List,I,J,Z)`; wrapper `LA14.e` forwards the exact same source into the Player.
- [Signed T0 admission CI #1 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44075018858): branch-sensitive source parameter→singletonList→T0 is **same-reference**, and `T0` forwards the exact List parameter to `d.A0(List,I)` at PC 51. This is native Player playlist admission, not audible current selection.
- **Critical [signed A0 source-holder CI #5 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44076441146)**: `A0` uses `List.get` on its same input List; exact retrieved source reference passes via check-cast unchanged into `i$c(LSl6;Z)`; the same i$c allocation enters `ArrayList.add`. `i$c` forwards exact source to `Lp96(LSl6,Z)` and stores that newly created Lp96 wrapper; `Lp96` forwards exact source into `LuIb(LSl6)`, where the exact argument is **stored on `this` in an LSl6-typed field**. Checkpoint `dca9e8e5...` above. **`one_source_to_internal_playlist_holder_static_proven=true`**.
- This is a **real new source object → internal native playlist owner identity proof**, not a claim that a queued holder is the one currently playing. Runtime current selected Track+album+edition+duration+generation, active MediaPeriod/decoder and CELIKOM audio remain **unproven**. Stage B **NO-GO**.
- All changes Python static read-only tools, unit tests, workflows and docs. Last runtime hook change `a655712d`; no APK or vendor code modifications.

## 17 Nov — NEW exact source → returned MediaPeriod identity CI green

**Read the new [MediaPeriod identity proof](ANDROID-A1-EXACT-SOURCE-MEDIAPERIOD-IDENTITY-20261117.md)**. It continues the already signed, same-object source→Player→playlist-holder route; it does NOT claim current audible playback.

- **[Exact signed MediaPeriod CI #3 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44077450137)**, fail-closed fixtures: the exact `LuIb.<init>(LSl6;)V` constructor stores its original source argument to a particular `LuIb` DEX field. `Lp96.transient(LSl6$b;LrH2;J)Lo96;` reads **that identical field reference**, not merely the same declared type; source values and field names are not exported.
- Within `Lp96.transient`, the identical original source is stored on the **unique `Lo96` MediaPeriod object** (PC 18), and **both return paths** (PC 51, 64) return that same newly created Lo96. Branch-sensitive CFG 34 states, 1 object allocation, 1 constructor call, 2/2 verified period returns. `static_same_source_to_returned_MediaPeriod_proven=true`.
- This closes the exact *static* source→MediaPeriod identity gap from verified `LcA9 TrackWrapper → LiLb → LA14.e → ExoPlayer.d.e → singletonList → d.T0 → d.A0 → i$c → Lp96 → LuIb → Lo96`. It is **not** proof that the returned period was selected for actual playback.
- **Still missing:** runtime active/current period vs prepared/prefetch, selected Player receiver/item, track+album+edition+duration+generation, period-to-decoder instance and sound, CELIKOM grant/replacement. **Stage B remains NO-GO.**
- Code SHA `24c37a59d454cc5ec0b69f9e548fbe3349108673`, exact backup above. No runtime hooks/APK or vendor original changed.

## 17 Nov — PRIOR verified exact Lo96 period → engine holder handoff

**Previous detailed proof: [ANDROID-A1-EXOPLAYER-ENGINE-PERIOD-HOLDER-20261117.md](ANDROID-A1-EXOPLAYER-ENGINE-PERIOD-HOLDER-20261117.md).** This is the latest step after the previously proven `Lo96` MediaPeriod; no other historical handoff supersedes it.

- **[Signed period-holder CI #3 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44093915839)**: `Lp96.goto(LSl6$b;LrH2;J)Lwh6;` returns the **identical `Lo96`** from `Lp96.transient`. A `Lxh6` constructor reads the exact `Lp96` reference from `ExoPlayer/i$c`, receives its `Lo96` period at PC 99, places it as the `IdentityHashMap` **key** at PC 102, and passes the **same period reference** to `Lup1.<init>(Lwh6;ZJJ)` at PC 132. `Lup1` stores that exact incoming period argument on `this` at PC 3. This grounds period→native wrapper identity, **not playback selection**.
- **[Signed native engine CI #2 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44094591928)**: the **sole direct** exact `Lxh6.<init>([Landroidx/media3/exoplayer/l;JLOFa;LrH2;Landroidx/media3/exoplayer/i;Lyh6;LRFa;)V` caller is `Landroidx/media3/exoplayer/e;.break()V` at PC 275, which allocates the same local `Lxh6` object at PC 240. The engine touches `Landroidx/media3/exoplayer/h` queue-like `Lxh6` fields and other rendering/scheduling methods. **Neither a method name nor a newly created queue holder proves it is active/current.**
- **Interpretation:** exact static `TrackWrapper → LiLb source → native ExoPlayer → playlist owner → Lo96 MediaPeriod → Lup1/Lxh6 wrapper → Exo internal engine caller` exists on the **signed NAV17 2025 original**. Still missing exact **currently audible queue holder/period/decoder and Track+album+edition+duration+generation**. Stage B **NO-GO**; no CELIKOM playback/replacement tested.
- Green code `762088f5...` / backup above. No runtime hooks, APK or signed original modified. Last runtime hook change remains `a655712d210189f3bc611847235de3ed4d985c1a`.
- Initial [engine CI #1 failure](https://github.com/manufact-test/nomusic/actions/runs/44094414204) was a deliberately fail-closed bound over unrelated engine field references, **not** a failed signed source path; the script narrowed to exact period/holder field types before **CI #2 SUCCESS**. Likewise period-holder CI #2 failed only due to a fixture expecting 3 targets after adding the fourth; corrected with **CI #3 SUCCESS**. Do not confuse intermediate failed runs with final status.

## 17 Nov — PRIOR scoped native queue → renderer stream comparator (SIGNED CI green)

**Prior scoped proof: [ANDROID-A1-ACTIVE-QUEUE-RENDERER-STREAM-IDENTITY-20261117.md](ANDROID-A1-ACTIVE-QUEUE-RENDERER-STREAM-IDENTITY-20261117.md)**. This established the queue-to-renderer comparator after the prior `Lo96 → Lup1/Lxh6 → Exo e/h` constructor/holder bridge. Code **`29d031ae74a7e21975b01784ce53f43c7ac981cf`**, reserve `backup/android-a1-render-stream-identity-route-ci-green-20261117`, [CI #44100887314 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44100887314).

- The exact signed `ExoPlayer/h` has **five distinct `Lxh6` queue pointer slots**, not a single active period field. `h.if()Lxh6;` advances **`SLOT_A` through the same holder's successor pointer and returns the updated front** (PC 49→51→53→58→60). This proves front-advance semantics, **not which holder is currently audible**.
- Exact `e.break()V` **`h.SLOT_B` read at PC 547** flows as the **same reference on all bounded reaching CFG states** to native `LmQ8.try(Lxh6;Landroidx/media3/exoplayer/k;)Z` at PCs **590/598**, zero unmodeled instructions. [CI #44099132883 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44099132883).
- In this **exact LmQ8.try**, a **holder-owned `[LR29;` element** is compared by DEX `if-ne` to a stream returned from **`k.while()LR29;`** (PC 20); a successor-holder comparison occurs at PC 78. `LmQ8.new(Lxh6;)k` similarly compares at PCs 19/32. The verifier checks exact array field, registers and comparison operands, **not just types**. [CI #44100299068 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44100299068).
- This is the first scoped, concrete **queue holder ↔ native renderer attached-stream *identity test*** on the signed original. **No runtime result of the test is known**, nor active decoder instance, selected Track+album+edition+duration+generation, or CELIKOM sound. Stage B **NO-GO**. `LR29/k/l` are interfaces, concrete getter/decoder implementation not resolved by the bounded declared-code-body inspection. No runtime hook/APK changes, last runtime edit stays `a655712d210189f3bc611847235de3ed4d985c1a`.

## 17 Nov — PRIOR native period selection → renderer sample-stream identity bridge (SIGNED CI GREEN)

**Read first: [ANDROID-A1-PERIOD-TO-RENDERER-SAMPLE-STREAM-IDENTITY-20261117.md](ANDROID-A1-PERIOD-TO-RENDERER-SAMPLE-STREAM-IDENTITY-20261117.md)** — prior signed stream-selection and adapter proof, superseded by the current attached stream native read bridge. Read-only code SHA **`a63a900b16af8a998fc78dde4b111741bbf8390a`**, backup `backup/android-a1-verified-stream-adapter-cfg-final-ci-green-20261117`, [CI #44106916503 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44106916503) (4/4 tests). **Stage A NAV17 PASS, Stage B NO-GO.**

- Signed `Lxh6.<init>` allocates/stores a single exact `[LR29;` stream array field at PCs 28/30. **That identical DEX field** is read by `Lxh6.if` during native period selection (PC 63) **and by both previously grounded renderer stream comparison helpers** `LmQ8.try` (PC 4) / `LmQ8.new` (PC 2). The proof compares full internal DEX field references; no private names/values exported.
- `Lxh6.<init>` constructs one specific `Lup1` wrapping the already proven same `Lo96` MediaPeriod (PCs 119/132), stores the same wrapper in an exact `Lxh6` Object field (PC 136). `Lxh6.if` reads **the same field** (PC 61), passes this same `Lup1` receiver **and the holder's exact `[LR29;` array** into `Lwh6.case` period selection at PC 73. The register/alias proof is fail-closed.
- `Lup1.case` internally creates a **distinct** `[LR29;` child stream array and sends it to the wrapped period `Lwh6.case` at PC 45; `Lo96.case` itself delegates to its child `Lwh6.case`. Thus the child source stream **is not directly identical** to the renderer-facing wrapper.
- **New deeper bridge [CI #44105627930 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44105627930):** `Lup1.case` reads child `LR29` at PC 121 from nested array, compares it to the existing `Lup1$a` delegate at PCs 136/138, can create `Lup1$a` with the same child stream passed at PCs 140/142 and store the adapter at PC 145. The exact adapter-array field is re-read at PC 147, selected adapter retrieved at PC 149, and **written to the ORIGINAL incoming holder stream array** at PC 151. That holder array is the exact one compared to `k.while()LR29;` by the native renderer helper. Additional **CI #44106916503 SUCCESS** verifies **1/1 branch-sensitive constructor-reaching path** retains the exact child LR29 reference and that `Lup1$a.<init>` stores the incoming LR29 argument into the exact delegate field read during reuse comparison. This is a **source-backed period selection → precisely wrapped child stream → renderer reference-check static chain**, not a type-only correlation.
- **Not proven:** current runtime equality outcome at `LmQ8.try/new`, which queue generation/Track+album+edition/duration is audible, actual decoder consuming the selected stream, CELIKOM grant/audio/replacement or owner acoustic QA. No runtime-hook/APK/vendor/production changes; last runtime edit stays `a655712d210189f3bc611847235de3ed4d985c1a`.

## 17 Nov — CURRENT LAST VERIFIED native queue → renderer-attached stream → sample-read bridge

**Mandatory latest detailed proof: [ANDROID-A1-CONCRETE-RENDERER-ATTACHED-STREAM-20261117.md](ANDROID-A1-CONCRETE-RENDERER-ATTACHED-STREAM-20261117.md)**, especially its last section **"Newly closed exact native queue → renderer attachment → sample read path"**. Latest code `a5b6861ed17252bf67ce35bad8dbd64842dcf1d1`, backup `backup/android-a1-attached-native-samplestream-read-ci-green-20261117`, [CI #44117163552 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44117163552), all signed-original guards. **Stage A NAV17 PASS, Stage B NO-GO.**

1. **Concrete native renderer interface resolved**: `k.while()LR29;` is implemented by inherited `androidx.media3.exoplayer.b.while()LR29;` (only one direct implementer of `k`, 18 descendants). The exact field returned by this getter is written from the original incoming `LR29` argument of `b.package([LSr4;LR29;JJLSl6$b;)V` at PC 7, and cleared by `b.case()V` at PC 19. [CI #44114869620 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44114869620).
2. **Renderer attachment caller identified**: `LmQ8.catch(Landroidx/media3/exoplayer/k;Lxh6;LRFa;LLL2;)I` calls `k.package(...LR29...)` at PC 114. The only other exact direct caller is internal `b.super(...)`; the engine **does not** directly invoke this setter. [CI #44115226209 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44115226209).
3. **Branch-sensitive same-reference path proven**: In exact `e.break()V`, **the same precise `h.SLOT_B` field** is read at PCs 547 and 1051; the PC 1051 `Lxh6` moves unchanged to `LmQ8.catch` calls at PCs **1088 and 1094** (1/1 reaching states each). The latter reads `Lxh6.[LR29;` at PC 91, obtains the sample stream at PC 93 and forwards **the same LR29 reference** to `k.package` at PC 114 (1/1 reaching states). `b.package` writes that exact stream as the renderer's attached field. [CI #44116451280 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44116451280).
4. **Exact native sample-read entry proven**: `b.g(LiA9;LRF2;I)I` reads **the same attached LR29 field at PC 0**, invokes `LR29.throw(LiA9;LRF2;I)I` with that identical reference as receiver at PC 5 (**1/1 reaching states**). `b.h(J)I` similarly calls `LR29.class(J)I` at PC 8 on the same field. This is a real native **sample-read interface** route, not just source creation or prefetch. 18-class exact renderer subtree has 18 bounded sample read/skip callsites across `LEF2`, `LF35`, `LcC0`, `Lkd6`, `LT21`, `Lbsa`, `Leq6` (and skip descendants). [CI #44117163552 SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44117163552).
5. **Still missing**: *which live holder/stream is currently selected/audible* and queue generation; concrete active **audio** renderer vs video/other, true decoder consumption; verified Track+album+edition+duration and CELIKOM entitlement/replacement/acoustic QA. **Static attached sample-read methods do NOT imply active sound.** No APK/runtime hook changes. Last runtime hook edit still `a655712d210189f3bc611847235de3ed4d985c1a`.

**Exact proven static continuity:** `TrackWrapper → LiLb → native Player/i$c/Lp96 → Lo96 → Lup1 → Lup1$a → Lxh6.[LR29 → h.SLOT_B → e.break → LmQ8.catch → k.package → b.attached LR29 → b.g → LR29.throw(LiA9;LRF2;I)I`. Distinguish adapter stream (`Lup1$a`) from raw child source stream (`LR29`).

## Current next task (supersedes the old pre-NAV18 task)

**Receive the owner's actual NAV18 TXT + symptom report first.** Interpret the final build marker, hook-registration status, matched renderer stream summaries, whether original audio plays across Next/seek/My Wave; distinguish queue/prefetch vs currently decoded audible output. Next code change, if any, must be precisely grounded in these outcomes and backed up. The earlier suggestion to *create* a live witness is **already complete in NAV18**, so do **NOT** redo it. Full detail: [ANDROID-A1-NAV18-FINAL-HANDOFF-AWAIT-OWNER-DIAGNOSTICS-20261117.md](ANDROID-A1-NAV18-FINAL-HANDOFF-AWAIT-OWNER-DIAGNOSTICS-20261117.md).

**Never confuse** the original Yandex 2025.10.4 #120.1gpr with the unrelated 2026.10.3 `HookSpec.java` targets. Stage A owner-accepted original playback PASS; Stage B CELIKOM replacement NO-GO; no changes to original app, NAV17, Test.50, other platforms or backend. The entire 17 Nov signed-static proof above remains valid history.



## BETA11 failure analysis + MP3/M4A parity fix (21.11.2026)

- Owner's latest phone diagnostic: `CELIKOM-A1-Diagnostics-1795254709741.txt`. BETA11 owner session enabled; one prefetch; `OWNER_RESOLVE_NOT_APPROVED=ONE`; no signed grant, alternate decision, datasource arm, audio open/read. `OWNER_RESOLVE_NOT_APPROVED` in BETA11 was an aggregate of FOUR booleans (found, approved, entitled, mime=audio/mpeg), so it did **not** prove that the approved DB row was absent or unapproved.
- Known historical CELIKOM library evidence: Ramil' «Ау», album `38902809`, Yandex track `144530503`, replacement #1, approved/active; MP3 duration 180872 ms; prior byte-for-byte match against the active extension record. User confirms Windows desktop and browser extension currently replace the same album track. Do not ask user to find the song via MyWave or re-prove the mapping.
- Confirmed code-level client mismatch: extension `extension/src/api/api-client.ts` requests `audio_formats=mp3,m4a`; Android BETA11 `NativeOwnerControlPlane` requested only `audio_formats=mp3` and accepted only `audio/mpeg`. Server `ResolveService` intentionally returns `found=false` for an `audio/mp4` asset unless `audio_formats=mp3,m4a` is requested. Existing `NativeGrantContract` and `NativeExoAlternateByteRoute` already support `audio/mp4`; Android's strict gate/preflight was the inconsistent part. This is a concrete parity bug, not proof the live «Ау» asset is M4A.
- Candidate code change on this branch (HEAD `de67ab7e1eb58d64d4901e8d3e54499055e4553b`): owner resolve now requests both MP3 and M4A; common gate accepts only approved+entitled MPEG/MP4; byte-range preflight validates MP3 frame/ID3 or ISO-BMFF `ftyp`; certified-source and limited-beta routes share the same format gate. Added privacy-safe reason counters: resolve not found, approval flag, entitlement, unsupported MIME, MPEG, MP4, and generic signed-audio readiness. The old MPEG-ready counter is retained only for MPEG.
- Regression test added to `test_a1_issuer_proxy_contract.py` to keep Android's format request/gate in parity with the extension and test both formats. Latest workflow `44893567368`: JVM issuer-proxy/contract job SUCCESS; isolated ARM13 module build still running at handoff. No new APK has been exported or installed yet.
- Independent remaining blocker in the same owner diagnostic: creator Track+Album later Flow link was observed once, but `ORIGINAL_SETTER=NONE`, `NATIVE_MAIN_SOURCE_ENTER=NONE`, `WRAPPER_MAIN_SOURCE=NONE`, `TRACK_DESCRIPTOR_FACTORY_LINK=NONE`, `DECISION_ALTERNATE=NONE`, `DATASOURCE_ARMED=NONE`. Do not declare playback fixed from format parity alone; exact original source -> descriptor/factory -> unopened DataSource chain still needs to be connected.
- Live admin/database was **not** inspected from this chat session. Known historical mapping above is already documented; do not ask owner for screenshots as a substitute. Browser fetch to Hostinger was unavailable here and there is no Hostinger hPanel/database connector exposed. Do not claim a live DB check.


### Latest verification update (21.11.2026)

- Current branch HEAD: `de67ab7e1eb58d64d4901e8d3e54499055e4553b`.
- Added explicit signed `audio/mp4` acceptance assertion to `NativeGrantContractTest.java`; isolated exact-identity Java workflow `44893887112` SUCCESS.
- Latest owner audio workflow `44893907029`: JVM issuer-proxy/contract job SUCCESS; isolated ARM13 build/test job queued/in progress. No APK artifact yet.

## Authoritative next-chat handoff — 21.11.2026

The concise continuation brief is now saved at [CELIKOM-A1-NEXT-CHAT-START-2026-11-21.md](CELIKOM-A1-NEXT-CHAT-START-2026-11-21.md). **Use it as the starting point**; it supersedes the older 'await NAV18' / generic next-step paragraphs above wherever they conflict.

Important correction from the actual BETA11 TXT: EXACT_PREPARE=ONE (so do not say there was no prepare); creator Track+Album later Flow link was observed once; however ORIGINAL_SETTER=NONE, NATIVE_MAIN_SOURCE_ENTER=NONE, WRAPPER_MAIN_SOURCE=NONE, TRACK_DESCRIPTOR_FACTORY_LINK=NONE, DECISION_ALTERNATE=NONE, DATASOURCE_ARMED=NONE, AUDIO_OPEN/READ=NONE. Original Exo reads are present but CELIKOM_REPLACEMENT=NOT_CONNECTED. OWNER_RESOLVE_NOT_APPROVED is an aggregate gate result, not proof of missing/unapproved DB row.

Current code snapshot before this documentation-only handoff: 4b0351eddf3daead5cc88c4e8a93f6079173b9bd; new handoff document commit 415d45988fe80d4e8295dceee219b50981ec9687 is docs-only. Fetch actual branch HEAD before coding.

CI at last check: workflow 44893907029 JVM issuer-proxy contract SUCCESS; native ARM13 publisher-first 75s test still running. 44893887129 clone-alone differential SUCCESS; 44893887112 exact identity Java models SUCCESS; previous owner-audio ARM13 run 44893567368 SUCCESS. No new owner APK exported or installed.
