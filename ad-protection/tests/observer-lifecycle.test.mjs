import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const core=readFileSync(path.join(root,'observer/core.js'),'utf8');
const content=readFileSync(path.join(root,'observer/content.js'),'utf8');
const popup=readFileSync(path.join(root,'observer/popup.js'),'utf8');
const html=readFileSync(path.join(root,'observer/popup.html'),'utf8');

function rig(){
  let callback,receive;
  let time=1000;
  const pending=[];
  const nodes=[];
  const listeners=new Map();
  const element=(klass)=>({
    nodeType:1,isConnected:true,klass,
    getAttribute(name){return name==='class'?this.klass:null;},
    querySelectorAll(){return []}
  });
  const root=element('');
  const document={
    documentElement:root,
    querySelectorAll(){return nodes;},
    addEventListener(name,fn){listeners.set(name,fn)}
  };
  class MutationObserver{
    constructor(fn){callback=fn}
    observe(){} disconnect(){}
  }
  class HTMLMediaElement{}
  const runtime={id:'internal-observer',onMessage:{addListener(fn){receive=fn}}};
  const scope=vm.createContext({
    document,performance:{now:()=>time},
    window:{addEventListener(){}},
    chrome:{runtime},MutationObserver,HTMLMediaElement,
    setTimeout(fn){pending.push(fn);return pending.length},
    clearTimeout(){}
  });
  vm.runInContext(core,scope);
  vm.runInContext(content,scope);
  function flush(){while(pending.length)pending.shift()()}
  function read(type='CELIKOM_OBSERVER_GET',sender={id:'internal-observer'}){
    let result;
    receive({type},sender,value=>{result=value});
    return result;
  }
  return {element,nodes,root,read,flush,mutate(node,kind='attributes'){
    callback([{type:kind,target:node,addedNodes:kind==='childList'?[node]:[]}]);
  }};
}

test('class removal and reappearance on same DOM element count two distinct appearances',()=>{
  const r=rig();
  const node=r.element('TopAdvertBanner_root');
  r.nodes.push(node);
  r.mutate(node);r.flush();
  assert.equal(r.read().candidates.banner,1);
  r.mutate(node);r.flush();
  assert.equal(r.read().candidates.banner,1);
  node.klass='OrdinaryContent';
  r.mutate(node);r.flush();
  node.klass='TopAdvertBanner_again';
  r.mutate(node);r.flush();
  assert.equal(r.read().candidates.banner,2);
});

test('classification does not hide service paywall or alter DOM',()=>{
  const r=rig();
  const paywall=r.element('PaywallModal_root');
  r.nodes.push(paywall);
  r.mutate(paywall);r.flush();
  assert.equal(r.read().candidates.banner,0);
  assert.equal(paywall.klass,'PaywallModal_root');
});

test('foreign sender or malformed sender cannot extract report',()=>{
  const r=rig();
  assert.equal(r.read('CELIKOM_OBSERVER_GET',{}),undefined);
  assert.equal(r.read('CELIKOM_OBSERVER_GET',null),undefined);
  assert.equal(r.read('CELIKOM_OBSERVER_GET',{id:'other-extension'}),undefined);
});

test('download UI is available but no broad permissions or interception is introduced',()=>{
  const manifest=JSON.parse(readFileSync(path.join(root,'observer/manifest.json'),'utf8'));
  assert.ok(html.includes('id="download"'));
  assert.ok(popup.includes('celikom-observation.json'));
  assert.ok(popup.includes('URL.revokeObjectURL'));
  assert.equal(manifest.manifest_version,3);
  assert.ok(!Object.hasOwn(manifest,'permissions'));
  assert.ok(!Object.hasOwn(manifest,'host_permissions'));
  assert.ok(!Object.hasOwn(manifest,'background'));
  for(const needle of ['declarativeNetRequest','chrome.webRequest','XMLHttpRequest','document.cookie']){
    assert.equal(content.includes(needle),false,needle);
  }
});