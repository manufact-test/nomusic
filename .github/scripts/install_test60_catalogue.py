#!/usr/bin/env python3
"""Atomic narrow CELIKOM Test.60 catalogue API installer. Run on verified owner hosting only."""
from pathlib import Path
import os, shutil, subprocess, sys, tempfile, time

def die(message):
    raise SystemExit(message)

if len(sys.argv)!=3:
    die("usage: install_test60_catalogue.py LIVE_APP_SRC STAGING_DIR")
app=Path(sys.argv[1]).resolve()
stage=Path(sys.argv[2]).resolve()
expected_domain="darkred-camel-588676.hostingersite.com"
if expected_domain not in app.parts or app.name!="src":
    die("Refusing ambiguous app location")
live=app/"Application.php"
new=app/"Application"/"ReplacementCatalogueService.php"
staged_app=stage/"Application.php"
staged_service=stage/"ReplacementCatalogueService.php"
for file in (live,staged_app,staged_service):
    if not file.is_file():
        die("Required file missing: "+str(file))
old_text=live.read_text(encoding="utf-8")
candidate=staged_app.read_text(encoding="utf-8")
start="        if ($path === '/api/v1/replacement-catalog') {"
end="        if ($method === 'GET' && $path === '/api/v1/entitlement') {"
if candidate.count(start)!=1 or candidate.count(end)!=1:
    die("Candidate route delimiters absent/ambiguous")
if old_text.count(end)!=1:
    die("Live PHP route anchor absent/ambiguous")
route=start+candidate.split(start,1)[1].split(end,1)[0]
if start in old_text:
    if route not in old_text:
        die("Unknown existing catalogue endpoint - manual audit required")
    print("Existing catalogue endpoint already matches candidate")
    sys.exit(0)
if "class Application" not in old_text or "/api/v1/resolve" not in old_text or "BearerAuthenticator" not in old_text:
    die("Live PHP code does not match expected CELIKOM API")
if new.exists():
    die("Service already exists without route; stop for manual audit")
patched=old_text.replace(end,route+end)
if patched==old_text or patched.count(start)!=1:
    die("Atomic insert failed")
work=Path(tempfile.mkdtemp(prefix="celikom-test60-",dir=str(live.parent)))
try:
    temp_app=work/"Application.php"
    temp_service=work/"ReplacementCatalogueService.php"
    temp_app.write_text(patched,encoding="utf-8")
    shutil.copyfile(staged_service,temp_service)
    for f in (temp_app,temp_service):
        subprocess.run(["php","-l",str(f)],check=True,stdout=subprocess.DEVNULL)
    backup=Path.home()/"celikom-private-backups"/("test60-"+str(int(time.time())))
    backup.mkdir(parents=True,mode=0o700,exist_ok=False)
    shutil.copy2(live,backup/"Application.php")
    try:
        new.parent.mkdir(parents=True,exist_ok=True)
        os.replace(temp_service,new)
        os.replace(temp_app,live)
        subprocess.run(["php","-l",str(live)],check=True,stdout=subprocess.DEVNULL)
        subprocess.run(["php","-l",str(new)],check=True,stdout=subprocess.DEVNULL)
    except Exception:
        shutil.copy2(backup/"Application.php",live)
        if new.exists():
            new.unlink()
        raise
    print("DEPLOYED: catalogue endpoint and metadata service; rollback backup in private home")
finally:
    shutil.rmtree(work,ignore_errors=True)
