import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const script=readFileSync(new URL('playback-surface.js',import.meta.url),'utf8');
const guard=readFileSync(new URL('../../extension/src/player/original-audio-guard.ts',import.meta.url),'utf8');
function harness(){
  let time=1000, timer, sink;
  const events=[], native=[], listeners={};
  let physicalMuted=false,volume=0.7;
  const proto={};
  Object.defineProperties(proto,{muted:{configurable:true,get(){return physicalMuted},set(v){physicalMuted=!!v}},volume:{configurable:true,get(){return volume},set(v){volume=v}}});
  const element=Object.assign(Object.create(proto),{src:'opaque-original',addEventListener(){},removeEventListener(){}});
  const s={track:{id:'144530503',confidence:100,ambiguous:false,metadata:{durationMs:10000}},player:{mediaId:'m1',duration:10,readyState:4,paused:false,seeking:false,ended:false,currentTime:2,playbackRate:1,volume:0.7,muted:false}};
  const adapter={mount(v){sink=v},getSnapshot(){return s},getMediaElement(id){return id==='m1'?element:null}};
  const context={Date:{now:()=>time},document:{hidden:false,addEventListener(n,f){listeners[n]=f}},setInterval(f){timer=f},addEventListener(n,f){listeners[n]=f},CelikomLease:{postMessage(v){native.push(JSON.parse(v))}},__CELIKOM_YANDEX_ADAPTER_V1__:{createAdapter(){return adapter}}};
  context.window=context;context.top=context;context.globalThis=context;
  vm.runInNewContext(guard+'\n'+script,context);
  return {api:context.__CELIKOM_MOBILE__,s,element,native,physical:()=>physicalMuted,advance(n){time+=n;timer()},event(){sink.onPlayerEvent({})},hide(){context.document.hidden=true;listeners.visibilitychange()},events};
}
test('exact binding, guard and latest user volume/mute intent survive release',()=>{
  const h=harness();assert.equal(h.api.engage('wrong','m1','a'),false);
  assert.equal(h.api.engage('144530503','m1','a'),true);assert.equal(h.physical(),true);
  h.element.volume=0.3;h.element.muted=false;
  assert.equal(JSON.parse(h.api.snapshot()).volume,0.3);
  assert.equal(h.api.release('stale'),false);assert.equal(h.physical(),true);
  h.api.release('a');assert.equal(h.physical(),false);assert.equal(h.element.volume,0.3);
  assert.equal(h.native[0].released,'a');
});
test('stalled heartbeat, pause, seek, track change and hidden document restore original',()=>{
  for(const action of [h=>h.advance(1501),h=>{h.s.player.paused=true;h.event()},h=>{h.s.player.seeking=true;h.event()},h=>{h.s.track.id='2';h.event()},h=>h.hide()]){
    const h=harness();h.api.engage('144530503','m1','a');action(h);
    assert.equal(h.physical(),false);assert.equal(h.native.length,1);
  }
});
test('heartbeat refreshes lease, ambiguous/ad or mismatched media never gets muted',()=>{
  const h=harness();h.api.engage('144530503','m1','a');h.advance(1000);h.api.snapshot();h.advance(1000);assert.equal(h.physical(),true);h.api.release();
  h.s.track.ambiguous=true;assert.equal(h.api.engage('144530503','m1','b'),false);
  h.s.track.ambiguous=false;h.s.player.duration=30;assert.equal(h.api.engage('144530503','m1','b'),false);
  h.s.player.duration=10;assert.equal(h.api.engage('144530503','ad','b'),false);
});
