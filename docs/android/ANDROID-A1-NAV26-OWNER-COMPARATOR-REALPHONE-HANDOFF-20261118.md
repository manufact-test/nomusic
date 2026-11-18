# CELIKOM Android A1 — NAV26 signed owner diagnostic handoff (18 Nov 2026)

## Current state — authoritative

- Repository: `manufact-test/nomusic`.
- Sole working branch: `experiment/android-a1-metrica-init-state-observer-arm13-20261112`.
- Branch HEAD at handoff: `9916ac13c6a862f9fbe485c281c141879164806f`.
- Protected pre-handoff backup branch: `backup/android-a1-nav26-owner-signed-arm13-ci-green-pre-handoff-20261118`, created at the same HEAD.
- NAV26 observer source checkpoint: `19c73c433eee23359566c3df2a3a0e5e52756b9c`.
- NAV26 JVM regression CI #44259704837: **SUCCESS**.
- NAV26 exact signed Android13 ARM CI #44259704834: **SUCCESS**, final head `19c73c433eee23359566c3df2a3a0e5e52756b9c`.
- Successful workflow artifact: `CELIKOM-A1-NAV26-Owner-Renderer-Comparator-20261118`, artifact ID `14406884183`. The artifact was downloaded and inspected locally; it contains the APK and README. Do not use a GitHub Actions artifact URL as the owner's download route.

## NAV26 implementation

Exact hook: signed 2025 method `LmQ8.try(Lxh6;Landroidx/media3/exoplayer/k;)Z`.

- Calls original exactly once and returns its original boolean unchanged.
- Reads only the already-proven attached-stream reference via the existing renderer getter.
- Keeps weak in-memory references to the exact holder / renderer / attached stream; no raw references or metadata are exported.
- Records original boolean outcomes neutrally as TRUE and FALSE. **Do not assume TRUE means the currently selected song or even infer more comparator semantics than the exact source proves.**
- Later correlation is accepted only when holder, renderer and stream references all match the exact type=1/state=2 renderer read cohort.
- Correlation evidence is invalidated on renderer detach and reattach, including reattach with reused Java object references.
- Export is bounded to finite category counters; no track title, account/token, URL, DataSpec, audio bytes or raw object identity is exported.
- NAV26 is read-only diagnostics. It does not connect CELIKOM replacement and does not change original playback.

