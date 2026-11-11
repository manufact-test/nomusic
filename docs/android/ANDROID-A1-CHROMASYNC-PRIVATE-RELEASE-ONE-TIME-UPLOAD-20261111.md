# CELIKOM Android A1 — private upload of exact ChromaSync competitor APK

**Safety finding:** `manufact-test/nomusic` is PUBLIC. **Never** upload `ChromaSync-Clone-3.0.1.apk` to this repo: not in files, branches, issues, Actions artifacts or Releases. Other project repositories must not be used as a dumping ground.

## One-time owner GUI steps, no server/hosting required

1. Open https://github.com/new. Choose account `manufact-test`; repository name `celikom-a1-private-lab`; visibility **PRIVATE** (verify the private badge); create with a README. Do not create a public repo.
2. Send the created private repo link in this chat. The lead can add the tiny private workflow file with the linked GitHub connector, **if the connector is granted access to the new repo**. That workflow will use the prepared, pinned public *code-only* reusable workflow. No APK ever added to Git.
3. After the workflow is installed, go to **PRIVATE repo → Releases → Draft a new release**, tag exactly `a1-chromasync-301-private-lab`; drag `ChromaSync-Clone-3.0.1.apk` from PC into release assets (NOT the repo's Code tab). Publish the release. Although the release is published, it remains accessible only to those with access to the **private** repo. The private repository's `release.published` Action triggers the existing workflow; it can also run manually under Actions.
4. CI downloads the **exact original** asset into its ephemeral private runner using the caller repo's limited `GITHUB_TOKEN`, verifies **size=102572843** and **SHA256=4e6edb1c471f6b3715eae4c0a35f0bd898b0daaa87f3f8fb3ba0b20d1638b53d**, boots ARM Android13, installs ChromaSync alone, then reboots a clean guest with genuine publisher-signed 2026 Yandex first and tries ChromaSync alongside it. No phone involved.
5. Results are in the **private** Actions log, with only fixed-category installation/runtime status, not credentials, certificate contents, or APK binaries. The guest and all private payload bytes are deleted at job end. A native 16-second same-PID / resumed Activity probe is only a lifecycle check, **not proof of audio, user login, MyWave, Play Protect or visual pixel/UI correctness**.

## One-file private workflow template (lead adds after repo creation)

Create `.github/workflows/chromasync-private-arm13.yml` on the PRIVATE repo's default branch only:

```yaml
name: CELIKOM A1 private ChromaSync exact ARM13
on:
  workflow_dispatch:
  release:
    types: [published]
permissions:
  contents: read
jobs:
  validate:
    uses: manufact-test/nomusic/.github/workflows/android-a1-chromasync-private-release-reusable.yml@6319dbfed2e6a33317cdfc4db83a9e457f480ca7
    with:
      release_tag: a1-chromasync-301-private-lab
```

This private caller contains **no** APK and **no** personal access token. It uses the standard restricted `GITHUB_TOKEN` to fetch the private release asset; the public reusable workflow code is SHA-pinned, not a mutable branch. That reusable runner rejects any caller repo whose actual GitHub API visibility is not `private`.

Prepared public code-only reusable: `.github/workflows/android-a1-chromasync-private-release-reusable.yml` @ `6319dbfed2e6a33317cdfc4db83a9e457f480ca7`. It checks out the observer and tests from immutable `e7b3cb114d6d52d7e3341f3db26db4ca49bd1b04`, then operates only inside private caller ARM Actions. Main A1, accepted Test.50, stock Yandex on owner HONOR, Windows, extension and server unchanged.

**Run acceptance:** exact private APK SHA pass, separately observed Android PackageManager statuses and exact same MAIN PID for 16s, resumed Activity. The separate stock-first check must record any `INSTALL_FAILED_CONFLICTING_PROVIDER`; never confuse installed APK with living UI. If a genuine competitor native launch works, investigate lawful version-specific configuration differences; copying competitor `sigBypassLevel=2`, proprietary binary or third-party hooks into CELIKOM remains prohibited.

If the linked GitHub connector cannot write to the new repository immediately, install/authorize that PRIVATE repo in the GitHub connection, or paste the provided 13-line YAML template by hand. **Do not** ask the owner to provide a personal access token in chat.
