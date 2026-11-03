# CELIKOM Test.11 owner diagnostic → one Test.12 candidate (2026-11-03)

## Inputs and observed limits

Private owner files: `CELIKOM-combined-20261103-163703.txt` (3,596 lines) and `SVID_20261103_163158_1.mp4` (~173.5 s); never commit raw journal, video or credentials. The **fresh Test.11 run** starts at combined line 1881, local 2026-11-03 16:31:49 +03:00. The earlier Test.8/Test.9 history must not be counted as new Test.11 incidents.

- On «Дым», Лёша Свик, source alias 122, video shows repeated dragging/preview around 0:30, 1:38, 3:13, 1:43, 3:36 and 2:01. The direct Media3 controller remains around 10–12 s during much of the activity. Only one actual source position jump is observed around elapsed 134,412 ms, to 106,360 ms; CELIKOM consequently submits seekSeq 23 and ACKs at 134,447 ms. Other visible drag positions have no corresponding Media3 source position/event. Therefore the frozen native seek/ACK method is not shown to be broken; the missing input signal remains the limitation.
- `legacy_position_source_unavailable` at 77 ms with `stage=browser_connect` proves that Test.11's optional platform observer was rejected, so `source_seek_platform_recovered` could not run. An earlier 0.3.16 real HONOR probe had already found a rejected legacy browser connection; do not repeat this same unverified fix as if it were new evidence.
- 19 source boundaries, 18 completed replacement transitions. Four non-primed cold joins took 2,041–3,381 ms; fourteen primed joins completed in 238–397 ms. A playlist/manual-selection change invalidates unrelated future primes, then a new full download takes ~1–2+ seconds. Local-file seek is fast once loaded, but unpredictable current song selection cannot be prefetched exactly by the existing one-next-item lookahead.
- One `replacement_drift_unstable` at 11,669 ms restored original with reported drift 914 ms; no reliable source PCM/acoustic phase is exposed. Do not infer an exact waveform cause.
- Some measured duration deviations are larger (e.g. «Биг сити лайф» file ~1.35 s shorter, «Крылья» ~0.58 s shorter, «Дым» ~0.37 s longer). This is not proof of onset offset but reinforces that exact acoustic sameness is unverified. An exclusive switch after ~0.25–0.4 s of original can remain perceptible even with low transport latency.

## Candidate Test.12: more retained warm local files

A bounded, account-scoped in-session warm-file cache keeps up to 8 recent files / 96 MiB instead of 3 / 60 MiB. This is a **different way to reduce repeat and playlist-reorder cold joins**, without touching the accepted `ReplacementEngine.seek()` / `completeSeek()`, local full-file source path, gain ownership, crossfade or Yandex transport. The trimming helper protects both the just-cached file and a still-active speculative decoder's file, and records eviction reason/byte count without raw paths. Cache contents remain private and cleared on Stop/account-state cleanup. New host policy tests pin limits and negative boundaries. This may turn subsequent selections into cached local joins; it **cannot** make the first arbitrary uncached selection instantaneous.

Test package stays `pro.celikom.nativeprobe.test`, label CELIKOM Test, version `0.3.85-test.12`, code 86097. Signed ZIP and acoustic field acceptance are **pending CI and owner listening**. Do not test Test.10 separately.

## Remaining strategic blocker, not to disguise

A second public platform MediaBrowser has failed on HONOR; the current read-only Media3 signal sometimes never reports the Yandex UI scrub. No APK can reliably reconstruct an unreported numeric position using this same signal. An optional visible UI observer (Accessibility permission), OS-level playback capture, or a direct source integration would be a materially different permission/architecture contract requiring separate explicit owner approval and physical feasibility tests. Do not silently add these permissions, send hidden playback commands or weaken the stable seek guard. Preserve original fail-closed if source authority becomes unsafe.

For acoustic first-note seams, the current source and replacement transport clocks do not measure PCM alignment. Future stronger options require a separate experiment with explicit proof; do not promise imperceptible transitions on uncached arbitrary manual choices.

## Safety and verification

- Stable `0.3.85/code86`, backup refs, Hostinger, `stable.json` and PR#37 merge state unchanged.
- No raw owner files in Git.
- Required CI: native host suite; new cache limits; frozen HONOR seek source SHA; Android API36/D8; signed isolated APK and original signing certificate; stable publisher skipped.
- Deliver **one** direct GitHub Actions artifact ZIP only after a successful run. Report plainly if any original issue remains unresolved; do not call Test.12 phone-verified before listening.

## Verified signed candidate (2026-11-03)

- Final functional SHA: `d024db87d0e802327fa658407e659c47c1692cda`.
- GitHub Actions full CI [#41648755376](https://github.com/manufact-test/nomusic/actions/runs/41648755376): **success**. Native host suite, 300-song automatic activity, frozen seek hash, Android API36/D8, isolated signed APK and original certificate checks passed; stable publishing skipped.
- [Download ZIP artifact 13236337823](https://github.com/manufact-test/nomusic/actions/runs/41648755376/artifacts/13236337823). Name `CELIKOM-Test-0.3.85-test.12-code-86097`; APK `CELIKOM-Android-0.3.85-TEST-12-WARM-CACHE-SIGNED.apk`; APK SHA-256 `6415b13e009c48aea912b9fb19eb1e9f63fc9463d9ef8184915ec8bcd8f4bf36`, signer matches original, v3 signature verified.
- Owner's HONOR listening/seek acceptance **pending**. Critical: do not call «Дым» repaired; no new position source was added. This build improves bounded repeat/playlist cold-cache behavior only.
