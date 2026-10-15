import {access,readFile,writeFile,mkdtemp,rm,mkdir} from 'node:fs/promises';
import {spawn,spawnSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {stripTypeScriptTypes} from 'node:module';
let binary;
for(const p of ['/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium']){try{await access(p);binary=p;break}catch{}}
if(!binary){if(process.env.REQUIRE_BROWSER_AUDIO==='1')throw Error('Chromium required');console.log('Audio gain native check deferred to CI');process.exit(0);}
const directory=await mkdtemp(join(tmpdir(),'celikom-gain-'));
try{
 const ui=await readFile('server/src/Admin/audio-gain.js','utf8');
 const player=await readFile('extension/dist/unpacked/player/replacement-player.js','utf8');
 const core=await readFile('extension/dist/unpacked/player/core.js','utf8'),adapterCode=await readFile('extension/dist/unpacked/adapters/yandex-music-adapter.js','utf8');
 const guardCode=await readFile('extension/dist/unpacked/player/original-audio-guard.js','utf8'),mainCode=await readFile('extension/dist/unpacked/player/main-world-entry.js','utf8');
 const dsp=ui.slice(0,ui.indexOf('\n(()=>'));
 const deployed=player.slice(player.indexOf('function createGainChain'),player.indexOf('class ReplacementPlayer'));
 const canonical=s=>stripTypeScriptTypes(s,{mode:'transform'}).trim();
 if(canonical(deployed)!==canonical(dsp))throw Error('Admin/player DSP mismatch');
 const m4aFile=join(directory,'synthetic.m4a');
 const encoded=spawnSync('ffmpeg',['-v','error','-f','lavfi','-i','sine=frequency=660:duration=3','-c:a','aac','-b:a','128k',m4aFile]);
 if(encoded.status!==0)throw Error('Synthetic M4A encoder required');
 const m4a=await readFile(m4aFile);
 const mp3File=join(directory,'synthetic.mp3');
 const encodedMp3=spawnSync('ffmpeg',['-v','error','-f','lavfi','-i','sine=frequency=440:duration=3','-c:a','libmp3lame','-b:a','128k',mp3File]);
 if(encodedMp3.status!==0)throw Error('Synthetic MP3 encoder required');
 const mp3=await readFile(mp3File);
 const bytes=await readFile('extension/assets/test-audio.mp3');
 const css=await readFile('server/src/Admin/admin-style.css','utf8');
 const html=`<!doctype html><html><head><style>${css}</style></head><body><main><div class="player-wrap" id="audio-version-5"><audio data-gain-audio data-gain-db="0" controls></audio></div><details class="detail-toggle" data-gain-toggle><summary>Громкость версии</summary><form class="audio-gain-form" method="post" action="/admin/audio-gain" data-audio-gain data-audio-id="audio-version-5"><input type="hidden" name="csrf" value="fixture"><input type="hidden" name="gain_before" value="0"><label>Громкость версии <output data-gain-value>0 дБ</output></label><div class="audio-gain-controls"><span>Тише</span><input name="gain_db" type="range" min="-12" max="12" step="0.5" value="0"><span>Громче</span></div><button type="button" data-gain-reset>Исходная громкость</button><button type="submit">Сохранить громкость</button><p data-gain-note>Прослушайте и сохраните</p><p data-gain-save-status hidden></p></form></details><details><summary>Технические сведения</summary></details></main><script>${ui}\n${core}\n${adapterCode}\n${guardCode}\n${mainCode}\n${player}\n(async()=>{try{
 const check=(v,m)=>{if(!v)throw Error(m)};
 const render=async(db,amplitude)=>{document.body.dataset.gainStep='offline '+db;
  const context=new OfflineAudioContext(1,44100,44100),source=context.createBufferSource(),buffer=context.createBuffer(1,44100,44100),signal=buffer.getChannelData(0);
  for(let i=0;i<signal.length;i++)signal[i]=amplitude*Math.sin(2*Math.PI*440*i/44100);source.buffer=buffer;
  const facade={currentTime:0,destination:context.destination,createMediaElementSource:()=>source,createGain:()=>context.createGain(),createDynamicsCompressor:()=>context.createDynamicsCompressor(),createWaveShaper:()=>context.createWaveShaper()};
  createGainChain(facade,null,db);source.start();const audio=(await context.startRendering()).getChannelData(0);const kept=audio.slice(10000);return {rms:Math.sqrt(kept.reduce((n,x)=>n+x*x,0)/kept.length),peak:Math.max(...kept.map(Math.abs))};
 };
 const base=await render(0,0.03),boost=await render(6,0.03),quiet=await render(-6,0.03),loud=await render(12,0.95);
 check(boost.rms/base.rms>1.9&&boost.rms/base.rms<2.1,'quiet signal boost '+JSON.stringify({base,boost,quiet,loud,ratio:boost.rms/base.rms}));check(quiet.rms/base.rms>0.49&&quiet.rms/base.rms<0.52,'attenuation');check(loud.peak<=0.9801,'peak ceiling');
 document.body.dataset.gainStep='actual media';
 const {ReplacementPlayer}=globalThis.__CELIKOM_REPLACEMENT_PLAYER_V1__,fatal=[];
 const p=new ReplacementPlayer(window,r=>fatal.push(r));await p.prepare({url:'data:audio/mpeg;base64,${bytes.toString('base64')}',demoLoop:true,gainDb:6});
 check(p.gainContext.state==='running','real media gain context');p.applyState({volume:.4,muted:false,playbackRate:1});p.play();await new Promise(r=>setTimeout(r,150));check(!p.audio.paused&&p.audio.volume===.4,'real amplified media playback and volume sync');
 p.applyState({volume:.3,muted:true,playbackRate:1});check(p.audio.muted,'mute sync');const context=p.gainContext;p.destroy();await new Promise(r=>setTimeout(r,50));check(context.state==='closed'&&!p.audio.isConnected,'gain cleanup');check(fatal.length===0,'no media errors');
 document.body.dataset.gainStep='M4A direct playback';
 const m4aBytes=Uint8Array.from(atob('${m4a.toString('base64')}'),c=>c.charCodeAt(0));
 let m4aRequests=0;
 const m4aEnvironment={document,URL,AbortController,AudioContext,setTimeout:window.setTimeout.bind(window),clearTimeout:window.clearTimeout.bind(window),fetch:async(url,options)=>{
  m4aRequests++;const range=/^bytes=(\\d+)-(\\d+)$/.exec(options.headers.Range);check(Boolean(range),'M4A signed Range');
  const from=Number(range[1]),last=Math.min(Number(range[2]),m4aBytes.length-1);
  return new Response(m4aBytes.slice(from,last+1),{status:206,headers:{'Content-Type':'audio/mp4','Content-Range':'bytes '+from+'-'+last+'/'+m4aBytes.length}});
 }};
 const direct=new ReplacementPlayer(m4aEnvironment,r=>fatal.push(r));
 await direct.prepare({url:'https://private.example/audio',mimeType:'audio/mp4',durationMs:3023,gainDb:6});
 check(!direct.mediaSource&&direct.audio.src.startsWith('blob:'),'M4A original container through native decoder');
 check(Math.abs(direct.audio.duration-3)<.1&&m4aRequests>0,'M4A duration');
 direct.applyState({volume:1,muted:false,playbackRate:1});direct.play();await new Promise(r=>setTimeout(r,100));
 check(!direct.audio.paused&&direct.audio.currentTime>0,'M4A native plays');direct.audio.currentTime=1;
 await new Promise(r=>direct.audio.addEventListener('seeked',r,{once:true}));check(Math.abs(direct.audio.currentTime-1)<.3,'M4A native seeks');direct.pause();check(direct.audio.paused,'M4A pauses');direct.destroy();check(direct.audio.muted&&!direct.audio.getAttribute('src'),'M4A destroy releases local source');

 document.body.dataset.gainStep='actual MP3 MSE ranges';
 const mp3Bytes=Uint8Array.from(atob('${mp3.toString('base64')}'),c=>c.charCodeAt(0));
 const streaming=new ReplacementPlayer({...m4aEnvironment,MediaSource,fetch:async(url,options)=>{
  const match=/^bytes=(\\d+)-(\\d+)$/.exec(options.headers.Range);check(Boolean(match),'MP3 range');
  const from=Number(match[1]),last=Math.min(Number(match[2]),mp3Bytes.length-1);
  return new Response(mp3Bytes.slice(from,last+1),{status:206,headers:{'content-type':'audio/mpeg','content-range':'bytes '+from+'-'+last+'/'+mp3Bytes.length}});
 }},r=>fatal.push(r));
 await streaming.prepare({url:'https://private.example/audio',mimeType:'audio/mpeg',durationMs:3030});
 check(streaming.audio.readyState>=2&&streaming.mediaSource,'actual MP3 MSE decoder loads');
 streaming.applyState({volume:1,muted:false,playbackRate:1});streaming.play();await new Promise(r=>setTimeout(r,100));
 check(streaming.audio.currentTime>0&&!streaming.audio.paused,'actual MP3 MSE plays');streaming.destroy();

 document.body.dataset.gainStep='native stream transition';
 const blob=await fetch('data:audio/mpeg;base64,${bytes.toString('base64')}').then(r=>r.blob());
 const master=document.createElement('audio');master.hidden=true;master.muted=true;document.body.append(master);
 const urls=[URL.createObjectURL(blob),URL.createObjectURL(blob)];
 const ready=()=>new Promise((resolve,reject)=>{master.addEventListener('loadeddata',resolve,{once:true});master.addEventListener('error',reject,{once:true});});
 let loaded=ready();master.src=urls[0];master.load();await loaded;
 navigator.mediaSession.metadata=new MediaMetadata({title:'Fixture A',artist:'CELIKOM'});
 const adapter=__CELIKOM_YANDEX_ADAPTER_V1__.createAdapter(window);let previous=null,latest;
 for(const [id,title] of [['11','Fixture A'],['12','Fixture B']])adapter.ingestTrackPayload({id,title,artists:[{name:'CELIKOM'}],durationMs:Math.round(master.duration*1000)},'native-fixture');
 const observe=s=>{latest=s;if(previous&&s.track.id!=='11')previous.destroy();};
 adapter.mount({onSnapshot:observe,onPlayerEvent:e=>observe(e.snapshot)});
 try{
  check(latest.track.id==='11','native initial identity');
  previous=new ReplacementPlayer(window,r=>fatal.push(r));await previous.prepare({url:urls[0],demoLoop:true});previous.applyState({volume:.4,muted:false,playbackRate:1});previous.play();await new Promise(r=>setTimeout(r,50));check(!previous.audio.paused,'native previous replacement plays');
  loaded=ready();master.src=urls[1];
  const playing=master.play();check(previous.destroyed&&previous.audio.paused&&previous.audio.muted,'native old replacement silent before new play');await loaded;await playing;
  check(adapter.getSnapshot().track.id===null,'native stale metadata cannot restart previous recording');
  navigator.mediaSession.metadata=new MediaMetadata({title:'Fixture B',artist:'CELIKOM'});
  check(latest.track.id==='12','native metadata setter refresh is synchronous');
 }finally{previous?.destroy();adapter.unmount();master.pause();master.remove();for(const url of urls)URL.revokeObjectURL(url);}

 document.body.dataset.gainStep='native original handoff';
 const original=document.createElement('audio');original.hidden=true;document.body.append(original);
 const source=URL.createObjectURL(blob),loadedOriginal=new Promise((resolve,reject)=>{original.addEventListener('loadeddata',resolve,{once:true});original.addEventListener('error',reject,{once:true});});original.src=source;original.load();await loadedOriginal;await original.play();
 navigator.mediaSession.metadata=new MediaMetadata({title:'Fixture A',artist:'CELIKOM'});
 window.__STATE_PATCHES__=[[...['Fixture A','Fixture B'].map((title,index)=>({id:String(11+index),title,artists:[{name:'CELIKOM'}],durationMs:Math.round(original.duration*1000)}))]];
 const channel=__CELIKOM_PLAYER_CORE_V1__.CHANNEL,sessionId='native-handoff-session';let requestId=0;
 const message=(type,payload={},id=null)=>window.postMessage({channel,protocolVersion:1,direction:'to-main',sessionId,type,payload,requestId:id},'*');
 const exchange=(type,payload={})=>new Promise((resolve,reject)=>{const id=String(++requestId);const timer=setTimeout(()=>{window.removeEventListener('message',listener);reject(Error('native handoff response timeout'));},3000);const listener=e=>{if(e.source===window&&e.data?.direction==='from-main'&&e.data?.sessionId===sessionId&&e.data?.requestId===id){clearTimeout(timer);window.removeEventListener('message',listener);if(e.data.payload.ok)resolve(e.data.payload.result);else reject(Error(e.data.payload.error));}};window.addEventListener('message',listener);message('REQUEST',{type,payload},id);});
 message('INIT');await new Promise(r=>setTimeout(r,30));
 const snapshot=await exchange('GET_SNAPSHOT');
 await exchange('GUARD_ENGAGE',{trackId:'11',mediaId:snapshot.player.mediaId,token:sessionId+':1'});
 const physicalMute=()=>Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype,'muted').get.call(original);
 check(physicalMute(),'native original guard');
 const old=new ReplacementPlayer(window,r=>fatal.push(r));await old.prepare({url:source,demoLoop:true});old.applyState({volume:.4,muted:false,playbackRate:1});old.play();await new Promise(r=>setTimeout(r,30));
 navigator.mediaSession.metadata=new MediaMetadata({title:'Fixture B',artist:'CELIKOM'});
 check(old.audio.paused&&old.audio.muted,'native old replacement silenced');check(physicalMute(),'native OLD ORIGINAL stays silent while metadata is ahead of stream');
 await exchange('GUARD_RELEASE',{token:sessionId+':1',reason:'guard-lost:master-binding-changed'});check(physicalMute(),'old controller acknowledgement does not unmute old original');
 original.volume=.23;
 await exchange('GUARD_ENGAGE',{trackId:'12',mediaId:snapshot.player.mediaId,token:sessionId+':3'});check(physicalMute(),'handoff has no unmuted interval');
 await exchange('GUARD_RELEASE',{token:sessionId+':3',reason:'manual-original'});check(!physicalMute()&&original.volume===.23,'manual restore preserves intent');
 old.destroy();__CELIKOM_MAIN_BRIDGE_V1__.destroy();original.pause();original.remove();URL.revokeObjectURL(source);

 const toggle=document.querySelector('[data-gain-toggle]');check(!toggle.open,'gain collapsed initially');toggle.open=true;
 const input=document.querySelector('[name=gain_db]');input.value='6';input.dispatchEvent(new Event('input'));await new Promise(r=>setTimeout(r,50));check(document.querySelector('[data-gain-value]').textContent==='+6 дБ','slider display');
 document.querySelector('[data-gain-reset]').click();check(input.value==='0','reset');
 input.value='12';input.dispatchEvent(new Event('input'));check(input.style.getPropertyValue('--gain-fill')==='100%','max fills entire track');
 let saves=0;const oldFetch=window.fetch;window.fetch=async(url,options)=>{if(options?.method==='POST'){saves++;return new Response(JSON.stringify({saved:true,gain_db:12}),{headers:{'Content-Type':'application/json'}});}return oldFetch(url,options);};
 const position=scrollY,address=location.href,form=document.querySelector('[data-audio-gain]');
 form.requestSubmit();form.dispatchEvent(new Event('submit',{cancelable:true}));await new Promise(r=>setTimeout(r,100));
 check(saves===1,'one save');check(document.querySelector('[data-gain-save-status]').textContent==='Громкость сохранена.','inline confirmation');check(document.querySelector('[name=gain_before]').value==='12','next-save lease');check(scrollY===position&&location.href===address&&toggle.open,'save preserves scroll, URL and disclosure');window.fetch=oldFetch;

 check(document.documentElement.scrollWidth<=innerWidth,'mixer horizontal layout');document.body.dataset.gainResult='pass';
 }catch(e){document.body.dataset.gainResult=e.message+' at '+document.body.dataset.gainStep+' '+e.stack}})();</script></body></html>`;
 const file=join(directory,'gain.html');await writeFile(file,html);await mkdir('dist/layout-proof',{recursive:true});
 const browser=spawn(binary,['--headless=new','--no-sandbox','--disable-gpu','--autoplay-policy=no-user-gesture-required','--window-size=420,600','--remote-debugging-port=0','--user-data-dir='+join(directory,'profile'),pathToFileURL(file).href],{stdio:['ignore','ignore','pipe']});
 const exited=new Promise(resolve=>browser.once('exit',resolve));
 let socket;
 try{
  const pause=ms=>new Promise(r=>setTimeout(r,ms));let port;
  for(let i=0;i<100&&!port;i++){try{port=(await readFile(join(directory,'profile','DevToolsActivePort'),'utf8')).split('\n')[0];}catch{}if(!port)await pause(50);}
  if(!port)throw Error('Chrome debug port unavailable');
  const pages=await fetch('http://127.0.0.1:'+port+'/json/list').then(r=>r.json());const page=pages.find(x=>x.type==='page');if(!page)throw Error('Chrome page unavailable');
  socket=new WebSocket(page.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
  let id=0;const pending=new Map();socket.onmessage=event=>{const m=JSON.parse(event.data);if(pending.has(m.id)){const {resolve,reject}=pending.get(m.id);pending.delete(m.id);if(m.error)reject(Error(m.error.message));else resolve(m.result);}};
  const call=(method,params={})=>new Promise((resolve,reject)=>{const seq=++id;pending.set(seq,{resolve,reject});socket.send(JSON.stringify({id:seq,method,params}));});
  let state;
  for(let i=0;i<200;i++){
   const r=await call('Runtime.evaluate',{expression:'JSON.stringify({result:document.body?.dataset.gainResult,step:document.body?.dataset.gainStep})',returnByValue:true});
   state=JSON.parse(r.result.value||'{}');if(state.result)break;await pause(100);
  }
  if(state?.result!=='pass')throw Error('Audio gain browser: '+(state?.result||'no result at '+state?.step));
  const shot=await call('Page.captureScreenshot',{format:'png'});await writeFile(join(process.cwd(),'dist/layout-proof/audio-gain.png'),Buffer.from(shot.data,'base64'));
 }finally{socket?.close();browser.kill('SIGTERM');await Promise.race([exited,new Promise(resolve=>setTimeout(resolve,1500))]);}
 console.log('Native audio gain: actual decoded media, amplitude boost/attenuation/ceiling, volume/mute/cleanup, native stale-track transition/old-original mute handoff and admin slider/reset PASS');
}finally{await rm(directory,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
