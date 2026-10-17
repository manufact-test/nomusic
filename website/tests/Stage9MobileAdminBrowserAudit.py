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
                finally:
                    browser.close()
        finally:
            server.terminate()
            server.wait(timeout=5)


if __name__ == '__main__':
    main()
