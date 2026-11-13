import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = name => readFileSync(path.join(root, 'observer', name), 'utf8');
const manifest = JSON.parse(read('manifest.json'));
const coreCode = read('core.js');
const contentCode = read('content.js');
const popupCode = read('popup.js');
const sandbox = vm.createContext({});
vm.runInContext(coreCode, sandbox);
const core = sandbox.CELIKOM_AD_OBSERVER_CORE;

test('isolated read-only MV3 laboratory does not alter the stage-0 extension', () => {
  assert.equal(manifest.manifest_version, 3);
  assert.deepEqual(manifest.content_scripts[0].matches, ['https://music.yandex.ru/*']);
  assert.equal(manifest.content_scripts[0].world, 'ISOLATED');
  assert.deepEqual(manifest.content_scripts[0].js, ['core.js', 'content.js']);
  for (const key of ['permissions', 'host_permissions', 'background',
    'declarative_net_request', 'web_accessible_resources']) {
    assert.ok(!Object.hasOwn(manifest, key), key);
  }
  for (const source of [coreCode, contentCode, popupCode]) {
    for (const forbidden of ['document.cookie', 'XMLHttpRequest', 'chrome.storage',
      'chrome.debugger', 'chrome.webRequest', 'chrome.declarativeNetRequest',
      'window.fetch(', 'fetch(', 'window.open(']) {
      assert.equal(source.includes(forbidden), false, forbidden);
    }
  }
  const stage0 = JSON.parse(readFileSync(path.join(root, 'standalone/manifest.json'), 'utf8'));
  assert.equal(stage0.version, '0.0.1');
  assert.ok(!Object.hasOwn(stage0, 'content_scripts'));
  assert.ok(!Object.hasOwn(stage0, 'permissions'));
});

test('strict class markers distinguish a candidate from paywall or unrelated class', () => {
  assert.deepEqual(Array.from(core.classifyClassValue('TopAdvertBanner_root Other')), ['banner']);
  assert.deepEqual(Array.from(core.classifyClassValue('VideoAd_videoBlock_hash')), ['video']);
  assert.deepEqual(Array.from(core.classifyClassValue('AdModal_root AudioAd_root')), ['overlay','audio']);
  assert.deepEqual(Array.from(core.classifyClassValue('PaywallModal_root MyVideoAd_root')), []);
  const el = {
    nodeType: 1,
    getAttribute(key) { assert.equal(key, 'class'); return 'SideAdvertBanner_root'; },
    get textContent() { throw Error('Unexpected page text read'); }
  };
  assert.deepEqual(Array.from(core.classifyElement(el)), ['banner']);
});

test('session outputs only allowlisted labels, finite relative times and bounded history', () => {
  let now = 1000;
  const session = core.createSession(() => now, 2);
  assert.equal(session.recordCandidate('secret-account-id'), false);
  assert.equal(session.recordMedia('audio','secret-media-source'), false);
  session.recordCandidate('banner');
  now = 3000;
  session.recordMedia('audio', 'playing');
  session.recordMedia('audio', 'waiting');
  session.dropRoots(3);
  const snap = session.snapshot();
  assert.equal(snap.ageSeconds, 2);
  assert.equal(snap.recent.length, 2);
  assert.equal(snap.candidates.banner, 1);
  assert.equal(snap.media.audio.playing, 1);
  assert.equal(snap.droppedRoots, 3);
  assert.equal(JSON.stringify(snap).includes('secret'), false);
  const after = session.reset();
  assert.equal(after.candidates.banner, 0);
  assert.equal(after.recent.length, 0);
  assert.equal(after.droppedRoots, 0);
});

test('DOM and media event integration stays passive, and messages require our extension ID', () => {
  let observerCallback, receive;
  const handlers = new Map(), timers = [];
  const el = value => ({
    nodeType: 1, isConnected: true,
    getAttribute: key => key === 'class' ? value : null,
    querySelectorAll: () => []
  });
  const banner = el('TopAdvertBanner_root');
  const paywall = el('PaywallModal_root');
  class HTMLMediaElement {
    constructor(tagName) { this.tagName = tagName; }
  }
  class MutationObserver {
    constructor(callback) { observerCallback = callback; }
    observe() {}
    disconnect() {}
  }
  const env = vm.createContext({
    document: {
      documentElement: el(''),
      querySelectorAll: () => [banner, paywall],
      addEventListener: (event, callback) => handlers.set(event, callback)
    },
    window: {addEventListener() {}},
    chrome: {runtime: {id: 'own-ext', onMessage: {addListener: cb => {receive = cb;}}}},
    MutationObserver, HTMLMediaElement, performance: {now: () => 2000},
    setTimeout: cb => {timers.push(cb); return timers.length;},
    clearTimeout: () => {}
  });
  vm.runInContext(coreCode, env);
  vm.runInContext(contentCode, env);
  const ask = type => {
    let answer;
    receive({type}, {id:'own-ext'}, response => {answer = response;});
    return answer;
  };
  assert.equal(ask('CELIKOM_OBSERVER_GET').candidates.banner, 1);
  assert.equal(ask('CELIKOM_OBSERVER_GET').candidates.overlay, 0);
  const video = el('VideoAd_videoBlock');
  observerCallback([{type:'childList',addedNodes:[video]}]);
  while(timers.length) timers.shift()();
  assert.equal(ask('CELIKOM_OBSERVER_GET').candidates.video, 1);
  handlers.get('playing')({target:new HTMLMediaElement('AUDIO')});
  assert.equal(ask('CELIKOM_OBSERVER_GET').media.audio.playing, 1);
  let foreignReply = false;
  receive({type:'CELIKOM_OBSERVER_GET'}, {id:'another-ext'}, () => {foreignReply = true;});
  assert.equal(foreignReply, false);
  assert.equal(ask('CELIKOM_OBSERVER_RESET').candidates.banner, 0);
  assert.equal(ask('CELIKOM_OBSERVER_GET').media.audio.playing, 0);
});
