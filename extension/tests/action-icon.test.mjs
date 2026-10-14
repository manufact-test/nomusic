import test from 'node:test';
import assert from 'node:assert/strict';
import {createActionIcon} from '../dist/unpacked/background/action-icon.js';
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function fixture() {
 const icons=[],titles=[],timers=new Set(),events={};
 const api={action:{setIcon:async value=>icons.push(value),setTitle:async value=>titles.push(value)},
  tabs:{onRemoved:{addListener:fn=>events.removed=fn},onUpdated:{addListener:fn=>events.updated=fn}},
  storage:{onChanged:{addListener:fn=>events.storage=fn}}};
 const icon=createActionIcon(api,{schedule:fn=>{timers.add(fn);return fn},cancel:fn=>timers.delete(fn)});
 return {icon,icons,titles,timers,events};
}
test('toolbar reflects connected activity; another tab stays green until all connections stop',async()=>{
 const f=fixture();await tick();assert.match(f.icons.at(-1).path[32],/gray/);
 f.icon.update(1,true);await tick();assert.match(f.icons.at(-1).path[32],/green/);
 assert.match(f.titles.at(-1).title,/включён и подключён/);
 f.icon.update(2,true);f.icon.update(1,false);await tick();assert.match(f.icons.at(-1).path[32],/green/);
 f.events.removed(2);await tick();assert.match(f.icons.at(-1).path[32],/gray/);
});
test('logout, Stop, tab navigation and missing heartbeats restore the gray icon',async()=>{
 const f=fixture();f.icon.update(1,true);await tick();
 f.events.storage({enabled:{newValue:false}},'local');await tick();assert.match(f.icons.at(-1).path[16],/gray/);
 f.icon.update(1,true);f.events.updated(1,{status:'loading'});await tick();assert.match(f.icons.at(-1).path[16],/gray/);
 f.icon.update(1,true);await tick();[...f.timers].forEach(fn=>fn());await tick();assert.match(f.icons.at(-1).path[16],/gray/);
 f.icon.update(1,true);f.icon.clear();await tick();assert.match(f.icons.at(-1).path[16],/gray/);
});
test('repeated healthy heartbeats renew the lease without repainting or flickering',async()=>{
 const f=fixture();f.icon.update(1,true);await tick();const paints=f.icons.length;
 const old=[...f.timers][0];f.icon.update(1,true);await tick();
 assert.equal(f.icons.length,paints);assert.equal(f.timers.size,1);assert.equal(f.timers.has(old),false);
 f.icon.clear();
});

test('nested MV3 worker loads actual packaged gray and green PNGs from the extension root',async()=>{
 const {readFile}=await import('node:fs/promises');
 const {inflateSync}=await import('node:zlib');
 const loaded=[];
 const api={action:{setTitle:async()=>{},setIcon:async({path})=>{
  for(const [size,raw] of Object.entries(path)){
   const url=new URL(raw,'chrome-extension://fixture/background/service-worker.js');
   const bytes=await readFile(new URL('.'+url.pathname,new URL('../dist/unpacked/',import.meta.url)));
   assert.equal(bytes.toString('hex',0,8),'89504e470d0a1a0a');
   assert.equal(bytes.readUInt32BE(16),Number(size));
   const chunks=[];
   for(let at=8;at<bytes.length;){const length=bytes.readUInt32BE(at),tag=bytes.toString('ascii',at+4,at+8);if(tag==='IDAT')chunks.push(bytes.subarray(at+8,at+8+length));at+=12+length;}
   const pixels=inflateSync(Buffer.concat(chunks)),width=Number(size),x=Math.floor(width/2),y=x;
   const offset=y*(width*4+1)+1+x*4;
   const rgb=[...pixels.subarray(offset,offset+3)];
   assert.deepEqual(rgb,raw.includes('green')?[102,224,191]:[133,139,142]);
  }
  loaded.push(path);
 }},tabs:{},storage:{}};
 const icon=createActionIcon(api,{schedule:()=>0,cancel:()=>{}});
 // Real file loading crosses several event-loop ticks.
 for(let i=0;i<100&&loaded.length<1;i++)await new Promise(resolve=>setTimeout(resolve,2));
 assert.equal(loaded.length,1);
 icon.update(1,true);
 for(let i=0;i<100&&loaded.length<2;i++)await new Promise(resolve=>setTimeout(resolve,2));
 assert.equal(loaded.length,2);assert.match(loaded[1][32],/^\/assets\/icons\/green/);
 icon.clear();
});

test('failed setIcon retries on the next connected heartbeat rather than caching success',async()=>{
 let fail=false,attempts=0;const loaded=[];
 const api={action:{setTitle:async()=>{},setIcon:async({path})=>{
  attempts++;if(fail){fail=false;throw new Error('temporary icon load failure')};loaded.push(path);
 }},tabs:{},storage:{}};
 const icon=createActionIcon(api,{schedule:()=>0,cancel:()=>{}});await tick();
 fail=true;icon.update(1,true);await tick();assert.match(loaded.at(-1)[32],/gray/);
 const before=attempts;icon.update(1,true);await tick();
 assert.equal(attempts,before+1);assert.match(loaded.at(-1)[32],/green/);
 icon.clear();
});

test('selected failed tab overrides a different healthy tab and recovery restores green',async()=>{
 const f=fixture();f.icon.update(1,true);f.icon.update(2,true);await tick();
 f.icon.showFor(1,false);await tick();assert.match(f.icons.at(-1).path[32],/gray/);
 f.icon.update(2,true);await tick();assert.match(f.icons.at(-1).path[32],/gray/);
 f.icon.update(1,true);await tick();assert.match(f.icons.at(-1).path[32],/green/);
 f.icon.showFor(null,false);await tick();assert.match(f.icons.at(-1).path[32],/gray/);
});
