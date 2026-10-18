#!/usr/bin/env python3
"""Isolated local-only HTTP test for CMS auth, CSRF, editing, preview and logout.
CI provides a disposable dedicated MySQL service. No external requests.
"""
from html import unescape
import http.client
import os
import base64
import shutil
import tempfile
from pathlib import Path
import re
import socket
import subprocess
import time
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
with socket.socket() as sock:
    sock.bind(("127.0.0.1",0))
    port=sock.getsockname()[1]
env=dict(os.environ)
env["CELIKOM_LOCAL_ADMIN"]="1"
private_media=tempfile.mkdtemp(prefix="celikom-ci-private-media-")
env["CELIKOM_SITE_MEDIA_DIR"]=private_media
env["CELIKOM_SITE_WRITE_GATE_FILE"]=private_media+"/.celikom-cms-writes.lock"
env.pop("CELIKOM_LOCAL_PREVIEW",None)
server=subprocess.Popen(["php","-S",f"127.0.0.1:{port}","-t",str(ROOT/"public")],
    env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
cookie=""
def request(method,path,form=None):
    global cookie
    conn=http.client.HTTPConnection("127.0.0.1",port,timeout=6)
    headers={"Cookie":cookie} if cookie else {}
    body=None
    if form is not None:
        body=urlencode(form).encode("utf-8")
        headers["Content-Type"]="application/x-www-form-urlencoded"
    conn.request(method,path,body=body,headers=headers)
    reply=conn.getresponse()
    result=reply.read().decode("utf-8")
    status=reply.status
    set_cookie=reply.getheader("Set-Cookie")
    if set_cookie and set_cookie.startswith("celikom_site_admin="):
        cookie=set_cookie.split(";",1)[0]
    headers_out=dict(reply.getheaders())
    conn.close()
    return status,result,headers_out
def upload_image(csrf,alt,data,mime,filename):
    boundary="CelikomPrivateAssetBoundaryStage9"
    def part(name,value):
        return (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n"
        ).encode("utf-8")
    body=part("csrf",csrf)+part("action","media_upload")+part("alt",alt)
    body+=(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8")+data+b"\r\n"+f"--{boundary}--\r\n".encode("ascii")
    conn=http.client.HTTPConnection("127.0.0.1",port,timeout=6)
    conn.request("POST","/admin/",body=body,headers={
        "Cookie":cookie,
        "Content-Type":f"multipart/form-data; boundary={boundary}",
        "Content-Length":str(len(body))
    })
    response=conn.getresponse()
    status=response.status
    response_body=response.read().decode("utf-8")
    location=response.getheader("Location") or ""
    conn.close()
    return status,response_body,location

def hidden(html,name):
    m=re.search(r'name="'+re.escape(name)+r'" value="([^"]*)"',html)
    assert m,(name,html[:800])
    return unescape(m.group(1))
try:
    for attempt in range(40):
        try:
            status,landing,headers=request("GET","/admin/")
            break
        except OSError:
            if attempt==39:
                raise
            time.sleep(.1)
    assert status==200 and "Вход администратора" in landing, (status,landing[:800])
    assert "Сохранить черновик" not in landing
    assert headers.get("X-Robots-Tag","").startswith("noindex")
    csrf=hidden(landing,"csrf")
    # Freeze must reject a real valid-CSRF login BEFORE it can write rate
    # limits or audit; neither login nor editorial changes may cross snapshot.
    import fcntl
    gate_path=Path(env["CELIKOM_SITE_WRITE_GATE_FILE"])
    gate_fd=os.open(gate_path,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
    try:
        fcntl.flock(gate_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        frozen_status,_,frozen_headers=request("POST","/admin/",{
            "action":"login","csrf":csrf,"username":"owner","password":"invalid password"
        })
        assert frozen_status==503 and frozen_headers.get("Retry-After")=="5", (
            "blocked CMS POST executed during protected snapshot",frozen_status
        )
    finally:
        fcntl.flock(gate_fd,fcntl.LOCK_UN)
        os.close(gate_fd)
    bad_status,bad_html,_=request("POST","/admin/",{
        "action":"login","csrf":"wrong","username":"owner","password":"wrong"
    })
    assert bad_status==403 and "Недействительная форма" in bad_html
    status,html,_=request("POST","/admin/",{
        "action":"login","csrf":csrf,"username":"owner","password":"invalid password"
    })
    assert status==200 and "Неверные данные" in html,(status,html[:600])
    csrf=hidden(html,"csrf")
    status,_,headers=request("POST","/admin/",{
        "action":"login","csrf":csrf,"username":"owner",
        "password":"valid-Admin!2026-OnlyForCI"
    })
    assert status==303 and headers.get("Location")=="/admin/",status
    status,editor,headers=request("GET","/admin/")
    assert status==200 and "Сохранить черновик" in editor,(status,editor[:1000])
    assert "Выбери блок, измени текст и сохрани." in editor
    csrf=hidden(editor,"csrf")
    version=hidden(editor,"version")
    fields={}
    for name,value in re.findall(
        r'<textarea id="([^"]+)" name="text\[[^"]+\]" maxlength="\d+">(.*?)</textarea>',
        editor,re.S
    ):
        fields["text["+name+"]"]=unescape(value)
    assert len(fields)==87,len(fields)
    fields["text[faq.text.02]"]="Поддержка и ответы CELIKOM."
    status,_,_=request("POST","/admin/",{
        "action":"save","csrf":csrf,"version":version,**fields
    })
    assert status==303,status
    status,preview,_=request("GET","/admin/?view=preview")
    assert status==200 and "Поддержка и ответы CELIKOM." in preview
    assert preview.count('class="faq-item"')==28
    assert "Пока установка закрыта" in preview
    assert "<script>alert" not in preview
    assert preview.count('<script src=')==2
    status,stale,_=request("POST","/admin/",{
        "action":"save","csrf":csrf,"version":version,**fields
    })
    assert status==409 and "другой вкладке" in stale,(status,stale[:700])
    # FAQ CRUD remains private and versioned; new questions start hidden.
    status,editor,_=request("GET","/admin/")
    assert status==200 and 'id="faq-editor"' in editor
    assert 'name="faq_id" value="faq-question-27"' in editor
    assert "только просмотр" in editor
    faq_version=hidden(editor,"version")
    status,_,headers=request("POST","/admin/",{
        "action":"faq_create","csrf":csrf,"version":faq_version,
        "question":"Как связаться с поддержкой проекта?",
        "answer":"Опишите проблему через доступный канал поддержки.",
        "category":"help"
    })
    assert status==303 and headers.get("Location","").startswith("/admin/?saved=faq"),status
    status,hidden_preview,_=request("GET","/admin/?view=preview")
    assert status==200 and "Как связаться с поддержкой проекта?" not in hidden_preview
    status,editor,_=request("GET","/admin/")
    faq_version=hidden(editor,"version")
    assert 'name="faq_id" value="faq-question-29"' in editor
    status,_,_=request("POST","/admin/",{
        "action":"faq_update","csrf":csrf,"version":faq_version,
        "faq_id":"faq-question-29","question":"Как связаться с поддержкой проекта?",
        "answer":"Напишите в поддержку, указав описание проблемы.",
        "category":"help","sort_order":"290","visible":"1"
    })
    assert status==303,status
    status,visible_preview,_=request("GET","/admin/?view=preview")
    assert status==200 and "Как связаться с поддержкой проекта?" in visible_preview
    assert visible_preview.count('class="faq-item"')==29
    # Protected payment/trial conditions are read-only, even for logged-in owner.
    status,editor,_=request("GET","/admin/")
    faq_version=hidden(editor,"version")
    status,refused,_=request("POST","/admin/",{
        "action":"faq_update","csrf":csrf,"version":faq_version,
        "faq_id":"faq-question-04","question":"Пробный период",
        "answer":"Бесплатно всегда!","category":"start",
        "sort_order":"40","visible":"1"
    })
    assert status==422 and "Проверьте данные FAQ" in refused,(status,refused[:1000])
    status,still_public,_=request("GET","/admin/?view=preview")
    assert still_public.count('class="faq-item"')==29
    # Saving website copy later must preserve all FAQ draft operations.
    status,editor,_=request("GET","/admin/")
    latest_version=hidden(editor,"version")
    all_fields={}
    for name,value in re.findall(
        r'<textarea id="([^"]+)" name="text\[[^"]+\]" maxlength="\d+">(.*?)</textarea>',
        editor,re.S
    ):
        all_fields["text["+name+"]"]=unescape(value)
    assert len(all_fields)==87,len(all_fields)
    all_fields["text[faq.text.02]"]="Ответы редакции CELIKOM."
    status,_,_=request("POST","/admin/",{
        "action":"save","csrf":csrf,"version":latest_version,**all_fields
    })
    assert status==303,status
    status,merged_preview,_=request("GET","/admin/?view=preview")
    assert "Ответы редакции CELIKOM." in merged_preview
    assert "Как связаться с поддержкой проекта?" in merged_preview
    assert merged_preview.count('class="faq-item"')==29
    # An uploaded image remains private, and content-type spoofing is refused.
    sample_png=base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII="
    )
    status,body,_=upload_image(csrf,"Логотип для теста",
        b'<svg onload="alert(1)"></svg>',"image/png","spoof.png")
    assert status==422,(status,body[:500])
    status,body,location=upload_image(csrf,"Тестовая картинка",
        sample_png,"image/png","safe.png")
    assert status==303 and "saved=media" in location,(status,body[:500],location)
    status,editor,_=request("GET","/admin/?saved=media")
    assert "Тестовая картинка" in editor and "safe.png" in editor
    assert "Изображение добавлено в медиатеку" in editor
    assert 'class="section-editor"' in editor
    assert "Публикации и откат" in editor and "История версий" in editor
    assert 'view=media&amp;id=' in editor
    assert editor.count('class="section-editor"') >= 10
    # The private image is available only to the authenticated editor:
    media_id=re.search(r'view=media&amp;id=(\d+)',editor)
    assert media_id,editor[-4000:]
    conn=http.client.HTTPConnection("127.0.0.1",port,timeout=5)
    conn.request("GET","/admin/?view=media&id="+media_id.group(1),
        headers={"Cookie":cookie})
    binary_response=conn.getresponse()
    binary=binary_response.read()
    assert binary_response.status==200 and binary_response.getheader("Content-Type")=="image/png"
    assert binary==sample_png
    assert "no-store" in (binary_response.getheader("Cache-Control") or "")
    conn.close()
    status,draft_html,_=request("GET","/admin/?view=preview")
    assert "safe.png" not in draft_html
    assert "Тестовая картинка" not in draft_html
    assert len([name for name in os.listdir(private_media)
                if name != '.celikom-cms-writes.lock'])==1
    # Publication/restore require CSRF, explicit consent and fresh version.
    status,editor,_=request("GET","/admin/")
    version=hidden(editor,"version")
    assert 'id="revision-editor"' in editor and "Публикации" in editor
    status,rejected,_=request("POST","/admin/",{
        "action":"publish","csrf":csrf,"version":version,"note":"Без согласия"
    })
    assert status==422 and "подтверждение" in rejected
    status,_,headers=request("POST","/admin/",{
        "action":"publish","csrf":csrf,"version":version,
        "note":"Первая локальная публикация","confirm":"yes"
    })
    assert status==303 and "saved=published" in headers.get("Location","")
    status,history,_=request("GET","/admin/")
    assert "Текущая версия:" in history
    first_published=int(re.search(r'Текущая версия:\s*<strong>№(\d+)</strong>',history).group(1))
    assert first_published>0
    status,_,_=request("POST","/admin/",{
        "action":"publish","csrf":csrf,"version":"999999",
        "note":"Старая вкладка","confirm":"yes"
    })
    assert status==409
    # Save a second content state, publish it and restore the first revision.
    status,editor,_=request("GET","/admin/")
    version=hidden(editor,"version")
    current_fields={}
    for name,value in re.findall(
        r'<textarea id="([^"]+)" name="text\[[^"]+\]" maxlength="\d+">(.*?)</textarea>',
        editor,re.S
    ):
        current_fields["text["+name+"]"]=unescape(value)
    current_fields["text[faq.text.02]"]="Новая редакция FAQ."
    status,_,_=request("POST","/admin/",{
        "action":"save","csrf":csrf,"version":version,**current_fields
    })
    assert status==303,status
    status,editor,_=request("GET","/admin/")
    version=hidden(editor,"version")
    status,_,_=request("POST","/admin/",{
        "action":"publish","csrf":csrf,"version":version,
        "note":"Вторая локальная публикация","confirm":"yes"
    })
    assert status==303,status
    status,history,_=request("GET","/admin/")
    second_published=int(re.search(r'Текущая версия:\s*<strong>№(\d+)</strong>',history).group(1))
    assert second_published>first_published
    status,_,_=request("POST","/admin/",{
        "action":"restore","csrf":csrf,"version":str(second_published),
        "target_revision":str(first_published),
        "note":"Вернуть первую","confirm":"yes"
    })
    assert status==303,status
    status,history,_=request("GET","/admin/")
    restored=int(re.search(r'Текущая версия:\s*<strong>№(\d+)</strong>',history).group(1))
    assert restored>second_published and "Вернуть первую" in history
    assert "№"+str(first_published) in history
    # Publication does not clear the current draft even after restoration.
    status,preview,_=request("GET","/admin/?view=preview")
    assert "Новая редакция FAQ." in preview
    status,_,_=request("POST","/admin/",{
        "action":"logout","csrf":csrf
    })
    assert status==303,status
    status,denied_preview,_=request("GET","/admin/?view=media&id="+media_id.group(1))
    assert status==200 and "Вход администратора" in denied_preview
    status,closed,_=request("GET","/admin/?view=preview")
    assert status==200 and "Вход администратора" in closed
    assert "Поддержка и ответы CELIKOM." not in closed
    print("Stage9: owner login, CSRF, draft save, stale conflict, private preview, logout — PASS")
finally:
    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()
    if server.returncode not in (0,-15,None):
        print(server.stderr.read()[-1500:])
    shutil.rmtree(private_media,ignore_errors=True)
