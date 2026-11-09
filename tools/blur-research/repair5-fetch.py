#!/usr/bin/env python3
"""Download originals, transcode to deterministic MP3 and verify all 5 against pinned output SHA256.
Only ephemeral CI files; separate importer does private pending after preflight.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,urllib.request,time
if len(sys.argv)!=3:raise SystemExit('usage: fetch-repaired5.py audio state')
dest=Path(sys.argv[1]).resolve();state=Path(sys.argv[2]).resolve()
m=json.loads(Path('tools/blur-research/repair5-pending.json').read_text(encoding='utf8'))
rows=m['selected']
assert len(rows)==5 and len({r['id'] for r in rows})==5 and m['target_pending']==5
assert dest.is_dir() and state.is_dir()
for r in rows:
 tid=r['id'];src=dest/(tid+'.source');out=dest/(tid+'.mp3')
 try:
  for attempt in range(3):
   try:
    with urllib.request.urlopen(urllib.request.Request(r['source_url'],headers={'User-Agent':'CELIKOM-repaired-owner-pending'}),timeout=65) as stream,src.open('wb') as f:
     blob=stream.read(r['source_size']+1);f.write(blob)
    break
   except (OSError,TimeoutError):
    if attempt==2:raise
    time.sleep(3)
  assert len(blob)==r['source_size'],f'source_size_mismatch_{tid}'
  sha256=hashlib.sha256(blob).hexdigest()
  if 'source_sha256' in r:assert sha256==r['source_sha256'],f'source_hash_mismatch_{tid}'
  if 'source_git_blob' in r:
   assert hashlib.sha1(b'blob '+str(len(blob)).encode()+b'\0'+blob).hexdigest()==r['source_git_blob'],f'git_blob_mismatch_{tid}'
  run=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y','-i',str(src),'-map','0:a:0','-vn','-c:a','libmp3lame','-b:a','192k','-ar','44100','-id3v2_version','3',str(out)],capture_output=True,text=True,timeout=120)
  assert run.returncode==0,(tid,run.stderr[-250:])
  assert out.stat().st_size==r['size'],f'encoded_size_changed_{tid}'
  assert hashlib.sha256(out.read_bytes()).hexdigest()==r['sha256'],f'encoded_sha256_changed_{tid}'
  php='require "server/bootstrap.php"; $d=(new Celikom\\Application\\Mp3Inspector())->durationMs($argv[1]);echo $d===null?"null":$d;'
  check=subprocess.run(['php','-r',php,str(out)],text=True,capture_output=True,timeout=60)
  duration=int(check.stdout) if check.stdout.isdigit() else None
  assert duration and abs(duration-r['duration_ms'])<=1500,f'server_inspector_fail_{tid}'
  print('REPAIRED5_VERIFIED',tid,'bytes',r['size'],'duration_ms',duration,flush=True)
 finally:
  src.unlink(missing_ok=True)
(state/'selected-1.json').write_text(json.dumps({'schema':2,'source_commit':'multisource-20261109','target_pending':5,'selected':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(state/'source-status.json').write_text(json.dumps({'status':'PASS','repaired':5,'rights_verified':False},indent=2)+'\n',encoding='utf8')
