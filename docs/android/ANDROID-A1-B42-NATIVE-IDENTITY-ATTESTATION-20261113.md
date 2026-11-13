# CELIKOM Android A1 — B42 exact native identity attestation

Date: 13 November 2026  
Status: experimental server implementation committed; isolated PHP CI PASS; not deployed.

## Why this was needed

The native source contract accepts a replacement only when the selected Yandex item and the server grant attest the same exact track ID, album ID and edition ID. This is deliberate: title, artist, cover and track ID alone do not prove that the selected edition is the intended one.

The previous server could not satisfy that contract:
- The tracks table stored a display album string, not the native album ID or edition ID.
- TestAudioImporter stored artist/title/album labels only.
- PdoCatalogRepository selected no album/edition identity.
- ResolveService returned the track-level replacement URL, duration, MIME, version and expiry only.
- The B42 JS contract already has a regression test requiring the real backend without album/edition attestation to fail closed.

## Experimental change (not deployed)

1. Additive migration 019_android_a1_native_identity.sql adds service_album_id (24-character ASCII exact) and service_edition_id (128-character UTF-8 binary exact). Both are nullable. NULL means unverified; B42 must leave the original source selected.
2. Owner-only /admin/native-identity UI appears on upload cards. It requires both exact IDs, checks the expected Yandex Track ID, supports an explicit reset, uses CSRF and owner-role checks, and writes before/after values to audit_log. It does not accept display album names as identity.
3. PdoCatalogRepository returns the exact stored IDs. ResolveService adds:
   - track_id: exact requested Yandex track ID.
   - approved=true: only because the repository returns active approved mappings.
   - entitled=true only when the request passed authenticated user access and entitlement.
   - album_id and edition_id: exact stored values or NULL.
4. Private test API-token requests deliberately receive entitled=false. A test token must never masquerade as a real user entitlement.
5. The native adapter must map API snake_case fields to the normalized B42 contract: track_id to trackId, album_id to albumId, edition_id to editionId. This adapter mapping is not yet implemented or runtime-tested.

## Validation

Isolated workflow: .github/workflows/android-a1-native-identity-contract.yml  
Run: https://github.com/manufact-test/nomusic/actions/runs/43440938988  
Result: SUCCESS.

It runs PHP syntax checks and server/tests/android-a1-native-identity.php with in-memory SQLite and fake storage. It verifies owner identity write, exact round-trip, audit and idempotence; partial, malformed, control-character and stale identities rejected; non-Yandex tracks rejected; active approval explicit; user-access path reports entitlement true and remains session-bound; private API token reports entitlement false; missing identity remains NULL. Existing replacement-catalogue tests also pass.

The workflow has no secrets and no deployment step. It does not connect to Hostinger, production MySQL, account services or Yandex.

## Still blocked

- No separate authorized test account or permitted Yandex test track/album/edition values have been recorded.
- Do not populate IDs from a title, cover, display album label, guess or static DEX clue.
- Do not deploy migration or PHP changes to Hostinger yet.
- No live music, exact native source identity, pause/seek/radio or audible substitution is proven.
- Existing B42 source contract remains disconnected. Do not weaken exact identity, entitlement, ETag/Range or fail-closed rules.
- Do not touch Test.50, Windows, production, original installed Yandex or the owner's HONOR 50.

## Next exact sequence

1. Obtain a separate authorized test account and one permitted track for the disposable ARM13 clone; do not send credentials in chat.
2. During actual playback capture exact native trackId + albumId + editionId and sanitized MediaExtractor/readAt/same-object witness markers.
3. Only then populate the owner-only exact identity fields for that reviewed test mapping, verify authenticated Resolve returns matching fields and entitled=true, and map the response into B42.
4. Integrate before the existing decoder only after same-object/source path and grant identity are independently established. Test actual sound and controls; no second player.
