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
