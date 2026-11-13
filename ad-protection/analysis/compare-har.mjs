#!/usr/bin/env node
/**
 * Comparison across local HAR files, without persisting URLs or fingerprint salt.
 * Example: node analysis/compare-har.mjs --ad="./ad.har@120" --normal="./normal.har@120"
 * Mark seconds since EARLIEST network request in EACH HAR (not a tab navigation timestamp).
 * Never commit or upload raw captures.
 */
import {stat,readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {correlateCaptures} from './evidence-correlation.mjs';
import {assessAudioSafety} from './audio-safety.mjs';

export function parseCompareArgs(args) {
  if (!Array.isArray(args) || args.length === 0) throw Error('Usage: --ad=FILE.har@SECONDS --normal=FILE.har@SECONDS [--radius=12]');
  const samples=[];
  let radiusSeconds=12;
  for(const arg of args) {
    if (arg.startsWith('--radius=')) {
      const n=Number(arg.slice(9));
      if (!Number.isInteger(n) || n<1 || n>90) throw Error('Invalid radius');
      radiusSeconds=n;
      continue;
    }
    const role=arg.startsWith('--ad=')?'ad':arg.startsWith('--normal=')?'normal':null;
    if(!role) throw Error('Unknown argument; use --ad= or --normal=');
    const spec=arg.slice(role==='ad'?5:9);
    const sep=spec.lastIndexOf('@');
    if(sep<=0 || sep===spec.length-1) throw Error('Sample needs FILE.har@SECONDS');
    const filename=spec.slice(0,sep), secondsText=spec.slice(sep+1);
    if(!/^(?:\d+)(?:\.\d+)?$/.test(secondsText)) throw Error('Invalid marker seconds');
    const seconds=Number(secondsText);
    if(!Number.isFinite(seconds) || seconds<0 || seconds>86400) throw Error('Invalid marker seconds');
    samples.push({role,filename,second:seconds});
    if(samples.length>12) throw Error('At most 12 samples supported');
  }
  if(!samples.some(s=>s.role==='ad') || !samples.some(s=>s.role==='normal')) throw Error('Need both ad and normal samples');
  return {samples,radiusSeconds};
}

export async function runCompare(args) {
  const {samples,radiusSeconds}=parseCompareArgs(args);
  const captures=[];
  // Never open network addresses. readFile operates only on local file paths.
  for (const s of samples) {
    const filename=resolve(s.filename);
    const size=await stat(filename);
    if(!size.isFile() || size.size>10*1024*1024) throw Error('Local HAR file must be <=10 MiB');
    const har=JSON.parse(await readFile(filename,'utf8'));
    captures.push({role:s.role,markers:[s.second],har});
  }
  const result=correlateCaptures(captures,{radiusSeconds});
  result.safety=assessAudioSafety(result);
  process.stdout.write(JSON.stringify(result,null,2)+'\n');
  return result;
}
if(process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href) {
  try{await runCompare(process.argv.slice(2));}
  catch(err){process.stderr.write('Comparison failed: '+err.message+'\n');process.exitCode=1;}
}
