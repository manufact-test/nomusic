import {access,readFile,writeFile,mkdtemp,rm,mkdir} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
let binary;
for(const p of ['/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium']){try{await access(p);binary=p;break}catch{}}
if(!binary){if(process.env.REQUIRE_BROWSER_AUDIO==='1')throw Error('Chromium required');console.log('Audio gain native check deferred to CI');process.exit(0);}
const directory=await mkdtemp(join(tmpdir(),'celikom-gain-'));
try{
 const ui=await readFile('server/src/Admin/audio-gain.js','utf8');
 const player=await readFile('extension/dist/unpacked/player/replacement-player.js','utf8');
 const dsp=ui.slice(0,ui.indexOf('\n(()=>'));
 if(!player.includes(dsp))throw Error('Admin/player DSP mismatch');
 const bytes=await readFile('extension/assets/test-audio.mp3');
 const css=await readFile('server/src/Admin/admin-style.css','utf8');
 const html=`<!doctype html><html><head><style>${css}</style></head><body><main><div class="player-wrap" id="audio-version-5"><audio data-gain-audio data-gain-db="0" controls></audio></div><form class="audio-gain-form" data-audio-gain data-audio-id="audio-version-5"><label>Громкость версии <output data-gain-value>0 дБ</output></label><div class="audio-gain-controls"><span>Тише</span><input name="gain_db" type="range" min="-12" max="12" step="0.5" value="0"><span>Громче</span></div><button type="button" data-gain-reset>Исходная громкость</button><button>Сохранить громкость</button><p data-gain-note>Прослушайте и сохраните</p></form></main><script>${ui}\n${player}\n(async()=>{try{
 const check=(v,m)=>{if(!v)throw Error(m)};
 const render=async(db,amplitude)=>{
  const context=new OfflineAudioContext(1,44100,44100),source=context.createBufferSource(),buffer=context.createBuffer(1,44100,44100),signal=buffer.getChannelData(0);
  for(let i=0;i<signal.length;i++)signal[i]=amplitude*Math.sin(2*Math.PI*440*i/44100);source.buffer=buffer;
  const facade={currentTime:0,destination:context.destination,createMediaElementSource:()=>source,createGain:()=>context.createGain(),createDynamicsCompressor:()=>context.createDynamicsCompressor(),createWaveShaper:()=>context.createWaveShaper()};
  createGainChain(facade,null,db);source.start();const audio=(await context.startRendering()).getChannelData(0);const kept=audio.slice(10000);return {rms:Math.sqrt(kept.reduce((n,x)=>n+x*x,0)/kept.length),peak:Math.max(...kept.map(Math.abs))};
 };
 const base=await render(0,0.03),boost=await render(6,0.03),quiet=await render(-6,0.03),loud=await render(12,0.95);
 check(boost.rms/base.rms>1.9&&boost.rms/base.rms<2.1,'quiet signal boost');check(quiet.rms/base.rms>0.49&&quiet.rms/base.rms<0.52,'attenuation');check(loud.peak<=0.9801,'peak ceiling');
 const {ReplacementPlayer}=globalThis.__CELIKOM_REPLACEMENT_PLAYER_V1__,fatal=[];
 const p=new ReplacementPlayer(window,r=>fatal.push(r));await p.prepare({url:'data:audio/mpeg;base64,${bytes.toString('base64')}',demoLoop:true,gainDb:6});
 check(p.gainContext.state==='running','real media gain context');p.applyState({volume:.4,muted:false,playbackRate:1});p.play();await new Promise(r=>setTimeout(r,150));check(!p.audio.paused&&p.audio.volume===.4,'real amplified media playback and volume sync');
 p.applyState({volume:.3,muted:true,playbackRate:1});check(p.audio.muted,'mute sync');const context=p.gainContext;p.destroy();await new Promise(r=>setTimeout(r,50));check(context.state==='closed'&&!p.audio.isConnected,'gain cleanup');check(fatal.length===0,'no media errors');
 const input=document.querySelector('[name=gain_db]');input.value='6';input.dispatchEvent(new Event('input'));await new Promise(r=>setTimeout(r,50));check(document.querySelector('[data-gain-value]').textContent==='+6 дБ','slider display');
 document.querySelector('[data-gain-reset]').click();check(input.value==='0','reset');
 check(document.documentElement.scrollWidth<=innerWidth,'mixer horizontal layout');document.body.dataset.gainResult='pass';
 }catch(e){document.body.dataset.gainResult=e.message}})();</script></body></html>`;
 const file=join(directory,'gain.html');await writeFile(file,html);await mkdir('dist/layout-proof',{recursive:true});
 const r=spawnSync(binary,['--headless=new','--no-sandbox','--disable-gpu','--autoplay-policy=no-user-gesture-required','--window-size=420,600','--virtual-time-budget=12000','--dump-dom','--screenshot='+join(process.cwd(),'dist/layout-proof/audio-gain.png'),pathToFileURL(file).href],{encoding:'utf8',timeout:30000,maxBuffer:6e6});
 if(r.status!==0||!r.stdout.includes('data-gain-result="pass"'))throw Error('Audio gain browser: '+(r.stdout.match(/data-gain-result="([^"]*)"/)?.[1]||'no result'));
 console.log('Native audio gain: actual decoded media, amplitude boost/attenuation/ceiling, volume/mute/cleanup and admin slider/reset PASS');
}finally{await rm(directory,{recursive:true,force:true});}
