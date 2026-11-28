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
const rootConsumer = await readFile(
  new URL("../floki-windows-signed-root-consumer.py", import.meta.url), "utf8");

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

test("W156 owner bootstrap uses a short-lived signed transfer artifact; Floki promotion is protected", () => {
  assert.match(releaseWorkflow, /permissions:\s*\n\s+contents:\s+write/);
  assert.match(releaseWorkflow, /Pack exact signed six-file Floki transfer/);
  assert.match(releaseWorkflow, /windows-stable-private-import\.py pack/);
  assert.match(releaseWorkflow, /actions\/upload-artifact@v4/);
  assert.match(releaseWorkflow, /CELIKOM-Windows-P256-transfer-/);
  assert.match(releaseWorkflow, /retention-days: 1/);
  assert.doesNotMatch(releaseWorkflow, /gh release create/);
  assert.match(flokiStageWorkflow, /actions\/download-artifact@v4/);
  assert.match(flokiStageWorkflow, /floki-windows-signed-spool\.py/);
  assert.match(flokiStageWorkflow, /CELIKOM_WINDOWS_APPROVED_SIGNED_DATA_STAGED_FOR_ROOT_STABLE_PROMOTION/);
});

test("W189 Floki spool is a production publisher and every route is approval-gated", () => {
  assert.match(releaseWorkflow, /publish_to_production:\s*\n\s+description: Promote the signed release/);
  assert.match(releaseWorkflow, /publish_floki:[\s\S]*?inputs\.publish_to_production == true[\s\S]*?inputs\.publish_target \|\| vars\.CELIKOM_STABLE_PUBLISHER \|\| 'floki'[\s\S]*?== 'both'/);
  assert.match(releaseWorkflow, /publish:[\s\S]*?inputs\.publish_target \|\| vars\.CELIKOM_STABLE_PUBLISHER \|\| 'floki'[\s\S]*?== 'both'/);
  assert.match(flokiStageWorkflow, /Record owner-approved version for the existing public customer stable feed/);
  assert.match(releaseWorkflow, /verify_customer_stable:[\s\S]*?W198_PUBLIC_CUSTOMER_STABLE_OTA_VERIFIED/);
  assert.match(releaseWorkflow, /CELIKOM-Windows-P256-stable-/);
  assert.match(flokiStageWorkflow, /environment:\s*windows-stable-production/);
  assert.doesNotMatch(flokiStageWorkflow, /\n  workflow_dispatch:/);
  assert.doesNotMatch(flokiStageWorkflow, /\n  push:/);
  assert.doesNotMatch(releaseWorkflow, /FLOKI_PRODUCTION_PUBLISH_NOT_YET_APPROVED/);
  assert.match(rootConsumer, /await promoteLocalFeed\(arg\)/);
  assert.match(rootConsumer, /publish_signed_root\(version,sequence\)/);
});
