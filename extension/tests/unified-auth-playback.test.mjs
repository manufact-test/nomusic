import assert from 'node:assert/strict';
import test from 'node:test';
import {createAuthBroker} from '../dist/unpacked/auth/auth-broker.js';
import {createApiBroker} from '../dist/unpacked/api/api-broker.js';

function fixture() {
  let saved = null, allowed = true, expired = false, offline = false, releaseRefresh;
  const calls = [], local = {};
  const api = {runtime:{id:'unified',getManifest:()=>({version:'0.4.7'})},storage:{local:{get:async k=>({[k]:local[k]}),set:async v=>Object.assign(local,v)}}};
  const store = {get:async()=>saved,set:async v=>{saved=v},clear:async()=>{saved=null}};
  const session = token => ({access_token:token.repeat(64),refresh_token:(token==='a'?'b':'d').repeat(64),user:{id:4,email:'qa@example.org'}});
  const response = (data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
  const fetch = async (url,opts) => {
    if(offline) throw Error('private transport detail');
    const path=new URL(url).pathname;
    calls.push({path,opts});
    if(path.endsWith('/config')) return response({api_version:1,minimum_extension_version:'0.4.0',maintenance:false,features:{auth:true,replacements:true,entitlement:true},upload_enabled:true});
    if(path.endsWith('/login')) return response(session('a'));
    if(path.endsWith('/me')) return expired && opts.headers.Authorization==='Bearer '+'a'.repeat(64) ? response({error:'invalid_session'},401) : response({user:session('a').user});
    if(path.endsWith('/refresh')) {
      if(releaseRefresh) await new Promise(r=>{releaseRefresh.resolve=r});
      return response(session('c'));
    }
    if(path.endsWith('/entitlement')) return response({allowed,source:'trial',valid_until:new Date(Date.now()+432000000).toISOString(),reason:allowed?'trial_active':'trial_inactive'});
    if(path.endsWith('/resolve')) return response({found:true,replacement_id:1,version:1,duration_ms:180872,expires_at:Math.floor(Date.now()/1000)+600,audio_url:'/api/v1/audio/1?token='+'f'.repeat(64)+'&expires='+(Math.floor(Date.now()/1000)+600)+'&sid=55'});
    if(path.endsWith('/logout')) return response({ok:true});
    return response({error:'invalid_request'},400);
  };
  const auth=createAuthBroker(api,{store,fetch,readConfig:async()=>({baseUrl:'https://unified.example'})});
  const resolve=createApiBroker(api,{withAccess:auth.withEntitledAccess,fetch,readConfig:async()=>({baseUrl:'https://unified.example'})});
  const request=()=>resolve({type:'CELIKOM_API_RESOLVE',service:'yandex',trackId:'144530503'},{id:'unified',url:'https://music.yandex.ru/album/1/track/144530503'});
  return {auth,request,calls,local,store,setAllowed:v=>allowed=v,setExpired:v=>expired=v,setOffline:v=>offline=v,blockRefresh:()=>{releaseRefresh={};return releaseRefresh}};
}

test('Stage10 clean email session resolves approved audio without apiTestToken or leaked credentials',async()=>{
  const f=fixture();
  assert.equal((await f.request()).error,'api_access_missing');
  assert.equal((await f.auth.perform('login',{email:'qa@example.org',password:'correct horse battery staple'})).ok,true);
  const result=await f.request();
  assert.equal(result.ok,true);assert.equal(result.asset.replacementId,1);
  assert.match(result.asset.url,/&sid=55$/);
  assert.equal(f.local.apiTestToken,undefined);
  assert.equal(JSON.stringify(result).includes('a'.repeat(64)),false);
  assert.equal(JSON.stringify(result).includes('b'.repeat(64)),false);
  assert.equal(f.calls.find(c=>c.path.endsWith('/resolve')).opts.headers.Authorization,'Bearer '+'a'.repeat(64));
});
test('Stage10 cache cannot bypass denied entitlement, logout, or network loss',async()=>{
  const f=fixture();await f.auth.perform('login',{email:'qa@example.org',password:'correct horse battery staple'});
  assert.equal((await f.request()).ok,true);
  f.setAllowed(false);assert.equal((await f.request()).error,'api_forbidden');
  assert.equal(f.calls.filter(c=>c.path.endsWith('/resolve')).length,1);
  f.setAllowed(true);f.setOffline(true);assert.equal((await f.request()).ok,false);
  f.setOffline(false);await f.auth.perform('logout');assert.equal((await f.request()).error,'api_access_missing');
});
test('Stage10 playback refresh shares account authority and uses rotated bearer',async()=>{
  const f=fixture();await f.auth.perform('login',{email:'qa@example.org',password:'correct horse battery staple'});
  f.setExpired(true);
  assert.equal((await f.request()).ok,true);
  assert.equal(f.calls.filter(c=>c.path.endsWith('/refresh')).length,1);
  assert.equal(f.calls.find(c=>c.path.endsWith('/resolve')).opts.headers.Authorization,'Bearer '+'c'.repeat(64));
});
test('Stage10 an in-flight refresh cannot resurrect credentials after logout',async()=>{
  const f=fixture();await f.auth.perform('login',{email:'qa@example.org',password:'correct horse battery staple'});
  f.setExpired(true);const block=f.blockRefresh();const pending=f.request();
  for(let i=0;i<20&&!block.resolve;i++) await new Promise(r=>setImmediate(r));
  assert.equal(typeof block.resolve,'function');
  await f.auth.perform('logout');block.resolve();
  assert.equal((await pending).ok,false);assert.equal(await f.store.get(),null);
});
