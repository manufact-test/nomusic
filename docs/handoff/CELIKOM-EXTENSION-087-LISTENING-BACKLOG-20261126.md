# Extension0.4.87 — owner listening backlog,26 November2026

## Owner direction
Owner will listen throughout the day and send diagnostics in pieces. Analyze each and accumulate ONE deduplicated issue list; no runtime edits/new versions until evening unless a genuinely critical problem is found. No critical condition requiring an immediate release is established by the first fragment. This is NOT owner acceptance/public promotion.

Current owner candidate/source:0.4.87,main eae0b0d9be432ce00ec6749848eabbe1926fc3c9. Keep runtime frozen during collection. Android/Windows/backend untouched.

## Fragment1
Input Вставленный текст(20261126-101532).txt,Library libfile_a3735bd78e848191bfcfaec6438875c9;reports0.4.87. Owner: much better starts, but still hears occasional dropouts WITHOUT VPN.

Observed final state: replacement active,readyState4,not seeking/not muted,drift+3ms,bridge ready/healthy,no replacement/startup/connection error,no suspension/recovery. Current buffer0–145.136s while playback~19.813s;stream206,5,832,704bytes received. This final state does not reconstruct every preceding audible symptom.

20 cumulative activations/19 restores; only12 startup and12 restore rows retained. Do NOT call that19 network dropouts or treat the bounded rows as a whole-day count.

### E1 — startup fallback before descriptor confirmation (confirmed, priority1)
9/12 retained successful activations show native position100ms (intro held through preparation). On track131453313,trace explicitly records awaiting-confirmed-asset followed by replacement-prepared without exposing original:87 correction is working for this captured case.

3/12 retained activation rows are later than100ms:50208527 at141ms,27323613 at599ms,48592437 at619ms. The latter has full trace: native admission at1795688093983;intro-start-timeout at4391;original starts at4397;guard reacquired at4929. Original therefore runs about532ms before replacement admission. Unlike the86 trace, no replacement element exists at timeout: descriptor validation has NOT yet completed. The87 confirmed-preparation extension cannot apply there. This is a remaining late-descriptor branch of the same startup family, NOT evidence that the successful confirmed-asset fix was lost.

For this start,prepare939ms,warmLead67ms,resolve-stage460ms,load461ms. Config request284ms finishes1795688094213;resolve241ms finishes4454,AFTER the400ms intro fallback. There are two config fetches in that window (284ms and152ms) from existing clients; investigate their ownership/cache lifecycle before claiming they are duplicate bugs. Earlier slow start27323613 has config363ms andresolve255ms;API succeeds, but their sequential wait consumes startup budget.

Evening investigation: reduce/warm the cold policy/authorized descriptor critical path within the existing authority rules; measure audio readiness separately. Do NOT automatically increase every intro wait again or extend signed/access lifetimes. No fix implemented during collection.

### E2 — decoder settling on a late join (confirmed symptom, same E1 event)
After the E1 fallback on48592437, replacement is set near629ms and is seeking/readyState1 while native~628ms;later native1108ms and replacement1117ms,readyState4. This supports an extra brief settling interruption after late admission. It is NOT a separately proven transport outage or proof of permanent drift. Review target readiness alongside E1; avoid reintroducing broad complete-file joins,live-join or84 unbuffered-yield rules.

### E3 — end-of-track original release (audit item, not proven mid-song dropout)
Retained restore reasons:7 replacement-ended and5 guard-lost:master-binding-changed. Of the latter,one is master-ended andfour are next-track metadata transitions. The full131453313 boundary shows native164.606s == duration164.606s at replacement release,then next track starts. This particular replacement-ended is a natural boundary,NOT a mid-song network loss. Audit whether boundary release briefly exposes original tail, but there is no direct proof of that audible artifact in this file. Do not suppress real next-track/source cancellation or hold an old replacement over the next song.

### Not established
All24 retained API rows succeed. Audio range completion history is incomplete:API200 does NOT prove every audio transfer was fast. No bridge-unhealthy loop or failed auth/network request is recorded in the retained window. This does NOT negate the owner's heard dropouts; future fragments may capture another cause. CPU/GPU measurements are absent.

## Collection rules
Append later fragments here, retaining file identity, actual version, observation window and confirmed vs suspected findings. Deduplicate overlapping rolling histories by at/track/reason rather than adding counters repeatedly. Do not treat normal track changes/natural endings/manual actions as unexplained failures. Critical escalation means persistent silence,wrong old track continuing,crash or unresolved access failure supported by evidence;none is established at the end of fragment1.

No runtime patch,version bump,production publication or release approval was performed for this entry.

## Fragment2 —10:42 diagnostic
Input Вставленный текст(20261126-104253).txt,Library libfile_b292f45d081481918a85c952f6b07a86;version0.4.87. No new VPN condition was specified; retain the established without-VPN listening context, do not infer route changes.

