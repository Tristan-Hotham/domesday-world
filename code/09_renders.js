// Step 9. Renders of the live page (map only, no controls) for the header, the blog and paper figures and the collage.
//   node code/09_renders.js [only=name,name]
// Same local serving as code/qa_shots.js: the study folder, local Terrarium tiles (DEM_DIR), OpenFreeMap through node.
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..'), OUT = path.join(ROOT, 'release', 'figs');
const DEM = process.env.DEM_DIR || '/home/claude/newdata/raw9/terrarium';
const TC = process.env.TILECACHE || '/home/claude/work/domesday-world/tilecache';
fs.mkdirSync(OUT, { recursive: true }); fs.mkdirSync(TC, { recursive: true });
if (process.env.HTTPS_PROXY) { try { const { ProxyAgent, setGlobalDispatcher } = require('undici'); setGlobalDispatcher(new ProxyAgent(process.env.HTTPS_PROXY)); } catch (e) {} }
const TYPES = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.geojson': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.pbf': 'application/x-protobuf' };
const srv = http.createServer((q, r) => { const u = decodeURIComponent(q.url.split('?')[0]); const f = u.startsWith('/dem/') ? path.join(DEM, u.slice(5)) : path.join(ROOT, u === '/' ? 'index.html' : u);
  fs.readFile(f, (e, b) => { if (e) { r.statusCode = 404; r.end(); return; } r.setHeader('Content-Type', TYPES[path.extname(f)] || 'application/octet-stream'); r.end(b); }); }).listen(8799);
// name, lat, lon, zoom, width, height, device scale, extra query
const V = [
  ['header_map', 52.75, -1.35, 6.05, 1200, 630, 1, ''],
  ['b_england', 52.55, -1.4, 6.55, 1500, 1500, 1, ''],
  ['b_york', 53.959, -1.08, 13.2, 1500, 1000, 1, ''],
  ['b_mills', 51.0985, -1.1655, 15.0, 1500, 1000, 1, ''],
  ['b_fens', 52.42, 0.2, 10.3, 1500, 1000, 1, ''],
  ['b_droitwich', 52.2695, -2.155, 13.6, 1500, 1000, 1, ''],
  ['b_suffolk', 52.2423, 0.5398, 13.9, 1500, 1000, 1, ''],
  ['b_waste', 54.05, -1.4, 9.4, 1500, 1000, 1, '&waste=1'],
  ['c_england', 53.12, -2.15, 6.8, 1500, 1850, 2, ''],   // all England, Cornwall to Norfolk, Northumbria and the Welsh march, with sea round it
  ['c_york', 53.9595, -1.08, 13.25, 820, 820, 1.5, ''],
  ['c_fens', 52.40, 0.26, 11.2, 820, 820, 1.5, ''],
  ['c_droitwich', 52.2695, -2.155, 14.2, 820, 820, 1.5, ''],
  ['c_oxford', 51.7545, -1.2555, 13.6, 820, 820, 1.5, ''],
  ['c_village', 51.0985, -1.1655, 15.2, 820, 820, 1.5, ''],
];
const only = (process.argv.find(a => a.startsWith('only=')) || '').slice(5).split(',').filter(Boolean);
(async () => {
  const ML = process.env.MAPLIBRE_DIST || '/home/claude/work/domesday-world/node/node_modules/maplibre-gl/dist';
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  for (const [n, lat, lon, z, w, h, dsf, extra] of V) {
    if (only.length && !only.includes(n)) continue;
    const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: dsf });
    const p = await ctx.newPage();
    await p.route('**/cdn.jsdelivr.net/**', rt => rt.fulfill({ path: path.join(ML, rt.request().url().endsWith('.css') ? 'maplibre-gl.css' : 'maplibre-gl.js') }));
    await p.route('**/fonts.googleapis.com/**', rt => rt.fulfill({ status: 200, contentType: 'text/css', body: '' }));
    await p.route('**/tiles.openfreemap.org/**', async rt => {
      const u = rt.request().url(), f = path.join(TC, u.replace(/^https:\/\//, '').replace(/[^\w.]+/g, '_'));
      try { let body; if (fs.existsSync(f)) body = fs.readFileSync(f); else { const r = await fetch(u); if (!r.ok) { rt.fulfill({ status: r.status }); return; } body = Buffer.from(await r.arrayBuffer()); fs.writeFileSync(f, body); }
        rt.fulfill({ status: 200, body, headers: { 'Access-Control-Allow-Origin': '*' } }); } catch (e) { rt.abort(); }
    });
    await p.goto(`http://127.0.0.1:8799/index.html?maponly=1&clean=1&noclouds=1&at=${lat},${lon},${z}&dem=${encodeURIComponent('http://127.0.0.1:8799/dem/{z}/{x}/{y}.png')}&demmax=${z > 9 ? 10 : 8}${extra}`, { waitUntil: 'load' });
    try { await p.waitForFunction(() => window.__map && window.__map.loaded() && window.__map.areTilesLoaded(), null, { timeout: 180000, polling: 500 }); } catch (e) { console.log(n, 'timeout'); }
    await p.waitForTimeout(6000);   // the lazily loaded layers (roads, far woods) come in after the first idle
    if (extra.includes('waste')) await p.evaluate(() => window.__map.getLayer('waste-rings') && window.__map.setLayoutProperty('waste-rings', 'visibility', 'visible'));
    try { await p.waitForFunction(() => window.__map.loaded() && window.__map.areTilesLoaded(), null, { timeout: 120000, polling: 500 }); } catch (e) {}
    await p.waitForTimeout(2500);
    await p.screenshot({ path: path.join(OUT, n + '.png'), timeout: 240000 });
    console.log(n, 'done');
    await ctx.close();
  }
  await b.close(); srv.close();
})();
