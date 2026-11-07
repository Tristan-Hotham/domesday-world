// Step 3b. For each zoom 13 OpenFreeMap tile in WORK/tiles13.json: a 256 x 256 water mask (sea, lakes, ponds, rivers drawn
// as areas) and the waterway lines (rivers and streams; canals and drains flagged), written to WORK/ofm13/{x}_{y}.json.
// Used offline to keep every drawing off the water and to set each mill on its stream. Needs @mapbox/vector-tile and pbf
// (NODE_PATH). Map data (c) OpenStreetMap contributors, ODbL; tiles by OpenFreeMap (OpenMapTiles schema). The masks are not
// redistributed; only the derived positions of the drawings are.
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const { VectorTile } = require('@mapbox/vector-tile'), Pbf = require('pbf');
// behind a proxy (HTTPS_PROXY), route fetch through it
if (process.env.HTTPS_PROXY) { try { const { ProxyAgent, setGlobalDispatcher } = require('undici'); setGlobalDispatcher(new ProxyAgent(process.env.HTTPS_PROXY)); } catch (e) {} }
const WORK = process.env.DW_WORK || '/home/claude/work/domesday-world';
const URL = 'https://tiles.openfreemap.org/planet/20261101_080013_pt/13/{x}/{y}.pbf';
const OUT = path.join(WORK, 'ofm13'); fs.mkdirSync(OUT, { recursive: true });
const tiles = JSON.parse(fs.readFileSync(path.join(WORK, 'tiles13.json')));
const N = 256;
function fillRings(mask, rings, ext) {
  // even-odd scanline fill of all rings of one polygon feature
  const sc = N / ext;
  for (let row = 0; row < N; row++) {
    const yy = (row + 0.5) / sc, xs = [];
    for (const r of rings) for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      const a = r[i], b = r[j];
      if ((a.y > yy) !== (b.y > yy)) xs.push(a.x + (yy - a.y) * (b.x - a.x) / (b.y - a.y));
    }
    xs.sort((p, q) => p - q);
    for (let k = 0; k + 1 < xs.length; k += 2) {
      const c0 = Math.max(0, Math.ceil(xs[k] * sc - 0.5)), c1 = Math.min(N - 1, Math.floor(xs[k + 1] * sc - 0.5));
      for (let c = c0; c <= c1; c++) mask[row * N + c] = 1;
    }
  }
}
async function one([x, y]) {
  const f = path.join(OUT, x + '_' + y + '.json');
  if (fs.existsSync(f)) return;
  let buf = null;
  for (let a = 0; a < 4 && !buf; a++) {
    try { const r = await fetch(URL.replace('{x}', x).replace('{y}', y)); if (r.status === 404 || r.status === 204) { buf = Buffer.alloc(0); break; } if (!r.ok) throw new Error(r.status); buf = Buffer.from(await r.arrayBuffer()); }
    catch (e) { await new Promise(res => setTimeout(res, 1000 * (a + 1))); }
  }
  if (!buf) { console.error('fail', x, y); return; }
  if (buf[0] === 0x1f && buf[1] === 0x8b) buf = zlib.gunzipSync(buf);
  const mask = new Uint8Array(N * N), lines = [], roads = []; let ext = 4096;
  if (buf.length) {
    const vt = new VectorTile(new Pbf(buf));
    const W = vt.layers.water;
    if (W) { ext = W.extent; for (let i = 0; i < W.length; i++) { const ft = W.feature(i); if (ft.type !== 3 || ft.properties.class === 'swimming_pool') continue; fillRings(mask, ft.loadGeometry(), W.extent); } }
    const L = vt.layers.waterway;
    if (L) for (let i = 0; i < L.length; i++) {
      const ft = L.feature(i); if (ft.type !== 2) continue;
      const c = ft.properties.class, br = ft.properties.brunnel;
      for (const part of ft.loadGeometry()) lines.push([c, br === 'tunnel' ? 1 : 0, part.map(p => [Math.round(p.x * 4096 / L.extent), Math.round(p.y * 4096 / L.extent)])]);
    }
    // streets and lanes (OpenMapTiles transportation: primary to minor), used only as a proxy for the lines of old village
    // streets and town streets when laying out the houses
    const T = vt.layers.transportation, RC = { primary: 1, secondary: 1, tertiary: 2, minor: 3 };
    if (T) for (let i = 0; i < T.length; i++) {
      const ft = T.feature(i); if (ft.type !== 2) continue;
      const c = RC[ft.properties.class]; if (!c || ft.properties.brunnel === 'tunnel' || ft.properties.brunnel === 'bridge') continue;
      for (const part of ft.loadGeometry()) roads.push([c, part.map(p => [Math.round(p.x * 4096 / T.extent), Math.round(p.y * 4096 / T.extent)])]);
    }
  }
  // the mask as runs of rows: [row, start, end, ...] keeps the files tiny
  const runs = [];
  for (let r = 0; r < N; r++) { let c = 0; while (c < N) { if (mask[r * N + c]) { const s = c; while (c < N && mask[r * N + c]) c++; runs.push(r, s, c); } else c++; } }
  fs.writeFileSync(f, JSON.stringify({ r: runs, w: lines, t: roads }));
}
(async () => {
  let i = 0, done = 0; const C = 12;
  await Promise.all(Array.from({ length: C }, async () => { while (i < tiles.length) { const t = tiles[i++]; await one(t); if (++done % 500 === 0) console.log(done, '/', tiles.length); } }));
  console.log('done', done);
})();
