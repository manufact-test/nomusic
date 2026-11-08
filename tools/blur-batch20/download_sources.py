#!/usr/bin/env python3
"""Download exactly twenty pinned public-source MP3s into disposable runner disk.

No transfer outside explicitly authorized private moderation staging.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from urllib.request import urlopen, Request

BASE = Path(__file__).resolve().parent
MANIFEST = BASE / 'batch20.json'
REPO = 'Hazzz895/FckCensorData'
PINNED = '10187b7af56f311fe141a3c9b75483798bf0f589'
EXPECTED_IDS = ["63104735","137472446","88057589","111402809","136272297","123382745","138778164","155025088","137300017","93401053","63607809","152396542","59357625","138629224","110374527","149870633","30212997","111001121","120305632","63607797"]

def main():
    started = time.monotonic()
    if len(sys.argv) != 2:
        raise ValueError('expected exactly one private output directory argument')
    dest = Path(sys.argv[1]).resolve()
    if not dest.is_dir():
        raise ValueError('missing directory')
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    tracks = manifest['tracks']
    if manifest.get('source_commit') != PINNED or len(tracks) != 20 or [x['id'] for x in tracks] != EXPECTED_IDS:
        raise ValueError('unexpected source or track list')
    for track in tracks:
        tid, size, expected = track['id'], track['size'], track['blob']
        if not isinstance(size, int) or size < 1024 or size > 25_000_000:
            raise ValueError('invalid source size')
        url = f'https://raw.githubusercontent.com/{REPO}/{PINNED}/tracks/{tid}'
        h = hashlib.sha1(b'blob ' + str(size).encode('ascii') + b'\0')
        path = dest / f'{tid}.mp3'
        total = 0
        with urlopen(Request(url, headers={'User-Agent': 'CELIKOM-private-pending-pilot/1.0'}), timeout=35) as response, path.open('xb') as f:
            while True:
                part = response.read(262_144)
                if not part:
                    break
                total += len(part)
                if total > size:
                    raise ValueError(f'source oversized {tid}')
                h.update(part)
                f.write(part)
        if total != size or h.hexdigest() != expected:
            raise ValueError(f'source integrity invalid {tid}')
    print(json.dumps({'status':'SOURCE_VALIDATED','count':20,'total_bytes':sum(x['size'] for x in tracks),'download_seconds':round(time.monotonic()-started,2)}))

if __name__ == '__main__':
    main()