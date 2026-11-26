#!/usr/bin/env node
/**
 * Example:
 * node analysis/align-observation.mjs observer.json session.har --offset=-30 --radius=12
 *
 * --offset is HAR-clock seconds minus observer-clock seconds:
 * an event marked at observer +120s that appears at HAR +90s requires --offset=-30.
 * Both files are local. Only sanitized output is printed; no network calls.
 */
import {readFile,stat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {alignObservation} from './align-observation-core.mjs';

export function parseAlignArgs(args){
  if (!Array.isArray(args) || args.length<3 || args.length>4) {
    throw Error('Usage: OBSERVER.json CAPTURE.har --offset=N [--radius=12]');
  }
  const [observerPath,harPath,...options]=args;
  if (!observerPath || !harPath || observerPath.startsWith('-') || harPath.startsWith('-')) {
    throw Error('First two arguments must be local input files');
  }
  let offset=null, radius=12;
  for(const arg of options){
    if(arg.startsWith('--offset=')){
      if(offset!==null)throw Error('Duplicate offset');
      const raw=arg.slice(9);
      if(!/^[+-]?(?:\d+)(?:\.\d+)?$/.test(raw))throw Error('Invalid offset');
      offset=Number(raw);
      if(!Number.isFinite(offset)||Math.abs(offset)>86400)throw Error('Offset out of range');
    }else if(arg.startsWith('--radius=')){
      const raw=arg.slice(9);
      if(!/^\d+$/.test(raw))throw Error('Invalid radius');
      radius=Number(raw);
      if(!Number.isInteger(radius)||radius<1||radius>120)throw Error('Radius out of range');
    }else throw Error('Unknown argument');
  }
  if(offset===null)throw Error('Explicit --offset required');
  return {observerPath,harPath,offsetSeconds:offset,radiusSeconds:radius};
}

async function readLocalJson(input){
  const file=resolve(input);
  const info=await stat(file);
  if(!info.isFile()||info.size>10*1024*1024)throw Error('Only local JSON files <= 10 MiB allowed');
  return JSON.parse(await readFile(file,'utf8'));
}

export async function runAlign(args){
  const options=parseAlignArgs(args);
  const result=alignObservation(
    await readLocalJson(options.observerPath),
    await readLocalJson(options.harPath),
    {offsetSeconds:options.offsetSeconds,radiusSeconds:options.radiusSeconds}
  );
  process.stdout.write(JSON.stringify(result,null,2)+'\n');
  return result;
}

if(process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  try{await runAlign(process.argv.slice(2))}
  catch(err){process.stderr.write('Evidence alignment failed: '+err.message+'\n');process.exitCode=1}
}
