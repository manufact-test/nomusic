# CELIKOM Android A1 — NAV15: original token envelope and owner account selection (14 Nov 2026)

## Owner report and **real** NAV14 phone diagnostic

Owner supplied `CELIKOM-A1-Diagnostics-1794673530972.txt` (538 event lines). User described Yandex ID external sign-in: chooses one of TWO available Yandex accounts after entering the one-time code, sees the success indicator in Yandex ID; CELIKOM subsequently loads and returns to the four initial onboarding screens. This visual success proves only the Passport side, not successful Music token-to-userInfo progression.

Verified original events:
- Passport subprocess: clone-owned account added (`ACCOUNT_ADD=ADDED`); master-token read PRESENT and decrypt exception absent. MAIN clone `ACCOUNT_STATE=ONE`.
- Original `LOGIN_PIPELINE_SOURCE=PASSPORT_LOGIN_RESULT`, `INITIAL=NONTERMINAL_OR_OTHER`, `AFTER_TOKEN_REQUEST=NO_USERINFO_RESULT`, flow `NO_USERINFO_RESULT`, publish `OTHER_RESULT`, result consumed. No genuine userInfo success, no native post-login route or music playback. No OS crash/forced exit on export.
- NAV14 `LOGIN_TOKEN_OUTCOME=OTHER_NONFAILURE_RESULT` is **NOT** evidence of token success: its reflection observer classified the outer Kotlin result envelope `zW8`, failing to unwrap `zW8.default`. The original bytecode at the token resume clearly does `check-cast zW8` then `iget-object zW8.default`, followed by a test of `zW8$b` failure vs String. Consequently the NAV14 enum was non-diagnostic for the actual payload. **Do not claim successful token, null token, or auth error from NAV14**.
- The `DIAGNOSTIC_BUILD=NAV_V12...` string in old TXT was a stale build constant. NAV15 corrects it; old TXT itself contains NAV14 `LOGIN_TOKEN_OUTCOME` as version evidence.
- MAIN/PASSPORT sections in exported TXT are concatenated, not a single globally ordered stream. Do not reorder events across process sections to make a false causal claim.

## Exact-original signed DEX verification

Read privately from the nested 2025 issuer APK embedded in owner NAV14 artifact; no vendor APK, identifiers, tokens, or decompiled private code added to repo. Original coroutine `nY5.invokeSuspend` stores the resumed object into `nY5.private`; original `qY5.if` checks resume label 1, casts it to `zW8`, takes `zW8.default:Object` and only then checks subtype `zW8$b` (failure) or `String` (token). Signed DEX exact sites (byte offset in original coroutine bytecode) are now contract-gated: 0xA0 envelope type, 0xA4 inner value, 0xE4 failure subtype and 0xF2 String subtype; by original APK hash. This is the immediate root cause of the **misleading observer label**, not yet a proven fix to the original Passport login failure.

## Change set, working branch only

**Only** working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. Exact pre-fix protected backup:
`backup/android-a1-nav14-owner-wrapper-unwrapping-pre-fix-20261114` @ `41890d2cdeb5c3d31cacb8c660191c161d9b8420`.

- `d7e3d515025ee2a9c47f5a284f830e2853766c79` fixes the read-only `LOGIN_TOKEN_OUTCOME` hook to unwrap only `zW8.default` and inspect just type: `WRAPPED_NULL`, `WRAPPED_FAILURE`, `WRAPPED_STRING`, `WRAPPED_OTHER`, `UNEXPECTED_ENVELOPE`; if failure, optional `LOGIN_TOKEN_ERROR_KIND` fixed category. No account ID, password, actual token, error message, URL or stack trace is logged; original coroutine returns normally and its result is not modified.
- `c6916e2db1fbc2aa97602269d6ae540bf9b70afe` updates source tests to pin inner value, bounds and privacy.
- `20284fbc24e69bbb51c8b7302b7dea11bb34a606` adds precise original DEX guard. An early CI failed because the existing parser has no `.field()` method; corrected in `5607a0b4c7b3b580003dcba40cf653e64a5d7acd` by reading bounded DEX field tables (no runtime impact).
- `f0d1ffc05db6b9e41523ea0bd7cdd8afea796c8a` and `939b19ac080430e5357e984f84cc58abb4942627` change the misleading on-device build marker to `NAV_V15_EXACT_TOKEN_ENVELOPE` and update tests.

CI at time of document creation: final paired #43616245271 (head `939b19ac`) pending final verdict; latest clone-only #43616217356 (source `f0d1ffc`, same instrumentation) pending final verdict. Earlier interrupted runs from intermediate commits are NOT an acceptance verdict. Confirm exact final statuses and module/DEX checks from both runs.

## Next work and owner boundaries

- Do not request account passwords or Yandex one-time code in this chat. Do not ask the owner to keep repeating Yandex ID selection or OTP. Existing clone own account may allow observation on an in-place signed update/ordinary launch.
- First finish actual native CI, ensure permanent owner signer and artifact integrity. If and only if green, use established **assistant-driven** GitHub Actions one-shot workflow dispatcher to export signed diagnostic APK to owner Library; do not tell owner to click workflows. Preserve signer and existing clone data where possible. Do not remove original Yandex.
- With new phone TXT, distinguish `WRAPPED_FAILURE` (error category) vs `WRAPPED_NULL` vs `WRAPPED_STRING`, and then implement the actual token-path correction based on the relevant vendor/AccountManager public contract, without spoofing Music success or bypassing Android ownership. If category is `WRAPPED_STRING` despite NO_USERINFO, investigate exact next vendor call, not token failure.
- Native ARM13 co-install and hook-registration are NOT owner successful login. Stage A NO-GO, Stage B LOCKED; native Main and audio not yet proven. Do not call the issue resolved.
