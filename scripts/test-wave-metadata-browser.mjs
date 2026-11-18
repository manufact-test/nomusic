import assert from 'node:assert/strict';
import {createServer} from 'node:http';
import {resolve} from 'node:path';
import {createRequire} from 'node:module';
const {chromium}=createRequire(import.meta.url)('playwright');
const unpacked=resolve(process.env.WAVE_UNPACKED||'extension/dist/unpacked');
const pcm=Buffer.alloc(8000*2*2),wav=Buffer.alloc(44+pcm.length);
wav.write('RIFF');wav.writeUInt32LE(wav.length-8,4);wav.write('WAVEfmt ',8);wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(1,22);wav.writeUInt32LE(8000,24);wav.writeUInt32LE(16000,28);wav.writeUInt16LE(2,32);wav.writeUInt16LE(16,34);wav.write('data',36);wav.writeUInt32LE(pcm.length,40);
const server=createServer((req,res)=>{
  if(req.url.endsWith('.wav')){res.writeHead(200,{'Content-Type':'audio/wav','Content-Length':wav.length});res.end(wav);}
  else {res.writeHead(200,{'Content-Type':'text/html'});res.end('<!doctype html><title>Wave metadata regression fixture</title><audio id="master" preload="auto" src="/tone.wav"></audio>');}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
let browser;
try {
 browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--autoplay-policy=no-user-gesture-required']});
 const page=await browser.newPage();await page.goto('http://127.0.0.1:'+server.address().port);
 await page.waitForFunction(()=>document.querySelector('audio').readyState===4);
 for(const path of ['player/core.js','adapters/yandex-music-adapter.js'])await page.addScriptTag({path:resolve(unpacked,path)});
 const result=await page.evaluate(async()=>{
  const audio=document.querySelector('audio'),session=navigator.mediaSession;
  const data={title:'Wave fixture song',artist:'Fixture artist',album:'Fixture album'};
  session.metadata=new MediaMetadata(data);
  const adapter=globalThis.__CELIKOM_YANDEX_ADAPTER_V1__.createAdapter(globalThis),seen=[];
  adapter.mount({onSnapshot:s=>seen.push(s.track.id),onPlayerEvent(){}});
  adapter.ingestTrackPayload({id:'24680001',title:data.title,artists:[{name:data.artist}],albums:[{title:data.album}],durationMs:2000},'fixture');
  seen.length=0;
  try {
   for(let i=0;i<8;i++){
    session.metadata=null;
    if(session.metadata!==null)throw Error('Native metadata was altered');
    await new Promise(r=>setTimeout(r,9));
    adapter.emitSnapshot('poll',true);audio.dispatchEvent(new Event('timeupdate'));
    if(adapter.getSnapshot().track.id!=='24680001')throw Error('Identity lost during same-song refresh');
    session.metadata=new MediaMetadata(data);
   }
   if(!seen.every(id=>id==='24680001'))throw Error('Transient null reached snapshot subscriber');
   session.metadata=null;audio.src='/next.wav';
   if(adapter.effectiveSessionMetadata()!==null)throw Error('Grace crossed source transition');
   await new Promise(r=>audio.addEventListener('canplay',r,{once:true}));
   session.metadata=new MediaMetadata(data);session.metadata=null;
   await new Promise(r=>setTimeout(r,75));
   if(adapter.getSnapshot().track.id!==null)throw Error('Persistent missing identity kept indefinitely');
   return {pass:true,refreshes:8,nativeMediaMetadata:true,sourceChange:true,persistentClear:true};
  }finally{adapter.unmount();}
 });
 assert.equal(result.pass,true);console.log('BROWSER_WAVE_PASS',JSON.stringify(result));
}finally{await browser?.close();await new Promise(r=>server.close(r));}
