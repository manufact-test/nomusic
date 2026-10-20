/**
 * CELIKOM Ad Protection / Stage 1: local, read-only HAR evidence normalizer.
 * No third-party code. No network I/O. Do not commit or share raw HAR files.
 * A report is not proof that any event is an ad.
 */

const SCHEMA = 'celikom-har-evidence-v1';
const MAX_ENTRIES = 50000;
const MAX_TIMELINE_EVENTS = 1200;
const MAX_WINDOWS = 20;
const KNOWN_TYPES = new Set(['media', 'xmlhttprequest', 'fetch', 'script', 'image', 'stylesheet', 'font', 'other', 'document']);
const ALLOWED_METHODS = new Set(['GET', 'POST', 'HEAD', 'OPTIONS']);

function finiteNumber(n, min, max, fallback = null) {
  return typeof n === 'number' && Number.isFinite(n) && n >= min && n <= max ? n : fallback;
}

function bucketSource(url) {
  if (typeof url !== 'string' || url.length > 16384) return 'unknown';
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') return 'unknown';
    const host = parsed.hostname.toLowerCase();
    if (host === 'music.yandex.ru') return 'music-site';
    if (/^(?:[a-z0-9-]+\.)*yandex\.(?:ru|net|com|by|kz|uz)$/.test(host) ||
        /^(?:[a-z0-9-]+\.)*(?:yastatic\.net|yandexcdn\.com)$/.test(host)) return 'yandex-family';
    return 'other-host';
  } catch {
    return 'unknown';
  }
}

function mimeBucket(mime) {
  if (typeof mime !== 'string') return 'unknown';
  const type = mime.split(';', 1)[0].toLowerCase().trim();
  if (type.startsWith('audio/')) return 'audio';
  if (type.startsWith('video/')) return 'video';
  if (['application/vnd.apple.mpegurl', 'application/x-mpegurl'].includes(type)) return 'hls-manifest';
  if (type === 'application/dash+xml') return 'dash-manifest';
  if (type === 'application/json' || type.endsWith('+json')) return 'json';
  if (type.startsWith('image/')) return 'image';
  if (type.startsWith('text/') || type === 'application/javascript') return 'text';
  if (type === '' || type === 'application/octet-stream') return 'unknown';
  return 'other';
}

function resourceType(entry, mime) {
  const raw = entry?._resourceType ?? entry?.request?._resourceType;
  if (typeof raw === 'string') {
    const mapped = raw.toLowerCase();
    if (KNOWN_TYPES.has(mapped)) return mapped;
    if (mapped === 'xhr') return 'xmlhttprequest';
  }
  if (mime === 'audio' || mime === 'video' || mime === 'hls-manifest' || mime === 'dash-manifest') return 'media';
  if (mime === 'image') return 'image';
  if (mime === 'json') return 'fetch';
  return 'other';
}

function hasRangeHeader(headers) {
  if (!Array.isArray(headers) || headers.length > 1000) return false;
  return headers.some(h => h && typeof h.name === 'string' && h.name.toLowerCase() === 'range');
}

function normalize(entry, originMs) {
  if (!entry || typeof entry !== 'object' || !entry.request || !entry.response) return null;
  const timestamp = Date.parse(entry.startedDateTime);
  if (!Number.isFinite(timestamp)) return null;
  const seconds = Math.max(0, Math.round((timestamp - originMs) / 1000));
  const headers = Array.isArray(entry.response.headers) ? entry.response.headers : [];
  const contentType = headers.find(h => h && typeof h.name === 'string' && h.name.toLowerCase() === 'content-type');
  const mime = mimeBucket(entry.response?.content?.mimeType || contentType?.value);
  const resource = resourceType(entry, mime);
  const rawStatus = entry.response.status;
  const status = Number.isInteger(rawStatus) && rawStatus >= 0 && rawStatus <= 599 ? rawStatus : null;
  const method = ALLOWED_METHODS.has(entry.request.method) ? entry.request.method : 'OTHER';
  const duration = finiteNumber(entry.time, 0, 86400000);
  const durationMs = duration === null ? null : Math.round(duration);
  return {
    second: seconds,
    resource,
    mime,
    source: bucketSource(entry.request.url),
    method,
    status,
    partial: status === 206,
    rangeRequest: hasRangeHeader(entry.request.headers),
    durationMs
  };
}

