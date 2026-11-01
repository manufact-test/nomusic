import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const manifest = JSON.parse(readFileSync(path.join(root, 'standalone/manifest.json'), 'utf8'));

test('Stage 0 is an inert standalone MV3 extension', () => {
  assert.equal(manifest.manifest_version, 3);
  assert.equal(manifest.version, '0.0.1');
  for (const field of ['content_scripts', 'background', 'host_permissions', 'permissions', 'declarative_net_request', 'web_accessible_resources']) {
    assert.equal(Object.hasOwn(manifest, field), false, field + ' must be absent at Stage 0');
  }
});

test('Stage 0 has its own package and docs', () => {
  const pkg = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'));
  assert.equal(pkg.private, true);
  for (const filename of ['README.md', 'MASTER.md', 'ROADMAP.md', 'NEXT-CHAT.md', 'docs/ARCHITECTURE.md', 'docs/TEST-MATRIX.md', 'docs/RESEARCH-SOURCES.md']) {
    assert.ok(existsSync(path.join(root, filename)), filename);
  }
});

test('Stage 0 does not depend on an installed production extension', () => {
  assert.equal(existsSync(path.join(root, 'node_modules')), false, 'Stage 0 has no dependencies and should not need a node_modules folder');
});
