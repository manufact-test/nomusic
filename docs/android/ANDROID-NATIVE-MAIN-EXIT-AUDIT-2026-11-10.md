# CELIKOM Android — MAIN EXIT_SELF evidence and sorted-provider A/B (10.11.2026)

## Verified runtime: why the process disappears

Working branch: `experiment/android-native-yandex-fileinfo-hooklab-20261109`.
Functional code: `9c117e994c1562c5f820de843fa15e04d58b8e38`.
Backup with complete A/B code: `backup/android-native-exit-self-ab-evidence-20261110`.
Earlier backups: `backup/android-native-pre-exit-diagnostics-20261110`,
`backup/android-native-pre-sorted-metrica-20261110`.
Never alter accepted Test.50: `backup/android-test50-exact-source-owner-accepted-20261108`.

**MAIN/UI remains NO-GO.** Original signed Yandex 2026.10.3 #170gpr
runs in isolated Android 11 x86/ARMv7 translation. Original and disposable
different-signer package install together (5+5 split APK). In clone, MAIN
starts and dies; `:AppMetrica` remains. Android application exit-info
explicitly records `reason=1 / REASON_EXIT_SELF` **for the clone MAIN**.
Activity manager event stream independently records MAIN `am_proc_start`
and `am_proc_died`, without `am_crash` or `am_kill` events.
No launcher foreground or focused clone window is present. That is evidence
of a process self-exit, **not proof why publisher code initiates it**.

## Evidence matrix

