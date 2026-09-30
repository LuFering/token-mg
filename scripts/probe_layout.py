# -*- coding: utf-8 -*-
"""
用 Playwright 打开合成页，seek 到指定时刻，导出关键元素的实际几何。
用来定位"展开后顶部露出白边"的真实原因，而不是靠猜。
"""
import json
import os
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

PROJ = r"D:\cut\token-mg"
PORT = 5199

# 起一个静态服务器（HyperFrames 的 preview 也可，但直接 http.server 更轻）
srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1"],
                       cwd=PROJ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

PROBE = """
(() => {
  const tl = window.__timelines && window.__timelines['stack'];
  if (!tl) return { error: 'timeline not found' };
  tl.seek(T);
  const ids = ['s1','s4','s5','w5','v5'];
  const out = { t: T };
  for (const id of ids) {
    const e = document.getElementById(id);
    if (!e) { out[id] = null; continue; }
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    out[id] = {
      x: Math.round(r.x), y: Math.round(r.y),
      w: Math.round(r.width), h: Math.round(r.height),
      top: cs.top, left: cs.left, inset: cs.inset,
      bg: cs.backgroundColor, radius: cs.borderRadius,
      transform: cs.transform
    };
  }
  return out;
})()
"""

try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1920, "height": 1080})
        page.goto("http://127.0.0.1:%d/index.html" % PORT)
        page.wait_for_timeout(2000)

        for t in (9.7, 11.0, 12.5, 13.8):
            r = page.evaluate(PROBE.replace("T", str(t)))
            print("=== t=%.1fs ===" % t)
            if r.get("error"):
                print("  ", r["error"])
                continue
            for k, v in r.items():
                if k == "t" or v is None:
                    continue
                print("  %-4s x=%4d y=%4d w=%4d h=%4d  inset=%-12s bg=%-22s radius=%s"
                      % (k, v["x"], v["y"], v["w"], v["h"], v["inset"], v["bg"], v["radius"]))
            print()

        b.close()
finally:
    srv.terminate()
