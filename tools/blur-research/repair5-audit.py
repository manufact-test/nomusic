#!/usr/bin/env python3
"""Read-only check: transcode 2 ffprobe-readable but strict-invalid MP3 + 3 WebM.
No uploads; no rights assumptions. Report technical output and integrity.
"""
import json,hashlib,subprocess,tempfile,pathlib,urllib.request,time
SOURCES=[
('39580348','Овсянкин feat. Вертушка Газманова','Тебя прёт габба','https://raw.githubusercontent.com/Hazzz895/FckCensorData/10187b7af56f311fe141a3c9b75483798bf0f589/tracks/39580348','4ae0d6d6c857a8112b037ea740cd30ebdc9789b991ea13b655287edebcc2cefa',8831610),
('136404135','ПОШЛАЯ МОЛЛИ','Школа Не Нужна','https://raw.githubusercontent.com/Hazzz895/FckCensorData/10187b7af56f311fe141a3c9b75483798bf0f589/tracks/136404135','bd4aa3081fd914cf577dfd2c9b6d38a0798391cf9ec9acd549775cf6287ad5e2',3772370),
('144998587','NEXTIME','СВЕТЛАНА!','https://raw.githubusercontent.com/kotzillac/FckCensorData/main/tracks/144998587',None,1674805),
('145242788','паранойя','ALASKA PUFFER 2','https://raw.githubusercontent.com/kotzillac/FckCensorData/main/tracks/145242788',None,1751252),
('146150936','NEXTIME','АНТИСВЕТЛАНА','https://raw.githubusercontent.com/kotzillac/FckCensorData/main/tracks/146150936',None,1708187)
]
rows=[]
with tempfile.TemporaryDirectory() as td:
 for id,artist,title,url,sha,size in SOURCES:
  src=pathlib.Path(td)/(id+'.source')
  dest=pathlib.Path(td)/(id+'.mp3')
  rec={'id':id,'artist':artist,'title':title,'source':url,'size_original_expected':size,'status':'unverified'}
  try:
   for attempt in range(3):
    try:
     with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CELIKOM-owner-repair-audit'}),timeout=60) as r:
      data=r.read(25000001)
     break
    except (OSError,TimeoutError):
     if attempt==2:raise
     time.sleep(3)
   assert len(data)==size,(id,len(data))
   if sha:assert hashlib.sha256(data).hexdigest()==sha,id
   src.write_bytes(data)
   orig=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration,format_name:stream=codec_name,codec_type','-of','json',str(src)],text=True,capture_output=True,timeout=25)
   if orig.returncode!=0:raise RuntimeError('source_probe:'+orig.stderr[:180])
   info=json.loads(orig.stdout)
   audio=[s for s in info.get('streams',[]) if s.get('codec_type')=='audio']
   if not audio:raise RuntimeError('no_audio_stream')
   duration=float(info['format']['duration'])
   cmd=['ffmpeg','-hide_banner','-nostdin','-loglevel','error','-y','-i',str(src),'-map','0:a:0','-vn','-c:a','libmp3lame','-b:a','192k','-ar','44100','-id3v2_version','3',str(dest)]
   process=subprocess.run(cmd,text=True,capture_output=True,timeout=100)
   if process.returncode:raise RuntimeError('transcode:'+process.stderr[-400:])
   p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration,format_name','-of','json',str(dest)],text=True,capture_output=True,timeout=25)
   output=json.loads(p.stdout)['format'];trans_duration=float(output['duration'])
   php='require "server/bootstrap.php"; $d=(new Celikom\\Application\\Mp3Inspector())->durationMs($argv[1]); echo $d===null?"null":$d;'
   z=subprocess.run(['php','-r',php,str(dest)],text=True,capture_output=True,timeout=60)
   ms=int(z.stdout) if z.stdout.isdigit() else None
   rec.update({'source_codec':audio[0].get('codec_name'),'original_duration_ms':round(duration*1000),'encoded_duration_ms':round(trans_duration*1000),'inspector_ms':ms,'encoded_size':dest.stat().st_size,'encoded_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'duration_diff_ms':round(abs(trans_duration-duration)*1000)})
   rec['status']='repaired_mp3_valid' if ms and abs(ms-trans_duration*1000)<=1500 and abs(trans_duration-duration)<1.5 and dest.stat().st_size<25000000 else 'rejected_after_transcode'
  except Exception as e:rec.update({'status':'technical_failure','error':str(e)[:350]})
  rows.append(rec)
  print('REPAIR5 '+json.dumps(rec,ensure_ascii=False),flush=True)
out={'summary':{'checked':5,'repaired':sum(r['status']=='repaired_mp3_valid' for r in rows),'writes':0,'rights_verified':False},'records':rows}
pathlib.Path('repair5-audio-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print('REPAIR5_SUMMARY '+json.dumps(out['summary']),flush=True)
