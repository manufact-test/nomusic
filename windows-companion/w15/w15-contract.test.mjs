import test from "node:test";
import assert from "node:assert/strict";
import {createCelikomSourceController, validateCelikomGrant, exactTrackId} from "./source-controller.mjs";
import {createCompanionBridge, LOCAL_ORIGIN} from "./bridge-client.mjs";
const ORIGIN = "https://api.celikom.example";
const NOW = 1794182400000;
const EXP = Math.floor(NOW/1000)+120;
const TOKEN = "a".repeat(64);
const url = "/api/v1/audio/42?token="+TOKEN+"&expires="+EXP+"&sid=7";
const grant = id => ({trackId:id, approved:true, entitled:true,
  audioUrl:ORIGIN+url, expiresAt:EXP*1000});
function fixture(resolver=async id=>grant(id)){
  let change=()=>{}, writes=[];
  const api={
    player:{getSnapshot:async()=>({track:{id:"123"}}),
      onTrackChange:fn=>{change=fn;return()=>{change=()=>{}}}},
    client:{setTrackReplacements:async map=>{writes.push({map})},
      clearTrackReplacements:async()=>{writes.push({clear:true})}}
  };
  const c=createCelikomSourceController({api,resolve:resolver,allowedOrigin:ORIGIN,now:()=>NOW});
  return {c,writes,change:t=>change(t)};
}
test("W15 numeric IDs only, no colon or fuzzy title",()=>{
  assert.equal(exactTrackId({id:"12345678901234567890"}),"12345678901234567890");
  for(const id of ["123:42","0001","1/",0,"name",Infinity])
    assert.equal(exactTrackId({id}),null);
});
test("W15 validates actual PHP ResolveService audio + sid + expires",()=>{
  assert.equal(validateCelikomGrant(grant("123"),"123",ORIGIN,NOW),ORIGIN+url);
});
test("W15 rejects stale, cross-origin, mismatched or duplicated grant",()=>{
  const bad=[
    {trackId:"other"},{approved:false},{entitled:false},
    {expiresAt:EXP*1000-1000},{expiresAt:NOW+40*60*1000},
    {audioUrl:"http://api.celikom.example"+url},
    {audioUrl:"https://api.celikom.example.evil.com"+url},
    {audioUrl:ORIGIN+url+"&sid=8"},
    {audioUrl:ORIGIN+url+"&unused=1"},
    {audioUrl:ORIGIN+url.replace(TOKEN,"abc")},
    {audioUrl:ORIGIN+url.replace("sid=7","sid=0")},
    {audioUrl:ORIGIN+url.replace("expires="+EXP,"expires="+(EXP+1))}
  ];
  for(const patch of bad)assert.equal(
    validateCelikomGrant({...grant("123"),...patch},"123",ORIGIN,NOW),null,
    JSON.stringify(patch));
});
test("W15 off by default, set only one mapping then clean on Stop",async()=>{
  const x=fixture();await x.c.start();
  assert.equal(x.writes.filter(v=>v.map).length,0);
  x.c.enable();await x.c.flush();
  assert.deepEqual(Object.keys(x.writes.find(v=>v.map).map),["123"]);
  assert.equal(x.c.status,"SDK_MAPPING_ACCEPTED");
  x.c.disable();await x.c.flush();
  assert.equal(x.writes.at(-1).clear,true);
  await x.c.dispose();
});
test("W15 Next cancels stale result and Original persists until new track",async()=>{
  let release;
  const delayed=new Promise(r=>{release=r});
  const x=fixture(id=>id==="123"?delayed:Promise.resolve(grant(id)));
  await x.c.start();x.c.enable();await new Promise(r=>setImmediate(r));
  x.change({id:"789"});release(grant("123"));
  await x.c.flush();
  assert.deepEqual(x.writes.filter(v=>v.map).map(v=>Object.keys(v.map)),[["789"]]);
  x.c.original();await x.c.flush();
  x.change({id:"789"});await x.c.flush();
  assert.equal(x.writes.filter(v=>v.map).length,1);
  x.change({id:"999"});await x.c.flush();
  assert.equal(x.writes.filter(v=>v.map).length,2);
  await x.c.dispose();
});
test("W15 denied entitlement never sends source",async()=>{
  const x=fixture(async()=>({...grant("123"),entitled:false}));
  await x.c.start();x.c.enable();await x.c.flush();
  assert.equal(x.writes.some(v=>v.map),false);
  await x.c.dispose();
});
test("W15 bridge refuses requests before explicit pairing",async()=>{
  const calls=[];
  const local=createCompanionBridge({net:{json:async(url)=>{calls.push(url);
    return {companion:true,version:15};
  }},storage:{get:async()=>undefined,set:async()=>{}}});
  await local.initialize();
  assert.equal(await local.health(),true);
  assert.equal(await local.resolve("123"),null);
  assert.equal(await local.pair("abc"),false);
  assert.deepEqual(calls,[LOCAL_ORIGIN+"/v1/health"]);
});
test("W15 paired token only in local header; not account credentials",async()=>{
  const saved={},calls=[];
  const local=createCompanionBridge({
    storage:{get:async k=>saved[k],set:async(k,v)=>{saved[k]=v}},
    net:{json:async(url,opts)=>{calls.push({url,opts});
      if(url.endsWith("/v1/pair"))return {bridgeToken:"b".repeat(64)};
      if(url.endsWith("/v1/state"))return {signedIn:true,enabled:true,apiOrigin:ORIGIN};
      if(url.includes("/v1/resolve"))return {found:true,grant:grant("123")};
      return {ok:true};
    }}
  });
  await local.initialize();
  assert.equal(await local.pair("123456"),true);
  assert.deepEqual(await local.state(),{paired:true,signedIn:true,enabled:true,apiOrigin:ORIGIN});
  assert.deepEqual(await local.resolve("123"),grant("123"));
  assert.equal(await local.resolve("wrong"),null);
  await local.heartbeat("123","SDK_MAPPING_ACCEPTED");
  for(const {url,opts} of calls){
    assert.ok(url.startsWith(LOCAL_ORIGIN+"/v1/"));
    assert.ok(!url.includes("b".repeat(64)));
    if(!url.endsWith("/v1/pair"))
      assert.equal(opts.headers["X-Celikom-Bridge-Token"],"b".repeat(64));
  }
});
