// QA: screenshots of the page at given views on desktop and phone, with console errors and what each layer draws.
//   node code/qa_shots.js qa [name=lat,lon,zoom ...] [--phone] [--click]
// Serves the study folder and the local Terrarium tiles on 127.0.0.1:8798; OpenFreeMap through the proxy (HTTPS_PROXY).
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..'), OUT = path.resolve(process.argv[2] || 'qa');
const DEM = process.env.DEM_DIR || '/home/claude/newdata/raw9/terrarium';
fs.mkdirSync(OUT, { recursive: true });
const TC = process.env.TILECACHE || '/home/claude/work/domesday-world/tilecache'; fs.mkdirSync(TC, { recursive: true });
if (process.env.HTTPS_PROXY) { try { const { ProxyAgent, setGlobalDispatcher } = require('undici'); setGlobalDispatcher(new ProxyAgent(process.env.HTTPS_PROXY)); } catch (e) { console.warn('undici', e.message); } }
const TYPES = { '.js': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.geojson': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.pbf': 'application/x-protobuf', '.css': 'text/css' };
const srv = http.createServer((q, r) => {
  let u = decodeURIComponent(q.url.split('?')[0]);
  let f = u.startsWith('/dem/') ? path.join(DEM, u.slice(5)) : path.join(ROOT, u === '/' ? 'index.html' : u);
  fs.readFile(f, (e, b) => { if (e) { r.statusCode = 404; r.end(); return; } r.setHeader('Content-Type', TYPES[path.extname(f)] || 'application/octet-stream'); r.setHeader('Access-Control-Allow-Origin', '*'); r.end(b); });
}).listen(8798);
const args = process.argv.slice(3);
const phone = args.includes('--phone'), click = args.includes('--click');
const views = args.filter(a => a.includes('=')).map(a => { const [n, v] = a.split('='); const [lat, lon, z] = v.split(',').map(Number); return { n, lat, lon, z }; });
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const ctx = await b.newContext({ viewport: phone ? { width: 390, height: 844 } : { width: 1280, height: 800 }, deviceScaleFactor: phone ? 2 : 1, ignoreHTTPSErrors: true });
  const out = {};
  for (const v of views) {
    const p = await ctx.newPage(); const errs = [];
    // MapLibre from the local npm copy (MAPLIBRE_DIST), web fonts skipped; everything else as the page asks
    const ML = process.env.MAPLIBRE_DIST || '/home/claude/work/domesday-world/node/node_modules/maplibre-gl/dist';
    await p.route('**/cdn.jsdelivr.net/**', rt => { const u = rt.request().url(); const f = u.endsWith('.css') ? 'maplibre-gl.css' : 'maplibre-gl.js'; rt.fulfill({ path: path.join(ML, f) }); });
    await p.route('**/fonts.googleapis.com/**', rt => rt.fulfill({ status: 200, contentType: 'text/css', body: '' }));
    await p.route('**/fonts.gstatic.com/**', rt => rt.abort());
    // OpenFreeMap tiles fetched by node (through HTTPS_PROXY when set) and kept in a cache folder, for the page and its workers
    await p.route('**/tiles.openfreemap.org/**', async rt => {
      const u = rt.request().url(), f = path.join(TC, u.replace(/^https:\/\//, '').replace(/[^\w.]+/g, '_'));
      try {
        let body; if (fs.existsSync(f)) body = fs.readFileSync(f);
        else { const r = await fetch(u); if (!r.ok) { rt.fulfill({ status: r.status }); return; } body = Buffer.from(await r.arrayBuffer()); fs.writeFileSync(f, body); }
        rt.fulfill({ status: 200, body, headers: { 'Access-Control-Allow-Origin': '*', 'Content-Type': u.endsWith('.pbf') ? 'application/x-protobuf' : 'application/json' } });
      } catch (e) { rt.abort(); }
    });
    p.on('requestfailed', rq => errs.push('reqfail: ' + rq.url().slice(0, 140) + ' ' + (rq.failure() || {}).errorText));
    let bytes = { page: 0, tiles: 0, other: 0 };
    p.on('response', async rs => { if (rs.status() >= 400) errs.push('http ' + rs.status() + ' ' + rs.url().slice(0, 140)); try { const u = rs.url(); const b = (await rs.body()).length; if (u.includes('openfreemap')) bytes.tiles += b; else if (u.includes('127.0.0.1') && !u.includes('/dem/')) bytes.page += b; else bytes.other += b; } catch (e) {} });
    p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.type() + ': ' + m.text().slice(0, 300)); });
    p.on('pageerror', e => errs.push('pageerror: ' + e.message));
    const url = `http://127.0.0.1:8798/index.html?at=${v.lat},${v.lon},${v.z}&dem=${encodeURIComponent('http://127.0.0.1:8798/dem/{z}/{x}/{y}.png')}&demmax=${process.env.DEMMAX || 8}&noclouds=1${process.env.EXTRA || ''}`;
    const t0 = Date.now();
    await p.goto(url, { waitUntil: 'load' });
    try { await p.waitForFunction(() => window.__map && window.__map.loaded() && window.__map.areTilesLoaded(), null, { timeout: 90000, polling: 500 }); } catch (e) { errs.push('timeout waiting for tiles'); }
    await p.waitForTimeout(+(process.env.WAIT || 4000));
    try { await p.waitForFunction(() => window.__map.loaded(), null, { timeout: 30000, polling: 500 }); } catch (e) {}
    if (!(await p.evaluate(() => !!window.__map))) { console.log('NO MAP', errs.join('\n')); await p.screenshot({ path: path.join(OUT, v.n + '_fail.png') }); continue; }
    const info = await p.evaluate(() => {
      const m = window.__map, o = {};
      for (const id of ['dw', 'vill-glyphs', 'vill-names', 'trees', 'relief', 'shire-names', 'hundred-names', 'roman-case', 'modern-names']) { try { o[id] = m.getLayer(id) ? m.queryRenderedFeatures({ layers: [id] }).length : -1; } catch (e) { o[id] = 'err'; } }
      // anything modern left in view? the OpenFreeMap layers that should not be drawn
      const style = m.getStyle(); o.ofmLayersShown = style.layers.filter(l => l.source === 'ofm' && (l.layout || {}).visibility !== 'none').map(l => l.id + ':' + l['source-layer']);
      const kinds = {}; try { for (const f of m.queryRenderedFeatures({ layers: ['dw'] })) kinds[f.properties.t] = (kinds[f.properties.t] || 0) + 1; } catch (e) {}
      o.kinds = kinds; o.zoom = m.getZoom(); return o;
    });
    info.ms = Date.now() - t0; info.bytes = bytes;
    const name = v.n + (phone ? '_phone' : '');
    await p.screenshot({ path: path.join(OUT, name + '.png'), timeout: 240000 });
    if (click) {
      // click the drawing nearest the centre and capture the popup
      const pt = await p.evaluate(() => { const m = window.__map, c = m.getCanvas(); const fs = m.queryRenderedFeatures({ layers: ['dw'] }); if (!fs.length) return null; const W = c.clientWidth / 2, H = c.clientHeight / 2; let best = null, bd = 1e9; for (const f of fs) { const q = m.project(f.geometry.coordinates); const d = Math.hypot(q.x - W, q.y - H); if (d < bd) { bd = d; best = { x: q.x, y: q.y - 4, t: f.properties.t }; } } return best; });
      if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(2500); info.popup = await p.evaluate(() => { const e = document.querySelector('.maplibregl-popup-content'); return e ? e.innerText.slice(0, 1500) : null; }); info.clicked = pt.t; await p.screenshot({ path: path.join(OUT, name + '_popup.png') }); }
    }
    info.errors = errs; out[name] = info;
    console.log(name, JSON.stringify(info).slice(0, 900));
    await p.close();
  }
  fs.writeFileSync(path.join(OUT, 'shots' + (phone ? '_phone' : '') + '.json'), JSON.stringify(out, null, 1));
  await b.close(); srv.close();
})();
