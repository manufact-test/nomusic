# CELIKOM Android A1 — signed-original tCa birth/callsite static follow-up
18 November 2026. Scope: `manufact-test/nomusic`, sole working branch `experiment/android-a1-metrica-init-state-observer-arm13-20261112`. This is a read-only CI audit of the publisher-signed Yandex Music **2025.10.4 #120.1gpr**. No runtime build or APK change.

## Exact verification
- Audit code commit: `7812cf321318e8d77d8af6a86879226cb80af65a`.
- [Signed-original read-only CI run #44335142995 — SUCCESS](https://github.com/manufact-test/nomusic/actions/runs/44335142995).
- The workflow validated the bounded parser and fail-closed fixtures, downloaded the exact pinned signed XAPK into ephemeral runner storage, scanned all six signed DEX files, and deleted the temporary original input.
- Guards: `original_binary_modified=false`, `original_binary_exported=false`, `user_login_or_media_accessed=false`, `runtime_hooks_changed=false`, `decoder_source_changed=false`.
- No raw diagnostic TXT, media IDs, field names, method symbols, values, URLs, tokens or audio data were committed or emitted.

## Findings

### 1. Existing exact Player source-setter path
- The exact original `LcA9.extends(...LtCa...)` path still has **2 direct callers**, both traces complete.
- Both pass the same `tCa` reference through a typed field read (`direct_same_tca_reference_to_lca9_count=2`).
- Neither direct caller constructs that same `tCa` object (`direct_constructor_to_lca9_same_object_count=0`). The exact setter handoff is therefore not the birth site.

### 2. The exact `tCa(String)` creator and Track source
- One creator method was identified. Its String argument originates from a Track-typed field read on a parameter object (`TRACK_FIELD`).
- The parameter's declared type matches the owner type of that Track field and its writer (`creator_parameter_owner_is_track_writer_owner_count=1`).
- The creator is a non-private instance method, but is not a constructor, not `Gp0.new`, not `Fp0.invokeSuspend`, and not named `invoke`.
- Its owner class is neither a coroutine Continuation nor a Kotlin Function class.
- The Track field has one writer method and one write site; the writer's two direct callers carry Track origins categorized as `TRACK_FIELD` and `TRACK_PARAMETER`. No same-object chain from those callers to the exact creator parameter was proven.

### 3. Exact caller / dispatch search — fail closed
- No direct DEX invoke callsite to the exact creator method was found.
- No direct caller of the creator's Track-holder parameter method was found.
- The creator class has two ancestor owners, but no matching ancestor method declaration exists in the app's six DEX files.
- One same-signature ancestor method reference is invoked, but the call is **static** (`receiver_origin_categories=[STATIC]`), not an instance/virtual receiver; it provides no same-object dispatch evidence.
- No method-handle reference, method-handle callsite, `invoke-custom` reference or `const-method-handle` instruction points to the exact creator/ancestor target set.
- The bounded scans completed. The result is not an incomplete scan; it is a completed absence of the sought exact DEX reference edge within this scope.

## Conclusion
The owner-phone NAV36 result `BIRTH_NO_TRACK_SCOPE=MANY` remains a valid observation that the exact Player-scoped original `tCa` was born while the existing synchronous `Gp0.new(...Track...)` scope was absent. The signed static follow-up found a Track-backed field as the source of the `tCa(String)` argument, but **did not prove that this Track is the same Java object as the Track in the synchronous scope**, nor identify a coroutine handoff or another exact same-object edge.

Do not reinterpret this as proof that Track/Album is absent, do not claim an asynchronous cause, and do not infer a playback fault. No narrow same-object evidence currently justifies NAV37 or any new runtime hook. Keep NAV36 unchanged, `IDENTITY_STATUS=STRUCTURAL_ONLY`, `CELIKOM_REPLACEMENT=NOT_CONNECTED`.

## Next action
Stop this static branch of investigation here rather than broadening into unrelated vendor methods, media values, reflective guesses, EOS/comparator work or new runtime instrumentation. Reopen only if a new concrete signed-source reference path or new owner diagnostic gives a specific, testable edge. Preserve NAV36 and all rollback checkpoints.


## Superseding follow-up — NAV37 exact creator Track-field observation (18 Nov 2026)

The original conclusion above was correct for the static caller-edge question: the bounded DEX scan did not prove a direct caller or same-object edge from that creator parameter to the synchronous Gp0 Track scope. It is now superseded as a decision about whether a minimal NAV37 diagnostic is justified. A narrower runtime observation can hook the exact creator method itself, read the Track field from its actual owner argument inside the existing tCa constructor hook, and fail closed by shadowing outer scope when that field is absent. This does not require inventing a static caller edge and does not prove selected edition/current queue generation. See [NAV37 creator Track-field scope](ANDROID-A1-NAV37-CREATOR-TRACK-FIELD-SCOPE-20261118.md). The resulting candidate passed JVM and signed Android13 ARM13 gates; `AUDIO_NATIVE_TCA_CREATOR_HOOK=REGISTERED`. No owner-phone NAV37 diagnostic or music replacement has been verified yet.
