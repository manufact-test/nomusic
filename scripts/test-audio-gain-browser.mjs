import {access,readFile,writeFile,mkdtemp,rm,mkdir} from 'node:fs/promises';
import {spawn} from 'node:child_process';
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
 const dsp=ui.slice(0,ui.indexOf('\n(()=>'));
 const deployed=player.slice(player.indexOf('function createGainChain'),player.indexOf('class ReplacementPlayer'));
 const canonical=s=>stripTypeScriptTypes(s,{mode:'transform'}).trim();
 if(canonical(deployed)!==canonical(dsp))throw Error('Admin/player DSP mismatch');
 const bytes=await readFile('extension/assets/test-audio.mp3');
 const css=await readFile('server/src/Admin/admin-style.css','utf8');
 const html=`<!doctype html><html><head><style>${css}</style></head><body><main><div class="player-wrap" id="audio-version-5"><audio data-gain-audio data-gain-db="0" controls></audio></div><form class="audio-gain-form" data-audio-gain data-audio-id="audio-version-5"><label>Громкость версии <output data-gain-value>0 дБ</output></label><div class="audio-gain-controls"><span>Тише</span><input name="gain_db" type="range" min="-12" max="12" step="0.5" value="0"><span>Громче</span></div><button type="button" data-gain-reset>Исходная громкость</button><button>Сохранить громкость</button><p data-gain-note>Прослушайте и сохраните</p></form></main><script>${ui}\n${player}\n(async()=>{try{
 const check=(v,m)=>{if(!v)throw Error(m)};
 const render=async(db,amplitude)=>{document.body.dataset.gainStep='offline '+db;
  const context=new OfflineAudioContext(1,44100,44100),source=context.createBufferSource(),buffer=context.createBuffer(1,44100,44100),signal=buffer.getChannelData(0);
  for(let i=0;i<signal.length;i++)signal[i]=amplitude*Math.sin(2*Math.PI*440*i/44100);source.buffer=buffer;
  const facade={currentTime:0,destination:context.destination,createMediaElementSource:()=>source,createGain:()=>context.createGain(),createDynamicsCompressor:()=>context.createDynamicsCompressor(),createWaveShaper:()=>context.createWaveShaper()};
  createGainChain(facade,null,db);source.start();const audio=(await context.startRendering()).getChannelData(0);const kept=audio.slice(10000);return {rms:Math.sqrt(kept.reduce((n,x)=>n+x*x,0)/kept.length),peak:Math.max(...kept.map(Math.abs))};
 };
 const base=await render(0,0.03),boost=await render(6,0.03),quiet=await render(-6,0.03),loud=await render(12,0.95);
 check(boost.rms/base.rms>1.9&&boost.rms/base.rms<2.1,'quiet signal boost');check(quiet.rms/base.rms>0.49&&quiet.rms/base.rms<0.52,'attenuation');check(loud.peak<=0.9801,'peak ceiling');
 document.body.dataset.gainStep='actual media';
 const {ReplacementPlayer}=globalThis.__CELIKOM_REPLACEMENT_PLAYER_V1__,fatal=[];
 const p=new ReplacementPlayer(window,r=>fatal.push(r));await p.prepare({url:'data:audio/mpeg;base64,${bytes.toString('base64')}',demoLoop:true,gainDb:6});
 check(p.gainContext.state==='running','real media gain context');p.applyState({volume:.4,muted:false,playbackRate:1});p.play();await new Promise(r=>setTimeout(r,150));check(!p.audio.paused&&p.audio.volume===.4,'real amplified media playback and volume sync');
 p.applyState({volume:.3,muted:true,playbackRate:1});check(p.audio.muted,'mute sync');const context=p.gainContext;p.destroy();await new Promise(r=>setTimeout(r,50));check(context.state==='closed'&&!p.audio.isConnected,'gain cleanup');check(fatal.length===0,'no media errors');
 const input=document.querySelector('[name=gain_db]');input.value='6';input.dispatchEvent(new Event('input'));await new Promise(r=>setTimeout(r,50));check(document.querySelector('[data-gain-value]').textContent==='+6 дБ','slider display');
 document.querySelector('[data-gain-reset]').click();check(input.value==='0','reset');
 check(document.documentElement.scrollWidth<=innerWidth,'mixer horizontal layout');document.body.dataset.gainResult='pass';
 }catch(e){document.body.dataset.gainResult=e.message}})();</script></body></html>`;
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
 console.log('Native audio gain: actual decoded media, amplitude boost/attenuation/ceiling, volume/mute/cleanup and admin slider/reset PASS');
}finally{await rm(directory,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
