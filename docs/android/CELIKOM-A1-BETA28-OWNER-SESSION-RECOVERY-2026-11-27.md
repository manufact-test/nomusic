> **Historical BETA28 handoff.** BETA28 was subsequently delivered through Floki and tested; BETA29 NAV50 has since been built and delivered. The section below titled “BETA28 delivery status” records the earlier checkpoint before that delivery and is not the current project state. For current work, follow `docs/android/NEXT-CHAT.md` and the NAV50 correlation report.

# CELIKOM Android A1 — BETA28 owner session recovery

Date: 2026-11-27  
Repository: `manufact-test/nomusic`  
Branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`  
Source commit: `895306cee0934e245aeda7aaa0ce95f3b609eff2`

## Why BETA28 exists

The owner tested delivered BETA27 and reported:
- no audible alternative-audio replacement;
- the top diagnostic button status changed from the expected disabled/off label to `ОШИБКА`;
- TXT diagnostic export still worked.

The fresh BETA27 diagnostic `CELIKOM-A1-Diagnostics-1795803734296.txt` showed, in the current process summary:
- `BETA_OWNER_AUTO_START=FAILED`
- `OWNER_ENABLED=NONE`
- `OWNER_RESOLVE_REQUEST=NONE`
- `GRANT_ADMITTED=NONE`
- `FIRST_OPEN_DESCRIPTOR_LOST=NONE`
- `FIRST_OPEN_CANDIDATE_ACCEPTED=ONE`
- `FIRST_OPEN_SETTER_MATCH=ONE`
- `FIRST_OPEN_DEFERRED_ARM_CALLED=ONE`
- `DEFERRED_ARM_ENTER=ONE`
- `DEFERRED_ARM_NO_PENDING_APPROVED=ONE`
- `DEFERRED_ARM_ACCEPTED=NONE`
- `DATASOURCE_ARMED/AUDIO_OPEN/AUDIO_READ=NONE`
- `ISSUER_VALUE_TARGET_ALLOWLISTED=NONE`

The TXT export itself worked. The visible status comes from owner auto-start / session activation, not from diagnostic export. The counters above are process summary counters: do not infer that the accepted candidate is the intended «Ау», and do not combine counters across tracks or selection generations.

The precise cause of the BETA27 session failure was not established from the old generic status. Existing `NativeOwnerControlPlane.action` collapsed configuration, refresh, local token/storage and activation failures into a broad network/auth error. No authenticated server/DB check was performed. Server source confirms refresh-token rotation and the risk of replaying an already rotated token; do not retry an uncertain refresh automatically, reset user data, weaken entitlement, or bypass verification.

## BETA28 source change

BETA28 makes a narrow owner-session recovery change and retains the BETA27 audio descriptor-lifetime fix unchanged.

- Distinguishes configuration, refresh/session and activation failure categories.
- HTTP 401 on refresh or activation, and malformed saved-token state, map to a fixed `login_required` outcome.
- Fixed enum-like statuses only; do not emit secrets, raw tokens, response bodies or exception messages.
- Short press on the CELIKOM diagnostic control continues to export TXT.
- Long press opens a recovery menu with explicit `Проверить` and `Войти` actions.
- Login and activation are guarded against competing UI operations.
- If refresh fails or session rejection is confirmed, require explicit re-login rather than replaying a possibly rotated refresh token on activity resume.
- The re-login guard is process-local; it is not a persisted guarantee across process restarts.

No changes to Yandex authentication, server, catalogue, signed-grant authorization, original codec arguments, BETA27 audio identity guards, Windows, stable Android or OTA.

## CI / APK provenance

All relevant BETA28 source workflows completed successfully:
- Owner build/export and JVM issuer/proxy contract: run `46049315766`, attempt 1 — SUCCESS.
- Separate clone-alone Android 13 ARM13 differential: run `46049315771`, attempt 1 — SUCCESS.
- Renderer/observer JVM regression: run `46049315695`, attempt 1 — SUCCESS.

The owner run's Android 13 gate completed publisher-first / clone-second native launch for 75 seconds, with original publisher stable and concurrently installed. Its exact verdict is `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.

