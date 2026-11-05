# CELIKOM Android 0.3.85 Test.36 — verified in-flight lookahead takeover (2026-11-05)

## Decision and immutable rollback

**Test.33 is the owner-accepted best sounding reference, not superseded by this experiment.** Exact functional SHA `53d94d66a32b332b62848e0895285d81dda226e9`, immutable branch `backup/android-0385-test33-owner-accepted-20261105`. Original owner-accepted signed APK SHA256 `7c51a7a394e53462b171ed3250953fbb7ab840a54587b4c89548aa957489a5e3`, Library ID `libfile_0924722c86908191bef31db36cfcf0ed`. Complete rollback ZIP Library ID `libfile_670135d6fbec81919cbac9cc1e75a4cb`. Do not modify either frozen branch or APK.

**Test.34 and Test.35 were not accepted by owner.** Paired user evidence Test.33→Test.35 on 18 matching tracks showed 15 slower joins, mean +382 ms, median +208 ms; Test.35 replaced the efficient complete-file lookahead with partial streaming too often. Preserve Test.33 full local-file path and its exact original source/seek and 160 ms complementary blend.

## Actual cause found in Test.33 forensic

From `CELIKOM-combined-20261105-120605.txt`, Johnyboy «Метамир», track `42601865`:

1. `elapsed_ms=134577`: correctly identified the next song, speculative full-file prefetch started.
2. `136036`: candidate became current while prefetch was downloading; fresh current resolve checked the edition.
3. `137348`: arbitrary 1,200 ms timer fired. Current preparation canceled the in-flight whole-file transfer and restarted with sparse Range.
4. `137373`: transport cancellation logged **8,592,404 already received bytes discarded** (`reasonCode=download_cancelled`, `priority=lookahead`).
5. `138637` onwards: another sparse connection prepared the same audio, followed by decoder alignment/runway wait and audible late joining.

This is a concrete source of avoidable delay, distinct from the remaining amplitude/timbre click (which cannot be proved away without original-session PCM and sample-accurate mixing).

## Test.36 mechanism

- A new isolated `LookaheadTransferState` tracks verified HTTP response length, received bytes, last transport progress and whether the transfer has been *promoted* to current priority.
- **Promotion requires both exact lookahead Track ID/current alias and a fresh matching replacement edition key**. A different version or account can never borrow speculative bytes.
- `AudioTransfer.copy` reports byte progress only after writing validated 200/206 response bytes; existing ETag/If-Range resumability and account/source leases are retained.
- Once freshly verified as the current song, the existing speculative whole-file connection no longer yields to unrelated foreground demands and **no duplicate download is launched** while it finishes.
- The original 1,200 ms timer still applies to a transfer that is stalled, too small, unverifiable or making insufficient progress. Only an already-progressing full transfer at >=60%, >=1 MiB and progress within 450 ms can extend briefly, with an absolute 2,600 ms wait ceiling. On failure/cancellation, return to the original verified sparse/full fallback; source stays audible until a valid decoder is ready.
- Fully downloaded lookahead is still cached/primed as in Test.33; cached seeks and owner-accepted 160 ms output handover are untouched.
- Opt-in exists **only in separate CELIKOM Test service** via fourth `ReplacementEngine` constructor boolean; existing three-argument production regression constructor remains frozen.

## Evidence and limits

`Test36TransferTakeover` exercises simulated 8.7 MB current promotion, no duplicate download, source not muted, stalled progress, wrong edition, unchanged Test.33 path and actual `AudioTransfer.copy` progress callbacks. **74 specific assertions pass**. Complete native host suite, Android build contract, baseline seek hash gates and previous replay tests pass locally. SDK 36/DEX/signed APK must be verified in GitHub Actions.

Expected benefit is fewer needless 1.2s prefetch cancellations *where nearly complete whole-file data already exists*. This does **not** fix songs with no next-item lookahead, inaccurate track metadata, independent source-vs-replacement mastering volume, or a genuine native finger-seek stall. Do not describe this as sample-accurate seamless playback. Only the owner HONOR listening test determines acoustic acceptance.

## Build provenance

- Repo: `manufact-test/nomusic`
- Experiment branch: `feature/android-0385-test36-audible-handoff-20261105`
- First validated functional GitHub commit: `c131268c8980a1d76b2ad2057df727b63f97ca10`; Git tree `90f1c6757e84ded8fbf4ef3031fa206e3a9eccdf` equals locally tested tree.
- Test package separate: `pro.celikom.nativeprobe.test`, app label `CELIKOM Test`, version `0.3.85-test.36`, code `86121`.
- GitHub Actions [full validation and signed test build **SUCCESS** #42003789761](https://github.com/manufact-test/nomusic/actions/runs/42003789761); both native SDK36/DEX and signed side-by-side build succeeded.
- **Original-signer v3 signed Test.36 APK**: permanent Library ID `libfile_22de1c2148248191a1e5a95d38b1022a`, [download](https://chatgpt.com/library?file_id=libfile_22de1c2148248191a1e5a95d38b1022a&account_id=personal). Filename `CELIKOM-Android-0.3.85-TEST-36-VERIFIED-TRANSFER-TAKEOVER-SIGNED.apk`, exactly `8,812,697` bytes, verified SHA256 **`6099d3cb9c18ff69a2b2cc6eaaf400f300ea14353de5f512146148b2ba3ac44b`**, signer SHA256 `67fe81c56fac1c1d145344b69a0e3faf9005cf6607f4e26ca27d5926c3eefc4f`, v3 true, v2 false as in original signer. Original signed receipt from CI matched every APK byte and records `physical_phone_playback_verified=false`, `acoustic_acceptance=false`.
- Stable Android package, original APK, signing inputs, Hostinger, OTA and PC extension are unchanged.

## Owner test checklist (one combined drive)

1. Known fast first ten playlist songs: must not worsen vs Test.33.
2. Arbitrary album selections, especially Johnyboy «Метамир»: watch whether `replacement_lookahead_transfer_promoted` and `replacement_lookahead_transfer_near_complete` occur, and count `replacement_lookahead_prefetch_current_fallback` vs Test.33.
3. The same two troublesome finger scrubs RASKOL «Нас не понимают вообще» and Лёша Свик «Дым»: only regression check; their root issue remains open.
4. Report loud clicks, overlap, missing replacements, >2.6s current wait. If worse, revert immediately to immutable Test.33 APK; do not “recreate” Test.33 from changed source.
