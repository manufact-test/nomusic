# W126 — Single bounded entitlement activation for first install/upgrade — 14 November 2026

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Exact pre-W126 code backup: `backup/windows-main-pre-w126-single-start-activation-20261114` @ `2488e38ebfae605c78d9e3f511d6fca0901c5cc2`.
- W126 final code HEAD: `ed41f613640f55c8de4a027a8f6f12ac31a15093`.
- Exact green rollback snapshot: `backup/windows-main-post-w126-ci-green-20261114` @ the W126 code HEAD.
- Main CI [43601959568](https://github.com/manufact-test/nomusic/actions/runs/43601959568) and Windows integration CI [43601959593](https://github.com/manufact-test/nomusic/actions/runs/43601959593) — **SUCCESS**.

## Changes

1. First Start now checks the native integration state before sending activation. If the native module must be installed/upgraded, it goes directly to the existing consented `ConnectYandexAsync` transaction. It no longer POSTs activation once in `StartAction` and a second time after consent in `ConnectYandexAsync`.
2. `ConnectYandexAsync` now uses `StartupActivationRecovery.ActivateAsync`: at most one bounded retry for transient transport/temporary server errors, only while the same Start generation and account remain active. 401/403 and 429 are not retried.
3. After the fresh activation response, the compact access label/account confirmation/timestamp are updated and any older read-only preview is invalidated before the native install/upgrade continues.
4. A failed bounded network retry is handled as an entitlement/network failure, not mislabeled as native integration damage. It does not trigger the native-failure Yandex catalog refresh or a misleading install-failure modal.
5. Integration CI guards the order of the native readiness gate versus activation, the retry helper in the install path, and the post-activation account label update.

## Safety / scope

- The native integration still requires the existing explicit consent and existing signed native installer path. No new architecture, native patching strategy, or product variant was introduced.
- Server activation remains idempotent; this change removes the unnecessary duplicate request rather than changing trial/subscription policy.
- CI validates code paths only. No installer was built and no owner-PC install/audio test was requested.

