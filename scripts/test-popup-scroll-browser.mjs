import {access,readFile,writeFile,mkdtemp,rm,mkdir} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
let binary;
for(const p of [process.env.CELIKOM_BROWSER_BINARY,'/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium']){if(!p)continue;try{await access(p);binary=p;break}catch{}}
if(!binary){if(process.env.REQUIRE_BROWSER_AUDIO==='1')throw Error('Chromium required');console.log('Popup scroll browser deferred to CI');process.exit(0);}
const directory=await mkdtemp(join(tmpdir(),'celikom-scroll-'));
try{
 const base=new URL('../extension/dist/unpacked/',import.meta.url);
 const css=await readFile(new URL('popup/popup.css',base),'utf8');
 const script=(await readFile(new URL('popup/scroll-spacing.js',base),'utf8')).replace(/^export /gm,'');
 let html=(await readFile(new URL('popup/popup.html',base),'utf8')).replace('<link rel="stylesheet" href="popup.css">',`<style>${css} body{width:292px}</style>`).replace('<script type="module" src="popup.js"></script>','');
 html=html.replace('</body>',`<script>${script}\n(async()=>{try{
 const check=(value,message)=>{if(!value)throw Error(message)};
 const settle=()=>new Promise(r=>setTimeout(r,250));
 const panel=document.querySelector('.account-panel'),area=document.querySelector('.account-content');
 panel.open=true;initScrollSpacing();
 const forms=[...document.querySelectorAll('.account-form')],signed=document.querySelector('[data-auth-signed]');
 for(const screen of ['login','register','verify','recovery','signed']){
  panel.dataset.authScreen=screen;forms.forEach(f=>f.hidden=true);signed.hidden=screen!=='signed';
  if(screen!=='signed'){
   const selectors={login:'[data-auth-form]',register:'[data-auth-form]',verify:'[data-auth-verify-form]',recovery:'[data-auth-recovery-form]'};
   const form=document.querySelector(selectors[screen])||forms[0];form.hidden=false;
   // Force a real inner scrollbar in each auth screen without changing its controls.
   const filler=document.createElement('p');filler.textContent='Проверка длинного сообщения. '.repeat(50);form.append(filler);
   await settle();check(area.dataset.scrollOverflow==='true','auth overflow '+screen);
   check(parseFloat(getComputedStyle(area).paddingRight)===10,'auth scrollbar gap '+screen);filler.remove();
  }else{
   const promo=document.querySelector('[data-auth-promo-panel]'),benefits=document.querySelector('[data-benefits-panel]');
   promo.hidden=false;benefits.hidden=false;promo.open=false;benefits.open=false;
   await settle();check(area.dataset.scrollOverflow==='false','short signed content no overflow');check(getComputedStyle(area).paddingRight==='0px','normal gap without scrollbar');
   promo.open=true;benefits.open=true;
   const note=document.querySelector('[data-promo-note]');note.textContent='Длинное сообщение о промокоде. '.repeat(35);
   await settle();check(area.dataset.scrollOverflow==='true','signed overflow');
   const scrollEdge=area.getBoundingClientRect().left+area.clientWidth;
   for(const selector of ['[data-auth-promo-panel] input','[data-auth-logout]']){const right=document.querySelector(selector).getBoundingClientRect().right;check(scrollEdge-right>=9,'control gap '+selector);}
   note.textContent='';promo.open=false;benefits.open=false;await settle();check(area.dataset.scrollOverflow==='false','gap removed when collapsed');
  }
  check(document.documentElement.scrollWidth<=innerWidth,'no horizontal overflow '+screen);
 }
 check(parseFloat(getComputedStyle(document.querySelector('main')).paddingRight)===16,'outer scrollbar keeps popup padding');
 document.querySelector('[data-auth-identity]').textContent='admin@example.invalid';document.querySelector('[data-auth-promo-panel]').open=true;document.querySelector('[data-promo-note]').textContent='Сообщение о промокоде. '.repeat(12);await settle();document.body.dataset.scrollResult='pass';
 }catch(e){document.body.dataset.scrollResult=e.message}})();</script></body>`);
 const file=join(directory,'popup.html');await writeFile(file,html);
 await mkdir('dist/layout-proof',{recursive:true});
 const r=spawnSync(binary,['--headless=new','--no-sandbox','--disable-gpu','--window-size=340,600','--virtual-time-budget=7000','--dump-dom','--screenshot='+join(process.cwd(),'dist/layout-proof/popup-scroll.png'),pathToFileURL(file).href],{encoding:'utf8',timeout:30000,maxBuffer:2e6});
 if(r.status!==0||!r.stdout.includes('data-scroll-result="pass"'))throw Error('Popup scroll spacing: '+(r.stdout.match(/data-scroll-result="([^"]*)"/)?.[1]||'no result'));
 console.log('Popup scrollbar spacing across auth and expanded promo/benefits PASS');
}finally{await rm(directory,{recursive:true,force:true});}
