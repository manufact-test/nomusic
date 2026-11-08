import { readFile, writeFile, mkdtemp, rm, access } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const candidates=[process.env.CELIKOM_BROWSER_BINARY,'/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium'];
let browser;
for (const candidate of candidates) {
  if (!candidate) continue;
  try { await access(candidate); browser=candidate; break; } catch {}
}
if (!browser) {
  if (process.env.CI) throw new Error('Browser required in CI');
  console.log('Bulk layout needs Chromium; skipped outside CI');
  process.exit(0);
}
const source=await readFile(process.argv[2],'utf8');
const injection='<script>try {'
 + 'const bar=document.querySelector("[data-bulk-select]");'
 + 'const boxes=[...document.querySelectorAll("[data-bulk-candidate]")];'
 + 'if(!bar || boxes.length!==50)throw Error("50 checkboxes absent");'
 + 'if(boxes.some(x=>x.checked))throw Error("Preselected");'
 + 'bar.querySelector("[data-bulk-all]").click();'
 + 'if(boxes.filter(x=>x.checked).length!==50 || !bar.querySelector("[data-bulk-count]").textContent.includes("50 из 50"))throw Error("Select all");'
 + 'if(bar.querySelector("[name=bulk_action]").disabled)throw Error("Actions disabled");'
 + 'const form=document.querySelector("#bulk-selection");'
 + 'if(new FormData(form).getAll(boxes[0].name).length!==1)throw Error("Form association");'
 + 'const els=[bar,...bar.querySelectorAll("button"),...document.querySelectorAll(".bulk-card-check")];'
 + 'for(const el of els){const r=el.getBoundingClientRect();if(r.width && (r.left<-1 || r.right>innerWidth+1))throw Error("Horizontal overflow element")}'
 + 'if(document.documentElement.scrollWidth>innerWidth+1)throw Error("Page horizontal overflow");'
 + 'bar.querySelector("[data-bulk-none]").click();'
 + 'if(boxes.some(x=>x.checked) || !bar.querySelector("[data-bulk-count]").textContent.includes("0 из 50"))throw Error("Clear selection");'
 + 'document.body.dataset.bulkLayout="pass";'
 + '}catch(e){document.body.dataset.bulkLayout=e.message}</script>';
const directory=await mkdtemp(join(tmpdir(),'celikom-bulk-browser-'));
try{
  const file=join(directory,'index.html');
  await writeFile(file,source.replace('</body>',injection+'</body>'));
  for(const width of [1440,768,390]){
    const res=spawnSync(browser,['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage',
      '--force-device-scale-factor=1','--window-size='+width+',900','--dump-dom',pathToFileURL(file).href],
      {encoding:'utf8',timeout:45000,maxBuffer:15*1024*1024});
    const status=res.stdout.match(/data-bulk-layout="([^"]*)"/)?.[1]??'not executed';
    if(res.status!==0 || status!=='pass')throw new Error('Bulk layout '+width+': '+status+' '+res.stderr.slice(-500));
    console.log('PASS bulk moderation responsive '+width+'px; select all/none and form submission');
  }
} finally {await rm(directory,{recursive:true,force:true});}
