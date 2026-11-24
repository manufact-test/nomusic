import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile, lstat } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { stageBuild } from '../floki-private-build-spool.mjs';

async function fixture(t) {
    const root = await mkdtemp(path.join(os.tmpdir(), 'celikom-spool-test-'));
    t.after(() => rm(root, { recursive: true, force: true }));
    const workspace = path.join(root, 'source');
    await mkdir(path.join(workspace, 'extension/dist'), { recursive: true });
    await mkdir(path.join(workspace, 'dist'));
    await writeFile(path.join(workspace, 'package.json'), '{"version":"1.2.3"}');
    await writeFile(path.join(workspace, 'extension/package.json'), '{"version":"4.5.6"}');
    for (const name of ['dist/celikom-server-1.2.3.zip', 'extension/dist/celikom-extension-4.5.6.zip']) {
        const bytes = Buffer.from('504b030400010203', 'hex');
        const sha = createHash('sha256').update(bytes).digest('hex');
        await writeFile(path.join(workspace, name), bytes);
        await writeFile(path.join(workspace, name + '.sha256'), sha + '  ' + path.basename(name) + '\n');
    }
    return { workspace, spool: path.join(root, 'private'), sha: 'a'.repeat(40), runId: '123', attempt: '1' };
}

test('verified packages staged atomically and privately without extra workspace files', async t => {
    const f = await fixture(t);
    await writeFile(path.join(f.workspace, 'dist', 'not-a-release.txt'), 'ignored');
    const receipt = await stageBuild(f);
    assert.equal(receipt.state, 'private-unreleased-ci');
    assert.deepEqual(receipt.files.map(x => x.kind), ['extension', 'server-private']);
    const dir = path.join(f.spool, f.sha + '-123-1');
    assert.equal((await lstat(f.spool)).mode & 0o077, 0);
    assert.equal((await lstat(dir)).mode & 0o077, 0);
    assert.deepEqual((await readdir(dir)).sort(), [
        'celikom-extension-4.5.6.zip', 'celikom-extension-4.5.6.zip.sha256',
        'celikom-server-1.2.3.zip', 'celikom-server-1.2.3.zip.sha256', 'receipt.json',
    ]);
    assert.deepEqual(JSON.parse(await readFile(path.join(dir, 'receipt.json'), 'utf8')), receipt);
    await assert.rejects(stageBuild(f), /BUILD_ALREADY_STAGED/);
});
test('corrupt checksum fails before staging any output', async t => {
    const f = await fixture(t);
    await writeFile(path.join(f.workspace, 'dist/celikom-server-1.2.3.zip.sha256'), 'incorrect');
    await assert.rejects(stageBuild(f), /BUILD_CHECKSUM_MISMATCH/);
    await assert.rejects(lstat(f.spool), { code: 'ENOENT' });
});
test('invalid identifiers, symlinks, and nonprivate spool are rejected', async t => {
    const f = await fixture(t);
    await assert.rejects(stageBuild({ ...f, runId: '../escape' }), /INVALID_BUILD_IDENTITY/);
    await mkdir(f.spool, { mode: 0o755 });
    await assert.rejects(stageBuild(f), /UNSAFE_PRIVATE_SPOOL/);
    const source = path.join(f.workspace, 'dist/celikom-server-1.2.3.zip');
    await renameForTest(source, source + '.real');
    await symlink(source + '.real', source);
    await assert.rejects(stageBuild(f), /INVALID_BUILD_FILE/);
});
async function renameForTest(a, b) {
    const { rename } = await import('node:fs/promises');
    await rename(a, b);
}

test('manual main extension build stages only the verified extension without any backend package', async t => {
    const f = await fixture(t);
    await rm(path.join(f.workspace, 'dist'), { recursive: true });
    const receipt = await stageBuild({ ...f, extensionOnly: true });
    assert.equal(receipt.state, 'private-unreleased-ci');
    assert.deepEqual(receipt.files.map(x => x.kind), ['extension']);
    assert.deepEqual((await readdir(path.join(f.spool, f.sha + '-123-1'))).sort(), [
        'celikom-extension-4.5.6.zip', 'celikom-extension-4.5.6.zip.sha256', 'receipt.json',
    ]);
    await assert.rejects(stageBuild({ ...f, extensionOnly: 'true' }), /INVALID_BUILD_SCOPE/);
});
