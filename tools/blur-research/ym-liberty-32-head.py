#!/usr/bin/env python3
"""HEAD-only public candidate availability check; no audio transfers and no production access."""
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError,URLError
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
source=json.loads(Path('tools/blur-research/ym-liberty-33-candidates.json').read_text('utf-8'))
exclude='68070362'
candidates=[x for x in source if x['track_id']!=exclude]
assert len(candidates)==32
ALLOW={'huggingface.co','raw.githubusercontent.com','github.com'}
def check(x):
    address=x['source_url']
    domain=urlsplit(address).hostname
    o={'track_id':x['track_id'],'source_url':address,'status':'untested','code':None,'mime':'','content_length':None}
    if domain not in ALLOW:
        o['status']='unapproved_host'
        return o
    try:
        req=Request(address,method='HEAD',headers={'User-Agent':'CELIKOM-candidate-readonly/1.0'})
        with urlopen(req,timeout=23) as response:
            o['status']='http_ok'
            o['code']=response.status
            o['mime']=response.headers.get('Content-Type','')
            raw_size=response.headers.get('Content-Length')
            o['content_length']=int(raw_size) if raw_size and raw_size.isdigit() else None
            o['final_url_host']=urlsplit(response.url).hostname
    except HTTPError as e:
        o['status']='http_error';o['code']=e.code
    except (URLError,OSError,ValueError) as e:
        o['status']='transient_or_blocked';o['error']=type(e).__name__
    return o
results=[]
with ThreadPoolExecutor(max_workers=6) as pool:
    fut={pool.submit(check,x):x for x in candidates}
    for future in as_completed(fut):
        r=future.result()
        results.append(r)
        print('YM_LIBERTY_PUBLIC_HEAD '+json.dumps(r,ensure_ascii=False),flush=True)
results.sort(key=lambda x:int(x['track_id']))
summary={'tested':len(results),'http_200':sum(r['code']==200 for r in results),'http_errors':sum(r['status']=='http_error' for r in results),'transient_or_blocked':sum(r['status']=='transient_or_blocked' for r in results),'valid_mp3_audio_bytes_not_yet_verified':True,'production_writes':0}
Path('ym-liberty-33-head-results.json').write_text(json.dumps({'summary':summary,'results':results},ensure_ascii=False,indent=2)+'\n')
print('YM_LIBERTY_HEAD_SUMMARY '+json.dumps(summary,ensure_ascii=False),flush=True)
