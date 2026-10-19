import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const script = readFileSync(path.join(root, 'visual-lab/fixture-controller.js'), 'utf8');
let observerCallback;
class MutationObserver {
  constructor(fn) { observerCallback = fn; }
  observe() {} disconnect() {}
}
const scope = vm.createContext({MutationObserver});
vm.runInContext(script, scope);
const {createController, matchesBanner} = scope.CELIKOM_VISUAL_FIXTURE;

function element(name = '', children = []) {
  const state = new Map();
  const node = {
    nodeType:1,
    klass: name,
    children,
    protected:false,
    getAttribute(key) { if(key==='class') return this.klass; if(key==='data-celikom-fixture') return this.fixture ? '1' : null; return null; },
    closest() { return this.protected ? this : null; },
    querySelector() { return this.containsProtected ? {} : null; },
    querySelectorAll() { return this.children.filter(x => x.klass.includes('AdvertBanner_')); },
    style: {
      setProperty(key,value,priority='') {state.set(key,{value,priority});},
      getPropertyValue(key) {return state.get(key)?.value ?? '';},
      getPropertyPriority(key) {return state.get(key)?.priority ?? '';},
      removeProperty(key) {state.delete(key);}
    }
  };
  return node;
}

test('only explicit synthetic fixture can create DOM suppression',()=>{
  assert.throws(()=>createController(element('TopAdvertBanner_root')));
  assert.equal(matchesBanner(element('TopAdvertBanner_root')),true);
  assert.equal(matchesBanner(element('MyTopAdvertBanner_root')),false);
  assert.equal(matchesBanner(element('PaywallModal_root')),false);
});

test('toggle hides banners reversibly while leaving media and service UI intact',()=>{
  const ad=element('TopAdvertBanner_root');
  const side=element('SideAdvertBanner_root');
  side.style.setProperty('display','inline-block','important');
  const protectedAd=element('TopAdvertBanner_root'); protectedAd.protected=true;
  const childProtected=element('TopAdvertBanner_root'); childProtected.containsProtected=true;
  const paywall=element('PaywallModal_root');
  const fixture=element('',[ad,side,protectedAd,childProtected,paywall]);fixture.fixture=true;
  const c=createController(fixture,MutationObserver);
  assert.equal(c.snapshot().hiddenBannerCandidates,0);
  c.enable();
  assert.equal(c.snapshot().hiddenBannerCandidates,2);
  assert.equal(ad.style.getPropertyValue('display'),'none');
  assert.equal(side.style.getPropertyPriority('display'),'important');
  assert.equal(protectedAd.style.getPropertyValue('display'),'');
  assert.equal(childProtected.style.getPropertyValue('display'),'');
  assert.equal(paywall.style.getPropertyValue('display'),'');
  c.disable();
  assert.equal(ad.style.getPropertyValue('display'),'');
  assert.equal(side.style.getPropertyValue('display'),'inline-block');
  assert.equal(side.style.getPropertyPriority('display'),'important');
  assert.equal(c.snapshot().hiddenBannerCandidates,0);
  c.dispose();
  assert.throws(()=>c.enable());
});

test('dynamic element and class removal trigger reversible classification',()=>{
  const root=element();root.fixture=true;
  const ad=element('TopAdvertBanner_dynamic');
  const c=createController(root,MutationObserver);
  c.enable();
  observerCallback([{type:'childList',addedNodes:[ad]}]);
  assert.equal(ad.style.getPropertyValue('display'),'none');
  ad.klass='OrdinaryContent';
  observerCallback([{type:'attributes',target:ad}]);
  assert.equal(ad.style.getPropertyValue('display'),'');
  c.dispose();
});
