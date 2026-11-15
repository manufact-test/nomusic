import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const helper = await readFile(
  new URL("../windows-stable-owner-package.ps1", import.meta.url), "utf8");
const releaseWorkflow = await readFile(
  new URL("../../workflows/windows-stable-signed-release.yml", import.meta.url), "utf8");
const publisher = await readFile(
  new URL("../windows-stable-publish-hostinger.sh", import.meta.url), "utf8");

test("W156 protected signed release creates one EXE, one root-entry ZIP and SHA256SUMS", () => {
  assert.match(releaseWorkflow, /windows-stable-owner-package\.ps1/);
  assert.match(releaseWorkflow, /windows-stable-owner-package-contract\.test\.mjs/);
  assert.match(helper, /Compress-Archive -LiteralPath \$installer/);
  assert.match(helper, /W156_OWNER_PACKAGE_ZIP_MUST_HAVE_ONE_ROOT_EXE/);
  assert.match(helper, /W156_OWNER_PACKAGE_ZIP_CONTENT_HASH_MISMATCH/);
  assert.match(helper, /SHA256SUMS\.txt/);
  assert.match(helper, /W156_OWNER_PACKAGE_OUTPUT_ALREADY_EXISTS/);
});

test("W156 ZIP and owner checksums are not promoted into the production feed", () => {
  assert.match(publisher, /cp "\$release_dir\/\$version\/\$exe"/);
  assert.doesNotMatch(publisher, /CELIKOM-Windows-.*\.zip/);
  assert.doesNotMatch(publisher, /owner-bootstrap/);
});

test("W156 owner bootstrap is stored in an unpublished draft release, not a public Actions artifact", () => {
  assert.match(releaseWorkflow, /permissions:\s*\n\s+contents:\s+write/);
  assert.match(releaseWorkflow, /Create unpublished owner-only draft release/);
  assert.match(releaseWorkflow, /gh release create .*--draft/);
  assert.match(releaseWorkflow, /gh release view .*--json isDraft,tagName,assets,url/);
  assert.match(releaseWorkflow, /W156_DRAFT_RELEASE_MUST_REMAIN_UNPUBLISHED/);
  assert.match(releaseWorkflow, /W156_DRAFT_RELEASE_ASSET_SET_MISMATCH/);
  const artifactStart = releaseWorkflow.indexOf("- uses: actions/upload-artifact@v4");
  const publishStart = releaseWorkflow.indexOf("\n\n  publish:");
  assert.ok(artifactStart >= 0 && publishStart > artifactStart);
  const artifactBlock = releaseWorkflow.slice(artifactStart, publishStart);
  assert.match(artifactBlock, /if: inputs\.publish_to_production == true/);
});
