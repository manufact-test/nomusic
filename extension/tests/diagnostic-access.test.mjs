import assert from 'node:assert/strict';
import test from 'node:test';
import {diagnosticsIdentity,redactDiagnostics,publicPlaybackState} from '../dist/unpacked/auth/diagnostic-access.js';
import {createAuthBroker} from '../dist/unpacked/auth/auth-broker.js';
const approved='18e9af33bc55e691582e0495d6f9024611649a3342742ec7569cd565e28af572';
test('support rights require an active, valid server identity and exact allowlist digest',async()=>{
 assert.equal(await diagnosticsIdentity({id:1,email:'ordinary@example.test',status:'active'}),false);
 assert.equal(await diagnosticsIdentity({id:1,email:' fixture@example.test ',status:'active'},async s=>{assert.equal(s,'fixture@example.test');return approved;}),true);
 for(const user of [null,{}, {id:0,email:'fixture@example.test',status:'active'},{id:1,email:'fixture@example.test',status:'blocked'},{id:1,email:'fixture@example.test',status:'active',role:'owner',promo:'forever'}]){
  assert.equal(await diagnosticsIdentity(user,async()=> 'not-allowlisted'),false);
 }
 assert.equal(await diagnosticsIdentity({id:1,email:'a@example.test'} ,async()=>approved),false);
});
test('normal UI status has no full player timeline, raw network events or signed audio URLs',()=>{
 const state={enabled:true,phase:'READY',version:'test',player:{paused:false,src:'https://audio.test/file?token=secret'},network:[{secret:1}],replacementPlayer:{clock:123},playback:{internal:'trace'},scoring:{private:1},preparation:{stage:'ready',elapsedMs:12,stream:{url:'private'}}};
 assert.deepEqual(publicPlaybackState(state),{enabled:true,phase:'READY',version:'test',player:{paused:false},preparation:{stage:'ready',elapsedMs:12}});
});
test('even owner exports strip credentials and signed URL queries',()=>{
 const out=redactDiagnostics({access_token:'secret',nested:{authorization:'Bearer abc',src:'https://x.test/file?token=abc#secret'},note:'Bearer abc123'});
 assert.equal(JSON.stringify(out).includes('abc'),false);assert.equal(out.nested.src,'https://x.test/file');
});
test('locally saved identity and promo are never sufficient for privileged export',async()=>{
 const saved={user:{id:7,email:'spoofed@example.test'},access_token:'a'.repeat(64),refresh_token:'b'.repeat(64)};
 let response={user:{id:7,email:'ordinary@example.test',status:'active'}},calls=0;
 const broker=createAuthBroker({storage:{local:{get:async()=>({}),set:async()=>{}}},runtime:{getURL:p=>p}}, {
  store:{get:async()=>saved,set:async()=>{},clear:async()=>{}},readConfig:async()=>({baseUrl:'https://api.example.test'}),
  fetch:async()=>{calls++;return new Response(JSON.stringify(response),{status:200,headers:{'content-type':'application/json'}});}
 });
 assert.equal((await broker.perform('diagnostics-access')).allowed,false);
 let invoked=false;await assert.rejects(broker.withDiagnosticsAccess(()=>{invoked=true;}),/access_denied/);assert.equal(invoked,false);assert.ok(calls>=2);
 response={user:{id:8,email:'ordinary@example.test',status:'active'}};
 await assert.rejects(broker.withDiagnosticsAccess(()=>true),/access_denied/);
});
