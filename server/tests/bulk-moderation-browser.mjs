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
const expected=Number(process.argv[3]||50);
if(!Number.isInteger(expected)||expected<1||expected>50)throw Error('Invalid expected count');
const source=await readFile(process.argv[2],'utf8');
const injection='<script>try {'
 + 'const bar=document.querySelector("[data-bulk-select]");'
 + 'const boxes=[...document.querySelectorAll("[data-bulk-candidate]")];'
 + 'if(!bar || boxes.length!=='+expected+')throw Error("Checkboxes absent");'
 + 'if(boxes.some(x=>x.checked))throw Error("Preselected");'
 + 'bar.querySelector("[data-bulk-all]").click();'
 + 'if(boxes.filter(x=>x.checked).length!==boxes.length || !bar.querySelector("[data-bulk-count]").textContent.includes(boxes.length+" из "+boxes.length))throw Error("Select all");'
 + 'const onlyPending=boxes.every(x=>x.dataset.bulkStatus==="pending");for(const b of bar.querySelectorAll("[name=bulk_action]")){if(b.disabled!==(b.value!=="delete"&&!onlyPending))throw Error("Wrong action availability")}'
 + 'const form=document.querySelector("#bulk-selection");'
 + 'if(new FormData(form).getAll(boxes[0].name).length!==1)throw Error("Form association");'
 + 'const els=[bar,...bar.querySelectorAll("button"),...document.querySelectorAll(".bulk-card-check")];'
 + 'for(const el of els){const r=el.getBoundingClientRect();if(r.width && (r.left<-1 || r.right>innerWidth+1))throw Error("Horizontal overflow element")}'
 + 'if(document.documentElement.scrollWidth>innerWidth+1)throw Error("Page horizontal overflow");'
 + 'bar.querySelector("[data-bulk-none]").click();'
 + 'if(boxes.some(x=>x.checked) || !bar.querySelector("[data-bulk-count]").textContent.includes("0 из "+boxes.length))throw Error("Clear selection");'
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

