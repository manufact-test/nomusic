#!/usr/bin/env node
/** Offline CLI. Raw HAR stays on the user's computer and is never written to GitHub. */
import {readFile, stat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {summarizeHar} from './har-evidence.mjs';

export function parseArgs(args) {
  if (!args.length || args[0].startsWith('-')) throw Error('Usage: node analysis/summarize-har.mjs LOCAL.har [--mark=SECONDS] [--radius=12]');
  const input = args[0];
  const markers = [];
  let radiusSeconds = 12;
  for (const arg of args.slice(1)) {
    if (arg.startsWith('--mark=')) {
      const n = Number(arg.slice('--mark='.length));
      if (!Number.isFinite(n) || n < 0 || n > 86400 || markers.length >= 20) throw Error('Invalid --mark seconds');
      markers.push(n);
    } else if (arg.startsWith('--radius=')) {
      const n = Number(arg.slice('--radius='.length));
      if (!Number.isFinite(n) || n < 1 || n > 120) throw Error('Invalid --radius seconds');
      radiusSeconds = n;
    } else throw Error('Unknown option');
  }
  return {input, markers, radiusSeconds};
}

export async function run(args) {
  const {input, markers, radiusSeconds} = parseArgs(args);
  const file = resolve(input);
  const info = await stat(file);
  if (!info.isFile() || info.size > 10 * 1024 * 1024) throw Error('Only local HAR files up to 10 MiB are supported');
  const raw = await readFile(file, 'utf8');
  const har = JSON.parse(raw);
  const report = summarizeHar(har, {markers, radiusSeconds});
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  return report;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try { await run(process.argv.slice(2)); }
  catch (e) { process.stderr.write('Local analysis failed: ' + e.message + '\n'); process.exitCode = 1; }
}
