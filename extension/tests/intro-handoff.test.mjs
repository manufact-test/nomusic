import assert from 'node:assert/strict';
import test from 'node:test';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../dist/unpacked/player/main-world-entry.js',import.meta.url),'utf8');
function fixture(){
 let time=10000,seq=0,sink,plays=0;const timers=new Map(),listeners=new Map(),posts=[],documentListeners=new Map();let watchdog;
 const media={src:'https://stream.example/one',paused:true,muted:false};
 const snapshot={track:{id:'2',confidence:240,ambiguous:false,metadata:{durationMs:200000}},player:{mediaId:'m',paused:true,seeking:false,ended:false,readyState:4,currentTime:.1,duration:200}};
 const adapter={mounted:false,service:'yandex',mount(s){sink=s;this.mounted=true},unmount(){this.mounted=false},getSnapshot(reason){return structuredClone({...snapshot,reason,triggerMediaId:'m'})},getMediaElement(){return media}};
 class Guard{
  constructor(){this.current=null;}
  engage(element,mediaId,token){this.current={element,mediaId,token};element.muted=true;}
  transfer(element,mediaId,old,token){assert.equal(this.current.token,old);this.current.token=token;}
  state(){return {active:!!this.current,mediaId:this.current?.mediaId};}
  release(){if(this.current)this.current.element.muted=false;this.current=null;return {released:true};}
 }
 class Clock extends Date{static now(){return time}}
 const document={hidden:false,querySelectorAll:()=>[],addEventListener:(name,fn)=>documentListeners.set(name,fn),removeEventListener:name=>documentListeners.delete(name)};
 const ctx=vm.createContext({Date:Clock,console,document,
  __CELIKOM_PLAYER_CORE_V1__:{CHANNEL:'test',PROTOCOL_VERSION:1,VERSION:'test'},
  __CELIKOM_YANDEX_ADAPTER_V1__:{createAdapter:()=>adapter},__CELIKOM_ORIGINAL_GUARD_V1__:{OriginalAudioGuard:Guard},
  setTimeout:(fn,ms)=>{const id=++seq;timers.set(id,{at:time+ms,fn});return id},clearTimeout:id=>timers.delete(id),setInterval:fn=>{watchdog=fn;return ++seq},clearInterval(){},
  addEventListener:(type,fn)=>listeners.set(type,fn),removeEventListener:type=>listeners.delete(type),postMessage:m=>posts.push(m)});
 vm.runInContext(source,ctx);const root=vm.runInContext('globalThis',ctx);
 const send=(type,payload={})=>listeners.get('message')({source:root,data:{channel:'test',protocolVersion:1,direction:'to-main',sessionId:'test-session',type,payload,requestId:'request'}});
 send('INIT');send('POLICY_UPDATE',{revision:1,enabled:true,holdIntro:true});
 const hold=()=>{sink.onSnapshot(adapter.getSnapshot('before-method:play'));return sink.holdIntroPlay(media,()=>{plays++;media.paused=false;snapshot.player.paused=false;return Promise.resolve()})};
 const tick=ms=>{const end=time+ms;for(;;){const next=[...timers].filter(([,t])=>t.at<=end).sort((a,b)=>a[1].at-b[1].at)[0];if(!next)break;time=next[1].at;timers.delete(next[0]);next[1].fn()}time=end};
 const request=(preparing=false)=>send('REQUEST',{type:'GUARD_ENGAGE',payload:{token:'test-session:1',trackId:'2',mediaId:'m',preparing}});
 return {document,visibility:()=>documentListeners.get("visibilitychange")?.(),watchdog:()=>watchdog(),media,snapshot,hold,tick,request,send,posts,get plays(){return plays},get sink(){return sink}};
}
test('guarded decoder readiness resumes native intro within the unchanged 400ms deadline',async()=>{
 const f=fixture(),pending=f.hold();assert(pending);assert.equal(f.media.muted,true);
 f.tick(100);assert.equal(f.plays,0);assert.equal(f.media.paused,true);assert.equal(f.media.muted,true);
 f.request(true);f.tick(100);assert.equal(f.plays,0,'preparation reservation cannot shorten or restart the intro deadline');
 f.request();await pending;assert.equal(f.plays,1);assert.equal(f.media.muted,true);
 f.tick(1600);assert.equal(f.plays,1);
});
test('unavailable replacement fails open at one bounded deadline even under repeated snapshots',async()=>{
 const f=fixture(),pending=f.hold();
 for(let i=0;i<3;i++){f.tick(100);f.sink.onSnapshot({...structuredClone(f.snapshot),reason:'poll'});}
 assert.equal(f.plays,0);f.tick(100);await pending;assert.equal(f.plays,1);assert.equal(f.media.muted,false);
 f.tick(10000);assert.equal(f.plays,1);
});
test('user pause and changed source cancel a pending native intro instead of replaying old audio',async()=>{
 for(const reason of ['pause','source']){
  const f=fixture(),pending=f.hold();const rejected=assert.rejects(pending,{name:'AbortError'});
  f.tick(100);
  if(reason==='pause')f.sink.beforeNativeMethod('pause',f.media);
  else{f.media.src='https://stream.example/two';f.snapshot.track.id='3';f.sink.onSnapshot({...structuredClone(f.snapshot),reason:'loadstart'});}
  await rejected;f.tick(3000);assert.equal(f.plays,0);
 }
});
test('negative or bypass policy never admits an intro hold; mid-song play is never delayed',()=>{
 for(const policy of [{bypassTrackId:'2'},{negative:{trackId:'2',until:20000}},{blockedTrackId:'2'}]){
  const f=fixture();f.send('POLICY_UPDATE',{revision:2,enabled:true,holdIntro:true,...policy});assert.equal(f.hold(),null);assert.equal(f.media.muted,false);
 }
 const f=fixture();f.snapshot.player.currentTime=40;assert.equal(f.hold(),null);
});


