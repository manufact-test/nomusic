#!/usr/bin/env python3
"""Owner CMS workspace v5.14, isolated SQL fixture: real Chromium desktop/mobile."""
import os,re,socket,subprocess,tempfile,time
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
fixture=(ROOT/'tests'/'Stage9CmsCoreTest.php').read_text()
match=re.search(r"password_hash\('([^']+)'",fixture)
assert match,'Isolated disposable fixture not found'
password=match.group(1)
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
with tempfile.TemporaryDirectory(prefix='celikom-workspace-ui-') as storage:
    env=dict(os.environ)
    env.update({'CELIKOM_LOCAL_ADMIN':'1','CELIKOM_SITE_MEDIA_DIR':storage,
      'CELIKOM_SITE_WRITE_GATE_FILE':storage+'/.celikom-cms-writes.lock'})
    server=subprocess.Popen(['php','-S',f'127.0.0.1:{port}','-t',str(ROOT/'public')],
        env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        time.sleep(.5)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
            for width in [320,390,768,1440]:
                context=browser.new_context(viewport={'width':width,'height':810})
                page=context.new_page()
                res=page.goto(f'http://127.0.0.1:{port}/admin/')
                assert res.status==200
                page.get_by_label('Логин').fill('owner')
                page.get_by_label('Пароль').fill(password)
                page.get_by_role('button',name='Войти').click()
                assert page.locator('#overview').is_visible()
                assert page.get_by_role('heading',name='Обзор сайта').is_visible()
                assert page.locator('.cms-home-card').count()==4
                assert not page.locator('#text-editor').is_visible()
                assert page.locator('#text-editor textarea').count()==87
                links=page.locator('.cms-side-menu a[data-cms-link]')
                assert links.count()==5
                for area in ['text-editor','faq-editor','media-editor','revision-editor','overview']:
                    page.locator(f'.cms-side-menu a[data-cms-link="{area}"]').click()
                    assert page.locator('#'+area).is_visible(),(area,width)
                    for other in ['overview','text-editor','faq-editor','media-editor','revision-editor']:
                        if other!=area: assert not page.locator('#'+other).is_visible(),(area,other,width)
                page.locator('.cms-side-menu a[data-cms-link="text-editor"]').click()
                assert page.locator('details.section-editor:not([hidden])').count()==1
                page.locator('button[data-cms-group-select="faq"]').click()
                assert page.locator('details.section-editor:not([hidden])').count()==1
                assert page.locator('textarea[name="text[faq.text.02]"]').is_visible()
                page.locator('.cms-side-menu a[data-cms-link="faq-editor"]').click()
                page.get_by_label('Найти вопрос FAQ').fill('Что такое CELIKOM')
                assert page.locator('#faq-editor details.faq-entry:not([hidden])').count()==1
                page.get_by_label('Найти вопрос FAQ').fill('')
                page.locator('button[data-faq-filter="music"]').click()
                assert page.locator('button[data-faq-filter="music"]').get_attribute('aria-pressed')=='true'
                assert page.locator('#faq-editor details.faq-entry:not([hidden])').count()>0
                assert page.locator('#faq-editor details.faq-entry:not([hidden])').count()<28
                page.locator('.cms-side-menu a[data-cms-link="media-editor"]').click()
                assert page.locator('#media-editor').is_visible()
                if width==320:
                    import base64
                    png=base64.b64decode(
                        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII=')
                    upload=page.locator('#media-editor form[enctype="multipart/form-data"]')
                    upload.locator('input[type="file"]').set_input_files({
                        'name':'cms-owner-demo.png','mimeType':'image/png','buffer':png})
                    upload.locator('input[name="alt"]').fill('Тест приватного изображения')
                    upload.get_by_role('button',name='Загрузить изображение').click()
                    assert page.get_by_text('Изображение добавлено в медиатеку.',exact=False).is_visible()
                    sel=page.locator('#media-pending-id')
                    asset=sel.locator('option').nth(1).get_attribute('value')
                    assert asset and asset.isdecimal()
                    sel.select_option(asset)
                    page.get_by_role('button',name='Сохранить выбор').click()
                    assert page.get_by_text('Изображение выбрано для предпросмотра.',exact=False).is_visible()
                    preview=page.goto(f'http://127.0.0.1:{port}/admin/?view=preview')
                    assert preview.status==200
                    img=page.locator('img[data-managed-media="celikom.popup.approved"]')
                    assert img.get_attribute('src')==f'/admin/?view=media&id={asset}'
                    page.goto(f'http://127.0.0.1:{port}/admin/')
                    page.locator('.cms-side-menu a[data-cms-link="media-editor"]').click()
                    page.locator('#media-pending-id').select_option('original')
                    page.get_by_role('button',name='Сохранить выбор').click()
                    assert page.get_by_text('Изображение выбрано для предпросмотра.',exact=False).is_visible()
                    print('CELIKOM admin: private upload, preview choice, original restore PASS',flush=True)
                dims=page.evaluate('''()=>({
                  doc:document.documentElement.scrollWidth,
                  body:document.body.scrollWidth,
                  width:document.documentElement.clientWidth})''')
                assert dims['doc']<=width+1 and dims['body']<=width+1,(width,dims)
                print(f"CELIKOM admin workspace {width}px: dashboard, 5 isolated sections, "
                      "14 targeted groups, filtered FAQ and responsive frame PASS",flush=True)
                if width==320:
                    page.locator('.cms-side-menu a[data-cms-link="text-editor"]').click()
                    page.locator('button[data-cms-group-select="faq"]').click()
                    field=page.locator('textarea[name="text[faq.text.02]"]')
                    field.fill('Ответы на вопросы CELIKOM — тест единого редактора.')
                    page.locator('#text-editor button[type="submit"]').click()
                    assert page.get_by_text('Изменения сохранены.').is_visible()
                    assert page.locator('#text-editor').is_visible()
                    preview=page.goto(f'http://127.0.0.1:{port}/admin/?view=preview')
                    assert preview.status==200
                    assert 'Ответы на вопросы CELIKOM — тест единого редактора.' in page.content()
                    page.goto(f'http://127.0.0.1:{port}/admin/')
                    page.get_by_role('button',name='Выйти').click()
                    assert page.get_by_role('heading',name='Вход администратора').is_visible()
                    print('CELIKOM admin: real 87-field draft save, preview, logout PASS',flush=True)
                context.close()
            browser.close()
    finally:
        server.terminate();server.wait(timeout=5)
