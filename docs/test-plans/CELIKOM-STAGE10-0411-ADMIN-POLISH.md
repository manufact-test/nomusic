# CELIKOM 0.4.11 — owner review fixes, 2026-10-11

Stage10 / Issue9 remains OPEN. Owner confirmed public MP3 upload, moderation and playback; requested four fixes and explicitly authorized implementation after collecting feedback.

## Result

- Admin input/select/textarea focus uses the existing green border, without an offset outline. Button/link keyboard indicators remain available.
- Uploaded versions always sort by numeric ID descending (newest first), independent of moderation status. Existing status filters remain.
- Popup distinguishes exact track detection from version presence: absent, pending moderation, available. A failed presence check never claims that audio is missing. Track changes discard stale responses; presence refreshes at most once per15seconds while popup is open and active replacement reports availability directly.
- Suggestions default to the pending queue. Progress is derived by exact service + Track ID: uploaded MP3 moves a proposal to “Версия на проверке”; active approved version to “Версия доступна”. These remain accessible through filters. Rejected audio reopens a pending proposal. Original proposal decisions and audit history are preserved; no DB rewrite or schema migration.
- New bearer-only read-only version-status endpoint returns only `{status}`, without assets, credentials or uploader information. It does not start trial or depend on the uploads switch. Existing duplicate prevention and playback authorization unchanged.

## Verification / release

Source06fd6f8ed728571483feeeca65377e42158cdfa5. LocalCI:125 extension +17PoC tests PASS; PHP runtime verified in GitHub CI38096633131 PASS (PHP8.3/MySQL8/browser suite). Private Chrome build38096630320 PASS; ZIP bytes match a local rebuild from the same source.

SHA256 CELIKOM-0.4.11-stage10.zip: `5ce6708a60bf662b49aaaaaada6db5ed66223a1fa649d1882b209bfeb64bb9a8`.

Pre-rollout snapshot38096630329 PASS:24SQL tables /7audio objects, including owner uploads. Backup gates now respect the owner’s current moderation decisions for legacy#2/#3; operations never activate or change those records. Approved144530503/#1 remains protected.

Pre-rollout isolated recovery38096739223 PASS: config and7audio restored and verified, actual MySQL schema and approved mapping recovered without touching live files/database. Rollout evidence pending.

## Owner check

Update the CURRENT extension folder in place to0.4.11, reload extension and Yandex tab; use existing account. Refresh admin page. Check login field focus, version numeric ordering before/after moderation, popup status on absent/pending/approved tracks, and suggestion progress in default queue and history filters. No new registration, test token or separate final client.

PR6 stays OPEN/unmerged, Issue7 stays OPEN. No repeat trial reset, credential rotation, media replacement or automated approval.
