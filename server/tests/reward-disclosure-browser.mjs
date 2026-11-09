import { access, mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
let binary;
for (const candidate of [process.env.CELIKOM_BROWSER_BINARY, '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium']) {
  if (!candidate) continue;
  try { await access(candidate); binary=candidate; break; } catch (_) {}
}
if (!binary) {
  if (process.env.REQUIRE_BROWSER_AUDIO === '1') throw new Error('Chromium required for disclosure regression');
  console.log('Disclosure scroll browser check deferred to Chromium CI');
  process.exit(0);
}
const directory=await mkdtemp(join(tmpdir(),'celikom-disclosure-'));
try {
  const source=await readFile(new URL('../src/Reward/reward-disclosure.js',import.meta.url),'utf8');
  const html=`<!doctype html><style>body{margin:0}header{height:1500px}summary{height:40px}details{overflow-anchor:none}article{height:1500px}</style>
<header></header><details open data-reward-account="2" data-reward-loaded="1"><summary>Свернуть</summary><div data-reward-content><article>История</article></div></details><footer style="height:50px"></footer>
<script>${source}</script><script>
setTimeout(()=>{
 try {
  const summary=document.querySelector('summary');window.scrollTo(0,1450);const y=scrollY;
  if(y!==1450)throw new Error('fixture scroll');
  summary.click();if(scrollY!==y)throw new Error('collapse jumped');
  summary.click();summary.click();if(scrollY!==y)throw new Error('repeated collapse jumped');
  window.scrollTo(0,0);
  // Virtual time can delay the native scroll event until after dump-dom.
  // Dispatch it explicitly; layout and viewport checks above remain native.
  window.dispatchEvent(new Event('scroll'));
  setTimeout(()=>{
   document.body.dataset.result=document.querySelector('body > div[aria-hidden="true"]').style.height==='0px'?'pass':'tail-not-released';
  },100);
 }catch(error){document.body.dataset.result=error.message}
},100);
</script>`;
  const file=join(directory,'fixture.html');await writeFile(file,html);
  const result=spawnSync(binary,['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-gpu','--window-size=900,600','--virtual-time-budget=2000','--dump-dom',pathToFileURL(file).href],{encoding:'utf8',timeout:30000});
  if(result.status!==0 || !result.stdout.includes('data-result="pass"')) throw new Error('Native Chromium disclosure regression failed: '+(result.stdout.match(/data-result="([^"]*)"/)?.[1]||'no result'));
  console.log('Native Chromium disclosure: bottom collapse, repeated toggle and space release PASS');
} finally {await rm(directory,{recursive:true,force:true})}
