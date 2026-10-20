# Android isolation checkpoint — 2026-10-20

Desktop checkpoint: `checkpoint/desktop-0.4.60-2026-10-20`, commit `a9f3b60ed42d3b4a2b2a07fd9be6834dbc0ecdf5`.
The owner confirmed desktop 0.4.60 playback works. Intermittent initial connection remains unresolved; the owner will provide the saved diagnostic separately.

Android work branch: `feature/android-isolated`. This branch deliberately removes every inherited GitHub Actions workflow, including production deployment, catalog SSH, desktop packaging and historical repair jobs. Only the isolation guard is reintroduced. The original desktop branch and its workflows remain unchanged.

The pinned guard permits subsequent changes only under `android/**` and `docs/android/**`. It checks the complete diff, including deletions and both sides of renames. The only permitted workflow must exactly match the definition in the pinned bootstrap commit. It executes its own script from that commit, so editing the working-copy guard does not bypass the check. Guard cases include protected source, root configuration, deployment scripts, deletions, renames and altered workflows.

This is a CI check, not an enforced GitHub branch protection rule or a separate secret store. Do not merge this Android workspace branch wholesale into the desktop branch. Production credentials still exist at repository level; no Android workflow references or uses them. This branch does not build an APK or access the production API.

## Required source recovery before the next APK

The repository contains companion-probe 0.3.16, not the exact 0.3.22 source used for the installed APK. The latest source and signing working files are in the currently unavailable execution environment. Do not rebuild 0.3.16 and label it a successor of 0.3.22. Recover the exact source, import it under android/, record its hash, then establish a reproducible baseline before functional edits. Private signing material must stay outside Git.

The installed 0.3.22 still uses the production API. Branch separation does not change the installed APK or isolate shared accounts, sessions, catalog, storage or API behavior. Before experiments that change shared behavior, provision and verify a separate API origin, database, storage and test account. Do not deploy mobile experiments to the production server. No staging environment is claimed to exist yet.

Next mobile work after source recovery: inspect the short resynchronization jump after headphone resume, and trace early track termination against the native player's timeline. Keep the deferred call test optional. Batch verification into a single candidate APK after automated checks rather than repeated owner reinstalls.
