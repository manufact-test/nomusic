"""Independent Android-only full source + addon/Test*.java host gate.
Run after pinned dependencies have been validated; no signing or API calls.
Requires Android SDK platform 36 in GitHub Actions; local fake-only use may skip.
"""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent.parent
SDK=Path(os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT') or '/usr/local/lib/android/sdk')
ANDROID=SDK/'platforms/android-36/android.jar'
if not ANDROID.is_file():
    if os.environ.get('GITHUB_ACTIONS')=='true':
        raise SystemExit('Mandatory Android Test* host gate requires android-36/android.jar')
    print('SKIP: SDK 36 not present locally; Android Test* gate remains mandatory in CI')
    raise SystemExit(0)
names=['annotation.jar','common.jar','guava.jar','session.jar']
deps=[ROOT/'deps'/name for name in names]
json=ROOT/'deps/json.jar'
for item in [*deps,json]:
    if not item.is_file():
        raise SystemExit('Missing pinned dependency: '+str(item))
with tempfile.TemporaryDirectory(prefix='celikom-android-full-host-') as temp:
    out=Path(temp);classes=out/'classes';classes.mkdir()
    tests=out/'testclasses';tests.mkdir()
    main_sources=sorted((ROOT/'addon/src').rglob('*.java'))
    check_sources=sorted((ROOT/'addon').glob('Test*.java'))
    assert len(main_sources)>15 and len(check_sources)>=15
    full_cp=os.pathsep.join(str(x) for x in [ANDROID,*deps])
    subprocess.run(['java','com.sun.tools.javac.Main','-encoding','UTF-8','-source','8','-target','8','-cp',full_cp,'-d',str(classes),*map(str,main_sources)],check=True)
    unit_cp=os.pathsep.join(str(x) for x in [json,classes,ANDROID])
    subprocess.run(['java','com.sun.tools.javac.Main','-encoding','UTF-8','-source','8','-target','8','-cp',unit_cp,'-d',str(tests),*map(str,check_sources)],check=True)
    run_cp=os.pathsep.join(str(x) for x in [json,classes,tests,ANDROID])
    for item in check_sources:
        clazz='pro.celikom.nativeprobe.identitydiag.'+item.stem
        subprocess.run(['java','-cp',run_cp,clazz],check=True)
    print('PASS: '+str(len(check_sources))+' native addon/Test*.java host gates, full Android source compile')
