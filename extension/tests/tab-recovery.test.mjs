import assert from 'node:assert/strict';
import test from 'node:test';
import {registerTabRecovery} from '../dist/unpacked/background/tab-recovery.js';
function fixture() {
 const listeners={},calls=[],forgot=[];
 let enabled=true;
 const tabs=new Map([[1,{id:1,url:'https://music.yandex.ru/',status:'complete'}]]);
 const api={tabs:{get:async id=>{if(!tabs.has(id))throw Error('closed');return tabs.get(id)}}};
 for(const event of ['onCreated','onUpdated','onActivated','onRemoved','onReplaced']) api.tabs[event]={addListener:fn=>listeners[event]=fn};
 registerTabRecovery(api,{ensure:async id=>calls.push(id),forget:id=>forgot.push(id)},async()=>enabled);
 return {tabs,calls,forgot,setEnabled:v=>enabled=v,emit:async(name,...args)=>{listeners[name](...args);await new Promise(resolve=>setImmediate(resolve))}};
}
test('new, background, restored and activated Yandex tabs reconnect without popup or Start',async()=>{
 const f=fixture();await f.emit('onCreated',f.tabs.get(1));
 await f.emit('onUpdated',1,{status:'complete'},f.tabs.get(1));
 await f.emit('onUpdated',1,{discarded:false},f.tabs.get(1));
 await f.emit('onActivated',{tabId:1});
 assert.deepEqual(f.calls,[1,1,1,1]);
 await f.emit('onRemoved',1);assert.deepEqual(f.forgot,[1]);
 f.tabs.set(2,{id:2,url:'https://music.yandex.ru/',status:'complete'});
 await f.emit('onReplaced',2,1);assert.equal(f.calls.at(-1),2);
});
test('Stop, unsupported pages, loading, discarded and closed tabs never auto-start',async()=>{
 const f=fixture();f.setEnabled(false);await f.emit('onCreated',f.tabs.get(1));await f.emit('onActivated',{tabId:1});
 f.setEnabled(true);
 for(const tab of [{url:'https://example.org/'},{url:'https://music.yandex.ru/',discarded:true},{url:'https://music.yandex.ru/',status:'loading'}]) {
  f.tabs.set(1,{id:1,...tab});await f.emit('onUpdated',1,{status:'complete'},tab);
 }
 await f.emit('onActivated',{tabId:999});assert.deepEqual(f.calls,[]);
});
test('navigation clears previous page failure, ordinary metadata updates do not probe',async()=>{
 const f=fixture();await f.emit('onUpdated',1,{status:'loading'},f.tabs.get(1));
 await f.emit('onUpdated',1,{url:'https://music.yandex.ru/album/1'},f.tabs.get(1));
 await f.emit('onUpdated',1,{title:'Song'},f.tabs.get(1));
 assert.deepEqual(f.forgot,[1,1]);assert.deepEqual(f.calls,[]);
 await f.emit('onUpdated',1,{status:'complete'},f.tabs.get(1));assert.deepEqual(f.calls,[1]);
});
test('Stop during tab lookup wins over automatic recovery',async()=>{
 const listeners={};let finish,enabled=true,calls=0;
 const api={tabs:{get:()=>new Promise(resolve=>finish=resolve),onActivated:{addListener:fn=>listeners.activate=fn}}};
 registerTabRecovery(api,{ensure:async()=>calls++},async()=>enabled);
 listeners.activate({tabId:1});await new Promise(resolve=>setImmediate(resolve));enabled=false;
 finish({id:1,url:'https://music.yandex.ru/'});await new Promise(resolve=>setImmediate(resolve));assert.equal(calls,0);
});
