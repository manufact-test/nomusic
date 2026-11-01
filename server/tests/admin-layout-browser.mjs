import { access, readFile, writeFile, mkdtemp, rm } from 'node:fs/promises';
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
  if (process.env.REQUIRE_BROWSER_AUDIO === '1') throw new Error('Chromium required for admin layout verification');
  console.log('Admin layout browser check deferred to Chromium CI');
  process.exit(0);
}
const directory=await mkdtemp(join(tmpdir(),'celikom-admin-layout-'));
try {
  const source=await readFile(process.argv[2],'utf8');
  const checks=`<script>
  try {
    const navs=document.querySelectorAll('nav.nav');
    if(navs.length!==1)throw new Error('multiple menus');
    if(navs[0].querySelectorAll('a[aria-current="page"]').length!==1)throw new Error('active section');
    if(document.documentElement.scrollWidth>innerWidth)throw new Error('horizontal overflow');
    for(const link of navs[0].querySelectorAll('a')){
      const r=link.getBoundingClientRect();if(r.left<0||r.right>innerWidth)throw new Error('hidden menu link');
    }
    const form=document.querySelector('.incident-form'), label=form.querySelector('label');
    const range=document.createRange();range.selectNodeContents(label.firstChild);
    const input=form.querySelector('textarea').getBoundingClientRect();
    const button=form.querySelector('button').getBoundingClientRect();
    if(input.top-range.getBoundingClientRect().bottom<7)throw new Error('label spacing');
    if(button.top-input.bottom<15)throw new Error('button spacing');
    document.body.dataset.layout='pass';
  }catch(error){document.body.dataset.layout=error.message}
  </script>`;
  const file=join(directory,'fixture.html');await writeFile(file,source.replace('</body>',checks+'</body>'));
  for(const width of [1365,900,375]){
    const result=spawnSync(binary,['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-gpu',`--window-size=${width},900`,'--dump-dom',pathToFileURL(file).href],{encoding:'utf8',timeout:30000});
    if(result.status!==0 || !result.stdout.includes('data-layout="pass"')) throw new Error(`Admin layout ${width}px: `+(result.stdout.match(/data-layout="([^"]*)"/)?.[1]||'no result'));
  }
  console.log('Native Chromium admin layout: unified menu and incident form spacing at desktop/tablet/mobile PASS');
} finally {await rm(directory,{recursive:true,force:true})}
