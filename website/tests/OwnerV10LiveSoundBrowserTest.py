#!/usr/bin/env python3
"""Closed Hostinger staging acceptance: TRUE music excerpts, not synthetic fixtures.

Must only run after BOTH verified, separate 11s clips exist. No publishing,
credential logging, screenshots, account writes or changes to music library.
"""
import os
from playwright.sync_api import sync_playwright

SITE="https://lemonchiffon-narwhal-791953.hostingersite.com/"
password=os.environ.get("CELIKOM_STAGING_BASIC_PASS")
if not password:
    raise SystemExit("Closed-staging browser credentials unavailable")
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for width,height in [(1440,900),(390,844)]:
        context=browser.new_context(
            viewport={"width":width,"height":height},
            reduced_motion="no-preference",
            http_credentials={"username":"review","password":password},
        )
        page=context.new_page()
        res=page.goto(SITE,wait_until="networkidle",timeout=45000)
        assert res is not None and res.status==200
        board=page.locator("#sound-panel")
        assert board.get_attribute("data-demo-ready")=="true"
        assert page.locator("#faq details.faq-item").count()==28
        assert page.locator("header nav a").count()==2
        assert page.locator("#celikom-demo-play").is_enabled()
        assert page.locator("#sound-result").is_hidden()
        assert page.locator("#sound-panel .wave-bar").count()==30
        assert page.locator("#celikom-demo-time").inner_text()=="0:00 / 0:11"
        # Both MP3 Range endpoints must work under Basic auth.
        for mode in ("service","restored"):
            fetch=page.request.get(
                SITE+"?demo_audio="+mode,
                headers={"Range":"bytes=0-1023"},
                timeout=30000,
            )
            assert fetch.status==206,(mode,fetch.status)
            assert fetch.headers.get("content-type","").startswith("audio/mpeg")
            assert len(fetch.body())==1024
        play=page.locator("#celikom-demo-play")
        play.click()
        page.wait_for_function("document.getElementById('celikom-demo-service').currentTime>0.6",timeout=15000)
        assert board.get_attribute("data-playing")=="true"
        before=page.evaluate("document.getElementById('celikom-demo-service').currentTime")
        page.locator("#mode-restored").click()
        page.wait_for_function("document.getElementById('celikom-demo-restored').currentTime>0.7",timeout=15000)
        after=page.evaluate("document.getElementById('celikom-demo-restored').currentTime")
        assert abs(before-after)<1.1,(before,after)
        assert page.locator("#mode-restored").get_attribute("aria-pressed")=="true"
        play.click()
        assert board.get_attribute("data-playing")=="false"
        page.locator("#mode-service").click()
        assert board.get_attribute("data-playing")=="false"
        page.locator("#celikom-demo-seek").evaluate("""element=>{
            element.value='5';
            element.dispatchEvent(new Event('input',{bubbles:true}))
        }""")
        page.wait_for_function("document.getElementById('celikom-demo-time').textContent.startsWith('0:05')",timeout=12000)
        play.click()
        page.wait_for_function("document.getElementById('celikom-demo-service').currentTime>5",timeout=15000)
        print(f"CELIKOM protected Hostinger {width}px: verified separate real MP3 Range, PLAY/PAUSE, sync swap and 5s seek PASS")
        context.close()
    browser.close()
