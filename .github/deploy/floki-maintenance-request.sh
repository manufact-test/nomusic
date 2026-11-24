#!/bin/bash
set -Eeuo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
SITE=/etc/nginx/sites-enabled/celikom-site-https
[[ -f "$SITE" ]]
SITE_REAL=$(readlink -f "$SITE")
[[ "$SITE_REAL" == /etc/nginx/sites-available/* ]]
backup=$(mktemp -d /root/celikom-downloads-backup.XXXXXXXX)
cp -a "$SITE_REAL" "$backup/site.conf"
echo '=== ROOT-OWNED PRIVATE DOWNLOADS ==='
install -d -o root -g www-data -m 750 /srv/celikom-releases/owner-downloads
python3 - <<'PY'
import pathlib,os,stat,hashlib,shutil,tempfile,json
root=pathlib.Path("/srv/celikom-releases")
target=root/"owner-downloads"
for p in [pathlib.Path("/srv"),root,target]:
    st=p.lstat()
    assert stat.S_ISDIR(st.st_mode) and st.st_uid==0 and not st.st_mode & 0o022
for src,name,expected in [
    (root/"windows/stable/versions/0.24.55/CELIKOM-Windows-0.24.55.exe","CELIKOM-Windows-0.24.55.exe","f4c9a7881164ac7a9b5681d9f3568e5cbd3a9915c9e1da7b475caa20d3fb6487"),
    (root/"private/extension/celikom-extension-0.4.73.zip","celikom-extension-0.4.73.zip","968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb"),
]:
    assert stat.S_ISREG(src.lstat().st_mode) and src.lstat().st_uid==0 and hashlib.file_digest(src.open("rb"),"sha256").hexdigest()==expected
    dst=target/name
    if dst.exists() or dst.is_symlink():
        s=dst.lstat()
        assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_nlink==1 and not s.st_mode & 0o022 and hashlib.file_digest(dst.open("rb"),"sha256").hexdigest()==expected
    else:
        fd,tmp=tempfile.mkstemp(dir=target)
        try:
            with os.fdopen(fd,"wb") as f,src.open("rb") as original:
                shutil.copyfileobj(original,f)
                f.flush()
                os.fsync(f.fileno())
            os.link(tmp,dst)
        finally:
            os.unlink(tmp)
    shutil.chown(dst,user="root",group="www-data")
    os.chmod(dst,0o640)
print("OWNER_RELEASE_FILES_READY")
PY
python3 - "$SITE_REAL" <<'PY'
import pathlib,sys,re,os,tempfile
p=pathlib.Path(sys.argv[1]);s=p.read_text()
begin="# BEGIN CELIKOM OWNER DOWNLOADS";end="# END CELIKOM OWNER DOWNLOADS"
assert 'auth_basic "CELIKOM private review";' in s and "auth_basic_user_file" in s
if begin in s:
    assert s.count(begin)==1 and s.count(end)==1
    s=re.sub(r"(?ms)^    "+re.escape(begin)+r".*?^    "+re.escape(end)+r"\n","",s)
needle="    location / {"
assert s.count(needle)==1
routes="""    # BEGIN CELIKOM OWNER DOWNLOADS
    location = /downloads/windows/CELIKOM-Windows-0.24.55.exe {
        alias /srv/celikom-releases/owner-downloads/CELIKOM-Windows-0.24.55.exe;
        default_type application/octet-stream;
        add_header Content-Disposition 'attachment; filename="CELIKOM-Windows-0.24.55.exe"' always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        add_header Cache-Control "private, no-store" always;
        access_log off;
        limit_except GET { deny all; }
    }
    location = /downloads/extension/celikom-extension-0.4.73.zip {
        alias /srv/celikom-releases/owner-downloads/celikom-extension-0.4.73.zip;
        default_type application/zip;
        add_header Content-Disposition 'attachment; filename="celikom-extension-0.4.73.zip"' always;
        add_header X-Robots-Tag "noindex, nofollow" always;
        add_header Cache-Control "private, no-store" always;
        access_log off;
        limit_except GET { deny all; }
    }
    # END CELIKOM OWNER DOWNLOADS
"""
data=s.replace(needle,routes+needle)
st=p.stat()
fd,tmp=tempfile.mkstemp(dir=p.parent)
with os.fdopen(fd,"w") as f: f.write(data)
os.chown(tmp,st.st_uid,st.st_gid);os.chmod(tmp,st.st_mode&0o777)
os.replace(tmp,p)
PY
rollback(){ cp -a "$backup/site.conf" "$SITE_REAL"; nginx -t && systemctl reload nginx; }
if ! nginx -t || ! systemctl reload nginx; then rollback; exit 1; fi
# Verify real public unauthenticated denial and filesystem access by nginx.
if ! (
  set -e
  for p in / /admin/ /downloads/windows/CELIKOM-Windows-0.24.55.exe /downloads/extension/celikom-extension-0.4.73.zip; do
    code=$(curl --max-time 15 -sS -o /dev/null -w '%{http_code}' "https://celikom.com$p")
    [[ "$code" == 401 ]]
    printf '%s anonymous=%s\n' "$p" "$code"
  done
  runuser -u www-data -- test -r /srv/celikom-releases/owner-downloads/CELIKOM-Windows-0.24.55.exe
  runuser -u www-data -- test -r /srv/celikom-releases/owner-downloads/celikom-extension-0.4.73.zip
); then rollback; exit 1; fi
echo CELIKOM_OWNER_DOWNLOAD_ROUTES_READY
echo '=== ANDROID PRIVATE BUILD INPUT ==='
python3 - <<'PY'
import pathlib,hashlib,stat,os,tempfile,shutil
src=pathlib.Path("/srv/celikom/migration/sites-20261124/android-private/android-build-inputs/CELIKOM-0.3.22-install.apk")
root=pathlib.Path("/srv/celikom-releases/private")
assert stat.S_ISDIR(root.lstat().st_mode) and root.lstat().st_uid==0 and root.lstat().st_mode&0o077==0
target=root/"android-build-inputs";target.mkdir(mode=0o700,exist_ok=True)
assert stat.S_ISDIR(target.lstat().st_mode) and target.lstat().st_uid==0 and target.lstat().st_mode&0o077==0
expected="170b1883e292570d28a3b5c619cf000eaccd9d11ee85ca6f6c08f7b50e5f72c9"
assert stat.S_ISREG(src.lstat().st_mode) and hashlib.file_digest(src.open("rb"),"sha256").hexdigest()==expected
dst=target/src.name
if dst.exists() or dst.is_symlink():
    assert stat.S_ISREG(dst.lstat().st_mode) and dst.lstat().st_uid==0 and dst.lstat().st_mode&0o077==0 and hashlib.file_digest(dst.open("rb"),"sha256").hexdigest()==expected
else:
    fd,tmp=tempfile.mkstemp(dir=target)
    try:
        with os.fdopen(fd,"wb") as f,src.open("rb") as original:
            shutil.copyfileobj(original,f)
            f.flush();os.fsync(f.fileno())
        assert hashlib.file_digest(open(tmp,"rb"),"sha256").hexdigest()==expected
        os.link(tmp,dst)
    finally:
        os.unlink(tmp)
print("ANDROID_BASE_PRIVATE_STORAGE_READY",dst.stat().st_size)
PY
echo '=== CUTOVER SOURCE CONFIG PREPARATION ==='
# Verify known site credential file structure without showing values.
python3 - <<'PY'
import pathlib
p=pathlib.Path("/srv/celikom/migration/sites-20261124/android-private/staging-owner-credentials.txt")
assert p.is_file()
for line in p.read_text().splitlines():
    if "=" in line: print("credential_field",line.split("=",1)[0].strip()[:80])
    elif ":" in line: print("credential_field",line.split(":",1)[0].strip()[:80])
PY
echo CELIKOM_DOWNLOAD_PREPARATION_OK
