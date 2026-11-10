# A1 experiment: own signature permissions instead of omitted Yandex declarations (11.11.2026)

Static proof from OWNER-provided ChromaSync 3.0.1 APK: its nested origin and outer manifests contain a **separate clone permission** `com.yandex.permission.READ_CREDENTIALS.clonelab` declared with `signature` protection and matching `uses-permission`, not the publisher's exact permission. Competitor's host is older `2025.10.4 #120.1rur`, has LSPatch loader and `sigBypassLevel=2`; do not infer it will launch/login without bypass.

Our existing parallel-clone manifest-only control instead **omits two declarations**, leaving the original READ_CREDENTIALS request in place, so the clone could lack its own signature permission even when no original app is installed. This is a plausible A/B hypothesis, **not a proven cause** of EXIT_SELF(0).

This experimental branch changes ONLY the separately named, independently signed, short-lived clone manifest (no DEX mutations) to DECLARE and REQUEST its **own pro.celikom.yandex.nativeclonelab.permission.READ_CREDENTIALS** and **.RELAY_PERMISSION** under Android signature protection, plus any same-name component permission references. No permissions are granted for `ru.yandex.music`, no bypass of issuer's original signature level, no access to other apps' private credentials. If Android's permission service denies self-owned permission, the test must report it and stop. Test merged 1 APK alone then with publisher original five splits in ephemeral translated Android 11. Compare to previous no-declaration A/B 42913442978. Audio, Yandex login, Play Protect and HONOR are NOT tested.

The signed native Yandex application could still rely on literal original permission names from its compiled DEX; do not patch such checks or impersonate issuer. If MAIN still self exits, the result is NO-GO and we MUST NOT claim safe deploy.

After owner-confirmed stable LSPatch audio and exact freeze, proactively remind Stage B own independent injection adapter.
