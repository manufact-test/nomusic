#!/usr/bin/env python3
"""Download exactly 50 owner-requested source files for private pending moderation.
Never uses Yandex credentials, updates production, or infers rights.
"""
import hashlib,json,pathlib,sys,time,urllib.request,subprocess
if len(sys.argv)!=3:raise SystemExit('usage: fetch.py audio-dir state-dir')
audio=pathlib.Path(sys.argv[1]).resolve()
state=pathlib.Path(sys.argv[2]).resolve()
assert audio.is_dir() and state.is_dir() and not audio.is_symlink()
data=json.loads(pathlib.Path('tools/blur-research/pending34-20261109.json').read_text(encoding='utf-8'))
rows=data['selected']
assert data['source_commit']=='multisource-20261109' and len(rows)==34 and len(set(r['id'] for r in rows))==34
assert sum(r['size'] for r in rows)<500000000
for i,r in enumerate(rows,1):
 tid=r['id']
 assert tid.isdigit() and r['source_url'].startswith(('https://raw.githubusercontent.com/','https://huggingface.co/'))
 assert len(r['sha256'])==64 and 1024<=r['size']<=25000000
 path=audio/(tid+'.mp3')
 success=False
 for attempt in range(3):
  try:
   h=hashlib.sha256();total=0
   req=urllib.request.Request(r['source_url'],headers={'User-Agent':'CELIKOM-multisource-owner-pending'})
   with urllib.request.urlopen(req,timeout=70) as source,path.open('wb') as dest:
    while chunk:=source.read(262144):
     total+=len(chunk)
     if total>r['size']:raise ValueError('oversize '+tid)
     h.update(chunk);dest.write(chunk)
   if total!=r['size'] or h.hexdigest()!=r['sha256']:raise ValueError('SHA256_MISMATCH '+tid)
   f=subprocess.run(['file','-b','--mime-type',str(path)],capture_output=True,text=True,check=True,timeout=20).stdout.strip()
   p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration,format_name','-of','json',str(path)],capture_output=True,text=True,check=True,timeout=50)
   j=json.loads(p.stdout)['format'];ms=round(float(j['duration'])*1000)
   if f!='audio/mpeg' or 'mp3' not in j['format_name'] or abs(ms-r['duration_ms'])>1500:raise ValueError('INVALID_MP3 '+tid)
   success=True;break
  except (OSError,TimeoutError) as exc:
   if attempt==2:raise
   time.sleep(2+attempt)
 if not success:raise RuntimeError('failed '+tid)
 if i%10==0:print('SOURCE50_VERIFIED',i,'of',len(rows),flush=True)
batch={'schema':2,'source_commit':'multisource-20261109','target_pending':len(rows),'selected':rows}
(state/'selected-1.json').write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(state/'source-status.json').write_text(json.dumps({'status':'PASS','verified':34,'bytes':sum(r['size'] for r in rows),'rights_verified':False},ensure_ascii=False),encoding='utf-8')
print('SOURCE34_PASS count=34 no_rights_confirmation',flush=True)
