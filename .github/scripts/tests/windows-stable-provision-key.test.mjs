import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const provision = await readFile(
  new URL("../windows-stable-provision-key.ps1", import.meta.url), "utf8");
const releaseWorkflow = await readFile(
  new URL("../../workflows/windows-stable-signed-release.yml", import.meta.url), "utf8");

test("W155 key provisioning requires a protected main-only environment", () => {
  assert.match(provision, /required_reviewers/);
  assert.match(provision, /deployment-branch-policies/);
  assert.match(provision, /W155_ENVIRONMENT_MUST_ALLOW_ONLY_MAIN/);
  assert.match(provision, /CELIKOM_STABLE_DEPLOY_ROOT/);
  assert.match(provision, /Assert-NoReparseAncestors \$repoRoot/);
  assert.match(provision, /Assert-NoReparseAncestors \$keyRoot/);
});

test("W155 existing signing keys are never silently replaced", () => {
  assert.match(provision, /W155_EXISTING_PRIVATE_SECRET_DO_NOT_OVERWRITE/);
  assert.match(provision, /W155_EXISTING_PUBLIC_PIN_MISMATCH_REFUSE_KEY_ROTATION/);
  assert.match(provision, /gh secret set/);
  assert.doesNotMatch(provision, /gh secret set[^\r\n]*--body/);
});

test("W155 public trust variables are resumable and precede private-key upload", () => {
  assert.match(provision, /\[AllowNull\(\)\]\[object\]\$Existing/);
  const publicPin = provision.indexOf('Set-OrConfirmVar $PublicVariableName');
  const privateUpload = provision.lastIndexOf("gh secret set ");
  assert.ok(publicPin >= 0 && privateUpload > publicPin);
  assert.match(provision, /if \(\$secretExists -and \$publicVar -cne \$publicBase64\)/);
});

test("W155 SSH deploy credential is scoped to the single publishing step", () => {
  const publish = releaseWorkflow.slice(releaseWorkflow.indexOf("\n  publish:"));
  const envStart = publish.indexOf("\n    env:");
  const stepsStart = publish.indexOf("\n    steps:");
  assert.ok(envStart >= 0 && stepsStart > envStart);
  const jobEnvironment = publish.slice(envStart, stepsStart);
  assert.doesNotMatch(jobEnvironment, /HOSTINGER_SSH_KEY/);
  const publishStep = publish.slice(publish.indexOf("- name: Publish exact"));
  assert.match(publishStep,
    /env:\s*\n\s+HOSTINGER_SSH_KEY:\s+\$\{\{\s*secrets\.HOSTINGER_SSH_KEY\s*\}\}/);
});