/**
 * A window marker is a manually supplied relative timestamp of an audible ad,
 * NOT an automatically inferred ad. No user-supplied note, label or URL retained.
 */
function normalizeMarkers(markers) {
  if (!Array.isArray(markers) || markers.length > MAX_WINDOWS) throw Error('Too many observation markers');
  return markers.map((value) => {
    // Do not silently coerce empty strings, booleans, null or arrays to a time.
    if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 86400)
      throw Error('Invalid marker second');
    const n = value;
    return Math.round(n);
  });
}

function histogram(events) {
  const counts = {
    resource: Object.create(null),
    mime: Object.create(null),
    source: Object.create(null),
    status: Object.create(null),
    ranged: 0,
    partial206: 0
  };
  for (const e of events) {
    for (const key of ['resource', 'mime', 'source']) counts[key][e[key]] = (counts[key][e[key]] ?? 0) + 1;
    const status = e.status === null ? 'unknown' : String(e.status);
    counts.status[status] = (counts.status[status] ?? 0) + 1;
    if (e.rangeRequest) counts.ranged++;
    if (e.partial) counts.partial206++;
  }
  return counts;
}

function trackable(e) {
  return e.resource === 'media' || e.resource === 'xmlhttprequest' || e.resource === 'fetch' ||
    ['audio', 'video', 'hls-manifest', 'dash-manifest'].includes(e.mime);
}

export function summarizeHar(document, options = {}) {
  const entries = document?.log?.entries;
  if (!Array.isArray(entries)) throw Error('Expected HAR 1.2 log.entries array');
  if (entries.length > MAX_ENTRIES) throw Error('HAR has too many entries; split capture locally');
  const marks = normalizeMarkers(options.markers ?? []);
  const radius = finiteNumber(options.radiusSeconds ?? 12, 1, 120);
  if (radius === null) throw Error('Invalid window radius');
  // Avoid spreading up to 50,000 timestamps as function arguments.
  let first = Infinity;
  for (const entry of entries) {
    const ms = Date.parse(entry?.startedDateTime);
    if (Number.isFinite(ms) && ms < first) first = ms;
  }
  if (!Number.isFinite(first)) first = 0;
  // No request URL, path, query, header value or token can enter output.
  const events = entries.map(e => normalize(e, first)).filter(Boolean);
  events.sort((a, b) => a.second - b.second);
  const timeline = events.filter(trackable);
  const compact = timeline.slice(0, MAX_TIMELINE_EVENTS);
  const windows = marks.map(second => {
    const inside = timeline.filter(e => Math.abs(e.second - second) <= radius);
    return {
      markerSecond: second,
      radiusSeconds: radius,
      countedRequests: inside.length,
      counts: histogram(inside),
      // Bounded preview. Fine-grained URLs, payloads and headers are omitted.
      events: inside.slice(0, 100),
      droppedPreviewEvents: Math.max(0, inside.length - 100)
    };
  });
  return {
    schema: SCHEMA,
    warning: 'OFFLINE SYNTHETIC/USER CAPTURE; NO ad identification. Each marker is MANUAL and unverified.',
    decision: 'UNKNOWN',
    inputEntries: entries.length,
    parsedEntries: events.length,
    omittedInvalidEntries: entries.length - events.length,
    durationSeconds: events.length ? events[events.length - 1].second : 0,
    counts: histogram(events),
    timeline: compact,
    droppedTimelineEvents: Math.max(0, timeline.length - compact.length),
    windows
  };
}

export {bucketSource, mimeBucket};
