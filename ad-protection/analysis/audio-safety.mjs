/** Read-only analysis. This module does not block any request. */
export function assessAudioSafety(report) {
 if(!report||report.schema!=='celikom-local-differential-v1'||report.decision!=='UNKNOWN'||!Array.isArray(report.groups)||!report.input||!Number.isSafeInteger(report.input.adCaptures)||!Number.isSafeInteger(report.input.normalCaptures))throw Error('Invalid differential report');
 let differential=0,ordinaryOverlap=0,mediaRangeRisk=0,mediaCandidates=0;
 const reasons=[];
 for(const g of report.groups){
  if(!g||g.forbiddenForBlocking!==true||!['adRequests','normalRequests','partial206Requests','rangeRequests','mediaLikeRequests'].every(k=>Number.isSafeInteger(g[k])&&g[k]>=0))throw Error('Invalid sanitized group');
  if(g.evidenceHint==='differential-candidate-only')differential++;
  if(g.adRequests>0&&g.normalRequests>0)ordinaryOverlap++;
  if(g.adRequests>0&&(g.rangeRequests>0||g.partial206Requests>0))mediaRangeRisk++;
  if(g.adRequests>0&&g.mediaLikeRequests>0)mediaCandidates++;
 }
 if(report.input.adCaptures<2)reasons.push('Too few independent ad observations');
 if(report.input.normalCaptures<2)reasons.push('Too few normal playback controls');
 if(differential===0)reasons.push('No repeated differential signature');
 if(ordinaryOverlap>0)reasons.push('Candidate also occurred during normal music');
 if(mediaRangeRisk>0)reasons.push('Possible music CDN or Range traffic - do not block');
 reasons.push('Live audible advertisement and uninterrupted playback not verified');
 return {schema:'celikom-audio-safety-v1',gate:'HOLD',blockingAllowed:false,rulesProposed:0,decision:'UNKNOWN',observations:{adCaptures:report.input.adCaptures,normalCaptures:report.input.normalCaptures,comparedGroups:report.groups.length,differentialCandidates:differential,ordinaryOverlap,mediaRangeRisk,mediaCandidates},reasons,requiredBeforeAnyLiveBlock:['Authorized real audio ad observations','Independent negative-control playback sessions','Proof media Range/CDN/queue/entitlement are unaffected','No silent ad-length gaps or stuck tracks','Chrome runtime and policy review']};
}
