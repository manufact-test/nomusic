# W136–W138 — CELIKOM Windows 0.24.37 single first-owner-review package

Date: 2026-11-14. Single product, single working branch `main`.

## Exact immutable source and rollback

- Source commit packaged: `1338b73f3709847d5e42f9eb47cc8e8078b70374`.
- Previous verified source before packaging repairs: `b7789299e901cf2218520f724043057744ef05ec`.
- Exact W136 rollback backup: `backup/windows-main-pre-w136-stage-pipeline-current-version-20261114` @ `b7789299e901cf2218520f724043057744ef05ec`.
- Exact W137 rollback backup: `backup/windows-main-pre-w137-one-package-exe-zip-20261114` @ `c2620d34884aad7d69d7e641e7b98e67bfe9716c`.
- Exact W138 version bump rollback backup: `backup/windows-main-pre-w138-first-owner-review-version-20261114` @ `48bd36d47aa1f7f2abfb0b89e95ffb8d5ecbdbdc`.
- App/Inno/Supervisor version aligned to `0.24.37` / `0.24.37.0` and exact existing Inno AppId. No separate TEST product, parallel install location, or new working branch.
- Production trust tuple is intentionally empty; real approved HTTPS feed, P-256 public key and Authenticode signer fingerprint are not available. Auto-update remains fail-closed/dormant.

## First owner acceptance — one private CI package

[Exact private Windows owner-review workflow run](https://github.com/manufact-test/nomusic/actions/runs/43617609655) — **SUCCESS** on source commit `1338b73f3709847d5e42f9eb47cc8e8078b70374`.

The private GitHub Actions artifact `CELIKOM-Windows-internal-stage-1338b73f3709847d5e42f9eb47cc8e8078b70374`, artifact ID `14122464630`, contains exactly:

1. `CELIKOM-W138-WINDOWS-02437-UNSIGNED.exe` — 85,126,190 bytes, SHA-256 `1986c8269c990c91ad0b5910fc76021915ecdbafd1cdf796dce8b474ad03bb38`.
2. `CELIKOM-Windows-0.24.37.zip` — 84,646,352 bytes, SHA-256 `adc372876b49b9d9a3fbded7d7b1a751d69874469de0f71b8492cee39f39d16a`, containing **only** that exact root-level installer.
3. `SHA256SUMS.txt` — 202 bytes, the matching SHA-256 lines.

Both checksums and nested ZIP root-entry identity were independently verified after downloading the private GitHub Actions artifact. This is a **single owner-review build** of the existing product, not a mass release, not a production signed update.

Exact source CI: [Main CI 43617609632](https://github.com/manufact-test/nomusic/actions/runs/43617609632) — **SUCCESS** and [Windows Integration CI 43617609631](https://github.com/manufact-test/nomusic/actions/runs/43617609631) — **SUCCESS**.
Staging job verified: W22/W23 media/route regressions, GUI warnings-as-errors build, native bridge tests, native installer catalog, Supervisor publish, Inno compilation, current-version ZIP acceptance, single-AppId in-place upgrade and per-user install/uninstall without Yandex installation, and one EXE+ZIP checksum package.

## What requires the owner PC now

Run ONE consolidated real-world acceptance pass with this **unsigned private owner review** (no elevated unknown prompts). Record diagnostic TXT only if something fails. Inspect:
- clean install, login/activation, repeated launch, startup/tray, diagnostics after disconnect;
- VPN A→B while an original/«Моя волна» track is playing; verify no audible source reset/pop;
- «Ты» (13 карат) actually playing alternate source and truthfulness of green status;
- Big City Life midpoint volume consistency, real `gain_db` audibility, no clipping on headroom/seek/Next/crossfade;
- natural signed-media 403→206 recovery without hiss;
- Brave/Yandex CPU/RAM/GPU and exact publisher of any unknown elevation prompt (do not authorize blindly);
- Yandex vendor update detection/reconnect where an actual official update can be observed.

CI cannot prove audible behavior. All six owner issues #52, #53, #54, #56, #57, #58 stay **OPEN**, and unresolved user experience is not asserted fixed.

## Production blockers — explicitly not bypassed

- Owner playback approval is not yet available; unsigned owner review cannot be promoted to stable.
- Real production HTTPS feed/signing identities and protected signing/publishing are required to activate unattended updates and real crash→rollback on the owner machine.
- Supervisor/DPAPI rollback simulation passed CI, but **no real production signed automatic update or forced-failure owner-PC rollback has been performed**.

Do not invoke the old Hostinger QA workflow or issue a second installer without a new owner decision. Future code changes continue directly on `main` with exact backups. The one-time W20 staging trigger is pinned to the unique owner request file; ordinary code/docs pushes must not build more interim packages.
