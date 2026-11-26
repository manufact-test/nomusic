import { access, readFile, writeFile, mkdtemp, rm } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
let binary;
for(const candidate of [process.env.CELIKOM_BROWSER_BINARY,'/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium']){
  if(!candidate)continue;
  try{await access(candidate);binary=candidate;break}catch(_){}
}
if(!binary){
  if(process.env.REQUIRE_BROWSER_AUDIO==='1')throw Error('Chromium required for incident presentation');
  console.log('Incident popup browser verification deferred to Chromium CI');process.exit(0);
}
const directory=await mkdtemp(join(tmpdir(),'celikom-incident-popup-'));
try{
  const base=new URL('../extension/dist/unpacked/',import.meta.url);
  const css=await readFile(new URL('popup/popup.css',base),'utf8');
  let html=await readFile(new URL('popup/popup.html',base),'utf8');
  html=html.replace('<link rel="stylesheet" href="popup.css">',`<style>${css}</style>`).replace('<script type="module" src="popup.js"></script>','');
  const scripts=await Promise.all(['upload/contract.js','popup/display-cache.js','popup/incident-status.js'].map(async name=>(await readFile(new URL(name,base),'utf8')).replace(/^import .*$/gm,'').replace(/^export /gm,'')));
  const checks=`<script>${scripts.join('\n;\n')}
  (async()=>{
    try{
      let active=true;
      const presentation=initIncidentStatus({readConfig:async()=>({baseUrl:'https://fixture.example/'}),fetch:async()=>({ok:true,json:async()=>({incident:{service:'yandex',active}})})});
      presentation.updateController({enabled:false,track:null});await presentation.refresh();
      const banner=document.querySelector('[data-incident-banner]');
      if(banner.hidden||banner.getClientRects().length!==1)throw Error('banner missing');
      const style=getComputedStyle(banner);if(style.borderTopWidth!=='2px'||style.borderTopColor!=='rgb(255, 129, 122)')throw Error('red frame');
      for(const name of ['start','stop','restore','add','suggest']){
        const button=document.querySelector('[data-action="'+name+'"]');if(button.getClientRects().length)throw Error('music button visible: '+name);
      }
      if(!document.querySelector('[data-auth-summary]').getClientRects().length)throw Error('account hidden');
      if(document.documentElement.scrollWidth>innerWidth)throw Error('horizontal overflow');
      active=false;await presentation.refresh();
      if(!banner.hidden||!document.querySelector('[data-action="start"]').getClientRects().length)throw Error('controls did not return');
      document.body.dataset.incident='pass';
    }catch(error){document.body.dataset.incident=error.message}
  })();</script>`;
  const file=join(directory,'fixture.html');await writeFile(file,html.replace('</body>',checks+'</body>'));
  for(const width of [340,560]){
    const result=spawnSync(binary,['--headless=new','--no-sandbox','--disable-dev-shm-usage','--disable-gpu',`--window-size=${width},800`,'--virtual-time-budget=2000','--dump-dom',pathToFileURL(file).href],{encoding:'utf8',timeout:30000});
    if(result.status!==0||!result.stdout.includes('data-incident="pass"'))throw Error('Incident popup browser: '+(result.stdout.match(/data-incident="([^"]*)"/)?.[1]||'no result'));
  }
  console.log('Native Chromium incident popup: red frame, hidden music actions, accessible account and automatic resolution PASS');
}finally{await rm(directory,{recursive:true,force:true})}
