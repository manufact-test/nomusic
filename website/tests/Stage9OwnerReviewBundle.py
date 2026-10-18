#!/usr/bin/env python3
"""CELIKOM OWNER REVIEW PACK: screenshot the REAL v10 and simple CMS.

Runner-only; requires the disposable website CI MySQL already seeded by
Stage9CmsCoreTest.php. Screenshots contain only synthetic CI data, NEVER live
owner credentials, sessions, backup data, or unapproved private media.

This produces an inspectable HTML gallery + screenshots as a downloadable
GitHub Actions artifact. It does NOT publish a staging or production website.
"""
from __future__ import annotations

import html
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ["CELIKOM_REVIEW_OUTPUT"]).resolve()
FIXTURE = ROOT / "tests" / "Stage9CmsCoreTest.php"


def require_disposable_ci():
    assert os.environ.get("CI") == "true"
    assert os.environ.get("CELIKOM_SITE_DB_HOST") == "127.0.0.1"
    assert os.environ.get("CELIKOM_SITE_DB_NAME") == "celikom_site_test"
    assert OUT != ROOT and ROOT not in OUT.parents
    assert not (ROOT / "public").resolve() in OUT.parents
    assert not OUT.exists() or not any(OUT.iterdir())
    OUT.mkdir(mode=0o700, parents=True, exist_ok=True)
    assert OUT.is_dir()


def take(page, name, *, full=False):
    path = OUT / name
    page.screenshot(path=str(path), full_page=full, animations="disabled")
    assert path.is_file() and path.stat().st_size > 1200, name


def gallery(names):
    cards = "".join(
        '<figure><a href="' + html.escape(image, quote=True) + '">'
        '<img loading="lazy" alt="' + html.escape(title, quote=True) + '" src="'
        + html.escape(image, quote=True) + '"></a><figcaption>'
        + html.escape(title) + '</figcaption></figure>'
        for image, title in names
    )
    page = """<!doctype html><html lang="ru"><meta charset="utf-8">
<title>CELIKOM — пакет визуальной приёмки</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:#f5f7f6;color:#202b29;font:16px/1.6 system-ui,Arial,sans-serif}
header{background:#0b1013;color:#f7f8f4;padding:32px max(18px,calc((100vw - 1100px)/2))}
h1{font-size:clamp(25px,4vw,38px);line-height:1.2}p{max-width:950px}
main{max-width:1140px;margin:auto;padding:24px 18px}
figure{margin:0 0 30px;border:1px solid #dce4df;background:white;border-radius:16px;overflow:hidden}
figure img{display:block;width:100%;height:auto}
figcaption{padding:12px 18px;font-weight:600}
a{color:#086b54}
small{color:#a8c4b9}code{font-size:.92em}
</style>
<header><h1>CELIKOM — просмотр сайта и небольшой админки</h1>
<p>Это фактические снимки из одноразовой GitHub CI: утверждённый сайт v10, вход,
управление текстами/FAQ, мобильный интерфейс и предпросмотр до и после сохранения черновика.
Нажмите изображение, чтобы открыть его в полном размере.</p>
<small>Только синтетические тестовые данные. Не опубликованный сайт. Не логин для пользователей.
Не подключено к Hostinger. Личный доступ для ручных правок организуется отдельно.</small></header>
<main>""" + cards + """<p><strong>Что проверять:</strong> внешний вид, отступы и адаптив;
понятность редактора, настройки FAQ и медиа; удобство мобильной админки;
соответствие текста после сохранения с закрытым предпросмотром.</p>
<p><strong>Что пока невозможно в этом пакете:</strong> интерактивно редактировать CMS
через Интернет. Файлы — снимки, а не живой сервер. Реальный личный тестовый доступ
создадим только после согласования безопасной staging-среды.</p>
</main></html>"""
    (OUT / "ОТКРЫТЬ-ПРОСМОТР.html").write_text(page, encoding="utf-8")
    (OUT / "README.txt").write_text(
        "CELIKOM: пакет визуальной приёмки сайта и небольшой CMS.\n"
        "Откройте ОТКРЫТЬ-ПРОСМОТР.html двойным щелчком и просмотрите изображения.\n"
        "Компьютер и телефон, вход, редактирование и FAQ сняты с настоящего PHP/MySQL"
        " только в одноразовой CI.\n"
        "Это НЕ размещённый сайт и НЕ интерактивная админка. Тестовые логины,"
        " пароли, пользовательские файлы, ключи и cookies НЕ включены.\n"
        "Запрещено выкладывать скриншоты в GitHub source/public_html.\n",
        encoding="utf-8",
    )


