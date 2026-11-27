# CURRENT HANDOFF — BETA28 ready; finish trusted delivery, then send owner APK

Date: 2026-11-27  
Repository: `manufact-test/nomusic`  
Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## What the next chat must do first

**Do not rebuild BETA28 and do not start another code experiment.** BETA28 is already built, signed and passed its required source/JVM/native-launch workflows. The owner is waiting for the installable version.

The only outstanding step is to finish the existing trusted Floki delivery, independently verify the direct `celikom.com` HTTPS URL, and send that exact URL to the owner. Do not send a GitHub download link. Do not reuse the BETA27 URL or guess a capability URL.

## Required reading

1. `docs/android/NEXT-CHAT.md` (this handoff)
2. `docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md`
3. `docs/android/CELIKOM-A1-BETA28-OWNER-SESSION-RECOVERY-2026-11-27.md`

The older BETA26 diagnostic plan is superseded for the current build. BETA27's descriptor-lifetime fix remains part of BETA28; see the BETA27 handoff document referenced in the delivery repair record if historical detail is needed.

## BETA28 source and successful checks

- Source commit: `895306cee0934e245aeda7aaa0ce95f3b609eff2`.
- Owner build/export + JVM issuer/proxy contract: run `46049315766`, attempt 1 — SUCCESS.
- Separate clone-alone Android 13 ARM13 differential: run `46049315771`, attempt 1 — SUCCESS.
- Renderer/observer JVM regression: run `46049315695`, attempt 1 — SUCCESS.
- Android 13 publisher-first / clone-second native launch completed for 75 seconds.
- Exact verdict: `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- The report says `audio_or_account_tested=false`, `stage_a=NO_GO`, `stage_b_current_player_album_edition_attested=false`, `acoustic_replacement_proven=false`. No MediaDataSource readAt candidate was observed.

## Exact BETA28 APK identity

- Filename: `CELIKOM-A1-RAMIL-AU-BETA28-HONOR50-20261127.apk`.
- Size: `71,602,156` bytes.
- SHA-256: `2c5dee053f2634224f929113e94b5aafe5ca5492160ed16f8e267020b394555c`.
- Persistent owner signer SHA-256: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`.
- Private unpublished owner draft release ID: `460950166`.
- Draft tag: `celikom-a1-owner-46049315766-1`.
- Draft has the exact APK, provenance, README and SHA256SUMS assets. Keep it unpublished.

## Delivery checkpoint — must resume here

Trusted-main request JSON on `main` was updated by commit `64a1f36a5d3fb6951f327e28864fd5a10440203b`; readback was:
```json
{
  "run_id": 46049315766,
  "attempt": 1,
  "release_id": 460950166
}
```

- Floki spool workflow: `46052141389`.
- Job: `140685817495`, `stage-verified-signed-apk`.
- Last verified state: workflow `in_progress`; job `in_progress`; job logs/steps were not yet available through the GitHub API.
- Regular HTTPS delivery workflow `46052140482` was `skipped` at that checkpoint.
- No independent root-owned receipt or verified `A1_OWNER_DOWNLOAD_URL` was yet confirmed.
- BETA27 remains the latest delivered APK until this completes.

Poll `46052141389` and inspect job `140685817495`. Follow only the existing `.github/workflows/android-a1-owner-floki-spool.yml` trusted-main route. Require:
1. source run/release/provenance, exact APK size/hash and signer checks;
2. immutable staging;
3. independent root-owned receipt;
4. live `celikom.com` HTTPS readback: HTTP 200, expected APK content type, exactly 71,602,156 bytes and SHA-256 `2c5dee...`;
5. unpublished draft update/readback containing exactly the actual `A1_OWNER_DOWNLOAD_URL`.

Only after all five pass, retrieve the URL from the draft and send it directly to the owner. Do not put the capability URL/token in Git, docs, logs, summaries or public messages. Do not publish the draft, bypass root receipt, use direct SSH, or fabricate a URL. If the spool run fails or stalls, diagnose/retry the existing trusted path without changing APK bytes or bypassing the root consumer.

## What BETA28 changes

BETA28 is a narrow owner-session recovery change on top of BETA27:
- Fixed categories for configuration, refresh/session and activation failures.
- HTTP 401 on refresh/activation and malformed saved-token state map to `login_required`.
- No raw secrets, tokens, response bodies or exception messages in diagnostics.
- Short press on the CELIKOM diagnostic control still exports TXT.
- Long press opens recovery menu with `Проверить` and `Войти`.
- Competing login/activation operations are guarded.
- After refresh failure/session rejection, require explicit re-login rather than replaying a possibly rotated refresh token on activity resume.
- This guard is process-local, not persisted across process restarts.

Do not change Yandex auth, server, catalogue, signed-grant authorization, original codecs, BETA27 audio identity guards, Windows, stable Android or OTA.

## Owner instructions after delivery

Send the verified direct `celikom.com` URL and tell the owner:
1. Install BETA28 over BETA27. Do not uninstall CELIKOM and do not clear app data/cache.
2. Check the top CELIKOM status. If it is not `ВКЛ`, long-press the diagnostic control.
3. Choose `Войти` for a session failure; complete normal CELIKOM login/verification. Use `Проверить` only if the existing session is believed valid.
4. Confirm `ВКЛ`. If it still fails, note the visible status and export TXT.
5. In original Yandex Music test Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, segment `00:43–00:54`.
6. Test the second song that previously had leading gaps.
7. Short-press the diagnostic control to export a fresh TXT after both tracks.

For the next diagnostic inspect owner config/refresh/login/activation first, then resolve/grant admission and:
`FIRST_OPEN_HOOK_ENTERED` → `FIRST_OPEN_CANDIDATE_ACCEPTED` → `FIRST_OPEN_SETTER_MATCH` → `FIRST_OPEN_DEFERRED_ARM_CALLED` → `DEFERRED_ARM_ENTER` → `DEFERRED_ARM_ACCEPTED` → `DATASOURCE_ARMED` → `AUDIO_OPEN` → `AUDIO_READ`.

Keep events separated by exact track and selection generation. Require the owner to confirm that the alternative sound is actually audible. CI success is not audio replacement proof.

## Owner communication

The owner asked to save this work for the next chat and expects that chat to deliver the BETA28 install link once the trusted HTTPS route is verified. Do not ask the owner to resend information already in this handoff. Do not ask for a new diagnostic before BETA28 has been delivered and installed.