The report explicitly says:
- `audio_or_account_tested=false`
- `stage_a=NO_GO`
- `stage_b_current_player_album_edition_attested=false`
- `acoustic_replacement_proven=false`
- no MediaDataSource readAt candidates were observed.

This proves the scoped build/native-launch checks, not owner login, current-player interception, audio DataSource read, or audible replacement.

Owner APK:
- Filename: `CELIKOM-A1-RAMIL-AU-BETA28-HONOR50-20261127.apk`
- Size: `71,602,156` bytes
- SHA-256: `2c5dee053f2634224f929113e94b5aafe5ca5492160ed16f8e267020b394555c`
- Persistent owner signer SHA-256: `048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`
- Private unpublished draft release ID: `460950166`
- Draft tag: `celikom-a1-owner-46049315766-1`

The private draft has the exact APK asset, provenance, README and SHA256SUMS. It must remain unpublished.

## BETA28 delivery status — historical snapshot (superseded)

Trusted-main request JSON on `main` was updated by commit `64a1f36a5d3fb6951f327e28864fd5a10440203b` and read back as:
```json
{
  "run_id": 46049315766,
  "attempt": 1,
  "release_id": 460950166
}
```

- Floki spool workflow: `46052141389`.
- At last check, run status was `in_progress`; job `140685817495` (`stage-verified-signed-apk`) was also `in_progress`.
- The regular owner HTTPS delivery workflow `46052140482` was `skipped` at that checkpoint. This is not a successful delivery.
- No independent root-owned receipt, no confirmed live HTTPS readback, and no verified `A1_OWNER_DOWNLOAD_URL` has yet been established in this checkpoint.
- BETA27 remains the latest delivered APK until BETA28 passes the full Floki route.

Continue the existing trusted Floki path only. Poll `46052141389`; verify the independent root receipt, the live `celikom.com` HTTPS response (HTTP 200, expected APK content type, exact 71,602,156 bytes and SHA-256 above), and the unpublished draft readback. Only then retrieve and send the exact URL from the draft. Never synthesize a URL, use a GitHub download link, publish the draft, bypass root receipt, or expose the capability URL in Git/docs/logs.

## Owner test after verified delivery

Install BETA28 over BETA27. Do not uninstall CELIKOM or clear app data/cache.

1. Open CELIKOM and check the top status.
2. If it is not `ВКЛ`, long-press the diagnostic control.
3. For session failure, choose `Войти` and complete the normal CELIKOM login/verification. Use `Проверить` only when the session is believed to be valid.
4. Confirm the status becomes `ВКЛ`; if not, note the exact visible status and export TXT.
5. In original Yandex Music, test Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, segment `00:43–00:54`.
6. Test the second song that previously had leading gaps.
7. Export a fresh TXT using a short press. Keep the two track tests in the same Yandex session if possible.

Inspect owner activation/config/refresh/login/activation outcome first. Then inspect resolve/grant admission and the complete audio chain:
`FIRST_OPEN_HOOK_ENTERED` → `FIRST_OPEN_CANDIDATE_ACCEPTED` → `FIRST_OPEN_SETTER_MATCH` → `FIRST_OPEN_DEFERRED_ARM_CALLED` → `DEFERRED_ARM_ENTER` → `DEFERRED_ARM_ACCEPTED` → `DATASOURCE_ARMED` → `AUDIO_OPEN` → `AUDIO_READ`.

Keep each event scoped to the exact track and selection generation. Require the owner to confirm hearing the alternate sound. Never describe CI native launch as audio replacement.

## Required continuation reading

1. `docs/android/NEXT-CHAT.md`
2. `docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md`
3. This file
