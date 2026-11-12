> **W77 0.24.24 CI SUCCESS**: [Actions #43241899043](https://github.com/manufact-test/nomusic/actions/runs/43241899043). 87 native Node checks, .NET UI/support/installer checks, stage gate, publish and Inno Setup, installer SHA256 `E0E3A7BC3ED8D0C194471A2BCAECD88187A5A53567F76CD777346E2AD5AF4068`. Original approved W76 installed source was 0.24.23. Explicit independent W76→W77 inplace upgrade: [Actions #43242681592](https://github.com/manufact-test/nomusic/actions/runs/43242681592) (check final status separately). **No real-owner audible check yet.**

# CELIKOM Windows W77 — Kishlak «Самый лучший день» lost prefetch replacement (2026-11-12)

## Report from installed W76 0.24.23

Owner reported that browser extension plays the approved alternative of **Кишлак — «Самый лучший день»** correctly, while Windows 0.24.23 (native 0.24.23, modules match) plays a censored/muted section around minute 1. Windows owner diagnostics timestamp 2026-11-12T14:39:43 UTC, provided as a separate TXT. Real-audio audible identity remains unobservable in the existing telemetry: mapped source or 206 response is not proof of what the decoder ultimately played.

### Evidence

- **Read-only production catalog query** through trusted CI [43240364480](https://github.com/manufact-test/nomusic/actions/runs/43240364480): exact Yandex track **102494056**, artist **Кишлак**, title **Самый лучший день**, album **Эскапист**, replacement **#65**, status `approved`, `is_active=1`, asset `audio/mpeg`, **3,733,464 bytes**, version duration **93,336 ms** compared with original **93,250 ms**. File is registered and active. Other IDs in the same diagnostic: 103624638 = FLESH, Lizer «False Mirror», 59633283 = GONE.Fludd «Проснулся В Темноте», 126749933 = ФРЭНК «Саня».
- Diagnostic 14:35:02–14:35:03 UTC: `SOURCE_BATCH_REQUEST|track=102494056` → `RESOLVE_REQUEST` → `LOCAL_HTTP_TIMEOUT` after one second → `RESOLVE_BRIDGE_FAILURE` → `GRANT_MISS` / `RESOLVE_CANCELLED` → `RESOLVE_TRANSIENT` → `SOURCE_RECOVERY_SCHEDULED`.
- During the following minutes **no** `SOURCE_RECOVERY_RETRY`, `SOURCE_MAPPED|track=102494056`, or native `PLAYER_NET_*|resource_id=65` appears in the provided owner diagnostic. Contrast: for *another song*, the log records native audio resource 96 with 206; never conflate that evidence with Kishlak.
- **Reproduced code-level fault:** W76 renderer scheduled retry immediately at failure; its `createTransientSourceRecovery` cancelled the job when Yandex had not yet advanced from the prior track (it was a prefetched **future** song). There was no persistent `preload-failed → later-current-track` handoff or retry on later playback. The absence of the retry event matches this path.
- The owner-observed muted words are consistent with an original censored source being played after this miss, but without a decoder audio fingerprint this cannot be stated as independently proved.

## W77 fix — same Yandex player, no new audio engine

Working branch: `experiment/windows-w77-kishlak-audio-path-20261112`. Before-work backup: `backup/windows-w77-pre-kishlak-incident-20261112`, source `9e4fd1d6e56e8e102c4a244a0e46fc6ffdf191fc` (green W76). Target version **0.24.24**, native **0.24.24**.

1. New `windows-companion/w23/deferred-track-recovery.mjs`: retain only safe, numeric Yandex IDs that had **transient** foreground file-info failures. Max 12 queued candidates, 12-minute TTL, no raw URLs/tokens/metadata. This is **not** a positive authorization or a new player.
2. `renderer-entry.mjs`: W76 no longer schedules future tracks too early. On `RESOLVE_TIMEOUT` or `RESOLVE_TRANSIENT`, records candidate; checks only a *known* current playing/paused song via W60's official player-state observer. Once IDs match, schedules exactly one bounded W76 `prime` + existing `reloadEntity('QUALITY_CHANGE')`. Revalidated signed grant is mandatory. On real 404 no candidate or repeated network fetch. Stop/logout/change origin clears all candidates.
3. `host.cjs` invokes the deferred promotion on its existing ~2.2s state check (not 3Hz full polling), logs `SOURCE_DEFERRED_WAITING/PROMOTED/EXPIRED` and `SOURCE_RECOVERY_NO_LONGER_CURRENT`. W77 differentiates background timeout/transient from foreground to avoid a retry loop.
4. W60 `current-source-refresh.mjs` now supports an optional **expected current track ID**; if Yandex changes while a recovery is in flight, it does not refresh another song. Existing toggles without expected ID continue unchanged.
5. W77 GUI `BridgeServer.cs` reduces repetitive `NATIVE_STATE_RECEIVED` diagnostic entries from every ~0.37s to at most once per 10 seconds without altering state polling or the audio bridge, preventing important incident events from being evicted.
6. If W77 deferred recovery starts, GUI will show `NATIVE_RECOVERING` and then either mapped/unverified or source-failed status; does not claim audible replacement from 206 alone.
7. No server deployment, no production DB writes, no catalog/audio changes, no music player, no Yandex source or playback controls modified outside the already approved in-place official reload, no changes to extension or Android.

## Verification and next action

- Read-only production catalog query: CI **success** [43240364480](https://github.com/manufact-test/nomusic/actions/runs/43240364480).
- Windows compile/package tests: workflow `.github/workflows/windows-w77-kishlak-recovery-installer.yml` targeting run [43241899043](https://github.com/manufact-test/nomusic/actions/runs/43241899043), confirm CI status before claiming green. Tests include `deferred-track-recovery.test.mjs` (actual Kishlak ID 102494056, prefetch → current after 110s, dedupe, stopped), `renderer-relay.test.mjs` Yandex end-to-end current switch and source refresh, `current-source-refresh.test.mjs` wrong-current safety, existing native and Windows .NET regressions.
- Artifacts (once CI passes): `CELIKOM-W77-KISHLAK-PREFETCH-RECOVERY-UNSIGNED` contains setup EXE 0.24.24, same AppId, replaces native integration files. **Do not uninstall old CELIKOM.** For already-integrated Yandex, finish the normal consented native-module update inside CELIKOM. On initial diagnosis owner had 0.24.23 + matching native; merely copying an EXE cannot update an already-patched running Yandex process.
- **Human QA still required:** install W77 on owner's Windows and recheck «Самый лучший день» around minute 1 for full uncensored words, replay / Next / pause / seek; compare to browser extension. If still censored, export diagnostics and verify `SOURCE_DEFERRED_PROMOTED`, `SOURCE_RECOVERY_RETRY`, `SOURCE_RECOVERY_RELOAD_OK`, `PLAYER_NET_REQUEST|resource_id=65` and status; absence points at newer bottleneck.
- Do not claim success on real audio until owner hears it.

