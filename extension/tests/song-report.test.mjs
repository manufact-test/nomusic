import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSongReport,buildSupportReport} from '../dist/unpacked/popup/song-report.js';
const state={enabled:true,phase:'READY',track:{id:'50163040',confidence:260,ambiguous:false,metadata:{durationMs:187520,title:'Холодно',artist:'SLIMUS'}},network:[{endpoint:'config',httpStatus:504,result:'api_response_error',elapsedMs:10000,Authorization:'SECRET'}],token:'SECRET',account:{email:'PRIVATE'},connection:{controllerPresent:true,detail:'SECRET'},recentLog:['SECRET'],player:{source:'https://private/SECRET',currentTime:3,duration:187.594,paused:false}};
test('song report captures useful state while excluding tokens, URLs, accounts and raw logs',()=>{
 const report=buildSongReport(state,'audio_issue','0.4.41');assert.equal(report.track.id,'50163040');assert.equal(report.diagnostics.network[0].httpStatus,504);assert.equal(report.diagnostics.currentTime,3);assert.equal(report.diagnostics.trace.at(-1).event,'status');assert.equal(report.diagnostics.trace[0].event,'backend_http');assert.equal(report.diagnostics.trace[0].httpCode,504);
 assert.doesNotMatch(JSON.stringify(report),/SECRET|PRIVATE|https:|Authorization/);
});
test('song report never attaches uncertain track identity or unknown category',()=>{
 for(const track of [{...state.track,ambiguous:true},{...state.track,confidence:20},{...state.track,id:null}])assert.throws(()=>buildSongReport({...state,track},'other','0.4.41'));
 assert.throws(()=>buildSongReport(state,'arbitrary','0.4.41'));
});

test('ordinary support works without a confident track and captures player timings without private state',()=>{
 const report=buildSupportReport({...state,track:null,playback:{activationCount:3,restoreCount:2,lastRestore:{reason:'api_forbidden'},startupHistory:[{prepareMs:150,masterTimeMs:900,at:Date.now(),token:'SECRET'}]}},'0.4.74');
 assert.equal(report.track,undefined);assert.equal(report.diagnostics.currentTime,3);assert.equal(report.diagnostics.activationCount,3);
 assert.equal(report.diagnostics.trace.at(-1).event,'replacement_prepared');assert.doesNotMatch(JSON.stringify(report),/SECRET|PRIVATE|https:/);
});
test('ordinary report ignores malformed network entries and bounds the attachment',()=>{
 const report=buildSupportReport({...state,network:[null,...Array.from({length:1000},()=>({endpoint:'config',result:'api_network_error',elapsedMs:10000}))]},'0.4.74');
 assert.ok(new TextEncoder().encode(JSON.stringify(report)).length<=6500);assert.ok(report.diagnostics.network.length<=12);assert.ok(report.diagnostics.trace.length<=32);
});
