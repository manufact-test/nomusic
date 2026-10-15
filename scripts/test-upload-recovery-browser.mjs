import {access,readFile,writeFile,mkdtemp,rm,mkdir,cp} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
let binary;
for(const p of ['/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium']){try{await access(p);binary=p;break}catch{}}
if(!binary){if(process.env.REQUIRE_BROWSER_AUDIO==='1')throw Error('Chromium required');console.log('Upload recovery native check deferred to CI');process.exit(0);}
const directory=await mkdtemp(join(tmpdir(),'celikom-upload-recovery-'));
try{
 await cp('extension/dist/unpacked',join(directory,'runtime'),{recursive:true});
 const file=join(directory,'runtime/popup/popup.html');
 let html=await readFile(file,'utf8');
 html=html.replace('<script type="module" src="popup.js"></script>',`<script>
 const nativeTimeout=window.setTimeout.bind(window);
 window.setTimeout=(fn,ms,...args)=>nativeTimeout(fn,ms===30000||ms===60000?500:ms,...args);
 const state={enabled:false,phase:'STOPPED',bridge:{healthy:true},track:{id:'1944599',confidence:260,ambiguous:false,metadata:{title:'Папиросы',artist:'Зануда',durationMs:200820}}};
 let blockStart=false,blockVersion=false,finishStart,posts=0;
 const access={allowed:true,source:'promo',reason:'promo_active',valid_until:null};
 window.chrome={runtime:{getURL:p=>new URL('../'+p,location.href).href,getManifest:()=>({version:'0.4.47'}),sendMessage:async m=>{
  if(m.type==='CELIKOM_STATUS_GET')return structuredClone(state);
  if(m.type==='CELIKOM_ENABLED_SET'){
   if(m.enabled&&blockStart)return new Promise(resolve=>finishStart=resolve);
   state.enabled=m.enabled;state.phase=m.enabled?'READY':'STOPPED';return structuredClone(state);
  }
  if(m.action==='track-status')return blockVersion?new Promise(()=>{}):{ok:true,status:'none'};
  if(m.action==='status')return {ok:true,available:true,signedIn:true,user:{email:'fixture@example.org'}};
  if(m.action==='entitlement'||m.action==='access-preview')return {ok:true,entitlement:access};
  if(m.action==='contribution-access')return {ok:true,access_token:'a'.repeat(64)};
  return {ok:true,tickets:[]};
 }},storage:{local:{get:async()=>({}),set:async()=>{},remove:async()=>{}},session:{get:async()=>({}),set:async()=>{},remove:async()=>{}}}};
 window.fetch=async(url,options={})=>{if(options.method==='POST')posts++;return new Response(JSON.stringify(String(url).includes('/tracks/upload-status')?{status:'none'}:{baseUrl:'https://fixture.example',incident:{service:'yandex',active:false}}),{headers:{'content-type':'application/json'}});};
 </script><script type="module">
 (async()=>{try{
  await import('./popup.js');
  const wait=ms=>new Promise(resolve=>nativeTimeout(resolve,ms)),check=(v,m)=>{if(!v)throw Error(m)},q=s=>document.querySelector(s);
  const until=async(test,label)=>{for(let i=0;i<150;i++){if(test())return;await wait(20);}throw Error(label+' / '+q('[data-upload-status]').textContent+' / add='+q('[data-action=add]').textContent);};
  await wait(30);document.body.dataset.recoveryStep='picker cancel';
  q('[data-action=add]').click();await until(()=>!q('[data-upload-form]').hidden,'initial form');
  const input=q('[data-upload-file]');check(!q('[data-upload-form]').hidden,'initial form');input.dispatchEvent(new Event('cancel'));
  check(!input.disabled&&!q('[data-action=add]').disabled,'cancel keeps picker available');check(posts===0,'cancel sends no file');
  state.track.id='1944611';q('[data-action=add]').click();await until(()=>q('[data-upload-track]').value==='1944611'&&!q('[data-upload-form]').hidden,'another song');
  check(q('[data-upload-track]').value==='1944611'&&!q('[data-upload-form]').hidden,'another song opens after cancel');
  document.body.dataset.recoveryStep='pending Start/Stop';blockStart=true;
  q('[data-action=start]').click();await wait(10);check(!q('[data-action=stop]').disabled,'Stop available during Start');
  q('[data-action=stop]').click();await wait(10);finishStart({...structuredClone(state),enabled:true,phase:'READY'});await wait(10);
  check(!q('[data-action=start]').disabled&&q('[data-status]').textContent==='Остановлен','late Start cannot overwrite Stop');
  q('[data-action=start]').click();await until(()=>!q('[data-action=start]').disabled&&q('[data-access-status]').textContent.includes('Проверка не завершена'),'Start timeout');
  check(!q('[data-action=start]').disabled&&q('[data-access-status]').textContent.includes('Проверка не завершена'),'stalled Start timeout unlocks');
  blockStart=false;q('[data-action=start]').click();await until(()=>state.enabled&&q('[data-status]').textContent==='Включён · играет оригинал','fresh Start');check(state.enabled&&q('[data-status]').textContent==='Включён · играет оригинал','fresh Start works');
  state.phase='PREPARING';state.preparation={stage:'loading',elapsedMs:10001};
  await until(()=>!q('[data-action=start]').disabled&&q('[data-action=start]').textContent==='Повторить'&&q('[data-status]').textContent==='Загружаем аудио…','stalled preparation exposes Retry');
  q('[data-action=start]').click();await until(()=>state.phase==='READY'&&q('[data-status]').textContent==='Включён · играет оригинал','manual retry takes effect');
  q('[data-action=stop]').click();await wait(20);
  document.body.dataset.recoveryStep='version timeout';blockVersion=true;state.track.id='1944612';await until(()=>q('[data-version-status]').textContent.includes('Не удалось проверить'),'version timeout');
  check(q('[data-version-status]').textContent.includes('Не удалось проверить'),'stalled version check leaves loading state');
  blockVersion=false;state.track.id='1944613';await until(()=>q('[data-version-status]').textContent.includes('ещё не загружена'),'fresh version');check(q('[data-version-status]').textContent.includes('ещё не загружена'),'fresh song recovers version check');
  check(posts===0,'no unintended POST');document.body.dataset.recoveryResult='pass';
 }catch(e){document.body.dataset.recoveryResult=e.message}})();
 </script>`);
 await writeFile(file,html);await mkdir('dist/layout-proof',{recursive:true});
 const browser=spawn(binary,['--headless=new','--allow-file-access-from-files','--no-sandbox','--disable-gpu','--autoplay-policy=no-user-gesture-required','--window-size=420,600','--remote-debugging-port=0','--user-data-dir='+join(directory,'profile'),pathToFileURL(file).href],{stdio:['ignore','ignore','pipe']});
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
   const r=await call('Runtime.evaluate',{expression:'JSON.stringify({result:document.body?.dataset.recoveryResult,step:document.body?.dataset.recoveryStep})',returnByValue:true});
   state=JSON.parse(r.result.value||'{}');if(state.result)break;await pause(100);
  }
  if(state?.result!=='pass')throw Error('Upload recovery browser: '+(state?.result||'no result at '+state?.step));
  const shot=await call('Page.captureScreenshot',{format:'png'});await writeFile(join(process.cwd(),'dist/layout-proof/upload-recovery.png'),Buffer.from(shot.data,'base64'));
 }finally{socket?.close();browser.kill('SIGTERM');await Promise.race([exited,new Promise(resolve=>setTimeout(resolve,1500))]);}
 console.log('Native popup recovery: cancelled picker, another song, pending Start/Stop, stale reply, deadline unlock and fresh retry PASS');
}finally{await rm(directory,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
