import { access, readFile, writeFile, mkdtemp, rm, mkdir } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
let binary;
for (const p of ['/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium']) {
  try { await access(p); binary = p; break; } catch {}
}
if (!binary) { if (process.env.REQUIRE_BROWSER_AUDIO === '1') throw Error('Chromium required'); console.log('Support browser check deferred to CI'); process.exit(0); }
const directory = await mkdtemp(join(tmpdir(), 'celikom-support-'));
try {
  const root = new URL('../extension/dist/unpacked/', import.meta.url);
  const css = await readFile(new URL('popup/popup.css', root), 'utf8');
  const code = (await readFile(new URL('popup/support.js', root), 'utf8')).replace(/^export /gm, '');
  let html = (await readFile(new URL('popup/popup.html', root), 'utf8')).replace('<link rel="stylesheet" href="popup.css">', `<style>${css}body{width:292px}</style>`).replace('<script type="module" src="popup.js"></script>', '');
  html = html.replace('</body>', `<script>${code}
  (async()=>{try{
  let copied='',opened='';
  const check=(v,m)=>{if(!v)throw Error(m)};
  window.chrome={runtime:{getManifest:()=>({version:'0.4.29'}),getURL:()=>'/config'},tabs:{create:async({url})=>{opened=url}}};
  window.fetch=async()=>({ok:true,json:async()=>({supportEmail:'team@example.org'})});
  Object.defineProperty(navigator,'clipboard',{value:{writeText:async(t)=>{copied=t}},configurable:true});
  await initSupport({getState:()=>({phase:'ERROR',track:{id:'36116709'},token:'SECRET',account:{email:'PRIVATE'}})});
  const panel=document.querySelector('[data-support-panel]');panel.open=true;
  const description=document.querySelector('[data-support-description]');description.value='Ошибка воспроизведения';
  document.querySelector('[data-support-copy]').click();await new Promise(r=>setTimeout(r,100));
  check(copied.includes('Ошибка воспроизведения')&&copied.includes('36116709'),'copied report');
  check(!copied.includes('SECRET')&&!copied.includes('PRIVATE'),'privacy');
  document.querySelector('[data-support-email]').click();await new Promise(r=>setTimeout(r,100));
  check(opened.startsWith('mailto:team%40example.org?subject='),'mail draft');
  check(document.documentElement.scrollWidth<=innerWidth,'horizontal overflow');
  panel.scrollIntoView();await new Promise(r=>setTimeout(r,200));
  document.body.dataset.supportResult='pass';
  }catch(e){document.body.dataset.supportResult=e.message}})();</script></body>`);
  const file = join(directory, 'support.html'); await writeFile(file, html); await mkdir('dist/layout-proof', {recursive:true});
  const r = spawnSync(binary, ['--headless=new','--no-sandbox','--disable-gpu','--window-size=340,700','--virtual-time-budget=3000','--dump-dom','--screenshot='+join(process.cwd(),'dist/layout-proof/support.png'),pathToFileURL(file).href], {encoding:'utf8',timeout:30000,maxBuffer:2e6});
  if (r.status!==0 || !r.stdout.includes('data-support-result="pass"')) throw Error('Support browser: '+(r.stdout.match(/data-support-result="([^"]*)"/)?.[1]||'no result'));
  console.log('Support UI, copy, mail draft and privacy browser PASS');
} finally { await rm(directory,{recursive:true,force:true}); }
