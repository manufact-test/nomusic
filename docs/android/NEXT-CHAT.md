# CELIKOM Android A1 — CURRENT HANDOFF

**Updated:** 15 November 2026  
**Repository:** manufact-test/nomusic  
**Status:** research-only, read-only native identity work. **NOT a product build. Stage A = NO-GO.**

## Active Git state

- **Only active branch:** experiment/android-a1-metrica-init-state-observer-arm13-20261112
- **Latest code + static-audit checkpoint:** 90f8ea394e1ac4168aa63f976e17fd18eb24befb
- **Last runtime Java hook change:** a655712d210189f3bc611847235de3ed4d985c1a
- Current branch HEAD is a documentation-only commit after the code checkpoint above.
- **Code/CI-green backup:** backup/android-a1-track-album-publisher-first-ci-green-20261115 @ 90f8ea394e1ac4168aa63f976e17fd18eb24befb
- **Pre-large-push rollback:** backup/android-a1-track-album-reference-pre-large-push-20261115 @ e0740cf224b34d3260822fa2248a8b136feac1e5
- Final docs/code backup branch: backup/android-a1-track-album-final-handoff-20261115-v2.

## What is actually done

1. Added read-only Album identity capture at the two signed Track constructors that each have exactly one Album parameter. The hook calls the original constructor once, then associates the resulting Track object with that Album argument by Java reference identity.
2. Added a read-only hook on the exact Track copy method. It calls the original method once, then associates its returned Track object with the Album argument.
3. StageBAudioEvidence carries weak Track/Album references and compares with Java ==. The Track map is bounded to 32 entries; source lineage to 16. Conflicting Track→Album associations revoke the Album link.
4. Album identity can be followed through Track Flow → wrapper → descriptor → factory → DataSource instance → successful open() → positive read(). A read is linked only to the same source and lineage after successful open. Failed reopen and close revoke open proof. Read-path inspection is capped at 256 callbacks per source/reopen window.
5. Static signed-DEX audit and regression tests were extended to report Track/Album constructor and copy-method shapes without making an audio/current-track claim.

## Verified CI — exact scope

- [Signed Track/Album static audit #43703523959](https://github.com/manufact-test/nomusic/actions/runs/43703523959): **SUCCESS**. One Album-typed field on Track; two constructors accept Album but direct same-argument write to Track's own field is **not proven**. One Track+Album→Track copy-method candidate; it reads source Track's Album field, passes the Album argument to a Track constructor and returns a Track. The audit does **not** prove the Album argument is stored on the returned Track. Current selected item is not proven.
- [Clone-only ARM13 #43703211359](https://github.com/manufact-test/nomusic/actions/runs/43703211359): **SUCCESS**, 25/25 stable observations; both Album hooks and all Track/Exo hooks registered. Publisher intentionally absent in this control.
- [Publisher-first ARM13 #43703211345](https://github.com/manufact-test/nomusic/actions/runs/43703211345): **SUCCESS**, original publisher 16/16 splits installed, clone co-installed, original remains installed, 25/25 stable observations, no Metrica fatal suppression. Both Album hooks and all Track/Exo hooks registered.
- All three are lab/CI results only. No owner phone was touched. No audio playback or account test was performed. No product APK was published.
- Final publisher-first verdict: METRICA_READONLY_NATIVE_MAIN_75S_PASS_NOT_AUDIO. stage_a=NO_GO; stage_b_current_player_album_edition_attested=false; audio_or_account_tested=false.

## Read these documents first

1. docs/android/NEXT-CHAT-ANDROID-A1-TRACK-EXO-CONTINUITY-20261115.md — focused technical handoff.
2. docs/android/ANDROID-A1-TRACK-ALBUM-IDENTITY-20261115.md — exact static findings and Album identity observer.
3. docs/android/ANDROID-A1-SOURCE-OPEN-READ-CLOSE-IDENTITY-20261115.md — fail-closed Exo source lifecycle.
4. Historical accumulated notes remain in Git history before this documentation cleanup; they are not the current task list.

## Next task — continue, do not restart

The next developer must continue in the existing branch and prove, using signed DEX analysis and read-only identity hooks:

1. Which Track object is the **current selected player item**, distinguishing it from queue, prefetch and download work.
2. Which exact edition/generation object belongs to that selected Track/Album.
3. Whether that same identity reaches the actual decoder input/audio renderer, not merely an Exo DataSource read.

Track Flow and positive DataSource reads are not proof of current audible playback. Do not infer edition semantics from obfuscated names or types. Do not mark Stage A ready until current Track + Album + edition + decoder identity and actual audio are demonstrated.

## Hard constraints

- Do not change the agreed A1 architecture, Test.50, frozen A1/LSPatch baseline, Windows, browser extension, backend, or original Yandex app/account.
- Keep this work read-only and fail-closed. Every vendor method must execute exactly once and unchanged; no fatal suppression.
- Do not create or deliver a product/release APK from this lab work.
- Do not ask the owner to install anything or perform manual multi-step diagnostics unless a specific owner-side measurement becomes genuinely necessary.
- Work in large coherent blocks. Avoid unnecessary status reports and one-click-at-a-time instructions.
- If the owner sends a diagnostics file, inspect the nine Album counters together with Track/Exo open/read/close counters. Distinguish hook registration, no observations, identity conflict and scan exhaustion.
