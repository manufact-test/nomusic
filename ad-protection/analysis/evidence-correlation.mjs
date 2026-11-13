/**
 * Local-only differential HAR analysis, no live request interception.
 * NEVER exports raw URLs, paths, queries, header values, credentials or hash keys.
 * Fingerprints are ephemeral per invocation; they are not blocking rules.
 */
import {createHmac, randomBytes} from 'node:crypto';
import {bucketSource, mimeBucket} from './har-evidence.mjs';

const MAX_CAPTURES = 12;
const MAX_ENTRIES = 50000;
const MAX_MARKERS = 20;
const MAX_GROUPS = 80;
const MAX_RADIUS = 90;
const METHODS = new Set(['GET','POST','HEAD','OPTIONS']);
const VALID_ROLES = new Set(['ad','normal']);

function safeMime(entry) {
  const r = entry?.response;
  if (typeof r?.content?.mimeType === 'string') return mimeBucket(r.content.mimeType);
  if (!Array.isArray(r?.headers)) return 'unknown';
  const header = r.headers.find(h => h && typeof h.name === 'string' && h.name.toLowerCase() === 'content-type');
  return mimeBucket(header?.value);
}

function groupLabel(url, method, key) {
  if (typeof url !== 'string' || url.length > 16384) return null;
  let parsed;
  try { parsed = new URL(url); } catch { return null; }
  if (!['http:','https:'].includes(parsed.protocol)) return null;
  const clean = parsed.protocol + '//' + parsed.hostname.toLowerCase() + parsed.pathname + '|' + method;
  return createHmac('sha256',key).update(clean).digest('hex').slice(0,16);
}

function relativeEntries(har, key) {
  const rows = har?.log?.entries;
  if (!Array.isArray(rows)) throw Error('Expected HAR log.entries');
  if (rows.length > MAX_ENTRIES) throw Error('HAR exceeds safe entry limit');
  let origin = Infinity;
  for (const row of rows) {
    const n = Date.parse(row?.startedDateTime);
    if (Number.isFinite(n) && n < origin) origin = n;
  }
  if (!Number.isFinite(origin)) return [];
  const events = [];
  for (const row of rows) {
    const stamp = Date.parse(row?.startedDateTime);
    if (!Number.isFinite(stamp) || typeof row?.request?.url !== 'string' || !row?.response) continue;
    const method = METHODS.has(row.request.method) ? row.request.method : 'OTHER';
    const fingerprint = groupLabel(row.request.url, method, key);
    if (!fingerprint) continue;
    const mime = safeMime(row);
    const status = row.response.status;
    events.push({
      second: Math.max(0,Math.floor((stamp-origin)/1000)),
      fingerprint,
      source: bucketSource(row.request.url),
      mime,
      method,
      mediaLike: mime === 'audio' || mime === 'video' || mime === 'hls-manifest' || mime === 'dash-manifest' ||
        row._resourceType === 'media',
      isPartial: status === 206,
      isRange: Array.isArray(row.request.headers) && row.request.headers.some(h => typeof h?.name === 'string' && h.name.toLowerCase() === 'range')
    });
  }
  return events;
}

export function correlateCaptures(captures, options = {}) {
  if (!Array.isArray(captures) || captures.length < 2 || captures.length > MAX_CAPTURES) throw Error('Expect 2–12 captures');
  const radius = options.radiusSeconds ?? 12;
  if (!Number.isInteger(radius) || radius < 1 || radius > MAX_RADIUS) throw Error('Invalid radius seconds');
  const key = options.key || randomBytes(32);
  if (!key || typeof key.length !== 'number' || key.length < 16) throw Error('Invalid local key');
  const groups = new Map();
  let adCaptures = 0, normalCaptures = 0, totalMarkers = 0, normalizedEntries = 0, selectedEvents = 0;

  for (let captureIndex=0;captureIndex<captures.length;captureIndex++) {
    const cap = captures[captureIndex];
    if (!cap || !VALID_ROLES.has(cap.role)) throw Error('Role must be ad or normal');
    if (!Array.isArray(cap.markers) || cap.markers.length < 1 || cap.markers.length > MAX_MARKERS ||
      cap.markers.some(v => typeof v !== 'number' || !Number.isFinite(v) || v < 0 || v > 86400)) {
      throw Error('Expected 1–20 finite marker seconds relative to HAR start');
    }
    if (cap.role === 'ad') adCaptures++;
    else normalCaptures++;
    totalMarkers += cap.markers.length;

    const events = relativeEntries(cap.har, key);
    normalizedEntries += events.length;
    const seen = new Set();
    for (const event of events) {
      // Each request counted at most once per capture, even in overlapping marker windows.
      if (!cap.markers.some(second => Math.abs(event.second-second) <= radius)) continue;
      selectedEvents++;
      let g = groups.get(event.fingerprint);
      if (!g) {
        g = {fingerprint:event.fingerprint, source:event.source, method:event.method,
          adRequests:0, normalRequests:0, adCaptures:0, normalCaptures:0,
          mediaLikeRequests:0, partial206Requests:0, rangeRequests:0, mime: Object.create(null)};
        groups.set(event.fingerprint,g);
      }
      if(cap.role === 'ad') g.adRequests++; else g.normalRequests++;
      g.mime[event.mime] = (g.mime[event.mime] ?? 0)+1;
      if(event.mediaLike) g.mediaLikeRequests++;
      if(event.isPartial) g.partial206Requests++;
      if(event.isRange) g.rangeRequests++;
      const visit = cap.role+'|'+captureIndex+'|'+event.fingerprint;
      if (!seen.has(visit)) {
        seen.add(visit);
        if(cap.role === 'ad') g.adCaptures++; else g.normalCaptures++;
      }
    }
  }
  if (!adCaptures || !normalCaptures) throw Error('At least one ad and one normal control capture required');
  const ordered = [...groups.values()].map(g => ({
    ...g,
    evidenceHint: g.adCaptures >= 2 && g.adRequests >= 2 && g.normalRequests === 0
      ? 'differential-candidate-only' : 'insufficient-separation',
    // Fingerprints are never evidence of an actual advertisement.
    forbiddenForBlocking: true
  })).sort((a,b)=>b.adCaptures-a.adCaptures || b.adRequests-a.adRequests || a.fingerprint.localeCompare(b.fingerprint));
  return {
    schema:'celikom-local-differential-v1',
    decision:'UNKNOWN',
    warning:'These are salted opaque URL-family fingerprints, NOT verified advertisements. No DNR rules may be generated.',
    markerClock:'seconds relative to earliest valid HAR network request PER capture',
    input:{adCaptures,normalCaptures,totalMarkers,normalizedEntries,selectedEvents},
    groups:ordered.slice(0,MAX_GROUPS),
    omittedGroups:Math.max(0,ordered.length-MAX_GROUPS)
  };
}
