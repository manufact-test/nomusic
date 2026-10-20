# Android isolation checkpoint — 2026-10-21

Desktop working release: **0.4.61**, commit `3a037e5fd5c1d09cd811dbf12dc80c7a12ed5e2e` on `feature/api-range`. The owner confirmed playback works after the startup timeout correction. The earlier 0.4.60 checkpoint remains historical, not the current working release.

Android work branch: `feature/android-isolated`. This branch deliberately removes every inherited GitHub Actions workflow, including production deployment, catalog SSH, desktop packaging and historical repair jobs. Only the isolation guard is reintroduced. The original desktop branch and its workflows remain unchanged.

The pinned guard permits subsequent changes only under `android/**` and `docs/android/**`. It checks the complete diff, including deletions and both sides of renames. The only permitted workflow must exactly match the definition in the pinned bootstrap commit. It executes its own script from that commit, so editing the working-copy guard does not bypass the check. Guard cases include protected source, root configuration, deployment scripts, deletions, renames and altered workflows.

This is a CI check, not an enforced GitHub branch protection rule or a separate secret store. Do not merge this Android workspace branch wholesale into the desktop branch. Production credentials still exist at repository level; no Android workflow references or uses them. This branch does not build an APK or access the production API.

## Current native source and accepted scope

Exact Android 0.3.22 source has been recovered from the installed APK's embedded ZIP and committed at `a40a27cb29c539f7a795a13fbdf565d810d44494` under `android/native-companion/`. Recompilation gave a byte-identical classes2.dex. Hashes are recorded in `android/native-companion/RECOVERED-0.3.22.json`. Private signing material remains outside Git.

The owner explicitly accepted continuing client-only Android fixes without staging setup, new hosting, migration or repeated manual tests. Do not require a staging environment for these client fixes. Do not modify/deploy shared API, session policy, catalogue, database, storage, desktop or website in this work. Builds and automated tests do not contact production. The installed Android app retains the existing API origin and its independent installation/session; separate folders and branches are code isolation, not a claim that an installed client has no shared service dependency.

Current candidate changes and offline build instructions are in `android/native-companion/README.md`. The design stage is still pending. Calls remain deferred. Deliver one candidate APK after automated checks and ask for one combined physical playback check, rather than another installation for every minor issue.
