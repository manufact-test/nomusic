import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

export function workflow(baseline) {
  if (!/^[a-f0-9]{40}$/.test(baseline)) throw new Error('Invalid baseline');
  return [
    'name: Android isolation guard',
    'on:',
    '  push:',
    '    branches: [feature/android-isolated]',
    '  pull_request:',
    '    branches: [feature/android-isolated]',
    '  workflow_dispatch:',
    'permissions:',
    '  contents: read',
    'jobs:',
    '  isolation:',
    '    runs-on: ubuntu-latest',
    '    timeout-minutes: 5',
    '    env:',
    '      BASELINE: '+baseline,
    '    steps:',
    '      - uses: actions/checkout@v4',
    '        with:',
    '          fetch-depth: 0',
    '      - uses: actions/setup-node@v4',
    '        with:',
    '          node-version: 24',
    '      - name: Run pinned guard and its negative cases',
    '        shell: bash',
    '        run: |',
    '          set -euo pipefail',
    '          git show "$BASELINE:.github/scripts/android-isolation.mjs" > "$RUNNER_TEMP/android-isolation.mjs"',
    '          node "$RUNNER_TEMP/android-isolation.mjs" --self-test',
    '          node "$RUNNER_TEMP/android-isolation.mjs" "$BASELINE" HEAD',
    ''
  ].join('\n');
}

export function allowedPath(path) {
  if (path.includes('\\') || path.split('/').some(p => p === '..' || p === '.' || p === '')) return false;
  return path.startsWith('android/') || path.startsWith('docs/android/') ||
    path === '.github/workflows/android-isolated.yml';
}
function checkPaths(paths) {
  const denied = paths.filter(path => !allowedPath(path));
  if (denied.length) throw new Error('Protected paths changed: '+denied.join(', '));
}
function checkWorkflow(paths, content, baseline) {
  assert.deepEqual(paths, ['.github/workflows/android-isolated.yml'], 'Inherited workflows are forbidden');
  assert.equal(content, workflow(baseline), 'Isolation workflow must remain identical to its pinned definition');
}
function tests() {
  checkPaths(['android/app/src/Main.java', 'docs/android/plan.md']);
  for (const path of [
    'extension/src/player.js','server/src/AuthService.php','website/index.php',
    'package.json','package-lock.json','.github/scripts/hostinger-deploy.sh',
    '.github/scripts/android-isolation.mjs','.github/workflows/hostinger-deploy.yml',
    'android/../server/x','android//x','android\\x','docs/decisions/x.md'
  ]) assert.throws(() => checkPaths([path]), undefined, path);
  // --no-renames makes a moved protected file appear as a deletion and an addition.
  assert.throws(() => checkPaths(['extension/src/player.js','android/moved.js']));
  assert.throws(() => checkPaths(['server/deleted.php']));
  const sha = 'a'.repeat(40), path = '.github/workflows/android-isolated.yml';
  checkWorkflow([path], workflow(sha), sha);
  assert.throws(() => checkWorkflow([path], workflow(sha)+'# changed\n', sha));
  assert.throws(() => checkWorkflow([path, '.github/workflows/hostinger-deploy.yml'], workflow(sha), sha));
  assert.throws(() => workflow('HEAD'));
  console.log('Isolation guard: positive, protected-file, deletion, rename and workflow-tampering cases passed');
}
if (process.argv[2] === '--self-test') {
  tests();
} else {
  const [baseline, head] = process.argv.slice(2);
  if (!/^[a-f0-9]{40}$/.test(baseline || '') || head !== 'HEAD') throw new Error('Expected pinned baseline SHA and HEAD');
  const git = (...args) => execFileSync('git', args, {encoding: 'utf8'});
  git('merge-base', '--is-ancestor', baseline, head);
  const paths = git('diff', '--no-renames', '--name-only', '-z', baseline, head).split('\0').filter(Boolean);
  checkPaths(paths);
  const workflows = git('ls-tree', '-r', '--name-only', head, '.github/workflows').trim().split('\n').filter(Boolean);
  checkWorkflow(workflows, readFileSync('.github/workflows/android-isolated.yml', 'utf8'), baseline);
  console.log('Protected desktop/server/root files unchanged; Android branch has only the isolated workflow');
}
