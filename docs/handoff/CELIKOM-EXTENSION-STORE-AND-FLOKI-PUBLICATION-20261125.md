# CELIKOM extension — Floki owner delivery and future Chrome Web Store

Updated 2026-11-25. Source: `main`. Do not alter extension audio logic or host permissions for release transport.

## Existing owner-only release

- Approved candidate: **0.4.82**, build run `45666962945`, source `2532f18acacfe246bf7c57bfb299338430b32754`.
- Size **2491981** bytes, SHA-256 `f8c03532c26d6465191779229f414554b86ff01b19fa71cb849f4fdc0992d3ac`.
- Spool: `/srv/celikom/ci-runner/runner/celikom-build-spool`, shared by both Floki CI runners.
- Permanent trusted consumer: `.github/scripts/floki-extension-owner-consumer.py`.
- One-time trusted installation: `.github/scripts/floki-extension-owner-install.sh`.
- **Declarative approval:** `.github/release/extension-owner-promotions.json`. The developer updates it only after a successfully built and checked new candidate, using the exact source commit, run, attempt, file size and SHA-256. The trusted host reads the approved main ref from the private mirror. Ordinary CI cannot write the release directory. Adding a candidate to this manifest is owner-channel approval only; it is not a customer-store release.
- Publisher runs through `celikom-extension-owner.timer`; it validates the ZIP and signed-off digest/identity, requires `https://api.celikom.com`, checks each HTTPS 401 anonymous / 200 authorized download and full SHA-256, then records trusted `current-owner.json`. Immutable older ZIP files remain available.
- Planned owner URLs once **verified active on host**: `https://celikom.com/downloads/extension/celikom-extension-0.4.82.zip` and `https://celikom.com/downloads/extension/celikom-extension-latest.zip`. Both inherit the site's existing private Basic authentication. DO NOT report as functioning until real host promotion and full HTTPS check succeed.
- Downloading a ZIP and loading an unpacked extension does **not** provide automatic browser updates. These private ZIPs are for owner testing only, not the customer download/install channel.

## Future public customer distribution — Chrome Web Store

**Decision:** customer installation and automatic extension updates are owned by **Chrome Web Store**. The CELIKOM website will link directly to the existing published item. It must not pretend that a direct ZIP/CRX download produces auto-updates. Preserve the Chrome Web Store extension ID across releases.

**First-time setup (only after owner has a store developer account and is ready to publish):**
1. Register/activate the Chrome Web Store developer account with two-step verification. The initial listing and first ZIP must be created through the Developer Dashboard, including store listing/privacy declarations. API cannot create a new item. This stage cannot be completed without the owner's Google publisher account and required approval.
2. Obtain the real `publisherId`, 32-character extension ID, real store URL, and authorize Chrome Web Store API **v2**. Keep OAuth/client credentials **only in a restricted trusted secret location**, never in Git, logs, CI workspaces or public web roots.
3. Configure the CELIKOM website installation link to the **verified real store listing**, not an invented URL. When the Store says the item is pending/rejected, the public website must continue linking to the last approved and available version.
4. Future stable release: developer approves a concrete tested release, the trusted publisher uploads its exact immutable ZIP using v2 `POST https://chromewebstore.googleapis.com/upload/v2/publishers/{publisherId}/items/{extensionId}:upload`, checks status, calls `.../v2/publishers/{publisherId}/items/{extensionId}:publish`, then polls `:fetchStatus`. A successful upload/submission is **not** publication. Review/approval may be delayed. Never put store credentials on the CI runners.
5. After status proves live and the installed extension receives the new version, update CELIKOM's public version indication. Do not claim Chrome Store publication from just a CI build or Floki owner latest. Store auto-update delivery is controlled by the browser/Google, not by our private ZIP route.

Chrome Web Store API v1 is deprecated; use v2. Official reference (2026-11-11):
https://developer.chrome.com/docs/webstore/using-api/

**Not yet configured:** publisher and item IDs, developer consent/first listing, restricted Store API credentials, live Store upload and on-device update confirmation. No fictional store URL, no premature customer distribution.

## Next extension developer handoff

1. Continue modifying the extension in `main`, build via existing Floki runner. Tests/checksum must pass.
2. Append the new exact candidate to `extension-owner-promotions.json` and ensure main mirror receives it; the trusted timer independently deploys approved owner ZIP when source spool is present. Inspect trusted receipt and verify site GET before giving owner the real `celikom.com` link.
3. Wait for owner's acceptance of browser behavior before sending this version to the future store stable channel.
4. Never introduce manifest `update_url` as a fake self-update method for Chrome Web Store items. Never distribute GitHub draft ZIP links to owner/customers.

Windows and Android have distinct signed publication and acceptance; do not alter them as part of extension release work.
