#!/usr/bin/env python3
"""Private pilot preflight for replacement candidates: no CELIKOM DB/storage writes."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.request import Request, urlopen
ROOT = Path(__file__).resolve().parent
candidates=json.loads((ROOT/'candidates.json').read_text(encoding='utf-8'))['candidates']
chosen=json.loads((ROOT/'batch20.json').read_text(encoding='utf-8'))['tracks']
done={x['id'] for x in chosen}
blocked={'91340238','25319594','115131527'}
reserves=[x for x in candidates if x['id'] not in done|blocked]
assert len(reserves)==12
PIN='10187b7af56f311fe141a3c9b75483798bf0f589'
ok=[]
with tempfile.TemporaryDirectory(prefix='celikom-reserve-mp3-') as tmp:
    for x in reserves:
        dest=Path(tmp)/(x['id']+'.mp3')
        try:
            h=hashlib.sha1(('blob '+str(x['size'])+'\0').encode('ascii'))
            n=0
            url=f'https://raw.githubusercontent.com/Hazzz895/FckCensorData/{PIN}/tracks/{x["id"]}'
            with urlopen(Request(url,headers={'User-Agent':'CELIKOM-reserve-preflight/1.0'}),timeout=35) as response,dest.open('xb') as out:
                while True:
                    chunk=response.read(262144)
                    if not chunk:break
                    n+=len(chunk)
                    if n>x['size']:raise ValueError('oversized')
                    h.update(chunk);out.write(chunk)
            if n!=x['size'] or h.hexdigest()!=x['blob']:raise ValueError('source_mismatch')
            php_code=r'''require "server/bootstrap.php"; $duration=(new Celikom\Application\Mp3Inspector())->durationMs($argv[1]); $mime=(new finfo(FILEINFO_MIME_TYPE))->file($argv[1]); if($duration===null||$mime!=="audio/mpeg"){fwrite(STDERR,"MP3_INCOMPATIBLE");exit(2);} echo (string)$duration;'''
            p=subprocess.run(['php','-r',php_code,str(dest)],capture_output=True,text=True,timeout=60,cwd=ROOT.parents[1])
            if p.returncode!=0 or not p.stdout.strip().isdigit():raise ValueError('celikom_mp3_incompatible')
            ok.append({'id':x['id'],'artist':x['artist'],'title':x['title'],'duration_ms':int(p.stdout.strip())})
            print('RESERVE_OK '+json.dumps(ok[-1],ensure_ascii=False),flush=True)
        except Exception as e:print('RESERVE_REJECTED '+str(x['id'])+' '+str(e),flush=True)
        finally:dest.unlink(missing_ok=True)
print('RESERVE_SUMMARY '+json.dumps({'usable':len(ok),'total':len(reserves)},ensure_ascii=False),flush=True)
if len(ok)<4:raise SystemExit(3)
