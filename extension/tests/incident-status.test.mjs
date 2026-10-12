import test from 'node:test';
import assert from 'node:assert/strict';
import { initIncidentStatus } from '../dist/unpacked/popup/incident-status.js';
function fixture() {
  const nodes=new Map(['[data-incident-banner]','[data-music-controls]','[data-music-details]','[data-auth-panel]'].map(s=>[s,{hidden:s==='[data-incident-banner]'}]));
  let value={incident:{service:'yandex',active:true}},fail=false,calls=0;
  const presentation=initIncidentStatus({document:{querySelector:s=>nodes.get(s)},readConfig:async()=>({baseUrl:'https://fixture.example/'}),fetch:async(url,options)=>{
    calls++;assert.equal(url,'https://fixture.example/api/v1/config');assert.equal(options.credentials,'omit');assert.equal(options.redirect,'error');assert.equal(options.headers,undefined);
    if(fail)throw Error('network unavailable');return{ok:true,json:async()=>value};
  }});
  return{nodes,presentation,set:v=>{value=v},fail:v=>{fail=v},calls:()=>calls};
}
test('global incident replaces music controls even when signed out, stopped and without a Yandex tab',async()=>{
  const f=fixture();f.presentation.updateController({enabled:false,track:null});await f.presentation.refresh();
  assert.equal(f.presentation.active(),true);assert.equal(f.nodes.get('[data-incident-banner]').hidden,false);
  for(const s of ['[data-music-controls]','[data-music-details]'])assert.equal(f.nodes.get(s).hidden,true);
  assert.equal(f.nodes.get('[data-auth-panel]').hidden,false,'account stays accessible');
  f.presentation.updateController({enabled:false,suspended:false});assert.equal(f.presentation.active(),true);
  f.fail(true);await f.presentation.refresh();assert.equal(f.presentation.active(),true,'transport failure cannot clear a confirmed outage');
  f.fail(false);f.set({incident:{service:'yandex',active:false}});await f.presentation.refresh();
  assert.equal(f.presentation.active(),false);assert.equal(f.nodes.get('[data-music-controls]').hidden,false);
  assert.equal(f.nodes.get('[data-incident-banner]').hidden,true);
});
test('network failure and malformed or other-service state do not invent a global incident',async()=>{
  const f=fixture();f.fail(true);await f.presentation.refresh();assert.equal(f.presentation.active(),false);
  f.fail(false);f.set({incident:{service:'future_adapter',active:true}});await f.presentation.refresh();assert.equal(f.presentation.active(),false);
  f.set({incident:{service:'yandex',active:'true'}});await f.presentation.refresh();assert.equal(f.presentation.active(),false);
});
test('authoritative resolution clears stale controller suspension and keeps stopped users able to Start',async()=>{
  const f=fixture();f.presentation.updateController({suspended:true,replacementError:'service_incident',enabled:false});
  assert.equal(f.presentation.active(),true);f.set({incident:{service:'yandex',active:false}});await f.presentation.refresh();
  f.presentation.updateController({suspended:true,replacementError:'service_incident',enabled:false});
  assert.equal(f.presentation.active(),false,'old stopped content flag cannot trap the popup after resolution');
});
test('reopening immediately presents the saved outage and refresh clears it without authorizing playback',async()=>{
  const saved=globalThis.localStorage;const data=new Map();
  globalThis.localStorage={getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v)};
  try{
    const first=fixture();await first.presentation.refresh();const reopened=fixture();
    assert.equal(reopened.presentation.active(),true);assert.equal(reopened.nodes.get('[data-music-controls]').hidden,true);
    reopened.set({incident:{service:'yandex',active:false}});await reopened.presentation.refresh();assert.equal(reopened.presentation.active(),false);
  }finally{globalThis.localStorage=saved}
});
