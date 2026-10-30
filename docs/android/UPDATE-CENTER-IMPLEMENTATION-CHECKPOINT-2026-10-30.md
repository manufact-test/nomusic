# CELIKOM Update Center — implementation checkpoint · 2026-10-30

## Verified work
- Initial branch HEAD verified at `90c995e99c0d2073a43c3e1b530e424064ba0230`. Pre-code backup: `backup/android-update-center-before-code-20261030`.
- Added isolated Android update coordinator, in-app visible update section, periodic JobScheduler checker, distinct notification channel and PackageInstaller session; audio classes remain unchanged.
- Extended pinned baseline build and strict manifest verifier for only `REQUEST_INSTALL_PACKAGES`, `UpdateCheckJob`, `UpdateInstallReceiver`.
- Added scoped Android-only website download, manifest and immutable APK routes, plus fail-closed PHP resolver and offline signed-release publisher. **Do not install repository root .htaccess**: existing live root .htaccess is intentionally preserved.
- Full Android CI succeeded at 0.3.56 source (`41052169881`) and 0.3.57 source (`41053261655`); PHP HTTP contract CI succeeded (`41052169874`).
- Read-only Hostinger SSH preflight succeeded (`41053721764`), confirming website directories, live .htaccess and PHP 8.3. This does **not** prove download routes are deployed.
- Signed locally with previously recovered original private certificate, strict `verify_release.py` PASS both times (correct package, version, signing continuity, DEX, manifest, archive). Secret material was **not uploaded to GitHub, CI or website**.
- Signed 0.3.56/code57: APK SHA256 `36c21f11198cd8c5238a05380fadd89a87730ae1ef498a21556b208b989e7525`, size 8722505. Saved in private Library `/CELIKOM/Android/Backups/CELIKOM-Android-0.3.56-UPDATE-CENTER-SIGNED-20261030.apk`.
- Signed 0.3.57/code58: APK SHA256 `1790b807f30f3be1478d5c2bb3b8625a4588b4f4dfc62475703635648befb206`, size 8722505. Saved in private Library `/CELIKOM/Android/Backups/CELIKOM-Android-0.3.57-UPDATE-CENTER-SIGNED-20261030.apk`.
- Snapshot of first signed updater source: `backup/android-update-center-0356-signed-20261030`. Active working branch is now release spec `0.3.57`/58.
- Prepared one-user-action Hostinger deployment ZIP `CELIKOM-Update-Center-HOSTINGER-DEPLOY-20261030.zip` (generated user artifact, not committed to GitHub); SHA256 `f3f717f508236eaa12f64fd64a53a70ef44317a1babe1db917ab6fb5534467d5`. Contains scoped PHP routes, stable pointer initially to signed 0.3.56, staged signed 0.3.57 and atomic version switch script. Local PHP HTTP GET/HEAD returns version 57 with correct size/MIME/SHA. Does not modify existing CMS/index/root .htaccess.

## Remaining blocking live acceptance
**NOT DEPLOYED / NOT VERIFIED LIVE.** Hostinger download endpoint has not been installed; no final live URL may be handed to the user. A GitHub-hosted workflow attempting write deployment could not be created due platform security restrictions, do not bypass. Owner action: in Hostinger File Manager, upload the deployment ZIP to the existing domain root (parent of `public_html` and `celikom-private`) and extract it there with folder hierarchy preserved, without replacing root `.htaccess`, `index.php`, CMS. This is one upload/extract operation.

After upload, verify live HTTPS unauthenticated GET and HEAD for download, manifest and immutable release paths; test payload SHA, MIME, Content-Length, Android browser download and potential Hostinger Basic-auth inheritance. If Hostinger applies a global auth policy before directory exclusions, fix only Android route scope; do not relax protection for unrelated site. Only then communicate the one final permanent working download link. Owner should install 0.3.56 first; after confirming installed code57, promote staged 0.3.57 by running private publish script and test real in-app banner, notification, verified installer and installed code58 with preserved data. Full physical HONOR and audio acceptance still pending.
