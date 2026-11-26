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
import xml.etree.ElementTree as ET
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

ANDROID='{http://schemas.android.com/apk/res/android}'
def summarize_xml(root):
    app=root.find('application')
    default=app.get(ANDROID+'process') if app is not None else None
    services=list(app.findall('service')) if app is not None else []
    def separate(entry):
        p=entry.get(ANDROID+'process',default)
        return bool(p and (p.startswith(':') or
                     (default and p!=default) or
                     p.rsplit(':',1)[-1] in ('player','playback','audio','media','music')))
    media=[x for x in services if MEDIA.search(x.get(ANDROID+'name',''))]
    return dict(
        services=len(services),
        service_explicit_process=sum(x.get(ANDROID+'process') is not None for x in services),
        service_separate_process=sum(separate(x) for x in services),
        media_named_services=len(media),
        media_named_separate_process=sum(separate(x) for x in media),
        media_named_main_process=sum(not separate(x) for x in media),
        application_explicit_process=bool(default))

def inspect(xapk,editor):
    if not xapk.is_file() or not editor.is_file():
        raise ValueError('VERIFIED_INPUT_REQUIRED')
    entries=[]
    with zipfile.ZipFile(xapk) as bundle:
        parts=[x for x in bundle.infolist() if x.filename.endswith('.apk')]
        if not 1<=len(parts)<=32:raise ValueError('SPLIT_COUNT_NOT_PINNED')
        total_splits=len(parts)
        # Main package split is the largest in the fixed verified XAPK.
        # Avoid decoding resource-only config splits in this narrow audit.
        parts=[max(parts,key=lambda part:part.file_size)]
        with tempfile.TemporaryDirectory(prefix='a1-private-topology-') as td:
            for i,part in enumerate(parts):
                if part.file_size>250_000_000:raise ValueError('APK_PART_TOO_LARGE')
                tmp=Path(td)/('part-'+str(i)+'.apk')
                outdir=Path(td)/('decoded-'+str(i))
                with bundle.open(part) as inp,tmp.open('wb') as out:
                    shutil.copyfileobj(inp,out)
                run=subprocess.run(['java','-Xmx1g','-jar',str(editor),
                    'd','-t','xml','-dex','-i',str(tmp),'-o',str(outdir)],
                    capture_output=True,timeout=140)
                if run.returncode!=0:raise ValueError('SIGNED_MANIFEST_DECODE_FAILED')
                manifest=outdir/'AndroidManifest.xml'
                if not manifest.is_file():raise ValueError('MANIFEST_FILE_MISSING')
                entries.append(summarize_xml(ET.parse(manifest).getroot()))
    names=tuple(entries[0].keys())
    out={k:(any(x[k] for x in entries) if k=='application_explicit_process'
         else sum(x[k] for x in entries)) for k in names}
    if out['services']<1:raise ValueError('MAIN_SERVICE_SET_ABSENT')
    out['splits_in_original_xapk']=total_splits
    out['manifests_inspected']=len(entries)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--xapk',required=True,type=Path)
    p.add_argument('--editor',required=True,type=Path)
    args=p.parse_args()
    print('A1_PRIVATE_PROCESS_TOPOLOGY '+json.dumps(inspect(args.xapk,args.editor),
         sort_keys=True),flush=True)
