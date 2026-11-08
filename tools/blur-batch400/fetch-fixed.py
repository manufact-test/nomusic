#!/usr/bin/env python3
"""Verify EXACTLY the pinned 200 source MP3s, then produce two fixed sets of 50.

A cancelled/failed deployment retry always replays these same 200 IDs and can
NEVER accidentally advance into a third/extra batch.
"""
from pathlib import Path
import hashlib
import json
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'blur-batch50'))
from prepare import download, COMMIT

def main():
    if len(sys.argv)!=4:
        raise SystemExit('usage: fetch-fixed.py fixed-plan400.json audio-dir state-dir')
    plan=json.loads(Path(sys.argv[1]).read_text('utf-8'))
    dest=Path(sys.argv[2]).resolve()
    state=Path(sys.argv[3]).resolve()
    records=plan.get('selected')
    if (plan.get('source_commit')!=COMMIT or plan.get('fixed_plan') is not True
        or plan.get('target_pending')!=200 or plan.get('batch_size')!=50
        or not isinstance(records,list) or len(records)!=200):
        raise ValueError('not_a_valid_immutable_hundred')
    if len({e['id'] for e in records})!=200:
        raise ValueError('duplicate IDs in fixed plan')
    if not dest.is_dir() or not state.is_dir() or dest.is_symlink() or state.is_symlink():
        raise ValueError('missing ephemeral output directories')
    started=time.monotonic()
    total=0
    for i,track in enumerate(records,1):
        if not track['id'].isdigit() or len(track['id'])>20:
            raise ValueError('invalid_track_id')
        duration,reason,transient=download(track,dest)
        if reason or transient or duration is None:
            raise RuntimeError(f'pinned_source_now_incompatible_{track["id"]}_{reason}')
        if abs(duration-int(track['duration_ms']))>1500:
            raise RuntimeError(f'pinned_duration_changed_{track["id"]}')
        total+=track['size']
        if i%10==0:print(f'PINNED400_VALIDATED {i}/200',flush=True)
    for batch in (1,2,3,4):
        items=records[(batch-1)*50:batch*50]
        data={'schema':1,'target_pending':50,'source_commit':COMMIT,'selected':items}
        (state/f'selected-{batch}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    status={'status':'PINNED400_SOURCE_VALIDATED','count':200,
            'bytes':total,'source_seconds':round(time.monotonic()-started,2),
            'plan_sha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()}
    (state/'source-status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PINNED400_STATUS '+json.dumps(status,ensure_ascii=False),flush=True)
if __name__=='__main__':
    main()
