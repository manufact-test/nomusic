# CELIKOM Android A1 — exact original 2025.10.4 post-login route (14 Nov 2026)

## Status
**NAV9 remains NOT FIXED. Stage A NO-GO; Stage B LOCKED.** No new APK has been prepared. This is an exact, source-independent investigation of the publisher-signed APK embedded inside the already tested NAV9, based on the existing 508-line owner diagnostic; no repeat OTP, ADB, or credential access is required.

Exact source of evidence: `/CELIKOM/CELIKOM-A1-NAV9-PostLogin-Route-Diagnostics-20261114.apk`, embedded `assets/lspatch/origin.apk` (29,803,070 bytes; SHA256 `1d0527a1b63e4d6eab7671258ec42a87e6e36b53e2c1f352c25a5b6f8ffb1b56`). Read-only inspection of unmodified original `classes3.dex`, `classes5.dex`, `classes6.dex`. All decompiled names below are vendor-internal diagnostic identifiers, not stable APIs to modify. No third-party bytes have been committed.

## The actual original post-login contract

1. `MainScreenActivity.onCreate` in classes6.dex reads `getSharedPreferences("Yandex_Music", MODE_PRIVATE).getBoolean("onboarding", true)` as part of startup decisions, but reading `UNSET` **does not prove** why the post-login return fails. Do not set this value manually.
2. On the unauthenticated startup path, `MainScreenActivity.l(Z)` creates an `EntryScreenActivity` intent with Parcelable `Login(openMainScreenAfter=false)` (or `ChangeUser` depending on argument), starts Entry and finishes Main. This is an **original vendor path**, not by itself evidence of clone-specific corruption.
3. `EntryScreenActivity.onCreate` reads `entry_type` and sets up its Entry fragment. The fragment registers a listener for **`EntryScreenCloseLoginKey`**, reading Parcelable **`EntryScreenLoginResultKey`** (`LiT3.onCreate`, classes3.dex).
4. The real LoginFragment coroutine `LeY5$a.emit` maps an actual successful login with `userInfo` (`Llw4`) into **`LWS3$b; Success(userInfo, wasAutoLogin)`**; failure is a different `LWS3$a` type. It notifies the `LYX5.if(LWS3)` interface, implemented by `LZX5.if(LWS3)`.
5. `LZX5.if(LWS3)` publishes the Parcelable result into AndroidX FragmentManager with **`EntryScreenCloseLoginKey`**. `LhT3.try(Bundle,String)` consumes this event; only the *successful*, userInfo-backed path can enter the original host's authorized state machine.
6. `LiT3.g(LgT3$a)` dispatches the confirmed `userInfo` via `LXS3.if(Llw4,Z)`; concrete `LYS3.if(Llw4,Z)` implements the native transition, updates the app's user state and, subject to its normal decisions, launches **MainScreenActivity** or **WizardActivity**, finishing the Entry Activity. These vendor transitions require genuine user information and must not be called just because an AccountManager entry exists.
7. The earlier handoff called `f67` an onboarding-completion callback. Actual DEX callsite inspection finds `Lf67.if(LLTa$a,LV2b)` reached through `LNJb.invokeSuspend` in the **application upgrade/initialization family**, not the demonstrated Passport success return chain. Thus the claim that NAV9 skipped a specific `f67` post-login callback is **not substantiated**.

## Verified original token/session boundary (additional finding)

The immutable publisher DEX has a separate **token/session** boundary between successful Passport UI and a usable Music `userInfo`. `LqY5.if` requests the token through `LEd5.this(uid)` / `LNG.this` / `Ltya.new` / `LAd5.try` / `LKi7.try` / original `com.yandex.passport.api.e.catch`. If no valid token is returned, its original error path is **not a successful Music login**; only the valid-token path proceeds to loading user information and `Success(userInfo)`. The original Passport SDK writes an **encrypted master-token password** and account metadata through `AccountManager.addAccountExplicitly`. When reading accounts back, `com.yandex.passport.internal.core.accounts.p.for` checks `AccountManager.getPassword(account)` and excludes an account if it lacks a master token; it also reads several `getUserData` keys. NAV9 saw the account count only; it did not prove the token or Music user-information object exists. There is no evidence that this token step is actually failing on the owner's device: **this is a justified suspect, not a diagnosed cause**.

