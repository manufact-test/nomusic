# CELIKOM Windows — current handoff / 15 November 2026

**Read first:** W119 architecture/owner contract, W150 task order, W155 updater handoff, W156 runtime-chain and provisioning record, W154 grouped owner acceptance.

- Repository: `manufact-test/nomusic`; only working branch: `main`.
- Current release-preparation checkpoint before this docs update: `718861a6b9a1ee3e01c190f49d7d7b75a3062465`.
- Exact backup before version alignment: `backup/windows-main-pre-final-owner-release-02438-20261115` @ `e3714f8c169ff95a59c6a973e6cdeed8bd2f9bde`.
- Target one-time bootstrap version: **0.24.38**. GUI, UpdateSupervisor and Inno installer metadata are aligned.
- Main CI run `43728931911`: SUCCESS. Windows integration CI run `43728931891`: SUCCESS.
- W151–W154 are code/test/CI-ready, but owner-PC acceptance is still pending. Use only the single grouped plan in `docs/windows/W154-CONSOLIDATED-REGRESSION-AND-OWNER-ACCEPTANCE-PLAN-20261115.md` after the final package.
- W155 runtime chain audit is complete; no concrete runtime gap was found. Do not repeat broad audits or add speculative improvements.
- W156 final package path is implemented and CI-tested: protected P-256 release workflow embeds only the public pin, builds one EXE, creates one ZIP with that EXE as its sole root entry, and writes SHA256SUMS. Production publication defaults OFF and must stay OFF.
- **Next owner action:** from the updated repository root on the trusted Windows PC, run once:
  ```powershell
  pwsh -NoProfile -ExecutionPolicy Bypass -File .github/scripts/windows-stable-provision-key.ps1
  ```
  Prerequisites: PowerShell 7+, Node 24, authenticated GitHub CLI with admin access, and protected `windows-stable-production` environment with required reviewer + custom deployment policy allowing exactly `main`. The script generates the key locally, stores the private PEM outside the repository with restricted ACL, sets public variables and uploads the PEM only to the protected environment secret. It prints only the public fingerprint.
- Send only the script success line and public fingerprint. **Never send the private PEM.** Keep an encrypted offline backup.
- After provisioning, dispatch `.github/workflows/windows-stable-signed-release.yml` on `main`: version `0.24.38`, sequence `1`, expiry valid UTC ISO timestamp within 30 days, `publish_to_production=false`. Approve the protected environment if prompted. Download the one artifact and use the EXE+ZIP for the single W154 acceptance.
- **Visibility:** `manufact-test/nomusic` is public. GitHub Actions artifacts are downloadable by anyone with repository read access; they are not private. No private signing key is included. If owner-only artifact access is required, stop before dispatch and arrange separate private storage.
- Not done: owner key provisioning, final EXE/ZIP, owner installation/acceptance, DNS/TLS/feed migration. No production feed has been published.
- Never use Authenticode/PFX, disable SmartScreen/Defender/UAC, publish the production feed early, create a TEST product/branch, touch Android/extension, or reopen excluded #53/#54/#56/#57/#58. #52 remains open pending owner-PC acceptance.

## First message for the next chat

Привет! Продолжаем CELIKOM Windows. Работай только в `manufact-test/nomusic`, ветка `main`. Сначала получи live HEAD и CI, затем прочитай W119, W150, W155, W156, W154 и этот NEXT-CHAT.

W155 runtime audit завершён. W156 final package workflow уже подключён и прошёл CI. Целевая версия — 0.24.38; Main CI 43728931911 и Windows integration CI 43728931891 SUCCESS на checkpoint 718861a6. Точный backup: `backup/windows-main-pre-final-owner-release-02438-20261115` @ `e3714f8c169ff95a59c6a973e6cdeed8bd2f9bde`.

Не начинай новые исследования и не меняй архитектуру. Сейчас единственный внешний блокер — владелец должен один раз запустить `.github/scripts/windows-stable-provision-key.ps1` на доверенном Windows PC и прислать только success line + public fingerprint, не PEM. После этого запусти ровно один защищённый release workflow на main с version 0.24.38, sequence 1, expiry в пределах 30 дней и publish_to_production=false; получи один EXE+ZIP+SHA256SUMS artifact. Учитывай, что репозиторий публичный, поэтому Actions artifact доступен любому с read access; не называй его private. Затем передай владельцу единую W154-приёмку.

Никакого Authenticode/PFX, никакого обхода SmartScreen/Defender/UAC, никакой ранней публикации production feed, никаких Android/extension изменений и никаких старых Issues #53/#54/#56/#57/#58. Не собирай промежуточные пакеты.
