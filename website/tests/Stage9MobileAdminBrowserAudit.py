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
    # The credential is CI-only and seeded by Stage9CmsCoreTest.php.
    # It is not read from a production secret or connected Hostinger.
    password = os.environ['CELIKOM_CI_OWNER_PASSWORD']
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
