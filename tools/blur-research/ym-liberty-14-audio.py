#!/usr/bin/env python3
"""Read-only ephemeral verification of 14 non-overlapping YM Liberty audio links.
No production access, upload, moderation, persistent audio files or rights assumption.
"""
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import subprocess,hashlib,json,tempfile,time
IDs=['27317249','27323572','33790386','63607785','78803018','113140426','113714170','130966246','146122668','148716121','149360077','152973936','153116884','155807913']
expected_sizes={'27317249':8403132,'27323572':5926462,'33790386':9551324,'63607785':13009986,'78803018':8779022,'113140426':9569179,'113714170':10010950,'130966246':5932076,'146122668':4933522,'148716121':6558219,'149360077':7642846,'152973936':6860847,'153116884':6757981,'155807913':5842396}
p=json.loads(Path('tools/blur-research/ym-liberty-33-candidates.json').read_text('utf-8'))
byid={x['track_id']:x for x in p}
assert len(IDs)==14 and len(set(IDs))==14 and set(IDs)<=set(byid)
out=[]
with tempfile.TemporaryDirectory() as d:
    for tid in IDs:
        x=byid[tid];url=x['source_url']
        item={'id':tid,'source':url,'status':'unchecked','sha256':None,'bytes':0,'mime':None,'duration_ms':None,'tags':{},'inspector_ms':None}
        dest=Path(d)/(tid+'.mp3')
        try:
            assert urlsplit(url).hostname in ('huggingface.co','raw.githubusercontent.com','github.com')
            req=Request(url,headers={'User-Agent':'CELIKOM-YMLiberty-readonly-audit/1.0'})
            h=hashlib.sha256();n=0
            with urlopen(req,timeout=45) as response,dest.open('wb') as f:
                if response.status!=200:raise RuntimeError('http_non_200')
                while chunk:=response.read(262144):
                    n+=len(chunk)
                    if n>25_000_000:raise RuntimeError('larger_than_import_limit')
                    h.update(chunk);f.write(chunk)
            item['bytes']=n
            item['sha256']=h.hexdigest()
            if n!=expected_sizes[tid]:raise RuntimeError('size_changed_since_head')
            mime=subprocess.run(['file','-b','--mime-type',str(dest)],check=True,text=True,capture_output=True,timeout=15).stdout.strip()
            item['mime']=mime
            if mime!='audio/mpeg':raise RuntimeError('not_mp3')
            probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:format_tags=title,artist,album','-of','json',str(dest)],check=True,text=True,capture_output=True,timeout=60)
            fmt=json.loads(probe.stdout).get('format',{})
            item['duration_ms']=round(float(fmt['duration'])*1000)
            item['tags']=fmt.get('tags',{})
            php='require "server/bootstrap.php";$x=(new Celikom\\Application\\Mp3Inspector())->durationMs($argv[1]);echo $x===null?"":$x;'
            res=subprocess.run(['php','-r',php,str(dest)],check=True,text=True,capture_output=True,timeout=60)
            item['inspector_ms']=int(res.stdout) if res.stdout.strip().isdigit() else None
            if not item['inspector_ms'] or abs(item['inspector_ms']-item['duration_ms'])>1500:
                raise RuntimeError('mp3inspector_or_duration_rejected')
            item['status']='audio_technically_valid'
        except Exception as e:
            item['status']='failed'
            item['error']=type(e).__name__+':'+str(e)[:120]
        finally:dest.unlink(missing_ok=True)
        out.append(item)
        print('YM_LIBERTY_AUDIO_VERIFIED '+json.dumps(item,ensure_ascii=False),flush=True)
stats={'checked':len(out),'valid_mp3':sum(x['status']=='audio_technically_valid' for x in out),'failed':sum(x['status']=='failed' for x in out),'production_writes':0,'rights_verified':False,'yandex_match_verified':False}
Path('ym-liberty-14-source-check.json').write_text(json.dumps({'summary':stats,'records':out},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('YM_LIBERTY_AUDIO_SUMMARY '+json.dumps(stats,ensure_ascii=False),flush=True)
