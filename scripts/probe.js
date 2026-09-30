
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('http://127.0.0.1:5199/index.html');
  await p.waitForTimeout(1500);
  const r = await p.evaluate(() => {
    const tl = window.__timelines['stack'];
    tl.seek(13.5);
    const out = {};
    for (const id of ['s5','w5']) {
      const e = document.getElementById(id);
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      out[id] = { x: r.x, y: r.y, w: r.width, h: r.height,
                  inset: cs.inset, top: cs.top, left: cs.left,
                  bg: cs.backgroundColor, radius: cs.borderRadius };
    }
    const v = document.getElementById('v5').getBoundingClientRect();
    out.v5 = { x: v.x, y: v.y, w: v.width, h: v.height };
    return out;
  });
  console.log(JSON.stringify(r, null, 2));
  await b.close();
})();
