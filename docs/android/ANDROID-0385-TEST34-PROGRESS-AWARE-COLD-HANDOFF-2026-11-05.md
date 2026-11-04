# CELIKOM Android Test.34 — progress-aware promoted prefetch handoff

Date: 2026-11-05. Status: experimental Test-only build; **not owner-acoustically accepted**.

## Non-negotiable accepted baseline

* **Owner's main acoustic reference remains Test.33**, immutable source SHA `53d94d66a32b332b62848e0895285d81dda226e9`, separate backup ref `backup/android-0385-test33-owner-accepted-20261105` pointing exactly at that commit. Never rebase, overwrite or merge into this backup. Original signed Test.33 APK and independent recovery kit are permanently linked in [the accepted Test.33 document](ANDROID-0385-TEST33-HONOR-LONGBROWSE-SEEK-REJOIN-2026-11-04.md).
* New isolated branch: `feature/android-0385-test34-cold-prep-handoff-20261105`, starting from docs SHA `365d4ec8c2dbf8c20d910fb7fe95718361282cad`. Separate app `pro.celikom.nativeprobe.test` / `0.3.85-test.34` versionCode `86119`, original signer. Stable Android, PC, Hostinger production, OTA, admin, source Track ID discovery, UI and native accepted seek remain untouched. No new permissions or Yandex pause automation.

## Concrete owner-forensic cause

Private owner HONOR Test.33 run `CELIKOM-combined-20261105-001528.txt`, third segment only, started 00:11:26 Minsk; do not commit private log/video. Johnyboy «Метамир» ID `42601865`:

1. Speculative lookahead starts `134.577s`, resolved `134.709s`, full-file transfer starts after its existing background yield.
2. Source selects it ~`136.020s` and fresh current resolve matches the **same edition / audio key** by `136.147s`.
3. Old Test.33 waits blindly 1.2s, then at `137.348s` **cancels its still-advancing lookahead file** and starts a duplicate foreground sparse download at `137.355s`.
4. At cancellation, its just-abandoned file had already received **8,592,404 bytes**. A later complete download of that same edition was **11,446,773 bytes**; approximately 75% of the final file was thrown away.
5. New sparse start became ready at `138.636s`, then the guarded 160ms handover completed `139.520s` — roughly **3.5s after song boundary**. Cannot infer exact possible savings without a real phone retest; original and replacement PCM not measured.

There were also genuinely unknown album selections (not eligible for lookahead) later in the same 242s run. This change specifically addresses **inflight predicted song promotion**; it cannot magically anticipate a randomly tapped song before user selection.

## Test.34 functional change

1. `AudioTransfer.copy` emits **validator- and Content-Length-bounded progress** from its real verified full-file copy, with zero changes to resume/If-Range, cancellation, network priorities, 30MiB single-file cap or file storage. Existing callers keep their old overload.
2. `NativeApi.AudioResult` gains an optional default `progress` callback. Every lookahead transfer gets its own `LookaheadHandoffProgress`; the owner reads only volatile counts/time, not network data or another player's position. An obsolete transfer cannot change a new track's progress tracker.
3. For **fresh-key-verified current promotion** only, keep the existing 1200ms current wait if transfer is slow, stale, unknown-length, under 60% complete, canceled or inactive. At the old expiry, if the **same** full-file download is at least 60% complete, actively advancing within 350ms and predicted remaining time is within 800ms, allow another 100ms check. Absolute new grace is **at most 900ms**. If delivery stalls, key/owner/account changes, or budget expires, use the existing sparse/full fallback immediately; never take Yandex audio before verified decoder preparation. This is evidence-driven head-of-line avoidance, not a global fade/latency change.
4. Keep Test.33's new-song 160ms complementary transfer, bounded 12-file / 96MiB cache, stream runway guard, unchanged mid-song seek and pause behavior, next-track resolver, UI and permissions.

## Tests

`Test34PromotedHandoff` exercises: actual in-memory HTTP full-file progress callback (without network); a Test.33 Johnyboy 75%-complete download handed off **without duplicate fetch**; slow progress fallback at original 1200ms; a stalled near-complete candidate revoking quickly; bounded extra wait even with continued progress; invalid/stale/untrusted lengths; and late canceled callback cannot play. All frozen host tests (Test.23/28/30/32/33 seek, source owner, long browsing, 300-song virtual replay) run as before.

Local full host suite: **PASS** (61 new Test.34 assertions including transport callback; Android API36 and D8 require GitHub CI). Test package contract: **PASS**. Device audio remains unverified until owner listens; signed APK source SHA, full CI run ID, signer and permanent APK hash must be pinned after successful workflow.

## Remaining limitations for owner feedback

* Random previously unseen tracks still require fresh identity, access authorization, audio bytes and decoder startup. We cannot start their audio before knowing which track user chose. Existing original-until-safe-runway avoids replacing stream with only one 128KiB block.
* The user-reported RASKOL «Нас не понимают вообще» and Лёша Свик «Дым» finger-seek artifacts remain OPEN. Fresh Test.33 native seek ACKs were 30–65ms after Media3 reported new positions but do not verify the audible sample. Do not alter the existing golden seek blindly.
* Cross-source level/timbre change remains audible; external source PCM is not available to directly calibrate the two masters. No unverified boost/equalizer modification or prolonged automatic Yandex pause was introduced.
* CI success validates build and state-machine regressions, **not acoustic quality**. If Test.34 is worse than Test.33, install the exact owner-accepted Test.33 APK from its independent recovery kit, and restart future work from its frozen commit.
