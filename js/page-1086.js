/* England in 1086, drawn: the page. Starts the Inked World engine in its 1086 mode (js/ink-map.js eraStyle, js/ink-worker.js
 * CFG.era), loads the vills (data/vills.json), and runs the layers panel, search, story buttons, popups, legend and stats.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  if (qs.has('maponly')) document.body.classList.add('maponly');
  if (qs.has('clean')) document.body.classList.add('clean');
  const base = new URL('./', location.href).href, DV = '?v=1086b';
  const opts = { era: 1086, winter: false, dv: DV,
    workerConfig: { era: 1, dw: base + 'data/dw/', dww: base + 'data/dww/', heritage: null, places: null, walls: null, houseRegions: null, hills: null, life: false, dv: DV } };
  if (qs.get('tj')) opts.tilejson = qs.get('tj');
  if (qs.get('dem')) opts.dem = qs.get('dem');
  if (qs.get('demmax')) opts.demMax = +qs.get('demmax');
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const ENG = [[-5.9, 49.9], [1.85, 55.0]];
  const STORIES = [
    ['All England', null, ENG],
    ['York and the wasted north', [-1.25, 54.05], 9.2],
    ['The Fens and Ely', [0.2, 52.42], 10.2],
    ['Droitwich salt', [-2.155, 52.269], 13.6],
    ['The New Forest', [-1.6, 50.88], 10.4],
    ['London and Westminster', [-0.11, 51.505], 12.6],
    ['Around Clitheroe', [-2.39, 53.88], 10.6],
  ];
  const pre = document.getElementById('presets');
  let map;
  STORIES.forEach(([n, c, z]) => {
    const b = document.createElement('button'); b.className = 'chip' + (c ? ' story' : ''); b.textContent = n;
    b.addEventListener('click', () => { if (!map) return; if (Array.isArray(z)) map.fitBounds(z, { padding: 20, duration: 2400, essential: true }); else map.flyTo({ center: c, zoom: z, duration: 2800, essential: true }); });
    pre.appendChild(b);
  });
  const start = qs.get('at') ? qs.get('at').split(',').map(Number) : null;
  const mapOptions = Object.assign({ minZoom: 5, maxZoom: 16.5, maxBounds: [[-11.5, 48.4], [5.5, 57.6]] },
    start ? { center: [start[1], start[0]], zoom: start[2] } : { bounds: ENG, fitBoundsOptions: { padding: 10 } });
  InkMap.create('map', Object.assign(opts, { mapOptions })).then(m => {
    map = window.__map = m;
    document.getElementById('nojs').remove();
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const fold = () => { const at = document.querySelector('.maplibregl-ctrl-attrib.maplibregl-compact'); if (at) { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); } };
    map.once('idle', fold); fold();
    if (window.InkExtras) { InkExtras.scaleBar(map, document.getElementById('scalebar')); document.getElementById('rose').innerHTML = InkExtras.compassSVG(58); }
    const zb = document.getElementById('zbadge');
    const upd = () => { zb.textContent = 'zoom ' + map.getZoom().toFixed(1); if (window.InkClouds && (!map.__clouds || map.__clouds.isOn())) { const s = document.createElement('span'); s.className = 'alt'; s.textContent = InkClouds.altitudeText(InkClouds.altitude(map)); zb.appendChild(s); } };
    map.on('zoom', upd); upd();
    const clouds = () => { if (window.InkClouds) { try { InkClouds.attach(map, { off: qs.has('noclouds'), onAlt: upd }); upd(); } catch (e) { console.warn('clouds', e); } } };
    if (map.loaded()) setTimeout(clouds, 200); else map.once('idle', () => setTimeout(clouds, 200));
    const isDark = () => { const r = document.documentElement; return r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; };
    const tone = () => InkMap.setSeaTone && InkMap.setSeaTone(map, isDark());
    tone(); new MutationObserver(tone).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    // the travellers on the old roads are the Inked World's own drawings (js/ink-life-art.js), drawn when first asked for
    map.on('styleimagemissing', e => { if (/^lr-/.test(e.id) && window.InkLifeArt && !map.hasImage(e.id)) { try { InkLifeArt.addOne(map, e.id); } catch (err) {} } });
    if (window.Ink1086) Ink1086.animate(map, { trim: InkMap.trim });
    loadVills(map).then(() => { setupSearch(map); });
    setupLand(map);
    setupLayers(map); setupPopups(map);
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });

  // ---------------- the vills (data/vills.json): far-zoom glyphs and names, search, and the index for popups
  let VILLS = null, SITES = {};
  async function loadVills(map) {
    const j = await (await fetch('data/vills.json' + DV)).json();
    const C = {}; j.cols.forEach((c, i) => C[c] = i);
    VILLS = new Map();
    const feats = [];
    for (const r of j.rows) {
      const v = { i: r[C.i], id: r[C.id], name: r[C.name], county: r[C.county], lon: r[C.lon], lat: r[C.lat], d: r[C.dwell], u: r[C.unsurveyed], t: r[C.town], c: r[C.church] || r[C.cathedral], w: r[C.waste], modern: r[C.modern], mills: r[C.mills], est: r[C.est] || 0, estBasis: r[C.estBasis] || '', estKind: r[C.estKind] || '' };
      VILLS.set(v.i, v);
      const d = v.u ? 0 : v.d + v.est;
      // names come in by size: towns first, then large vills, then hamlets (as the drawing fills in)
      const z = v.u ? 6 : (v.t && d >= 150) ? 5.8 : d >= 150 ? 7 : d >= 60 ? 8.3 : d >= 25 ? 9.6 : d >= 8 ? 10.8 : d >= 1 ? 11.9 : 12.4;
      feats.push({ type: 'Feature', properties: { i: v.i, n: v.name.replace(/[\[\]`{}]/g, ''), d, t: v.t, c: v.c, u: v.u, w: v.w, z }, geometry: { type: 'Point', coordinates: [v.lon, v.lat] } });
    }
    for (const s of j.sites || []) SITES[s.i] = s;
    map.getSource('vills').setData({ type: 'FeatureCollection', features: feats });
    // every vill Domesday calls waste, ringed in red (off until asked for)
    map.addLayer({ id: 'waste-rings', type: 'circle', source: 'vills', filter: ['==', ['get', 'w'], 1], layout: { visibility: 'none' },
      paint: { 'circle-color': 'rgba(163,38,27,0.08)', 'circle-stroke-color': '#A3261B', 'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], 6, 0.8, 12, 1.6], 'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 2.2, 10, 6, 13, 16], 'circle-stroke-opacity': 0.85 } }, 'vill-glyphs');
  }

  // ---------------- each vill's open fields, meadow, green and lanes (data/land/, zoom 9 cells), loaded round the view close in
  function setupLand(map) {
    let idx = null; const have = new Map(); let timer = null;
    const flush = () => { clearTimeout(timer); timer = setTimeout(() => { const fs = []; for (const v of have.values()) if (v) fs.push(...v); const s = map.getSource('land86x'); if (s) s.setData({ type: 'FeatureCollection', features: fs }); }, 80); };
    // coordinates come delta-coded in integers of 1e-5 degrees (code/04_place.py, enc)
    const dec = a => { const o = []; let x = 0, y = 0; for (let i = 0; i + 1 < a.length; i += 2) { x += a[i]; y += a[i + 1]; o.push([x / 1e5, y / 1e5]); } return o; };
    const conv = j => { const fs = [];
      for (const [v, p, r] of j.f || []) fs.push({ type: 'Feature', properties: { k: 'f', v, p }, geometry: { type: 'Polygon', coordinates: [dec(r)] } });
      for (const [v, r] of j.m || []) fs.push({ type: 'Feature', properties: { k: 'm', v }, geometry: { type: 'Polygon', coordinates: [dec(r)] } });
      for (const [v, r] of j.g || []) fs.push({ type: 'Feature', properties: { k: 'g', v }, geometry: { type: 'Polygon', coordinates: [dec(r)] } });
      for (const [v, l] of j.l || []) fs.push({ type: 'Feature', properties: { k: 'l', v }, geometry: { type: 'LineString', coordinates: dec(l) } });
      return fs; };
    const check = async () => {
      if (map.getZoom() < 10) return;
      idx = idx || (await (await fetch('data/land/index.json' + DV)).json()).cells.map(c => c[0] + '_' + c[1]);
      const set = new Set(idx), b = map.getBounds(), cx = lon => Math.floor((lon + 180) / 360 * 512), cy = lat => Math.floor((1 - Math.asinh(Math.tan(lat * Math.PI / 180)) / Math.PI) / 2 * 512);
      const want = [];
      for (let i = cx(b.getWest()) - 0; i <= cx(b.getEast()); i++) for (let j = cy(b.getNorth()); j <= cy(b.getSouth()); j++) { const k = i + '_' + j; if (set.has(k)) want.push(k); }
      if (want.length > 16) return;
      for (const k of want) if (!have.has(k)) { have.set(k, null); fetch('data/land/' + k + '.json' + DV).then(r => r.json()).then(j => { have.set(k, conv(j)); if (have.size > 40) { const first = have.keys().next().value; if (!want.includes(first)) have.delete(first); } flush(); }).catch(() => {}); }
    };
    map.on('moveend', check); if (map.loaded()) check(); else map.once('idle', check);
  }

  // ---------------- layers panel
  const DCAT = { houses: /^dh-(l|c|b|hall)/, churches: /^dch-/, mills: /^dmill/, castles: /^d(castle|gate)/, fish: /^d(fish|salt|vine)/, markets: /^d(market|stall)/,
    abbeys: /^dabbey/, stock: /^da-/, parks: /^d(park|haia)/, waste: /^d(h-w|waste)/ };
  function setupLayers(map) {
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    let SPR = null;
    fetch('data/dw/index.json' + DV).then(r => r.json()).then(j => { SPR = j.sprites; applyD(); });
    const dboxes = [...lp.querySelectorAll('input[data-d]')];
    function applyD() {
      if (!SPR || !map.getLayer('dw')) return;
      const off = dboxes.filter(b => !b.checked).map(b => DCAT[b.dataset.d]);
      const hidden = SPR.filter(s => off.some(rx => rx.test(s)));
      map.setFilter('dw', hidden.length ? ['!', ['in', ['get', 't'], ['literal', hidden]]] : null);
    }
    dboxes.forEach(b => b.addEventListener('change', applyD));
    lp.querySelectorAll('input[data-g]').forEach(b => {
      const apply = () => { InkMap.setGroup(map, b.dataset.g, b.checked); if (b.dataset.g === 'vills' && map.getLayer('waste-rings') && !b.checked) map.setLayoutProperty('waste-rings', 'visibility', 'none'); };
      b.addEventListener('change', apply);
      if (!b.checked) apply();
    });
    const wb = document.getElementById('wasteBox');
    wb.addEventListener('change', () => map.getLayer('waste-rings') && map.setLayoutProperty('waste-rings', 'visibility', wb.checked ? 'visible' : 'none'));
    const win = document.getElementById('winterBox'); win.checked = InkMap.isWinter(map);
    win.addEventListener('change', () => InkMap.setWinter(map, win.checked));
    const rose = document.getElementById('rose'), cb = document.getElementById('compassBox');
    cb.addEventListener('change', () => { rose.style.display = cb.checked ? '' : 'none'; });
    const clb = document.getElementById('cloudBox');
    try { clb.checked = !(localStorage.getItem('ink-clouds') === '0' || qs.has('noclouds')); } catch (e) {}
    clb.addEventListener('change', () => map.__clouds && map.__clouds.setOn(clb.checked));
    let frame = null; const fb = document.getElementById('frameBox');
    fb.addEventListener('change', () => { if (fb.checked && !frame && window.InkExtras) frame = InkExtras.frameOverlay(document.getElementById('map'), map); if (frame) frame.style.display = fb.checked ? '' : 'none'; });
  }

  // ---------------- search: Domesday's places (Hull's spelling, and the nearest modern name), hundreds and shires
  function norm(s) { return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[\[\]`'{}]/g, '').toLowerCase(); }
  function setupSearch(map) {
    const q = document.getElementById('q'), sug = document.getElementById('sug');
    const idx = [];
    for (const v of VILLS.values()) {
      idx.push({ k: norm(v.name), n: v.name.replace(/[\[\]`{}]/g, ''), ctx: CN[v.county] + (v.d ? ', ' + v.d + ' dwellings drawn' : ''), lon: v.lon, lat: v.lat, z: v.d >= 150 ? 13 : 14.2, s: v.d });
      if (v.modern) idx.push({ k: norm(v.modern), n: v.modern, ctx: 'today; Domesday ' + v.name.replace(/[\[\]]/g, '') + ', ' + CN[v.county], lon: v.lon, lat: v.lat, z: 14, s: v.d - 1 });
    }
    fetch('data/labels1086.geojson' + DV).then(r => r.json()).then(j => { for (const f of j.features) { const p = f.properties; if (p.kind === 'hundred' || p.kind === 'shire') idx.push({ k: norm(p.name), n: p.name, ctx: p.kind === 'shire' ? 'shire' : 'hundred, ' + p.county, lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1], z: p.kind === 'shire' ? 8 : 10.5, s: 5000 }); } });
    let items = [], sel = -1;
    function run() {
      const t = norm(q.value.trim()); if (t.length < 2) { sug.style.display = 'none'; return; }
      const sc = [];
      for (const r of idx) { const i = r.k.indexOf(t); if (i < 0) continue; sc.push([(i === 0 ? 0 : 10) + (r.k === t ? -5 : 0) - Math.min(4, Math.log10(1 + Math.max(0, r.s))), r]); }
      sc.sort((a, b) => a[0] - b[0]); items = sc.slice(0, 9).map(s => s[1]); sel = -1;
      sug.innerHTML = items.length ? items.map((r, i) => `<li role="option" data-i="${i}">${esc(r.n)} <span>${esc(r.ctx)}</span></li>`).join('') : '<li>No match</li>';
      sug.style.display = 'block';
    }
    function go(r) { if (!r) return; sug.style.display = 'none'; q.value = r.n; q.blur(); map.flyTo({ center: [r.lon, r.lat], zoom: r.z, duration: 2600, essential: true }); }
    q.addEventListener('input', run);
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); sel = Math.max(0, Math.min(items.length - 1, sel + (e.key === 'ArrowDown' ? 1 : -1))); [...sug.children].forEach((li, i) => li.setAttribute('aria-selected', i === sel)); }
      else if (e.key === 'Enter') { e.preventDefault(); go(items[sel < 0 ? 0 : sel]); }
      else if (e.key === 'Escape') sug.style.display = 'none';
    });
    sug.addEventListener('click', e => { const li = e.target.closest('li[data-i]'); if (li) go(items[+li.dataset.i]); });
    document.addEventListener('click', e => { if (!e.target.closest('.srch')) sug.style.display = 'none'; });
  }
  const CN = { BDF: 'Bedfordshire', BRK: 'Berkshire', BUK: 'Buckinghamshire', CAM: 'Cambridgeshire', CHS: 'Cheshire', CON: 'Cornwall', DBY: 'Derbyshire', DEV: 'Devon', DOR: 'Dorset',
    ESS: 'Essex', GLS: 'Gloucestershire', HAM: 'Hampshire', HEF: 'Herefordshire', HRT: 'Hertfordshire', HUN: 'Huntingdonshire', KEN: 'Kent', LEC: 'Leicestershire', LIN: 'Lincolnshire',
    MDX: 'Middlesex', NFK: 'Norfolk', NTH: 'Northamptonshire', NTT: 'Nottinghamshire', OXF: 'Oxfordshire', RUT: 'Rutland', SHR: 'Shropshire', SOM: 'Somerset', STS: 'Staffordshire',
    SUF: 'Suffolk', SUR: 'Surrey', SUS: 'Sussex', WAR: 'Warwickshire', WIL: 'Wiltshire', WOR: 'Worcestershire', YKS: 'Yorkshire' };

  // ---------------- popups: "In 1086 ..."
  const DET = {};
  const detail = c => DET[c] || (DET[c] = fetch('data/detail/' + c + '.json' + DV).then(r => r.json()));
  const fmt = n => (Math.round(n * 100) / 100).toLocaleString('en-GB');
  function money(d) {   // pence to pounds, shillings and pence
    if (d == null) return '';
    d = Math.round(d); const L = Math.floor(d / 240), s = Math.floor((d % 240) / 12), p = d % 12;
    if (!L && !s) return p + 'd';
    if (!L) return s + 's' + (p ? ' ' + p + 'd' : '');
    return '£' + L + (s ? ' ' + s + 's' : '') + (p ? ' ' + p + 'd' : '');
  }
  const CLS = { villagers: 'villagers', smallholders: 'smallholders', cottagers: 'cottagers', slaves: 'slaves', freemen: 'freemen (sokemen)', freeMen: 'free men', priests: 'priests', burgesses: 'burgesses', riders: 'riders', ploughmen: 'ploughmen', frenchmen: 'Frenchmen', smiths: 'smiths', swineherds: 'swineherds', fishermen: 'fishermen', menAtArms: 'men-at-arms' };
  const CLS1 = { villagers: 'villager', smallholders: 'smallholder', cottagers: 'cottager', slaves: 'slave', freemen: 'freeman (sokeman)', freeMen: 'free man', priests: 'priest', burgesses: 'burgess', riders: 'rider', ploughmen: 'ploughman', frenchmen: 'Frenchman', smiths: 'smith', swineherds: 'swineherd', fishermen: 'fisherman' };
  const STOCK = { sheep: ['sheep', 20], pigs: ['pigs', 10], cattle: ['cattle', 5], cows: ['cows', 5], goats: ['goats', 10], cobs: ['cobs', 3], horses: ['horses', 3], oxen: ['oxen', 4], beehives: ['beehives', 5], wildmares: ['wild mares', 5] };
  function head(t, D, v) {
    if (!t) return '';
    if (/^dmill/.test(t)) return `<div class="hd">${D.mr ? D.mr + (D.mr === 1 ? ' mill' : ' mills') : 'A share of a mill'}${D.mt && D.mt.length ? ': "' + esc(D.mt.join('; ')) + '"' : ''}. ${D.md || 0} drawn on the nearest stream${D.md < D.mr ? '; ' + (D.mr - D.md) + ' with no stream within 1.5 km on today\'s map, not drawn' : ''}.</div>`;
    if (/^dh-e/.test(t)) return `<div class="hd">Estimated: Domesday gives no usable household figure here, so ${v.est} dwellings are drawn pale and dotted. Method: ${esc(v.estBasis)}. Not counted in the recorded totals.</div>`;
    if (/^dh-x/.test(t)) return `<div class="hd">Estimated: Domesday calls this vill waste and counts nobody, so ${v.est} empty dwellings are drawn pale and roofless. Method: ${esc(v.estBasis)}. Not counted in the recorded totals.</div>`;
    if (/^dh-w/.test(t)) return '<div class="hd">A wasted or empty dwelling, drawn roofless.</div>';
    if (/^dh-hall/.test(t)) return '<div class="hd">The lord\'s hall (drawn where the manor has demesne ploughs or is worth £2 or more).</div>';
    if (/^dh-/.test(t)) return `<div class="hd">A dwelling: one of ${D.dw} drawn here, one for each household.</div>`;
    if (/^dch-cath/.test(t)) return '<div class="hd">The cathedral of the see in 1086.</div>';
    if (/^dch-minster/.test(t)) return '<div class="hd">A minster: the entry speaks of canons, monks or a minster.</div>';
    if (/^dch-/.test(t)) return `<div class="hd">A church: Domesday mentions one here (${D.ch} ${D.ch === 1 ? 'entry' : 'entries'}).</div>`;
    if (/^dcastle/.test(t)) return `<div class="hd">Castle: ${esc(D.castle || 'named in Domesday')}.</div>`;
    if (/^dabbey/.test(t)) return `<div class="hd">Religious house: ${esc((D.abbey || []).join('; '))}.</div>`;
    if (/^dsalt/.test(t)) return `<div class="hd">Salt: ${fmt(D.salt || 0)} salt-houses or salt-pans recorded (one hearth drawn per three).</div>`;
    if (/^dfish/.test(t)) return `<div class="hd">Fishery: ${fmt(D.fish || 1)} recorded${D.eels ? ', rendering ' + fmt(D.eels) + ' eels' : ''}.</div>`;
    if (/^dvine/.test(t)) return '<div class="hd">A vineyard (arpents of vines in the entry).</div>';
    if (/^dpark/.test(t)) return '<div class="hd">A park for woodland beasts.</div>';
    if (/^dhaia/.test(t)) return '<div class="hd">A hedged enclosure (haia) for taking deer.</div>';
    if (/^dmarket|^dstall/.test(t)) return `<div class="hd">A market${D.market ? ' (first recorded ' + esc(D.market) + ')' : ''}.</div>`;
    if (/^dwaste/.test(t)) return '<div class="hd">Waste: the entry calls the land waste and counts nobody living here.</div>';
    if (/^da-plough/.test(t)) return `<div class="hd">Plough teams: ${fmt(D.pt || 0)} recorded, eight oxen to a team; one team drawn per team.</div>`;
    if (/^da-pigwood/.test(t)) return `<div class="hd">Swine in the wood: woodland for ${fmt(D.wp || 0)} pigs (one drawn per 50).</div>`;
    const m = /^da-(\w+)/.exec(t);
    if (m) { const k = { sheep: 'sheep', pig: 'pigs', cattle: 'cattle', goat: 'goats', cob: 'cobs', mare: 'wildmares', hives: 'beehives', oxen: 'oxen' }[m[1]]; const st = (D.stock || {})[k] || (k === 'cattle' ? (D.stock || {}).cows : 0); return `<div class="hd">${STOCK[k] ? STOCK[k][0] : k}: ${fmt(st || 0)} recorded (one drawing per ${STOCK[k] ? STOCK[k][1] : 1}).</div>`; }
    return '';
  }
  function villHTML(v, D, t) {
    const rows = [];
    if (D.hh != null) rows.push(['Households', fmt(D.hh) + (D.cls ? ': ' + Object.entries(D.cls).map(([k, n]) => fmt(n) + ' ' + (n === 1 ? (CLS1[k] || CLS[k] || k) : (CLS[k] || k))).join(', ') : '')]);
    else rows.push(['Households', 'none counted']);
    rows.push(['Drawn', D.dw + ' dwellings from the record' + (v.est ? '; plus ' + v.est + (v.estKind === 'x' ? ' estimated empty (pale, roofless)' : ' estimated (pale, dotted)') : '')]);
    if (v.est) rows.push(['Estimated', esc(v.estBasis) + (v.u ? ' (left out of the survey)' : '')]);
    if (D.pt != null) rows.push(['Plough teams', fmt(D.pt) + (D.pl ? ' (land for ' + fmt(D.pl) + ')' : '')]);
    if (D.mr || D.mills) rows.push(['Mills', fmt(D.mills || D.mr) + (D.mt && D.mt.length ? ': ' + esc(D.mt.join('; ')) : '')]);
    if (D.ch) rows.push(['Church', 'yes']);
    if (D.mead) rows.push(['Meadow', fmt(D.mead) + ' acres']);
    if (D.wp || D.wha) rows.push(['Woodland', D.wp ? 'for ' + fmt(D.wp) + ' pigs' : 'measured (about ' + fmt(Math.round(D.wha)) + ' ha drawn as an estimate)']);
    if (D.fish) rows.push(['Fisheries', fmt(D.fish) + (D.eels ? ', ' + fmt(D.eels) + ' eels' : '')]);
    if (D.salt) rows.push(['Salt', fmt(D.salt) + ' salt-houses']);
    if (D.vine) rows.push(['Vineyard', 'yes']);
    if (D.stock && Object.keys(D.stock).length) rows.push(['Livestock', Object.entries(D.stock).map(([k, n]) => fmt(n) + ' ' + (STOCK[k] ? STOCK[k][0] : k)).join(', ')]);
    if (D.v66 != null || D.v86 != null) rows.push(['Value', (D.v66 != null ? money(D.v66) + ' in 1066; ' : '') + (D.v86 != null ? money(D.v86) + ' in 1086' : 'no 1086 value')]);
    if (D.l66) rows.push(['Held in 1066 by', esc(D.l66)]);
    if (D.tic) rows.push(['In 1086, of the King', esc(D.tic)]);
    if (D.t86) rows.push(['Held from them by', esc(D.t86)]);
    if (D.waste) rows.push(['Waste', 'the entry calls land here waste']);
    if (D.castle) rows.push(['Castle', esc(D.castle)]);
    if (D.abbey) rows.push(['Religious house', esc(D.abbey.join('; '))]);
    const q = D.q && D.q.length ? `<div class="q">"${esc(D.q[0][1])}" <span style="font-style:normal;color:#7A6A52">(${esc(D.q[0][0])})</span></div>` : '';
    const links = [D.od ? `<a href="https://opendomesday.org/place/${esc(D.od)}/" target="_blank" rel="noopener">Open Domesday</a>` : '', D.w ? `<a href="https://en.wikipedia.org/wiki/${encodeURIComponent(D.w.replace(/ /g, '_'))}" target="_blank" rel="noopener">Wikipedia</a>` : '',
      `<a href="https://maps.tristanhotham.com/domesday-destiny/" target="_blank" rel="noopener">Domesday Destiny</a>`].filter(Boolean).join(' · ');
    return `<b class="t">${esc(D.n.replace(/[\[\]`{}]/g, ''))}</b><div class="pl">${esc(D.c)}${D.h ? ', ' + esc(D.h) + ' hundred' : ''}${!v.u && D.m && D.m.toLowerCase() !== D.n.toLowerCase() ? '; nearest place today: ' + esc(D.m) : ''}${D.lost && !v.u ? ' (perhaps a lost village)' : ''}
      ${head(t, D, v)}<div style="font:500 12px var(--mono);margin-top:4px">In 1086 ...</div><table>${rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('')}</table>${q}
      <div>${links}</div>${(D.notes || []).map(n => `<p class="nt">${esc(n)}</p>`).join('')}<p class="nt">Entries: ${esc((D.refs || []).join('; '))}</p></div>`;
  }
  function siteHTML(s) {
    if (s.kind === 'castle') return `<b class="t">${esc(s.name)}</b><div class="pl">A castle built by 1086 (${s.year}, Wikidata ${esc(s.qid)}) that Domesday does not name; drawn ${s.stone ? 'as a stone keep' : 'as a motte and bailey'}. From the <a href="https://maps.tristanhotham.com/norman-castles/" target="_blank" rel="noopener">Norman castles</a> study.</div>`;
    return `<b class="t">${esc(s.name)}</b><div class="pl">${esc(s.order)}, founded by ${s.founded}; outside the lands Domesday surveyed, placed by hand.</div>`;
  }
  const LAYER_TEXT = {
    'shire-names': p => `<b class="t">${esc(p.name)}</b><div class="pl">A shire of 1086; ${p.n} vills located. Its edge on the map is approximate (drawn between its vills).</div>`,
    'hundred-names': p => `<b class="t">${esc(p.name)}</b><div class="pl">A hundred (or wapentake) of ${esc(p.county)}, lettered at the middle of its ${p.n} located vills.</div>`,
    'kingdom-names': p => `<b class="t">${esc(p.name)}</b><div class="pl">${p.kind === 'kingdom' ? 'A kingdom or principality beyond the survey in 1086.' : 'A land of 1086.'}${p.note ? ' ' + esc(p.note) + '.' : ''} Lettered by hand.</div>`,
    'forest-names': p => `<b class="t">${esc(p.name)}</b><div class="pl">A royal forest Domesday names${p.name === 'The New Forest' ? '; its outline joins the vills the Hampshire folios list in the New Forest (approximate)' : ''}.</div>`,
    'highway-names': p => `<b class="t">${esc(p.name)}</b><div class="pl">One of the four great highways under the King's peace; its name is lettered along an approximate line.</div>`,
    'tw-crest': p => `<b class="t">The walls of ${esc(p.n || 'the borough')}</b><div class="pl">The line of its Roman or medieval wall as OpenStreetMap maps it today (Winchester's traced by hand), standing in for the defences of 1086; some stretches are later.</div>`,
    'roman-case': p => `<b class="t">${esc(p.name || 'Roman road')}</b><div class="pl">A Roman road (Itiner-e, ${esc(p.cert || '')}), still the main way through the country in 1086.</div>`,
    'unsurv': () => `<b class="t">Not surveyed in 1086</b><div class="pl">Domesday stops at the Tees, the Ribble and the Welsh March: the north, Wales and Scotland were not surveyed. People lived here; the survey simply did not count them.</div>`,
    'marsh86': p => `<b class="t">${esc(p.name)}</b><div class="pl">Fen and marsh, drawn where the ground lies low in this basin today (Terrarium elevation, zoom 8): an approximate picture of the wetland of 1086.</div>`,
    'wantsum': () => `<b class="t">Wantsum Channel</b><div class="pl">The sea channel that made Thanet an island in 1086; drawn by hand along the Stour levels, approximate.</div>`,
  };
  function setupPopups(map) {
    const LAY = ['dw', 'vill-glyphs', 'vill-names', 'shire-names', 'hundred-names', 'kingdom-names', 'forest-names', 'highway-names', 'tw-crest', 'roman-case', 'marsh86', 'wantsum', 'unsurv'];
    map.on('click', async e => {
      const bb = [[e.point.x - 6, e.point.y - 6], [e.point.x + 6, e.point.y + 6]];
      const fs = map.queryRenderedFeatures(bb, { layers: LAY.filter(id => map.getLayer(id) && map.getLayoutProperty(id, 'visibility') !== 'none') });
      if (!fs.length) return;
      const f = fs[0], p = f.properties, id = f.layer.id;
      const pop = new maplibregl.Popup({ closeButton: true, maxWidth: '330px' }).setLngLat(e.lngLat);
      if (id === 'dw' || id === 'vill-glyphs' || id === 'vill-names') {
        const vi = id === 'dw' ? p.v : p.i;
        if (vi < 0) { pop.setHTML(`<b class="t">Travellers</b><div class="pl">On a Roman road: decoration, in period dress. Domesday records no traffic.</div>`).addTo(map); return; }
        if (vi >= 100000) { const s = SITES[vi]; if (s) pop.setHTML(siteHTML(s)).addTo(map); return; }
        const v = VILLS && VILLS.get(vi); if (!v) return;
        pop.setHTML(`<b class="t">${esc(v.name)}</b><div class="pl">Reading the entry…</div>`).addTo(map);
        try { const D = (await detail(v.county))[vi]; if (D) pop.setHTML(villHTML(v, D, id === 'dw' ? p.t : null)); } catch (err) { console.warn(err); }
        return;
      }
      const fn = LAYER_TEXT[id]; if (fn) pop.setHTML(fn(p)).addTo(map);
    });
    map.on('mousemove', e => {
      const fs = map.queryRenderedFeatures([[e.point.x - 4, e.point.y - 4], [e.point.x + 4, e.point.y + 4]], { layers: LAY.slice(0, 9).filter(id => map.getLayer(id)) });
      map.getCanvas().style.cursor = fs.length ? 'pointer' : '';
    });
  }

  // ---------------- the legend: every period drawing, drawn by the same code as the map
  (function () {
    const el = document.getElementById('legend'); if (!el) return;
    const L = [
      ['The vill', [['dh-l0', 'Villager\'s longhouse: one for each household of villagers or freemen'], ['dh-c0', 'Cottage: smallholders, cottagers, slaves and priests'], ['dh-b0', 'Burgess\'s house in a borough'], ['dh-hall', 'The lord\'s hall in its fenced court'], ['dh-w1', 'Wasted or empty dwelling, roofless'], ['dh-e0', 'Estimated dwelling, where Domesday gives no usable figure (not in the totals)'], ['dh-x0', 'Estimated empty dwelling in a waste vill (not in the totals)'], ['dwaste', 'A vill Domesday calls waste, with nobody counted']]],
      ['Church and castle', [['dch-wood', 'Timber church'], ['dch-stone', 'Stone church with a round-headed tower (larger vills and towns)'], ['dch-minster', 'Minster: canons or monks named'], ['dch-cathedral', 'Cathedral of the see in 1086'], ['dabbey', 'Religious house standing in 1086'], ['dcastle-m', 'Motte-and-bailey castle'], ['dcastle-k', 'Stone keep, where documented by 1086'], ['dgate', 'Town bank, wall and gate (boroughs of 150 dwellings or more)']]],
      ['Making a living', [['dmill-l', 'Watermill: one wheel for each mill recorded, on the nearest stream'], ['dfish', 'Fishery: an eel weir with wicker traps'], ['dsalt', 'Salt-pans and a boiling hearth on the coast'], ['dsalt-w', 'Brine pit and lead pans at the inland wiches'], ['dvine', 'Vineyard'], ['dmarket', 'Market'], ['dpark', 'Park for woodland beasts'], ['dhaia', 'Hedged enclosure (haia)']]],
      ['Beasts and ploughs', [['da-plough', 'Plough team: eight oxen, one drawn per team'], ['da-sheep', 'Sheep: one flock per 20'], ['da-pigwood', 'Swine at pannage: one per 50 pigs of woodland'], ['da-pig', 'Pigs: one per 10'], ['da-cattle', 'Cattle: one per 5'], ['da-goat', 'Goats: one per 10'], ['da-cob', 'Cobs and horses: one per 3'], ['da-mare', 'Wild mares: one per 5'], ['da-hives', 'Beehives: one per 5'], ['da-oxen', 'Oxen counted apart from teams: one per 4']]],
      ['Far out', [['dv-3c', 'A vill: huts to its size, a church where recorded'], ['dvt-9c', 'A borough, walled where its wall line is known'], ['dv-unsurveyed', 'London and Winchester, left out of the survey (houses estimated)'], ['wdp', 'Woodland, from Domesday\'s measures'], ['rf1', 'Open fields in ridge and furrow, sized to the plough teams'], ['mdw86', 'Meadow by the stream, sized to the acres recorded'], ['mrs', 'Fen and marsh (approximate)']]],
    ];
    const go = () => { for (const [h, items] of L) { const hd = document.createElement('h3'); hd.textContent = h; el.appendChild(hd); for (const [id, label] of items) { const c = window.InkIcons && InkIcons.draw(id); if (!c) continue; const d = document.createElement('div'); d.appendChild(c); const s = document.createElement('span'); s.textContent = label; d.appendChild(s); el.appendChild(d); } } };
    if ('IntersectionObserver' in window) { const io = new IntersectionObserver(es => { if (es.some(x => x.isIntersecting)) { io.disconnect(); go(); } }, { rootMargin: '600px' }); io.observe(el); } else setTimeout(go, 3000);
  })();

  // ---------------- theme and cartouche
  const th = document.getElementById('theme');
  th.addEventListener('click', () => { const r = document.documentElement; const dark = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = dark ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'), ctT = document.getElementById('ctToggle');
  const foldC = f => { ct.classList.toggle('folded', f); ctT.setAttribute('aria-expanded', String(!f)); };
  if (matchMedia('(max-width:600px)').matches) foldC(true);
  ctT.addEventListener('click', () => foldC(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => foldC(true));
  (function () {
    const mapEl = document.getElementById('map'); let done = false;
    const first = e => { if (done || (e && e.target && e.target.closest && e.target.closest('.cartouche,.ov,.lp,.mfs-btn,.maplibregl-ctrl'))) return; done = true; foldC(true); ['pointerdown', 'wheel', 'keydown'].forEach(t => mapEl.removeEventListener(t, first, true)); };
    ['pointerdown', 'wheel', 'keydown'].forEach(t => mapEl.addEventListener(t, first, { capture: true, passive: true }));
  })();
  document.addEventListener('fullscreenchange', () => { if (document.fullscreenElement) foldC(true); });
})();
