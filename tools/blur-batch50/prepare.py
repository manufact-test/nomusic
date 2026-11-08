#!/usr/bin/env python3
"""Pinned public source -> exactly 50 technically verified MP3s in ephemeral CI.

No production credentials here; never uploads or publishes anything.
Bad files are recorded, and replacement candidates are tried in source order.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import Request, urlopen
from datetime import date

SOURCE = 'Hazzz895/FckCensorData'
COMMIT = '10187b7af56f311fe141a3c9b75483798bf0f589'
FIELDS = ['track_id','artist','title','status','attempt','failure_code','source_commit',
          'source_audio_url','yandex_url','run_url','manual_resolution','checked_at']

def valid_mp3(path: Path) -> tuple[int | None, str | None]:
    mime = subprocess.run(['file','-b','--mime-type',str(path)],
                          capture_output=True,text=True,timeout=15,check=True).stdout.strip()
    if mime != 'audio/mpeg':
        return None, 'mime_'+mime.replace('/','_')
    php = subprocess.run(['php','-r',
         'require "server/bootstrap.php";$x=(new Celikom\\Application\\Mp3Inspector())->durationMs($argv[1]);echo $x===null?"":$x;',
         str(path)],capture_output=True,text=True,timeout=60,check=True)
    if not php.stdout.strip().isdigit():
        return None,'mp3_inspector_rejected'
    ms=int(php.stdout.strip())
    probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                          '-of','default=noprint_wrappers=1:nokey=1',str(path)],
                         capture_output=True,text=True,timeout=60)
    try:
        measured=round(float(probe.stdout.strip())*1000)
        if measured<1000 or measured>86400000 or abs(measured-ms)>1500:
            return None,'ffprobe_duration_discrepancy'
    except (ValueError,OverflowError):
        return None,'ffprobe_unavailable'
    return ms,None

def download(entry: dict, out: Path) -> tuple[int | None,str | None, bool]:
    tid,size,blob=entry['id'],entry['size'],entry['blob']
    url=f'https://raw.githubusercontent.com/{SOURCE}/{COMMIT}/tracks/{tid}'
    if not (isinstance(size,int) and 1024<=size<=25_000_000 and isinstance(blob,str) and len(blob)==40):
        return None,'invalid_manifest_metadata',False
    path=out/(tid+'.mp3')
    transient=None
    for retry in range(3):
        transient=None
        h=hashlib.sha1(b'blob '+str(size).encode('ascii')+b'\0')
        received=0
        try:
            with urlopen(Request(url,headers={'User-Agent':'CELIKOM-private-batch50/1.0'}),timeout=45) as response, path.open('xb') as file:
                while block:=response.read(262144):
                    received+=len(block)
                    if received>size: raise ValueError('size_overshoot')
                    h.update(block);file.write(block)
            if received!=size or h.hexdigest()!=blob:
                return None,'source_size_or_blob_sha_mismatch',False
            duration,reason=valid_mp3(path)
            if reason: return None,reason,False
            return duration,None,False
        except ValueError:
            return None,'source_size_or_blob_sha_mismatch',False
        except (OSError,subprocess.SubprocessError) as error:
            transient=type(error).__name__
            if retry<2: time.sleep(1+retry*2)
        finally:
            if (path.exists() and (received!=size or transient is not None)):
                path.unlink()
    return None,'temporary_download_or_probe_'+(transient or 'error'),True

def main() -> None:
    if len(sys.argv)!=5: raise SystemExit('usage: prepare.py manifest precheck output_dir state_dir')
    manifest=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    precheck=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
    out=Path(sys.argv[3]).resolve()
    state=Path(sys.argv[4]).resolve()
    if not out.is_dir() or not state.is_dir() or out.is_symlink() or state.is_symlink():
        raise ValueError('output must be temporary existing directories')
    if (manifest.get('source_commit')!=COMMIT or manifest.get('target_pending')!=50
            or precheck.get('status')!='READ_ONLY' or precheck.get('writes')!=0):
        raise ValueError('unpinned manifest or missing live read-only precheck')
    byid={e['id']:e for e in manifest['candidates']}
    eligible=precheck['eligible']
    if len(eligible)!=len(set(eligible)) or any(i not in byid for i in eligible):
        raise ValueError('inconsistent eligible Track IDs')
    started=time.monotonic()
    ready=[];bad=[];temporary=[];total=0;attempted=0
    for tid in eligible:
        if len(ready)>=50: break
        entry=byid[tid];attempted+=1
        duration,why,is_transient=download(entry,out)
        if why:
            record={'track_id':tid,'artist':entry['artist'],'title':entry['title'],
                'status':'retry_later' if is_transient else 'needs_manual_audio',
                'attempt':'batch50','failure_code':why,'source_commit':COMMIT,
                'source_audio_url':f'https://github.com/{SOURCE}/blob/{COMMIT}/tracks/{tid}',
                'yandex_url':f'https://music.yandex.ru/track/{tid}',
                'run_url':f"https://github.com/manufact-test/nomusic/actions/runs/{__import__('os').environ.get('GITHUB_RUN_ID','local')}",
                'manual_resolution':'not_found','checked_at':date.today().isoformat()}
            (temporary if is_transient else bad).append(record)
            print('SKIPPED_CANDIDATE '+json.dumps({'id':tid,'reason':why,'transient':is_transient},ensure_ascii=False),flush=True)
            path=out/(tid+'.mp3')
            if path.exists(): path.unlink()
            continue
        e=dict(entry)
        e['duration_ms']=duration
        e['original_duration_verified']=False
        ready.append(e)
        total+=entry['size']
    rejected_csv=state/'rejected-new.csv'
    with rejected_csv.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,FIELDS,quoting=csv.QUOTE_ALL)
        writer.writeheader();writer.writerows(bad)
    (state/'retry-later.json').write_text(json.dumps(temporary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (state/'duplicates.json').write_text(json.dumps(precheck['skipped'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (state/'selected.json').write_text(json.dumps({
        'schema':1,'source_commit':COMMIT,'target_pending':50,'selected':ready
    },ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary={'source':'pinned','eligible':len(eligible),'attempted':attempted,'technical_rejected':len(bad),
        'temporary_errors':len(temporary),'selected_count':len(ready),'bytes':total,
        'download_and_validate_seconds':round(time.monotonic()-started,2)}
    (state/'prepare-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print('SOURCE_PREPARATION_SUMMARY '+json.dumps(summary,ensure_ascii=False),flush=True)
    for record in bad:
        print('SOURCE_REJECTED_JSON '+json.dumps(record,ensure_ascii=False),flush=True)
    if len(ready)!=50:
        raise RuntimeError(f'only_{len(ready)}_technically_valid_candidates_available; no production upload')
if __name__=='__main__':
    main()
