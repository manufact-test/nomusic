# CELIKOM Android diagnostic 0.1.0-spike

Kotlin/Compose; Android API 26+, target/compile 36; JDK 17 and Gradle 8.13. Diagnostic identity pro.celikom.spike is not the Stage 17 final client.

Generate owned quiet 220/440 Hz WAV fixtures before building, with Android SDK installed:

```sh
python3 generate-fixtures.py
node generate-surface-probe.mjs
gradle :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
gradle :app:connectedDebugAndroidTest
```

Start, pause/resume, seek, Previous/Next, Original and injected failure control only two players owned by this app. UI explicitly labels local fixtures, not service songs. Background/focus loss restores original volume and pauses both; resuming is manual. No microphone, accessibility, notification listener, MediaProjection or third-party stream interception.

Optional login uses existing HTTPS /api/v1/auth/login and GET /api/v1/entitlement. It does not start trial, create promo or change shared API contracts. Password/bearer tokens are never persisted or logged. Installation ID is process-local. Explicit logout revokes its session; process death leaves the server session to expire or be revoked through existing device management. No refresh/recovery/registration in this diagnostic shell; production secure persistence and independent 90-day sessions belong to Stage 17. Platform/version diagnostic headers are not yet persisted by backend; do not claim mobile registration completed.

No real credentials, grants or catalog media are used by tests. Generated WAV/build/local SDK files are ignored. CI publishes only an authenticated-encrypted CMS AES-256-GCM diagnostic artifact, addressed to a temporary recipient certificate. Recipient private key is outside the repository/CI; plain APK is never uploaded. No public download or production signing is configured.

Real-service probe result: CI 38170400164 passed the harness, but Yandex showed a region restriction and no media/Track ID. This is not a playback proof. See docs/spikes/android-playback.md. Do not deliver intermediate diagnostic APKs to the owner.
