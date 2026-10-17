#!/usr/bin/env python3
"""Browser-level CMS accessibility audit; runs only against isolated CI MySQL."""
from pathlib import Path
import os
import socket
import subprocess
import tempfile
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def assert_layout(page, width):
    """Check horizontal overflow, offscreen controls and touch targets."""
    page.wait_for_load_state('domcontentloaded')
    dimensions = page.evaluate("""() => ({
      doc: document.documentElement.scrollWidth,
      body: document.body.scrollWidth,
      viewport: document.documentElement.clientWidth
    })""")
    assert dimensions['doc'] <= width + 1 and dimensions['body'] <= width + 1, (
        f"Mobile horizontal overflow at {width}: {dimensions}"
    )
    controls = page.locator(
        'main button, main select, main .secnav a, main details > summary, '
        'main input:not([type=hidden]):not([type=checkbox])'
    )
    for idx in range(controls.count()):
        element = controls.nth(idx)
        if not element.is_visible():
            continue
        rect = element.bounding_box()
        if rect is None:
            continue
        name = element.get_attribute('name') or element.get_attribute('id') or element.evaluate(
            '(el) => el.textContent.slice(0,70)'
        )
        assert rect['x'] >= -1 and rect['x'] + rect['width'] <= width + 1, (
            f"Offscreen control {name!r} at {width}: {rect}"
        )
        if width <= 390:
            assert rect['height'] >= 43.9, (
                f"Undersized touch target {name!r} at {width}: {rect['height']}"
            )


def exercise_authenticated_admin(page, base):
    """Actual mobile browser interactions, not only HTTP response inspection."""
    # Recover the deliberately disposable test fixture from its seed script.
    # Avoid a second copy of the credential and never query production.
    import re
    fixture = (ROOT/'tests'/'Stage9CmsCoreTest.php').read_text()
    match = re.search(r"password_hash\('([^']+)'", fixture)
    assert match, 'Disposable CI owner fixture missing'
    password = match.group(1)
    page.get_by_label('Логин').fill('owner')
    page.get_by_label('Пароль').fill(password)
    page.get_by_role('button', name='Войти').click()
    assert page.get_by_role('heading', name='Черновик текстов').is_visible()
    assert page.locator('#text-editor textarea').count() == 87

    for width in (320, 390, 768, 1024):
        page.set_viewport_size({'width': width, 'height': 780})
        page.reload()
        assert page.locator('#media-editor').count() == 1
        assert_layout(page, width)

    page.set_viewport_size({'width': 320, 'height': 720})
    field = page.locator('textarea[name="text[faq.text.02]"]')
    section = page.locator('details.section-editor').filter(has=field)
    assert section.count() == 1
    if section.get_attribute('open') is None:
        section.locator('summary').click()
    field.fill('Ответы на вопросы CELIKOM — мобильный QA.')
    page.locator('#text-editor').get_by_role('button', name='Сохранить черновик').click()
    assert page.get_by_text('Черновик сохранён в базе данных.').is_visible()
    assert_layout(page, 320)

    response = page.goto(base + '/admin/?view=preview')
    assert response.status == 200
    assert 'Ответы на вопросы CELIKOM — мобильный QA.' in page.content()
    page.goto(base + '/admin/')

    question = 'Как работает мобильная проверка CELIKOM?'
    new_faq = page.locator('#faq-editor form').last
    new_faq.locator('input[name="question"]').fill(question)
    new_faq.locator('textarea[name="answer"]').fill(
        'Это вопрос только для изолированного браузерного теста.'
    )
    new_faq.locator('select[name="category"]').select_option('help')
    new_faq.get_by_role('button', name='Добавить скрытый вопрос в черновик').click()
    assert page.get_by_text('Черновик сохранён в базе данных.').is_visible()
    entry = page.locator('#faq-editor details.faq-entry').filter(has_text=question)
    assert entry.count() == 1
    entry.locator('summary').click()
    entry.locator('input[name="visible"]').check()
    entry.get_by_role('button', name='Сохранить вопрос в черновик').click()
    page.goto(base + '/admin/?view=preview')
    assert question in page.content()
    page.goto(base + '/admin/')

    # Upload in the real mobile form. The media remains outside public_html.
    import base64
    png = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+pS1kAAAAASUVORK5CYII='
    )
    upload = page.locator('#media-editor form[enctype="multipart/form-data"]')
    upload.locator('input[type="file"]').set_input_files({
        'name': 'mobile-check.png', 'mimeType': 'image/png', 'buffer': png
    })
    upload.locator('input[name="alt"]').fill('Тестовый popup мобильной админки')
    upload.get_by_role('button', name='Сохранить приватно').click()
    assert page.get_by_text('Изображение сохранено приватно.', exact=False).is_visible()
    select = page.locator('#media-pending-id')
    # Latest asset is first after "original". Previous HTTP test temp files
    # were removed, so using an older stored ID would correctly fail SHA checks.
    newest = select.locator('option').nth(1).get_attribute('value')
    assert newest and newest.isdecimal()
    select.select_option(newest)
    page.get_by_role('button', name='Сохранить выбор только для предпросмотра').click()
    assert page.get_by_text(
        'Для закрытого предпросмотра выбрано изображение.', exact=False
    ).is_visible()
    assert_layout(page, 320)

    response = page.goto(base + '/admin/?view=preview')
    assert response.status == 200
    image = page.locator('img[data-managed-media="celikom.popup.approved"]')
    assert image.count() == 1
    assert image.get_attribute('src') == f'/admin/?view=media&id={newest}'
    assert image.get_attribute('alt') == 'Тестовый popup мобильной админки'
    image.scroll_into_view_if_needed()
    assert image.evaluate('(el) => el.complete && el.naturalWidth === 1')

    # Explicit owner action restores the original for the private preview.
    page.goto(base + '/admin/')
    page.locator('#media-pending-id').select_option('original')
    page.get_by_role('button', name='Сохранить выбор только для предпросмотра').click()
    page.goto(base + '/admin/?view=preview')
    assert page.locator('img[data-managed-media="celikom.popup.approved"]').get_attribute(
        'src'
    ) == '/media/celikom-popup-approved.png'

    page.goto(base + '/admin/')
    page.get_by_role('button', name='Выйти').click()
    assert page.get_by_role('heading', name='Вход администратора').is_visible()
    response = page.goto(base + '/admin/?view=preview')
    assert response.status == 200
    assert page.get_by_role('heading', name='Вход администратора').is_visible()
    print('Stage9 mobile browser: 320/390/768/1024, login, controls, draft, '
          'FAQ, private popup media, restore original and logout — PASS')


def main():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix='celikom-mobile-media-') as storage:
        env = dict(os.environ)
        env['CELIKOM_LOCAL_ADMIN'] = '1'
        env['CELIKOM_SITE_MEDIA_DIR'] = storage
        server = subprocess.Popen(['php', '-S', f'127.0.0.1:{port}', '-t', str(ROOT/'public')], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            time.sleep(0.5)
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, args=['--no-sandbox'])
                try:
                    page = browser.new_page(viewport={'width': 320, 'height': 720})
                    response = page.goto(f'http://127.0.0.1:{port}/admin/')
                    assert response.status == 200
                    assert page.get_by_role('heading', name='Вход администратора').is_visible()
                    assert_layout(page, 320)
                    exercise_authenticated_admin(page, f'http://127.0.0.1:{port}')
                finally:
                    browser.close()
        finally:
            server.terminate()
            server.wait(timeout=5)


if __name__ == '__main__':
    main()
