import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const provision = await readFile(
  new URL("../windows-stable-provision-key.ps1", import.meta.url), "utf8");
const releaseWorkflow = await readFile(
  new URL("../../workflows/windows-stable-signed-release.yml", import.meta.url), "utf8");

test("W155 owner key setup uses only built-in Windows PowerShell and GitHub web UI", () => {
  assert.match(provision, /ECDsaCng/);
  assert.match(provision, /BEGIN PRIVATE KEY/);
  assert.match(provision, /manifest-private\.pem/);
  assert.match(provision, /Set-Acl/);
  assert.match(provision, /SYSTEM/);
  assert.match(provision, /settings\/environments\/windows-stable-production/);
  assert.match(provision, /notepad\.exe/i);
  assert.doesNotMatch(provision, /^\s*(?:node|gh)(?:\.exe)?\s+/im);
  assert.doesNotMatch(provision, /\bgh(\.exe)?\b/i);
  assert.doesNotMatch(provision, /gh auth|gh secret|gh variable|Invoke-RestMethod|Invoke-WebRequest/);
  assert.match(provision, /W155_KEYPAIR_ALREADY_EXISTS_DO_NOT_REGENERATE/);
});

test("W155 release derives the public pin from the protected private key", () => {
  assert.match(releaseWorkflow, /environment:\s*windows-stable-production/);
  assert.match(releaseWorkflow, /if:\s*github\.ref == 'refs\/heads\/main'/);
  assert.match(releaseWorkflow, /CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM/);
  assert.match(releaseWorkflow, /windows-stable-key-public\.mjs/);
  assert.doesNotMatch(releaseWorkflow, /vars\.CELIKOM_STABLE_PUBLIC_KEY_DER_BASE64/);
  assert.match(releaseWorkflow, /default: '0\.24\.38'/);
  assert.match(releaseWorkflow, /\.github\/release\/owner-bootstrap-0\.24\.38\.trigger/);
  assert.match(releaseWorkflow, /inputs\.version \|\| '0\.24\.38'/);
  assert.match(releaseWorkflow, /inputs\.sequence \|\| '1'/);
  assert.match(releaseWorkflow, /default: '1'/);
  assert.match(releaseWorkflow, /Leave blank to use an automatic 7-day UTC expiry/);
  assert.match(releaseWorkflow, /UtcNow\.AddDays\(7\)/);
});

test("W155 private signing key is not exposed to build or publish jobs", () => {
  const publish = releaseWorkflow.slice(releaseWorkflow.indexOf("\n  publish:"));
  assert.doesNotMatch(publish, /CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM/);
  assert.match(releaseWorkflow, /MANIFEST_PRIVATE_PEM:\s*\$\{\{\s*secrets\.CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM\s*\}\}/);
});
