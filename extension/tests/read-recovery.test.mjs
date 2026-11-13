import test from 'node:test';
import assert from 'node:assert/strict';
import {createReadRecovery} from '../dist/unpacked/shared/read-recovery.js';
const transient=()=>Object.assign(new Error('gateway'),{retryable:true});
const flush=()=>new Promise(setImmediate);

test('idempotent read recovers after a transient gateway failure without a connectivity event',async(t)=>{
 t.mock.timers.enable({apis:['setTimeout','Date']});let calls=0;
 const recovery=createReadRecovery();const pending=recovery.run(async()=>{if(++calls===1)throw transient();return 'verified';});
 await flush();assert.equal(calls,1);t.mock.timers.tick(500);
 assert.equal(await pending,'verified');assert.equal(calls,2);
});
test('GET retry count and total deadline are bounded, while POST is never replayed',async(t)=>{
 t.mock.timers.enable({apis:['setTimeout','Date']});let calls=0;const recovery=createReadRecovery();
 const pending=recovery.run(async()=>{calls++;throw transient();});const checked=assert.rejects(pending,/gateway/);
 await flush();t.mock.timers.tick(500);await flush();t.mock.timers.tick(1000);await checked;assert.equal(calls,3);
 calls=0;await assert.rejects(recovery.run(async()=>{calls++;throw transient();},'POST'),/gateway/);assert.equal(calls,1);
 let signal;const dead=recovery.run(signalValue=>new Promise((_resolve,reject)=>{signal=signalValue;signal.addEventListener('abort',()=>reject(transient()),{once:true});}));
 const expired=assert.rejects(dead,/request_timeout/);await flush();t.mock.timers.tick(20000);await expired;assert.equal(signal.aborted,true);
});
test('reset aborts reads from the old connection and rejects late success without cancelling a write',async()=>{
 const recovery=createReadRecovery();let finish,signal;
 const old=recovery.run(s=>{signal=s;return new Promise(r=>finish=r);});const rejected=assert.rejects(old,/network_changed/);
 let finishWrite,writeSignal;const write=recovery.run(s=>{writeSignal=s;return new Promise(r=>finishWrite=r);},'POST');
 recovery.reset();assert.equal(signal.aborted,true);assert.equal(writeSignal.aborted,false);
 assert.equal(await recovery.run(async()=> 'fresh_verified'),'fresh_verified');
 finish('stale_verified');await rejected;finishWrite('write_confirmed');assert.equal(await write,'write_confirmed');
});
test('non-retryable account denials are immediate and remain denials',async()=>{
 let calls=0;await assert.rejects(createReadRecovery().run(async()=>{calls++;throw Error('invalid_session');}),/invalid_session/);assert.equal(calls,1);
});

test('deadline settles even when the underlying operation ignores abort; a new check can run',async(t)=>{
 t.mock.timers.enable({apis:['setTimeout','Date']});
 const recovery=createReadRecovery();let finish;
 const stuck=recovery.run(()=>new Promise(r=>finish=r));const checked=assert.rejects(stuck,/request_timeout/);
 t.mock.timers.tick(20000);await checked;
 assert.equal(await recovery.run(async()=> 'fresh'),'fresh');finish('late');
});
test('reset rejects a stuck GET immediately even if it ignores AbortSignal',async()=>{
 const recovery=createReadRecovery();let finish;const old=recovery.run(()=>new Promise(r=>finish=r));
 const checked=assert.rejects(old,/network_changed/);recovery.reset();await checked;finish('late');
});
