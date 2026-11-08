#!/usr/bin/env python3
"""Read-only inspect of 29 HF mirror URLs for known rejected tracks. Temporary audio, no production writes."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError,URLError
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,hashlib,tempfile,subprocess
manifest=json.loads(Path('tools/blur-research/ym-liberty-29-repair-candidates.json').read_text('utf8'))
assert len(manifest)==29 and len({x['track_id'] for x in manifest})==29
def verify(item):
    res={**item,'status':'untested','bytes':0,'sha256':None,'git_blob_match_original':None,'mime':'','duration_ms':None,'inspector_duration_ms':None,'tags':{}}
    with tempfile.TemporaryDirectory(prefix='celikom-hf-repair') as d:
        path=Path(d)/(item['track_id']+'.mp3')
        try:
            if urlsplit(item['source_url']).hostname!='huggingface.co':raise RuntimeError('wrong_host')
            req=Request(item['source_url'],headers={'User-Agent':'CELIKOM-repair-research-readonly'})
            sha=hashlib.sha256();blob=hashlib.sha1();n=0
            with urlopen(req,timeout=65) as reply,path.open('wb') as f:
                if reply.status!=200:raise RuntimeError('non_200')
                while chunk:=reply.read(262144):
                    n+=len(chunk)
                    if n>25000000:raise RuntimeError('exceeds_25mb')
                    sha.update(chunk);f.write(chunk)
            res['bytes']=n;res['sha256']=sha.hexdigest()
            with path.open('rb') as f:
                blob.update(b'blob '+str(n).encode()+b'\0')
                while chunk:=f.read(262144):blob.update(chunk)
            res['git_blob_match_original']=(blob.hexdigest()==item['old_blob_sha1'])
            if res['git_blob_match_original']:raise RuntimeError('same_file_as_rejected_original')
            mime=subprocess.run(['file','--brief','--mime-type',str(path)],text=True,capture_output=True,check=True,timeout=15).stdout.strip()
            res['mime']=mime
            if mime!='audio/mpeg':raise RuntimeError('not_mp3')
            p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:format_tags=title,artist,album','-of','json',str(path)],text=True,capture_output=True,check=True,timeout=60)
            data=json.loads(p.stdout).get('format',{})
            res['duration_ms']=round(float(data['duration'])*1000)
            res['tags']=data.get('tags',{})
            php='require "server/bootstrap.php";$x=(new Celikom\\Application\\Mp3Inspector())->durationMs($argv[1]);echo $x===null?"":$x;'
            p=subprocess.run(['php','-r',php,str(path)],text=True,capture_output=True,check=True,timeout=60)
            res['inspector_duration_ms']=int(p.stdout) if p.stdout.strip().isdigit() else None
            if not res['inspector_duration_ms'] or abs(res['inspector_duration_ms']-res['duration_ms'])>1500:raise RuntimeError('inspector_failed')
            res['status']='audio_technically_valid_alternative'
        except Exception as e:
            res['status']='needs_manual_audio'
            res['error']=type(e).__name__+':'+str(e)[:160]
    return res
results=[]
with ThreadPoolExecutor(max_workers=5) as pool:
    f=[pool.submit(verify,x) for x in manifest]
    for fut in as_completed(f):
        x=fut.result();results.append(x);print('HF29_REPAIR '+json.dumps(x,ensure_ascii=False),flush=True)
results.sort(key=lambda x:int(x['track_id']))
summary={'checked':len(results),'valid_replacements':sum(x['status']=='audio_technically_valid_alternative' for x in results),'manual_repair':sum(x['status']=='needs_manual_audio' for x in results),'production_writes':0,'yandex_track_match_verified':False,'rights_verified':False}
Path('hf29-repair-report.json').write_text(json.dumps({'summary':summary,'records':results},ensure_ascii=False,indent=2)+'\n')
print('HF29_SUMMARY '+json.dumps(summary,ensure_ascii=False),flush=True)
