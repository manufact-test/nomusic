# CELIKOM private build storage — 24.11.2026

The self-hosted FlokiNET runner bind mount is /srv/celikom/ci-runner/runner on the host, /home/runner in the container. Trusted main portable CI now stages only the verified extension ZIP and private backend ZIP plus SHA-256 sidecars and receipt, under /home/runner/celikom-build-spool/<commit>-<run>-<attempt>. No production secrets, public upload, network transfer, or deployment rights are added. The receipt explicitly identifies unreleased CI builds.

The host-side directory is /srv/celikom/ci-runner/runner/celikom-build-spool. After the first successful run, verify actual persisted files, receipt, hashes, and disk use from the VPS. Do not serve the runner workspace or private backend ZIP via Nginx. The spool is runner-writable, not a trusted release repository. Before release delivery, use a separate approved publication step with fixed filenames, independent checksums/signature verification, bounded size, no symlinks, explicit approval, and dedicated directory/permissions. No host root script may execute code taken from the spool. Do not grant the CI network access to production services.

The Android ARM signing/export and Windows signed installer need separate delivery and build paths. This spool does not eliminate their hosted compute requirement. Do not claim public/direct links yet. Routine artifacts in the general CI still require a separate verified migration; no deletion of existing artifacts or releases in this change.

Monitor disk usage and agree on retention before routine publishing. Only approved immutable release copies may be kept long-term; never automatically delete the only copy of a release.
