#!/usr/bin/env python3
"""Compare official 30s Apple previews with owner-authorized library file.

Network read-only; all media is scratch-only, not persisted or uploaded.
"""
import json
import pathlib
import subprocess
import urllib.request
import numpy as np
from scipy.signal import fftconvolve

root=pathlib.Path(__file__).resolve().parent
source=pathlib.Path(__import__('sys').argv[1])
assert source.is_file() and source.stat().st_size>1_000_000
def pcm(path,rate=8000):
    p=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-i',str(path),'-map','0:a:0','-ac','1','-ar',str(rate),'-f','f32le','pipe:1'])
    a=np.frombuffer(p,dtype='<f4').copy()
    # high-pass pre-emphasis reduces spurious correlation from bass
    a[1:]-=.95*a[:-1].copy()
    return a

def locate(full,small):
    result=fftconvolve(full,small[::-1],mode='valid')
    energy=fftconvolve(full*full,np.ones(len(small),dtype=np.float32),mode='valid')
    denominator=np.sqrt(np.maximum(energy,1e-12)*np.sum(small*small))
    normalized=result/denominator
    index=int(np.argmax(abs(normalized)))
    return round(index/8000,2),round(float(normalized[index]),4)

full=pcm(source)
print(json.dumps({'library_duration':round(len(full)/8000,3),'source':'read-only verified exact track 144530503'}))
for track in [1747791012,1853026725]:
    try:
        request=urllib.request.Request(f'https://itunes.apple.com/lookup?id={track}&country=us&entity=song',
                                      headers={'User-Agent':'CELIKOM-staging-audio-verification/1.0'})
        with urllib.request.urlopen(request,timeout=25) as response:data=json.load(response)
        entry=(data.get('results') or [{}])[-1]
        preview=entry.get('previewUrl')
        if not isinstance(preview,str) or not preview.startswith('https://'):
            print(json.dumps({'track':track,'result':'NO_PREVIEW'}));continue
        dest=source.parent/(str(track)+'.m4a')
        urllib.request.urlretrieve(preview,dest)
        small=pcm(dest)
        at,r=locate(full,small)
        duration=len(small)/8000
        print(json.dumps({'track':track,'title':entry.get('trackName'),
          'preview_duration':round(duration,3),
          'match_to_library_at_second':at,'normalized_audio_correlation':r,
          'covers_43_to_54':at<=43 and at+duration>=54,
          'source_duration_ms':entry.get('trackTimeMillis')},ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({'track':track,'failure':type(exc).__name__,'detail':str(exc)[:120]}))
