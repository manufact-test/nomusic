#!/usr/bin/env python3
"""Read-only signed APK process topology audit. Output: finite counters only.

Run on the isolated self-hosted CI runner. Never disclose app component names,
process names, app files, IDs, private data, or raw manifests in public logs.
"""
import argparse
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

EVENT = re.compile(r'^(\s*)E: ([\w.:-]+)')
NAME = re.compile(r'^\s*A: android:name(?:\([^)]*\))?=\s*"([^"]*)"')
PROCESS = re.compile(r'^\s*A: android:process(?:\([^)]*\))?=\s*"([^"]*)"')
MEDIA = re.compile(r'player|playback|audio|media|music|stream|radio|session',re.I)
COMPONENTS = {'application','service','receiver','provider','activity'}

def parse_manifest(tree):
    scope=[]
    found=[]
    for line in tree.splitlines():
        element=EVENT.match(line)
        if element:
            depth=len(element.group(1))
            scope=[node for node in scope if node['depth']<depth]
            node={'depth':depth,'tag':element.group(2),'name':'','process':None}
            scope.append(node)
            if node['tag'] in COMPONENTS:found.append(node)
            continue
        if not scope:continue
        name=NAME.match(line)
        if name:scope[-1]['name']=name.group(1)
        process=PROCESS.match(line)
        if process:scope[-1]['process']=process.group(1)
    return found

def summarize(found):
    app=next((x for x in found if x['tag']=='application'),None)
    default=app['process'] if app else None
    services=[x for x in found if x['tag']=='service']
    def separate(x):
        p=x['process'] if x['process'] is not None else default
        return bool(p and (p.startswith(':') or
                     (default and p!=default) or
                     p.rsplit(':',1)[-1] in ('player','playback','audio','media','music')))
    media=[x for x in services if MEDIA.search(x['name'])]
    return dict(
        services=len(services),
        service_explicit_process=sum(x['process'] is not None for x in services),
        service_separate_process=sum(separate(x) for x in services),
        media_named_services=len(media),
        media_named_separate_process=sum(separate(x) for x in media),
        media_named_main_process=sum(not separate(x) for x in media),
        application_explicit_process=bool(default))

def inspect(xapk,aapt2):
    if not xapk.is_file() or not aapt2.is_file():
        raise ValueError('VERIFIED_INPUT_REQUIRED')
    entries=[]
    with zipfile.ZipFile(xapk) as bundle:
        parts=[x for x in bundle.infolist() if x.filename.endswith('.apk')]
        if not 1<=len(parts)<=32:raise ValueError('SPLIT_COUNT_NOT_PINNED')
        with tempfile.TemporaryDirectory(prefix='a1-private-topology-') as td:
            for i,part in enumerate(parts):
                if part.file_size>250_000_000:raise ValueError('APK_PART_TOO_LARGE')
                tmp=Path(td)/('part-'+str(i)+'.apk')
                with bundle.open(part) as inp,tmp.open('wb') as out:
                    shutil.copyfileobj(inp,out)
                run=subprocess.run([str(aapt2),'dump','xmltree',str(tmp),
                    'AndroidManifest.xml'],capture_output=True,timeout=45)
                if run.returncode!=0 or len(run.stdout)>8000000:
                    raise ValueError('MANIFEST_READ_FAILED')
                entries.append(summarize(parse_manifest(run.stdout.decode('utf-8','replace'))))
    names=tuple(entries[0].keys())
    out={k:(any(x[k] for x in entries) if k=='application_explicit_process'
         else sum(x[k] for x in entries)) for k in names}
    out['splits']=len(entries)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--xapk',required=True,type=Path)
    p.add_argument('--aapt2',required=True,type=Path)
    args=p.parse_args()
    print('A1_PRIVATE_PROCESS_TOPOLOGY '+json.dumps(inspect(args.xapk,args.aapt2),
         sort_keys=True),flush=True)
