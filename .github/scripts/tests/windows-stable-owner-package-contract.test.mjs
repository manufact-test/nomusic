import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const helper = await readFile(
  new URL("../windows-stable-owner-package.ps1", import.meta.url), "utf8");
const releaseWorkflow = await readFile(
  new URL("../../workflows/windows-stable-signed-release.yml", import.meta.url), "utf8");
const publisher = await readFile(
  new URL("../windows-stable-publish-hostinger.sh", import.meta.url), "utf8");
const flokiStageWorkflow = await readFile(
  new URL("../../workflows/windows-stable-floki-private-stage.yml", import.meta.url), "utf8");

test("W156 owner package creates one EXE, one root-entry ZIP and SHA256SUMS", () => {
  assert.match(releaseWorkflow, /windows-stable-owner-package\.ps1/);
  assert.match(releaseWorkflow, /windows-stable-owner-package-contract\.test\.mjs/);
  assert.match(helper, /Compress-Archive -LiteralPath \$installer/);
  assert.match(helper, /W156_OWNER_PACKAGE_ZIP_MUST_HAVE_ONE_ROOT_EXE/);
  assert.match(helper, /W156_OWNER_PACKAGE_ZIP_CONTENT_HASH_MISMATCH/);
  assert.match(helper, /SHA256SUMS\.txt/);
  assert.match(helper, /W156_OWNER_PACKAGE_OUTPUT_ALREADY_EXISTS/);
});

test("W188 recovery candidate is staged privately and cannot publish customer stable", () => {
  assert.match(releaseWorkflow, /Pack exact signed six-file Floki transfer/);
  assert.match(releaseWorkflow, /windows-stable-private-import\.py pack/);
  assert.match(releaseWorkflow, /actions\/upload-artifact@v4/);
  assert.match(releaseWorkflow, /retention-days: 1/);
  assert.match(releaseWorkflow, /publish:\s*\n[\s\S]*if: github\.ref == 'refs\/heads\/main' && inputs\.publish_to_production == true/);
  assert.match(releaseWorkflow, /private_stage:\s*\n[\s\S]*recovery\/windows-w174-02454-known-good-20261126/);
  assert.doesNotMatch(releaseWorkflow, /gh release create/);
  assert.match(flokiStageWorkflow, /runs-on: celikom-ci-smoke-only/);
  assert.match(flokiStageWorkflow, /actions\/download-artifact@v4/);
  assert.match(flokiStageWorkflow, /floki-windows-signed-spool\.py/);
  assert.match(flokiStageWorkflow, /recovery\/windows-w174-02454-known-good-20261126/);
  assert.match(flokiStageWorkflow, /CELIKOM_WINDOWS_IMMUTABLE_SIGNED_DATA_STAGED_NO_GITHUB_RELEASE/);
  assert.doesNotMatch(flokiStageWorkflow, /MANIFEST_PRIVATE_PEM|HOSTINGER_SSH_KEY|secrets\./);
});

test("owner ZIP and checksums are not promoted into the customer production feed", () => {
  assert.match(publisher, /cp "\$release_dir\/\$version\/\$exe"/);
  assert.doesNotMatch(publisher, /CELIKOM-Windows-.*\.zip/);
  assert.doesNotMatch(publisher, /owner-bootstrap/);
});
