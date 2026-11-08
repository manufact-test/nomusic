#!/usr/bin/env python3
"""Copy the live CELIKOM API release, add the Test.60 catalogue, atomically switch symlink."""
from pathlib import Path
import os, shutil, subprocess, sys, time

def die(message): raise SystemExit(message)
if len(sys.argv)!=4: die("usage: install_test60_catalogue.py ACTIVE_SRC STAGING_DIR RUN_ID")
app=Path(sys.argv[1]).resolve()
stage=Path(sys.argv[2]).resolve()
run_id=sys.argv[3]
if not run_id.isdecimal(): die("Untrusted release run id")
domain=Path.home()/"domains"/"darkred-camel-588676.hostingersite.com"
root=domain/"celikom"
current=root/"current"
releases=root/"releases"
if not current.is_symlink() or not releases.is_dir(): die("CELIKOM immutable release layout not found")
before=current.resolve()
if not before.is_relative_to(releases.resolve()) or app!=before/"src":
    die("Active code does not match verified symlink")
live=app/"Application.php"
staged_app=stage/"Application.php"
staged_service=stage/"ReplacementCatalogueService.php"
for f in (live,staged_app,staged_service):
    if not f.is_file(): die("Missing expected file: "+str(f))
old_text=live.read_text(encoding="utf-8")
candidate=staged_app.read_text(encoding="utf-8")
start="        if ($path === '/api/v1/replacement-catalog') {"
end="        if ($method === 'GET' && $path === '/api/v1/entitlement') {"
if candidate.count(start)!=1 or candidate.count(end)!=1 or old_text.count(end)!=1:
    die("Candidate or live route anchor changed")
route=start+candidate.split(start,1)[1].split(end,1)[0]
if start in old_text:
    die("Existing live catalogue route - refusing to replace another deployment")
if "class Application" not in old_text or "/api/v1/resolve" not in old_text or "BearerAuthenticator" not in old_text:
    die("Unrecognized live CELIKOM API")
next_dir=releases/(before.name+"-test60catalog-"+run_id)
if next_dir.exists(): die("Release already exists: refusing overwrite")
# Clone immutable release. Symlinks (e.g. to shared config) remain symlinks.
shutil.copytree(before,next_dir,symlinks=True)
try:
    target_app=next_dir/"src"/"Application.php"
    target_service=next_dir/"src"/"Application"/"ReplacementCatalogueService.php"
    target_service.parent.mkdir(parents=True,exist_ok=True)
    if target_service.exists(): die("Unexpected existing catalogue service")
    target_service.write_bytes(staged_service.read_bytes())
    target_app.write_text(old_text.replace(end,route+end),encoding="utf-8")
    for f in (target_app,target_service):
        subprocess.run(["php","-l",str(f)],check=True,stdout=subprocess.DEVNULL)
    if current.resolve()!=before: die("Concurrent release: pointer changed; refusing deployment")
    backup=Path.home()/"celikom-private-backups"/("test60-catalog-"+run_id)
    backup.mkdir(parents=True,mode=0o700,exist_ok=False)
    (backup/"previous-release").write_text(str(before)+"\n",encoding="utf-8")
    (backup/"new-release").write_text(str(next_dir)+"\n",encoding="utf-8")
    temp=root/(".test60-current-"+run_id)
    temp.symlink_to(next_dir)
    os.replace(temp,current)
    print("DEPLOYED Test.60 approved catalogue route by atomic release pointer; previous release preserved")
except Exception:
    # The old symlink remains untouched until the final os.replace.
    if current.resolve()==before: shutil.rmtree(next_dir,ignore_errors=True)
    raise
