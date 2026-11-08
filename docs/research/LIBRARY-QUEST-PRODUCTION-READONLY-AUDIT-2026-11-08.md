# CELIKOM — фактическая проверка живой библиотеки Quest Pistols и массовой загрузки, 08.11.2026

## Результат (production, SELECT ONLY)
[Read-only workflow 42515133906 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/42515133906), snapshot 2026-11-08 19:27:37 UTC (22:27:37 Minsk). Branch `feature/library-readonly-quest-audit-20261108`, only audit script/workflow and this note; no changes to production DB, files, services, Android, main or extension. Exact run artifact `celikom-quest-library-readonly-42515133906`; `writes=0`.

### Quest Pistols «Он рядом»
* Exactly one matching Yandex track row in production: ID `89285816`, album `Superklass`, track DB duration `224490ms`, approved-active replacement `39` from 2026-10-25. Its audio asset duration `224575ms`, size `8987210` bytes; private file **exists**, exact registered size **matches**, full SHA256 **matches**. This is proof of preserved file, not proof Android playback.
* Current actual live catalogue explicitly contains `89285816`, title `Он рядом`, artist `Quest Pistols`, duration `224490ms`, replacement_available true.
* HONOR Test.72 log on 2026-11-08: Yandex media alias `1015` and `1063` both show **the same song** «Он рядом», Yandex artist `Quest Pistols, Quest Pistols Show`, duration `224520ms`, album `17497301`; album API returned HTTP 451. The 30ms duration difference is well below 1000ms strict matching threshold. Test.72 own catalogue incorrectly gave NO_MATCH because `HybridIdentity.artists` did not collapse this specific doubled display credit even though `AlbumMatch.artistKey` already did. Two Yandex media aliases are *not* two rows/tracks in CELIKOM library.
* Signed Test.73 fixes exactly this duplicate artist-credit case and misleading 451 UI, code/host tests PASS; **physical HONOR trial pending**. Never assert native pause/seek and cold loading solved.

### Whole library invariants
* `1108` different Yandex track IDs, `1113` replacement rows; as of last check **1108 active approved**, **0 pending**, 2 rejected and 3 disabled. Prior snapshot before moderation showed 908 active, 200 pending; do not confuse timestamps.
* Zero different Yandex track IDs with identical normalized (trimmed/case-folded) full artist+title; zero same ID with two active replacements. Four IDs have multiple historical versions, all with **exactly one** active and others rejected/disabled.
* Three audio assets are linked across different Yandex IDs:
  * 10AGE, Ramil' «Ау» ID 144530503, approved #1, shares audio with **rejected** O.G EzzY «Шёлковая простынь» ID 65774187, #25; rejected file also fails duration check. Old incorrect candidate, no active cross-song replacement.
  * Heronwater «PROJECT X» 106018754 #420 and «PROJECT X (Prod. by Heronwater)» 109332242 #660 use exactly the same file and duration 131709ms, both approved active. Different Yandex IDs and title suffix; separate database track mapping.
  * Jane Air «Junk» 117979417 #578 and Jane Air, Smike, Пойманные Муравьеды «Junk» 28676494 #491 share file/duration 208170ms, both approved active. Different Yandex IDs and performer credits; separate mapping. Same file across Yandex releases does **not** prove corruption.
* Two >1500ms file vs source duration outliers: 123250095 #24 (116800ms vs 268826ms) and 65774187 #25 (183720ms vs 180872ms); both **rejected, inactive**, originally 2026-10-14.
* Latest 900 imported fixed-plan records checked in GitHub manifests (batch100/200/400/600/800) have **zero Quest Pistols** candidates. Their dedup checks use Yandex track ID plus exact normalized artist+title, not artist alone. Repeat performer across different songs is permitted and not an automatic ID collision.
* **Remaining risk:** bulk importer pins source MP3 duration, but source manifests mark `original_duration_verified=false`. Live SQL matching source and stored MP3 durations does NOT prove official Yandex source album metadata agrees (which may be blocked by HTTP 451). Any future unknown-id song may fail strict Android duration/title/artist fallback. For future batches validate original Yandex title/credit and duration when available, and surface uncertain mapping for moderator review; do not silently relax to wrong track.

## Decision
**Go test signed Test.73 over Test.72**. Test Quest «Он рядом» first, then several other songs by repeat performers, and report fresh phone diagnostic. The prior absent-Quest bug is an actual predictable metadata alias mismatch, **not evidence that bulk uploads deleted Quest**. Pause/seek/native buffering problems remain a separate Android two-player question. Nothing should be deleted/reassigned in production based on these findings.
