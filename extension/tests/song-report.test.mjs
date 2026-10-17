import test from 'node:test';
import assert from 'node:assert/strict';
import {buildSongReport} from '../dist/unpacked/popup/song-report.js';
const state={enabled:true,phase:'READY',track:{id:'50163040',confidence:260,ambiguous:false,metadata:{durationMs:187520,title:'Холодно',artist:'SLIMUS'}},network:[{endpoint:'config',httpStatus:504,result:'api_response_error',elapsedMs:10000,Authorization:'SECRET'}],token:'SECRET',account:{email:'PRIVATE'},connection:{controllerPresent:true,detail:'SECRET'},recentLog:['SECRET'],player:{source:'https://private/SECRET',currentTime:3,duration:187.594,paused:false}};
test('song report captures useful state while excluding tokens, URLs, accounts and raw logs',()=>{
 const report=buildSongReport(state,'audio_issue','0.4.41');assert.equal(report.track.id,'50163040');assert.equal(report.diagnostics.network[0].httpStatus,504);assert.equal(report.diagnostics.currentTime,3);
 assert.doesNotMatch(JSON.stringify(report),/SECRET|PRIVATE|https:|Authorization/);
});
test('song report never attaches uncertain track identity or unknown category',()=>{
 for(const track of [{...state.track,ambiguous:true},{...state.track,confidence:20},{...state.track,id:null}])assert.throws(()=>buildSongReport({...state,track},'other','0.4.41'));
 assert.throws(()=>buildSongReport(state,'arbitrary','0.4.41'));
});
