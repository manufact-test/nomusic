#!/usr/bin/env python3
"""Validate 20 independent-fork audio sources outside production; no uploads or rights approvals."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError,URLError
import json,hashlib,subprocess,tempfile
source=json.loads(Path('tools/blur-research/new-forks-20-candidates.json').read_text('utf-8'))
assert len(source)==20 and len({x['track_id'] for x in source})==20
def check(x):
    t=x['track_id'];row={**x,'status':'unchecked','actual_bytes':0,'sha256':None,'git_blob_match':None,'mime':'','duration_ms':None,'inspector_duration_ms':None,'tags':{}}
    with tempfile.TemporaryDirectory(prefix='celikom-fork20-') as d:
        path=Path(d)/f'{t}.mp3'
        try:
            if urlsplit(x['source_url']).hostname!='raw.githubusercontent.com':raise ValueError('non_allowlisted_host')
            req=Request(x['source_url'],headers={'User-Agent':'CELIKOM-source-audit-readonly/1.0'})
            h=hashlib.sha256();n=0
            with urlopen(req,timeout=65) as response,path.open('wb') as f:
                if response.status!=200:raise RuntimeError('http_'+str(response.status))
                while data:=response.read(262144):
                    n+=len(data)
                    if n>25_000_000:raise RuntimeError('exceeds_import_limit')
                    h.update(data);f.write(data)
            row['actual_bytes']=n;row['sha256']=h.hexdigest()
            if n!=x['size_bytes']:raise RuntimeError('wrong_file_size')
            git=hashlib.sha1(b'blob '+str(n).encode()+b'\x00'+path.read_bytes()).hexdigest()
            row['git_blob_match']=(git==x['source_blob_sha1'])
            if not row['git_blob_match']:raise RuntimeError('source_blob_sha1_mismatch')
            mime=subprocess.run(['file','-b','--mime-type',str(path)],text=True,capture_output=True,check=True,timeout=15).stdout.strip()
            row['mime']=mime
            if mime!='audio/mpeg':raise RuntimeError('not_mp3')
            proc=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:format_tags=title,artist,album','-of','json',str(path)],check=True,text=True,capture_output=True,timeout=60)
            info=json.loads(proc.stdout).get('format',{})
            row['duration_ms']=round(float(info['duration'])*1000)
            row['tags']=info.get('tags',{})
            php='require "server/bootstrap.php";$x=(new Celikom\\Application\\Mp3Inspector())->durationMs($argv[1]);echo $x===null?"":$x;'
            got=subprocess.run(['php','-r',php,str(path)],check=True,text=True,capture_output=True,timeout=60)
            row['inspector_duration_ms']=int(got.stdout) if got.stdout.strip().isdigit() else None
            if not row['inspector_duration_ms'] or abs(row['inspector_duration_ms']-row['duration_ms'])>1500:raise RuntimeError('mp3inspector_duration_invalid')
            row['status']='audio_technically_valid'
        except Exception as exc:
            row['status']='needs_manual_audio'
            row['error']=type(exc).__name__+':'+str(exc)[:140]
    return row
rows=[]
with ThreadPoolExecutor(max_workers=5) as pool:
    futures=[pool.submit(check,x) for x in source]
    for fut in as_completed(futures):
        item=fut.result()
        rows.append(item)
        print('FORK20_SOURCE '+json.dumps(item,ensure_ascii=False),flush=True)
rows.sort(key=lambda v:int(v['track_id']))
summary={'checked':len(rows),'valid_mp3':sum(v['status']=='audio_technically_valid' for v in rows),'manual_repair':sum(v['status']=='needs_manual_audio' for v in rows),'production_writes':0,'yandex_track_id_match_verified':False,'rights_verified':False}
Path('fork20-audio-results.json').write_text(json.dumps({'summary':summary,'rows':rows},ensure_ascii=False,indent=2)+'\n')
print('FORK20_SUMMARY '+json.dumps(summary,ensure_ascii=False),flush=True)
