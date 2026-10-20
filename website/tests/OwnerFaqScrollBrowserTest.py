#!/usr/bin/env python3
"""Verify branded FAQ scrollbar on genuine v10 owner render at 320px/390px."""
import pathlib,subprocess,tempfile,time,socket
from playwright.sync_api import sync_playwright
root=pathlib.Path(__file__).resolve().parents[1]
site=root/'public'
cmd=["php","-r","""require 'website/app/bootstrap.php';
$base='website/';
$t=file_get_contents($base.'app/Templates/site-v10.html');
$m=file_get_contents($base.'app/Config/content-fields-v10.json');
$f=file_get_contents($base.'database/seeds/faq-v10.json');
$html=\\Celikom\\Website\\CmsEditor::validate($t,$m,$f,['content'=>[],'faq'=>[]]);
echo \\Celikom\\Website\\CmsV10OwnerMotion::apply($html);"""]
with tempfile.NamedTemporaryFile(dir=site,prefix='qa-faq-',suffix='.html',delete=False) as temp:
    temp.write(subprocess.check_output(cmd,cwd=root.parent))
    name=pathlib.Path(temp.name)
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
server=subprocess.Popen(['php','-S',f'127.0.0.1:{port}','-t',str(site)],
    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    time.sleep(.4)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
        for width in (320,390,1440):
            page=browser.new_page(viewport={'width':width,'height':820})
            response=page.goto(f'http://127.0.0.1:{port}/{name.name}')
            assert response.status==200
            nav=page.locator('#faq .faq-nav')
            indicator=page.locator('#faq .celikom-faq-track')
            assert nav.count()==1 and indicator.count()==1
            if width<=540:
                assert indicator.is_visible()
                assert nav.evaluate('el=>getComputedStyle(el).scrollbarWidth')=='none'
                before=page.locator('#faq .celikom-faq-thumb').evaluate('el=>el.style.transform')
                nav.evaluate('el=>el.scrollLeft=el.scrollWidth-el.clientWidth')
                page.wait_for_timeout(130)
                after=page.locator('#faq .celikom-faq-thumb').evaluate('el=>el.style.transform')
                assert before!=after,(width,before,after)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            else:
                assert not indicator.is_visible()
            print(f'FAQ branded scrollbar {width}px PASS',flush=True)
            page.close()
        browser.close()
finally:
    server.terminate();server.wait(timeout=5)
    name.unlink(missing_ok=True)
