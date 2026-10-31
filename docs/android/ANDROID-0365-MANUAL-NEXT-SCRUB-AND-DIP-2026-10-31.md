# Android 0.3.65 / versionCode 66 — manual Next, partial stream seek, exclusive transition

Date: 2026-10-31. Scope: Android native companion only; preserve package, signing, updater, and existing desktop/server applications.

## Device report and 0.3.64 evidence

Owner's HONOR NTH-NX9 (Android 13): finger scrubbing is mostly acceptable when the song changes automatically. Immediately after pressing Next, finger scrubbing causes audible jumps. New-song attachment still has an audible sudden entry; owner asked for a 500ms down/up volume transition instead of repeated short overlap patches.

The supplied combined 0.3.64 journal (last run begins 2026-10-31 12:23:30+03) shows partial HTTP streams begin playing with their prefix cached, while whole-song caching takes several seconds. Explicit user seeks into uncached ranges run for ~200–350ms. The 260ms muted-source hold (`replacement_scrub_hold`) expires during these seeks (`replacement_scrub_fallback` on «Солнца не видно», «Крылья», «Монпасье»), making repeated Yandex→CELIKOM handovers audible. Previously cached «Толер» does not exhibit that same sequence. This explains the manual Next vs natural/loaded-track difference without asserting that a headset was measured by software.

## Combined change

1. Keep the verified `AudioOwnership` lease, same decoder, current track, and command ticket. Before the decoder can output, require the confirmed decoder clock and ≤350ms source alignment. Existing timeout, pause, route, changed track, account, buffer and effect-control checks remain.
2. If user finger-seeks while `streaming!=null && !streaming.complete()`, **do not enter the 260ms muted original hold**. Silence the decoder, restore Yandex using the retained effect and let the one in-flight asynchronous decoder seek finish. Do not restart downloads, attach a new DSP effect, or issue duplicate native seeks.
3. Once the decoder is aligned and truly advances again, do one exclusive 500ms join: 250ms gradually lower original from 100% to zero while replacement remains 0%; grant verified ownership only when original is fully muted; 250ms raise replacement from zero to full while original remains muted. There is no overlap of two independently clocked versions. The brief volume valley is deliberate, per owner's proposal; its subjective acceptability requires phone listening.
4. Fresh-track cold attachment uses the same 500ms exclusive join. Fully cached streams and local files retain the prior quick 260ms muted-original seek; they resume directly when current decoder is ready. The fallback still restores native source on a genuinely stalled cached seek.
5. Pause, native buffering, multiple seeks, changed track or Stop invalidates all queued transition commands; no stale source/effect ownership may revive old output.

## Tests and remaining verification

- `TestHonor064ManualNext`: real-engine manual Next → fresh partial stream → 500ms join → three 310ms uncached seeks → verified 500ms rejoin without 260ms fallback or extra downloads → completed stream fast seek → automatic Next → boundary cancellation during a partially completed dip; 48 assertions.
- `TestHandoverClock` and `TestStreamingEngine`: frozen decoder, timed 500ms phase boundary, recorded offsets, completion, cancellation; never two commanded audible versions.
- Existing `TestHonor063SeekScrub`, `TestHonor059Journal`, `TestAudioOwnershipRegression`, unified transaction and 15-hour run continue to enforce safety/regression behavior. The direct legacy near-terminal blend primitive remains unit-tested to prevent the 0.3.62 final-tick bug, but production cold joins do **not** call it.
- Host fake audio tests are deterministic and cannot verify physical speaker/hearing characteristics. Full Android SDK 36 and signed APK packaging remain mandatory in GitHub Actions. Device listening must check Next+scrub, auto next, seeking both cached/unloaded audio, pause/resume, route changes and perceived midpoint valley.

Release rule: one Android APK signed with existing key and published through the stable update manifest; user installs via in-app **Проверить обновление**. No desktop/backend changes.
