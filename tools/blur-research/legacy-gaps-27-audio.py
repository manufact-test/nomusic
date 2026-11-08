#!/usr/bin/env python3
"""Examine 27 un-imported source MP3s left outside prior manifest, without production access."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,hashlib,subprocess,tempfile
data=json.loads(Path('tools/blur-research/legacy-gaps-27-candidates.json').read_text('utf8'))
assert len(data)==27 and len({x['track_id'] for x in data})==27
def validate(x):
    r={**x,'status':'unverified','actual_bytes':0,'sha256':None,'mime':'','duration_ms':None,'inspector_duration_ms':None,'tags':{}}
    with tempfile.TemporaryDirectory(prefix='celikom-oldgap-') as d:
        dest=Path(d)/(x['track_id']+'.mp3')
        try:
            if urlsplit(x['source_url']).hostname!='raw.githubusercontent.com':raise RuntimeError('host_invalid')
            req=Request(x['source_url'],headers={'User-Agent':'CELIKOM-legacy-gap-readonly'})
            h=hashlib.sha256();blob=hashlib.sha1();n=0
            with urlopen(req,timeout=70) as response,dest.open('wb') as f:
                if response.status!=200:raise RuntimeError('http_'+str(response.status))
                while chunk:=response.read(262144):
                    n+=len(chunk)
                    if n>25000000:raise RuntimeError('limit')
                    h.update(chunk);f.write(chunk)
            r['actual_bytes']=n;r['sha256']=h.hexdigest()
            if n!=x['source_bytes']:raise RuntimeError('size_changed')
            blob.update(b'blob '+str(n).encode()+b'\0')
            with dest.open('rb') as f:
                while chunk:=f.read(262144):blob.update(chunk)
            if blob.hexdigest()!=x['source_sha1']:raise RuntimeError('git_blob_invalid')
            mime=subprocess.run(['file','-b','--mime-type',str(dest)],check=True,text=True,capture_output=True,timeout=15).stdout.strip()
            r['mime']=mime
            if mime!='audio/mpeg':raise RuntimeError('not_mp3')
            p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:format_tags=title,artist,album','-of','json',str(dest)],check=True,text=True,capture_output=True,timeout=60)
            fmt=json.loads(p.stdout).get('format',{})
            r['duration_ms']=round(float(fmt['duration'])*1000)
            r['tags']=fmt.get('tags',{})
            php='require "server/bootstrap.php";$x=(new Celikom\\Application\\Mp3Inspector())->durationMs($argv[1]);echo $x===null?"":$x;'
            p=subprocess.run(['php','-r',php,str(dest)],check=True,text=True,capture_output=True,timeout=60)
            r['inspector_duration_ms']=int(p.stdout) if p.stdout.strip().isdigit() else None
            if not r['inspector_duration_ms'] or abs(r['duration_ms']-r['inspector_duration_ms'])>1500:raise RuntimeError('inspector_failed')
            r['status']='audio_technically_valid'
        except Exception as e:
            r['status']='needs_manual_audio';r['error']=type(e).__name__+':'+str(e)[:160]
    return r
rows=[]
with ThreadPoolExecutor(max_workers=5) as pool:
    fs=[pool.submit(validate,x) for x in data]
    for f in as_completed(fs):
        x=f.result();rows.append(x);print('OLDGAP27_RESULT '+json.dumps(x,ensure_ascii=False),flush=True)
rows.sort(key=lambda x:int(x['track_id']))
summary={'count':len(rows),'valid':sum(x['status']=='audio_technically_valid' for x in rows),'broken':sum(x['status']=='needs_manual_audio' for x in rows),'writes':0,'rights_verified':False,'yandex_ids_verified':False}
Path('oldgap27-report.json').write_text(json.dumps({'summary':summary,'rows':rows},ensure_ascii=False,indent=2)+'\n')
print('OLDGAP27_SUMMARY '+json.dumps(summary,ensure_ascii=False),flush=True)
