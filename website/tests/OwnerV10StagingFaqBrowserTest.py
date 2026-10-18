#!/usr/bin/env python3
"""Authenticated Chromium smoke on the actual closed Hostinger staging site.

Only reads site markup/interacts with FAQ in the browser; never edits CMS data.
The HTTP Basic password is passed as a masked, short-lived env var by Actions.
"""
import os
from playwright.sync_api import sync_playwright

URL = "https://lemonchiffon-narwhal-791953.hostingersite.com/"
PASSWORD = os.environ.get("CELIKOM_STAGING_BASIC_PASS", "")
if not PASSWORD:
    raise RuntimeError("Missing closed-staging browser credentials")

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for width, height in [(1440, 900), (390, 844)]:
        context = browser.new_context(
            viewport={"width": width, "height": height},
            reduced_motion="no-preference",
            http_credentials={"username": "review", "password": PASSWORD},
        )
        page = context.new_page()
        response = page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        assert response and response.status == 200, "Staging did not serve authorized page"
        page.wait_for_function(
            "() => !!document.querySelector('script[src*=\"owner-v10-motion.js?v=510\"]')",
            timeout=15000,
        )
        page.wait_for_timeout(450)
        assert page.locator("#faq details.faq-item").count() == 28
        result = page.evaluate("""async () => {
          const root=document.querySelector('#faq');
          const items=[...root.querySelectorAll('details.faq-item')];
          const first=items[0], second=items[19];
          const a=first.querySelector('.answer');
          first.querySelector('summary').click();
          const rows=[], start=performance.now();
          await new Promise(resolve=>{
            function frame(){
              rows.push([performance.now()-start,first.getBoundingClientRect().height]);
              if(performance.now()-start < 420)requestAnimationFrame(frame);
              else resolve();
            } requestAnimationFrame(frame);
          });
          const p=a.querySelector('p:last-child');
          const gap=a.getBoundingClientRect().bottom-p.getBoundingClientRect().bottom;
          first.querySelector('summary').click();
          const closing=[], t=performance.now();
          await new Promise(resolve=>{
            function frame(){
              closing.push([performance.now()-t,first.getBoundingClientRect().height]);
              if(performance.now()-t < 390)requestAnimationFrame(frame);
              else resolve();
            } requestAnimationFrame(frame);
          });
          first.querySelector('summary').click();
          await new Promise(r=>setTimeout(r,360));
          second.querySelector('summary').click();
          const counts=[], t2=performance.now();
          await new Promise(resolve=>{
            function frame(){
              counts.push(root.querySelectorAll('details.faq-item[open]').length);
              if(performance.now()-t2 < 740)requestAnimationFrame(frame);
              else resolve();
            } requestAnimationFrame(frame);
          });
          const endIds=[...root.querySelectorAll('details.faq-item[open]')].map(x=>x.id);
          root.querySelector('.faq-filter[data-filter="rewards"]').click();
          const afterFilter=root.querySelectorAll('details.faq-item[open]').length;
          return {rows,closing,gap,counts,endIds,afterFilter};
        }""")
        expected = 19 if width == 390 else 23
        assert abs(result["gap"] - expected) < 2, result
        opening = [row[1] for row in result["rows"]]
        closing = [row[1] for row in result["closing"]]
        assert len(opening) >= 12 and len(closing) >= 12, result
        assert opening[-1] > opening[0] + 10, result
        assert all(b + 1 >= a for a, b in zip(opening, opening[1:])), result
        assert all(a + 1 >= b for a, b in zip(closing, closing[1:])), result
        assert max(row[1] for row in result["rows"] if row[0] > 330) - min(
            row[1] for row in result["rows"] if row[0] > 330
        ) < 1.5, result
        assert max(result["counts"]) <= 1, result
        assert result["endIds"] == ["faq-question-20"], result
        assert result["afterFilter"] == 0, result
        print(f"Closed Hostinger Chromium {width}px: smooth FAQ, {expected}px gap, one open globally PASS")
        context.close()
    browser.close()
