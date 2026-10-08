# ADR 0005 — private test API, exact catalog and Range audio

Status: implemented for Stage 4, 2026-10-08.

PHP 8.3/MySQL provides `/api/v1` with health/config/resolve/audio/events. Resolve requires exact `service + service_track_id`, prepared SQL and an approved active mapping. A generated unique active_track_id prevents two approved active versions for one track. Assets are independent of mappings and deduplicated by SHA-256; storage keys remain private.

StorageAdapter defines stream/put/exists/delete/move/size/MIME operations; the initial factory supports LocalStorageAdapter. A future remote driver changes server infrastructure while retaining the client API. Local directories must be outside web root and reject traversal/symlink escapes. Server trust is limited to owner-reviewed fixtures; full metadata extraction/moderation belongs to later stages.

Resolve signs `replacement_id + version + expires` using HMAC-SHA256. Audio rechecks approval/version/file and validates the signature before opening the stream. GET supports one Range, bounded suffix/open-ended ranges, 206/416, Content-Range and exact Content-Length. HEAD ignores Range and returns full headers. Multiple ranges are rejected; If-Range mismatch returns full 200. Output compression must be off. Signed URLs are sensitive temporary bearer capabilities: exclude them from client diagnostics and restrict server access logs.

The MV3 worker uses one build-time HTTPS origin, fixed routes and bounded JSON. Host permissions include exactly that origin, never arbitrary URLs. Config/resolve caches are bounded and token-expiry-aware; remote audio uses native HTMLAudioElement and CORS. No original guard is acquired until loading, duration checks and binding revalidation succeed. Stale loads and API/media errors preserve or restore original audio and stop automatic same-track retries until explicit Start/track change.

Until account and entitlement stages, a private beta code gates resolve/events. It is stored only in server environment and extension local storage, never in bundles/Git/diagnostics. This does not authorize a public client release. Analytics default off; event IDs deduplicate retries, installation IDs are keyed-hashed, allowlisted discrete properties exclude track history/URLs/financial claims. SQL daily aggregation and retention provide later admin foundations.

Automated MySQL/PHP/HTTP/native Chromium checks validate this contract. They do not prove Yandex CSP, natural autoplay permission, hosting limits or HTTPS configuration; those remain the Stage 5 live gate.

Primary protocol references: [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), [Chrome extension network requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests), [PHP stream output](https://www.php.net/manual/en/function.fpassthru.php).
