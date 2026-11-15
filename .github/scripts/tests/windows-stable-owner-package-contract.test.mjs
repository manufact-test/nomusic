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