| Variant / job | Evidence | Outcome |
| --- | --- | --- |
| Initial strict CI [42696772783](https://github.com/manufact-test/nomusic/actions/runs/42696772783) | MAIN absent; helper alone persists | FAIL, correct |
| Numeric Android 11 exit parser + main event capture [42704598401](https://github.com/manufact-test/nomusic/actions/runs/42704598401) | MAIN start/died + `exit_reason_exit_self=true`; foreground=false | FAIL, causal category narrowed |
| Original six DEX signed static exit-call audit [42705716074](https://github.com/manufact-test/nomusic/actions/runs/42705716074) | 5 `System.exit`, 2 `Process.killProcess` direct callsites, none directly inside `YMApplication`; 0 undecodable methods | SUCCESS static only; no runtime caller attribution |
| DEX+manifest AppMetrica name-consistency A/B [42706194581](https://github.com/manufact-test/nomusic/actions/runs/42706194581) | One ordered same-length public authority DEX edit + matching manifest; MAIN starts/dies, `exit_reason_exit_self=true`, no focus | FAIL |
| Unchanged-DEX manifest-only parallel control [42706195477](https://github.com/manufact-test/nomusic/actions/runs/42706195477) | MAIN starts/dies, `exit_reason_exit_self=true`, no focus | FAIL |
| Structural five-split control [42706194551](https://github.com/manufact-test/nomusic/actions/runs/42706194551) | Packaging/provider identity structural invariants | SUCCESS, not native UI |
| Standalone read-only hooklab [42706194579](https://github.com/manufact-test/nomusic/actions/runs/42706194579) | Synthetic and module-build jobs | SUCCESS, not hooked real Yandex |

The numeric exit parser handles AOSP `reason=4 (APP CRASH(EXCEPTION))`
syntax and correctly separates `process=<clone>` from `<clone>:AppMetrica`.
It never publishes raw logs, PIDs, paths, secrets or account data.
New strict UI gate requires MAIN PID/process **and** resumed Activity **and**
window focus; `am start -W Status: ok` alone is insufficient.

## Interpretation and what NOT to do

- One inconsistent manifest-only AppMetrica provider name was a plausible
  hypothesis, but a DEX string replacement preserving mandatory
  `string_ids` ordering and matching the manifest did **not** fix exit.
  Do not retry the old unsorted literal; do not repeat this failed A/B.
- Actual caller/condition responsible for the clone's self-exit is unknown.
  It could involve initialization assumptions, package identity or security
  policy, but **a signature or anti-tamper rejection has NOT been proven**.
  Do not assert one from the observed `EXIT_SELF` alone.
- If a legitimate fix would require bypassing publisher authentication,
  signature checks, Play Protect, or modifying the official app on HONOR,
  that route is **NO-GO**. Do not distribute signed/repackaged Yandex APKs.
- No genuine native Yandex UI, Passport login, actual FileInfo runtime hook,
  edition-to-decoder pre-prepare mapping, or sound replacement has been
  demonstrated. Static `trackId` param0 remains true but insufficient.
- Keep one native Yandex player architecture. No second player and no
  synchronized replacement streams. Do not change Test.50, Windows,
  extension, server, database, production or owner phone.

## Next bounded investigation

Do not start another clone patch guess. First determine whether the
self-exit callsite/condition can be identified by permitted, privacy-safe,
**read-only** evidence in an authorized disposable runtime without
disabling publisher protections. If no lawful authorized diagnostic path
exists, stop clone feasibility as NO-GO and assess whether an official
first-party integration could supply the native pre-prepare boundary.
Only a demonstrated functional native MAIN UI allows proceeding to the
read-only real `trackId + edition + generation → source/decoder` trace.
RASKOL `42884423`, «Дым» `39949113`, join click, Next and radio are
**blocked until that gate**; do not ask owner to repeat earlier Audio Smoke.

No owner phone action required and no APK was released.

## UPDATE 10.11.2026 — EXIT_SELF(0), runtime and Windows cross-audit

**Code HEAD before docs:** b2e0f785083ea687631c95d1e2173a563cae9b4d.
**Backup:** backup/android-native-exit0-pid-scoped-static-audit-20261110.
**Verdict: NO-GO native clone MAIN/UI and replacement.** Signed original Yandex still runs; 5+5 installs concurrently only in disposable emulator. Clone MAIN starts/dies repeatedly and records Android 11 ApplicationExitInfo reason=1 (EXIT_SELF) **status=0**. No clone main Activity creation/resumption or focused window; :AppMetrica alone survives. [Manifest-only runtime 42708994496](https://github.com/manufact-test/nomusic/actions/runs/42708994496), [consistent sorted AppMetrica 42708994506](https://github.com/manufact-test/nomusic/actions/runs/42708994506): both FAIL and same symptom. Sorted-provider experiment is now **manual-only workflow** (commit b2e0f785); do not auto-repeat.

**New static evidence:** six genuine signed DEX [42710445292](https://github.com/manufact-test/nomusic/actions/runs/42710445292) PASS. Total direct calls: 5 System.exit and 2 Process.killProcess. Class Lck7 implements Thread.UncaughtExceptionHandler and its uncaughtException calls System.exit three times and throwable logging. YMApplication.onCreate contains two calls installing a default uncaught handler. This is a plausible hidden-exception route, **not proven as executed**.

**MAIN PID scoped runtime:** [42711030929](https://github.com/manufact-test/nomusic/actions/runs/42711030929) and [42711030869](https://github.com/manufact-test/nomusic/actions/runs/42711030869) correctly FAIL main UI. On clone MAIN PID(s), AndroidRuntime-tag logs and generic Exception/Error markers were detected. However **FATAL EXCEPTION=false, bounded Throwable=[], Caused by=[]**, creation-stage categories unavailable: no actual Java fatal or precise caller established. Do not claim Java crash is proven. Only categorical output; raw logs/PIDs/account data/vendor APK not published. Structural safe package CI #42711031353 SUCCESS and read-only hooklab CI #42711031318 SUCCESS do not prove native UI/audio.

**Windows / Analytics (read-only review):** Windows W45 proved and corrected origin music-application://desktop for audio-only CORS (CI 42707502289 SUCCESS). Android native Retrofit is not subject to browser CORS; no direct technical fix to transplant. Reused Windows bounded stage diagnostics and fail-closed reporting only. docs/analytics/event-catalog.md remains draft, ingestion not enabled. Windows branch, Test.50, HONOR, extension, backend, DB, production untouched.

**Next:** establish lawful, read-only concrete runtime self-exit caller/condition on disposable emulator, no signature, Passport or Play Protect bypass. If impossible without publisher security evasion, clone feasibility stays NO-GO; pursue only authorized native integration. No native Yandex live trackId→decoder hook, no real audio replacement, RASKOL 42884423/Дым 39949113 remains untested. Do not repeat already-passed standalone Audio Smoke or issue a user APK.

---

## UPDATE 10.11.2026 — publisher ART profiling denied; exit(0) caller still not attributed

**Latest code HEAD before this docs commit:** `360fec15b719543b909035daee99b30e3257c7ad`.
**Current code backup:** `backup/android-native-profileability-gate-exit-evidence-20261110`.
Earlier backup: `backup/android-native-pre-activity-start-trace-20261110`.

Real isolated Android 11 [ART startup-profiler CI #42775069981](https://github.com/manufact-test/nomusic/actions/runs/42775069981) reported `trace_available=false`, no trace file, no secret/raw trace or third-party APK distributed. Clone MAIN still exits `ApplicationExitInfo REASON_EXIT_SELF=1, status=0`; helper :AppMetrica alone alive, original Yandex still alive; UI gate FAIL.

**The publisher-signed original manifest explains the supported-access limit**: [structural CI #42775600758](https://github.com/manufact-test/nomusic/actions/runs/42775600758) SUCCESS, `profileable_declaration_present=true`, `profileable_shell_granted=false`, `publisher_debuggable=false`, `ordinary_shell_method_tracing_authorized=false`. Android official profileable specification states shell tools require app debug mode or explicit profileable shell permission. Neither is available here. **Do not add `debuggable` or `profileable` to a publisher app, run as root, or bypass Android policy.** New code rejects future `CELIKOM_PROFILE_MAIN_LAUNCH=1` if signed publisher doesn't grant tracing; startup profiler workflow is manual-only archived for authorized future cases.

**Additional signed-Dex static audit:** [CI #42775940114](https://github.com/manufact-test/nomusic/actions/runs/42775940114) SUCCESS, 6 original DEX / all methods decoded. The scanner investigated adjacent immediate-register arguments at 7 known termination callsites (5 `System.exit`, 2 `Process.killProcess`); **all 7 = `NOT_PROVEN`**, so `status=0` does **not** identify the actual caller. Three of the `System.exit` sites remain inside `Lck7.uncaughtException`, but no live invocation proof. Do not misread `NOT_PROVEN` as proof of a dynamic or nonzero argument.

**Current hard verdict: NO-GO for clone MAIN/UI and native audio;** unchanged original and 5+5 installation are not enough. No trackId/edition→actual decoder trace, no RASKOL/«Дым» native regression or replacement sound. A technical route forward requires a legitimate publisher-approved profiling/integration capability or independently verified authorized native source API. Do not reverse a publisher protection to make clone work. Windows, Test.50, official HONOR Yandex, extension, backend/DB/production not modified. No owner manual action.

---

