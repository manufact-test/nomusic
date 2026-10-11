import { readFile,writeFile,access,mkdtemp,rm } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';
let binary;
for(const candidate of [process.env.CELIKOM_BROWSER_BINARY,'/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium']) {
  if(!candidate)continue;try{await access(candidate);binary=candidate;break;}catch{}
}
if(!binary){if(process.env.REQUIRE_BROWSER_AUDIO==='1')throw Error('Chromium required');process.exit(0);}
const directory=await mkdtemp(join(tmpdir(),'celikom-promo-form-'));
try {
 const original=await readFile(process.argv[2],'utf8');
 const check=`<script>setTimeout(()=>{try{
 const form=document.querySelector('[data-promo-create]'),field=n=>form.elements.namedItem(n),deadline=document.querySelector('[data-promo-deadline]');
 const check=(v,m)=>{if(!v)throw Error(m)};
 check(deadline.getBoundingClientRect().height===0,'deadline initially hidden');
 field('activation_window').value='fixed';field('activation_window').dispatchEvent(new Event('change',{bubbles:true}));
 check(deadline.getBoundingClientRect().height>0&&field('activation_deadline').required,'deadline required and shown');
 check(deadline.getBoundingClientRect().top>field('activation_window').getBoundingClientRect().bottom,'deadline below selector');
 field('activation_window').value='unlimited';field('activation_window').dispatchEvent(new Event('change',{bubbles:true}));check(deadline.getBoundingClientRect().height===0,'deadline hidden again');
 const box=field('forever'),text=box.nextElementSibling;check(Math.abs(box.getBoundingClientRect().top-text.getBoundingClientRect().top)<12,'checkbox and label on same line');
 box.checked=true;box.dispatchEvent(new Event('change',{bubbles:true}));check(field('duration_days').disabled&&document.querySelector('[data-promo-days]').getBoundingClientRect().height===0,'lifetime hides days');
 field('discount_percent').value='20';field('discount_percent').dispatchEvent(new Event('input',{bubbles:true}));check(!box.checked&&box.disabled&&!field('duration_days').disabled,'partial discount cannot select lifetime');
 check(document.documentElement.scrollWidth<=innerWidth,'no page overflow');document.body.dataset.promoResult='pass';
 }catch(e){document.body.dataset.promoResult=e.message}},100);</script>`;
 const file=join(directory,'form.html');await writeFile(file,original.replace('</body>',check+'</body>'));
 for(const width of [1100,390]){
  const result=spawnSync(binary,['--headless=new','--no-sandbox','--disable-gpu',`--window-size=${width},900`,'--virtual-time-budget=1000','--dump-dom',pathToFileURL(file).href],{encoding:'utf8',timeout:30000,maxBuffer:2e6});
  if(result.status!==0||!result.stdout.includes('data-promo-result="pass"'))throw Error('Native promo form failed '+width+': '+(result.stdout.match(/data-promo-result="([^"]*)"/)?.[1]||result.error?.message||'no result'));
 }
 console.log('Native promo form desktop/mobile PASS');
}finally{await rm(directory,{recursive:true,force:true});}
