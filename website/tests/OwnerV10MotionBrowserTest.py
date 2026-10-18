#!/usr/bin/env python3
"""Chromium smoke: approved v10 layout, unique header anchors and smooth FAQ close."""
import http.server
import pathlib
import socketserver
import subprocess
import threading
import time
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = ROOT / "public" / "owner-motion-review.html"
HTML.write_bytes(subprocess.check_output(["php", str(ROOT / "tests" / "OwnerV10MotionFixture.php")]))
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

class Serving(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

try:
    with Serving(("127.0.0.1", 0), lambda *args, **kwargs: Quiet(*args, directory=str(ROOT/"public"), **kwargs)) as srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/owner-motion-review.html"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for width, height in [(1440, 900), (390, 844)]:
                page = browser.new_page(viewport={"width":width, "height":height},
                                        reduced_motion="no-preference")
                page.goto(url, wait_until="networkidle")
                assert page.locator("header nav a").count() == 2
                assert page.locator("header nav a").evaluate_all(
                    "es=>es.map(x=>[x.textContent.trim(),x.getAttribute('href')])"
                ) == [["Участие","#contribute"],["Вопросы","#faq"]]
                assert page.locator(".header-chip").get_attribute("href") == "#install"
                assert page.locator(".familiar-orbit svg.celikom-familiar-c path").get_attribute("d") == "M92 40 A36 36 0 1 0 92 88"
                assert page.locator(".familiar-orbit img").count() == 0
                assert page.locator(".reward-notice svg circle.celikom-info-dot").count() == 1
                assert page.locator(".reward-symbol svg circle").count() == 1
                assert page.locator("#faq details.faq-item").count() == 28
                assert page.locator(".closing-link").count() == 0
                if width == 1440:
                    assert page.locator("header nav").is_visible()
                    page.locator('header nav a[href="#faq"]').click()
                    page.wait_for_timeout(950)
                    assert page.evaluate("Math.abs(document.getElementById('faq').getBoundingClientRect().top - 24) < 130")
                else:
                    assert page.locator(".header-chip").is_visible()
                # Verify the entire details element moves smoothly, not just the answer text.
                result = page.evaluate("""async () => {
                    const d=document.querySelector('#faq details.faq-item');
                    const sum=d.querySelector('summary');
                    d.scrollIntoView({block:'center',behavior:'instant'});
                    sum.click();
                    await new Promise(r=>setTimeout(r, 410));
                    const opened=d.open, before=d.getBoundingClientRect().height;
                    sum.click();
                    const heights=[], t0=performance.now();
                    await new Promise(resolve=>{
                        function frame(){
                            const a=d.querySelector('.answer');
                            heights.push([performance.now()-t0,d.getBoundingClientRect().height,a.getBoundingClientRect().height,parseFloat(getComputedStyle(a).paddingBottom)]);
                            if(performance.now()-t0 < 450)requestAnimationFrame(frame);
                            else resolve();
                        }requestAnimationFrame(frame)
                    });
                    return {opened,closed:!d.open,before,heights,
                            final:d.getBoundingClientRect().height};
                }""")
                assert result["opened"] and result["closed"], result
                sizes = [x[1] for x in result["heights"]]
                assert sizes[0] > result["final"] + 10, result
                # Full card and answer's padding must both collapse smoothly.
                assert max(abs(a-b) for a,b in zip(sizes, sizes[1:])) < .36 * (sizes[0]-sizes[-1]), result
                assert abs(sizes[-1]-result["final"]) < 1, result
                # Before completing, bottom padding must gradually reach near zero.
                active=[h for h in result["heights"] if 25 < h[0] < 250]
                assert active[0][3]>active[-1][3] >=0, result
                assert all(active[i][3]+.75 >= active[i+1][3] for i in range(len(active)-1)), result
                # No large jumps in the last frames after the full closing animation.
                tail = [h for t,h in result["heights"] if t > 310]
                assert max(tail)-min(tail) < 1.5, result
                print(f"CELIKOM v10 Chromium {width}px: unchanged header, crisp C, info dot, FAQ continuous padding PASS")
                page.close()
            browser.close()
finally:
    HTML.unlink(missing_ok=True)
