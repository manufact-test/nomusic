from pathlib import Path
import json,subprocess
m=json.loads(Path('.github/scripts/admin-search/manifest.json').read_text())
base=subprocess.check_output(['git','show','239ef790e2224fa9ab678a16094b5b2fb096187c:server/src/Admin/AdminPanel.php']).decode()
for pair in m['replace']:
    assert base.count(pair['old'])==1
    base=base.replace(pair['old'],pair['new'])
assert base==Path('server/src/Admin/AdminPanel.php').read_text(), 'Unrelated AdminPanel source change'
print('PASS only search delta against canonical admin; playback and moderation unchanged')
