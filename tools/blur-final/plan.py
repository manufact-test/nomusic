#!/usr/bin/env python3
"""Non-mutating plan for one fixed, reproducible 200-song private pending upload.

Uses the tested batch50 downloader/strict verifier; fills failures from reserves.
Only emits a proposed manifest. Production upload is a DIFFERENT workflow and
MUST pin this exact manifest in GitHub first.
"""
import csv
from datetime import date
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'blur-batch50'))
from prepare import download, SOURCE, COMMIT, FIELDS

def main():
    if len(sys.argv)!=5:
        raise SystemExit('usage: plan.py candidates.json readonly-precheck.json audio-dir state-dir')
    candidates=json.loads(Path(sys.argv[1]).read_text('utf-8'))
    checked=json.loads(Path(sys.argv[2]).read_text('utf-8'))
    out=Path(sys.argv[3]).resolve()
    state=Path(sys.argv[4]).resolve()
    if not out.is_dir() or not state.is_dir() or out.is_symlink() or state.is_symlink():
        raise RuntimeError('unsafe temporary directories')
    if candidates.get('target_pending')!=200 or candidates['source_commit']!=COMMIT or len(candidates['candidates'])<300 or checked.get('status')!='READ_ONLY' or checked.get('writes')!=0:
        raise RuntimeError('missing verified source or live deduplication')
    source={e['id']:e for e in candidates['candidates']}
    with Path('docs/research/BLUR-REJECTED-CUMULATIVE.csv').open(newline='',encoding='utf-8') as f:
        known=list(csv.DictReader(f))
    rejected_ids={row['track_id'] for row in known}
    if len(known)!=len(rejected_ids) or len(rejected_ids)!=93:
        raise RuntimeError('cumulative_rejected_list_changed')
    eligible=[tid for tid in checked['eligible'] if tid not in rejected_ids]
    print('FINAL_ELIGIBILITY '+json.dumps({'live_eligible':len(checked['eligible']),'known_rejected_filtered':len(checked['eligible'])-len(eligible),'to_try':len(eligible)},separators=(',',':')),flush=True)
    if len(eligible)!=len(set(eligible)) or not all(i in source for i in eligible):
        raise RuntimeError('invalid deduplication output')
    begun=time.monotonic()
    chosen=[];rejected=[];temporary=[];name_seen=set();duplicates=[];attempts=0
    for tid in eligible:
        entry=source[tid]
        label=(' '.join(entry['artist'].lower().split()),' '.join(entry['title'].lower().split()))
        if label in name_seen:
            duplicates.append({'id':tid,'reason':'same_title_artist_in_fixed_plan'})
            continue
        attempts+=1
        duration,issue,transient=download(entry,out)
        if issue:
            r={
                'track_id':tid,'artist':entry['artist'],'title':entry['title'],
                'status':'retry_later' if transient else 'needs_manual_audio',
                'attempt':'final_sweep_plan','failure_code':issue,
                'source_commit':COMMIT,
                'source_audio_url':f'https://github.com/{SOURCE}/blob/{COMMIT}/tracks/{tid}',
                'yandex_url':f'https://music.yandex.ru/track/{tid}',
                'run_url':f"https://github.com/manufact-test/nomusic/actions/runs/{os.getenv('GITHUB_RUN_ID','local')}",
                'manual_resolution':'not_found','checked_at':date.today().isoformat()}
            (temporary if transient else rejected).append(r)
            path=out/(tid+'.mp3')
            if path.is_file():path.unlink()
            print('FINAL_REJECTED '+json.dumps(r,ensure_ascii=False,separators=(',',':')),flush=True)
            continue
        name_seen.add(label)
        item=dict(entry)
        item['duration_ms']=duration
        chosen.append(item)
        print(f'FINAL_SELECTED {len(chosen)}/200 {tid}',flush=True)
    with (state/'rejected-new.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,FIELDS,quoting=csv.QUOTE_ALL)
        w.writeheader();w.writerows(rejected)
    (state/'retry-later.json').write_text(json.dumps(temporary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (state/'skipped-live.json').write_text(json.dumps(checked['skipped']+duplicates,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    full={'schema':1,'purpose':'read-only inventory of all remaining candidates; no upload without a later fixed plan','source_repository':SOURCE,
          'source_commit':COMMIT,'selected':chosen,'target_pending':len(chosen),'batch_size':50,
          'original_duration_verified':False,'fixed_plan':True}
    (state/'fixed-final.json').write_text(json.dumps(full,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    stats={'status':'PREPARED_READ_ONLY','count':len(chosen),'attempts':attempts,
           'technical_rejected':len(rejected),'temporary_failures':len(temporary),
           'known_rejected_filtered':len(checked['eligible'])-len(eligible),
           'candidate_collisions':len(duplicates),'live_skipped':len(checked['skipped']),
           'total_bytes':sum(x['size'] for x in chosen),
           'seconds':round(time.monotonic()-begun,1),'production_writes':0}
    (state/'planning-summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('FINAL_SUMMARY '+json.dumps(stats,ensure_ascii=False,separators=(',',':')),flush=True)
    if not chosen:
        print('FINAL_NO_VALID_CANDIDATES',flush=True)
    # Emit one compact, machine-readable JSON line to pin the plan via GitHub.
    print('FINAL_FIXED_JSON '+json.dumps(full,ensure_ascii=False,separators=(',',':')),flush=True)

if __name__=='__main__':
    main()
