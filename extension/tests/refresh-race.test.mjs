import assert from 'node:assert/strict';
import {createAuthBroker} from '../dist/unpacked/auth/auth-broker.js';
const response=(v,code=200)=>new Response(JSON.stringify(v),{status:code,headers:{'content-type':'application/json'}});
const a='a'.repeat(64),b='b'.repeat(64),c='c'.repeat(64),d='d'.repeat(64);
let saved={user:{id:1,email:'fixture@example.invalid'},access_token:a,refresh_token:b};
let releaseRefresh, releaseStaleMe, startedRefresh, startedStaleMe;
const refreshStarted=new Promise(r=>startedRefresh=r),staleMeStarted=new Promise(r=>startedStaleMe=r);
let meCalls=0,refreshCalls=0,revoked=false;
const api={storage:{local:{get:async()=>({celikomInstallationId:'12345678-1234-4123-8123-123456789abc'}),set:async()=>{}}},runtime:{getURL:x=>x}};
const broker=createAuthBroker(api,{store:{get:async()=>saved,set:async x=>{saved=x},clear:async()=>{saved=null}},readConfig:async()=>({baseUrl:'https://fixture.invalid'}),fetch:async(url,opts)=>{
 const path=new URL(url).pathname;
 if(path.endsWith('/me')){meCalls++;if(meCalls===1)return response({error:'invalid_session'},401);if(meCalls===2){startedStaleMe();return new Promise(r=>releaseStaleMe=()=>r(response({error:'invalid_session'},401)));}return response({user:saved.user});}
 if(path.endsWith('/refresh')){refreshCalls++;if(refreshCalls===1){startedRefresh();return new Promise(r=>releaseRefresh=()=>r(response({...saved,access_token:c,refresh_token:d})));}if(JSON.parse(opts.body).refresh_token===b)revoked=true;return response({error:'invalid_session'},401);}
 throw new Error('unexpected fixture endpoint');
}});
const first=broker.withAccess(async()=>true);await refreshStarted;
const second=broker.withAccess(async()=>true).then(()=>({ok:true}),e=>({ok:false,error:e.message}));await staleMeStarted;
releaseRefresh();await first;releaseStaleMe();const result=await second;
console.log(JSON.stringify({firstSucceeded:true,second:result,refreshCalls,oldRefreshReplayRevokedDesktopSession:revoked,remoteRequests:0}));
assert.equal(revoked,false,'rotated token must never be replayed');
assert.equal(refreshCalls,1);assert.equal(result.ok,true);