def main():
    require_disposable_ci()
    fixture = FIXTURE.read_text(encoding="utf-8")
    found = re.search(r"password_hash\('([^']+)'", fixture)
    assert found, "Synthetic CI password absent"
    password = found.group(1)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="celikom-owner-review-") as private:
        env = os.environ.copy()
        env["CELIKOM_LOCAL_ADMIN"] = "1"
        env["CELIKOM_LOCAL_PREVIEW"] = "1"
        env["CELIKOM_SITE_MEDIA_DIR"] = private
        env["CELIKOM_SITE_WRITE_GATE_FILE"] = private + "/.celikom-cms-writes.lock"
        process = subprocess.Popen(
            ["php", "-S", f"127.0.0.1:{port}", "-t", str(ROOT / "public")],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(0.7)
            names = []
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
                try:
                    desktop = browser.new_context(
                        viewport={"width": 1440, "height": 900}, device_scale_factor=1
                    )
                    page = desktop.new_page()
                    response = page.goto(base + "/", wait_until="networkidle")
                    assert response.status == 200, "Local v10 HTML not served"
                    assert "CELIKOM" in page.title()
                    take(page, "01-сайт-десктоп.png", full=True)
                    names.append(("01-сайт-десктоп.png", "1. Утверждённый сайт CELIKOM v10 · компьютер 1440px"))

                    page.set_viewport_size({"width": 390, "height": 844})
                    page.reload(wait_until="networkidle")
                    assert page.evaluate("document.documentElement.scrollWidth") <= 392
                    take(page, "02-сайт-телефон.png", full=True)
                    names.append(("02-сайт-телефон.png", "2. Утверждённый сайт v10 · телефон 390px"))
                    page.set_viewport_size({"width": 1440, "height": 900})

                    response = page.goto(base + "/admin/", wait_until="domcontentloaded")
                    assert response.status == 200
                    assert page.get_by_role("heading", name="Вход администратора").is_visible()
                    take(page, "03-вход-в-админку.png")
                    names.append(("03-вход-в-админку.png", "3. Вход в небольшую CMS"))

                    page.get_by_label("Логин").fill("owner")
                    page.get_by_label("Пароль").fill(password)
                    page.get_by_role("button", name="Войти").click()
                    assert page.get_by_role("heading", name="Обзор сайта").is_visible()
                    assert page.locator("#text-editor textarea").count() == 87
                    # Clear password from memory-backed form by navigating after login.
                    page.reload(wait_until="domcontentloaded")
                    take(page, "04-редактор-десктоп.png")
                    names.append(("04-редактор-десктоп.png", "4. Рабочий стол новой CELIKOM CMS"))

                    page.set_viewport_size({"width": 390, "height": 844})
                    page.reload()
                    assert page.locator("#text-editor").count() == 1
                    take(page, "05-редактор-телефон.png")
                    names.append(("05-редактор-телефон.png", "5. Адаптивный рабочий стол CMS на телефоне"))
                    page.set_viewport_size({"width": 1440, "height": 900})
                    page.reload()
                    page.locator('.cms-side-menu a[data-cms-link="faq-editor"]').click()
                    take(page, "06-редактор-faq.png")
                    names.append(("06-редактор-faq.png", "6. Раздел управления FAQ"))
                    page.locator('.cms-side-menu a[data-cms-link="media-editor"]').click()
                    take(page, "07-редактор-изображений.png")
                    names.append(("07-редактор-изображений.png", "7. Управление приватными изображениями"))

                    response = page.goto(base + "/admin/?view=preview", wait_until="networkidle")
                    assert response.status == 200
                    take(page, "08-предпросмотр-до.png", full=True)
                    names.append(("08-предпросмотр-до.png", "8. Закрытый предпросмотр до изменения"))
                    page.goto(base + "/admin/")
                    page.locator('.cms-side-menu a[data-cms-link="text-editor"]').click()
                    page.locator('button[data-cms-group-select="faq"]').click()
                    field = page.locator('textarea[name="text[faq.text.02]"]')
                    assert field.count() == 1
                    detail = page.locator("details.section-editor").filter(has=field)
                    assert detail.count() == 1
                    assert detail.is_visible() and detail.get_attribute("open") is not None
                    field.fill("CELIKOM — демонстрация изменения текста через небольшую CMS.")
                    page.locator("#text-editor").get_by_role(
                        "button", name="Сохранить черновик"
                    ).click()
                    assert page.get_by_text("Изменения сохранены.").is_visible()
                    response = page.goto(base + "/admin/?view=preview", wait_until="networkidle")
                    assert response.status == 200
                    assert "демонстрация изменения текста через небольшую CMS." in page.content()
                    take(page, "09-предпросмотр-после.png", full=True)
                    names.append(("09-предпросмотр-после.png", "9. Предпросмотр после сохранения тестового текста"))
                    gallery(names)
                    # Smoke-check that output contains no test secret or cookie.
                    assert password not in (OUT / "ОТКРЫТЬ-ПРОСМОТР.html").read_text()
                    assert all(p.stat().st_size > 0 for p in OUT.iterdir())
                finally:
                    browser.close()
        finally:
            process.terminate()
            process.wait(timeout=6)
    print("Owner review: 9 real site/CMS screenshots + Russian offline gallery; "
          "edited FAQ draft and protected preview verified — PASS")


if __name__ == "__main__":
    main()
