// The legend of the period drawings as a PNG (code/legend.html): node code/legend_shot.js out.png [cols] [width] [scale]
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, b) => { if (e) { r.statusCode = 404; r.end(); return; } r.setHeader('Content-Type', f.endsWith('.js') ? 'text/javascript' : 'text/html'); r.end(b); }); }).listen(8796);
(async () => {
  const [out, cols, w, sc] = [process.argv[2], process.argv[3] || 2, process.argv[4] || 700, +(process.argv[5] || 2)];
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +w + 40, height: 400 }, deviceScaleFactor: sc });
  await p.goto(`http://127.0.0.1:8796/code/legend.html?cols=${cols}&w=${w}`); await p.waitForFunction(() => document.title === 'done');
  await (await p.$('#o')).screenshot({ path: out }); await b.close(); srv.close();
})();
