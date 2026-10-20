#!/usr/bin/env node
/** Offline evidence triage. Manual marks are testimony, never proof of an ad or safe filtering. */
import {readFile, stat} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const ROLES = new Set(['ad', 'normal']);
const MARKS = new Set(['ad-heard', 'normal-music', 'video-ad-seen', 'popup-ad-seen']);
const AD_MARKS = new Set(['ad-heard', 'video-ad-seen', 'popup-ad-seen']);
const MAX_CAPTURES = 12;
const MAX_FILE_BYTES = 1024 * 1024;
const validCount = n => Number.isSafeInteger(n) && n >= 0 && n <= 1_000_000_000;
const validSecond = n => Number.isSafeInteger(n) && n >= 0 && n <= 604800;

export function assessSessionSet(captures) {
  if (!Array.isArray(captures) || captures.length < 2 || captures.length > MAX_CAPTURES)
    throw Error('Provide 2–12 separate ad and normal observer captures');
  const sessions = [];
  for (const capture of captures) {
    if (!capture || !ROLES.has(capture.role)) throw Error('Capture role must be ad or normal');
    const report = capture.report;
    if (!report || report.schema !== 'celikom-ad-observer-v1' ||
        !validSecond(report.ageSeconds) || !validCount(report.droppedRoots) ||
        !report.candidates || !report.media ||
        !Array.isArray(report.markers) || report.markers.length > 20 ||
        !Array.isArray(report.recent) || report.recent.length > 80) {
      throw Error('Invalid or oversized observation report');
    }
    for (const name of ['banner','overlay','video','audio'])
      if (!validCount(report.candidates[name])) throw Error('Invalid candidate counter');
    for (const kind of ['audio','video'])
      for (const event of ['play','playing','pause','ended','waiting','stalled','error'])
        if (!validCount(report.media[kind]?.[event])) throw Error('Invalid media counter');
    const totals = {'ad-heard':0,'normal-music':0,'video-ad-seen':0,'popup-ad-seen':0};
    let prev = -1;
    for (const mark of report.markers) {
      if (!mark || !MARKS.has(mark.kind) || !validSecond(mark.s) ||
          mark.s > report.ageSeconds + 2 || mark.s < prev)
        throw Error('Invalid or nonchronological manual marks');
      totals[mark.kind]++;
      prev = mark.s;
    }
    const ads = [...AD_MARKS].reduce((sum, k) => sum + totals[k], 0);
    const normal = totals['normal-music'];
    const issues = [];
    if (report.droppedRoots > 0) issues.push('dropped-dom-roots');
    if (report.markers.length === 20) issues.push('marker-cap-reached');
    if (report.recent.length === 80) issues.push('event-cap-reached');
    if (capture.role === 'normal' && ads > 0) issues.push('ad-mark-in-negative-control');
    if (capture.role === 'normal' && normal === 0) issues.push('missing-normal-music-mark');
    if (capture.role === 'ad' && ads === 0) issues.push('missing-manual-ad-mark');
    const clean = issues.length === 0;
    sessions.push({
      index:sessions.length + 1, role:capture.role, durationSeconds:report.ageSeconds,
      manualMarks:{audioAds:totals['ad-heard'], visualAds:totals['video-ad-seen'] + totals['popup-ad-seen'], normalMusic:normal},
      droppedRoots:report.droppedRoots, clean, issues
    });
  }
  const adSessions = sessions.filter(s=>s.role==='ad');
  const controls = sessions.filter(s=>s.role==='normal');
  if (!adSessions.length || !controls.length) throw Error('Require both ad and normal control sessions');
  const cleanAudio = adSessions.filter(s=>s.clean && s.manualMarks.audioAds > 0).length;
  const cleanVisual = adSessions.filter(s=>s.clean && s.manualMarks.visualAds > 0).length;
  const cleanNormal = controls.filter(s=>s.clean).length;
  const issues = [];
  if (sessions.some(s=>!s.clean)) issues.push('Some captures contain observation gaps, capped histories or mismatched markers');
  if (cleanNormal < 2) issues.push('Fewer than two clean negative-control sessions');
  if (cleanAudio < 2) issues.push('Fewer than two clean manually marked audio-ad sessions');
  return {
    schema:'celikom-session-set-triage-v1', decision:'UNKNOWN', gate:'HOLD', blockingAllowed:false,
    provenance:'MANUAL observer marks only; no Chrome, Yandex account, audio or network verification',
    summary:{total:sessions.length, adSessions:adSessions.length, normalSessions:controls.length,
      cleanAudioAdSessions:cleanAudio, cleanVisualAdSessions:cleanVisual,
      cleanNormalSessions:cleanNormal, incompleteSessions:sessions.filter(s=>!s.clean).length,
      minimumManualAudioComparison:cleanAudio>=2 && cleanNormal>=2},
    issues,
    sessions,
    reminder:'Even a complete manual comparison is NOT proof of ad-only traffic; HTTP Range/206 and uninterrupted music require separate live validation.'
  };
}

export function parseSessionArgs(args) {
  if (!Array.isArray(args) || args.length < 2 || args.length > MAX_CAPTURES)
    throw Error('Usage: --ad=OBSERVER.json --ad=OBSERVER.json --normal=OBSERVER.json --normal=OBSERVER.json');
  return args.map(arg => {
    const role=arg.startsWith('--ad=')?'ad':arg.startsWith('--normal=')?'normal':null;
    if (!role) throw Error('Use --ad= or --normal= for each local observer JSON');
    const filename=arg.slice(role==='ad'?5:9);
    if (!filename || filename.startsWith('-') || filename.includes('://')) throw Error('Expected local file path');
    return {role,filename};
  });
}

export async function runSessionSet(args) {
  const captures=[];
  for (const item of parseSessionArgs(args)) {
    const filename=resolve(item.filename);
    const info=await stat(filename);
    if (!info.isFile() || info.size > MAX_FILE_BYTES) throw Error('Observer JSON must be a local file <=1 MiB');
    captures.push({role:item.role,report:JSON.parse(await readFile(filename,'utf8'))});
  }
  const result=assessSessionSet(captures);
  process.stdout.write(JSON.stringify(result,null,2)+'\n');
  return result;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {await runSessionSet(process.argv.slice(2));}
  catch (err) {process.stderr.write('Observer triage failed: '+err.message+'\n');process.exitCode=1;}
}
