/**
 * Join read-only CELIKOM observer markers with a local HAR snapshot.
 * A manually supplied offset is required because clocks have different origins.
 * Does NOT inspect audio bodies, block traffic, or infer that a network request is advertising.
 */
import {summarizeHar} from './har-evidence.mjs';

const TYPES = new Set(['ad-heard', 'normal-music', 'video-ad-seen', 'popup-ad-seen']);
const MAX_MARKERS = 20;

export function validateObserverSnapshot(value) {
  if (!value || typeof value !== 'object' ||
      value.schema !== 'celikom-ad-observer-v1' ||
      !Array.isArray(value.markers) || value.markers.length > 24 ||
      !Number.isSafeInteger(value.ageSeconds) || value.ageSeconds < 0 || value.ageSeconds > 86400) {
    throw Error('Invalid observation report format');
  }
  const normalized = value.markers.map(marker => {
    if (!marker || typeof marker !== 'object' || !TYPES.has(marker.kind) ||
        typeof marker.s !== 'number' || !Number.isFinite(marker.s) ||
        marker.s < 0 || marker.s > value.ageSeconds + 2) {
      throw Error('Invalid observation marker');
    }
    return {kind:marker.kind,second:Math.round(marker.s)};
  });
  if (normalized.some((marker,i)=>i>0 && marker.second<normalized[i-1].second)) {
    throw Error('Nonchronological manual markers');
  }
  return normalized;
}

export function alignObservation(observer, har, options={}) {
  const offset=options.offsetSeconds;
  if (typeof offset!=='number' || !Number.isFinite(offset) || Math.abs(offset)>86400) {
    throw Error('Provide finite observer-to-HAR start offset, within +/-86400 seconds');
  }
  const radius = options.radiusSeconds ?? 12;
  if (!Number.isInteger(radius) || radius < 1 || radius > 120) throw Error('Invalid radius');
  const markers=validateObserverSnapshot(observer);
  if (!markers.length) throw Error('At least one manual marker is required');
  if (markers.length>MAX_MARKERS) throw Error('At most 20 manual markers per report; reset and capture a shorter session');

  const aligned=markers.map(m=>({kind:m.kind,observerSecond:m.second,harSecond:Math.round(m.second+offset)}));
  if (aligned.some(m=>m.harSecond<0 || m.harSecond>86400)) {
    throw Error('Marker is outside plausible HAR time range; verify synchronization offset');
  }
  const harReport=summarizeHar(har,{markers:aligned.map(m=>m.harSecond),radiusSeconds:radius});
  // Only allow fields produced by sanitizer; original observation is not echoed back.
  const alignedWindows=aligned.map((mark,i)=>({
    marker:mark.kind,
    observerSecond:mark.observerSecond,
    harSecond:mark.harSecond,
    requests:harReport.windows[i].countedRequests,
    counts:harReport.windows[i].counts,
    events:harReport.windows[i].events,
    droppedPreviewEvents:harReport.windows[i].droppedPreviewEvents
  }));
  return {
    schema:'celikom-aligned-evidence-v1',
    decision:'UNKNOWN',
    warning:'Manual timing correlation only. Requests near an ad do not prove they serve the ad.',
    offsetSeconds:offset,
    radiusSeconds:radius,
    parsedEntries:harReport.parsedEntries,
    invalidEntries:harReport.omittedInvalidEntries,
    alignmentQuality:{
      synchronization:'manual-offset-not-independently-verified',
      emptyWindows:alignedWindows.filter(item=>item.requests===0).length,
      partialContentWindows:alignedWindows.filter(item=>item.counts.partial206>0).length,
      requestCorrelationProvesAdvertising:false
    },
    markers:alignedWindows
  };
}
