# CURRENT HANDOFF — BETA29 delivered; awaiting owner phone diagnostic

Date: 2026-11-27
Repository: `manufact-test/nomusic`
Working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`

## Read first

1. `docs/android/NEXT-CHAT.md` — this handoff.
2. `docs/android/CELIKOM-A1-FLOKI-DELIVERY-REPAIR-2026-11-25.md` — trusted delivery and root verification.
3. `docs/android/CELIKOM-A1-BETA28-OWNER-SESSION-RECOVERY-2026-11-27.md` — historical BETA28 session recovery; its delivery-pending section is superseded.
4. `docs/android/CELIKOM-A1-BETA28-ALT-DATASOURCE-LIVE-RENDERER-CORRELATION-2026-11-27.md` — BETA28 evidence and NAV50/BETA29 diagnostic design.

## Current state

**BETA29 has been built, signed, delivered and root-verified. The next step is the owner's BETA29 phone test and fresh TXT diagnostic.**

- BETA29 NAV50 source/export run: `46061697450`, attempt 1 — SUCCESS.
- BETA29 build source commit: `1afa88c78b5b3a3063fac5176f1152a95dcdf962`.
- NAV50 source change commit: `466eb2cd8b8de6ca6c6d3cff4cc1553cbe268f1d`.
- Private unpublished draft release: `461031098`.
- APK: `CELIKOM-A1-RAMIL-AU-BETA29-HONOR50-20261127.apk`.
- Size: `71,602,156` bytes.
- SHA-256: `5ae5c75a10daff02910fa5c2a8b4a10e0b02e28df2bfe6d1461d80337975b459`.
- Persistent owner signer verified; install mode is `UPDATE_EXISTING`.
- Direct HTTPS URL from `celikom.com` was read from the unpublished draft and sent to the owner in the preceding chat. Do not copy the capability URL/token into Git, docs, logs or public messages.

### Trusted delivery proof

- Floki manual workflow run `46064236455`, run number 33 — SUCCESS.
- Job `140727455245` (`stage-verified-signed-apk`) — SUCCESS.
- Independent root-owned consumer verified signer/package, source provenance, spool receipt, live HTTPS HTTP 200, APK content type, exact size/SHA-256 and unpublished draft readback. Final marker: `A1_ROOT_RECEIPT_AND_OWNER_DRAFT_LINK_VERIFIED`.
- Duplicate push-triggered run `46063409036` was cancelled by the workflow concurrency group. It is not the delivery run and does not invalidate the successful manual run.
- Draft release `461031098` remains unpublished.

## What BETA29 changes

BETA29 adds NAV50 read-only identity correlation. It does **not** change the audio route, player, Yandex codecs, server, authorization, Windows, stable Android or OTA.

It checks whether the exact DataSource that returned approved alternate bytes is also the DataSource belonging to the current live renderer period. The key counters are:

- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_NON_EOS` — strongest positive evidence: alternate bytes reached the current non-EOS Exo renderer source path.
- `LIVE_RENDERER_ALT_SOURCE_READ_SAME_CURRENT_PERIOD_EOS_UNKNOWN` — same source/current period, but EOS state is unknown; not full proof.
- `LIVE_RENDERER_ALT_SOURCE_DIFFERENT_CURRENT_PERIOD` — current period uses a different DataSource; investigate prefetch/stale generation or source binding.
- `LIVE_RENDERER_ALT_SOURCE_ARMED_NO_READ_CURRENT_PERIOD` — current period has the armed source, but no positive alternate read was observed for it.
- `LIVE_RENDERER_ALT_SOURCE_NO_ROUTE_CURRENT_PERIOD` — no matching alternate route for the current period.
- `LIVE_RENDERER_ALT_SOURCE_DATASOURCE_UNRESOLVED_CURRENT_PERIOD` — wrapper-to-DataSource identity could not be resolved.
- `LIVE_RENDERER_ALT_SOURCE_SLOT_OR_PERIOD_CHANGED` — holder/queue/period changed during the evidence check.

A same-source NAV50 counter proves that alternate bytes reached the active Exo source path, **not** that the user heard them. If positive, investigate extractor/decoder/output using the new evidence; do not rebuild source selection. If DataSource differs, investigate selection-generation/prefetch binding only. If unresolved, repair only the identity witness.

## CI gates — passed, but not audio proof

- Renderer observer JVM run `46060063393` — SUCCESS; NAV50 same-source/current-period and mismatch tests passed.
- Owner preflight run `46060063423` — SUCCESS; ARM13 native 75s verdict `METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO`.
- Clone-alone run `46060063402` — SUCCESS; verdict `CLONE_ONLY_STABLE_DIFFERENTIAL_NOT_PRODUCT_PASS`.
- Owner/export run `46061697450` — SUCCESS.
- Floki root-verified delivery run `46064236455` — SUCCESS.

These are build, stability, signing and delivery checks. They do not prove CELIKOM session state on the owner's phone, current-track interception or audible replacement.

## Owner phone test — pending

Install BETA29 **over BETA28**. Do not uninstall CELIKOM and do not clear app data/cache.

1. Open CELIKOM and check that its status is `ВКЛ`.
2. If it is not `ВКЛ`, long-press the diagnostic control and use the explicit `Войти` action if the session requires re-login. Complete normal CELIKOM authorization; do not change Yandex login.
3. In the original Yandex Music app, test Ramil / 10AGE — «Ау», album `38902809`, track `144530503`, segment `00:43–00:54`.
4. Test the second song that previously had leading gaps.
5. Export a fresh TXT diagnostic after both tests and attach it in the next chat. Keep both tests in the same Yandex session if possible.
6. Record separately whether the alternate sound was actually heard; counters alone are not a substitute for listening confirmation.

The owner will provide the BETA29 TXT in the next chat. Do not ask for another BETA28 diagnostic or ask the owner to repeat information already documented. First inspect the newly attached BETA29 TXT, correlate NAV50 counters per track/selection generation, then decide the narrowest justified next step.

## Engineering guardrails

- Do not start a second player or new audio architecture.
- Do not change audio mechanics, codecs, transcoding or source selection without diagnostic evidence.
- Do not modify server, catalogue, signed-grant authorization, Windows, stable Android or OTA without direct evidence.
- Do not build another APK before analysing the BETA29 phone diagnostic.
- Do not infer audible replacement from native launch PASS, `AUDIO_READ`, or a NAV50 same-source counter alone.
- Keep owner drafts unpublished and use only the trusted Floki/root route for any future owner APK. Never send GitHub APK links or fabricate a celikom.com URL.
