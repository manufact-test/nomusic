import { createHash } from 'node:crypto';
import { lstat, mkdir, mkdtemp, readFile, rename, rm, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const MAX_PACKAGE_BYTES = 64 * 1024 * 1024;
const versionPattern = /^\d{1,5}\.\d{1,5}\.\d{1,5}$/;
const shaPattern = /^[a-f0-9]{40}$/;
const numberPattern = /^[1-9][0-9]{0,19}$/;
const digest = bytes => createHash('sha256').update(bytes).digest('hex');

async function regularBytes(file, max) {
    const info = await lstat(file);
    if (!info.isFile() || info.size < 1 || info.size > max) throw Error('INVALID_BUILD_FILE');
    const bytes = await readFile(file);
    if (bytes.length !== info.size || bytes.length > max) throw Error('INVALID_BUILD_SIZE');
    return bytes;
}

// This is a private, non-privileged runner spool. It is NOT a deployment
// directory, an HTTP document root or an authority for release approval.
export async function stageBuild({ workspace, spool, sha, runId, attempt }) {
    if (!shaPattern.test(sha) || !numberPattern.test(runId) || !numberPattern.test(attempt)) {
        throw Error('INVALID_BUILD_IDENTITY');
    }
    const packages = [];
    for (const [kind, packagePath, buildDir, prefix] of [
        ['extension', 'extension/package.json', 'extension/dist', 'celikom-extension'],
        ['server-private', 'package.json', 'dist', 'celikom-server'],
    ]) {
        const version = JSON.parse(await readFile(path.join(workspace, packagePath), 'utf8')).version;
        if (typeof version !== 'string' || !versionPattern.test(version)) throw Error('INVALID_BUILD_VERSION');
        const name = prefix + '-' + version + '.zip';
        const source = path.join(workspace, buildDir, name);
        const bytes = await regularBytes(source, MAX_PACKAGE_BYTES);
        if (bytes.length < 4 || bytes.subarray(0, 4).toString('hex') !== '504b0304') {
            throw Error('INVALID_ZIP_HEADER');
        }
        const sha256 = digest(bytes);
        const checksum = await regularBytes(source + '.sha256', 256);
        if (checksum.toString('utf8') !== sha256 + '  ' + name + '\n') throw Error('BUILD_CHECKSUM_MISMATCH');
        packages.push({ kind, name, bytes, sha256 });
    }
    await mkdir(spool, { mode: 0o700 }).catch(error => {
        if (error.code !== 'EEXIST') throw error;
    });
    const root = await lstat(spool);
    if (!root.isDirectory() || (root.mode & 0o077) !== 0) throw Error('UNSAFE_PRIVATE_SPOOL');
    const id = sha + '-' + runId + '-' + attempt;
    const destination = path.join(spool, id);
    try {
        await lstat(destination);
        throw Error('BUILD_ALREADY_STAGED');
    } catch (error) {
        if (error.code !== 'ENOENT') throw error;
    }
    const tmp = await mkdtemp(path.join(spool, '.incoming-'));
    try {
        const files = [];
        for (const p of packages) {
            await writeFile(path.join(tmp, p.name), p.bytes, { flag: 'wx', mode: 0o600 });
            await writeFile(path.join(tmp, p.name + '.sha256'), p.sha256 + '  ' + p.name + '\n', { flag: 'wx', mode: 0o600 });
            files.push({ kind: p.kind, name: p.name, bytes: p.bytes.length, sha256: p.sha256 });
        }
        const receipt = { schema: 1, state: 'private-unreleased-ci', sha, runId, attempt, files };
        await writeFile(path.join(tmp, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
        await rename(tmp, destination);
        return receipt;
    } catch (error) {
        await rm(tmp, { recursive: true, force: true });
        throw error;
    }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
    const [workspace, spool, sha, runId, attempt] = process.argv.slice(2);
    if (!workspace || !spool || !sha || !runId || !attempt) throw Error('MISSING_BUILD_ARGUMENTS');
    const receipt = await stageBuild({ workspace, spool, sha, runId, attempt });
    console.log(JSON.stringify(receipt, null, 2));
    console.log('CELIKOM_FLOKI_PRIVATE_BUILD_SPOOL_OK');
}