Deduplication by startup at and restore(requestedAt,trackId,reason): first5 of the retained12 startup rows and first5 of12 restore rows overlap fragment1. Exactly7 new activation rows and7 new restores are retained. Cumulative counters20→27 and19→26 are consistent; do NOT add the whole rolling12 again.

| New track | Prepare ms | Resolve stage ms | Audio-load stage ms | Native position at activation ms |
|---|---:|---:|---:|---:|
|27317260|1387|423|945|1061|
|132465315|704|215|450|100|
|1944599|3558|260|3264|2618|
|89285816|754|285|437|100|
|48592132|653|172|428|100|
|48592121|1067|258|788|152|
|50163040|990|447|519|666|

Three new starts are held through activation at100ms;four are late. E1 is confirmed again on50163040: admission at1795689630149,unconfirmed intro timeout0557,original play0563,guard reacquisition1145 (~582ms later). Config282ms andresolve187ms finish the descriptor at0605,after the short fallback. This is the existing late-descriptor category;do not create a duplicate issue.

### E4 — slow audio preparation after a prompt descriptor (new distinct investigation item,priority1)
Track1944599 at1795688822492 takes3558ms overall,with260ms resolve stage and3264ms audio-load stage. This is much slower than the typical437–519ms audio stages in this fragment and is NOT explained by the descriptor alone. Same Track ID also had a slow1768ms audio-load stage in the earlier85 morning diagnostic (Вставленный текст(20261126-070712).txt). Record recurrence,not a proved cause. Possible body transfer/format/decoder startup costs cannot be distinguished from the current aggregate loadMs;that stage can include player preparation and gain setup. There is no per-range/header/body/decoder trace for this old event,so do not label it server downtime,network failure,corrupt MP3 or proven decoder-only delay. Compare the actual asset and preparation path during the evening investigation without modifying runtime during collection. Track27317260 also takes945ms in audio preparation.

### Confirmed-reservation limit (E1 extension,not another unrelated outage)
The retained48592121 trace shows87's confirmed wait activating at400ms but reaching the ORIGINAL1-second reservation deadline at1795689430719 while replacement is still readyState0. Original begins0726;guard reacquires0793 (~67ms later). Thus the fix works within its bound but does not hide audio that becomes ready just AFTER the cap. Record as E1 startup budget/slow audio interaction;do not blindly lengthen the cap again. Full long-load1944599 trace is no longer retained.

### Endings / current state
Seven new restores consist of4 master-ended and3 replacement-ended;all accompany subsequent track advances. Full48592132 release is at native182.625s==duration182.625s;48592121 native pause is at199.297s==duration199.297s before next-track ended event. These two captured boundaries do not establish a mid-song dropout. E3 remains an audit item,not a confirmed interruption count.

At capture:active50163040,fully buffered0–187.506919s,replacement playing/readyState4/not seeking,reported drift-3ms,bridge healthy,no startup/replacement/connection error,no suspension/recovery. Raw player snapshots differ slightly because captured at separate times;do not subtract them instead of using synchronized driftMs. All24 retained API rows succeed;no bridge-unhealthy/failed authorization/transport failure is recorded. No persistent silence,wrong-track continuation or crash justifying an emergency patch is established in this fragment.

Runtime remains frozen at87 per owner direction. No code edits,build,promotion or public release performed. Current prioritized evening list:E1 cold descriptor/startup handover;E4 slow audio preparation;E2 late-join settling linked to these;E3 boundary-tail audit with limited evidence.

## Fragment3 — critical pause/resume divergence; collection freeze lifted
Input Вставленный текст(20261126-115215).txt, Library libfile_8451bf3b5e7c819198ce954d6ce1320b; screenshot libfile_54e72e85e3188191b5af6991baecb68d. Owner explicitly authorized immediate investigation/new version after wrong audible original despite matching Yandex/extension labels. This supersedes the collection-only freeze above.

### E5 — persistent displayed-track/native-audio mismatch (critical symptom, root cause open)
Final87 has no active replacement, native unguarded and playing334.6s resource; metadata48592143 catalog250.21s. Earlier actual48591518 also334.6s; metadata changed during pause at28.489s, then resumed28.489s with334.6s duration and stale48592143 label. Existing duration gate prevents wrong replacement but popup incorrectly claims version available and disables Start. Actual native source URL continuity is not provable from redacted historical hosts alone. VPN or CELIKOM/Yandex root cause not established. Final snapshot is original audio, not an old CELIKOM replacement continuing.

88 adds truthful persistent mismatch state, cancels stale visible track targets/presence, explicit user-requested/revalidated page reload and anonymous resource revision evidence. It does not claim a permanent Yandex divergence fix. See CELIKOM-EXTENSION-088-PLAYER-MISMATCH-20261126.md.416 local tests/manifest/security pass; real listening pending. E1–E4 remain open; no speculative wait/decoder/network changes bundled.
