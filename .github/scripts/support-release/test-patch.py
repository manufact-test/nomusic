"""Exercise patch/reversal, unknown-live-source refusal and current protection."""
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import hashlib

payload=pathlib.Path('dist/browser-support-payload').resolve()
manifest=json.loads((payload/'manifest.json').read_text())
with tempfile.TemporaryDirectory(prefix='celikom-support-patch-test-') as temp:
    root=pathlib.Path(temp)
    for name,entry in manifest['files'].items():
        dest=root/name
        if entry['before'] is not None:
            data=subprocess.check_output(['git','show','7e648eacaeb50cc371842590ed7a30284e440d2a:server/'+name])
            # Simulate an unrelated existing native-client customization.
            if name in ('src/Application.php','src/Admin/AdminPanel.php'):
                data=data.replace(b'<?php\n',b'<?php\n// Existing live customization must survive.\n',1)
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(data)
            entry['before']=hashlib.sha256(data).hexdigest()
    fixture=root/'manifest.json'
    fixture.write_text(json.dumps(manifest))
    originals={n:(root/n).read_bytes() for n,e in manifest['files'].items() if e['before'] is not None}
    env={**os.environ,'APP_ENV':'test'}
    subprocess.run(['php',str(payload/'patch.php'),str(root),str(payload),str(fixture)],env=env,check=True)
    for name,entry in manifest['files'].items():
        actual=(root/name).read_text()
        if 'replace' in entry:
            assert 'Existing live customization must survive.' in actual
            restored=actual
            for pair in reversed(entry['replace']):restored=restored.replace(pair['new'],pair['old'])
            assert restored.encode()==originals[name]
        else:assert hashlib.sha256((root/name).read_bytes()).hexdigest()==entry['after']
    # Reapplication/changed source must fail before another candidate write.
    unchanged={n:(root/n).read_bytes() for n in manifest['files']}
    bad=subprocess.run(['php',str(payload/'patch.php'),str(root),str(payload),str(fixture)],env=env,capture_output=True)
    assert bad.returncode!=0 and b'live_source_changed' in bad.stderr
    assert all((root/n).read_bytes()==data for n,data in unchanged.items())
print('Support surgical patch tests PASS: unrelated source preserved; reverse proof; stale source refused.')
