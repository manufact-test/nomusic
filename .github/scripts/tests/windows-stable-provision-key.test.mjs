import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const provision = await readFile(
  new URL("../windows-stable-provision-key.ps1", import.meta.url), "utf8");
const releaseWorkflow = await readFile(
  new URL("../../workflows/windows-stable-signed-release.yml", import.meta.url), "utf8");

const gui = await readFile(
  new URL("../../../windows-companion/w15/Celikom.Companion/Celikom.Companion.csproj", import.meta.url), "utf8");

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
  const version = gui.match(/<Version>(\d+\.\d+\.\d+)<\/Version>/)?.[1];
  assert.ok(version);
  assert.ok(releaseWorkflow.includes("default: '" + version + "'"));
  assert.ok(releaseWorkflow.includes(".github/release/owner-bootstrap-" + version + ".trigger"));
  assert.ok(releaseWorkflow.includes("inputs.version || '" + version + "'"));
  const sequence = releaseWorkflow.match(/RELEASE_SEQUENCE:\s*\$\{\{\s*inputs\.sequence \|\| '([1-9]\d*)'\s*\}\}/)?.[1];
  assert.ok(sequence && Number(sequence) >= 2, "signed release sequence stays monotonic");
  assert.ok(releaseWorkflow.includes("default: '" + sequence + "'"));
  assert.doesNotMatch(releaseWorkflow, /FLOKI_PRODUCTION_PUBLISH_NOT_YET_APPROVED/);
  assert.match(releaseWorkflow, /W189_STABLE_PUBLISHER_NOT_CONFIGURED/);
  assert.match(releaseWorkflow, /CELIKOM_STABLE_PUBLISHER:\\s*\\$\\{\\{\\s*vars\\.CELIKOM_STABLE_PUBLISHER\\s*\\}\\}/);
  assert.match(releaseWorkflow, /publish_floki:[\\s\\S]*?inputs\\.publish_to_production == true[\\s\\S]*?CELIKOM_STABLE_PUBLISHER == 'floki'/);
  assert.match(releaseWorkflow, /publish:[\\s\\S]*?CELIKOM_STABLE_PUBLISHER == 'hostinger'/);
  assert.match(releaseWorkflow, /Pack exact signed six-file Floki transfer/);
  assert.match(releaseWorkflow, /actions\/upload-artifact@v4/);
  assert.match(releaseWorkflow, /Leave blank to use an automatic 7-day UTC expiry/);
  assert.match(releaseWorkflow, /UtcNow\.AddDays\(7\)/);
});

test("W155 private signing key is not exposed to build or publish jobs", () => {
  const publish = releaseWorkflow.slice(releaseWorkflow.indexOf("\n  publish:"));
  assert.doesNotMatch(publish, /CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM/);
  assert.match(releaseWorkflow, /MANIFEST_PRIVATE_PEM:\s*\$\{\{\s*secrets\.CELIKOM_STABLE_MANIFEST_PRIVATE_KEY_PEM\s*\}\}/);
});