test('mid-song resume without a prepared replacement never mutes native audio for an intro admission',()=>{
 const f=fixture();f.snapshot.player.currentTime=2.437;
 assert.equal(f.hold(),null);assert.equal(f.media.muted,false);
});


test('MAIN keeps its hidden lease while a returning visible tab verifies the worker, but repeated visible notifications cannot extend it',async()=>{
 const f=fixture(),pending=f.hold();f.request();await pending;
 f.document.hidden=true;f.visibility();f.tick(60000);f.watchdog();assert.equal(f.media.muted,true);
 f.document.hidden=false;f.visibility();f.watchdog();assert.equal(f.media.muted,true,'do not retroactively apply 12s visible timeout to a hidden interval');
 f.tick(11000);f.visibility();f.tick(1001);f.watchdog();assert.equal(f.media.muted,false,'no verified reply: bounded foreground grace must expire');
});
test('MAIN visibility grace cannot exceed the existing hidden heartbeat deadline',async()=>{
 const f=fixture(),pending=f.hold();f.request();await pending;
 f.document.hidden=true;f.visibility();f.tick(119000);f.document.hidden=false;f.visibility();f.watchdog();assert.equal(f.media.muted,true);
 f.tick(1001);f.watchdog();assert.equal(f.media.muted,false,'a return at the hidden deadline cannot grant another twelve seconds');
});
test('a fresh verified heartbeat after returning resumes the original short MAIN deadline',async()=>{
 const f=fixture(),pending=f.hold();f.request();await pending;
 f.document.hidden=true;f.visibility();f.tick(60000);f.document.hidden=false;f.visibility();f.send('HEARTBEAT');
 f.tick(12001);f.watchdog();assert.equal(f.media.muted,false,'the dead extension still fails open after a fresh heartbeat expires');
});

for(const delay of [450,650,850])test('confirmed asset ready at '+delay+'ms does not briefly expose original at 400ms',async()=>{
 const f=fixture(),pending=f.hold();f.tick(150);f.request(true);f.tick(delay-150);
 assert.equal(f.plays,0,'native clock must remain paused while the confirmed decoder loads');assert.equal(f.media.muted,true);
 f.request();await pending;assert.equal(f.plays,1);assert.equal(f.media.muted,true,'handoff must never release the original mute');
 assert.equal(f.posts.some(m=>m.type==='GUARD_RELEASED'),false);
});
test('confirmed but hanging decoder cannot exceed the original handoff deadline or renew it with repeated requests',async()=>{
 const f=fixture(),pending=f.hold();f.tick(150);f.request(true);f.tick(300);assert.equal(f.plays,0);
 // Generic snapshots and another preparing request do not extend the deadline.
 f.request(true);f.sink.onSnapshot({...structuredClone(f.snapshot),reason:'poll'});f.tick(549);assert.equal(f.plays,0);
 f.tick(1);await pending;assert.equal(f.plays,1);assert.equal(f.media.muted,false);
});
test('pause or source change during confirmed intro wait cancels the old native start',async()=>{
 for(const kind of ['pause','source']){
  const f=fixture(),pending=f.hold(),rejected=assert.rejects(pending,{name:'AbortError'});f.tick(100);f.request(true);f.tick(500);
  if(kind==='pause')f.sink.beforeNativeMethod('pause',f.media);
  else{f.media.src='https://stream.example/new';f.snapshot.track.id='3';f.sink.onSnapshot({...structuredClone(f.snapshot),reason:'loadstart'});}
  await rejected;f.tick(2000);assert.equal(f.plays,0);
 }
});
test('preparation reservation preceding native play keeps its original deadline',async()=>{
 const f=fixture();f.sink.onSnapshot({...structuredClone(f.snapshot),reason:'before-method:play',triggerMediaId:'m'});
 f.tick(100);f.request(true);f.tick(50);const pending=f.hold();assert(pending);
 f.tick(500);assert.equal(f.plays,0);f.request();await pending;assert.equal(f.plays,1);assert.equal(f.media.muted,true);
});
