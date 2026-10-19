import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const code=fs.readFileSync(path.join(root,'observer/core.js'),'utf8');
const content=fs.readFileSync(path.join(root,'observer/content.js'),'utf8');
const html=fs.readFileSync(path.join(root,'observer/popup.html'),'utf8');
const popup=fs.readFileSync(path.join(root,'observer/popup.js'),'utf8');
const ctx=vm.createContext({performance:{now:()=>1000}});
vm.runInContext(code,ctx);
const core=ctx.CELIKOM_AD_OBSERVER_CORE;

test('manual markers are explicit, finite, bounded, private and resettable',()=>{
  let t=1000;const s=core.createSession(()=>t,80);
  assert.equal(s.recordMarker('custom:SECRET-TOKEN'),false);
  assert.equal(s.recordMarker('ad-heard'),true);
  t=3100;s.recordMarker('normal-music');
  const data=s.snapshot();
  assert.equal(data.markers.length,2);
  assert.equal(data.markers[1].s,2);
  assert.equal(data.recent.at(-1).category,'marker');
  assert.equal(JSON.stringify(data).includes('SECRET-TOKEN'),false);
  for(let i=0;i<40;i++)s.recordMarker('ad-heard');
  assert.equal(s.snapshot().markers.length,24);
  s.reset();
  assert.equal(s.snapshot().markers.length,0);
});

test('marker controls exist and stay in independent observation UI',()=>{
  for(const kind of ['ad-heard','normal-music','video-ad-seen','popup-ad-seen']){
    assert.ok(html.includes('data-marker="'+kind+'"'));
  }
  assert.ok(popup.includes('CELIKOM_OBSERVER_MARK'));
  assert.ok(content.includes("core.MARKER_KINDS.includes(message.kind)"));
  assert.equal(content.includes('chrome.declarativeNetRequest'),false);
  assert.equal(content.includes('document.cookie'),false);
});