Relevant source files:
- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/ExitCallsiteWitness.java`
- `android/native-yandex-hooklab/exit-callsite-witness-module/app/src/main/java/pro/celikom/a1exitwitness/NativeRendererStreamEvidence.java`
- `android/native-yandex-hooklab/tests/src/pro/celikom/a1exitwitness/NativeRendererStreamEvidenceTest.java`
- Workflow: `.github/workflows/android-a1-nav26-renderer-comparator-owner-diagnostic-export-once.yml`

New summary categories include:
- `RENDERER_COMPARATOR`, `RENDERER_COMPARATOR_TRUE/FALSE/UNAVAILABLE`
- `ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE/FALSE`
- `ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE_MINUS4/FALSE_MINUS4`

The precise current names are in `NativeRendererStreamEvidence.exportLines()`. Keep TRUE and FALSE separate. The older NAV25 category names are not the NAV26 result names.

## APK verification and personal ChatGPT Library

APK extracted from successful artifact:
- Name: `CELIKOM-A1-NAV26-Renderer-Comparator-ReadOnly-20261118.apk`
- Size: **71,475,180 bytes**
- SHA-256: **`1acd57a45dd025e144c4aaedfb43730b819806b1150eedff69274a3ae94d23a6`**
- Owner signer certificate SHA-256: **`048d76e1c4447fa4f3ac976c45d5a0f8427c087fa665c4fca88ce5caa068f9bf`**, matches accepted NAV25 signer.
- Embedded original Yandex publisher APK SHA-256: **`1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`**, unchanged.
- APK contains embedded module `assets/lspatch/modules/pro.celikom.a1exitwitness.apk`; inspected module DEX strings contain NAV26 build marker and the exact new comparator category names.

Personal Library:
- Canonical APK entry: `/CELIKOM/Android/Native/CELIKOM-A1-NAV26-Renderer-Comparator-ReadOnly-20261118.apk`
- A duplicate-safe second copy also exists with suffix `(1)`. Both were independently materialized from Library and both SHA-256 values match the CI APK exactly.
- Instruction entry: `/CELIKOM/Android/Native/CELIKOM-A1-NAV26-Инструкция.txt` (a duplicate-safe `(1)` copy also exists).
- APK upload and independent Library listing/materialization are verified. The Library bytes are identical to the successful CI artifact.
- Do not tell owner to use the duplicate path; use the canonical unsuffixed APK entry.

## Owner's next action — one install and short ordinary listening

Ask owner to install NAV26 **over NAV25**, without uninstalling and without clearing app data. If Android refuses the update or reports a signer mismatch, stop; do not remove NAV25. Do not touch the separate official Yandex app.

Then open CELIKOM normally, listen to 2–5 ordinary tracks in the usual way, and export the TXT with the in-app diagnostic button. No special pause/seek/Next torture tests are needed. Owner reports original playback has always worked normally; do not invent playback defects or ask to retest functions that have not failed.

When TXT arrives, parse the active NAV26 marker and these categories first:
- `RENDERER_COMPARATOR`
- `RENDERER_COMPARATOR_TRUE`, `RENDERER_COMPARATOR_FALSE`, `RENDERER_COMPARATOR_UNAVAILABLE`
- `ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE/FALSE`
- `ENGINE_COMPARATOR_TYPE1_STATE2_READ_RESULT_TRUE_MINUS4/FALSE_MINUS4`
- `ENGINE_HOLDER_STREAM_ARRAY_MATCH`, `ENGINE_HOLDER_RENDERER_TYPE1`, `ENGINE_HOLDER_TYPE1_STATE2`
- `READ_RETURN_LINK_LOST`
- `CELIKOM_REPLACEMENT`

Remember: type=1/state=2 and even exact comparator/read correlation do **not** by themselves prove current selected Track, album, edition, queue generation, audible PCM, or working CELIKOM replacement.

## Next engineering target after NAV26 phone evidence

Do not restart the static chain or retry the failed NAV25 EOS accessor. Do not change architecture or stock Yandex.

If NAV26 gives same-holder/renderer/stream comparator-to-read evidence, next work is to ground its relationship to the **current selected track and queue generation**, then the same selected Track → Album → edition/generation → active renderer. Only when that exact identity is proven can the existing authorized CELIKOM resolution/entitlement route be considered. No source swap or substitution based on counters alone. Preserve original fallback and all accepted backups.

## Previous baseline / known state

- Owner's NAV25 TXT: `CELIKOM-A1-Diagnostics-1794984522604.txt` (private; never commit raw TXT).
- NAV25: renderer/engine-holder stream link FEW, mismatches/unavailable NONE; type1/state2 and strict original `b.g=-4` cohort MANY; `READ_RETURN_LINK_LOST=NONE`; EOS accessor `NO_HOOK`. Do not repeat EOS probe.
- Stage B: `CELIKOM_REPLACEMENT=NOT_CONNECTED`. Existing TrackWrapper/source counters do not prove same selected item to active renderer. Separate Exo open/read counters are not same-track evidence.
- Existing NAV25 signed APK in Library: SHA-256 `5757472158cf83899ceddf6f27c4281bd5d020085bdefcb581906bc19b76581d`.
- NAV25 source checkpoint: `8b31f68005ca84b40d1ce1104424132d9c38bd12`.
- Pre-NAV26 backup branch: `backup/android-a1-nav25-owner-signed-library-verified-final-20261118`.
- NAV26 JVM-green backup: `backup/android-a1-nav26-comparator-identity-guard-jvm-green-20261118` @ `19c73c433eee23359566c3df2a3a0e5e52756b9c`.
- Do not inspect or instrument credentials or account-token contents; account/Passport telemetry is outside this audio task.

## Mandatory reading

1. `docs/android/NEXT-CHAT.md` — current top block.
2. This document — NAV26 signed APK and exact next steps.
3. `docs/android/ANDROID-A1-NAV25-OWNER-NAV24-REALPHONE-EOS-BOUNDARY-20261118.md` — NAV25 phone evidence and previous gate.
4. `docs/android/ANDROID-A1-NAV24-EXACT-AUDIO-RENDERER-STATE-20261118.md`.
5. `docs/android/ANDROID-A1-NAV23-OWNER-REALPHONE-ENGINE-HOLDER-MATCH-20261118.md`.

Raw owner TXT remains private and must never be committed.
