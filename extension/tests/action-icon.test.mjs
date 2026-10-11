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
