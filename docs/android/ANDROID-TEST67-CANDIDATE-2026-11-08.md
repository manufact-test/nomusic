# CELIKOM Android 0.3.85-test.67 — isolated HONOR tuning candidate

## Input
Owner diagnosis `CELIKOM-combined-20261108-172101.txt`. The new Test.66 run starts 2026-11-08T17:19:19+03:00. Older Test.64 and Test.65 segments excluded from current-run fault classification. [Evidence and timing](ANDROID-TEST66-HONOR-172101-ANALYSIS-2026-11-08.md).

## Changes in this separate Android-only branch
1. Approved-only NO_MATCH **in the collapsed Android notification while playing**, exact text `Нет одобренной версии · играет оригинал` (39 chars). It must NOT say `на модерации` without server confirmation; the Activity keeps the full approved-only wording. Paused/missing/ambiguous/stale states and suggestion permission rules untouched.
2. Test.66 «Розовое вино» 3067ms: long successor file (246810ms) was promoted while downloading about 2.3s after prefetch start; after 400ms wait it still required verified sparse cold start (stream ready ~1542ms later). Experimental **bounded** 200ms current handoff wait only when progressive is on, duration >=240000ms, phase downloading and speculative prefetch age 0..2599ms. Older mature downloads retain existing 400ms, short tracks 1200ms, frozen/non-progressive 10000ms. The existing cancellation, fresh resolve authorization, generation and source guards remain intact. No fade/seek/PCM/effect ownership code changes. Numerical real HONOR improvement is **not confirmed**; a younger speculative transfer can occasionally complete in that 200ms being saved.
3. Tests for approved-only notice and short/long/frozen waiting boundaries; existing RASKOL and source buffering tests remain. **RASKOL pause/seek and «Дым» BUFFERING still unconfirmed on Test.66, do not declare repaired**.

## Isolation and release
Dedicated branch `feature/android-0385-test66-compact-notification-honor-20261108`, Test.67 package `pro.celikom.nativeprobe.test`, version code 86153. Stable Android 0.3.92, golden Test.50 sound, main, backend, OTA, desktop and other branches untouched. Full CI/Android D8, signing, verifier, Library upload required before any user APK. Physical HONOR confirmation of sound/status/latency required after delivery. No stable promotion.
