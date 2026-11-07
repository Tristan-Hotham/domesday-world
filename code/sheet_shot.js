// Draw every 1086 sprite on one sheet (code/sheet_1086.html) and save a PNG: node code/sheet_shot.js out.png [zoom]
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const srv = http.createServer((q, r) => { const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, b) => { if (e) { r.statusCode = 404; r.end(); return; } r.setHeader('Content-Type', f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : 'application/octet-stream'); r.end(b); }); }).listen(8797);
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 1 });
  p.on('console', m => console.log('console', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('http://127.0.0.1:8797/code/sheet_1086.html?z=' + (process.argv[3] || 3)); await p.waitForFunction(() => document.title === 'done');
  await p.screenshot({ path: process.argv[2] || 'sheet.png', fullPage: true }); await b.close(); srv.close();
})();
