import { pathToFileURL } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';

const origin = 'https://darkred-camel-588676.hostingersite.com';
const checks = [
  {name:'health', path:'/api/v1/health', status:200, valid:d=>d?.status==='ok'&&d?.service==='celikom-api'},
  {name:'config', path:'/api/v1/config', status:200, valid:d=>d?.features?.replacements===true&&d?.features?.analytics===false},
  {name:'anonymous_resolve', path:'/api/v1/resolve?service=yandex&track_id=144530503', status:401}
];

export async function probe(fetcher=fetch) {
  return Promise.all(checks.map(async check=>{
    const started=Date.now(); let status=null;
    try {
      const response=await fetcher(origin+check.path,{method:'GET',redirect:'error',cache:'no-store',signal:AbortSignal.timeout(12000)});
      status=response.status;
      if(status!==check.status) { await response.body?.cancel(); throw Error('http_status'); }
      if(check.valid) {
        if(!response.headers.get('content-type')?.startsWith('application/json')) { await response.body?.cancel(); throw Error('content_type'); }
        const reader=response.body.getReader(); let size=0; const chunks=[];
        try {
          for(;;) { const {done,value}=await reader.read(); if(done)break; size+=value.byteLength; if(size>16384)throw Error('body_limit'); chunks.push(value); }
        } finally { await reader.cancel(); }
        const bytes=new Uint8Array(size);let offset=0;
        for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
        if(!check.valid(JSON.parse(new TextDecoder().decode(bytes))))throw Error('contract');
      } else await response.body?.cancel();
      return {endpoint:check.name,status,ok:true,elapsedMs:Date.now()-started};
    } catch(error) {
      const reason=['http_status','content_type','body_limit','contract'].includes(error?.message)?error.message:'transport_or_invalid_json';
      return {endpoint:check.name,status,ok:false,reason,elapsedMs:Date.now()-started};
    }
  }));
}

export async function monitor(fetcher=fetch, pause=delay) {
  const samples=[{at:new Date().toISOString(),checks:await probe(fetcher)}];
  if(samples[0].checks.some(c=>!c.ok)) {
    await pause(3000);
    samples.push({at:new Date().toISOString(),checks:await probe(fetcher)});
  }
  return {ok:samples.at(-1).checks.every(c=>c.ok),recovered:samples.length>1&&samples.at(-1).checks.every(c=>c.ok),samples};
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href) {
  const result=await monitor();
  console.log(JSON.stringify(result,null,2));
  if(!result.ok)process.exitCode=1;
}
