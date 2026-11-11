"""Build only the approved support delta, never the full historical server tree."""
import hashlib
import json
import pathlib
import subprocess

base = '7e648eacaeb50cc371842590ed7a30284e440d2a'
expected = {
 'src/Application.php':'920a4fa28357a3e61d6af64085448eacc76ea8c3c3c1946597b6428e61b506e0',
 'src/Admin/AdminPanel.php':'e718f0444551984484ac4731722a94988140bf70e88d9e3eee0aeb203c03699f',
 'src/Support/SongReport.php':'3ae387adfdf29a9f6e9ef66ac03b02830e0ef296788f4b9e103cbe124842e2af',
 'src/Support/SupportService.php':'317e853caf8a64457886da30d3b7477715c2ce5ef3381dc5d3bf1df053158ef2',
 'src/Support/SupportAdminView.php':'9b55e8dcd8a9c32f0ab242aa5aaf312b962767513abd5a08e63f833f0210c73b',
 'src/Support/SupportReport.php':None,
 'src/Support/WindowsSupportDiagnostics.php':None,
}
root = pathlib.Path('dist/browser-support-payload')
root.mkdir(parents=True, exist_ok=True)
files = {}
for path, digest in expected.items():
    current = pathlib.Path('server', path).read_text()
    entry = {'before':digest}
    if path in ('src/Application.php', 'src/Admin/AdminPanel.php'):
        old = subprocess.check_output(['git','show',base+':server/'+path]).decode()
        if path=='src/Application.php':
            anchor="                    $data=['ticket_id'=>$support->create((int)$session['user_id'],$data['message'],$data['request_key'],$report)];\n"
            start=current.index('                    $legacyDiagnostics=')
            end=current.index("                }else return Response::json", start)
            new=current[start:end]
            assert old.count(anchor)==1
            assert old.replace(anchor,new)==current, 'Unrelated Application change'
            entry['replace']=[{'old':anchor,'new':new}]
        else:
            pairs = [
             ("            if($thread['kind']!=='song'||!is_array($thread['report']))return Response::json(404,['error'=>'not_found']);\n",
              "            if(!is_array($thread['report']))return Response::json(404,['error'=>'not_found']);\n"),
             ("            $payload=json_encode(['schema'=>'celikom-song-diagnostic-v1','ticket'=>$ticket,\n",
              "            $payload=json_encode(['schema'=>$thread['kind']==='song'?'celikom-song-diagnostic-v1':'celikom-support-diagnostic-v1','ticket'=>$ticket,\n"),
             ("             'Content-Disposition'=>'attachment; filename=\"CELIKOM-song-'.$ticket.'-diagnostics.json\"',\n",
              "             'Content-Disposition'=>'attachment; filename=\"CELIKOM-'.$thread['kind'].'-'.$ticket.'-diagnostics.json\"',\n"),
            ]
            checked=old
            for a,b in pairs:
                assert checked.count(a)==1
                checked=checked.replace(a,b)
            assert checked==current, 'Unrelated AdminPanel change'
            entry['replace']=[{'old':a,'new':b} for a,b in pairs]
    else:
        data=pathlib.Path('server',path).read_bytes()
        entry['after']=hashlib.sha256(data).hexdigest()
        dest=root/path
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
    files[path]=entry
(root/'manifest.json').write_text(json.dumps({'files':files},indent=2))
for name in ('patch.php','smoke.php'):
    (root/name).write_bytes(pathlib.Path('.github/scripts/support-release',name).read_bytes())
print('Support-only payload built; Application/AdminPanel are surgical deltas.')
