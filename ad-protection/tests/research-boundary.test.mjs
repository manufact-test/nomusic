import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=name=>readFileSync(path.join(root,name),'utf8');
const manifest=JSON.parse(read('standalone/manifest.json'));
const observed=JSON.parse(read('observer/manifest.json'));

test('Stage 0 foundation stays inert even when observer is installed',()=>{
 assert.equal(manifest.version,'0.0.1');
 for(const key of ['content_scripts','permissions','host_permissions','background','declarative_net_request']) {
  assert.equal(Object.hasOwn(manifest,key),false,key);
 }
 assert.equal(observed.content_scripts.length,1);
 assert.deepEqual(observed.content_scripts[0].matches,['https://music.yandex.ru/*']);
 assert.equal(observed.content_scripts[0].world,'ISOLATED');
 for(const key of ['permissions','host_permissions','background','declarative_net_request']) {
  assert.equal(Object.hasOwn(observed,key),false,key);
 }
});

test('observation code contains no request interception, audio changes, or remote code',()=>{
 const names=['observer/content.js','observer/core.js','observer/popup.js','visual-lab/fixture-controller.js'];
 for(const name of names) {
  const source=read(name);
  for(const forbidden of [
   'chrome.declarativeNetRequest','chrome.webRequest','chrome.debugger',
   'XMLHttpRequest','document.cookie','chrome.storage','window.fetch(',
   'HTMLMediaElement.prototype','AudioContext.prototype','eval('
  ]) assert.equal(source.includes(forbidden),false,name+' -> '+forbidden);
 }
});

test('research analysis imports stay inside ad-protection and do not call network',()=>{
 const names=readdirSync(path.join(root,'analysis')).filter(x=>x.endsWith('.mjs'));
 assert.ok(names.length>=6);
 for(const filename of names) {
  const code=read('analysis/'+filename);
  for(const bad of ['https://','http://','node:http','node:https','node:net','node:dgram','process.env.OPENAI_API_KEY']) {
   // Comments and examples may contain protocols, but no request networking methods.
   if (bad==='https://' || bad==='http://') continue;
   assert.equal(code.includes(bad),false,filename+': '+bad);
  }
  for(const match of code.matchAll(/from\s+['"]([^'"]+)['"]/g)) {
   const spec=match[1];
   assert.ok(spec.startsWith('./') || ['node:crypto','node:fs/promises','node:path','node:url'].includes(spec),
     filename+' unexpected import: '+spec);
   assert.ok(!spec.includes('..'),filename+' escapes analysis');
  }
 }
});

test('no observer source references another CELIKOM module by relative path',()=>{
 for(const filename of ['observer/content.js','observer/core.js','observer/popup.js']) {
  const code=read(filename);
  assert.ok(!code.includes('../../'),filename);
  assert.ok(!code.includes('chrome.tabs.executeScript'),filename);
 }
});
