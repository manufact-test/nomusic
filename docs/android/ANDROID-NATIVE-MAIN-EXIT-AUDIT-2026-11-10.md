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
