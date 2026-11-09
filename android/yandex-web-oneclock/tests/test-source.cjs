const {test}=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const script=fs.readFileSync(path.join(__dirname,'../app/src/main/assets/celikom-web-source.js'),'utf8');

function env() {
  const sent=[];
  let master;
  const catalog=new Map([['42884423',{albumId:'555',durationMs:232330}]]);
  const track={id:'42884423',ambiguous:false,confidence:150,metadata:{durationMs:232330}};
  const state={track,player:{mediaId:'media-1',currentTime:0,paused:true}};
  class FakeMedia {
    constructor(){
      this.tagName='AUDIO';this.src='https://music.yandex.ru/original.mp3';
      this.paused=true;this.currentTime=0;this.srcObject=null;
      this.played=0;this.loaded=0;this.handlers=new Map();
    }
    play(){this.played++;return Promise.resolve();}
    load(){this.loaded++;}
    addEventListener(type,listener,options={}) {
      const arr=this.handlers.get(type)||[];
      arr.push({listener,once:!!options.once});
      this.handlers.set(type,arr);
    }
    emit(type) {
      const arr=this.handlers.get(type)||[];
      this.handlers.set(type,arr.filter(x=>!x.once));
      for(const h of arr)h.listener({target:this,type});
    }
  }
  master=new FakeMedia();
  const adapter={
    trackCatalog:catalog, getSnapshot(){return state;},
    getMediaElement(id){return id==='media-1'?master:null;},
    mount(sink){this.sink=sink;}
  };
  const root={
    location:{origin:'https://music.yandex.ru'},
    URL,
    HTMLMediaElement:FakeMedia,
    __CELIKOM_YANDEX_ADAPTER_V1__:{createAdapter(){return adapter;}},
    CelikomBridge:{postMessage(x){sent.push(JSON.parse(x));}}
  };
  root.globalThis=root;
  vm.runInNewContext(script,root);
  return {root,master,adapter,state,sent};
}
const ready=(root,album='555')=>root.__CELIKOM_WEB_SOURCE_V1__.ready(
  '42884423',album,232330,
  'https://music.yandex.ru/__celikom_audio/12345678-1234-1234-1234-123456789012-12345678-1234-1234-1234-123456789012/42884423/'+album+'.mp3'
);

test('no second audio player: cached asset uses existing Yandex media element',async()=>{
  const x=env();
  x.root.__CELIKOM_WEB_SOURCE_V1__.enable(true);
  assert.equal(x.sent.some(e=>e.kind==='track'&&e.id==='42884423'),true);
  await x.master.play();
  assert.equal(x.master.src,'https://music.yandex.ru/original.mp3');
  ready(x.root);
  await x.master.play();
  assert.match(x.master.src,/__celikom_audio\/.*\/42884423\/555\.mp3/);
  assert.equal(x.master.loaded,1);
  assert.equal(x.master.played,2);
  assert.equal(x.sent.some(e=>e.kind==='selected'&&e.id==='42884423'),true);
});
test('wrong album is always left on original source',async()=>{
  const x=env();x.root.__CELIKOM_WEB_SOURCE_V1__.enable(true);
  ready(x.root,'666');
  await x.master.play();
  assert.equal(x.master.loaded,0);
});
test('ambiguous ID can never take over source',async()=>{
  const x=env();x.root.__CELIKOM_WEB_SOURCE_V1__.enable(true);ready(x.root);
  x.state.track.ambiguous=true;
  await x.master.play();
  assert.equal(x.master.loaded,0);
});
test('no verified album is not eligible',async()=>{
  const x=env();x.root.__CELIKOM_WEB_SOURCE_V1__.enable(true);ready(x.root);
  x.adapter.trackCatalog.clear();
  await x.master.play();
  assert.equal(x.master.loaded,0);
});
test('paused/resumed midpoint keeps current source',async()=>{
  const x=env();x.root.__CELIKOM_WEB_SOURCE_V1__.enable(true);ready(x.root);
  x.master.currentTime=37;
  await x.master.play();
  assert.equal(x.master.loaded,0);
});
test('disabled mode always retains Yandex original',async()=>{
  const x=env();ready(x.root);
  await x.master.play();
  assert.equal(x.master.loaded,0);
});
test('no Yandex host/invalid cache URL is rejected',async()=>{
  const x=env();x.root.__CELIKOM_WEB_SOURCE_V1__.enable(true);
  x.root.__CELIKOM_WEB_SOURCE_V1__.ready('42884423','555',232330,'https://attacker.invalid/audio');
  await x.master.play();
  assert.equal(x.master.loaded,0);
});

test('failed alternate startup restores ORIGINAL on same audio element',async()=>{
  const x=env();
  x.root.__CELIKOM_WEB_SOURCE_V1__.enable(true);ready(x.root);
  await x.master.play();
  assert.match(x.master.src,/__celikom_audio/);
  x.master.emit('error');
  assert.equal(x.master.src,'https://music.yandex.ru/original.mp3');
  assert.equal(x.master.loaded,2);
  assert.equal(x.master.played,2);
  assert.equal(x.sent.some(e=>e.phase==='original-startup-fallback'),true);
});
test('playing alternate never triggers mid-song original fallback',async()=>{
  const x=env();
  x.root.__CELIKOM_WEB_SOURCE_V1__.enable(true);ready(x.root);
  await x.master.play();
  x.master.emit('playing');
  assert.equal(x.sent.some(e=>e.phase==='alternate-playing'),true);
  x.master.emit('error');
  assert.match(x.master.src,/__celikom_audio/);
  assert.equal(x.master.loaded,1);
});
