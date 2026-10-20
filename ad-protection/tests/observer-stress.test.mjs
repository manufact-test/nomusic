import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const code=(name)=>readFileSync(path.join(root,'observer',name),'utf8');
const events=['play','playing','pause','ended','waiting','stalled','error'];

function setup(){
  let mutation,receiver,now=1000;
  let observed=0,disconnected=0;
  const timers=[];
  const winListeners=new Map();
  const el=(klass='',children=[])=>({
    nodeType:1,isConnected:true,klass,children,
    getAttribute(key){return key==='class'?this.klass:null},
    querySelectorAll(){return this.children}
  });
  const root=el('');
  const contentDocument={
    documentElement:root,querySelectorAll(){return []},
    addEventListener(){}
  };
  const window={addEventListener(name,fn){winListeners.set(name,fn)}};
  class MutationObserver{
    constructor(fn){mutation=fn}
    observe(){observed++}
    disconnect(){disconnected++}
  }
  class HTMLMediaElement{}
  const scope=vm.createContext({
    document:contentDocument,window,MutationObserver,HTMLMediaElement,
    performance:{now:()=>now},chrome:{runtime:{id:'our-extension',
      onMessage:{addListener(fn){receiver=fn}}}},
    setTimeout(fn){timers.push(fn);return timers.length},
    clearTimeout(){}
  });
  vm.runInContext(code('core.js'),scope);
  vm.runInContext(code('content.js'),scope);
  const read=()=>{let result;receiver({type:'CELIKOM_OBSERVER_GET'},{id:'our-extension'},v=>result=v);return result};
  const flush=()=>{let max=100;while(timers.length&&max-->0)timers.shift()();if(max<=0)throw Error('Nonterminating scheduler')};
  return {el,root,read,flush,emit(records){mutation(records)},lifecycle(name){winListeners.get(name)()},get observed(){return observed},get disconnected(){return disconnected}};
}

test('observer caps DOM mutation deliveries and reports skipped roots',()=>{
  const r=setup();
  const many=Array.from({length:5000},()=>({type:'attributes',target:r.el('TopAdvertBanner_root')}));
  r.emit(many);
  r.flush();
  const snap=r.read();
  assert.equal(snap.candidates.banner,160);
  assert.ok(snap.droppedRoots>=5000-1000);
  assert.ok(snap.droppedRoots>0);
});

test('observer bounds large added-node batches and subtree matches',()=>{
  const r=setup();
  const candidates=Array.from({length:400},()=>r.el('SideAdvertBanner_item'));
  const root=r.el('',candidates);
  r.emit([{type:'childList',addedNodes:[root]}]);
  r.flush();
  const snap=r.read();
  assert.equal(snap.candidates.banner,120);
  assert.ok(snap.droppedRoots>=280);
});

test('observer suspends on pagehide and resumes on pageshow',()=>{
  const r=setup();
  r.lifecycle('pagehide');
  r.emit([{type:'attributes',target:r.el('TopAdvertBanner_root')}]);
  r.flush();
  assert.equal(r.read().candidates.banner,0);
  assert.ok(r.disconnected>=1);
  r.lifecycle('pageshow');
  r.emit([{type:'attributes',target:r.el('TopAdvertBanner_root')}]);
  r.flush();
  assert.equal(r.read().candidates.banner,1);
  assert.ok(r.observed>=2);
});

test('20 manual marks is consistent with HAR analyzer window maximum',()=>{
  const ctx=vm.createContext({performance:{now:()=>20000}});
  vm.runInContext(code('core.js'),ctx);
  const core=ctx.CELIKOM_AD_OBSERVER_CORE;
  const s=core.createSession(()=>20000,80);
  for(let i=0;i<300;i++)s.recordMarker('ad-heard');
  assert.equal(s.snapshot().markers.length,20);
});

test('strict exported schema strips unknown URLs and identifiers',()=>{
  const ctx=vm.createContext({});
  vm.runInContext(code('export-core.js'),ctx);
  const norm=ctx.CELIKOM_OBSERVER_EXPORT.normalize;
  const input={
    schema:'celikom-ad-observer-v1',ageSeconds:10,
    candidates:{banner:0,overlay:1,video:0,audio:0,privateUrl:'https://private.example'},
    media:Object.fromEntries(['audio','video'].map(kind=>[kind,Object.fromEntries(events.map(name=>[name,0]))])),
    droppedRoots:0,
    markers:[{s:5,kind:'ad-heard',title:'PRIVATE_SECRET'}],
    recent:[{s:5,category:'marker',kind:'ad-heard',token:'PRIVATE_SECRET'}],
    accountId:'PRIVATE_SECRET'
  };
  const safe=norm(input);
  assert.equal(safe.markers.length,1);
  assert.equal(JSON.stringify(safe).includes('PRIVATE_SECRET'),false);
  assert.equal(JSON.stringify(safe).includes('private.example'),false);
  assert.equal(safe.candidates.overlay,1);
});

test('export fails closed on unknown labels, unexpected counters or oversize history',()=>{
  const ctx=vm.createContext({});
  vm.runInContext(code('export-core.js'),ctx);
  const norm=ctx.CELIKOM_OBSERVER_EXPORT.normalize;
  const good={
    schema:'celikom-ad-observer-v1',ageSeconds:10,
    candidates:{banner:0,overlay:1,video:0,audio:0},
    media:Object.fromEntries(['audio','video'].map(k=>[k,Object.fromEntries(events.map(e=>[e,0]))])),
    droppedRoots:0,markers:[],recent:[]
  };
  assert.throws(()=>norm({...good,markers:[{s:2,kind:'JWT'}]}));
  assert.throws(()=>norm({...good,markers:Array(21).fill({s:2,kind:'ad-heard'})}));
  assert.throws(()=>norm({...good,candidates:{...good.candidates,banner:-5}}));
  assert.throws(()=>norm({...good,recent:[{s:2,category:'unknown',kind:'token'}]}));
  assert.throws(()=>norm({...good,media:{...good.media,audio:{...good.media.audio,play:Infinity}}}));
});

test('popup loads sanitizer before presentation and performs no ad request filtering',()=>{
  const html=code('popup.html');
  const script=code('popup.js');
  const manifest=JSON.parse(code('manifest.json'));
  assert.ok(html.indexOf('export-core.js')<html.indexOf('popup.js'));
  assert.ok(script.includes('normalize(input)'));
  assert.ok(script.includes('normalize(last)'));
  assert.ok(!Object.hasOwn(manifest,'permissions'));
  assert.ok(!Object.hasOwn(manifest,'host_permissions'));
  assert.ok(!Object.hasOwn(manifest,'declarative_net_request'));
});
