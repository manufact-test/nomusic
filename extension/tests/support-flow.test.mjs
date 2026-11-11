import test from 'node:test';
import assert from 'node:assert/strict';
import {initSupport} from '../dist/unpacked/popup/support.js';
function node(value=''){const listeners=new Map();return {value,textContent:'',hidden:false,disabled:false,addEventListener:(n,f)=>listeners.set(n,f),fire:n=>listeners.get(n)?.()};}
function fixture(){
 const nodes=new Map(['panel','send','description','note','kind','category','song-fields','track','label'].map(k=>[k,node()]));nodes.get('kind').value='general';nodes.get('category').value='audio_issue';
 const requests=[];let fail=false,statusFail=false,state={enabled:true,phase:'READY',track:{id:'50163040',confidence:260,ambiguous:false,metadata:{durationMs:187520,title:'Холодно',artist:'SLIMUS'}},token:'SECRET'};
 const send=async m=>{if(m.type==='CELIKOM_STATUS_GET'||m.type==='CELIKOM_SUPPORT_STATUS_GET'){if(statusFail)throw Error('snapshot unavailable');return state;}requests.push(m);if(fail)throw Error('network');return {ok:true,ticket_id:5};};
 let draft={};globalThis.chrome={runtime:{getManifest:()=>({version:'0.4.41'})},storage:{session:{get:async()=>draft,set:async v=>Object.assign(draft,v),remove:async k=>delete draft[k]}}};
 return {nodes,requests,send,doc:{querySelector:s=>nodes.get(s.match(/data-support-([^\]]+)/)[1])},setFail:v=>fail=v,setStatusFail:v=>statusFail=v,setTrack:id=>state={...state,track:{...state.track,id}}};
}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
test('ordinary support attaches diagnostics, song report pins track and retries the exact payload',async()=>{
 const f=fixture();await initSupport({document:f.doc,send:f.send});
 f.nodes.get('description').value='Обычное сообщение';await f.nodes.get('send').fire('click');assert.equal(f.requests[0].kind,'general');assert.equal(f.requests[0].message,'Обычное сообщение');assert.equal(f.requests[0].report.platform,'chromium');assert.equal(f.requests[0].report.diagnostics.phase,'READY');assert.doesNotMatch(JSON.stringify(f.requests[0]),/SECRET/);
 f.nodes.get('kind').value='song';f.nodes.get('kind').fire('change');await tick();assert.match(f.nodes.get('track').textContent,/Холодно/);
 f.nodes.get('description').value='';f.nodes.get('description').fire('input');f.setFail(true);await f.nodes.get('send').fire('click');const first=f.requests.at(-1);assert.equal(first.report.category,'audio_issue');assert.equal(first.message,'');assert.doesNotMatch(JSON.stringify(first),/SECRET/);
 f.setFail(false);await f.nodes.get('send').fire('click');assert.deepEqual(f.requests.at(-1),first);assert.match(f.nodes.get('note').textContent,/песней отправлено/);
});
test('a changed song is never silently attached to the old report and duplicate click sends once',async()=>{
 const f=fixture();await initSupport({document:f.doc,send:f.send});f.nodes.get('kind').value='song';f.nodes.get('kind').fire('change');await tick();f.setTrack('50163041');await f.nodes.get('send').fire('click');assert.equal(f.requests.length,0);assert.match(f.nodes.get('note').textContent,/Трек изменился/);
 f.nodes.get('kind').fire('change');await tick();await Promise.all([f.nodes.get('send').fire('click'),f.nodes.get('send').fire('click')]);assert.equal(f.requests.length,1);assert.equal(f.requests[0].report.track.id,'50163041');
});

test('ordinary support snapshot is pinned on retries and collection failure never loses the message',async()=>{
 const f=fixture();await initSupport({document:f.doc,send:f.send});
 f.nodes.get('description').value='Не подключается';f.setFail(true);
 await f.nodes.get('send').fire('click');const first=structuredClone(f.requests.at(-1));
 f.setTrack('50163041');f.setFail(false);await f.nodes.get('send').fire('click');assert.deepEqual(f.requests.at(-1),first);
 const g=fixture();await initSupport({document:g.doc,send:g.send});g.setStatusFail(true);
 g.nodes.get('description').value='Ошибка запуска';await g.nodes.get('send').fire('click');
 assert.equal(g.requests.length,1);assert.equal(g.requests[0].message,'Ошибка запуска');assert.equal(g.requests[0].report.diagnostics.connectionError,'support_status_unavailable');
});