A read-only exact-version private source contract guard was added at `android/native-yandex-hooklab/ci/a1_private_postlogin_contract.py`, with **14 original DEX callsite contracts** confirmed locally against embedded NAV9 `origin.apk`. The pinned private-XAPK gate passed in GitHub native workflow run `43568891197` at its "Verify exact original ... DEX contract" step. Static 14/14 is **not** evidence of authenticated runtime or finished Android native CI. Keep credentials/token values out of output.

## Owner APK signing continuity: verified separate deployment blocker

The old NAV8 and NAV9 artifact certificates differ: NAV8 SHA256 `8c71b643f3ae3c3a9f037ffe7808217c69c4c72b03599b68f9e2c7e069f61295`, NAV9 SHA256 `03c2917442666c49d3d60466e0ed43077321ee472e7915d065b4bb4c1b3b6081`. The current native CI `owner_2025_same_name_own_key_arm13_control.sign_same_name` **generates a fresh disposable own-signing JKS in each run**. Therefore a future build will be incompatible with an Android in-place update of NAV9 and could require uninstall/data loss. **Do not offer another owner APK** under this policy. Establish a secure persistent release signing key (without exposing it in source or logs) before any further owner delivery; the unavailable NAV9 ephemeral private key cannot simply be reconstructed from its certificate.

The push-triggered workflow no longer automatically exports diagnostic owner APK artifacts; export requires an explicit manual dispatch. The exact original issuer signature and nested asset remain unchanged, and the existing Passport AccountManager hook is untouched.

## What the owner diagnostic really proves

- `ACCOUNT_ADD CLONE_OWN ADDED`: real Android AccountManager accepted the clone-owned account.
- `ACCOUNT_STATE CLONE_OWN ONE`: clone MAIN can see the stored account. This is **not** proof of a usable Yandex Music `userInfo` session.
- Six `ACTIVITY_RESULT PASSPORT_ACTIVITY OK`: the current witness hooks **`Activity.setResult`** in the Passport activities. This does **not** observe Android delivery to the Entry Activity, `LeY5$a.emit(Success)`, `LZX5.if(Success)`, or the FragmentManager result callback.
- Entry resumes after account creation; there is no observed new Main creation, and `ONBOARDING_PREF` stays `UNSET`. This establishes the failure outcome, **not** which of the return-chain stages failed.
- No observed Java/process crash. The prior owned AccountManager constructor/query bridge works and must not be undone.

## Engineering consequence / safe route

The missing step must be established between (a) Passport result delivery, (b) LoginFragment receiving real `Success(userInfo)`, (c) FragmentManager `EntryScreenCloseLoginKey` publication/consumption, and (d) `LYS3` native navigation. **Do not** mark authorization successful, manufacture `Llw4`, call the success callback by hand, set `onboarding`, or launch the main UI based solely on account count. Any real repair must retain the original vendor callback and valid user session.

Existing NAV9 data cannot distinguish these cases. Target any following source change to one defensible broken step once verified. No repeated user OTP attempts or diagnostic APK series. For any eventual owner APK, enforce original APK/signature parity, standalone and publisher-first ARM13 checks, and **Library /CELIKOM/ upload + verification before sharing**. Idle 25/25 remains only startup evidence.

Snapshot before this documentation work: `278d5c828586fab825963748ef57e2c0ce81e6c2`, safeguarded verbatim at `backup/android-a1-nav9-owner-loop-complete-handoff-20261114`.
