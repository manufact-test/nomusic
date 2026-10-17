#!/usr/bin/env python3
"""Isolated local-only HTTP test for CMS auth, CSRF, editing, preview and logout.
CI provides a disposable dedicated MySQL service. No external requests.
"""
from html import unescape
import http.client
import os
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
    assert "Публикация пока недоступна" in editor
    csrf=hidden(editor,"csrf")
    version=hidden(editor,"version")
    fields={}
    for name,value in re.findall(
        r'<textarea id="([^"]+)" name="text\[[^"]+\]" maxlength="\d+">(.*?)</textarea>',
        editor,re.S
    ):
        fields["text["+name+"]"]=unescape(value)
    assert len(fields)==84,len(fields)
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
    assert "защищённый текст" in editor
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
    assert len(all_fields)==84,len(all_fields)
    all_fields["text[faq.text.02]"]="Ответы редакции CELIKOM."
    status,_,_=request("POST","/admin/",{
        "action":"save","csrf":csrf,"version":latest_version,**all_fields
    })
    assert status==303,status
    status,merged_preview,_=request("GET","/admin/?view=preview")
    assert "Ответы редакции CELIKOM." in merged_preview
    assert "Как связаться с поддержкой проекта?" in merged_preview
    assert merged_preview.count('class="faq-item"')==29
    status,_,_=request("POST","/admin/",{
        "action":"logout","csrf":csrf
    })
    assert status==303,status
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
