#!/usr/bin/env python3
"""Chromium: approved v10 layout, continuous FAQ open/close and global exclusivity."""
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
                    const opening=[], openStart=performance.now();
                    await new Promise(resolve=>{
                        function frame(){
                            opening.push([performance.now()-openStart,
                                d.getBoundingClientRect().height,
                                parseFloat(getComputedStyle(d.querySelector('.answer')).paddingBottom),
                                d.open]);
                            if(performance.now()-openStart<410)requestAnimationFrame(frame);
                            else resolve();
                        }requestAnimationFrame(frame)
                    });
                    const opened=d.open, before=d.getBoundingClientRect().height;
                    const a=d.querySelector('.answer'), p=a.querySelector('p:last-child');
                    const bottomPadding=parseFloat(getComputedStyle(a).paddingBottom);
                    const visibleGap=a.getBoundingClientRect().bottom-p.getBoundingClientRect().bottom;
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
                    const closed=!d.open, collapsedHeight=d.getBoundingClientRect().height;
                    sum.click();
                    await new Promise(r=>setTimeout(r,410));
                    const reopened=d.open;
                    const reopenedGap=a.getBoundingClientRect().bottom-p.getBoundingClientRect().bottom;
                    return {opened,closed,reopened,before,opening,heights,bottomPadding,
                            visibleGap,reopenedGap,final:collapsedHeight};
                }""")
                assert result["opened"] and result["closed"] and result["reopened"], result
                expected_pad = 19 if width <= 540 else 23
                # Opening must grow in ONE continuous border-box-height
                # animation: no last-frame snap when bottom padding is restored.
                opening = result["opening"]
                heights_open = [row[1] for row in opening]
                assert len(opening) >= 12, result
                assert heights_open[-1] > heights_open[0]+15, result
                assert all(b+.8 >= a for a,b in zip(heights_open,heights_open[1:])), result
                assert max(abs(b-a) for a,b in zip(heights_open,heights_open[1:])) < .38*(heights_open[-1]-heights_open[0]),result
                opening_tail = [row[1] for row in opening if row[0] > 330]
                assert max(opening_tail)-min(opening_tail) < 1.5,result
                assert abs(opening[-1][2]-expected_pad) < 1,result
                assert abs(result["bottomPadding"]-expected_pad) < 1, result
                assert abs(result["visibleGap"]-expected_pad) < 2, result
                assert abs(result["reopenedGap"]-expected_pad) < 2, result
                sizes = [x[1] for x in result["heights"]]
                assert sizes[0] > result["final"] + 10, result
                # Full card and answer's padding must both collapse smoothly.
                assert max(abs(a-b) for a,b in zip(sizes, sizes[1:])) < .36 * (sizes[0]-sizes[-1]), result
                assert abs(sizes[-1]-result["final"]) < 1, result
                # The answer's visible box, including whatever bottom padding
                # this responsive breakpoint computes, must shrink in one pass.
                active=[h for h in result["heights"] if 25 < h[0] < 250]
                assert active[0][2] > active[-1][2] >= 0, result
                assert all(active[i][2]+.75 >= active[i+1][2] for i in range(len(active)-1)), result
                # No large jumps in the last frames after the full closing animation.
                tail = [row[1] for row in result["heights"] if row[0] > 310]
                assert max(tail)-min(tail) < 1.5, result
                # Clicking a question in the OTHER column/category closes
                # the old item before opening the new one. Never 2 open attrs.
                switching = page.evaluate("""async()=>{
                    const items=[...document.querySelectorAll('#faq details.faq-item')];
                    items[19].querySelector('summary').click();
                    const counts=[], t=performance.now();
                    await new Promise(resolve=>{
                        function frame(){
                            counts.push(document.querySelectorAll('#faq details.faq-item[open]').length);
                            if(performance.now()-t<740)requestAnimationFrame(frame);
                            else resolve();
                        }requestAnimationFrame(frame)
                    });
                    return {max:Math.max(...counts),
                        open:[...document.querySelectorAll('#faq details.faq-item[open]')].map(d=>d.id)};
                }""")
                assert switching["max"] <= 1, switching
                assert switching["open"] == ["faq-question-20"], switching
                # Changing category mid-animation must cancel the disappearing
                # element's effect; rapid reversal and a new target must work.
                rapid = page.evaluate("""async()=>{
                    const root=document.getElementById('faq');
                    root.querySelector('.faq-filter[data-filter="rewards"]').click();
                    const items=[...root.querySelectorAll('details.faq-item')];
                    items[9].querySelector('summary').click();
                    await new Promise(r=>setTimeout(r,45));
                    items[9].querySelector('summary').click();
                    await new Promise(r=>setTimeout(r,40));
                    items[10].querySelector('summary').click();
                    await new Promise(r=>setTimeout(r,730));
                    return {open:[...root.querySelectorAll('details.faq-item[open]')].map(d=>d.id),
                        category:root.querySelector('.faq-filter[aria-pressed="true"]').dataset.filter};
                }""")
                assert rapid == {"open":["faq-question-11"],"category":"rewards"}, rapid
                # A hash to a hidden question selects its category and opens it.
                page.evaluate("location.hash='#faq-question-23'")
                page.wait_for_timeout(830)
                assert page.locator('#faq details.faq-item[open]').evaluate_all(
                    'items=>items.map(x=>x.id)') == ["faq-question-23"]
                assert page.locator('.faq-filter[aria-pressed="true"]').get_attribute(
                    "data-filter") == "music"
                # Reduced motion retains strict accordion without animation.
                page.emulate_media(reduced_motion="reduce")
                page.locator('.faq-filter[data-filter="all"]').click()
                page.locator('#faq-question-01 summary').click()
                page.locator('#faq-question-22 summary').click()
                assert page.locator('#faq details.faq-item[open]').evaluate_all(
                    'items=>items.map(x=>x.id)') == ["faq-question-22"]
                print(f"CELIKOM v10 Chromium {width}px: continuous FAQ open/close, {expected_pad}px padding, global accordion, fast clicks, filters, hash and reduced motion PASS")
                page.close()
            browser.close()
finally:
    HTML.unlink(missing_ok=True)
