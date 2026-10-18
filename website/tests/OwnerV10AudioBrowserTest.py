#!/usr/bin/env python3
"""Chromium regression for the real v10 A/B player using generated TEST tones.

The generated sine wave never ships as music or appears on the live website.
The real site must still receive two independently sourced music clips.
"""
import http.server
import io
import math
import pathlib
import socketserver
import struct
import subprocess
import threading
import wave
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
HTML=ROOT/"public"/"owner-audio-review.html"

def tone(hz):
    memory=io.BytesIO()
    with wave.open(memory,"wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        # 11 seconds of deliberately synthetic fixture audio.
        chunk=bytearray()
        for n in range(11*16000):
            chunk+=struct.pack("<h",round(4000*math.sin(n*hz*math.tau/16000)))
            if len(chunk)>=32000:
                writer.writeframesraw(chunk)
                chunk.clear()
        writer.writeframesraw(chunk)
    return memory.getvalue()

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

class Serving(socketserver.ThreadingTCPServer):
    allow_reuse_address=True

HTML.write_bytes(subprocess.check_output(["php",str(ROOT/"tests"/"OwnerV10MotionFixture.php")]))
try:
    with Serving(("127.0.0.1",0),lambda *args,**kwargs: Quiet(*args,directory=str(ROOT/"public"),**kwargs)) as srv:
        threading.Thread(target=srv.serve_forever,daemon=True).start()
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True)
            for width,height in [(1440,900),(390,844)]:
                page=browser.new_page(viewport={"width":width,"height":height})
                a=tone(250)
                b=tone(390)
                page.route("**/?demo_audio=service",lambda route:route.fulfill(status=200,content_type="audio/wav",body=a))
                page.route("**/?demo_audio=restored",lambda route:route.fulfill(status=200,content_type="audio/wav",body=b))
                page.goto(f"http://127.0.0.1:{srv.server_address[1]}/owner-audio-review.html",wait_until="networkidle")
                assert page.locator("#sound-panel .wave-bar").count()==30
                assert page.locator("#celikom-demo-play").count()==1
                assert page.locator("#celikom-demo-seek").count()==1
                assert page.locator("#celikom-demo-time").inner_text()=="0:00 / 0:11"
                assert page.locator("#mode-service").get_attribute("aria-pressed")=="true"
                page.evaluate("""()=>{
                  const board=document.getElementById('sound-panel');
                  board.dataset.demoReady='true';
                  document.getElementById('celikom-demo-play').disabled=false;
                  document.querySelectorAll('#sound-panel audio').forEach(a=>a.preload='auto');
                }""")
                page.locator("#celikom-demo-play").click()
                page.wait_for_function("document.getElementById('celikom-demo-service').currentTime>.4",timeout=10000)
                assert page.locator("#sound-panel").get_attribute("data-playing")=="true"
                before=page.evaluate("document.getElementById('celikom-demo-service').currentTime")
                page.locator("#mode-restored").click()
                page.wait_for_function("document.getElementById('celikom-demo-restored').currentTime>.4",timeout=10000)
                after=page.evaluate("document.getElementById('celikom-demo-restored').currentTime")
                assert abs(before-after)<1.2,(before,after)
                assert page.locator("#mode-restored").get_attribute("aria-pressed")=="true"
                page.locator("#celikom-demo-play").click()
                assert page.locator("#sound-panel").get_attribute("data-playing")=="false"
                page.locator("#mode-service").click()
                assert page.locator("#sound-panel").get_attribute("data-playing")=="false"
                page.locator("#celikom-demo-seek").evaluate("""x=>{
                    x.value='6';
                    x.dispatchEvent(new Event('input',{bubbles:true}));
                }""")
                assert page.locator("#celikom-demo-time").inner_text().startswith("0:06")
                page.locator("#celikom-demo-play").click()
                page.wait_for_function("document.getElementById('celikom-demo-service').currentTime>6",timeout=10000)
                print(f"CELIKOM synthetic-audio Chromium {width}px: play/pause/swap/seek PASS")
                page.close()
            browser.close()
finally:
    HTML.unlink(missing_ok=True)
