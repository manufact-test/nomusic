#!/usr/bin/env python3
"""Fail-closed site AND admin until joint Stage 10 release (never deploy)."""
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

BASE=Path(__file__).resolve().parents[1]
PUBLIC=BASE/"public"
assert not (BASE/"RELEASE_READY").exists()
assert not (BASE/"celikom-private/app/release-approved.php").exists()
assert (PUBLIC/"admin/index.php").is_file()
with socket.socket() as sock:
    sock.bind(("127.0.0.1",0))
    port=sock.getsockname()[1]
env=dict(os.environ)
env.pop("CELIKOM_LOCAL_ADMIN",None)
env.pop("CELIKOM_LOCAL_PREVIEW",None)
server=subprocess.Popen(
    ["php","-S",f"127.0.0.1:{port}","-t",str(PUBLIC)],
    cwd=BASE,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for path in ("/","/admin/"):
        for attempt in range(40):
            try:
                with urlopen(f"http://127.0.0.1:{port}{path}",timeout=2) as response:
                    raise AssertionError(f"{path} unexpectedly returned {response.status}")
            except HTTPError as error:
                assert error.code == 503, (path,error.code)
                page=error.read().decode("utf-8")
                assert "CELIKOM" in page or "Панель" in page, (path,page[:100])
                assert error.headers.get("X-Robots-Tag","").startswith("noindex")
                break
            except (URLError,TimeoutError):
                if attempt == 39:
                    raise
                time.sleep(0.1)
    print("Stage9: / and /admin/ remain 503/noindex without Stage 10 authorization — PASS")
finally:
    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()
