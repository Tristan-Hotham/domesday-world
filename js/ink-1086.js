/* England in 1086, drawn: the period drawings, in the Inked World's pen (js/ink-icons.js Pen: brown-black ink, paper,
 * hatching for shade, the same bird's-eye viewpoint as the townhouses, depth running up and to the right).
 * Houses of villagers, smallholders and burgesses, the lord's hall, wasted dwellings; timber and stone churches, minsters
 * and cathedrals; the watermill with its undershot wheel and leat (animated); motte-and-bailey and stone castles; salt-pans,
 * brine pits, eel weirs, vineyards, parks, hedged enclosures, abbeys; plough teams of eight oxen, flocks, swine, cattle,
 * goats, cobs, wild mares and bee skeps; and the vill glyphs used far out. Every drawing is original.
 * Registered through InkIcons.addAll (lazily, the first time a tile asks for one).
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function (global) {
  'use strict';
  const PAL = global.InkPalette || {};
  const INK = PAL.ink || '#2B2119', PAPER = PAL.paperFill || 'rgba(243,229,191,0.97)', RED = PAL.red || '#A3261B', BLUE = PAL.blue || '#3D6E9E';
  const BLUES = PAL.blueSoft || '#6F9DC6';
  const DV = [0.38, -0.7];
  const THATCH = ['#C7A35C', '#9B7A3C'], THATCH2 = ['#B8975A', '#8D6E3A'], SHINGLE = ['#8A6A4E', '#664C36'], STONE = ['#D2C6A8', '#A99B7C'];
  const DAUB = ['#EEE0BC', '#CDB98F'], TIMBER = '#5A4030', DARK = '#3A2C20', GREEN = '#8FA46A', GREENS = '#6F8550', WATER = '#9DBBD6';
  const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];

  // ---------------- a bird's-eye house with a thatched (or shingled, or stone-slated) roof and no chimney
  // o: x, gy (ground), w (front width), hw (wall height), d (depth), rh (roof rise), roof: [lit, shade], wall: [lit, shade],
  // gable (ridge runs back from the front), hip (thatch rounded at the ends), door, smoke (a wisp from the louvre)
  function hut(p, o) {
    const { x: x0, gy, w, hw, d, rh } = o, R = o.roof || THATCH, Wc = o.wall || DAUB;
    const dx = DV[0] * d, dy = DV[1] * d, top = gy - hw, x1 = x0 + w;
    const A = [x0, gy], B = [x1, gy], At = [x0, top], Bt = [x1, top];
    const Bb = [B[0] + dx, B[1] + dy], Bbt = [Bt[0] + dx, Bt[1] + dy], Abt = [At[0] + dx, At[1] + dy];
    p.poly([B, Bb, Bbt, Bt], Wc[1], 0.8);                                     // side wall in shade
    if (o.gable) {
      const F = [x0 + w / 2, top - rh], Fb = [F[0] + dx, F[1] + dy];
      p.poly([Bt, Bbt, Fb, F], R[1], 0.8); straw(p, Bt, Bbt, Fb, F, 0.35);
      p.poly([At, Abt, Fb, F], R[0], 0.8); straw(p, At, Abt, Fb, F, 0.3);
      p.poly([A, B, Bt, F, At], Wc[0], 0.85);                                 // gable front
      if (o.post !== false) { p.col(TIMBER).line([[x0 + 0.5, gy], [x0 + 0.5, top]], 0.7).line([[x1 - 0.5, gy], [x1 - 0.5, top]], 0.7).line([At, F, Bt], 0.75).col(INK); }
      if (o.smoke) smoke(p, Fb[0] - dx * 0.5, Fb[1] - dy * 0.5 - 0.5);
    } else {
      const hip = o.hip ? Math.min(w * 0.22, 2.6) : 0;
      const R1 = [x0 + dx / 2 + hip, top + dy / 2 - rh], R2 = [x1 + dx / 2 - hip, top + dy / 2 - rh];
      p.poly([Abt, Bbt, R2, R1], R[1], 0.8);                                  // back slope, just seen
      if (hip) { p.poly([Bt, Bbt, R2], R[1], 0.8); straw(p, Bt, Bbt, R2, R2, 0.3); }
      else p.poly([Bt, Bbt, R2], Wc[1], 0.8);
      p.poly([At, Bt, R2, R1], R[0], 0.85); straw(p, At, Bt, R2, R1, 0.32);  // the big front slope
      if (hip) { p.poly([At, R1, Abt], R[0], 0.7); }
      p.col(R[1]).line([R1, R2], 1.1).col(INK);                              // ridge
      p.poly([A, B, Bt, At], Wc[0], 0.85);                                    // front wall: wattle and daub between posts
      if (o.post !== false) { p.col(TIMBER); const n = Math.max(1, Math.round(w / 4)); for (let i = 0; i <= n; i++) { const xx = x0 + 0.4 + (w - 0.8) * i / n; p.line([[xx, gy], [xx, top]], 0.6); } p.col(INK); }
      if (o.smoke) smoke(p, (R1[0] + R2[0]) / 2, (R1[1] + R2[1]) / 2 - 0.4);
    }
    if (o.door !== false) { const dxo = x0 + w * (o.doorAt || 0.45); p.rect(dxo - 0.8, gy - 2.7, 1.6, 2.7, DARK, 0); }
    p.col(INK).line([A, B], 0.9);
  }
  // straw: fine strokes down a thatched slope, from the ridge towards the eaves
  function straw(p, e0, e1, t1, t0, op) {
    p.col('rgba(60,40,18,' + (op || 0.3) + ')');
    for (let k = 1; k < 7; k++) { const t = k / 7, a = lerp(e0, e1, t), b = lerp(t0, t1, t); p.line([lerp(b, a, 0.08), lerp(b, a, 0.9)], 0.35); }
    p.col('rgba(60,40,18,0.55)').line([e0, e1], 0.9).col(INK);              // the thick eaves of the thatch
  }
  function smoke(p, x, y) { p.col('rgba(120,112,104,0.55)').line([[x, y], [x - 0.8, y - 1.6], [x + 0.3, y - 3], [x - 0.5, y - 4.4]], 0.6).col(INK); }
  function fence(p, pts, h) { p.col(TIMBER); for (let i = 0; i < pts.length - 1; i++) { const a = pts[i], b = pts[i + 1]; p.line([a, b], 0.5); const n = Math.max(1, Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) / 2.2)); for (let k = 0; k <= n; k++) { const q = lerp(a, b, k / n); p.line([q, [q[0], q[1] - (h || 1.6)]], 0.45); } } p.col(INK); }
  function tuft(p, x, y, s) { s = s || 1; p.col(GREENS).line([[x - 1.2 * s, y], [x - 1.6 * s, y - 1.6 * s]], 0.5).line([[x, y], [x, y - 2 * s]], 0.5).line([[x + 1.2 * s, y], [x + 1.6 * s, y - 1.6 * s]], 0.5).col(INK); }
  function arch(p, cx, y, w, h, fill) { const pts = [[cx - w / 2, y], [cx - w / 2, y - h + w / 2]]; for (let i = 0; i <= 8; i++) { const a = Math.PI + Math.PI * i / 8; pts.push([cx + Math.cos(a) * w / 2, y - h + w / 2 + Math.sin(a) * w / 2]); } pts.push([cx + w / 2, y]); p.poly(pts, fill || DARK, 0); }

  // ---------------- houses of the vill
  function longhouse(p, v) {   // villagers and freemen: a long low house, byre at one end, thatch hipped
    const gy = 20, L = [[3, 15, 4.2, 9, 5.6], [2, 17, 4, 8, 5.2], [4, 13, 4.6, 10, 6], [3, 16, 4.4, 9, 5.8]][v];
    hut(p, { x: L[0], gy, w: L[1], hw: L[2], d: L[3], rh: L[4], hip: true, roof: v % 2 ? THATCH2 : THATCH, smoke: v !== 2, doorAt: 0.3 });
    if (v === 1) p.rect(L[0] + L[1] * 0.72, gy - 2.4, 1.8, 2.4, DARK, 0);   // the byre door
    if (v === 3) fence(p, [[0.5, gy + 1.5], [8, gy + 2.6], [16, gy + 2.2]], 1.4);
  }
  function cottage(p, v) {     // smallholders, cottagers, slaves: small cruck cottages and huts
    const gy = 17;
    if (v === 0) hut(p, { x: 4, gy, w: 8, hw: 3.4, d: 7, rh: 5.2, gable: true, roof: THATCH, smoke: true });
    else if (v === 1) hut(p, { x: 3, gy, w: 10, hw: 3.2, d: 7, rh: 4.6, hip: true, roof: THATCH2 });
    else if (v === 2) { hut(p, { x: 3, gy, w: 7, hw: 3, d: 6, rh: 4.6, gable: true, roof: THATCH2, post: false }); fence(p, [[10.5, gy + 0.5], [15, gy - 0.5]], 1.3); }
    else { hut(p, { x: 4, gy, w: 9, hw: 2.6, d: 8, rh: 5, hip: true, roof: THATCH, smoke: true }); tuft(p, 2, gy + 1.5, 0.8); }
  }
  function burgage(p, v) {     // burgesses: town houses, some gable to the street, some eaves to it; thatch or shingles, a few of two storeys
    const gy = 22;
    if (v === 0) hut(p, { x: 4, gy, w: 8, hw: 4.6, d: 11, rh: 6.4, gable: true, roof: THATCH, smoke: true });
    else if (v === 1) { hut(p, { x: 3, gy, w: 12, hw: 6, d: 9, rh: 5.6, roof: SHINGLE }); p.rect(6.5, gy - 5, 1.2, 1.2, DARK, 0); p.rect(11, gy - 5, 1.2, 1.2, DARK, 0); }
    else if (v === 2) hut(p, { x: 3, gy, w: 13, hw: 4.4, d: 9, rh: 5.4, hip: true, roof: THATCH2, smoke: true });
    else if (v === 3) { hut(p, { x: 2, gy, w: 7, hw: 5, d: 10, rh: 6, gable: true, roof: SHINGLE }); hut(p, { x: 9.5, gy: gy + 0.5, w: 7, hw: 4.2, d: 10, rh: 5.6, gable: true, roof: THATCH }); }
    else if (v === 4) hut(p, { x: 3, gy, w: 12, hw: 4.8, d: 9, rh: 5.6, roof: THATCH, doorAt: 0.3 });
    else { hut(p, { x: 2, gy, w: 9, hw: 4.4, d: 9, rh: 5.2, roof: THATCH2 }); hut(p, { x: 11, gy: gy + 0.4, w: 6, hw: 4.6, d: 9, rh: 6, gable: true, roof: SHINGLE }); }
  }
  function ruin(p, v) {        // a wasted dwelling: roofless walls, charred rafters, ash
    const gy = 17, x0 = 3 + v, w = 9 - v, hw = 3;
    const dx = DV[0] * 7, dy = DV[1] * 7;
    p.poly([[x0, gy], [x0 + w, gy], [x0 + w + dx, gy + dy], [x0 + dx, gy + dy]], '#BFAE8A', 0.6);   // the floor
    p.poly([[x0 + w, gy], [x0 + w + dx, gy + dy], [x0 + w + dx, gy + dy - hw * 0.6], [x0 + w, gy - hw]], DAUB[1], 0.8);
    p.poly([[x0, gy], [x0 + w * 0.6, gy], [x0 + w * 0.45, gy - hw * 0.5], [x0 + w * 0.2, gy - hw], [x0, gy - hw * 0.8]], DAUB[0], 0.8);
    p.col('#2A1C12').line([[x0 + 1, gy - hw], [x0 + w * 0.5 + dx * 0.5, gy - hw - 3.5 + dy * 0.3]], 0.9).line([[x0 + w, gy - hw], [x0 + w * 0.6 + dx * 0.5, gy - hw - 2.8 + dy * 0.3]], 0.8).col(INK);
    for (let i = 0; i < 5; i++) p.dot(x0 + 1.5 + i * 1.6, gy - 0.8 + (i % 2) * 0.6, 0.45, '#3B3029');
  }
  function hall(p) {           // the lord's hall: a big aisled hall in a fenced curia, with a barn
    const gy = 26;
    fence(p, [[1, gy + 1.5], [14, gy + 3], [30, gy + 2], [33, gy - 6]], 1.8);
    hut(p, { x: 4, gy, w: 19, hw: 5.6, d: 12, rh: 7.6, hip: true, roof: THATCH, smoke: true, doorAt: 0.55 });
    hut(p, { x: 24, gy: gy - 2, w: 7, hw: 4, d: 8, rh: 5, gable: true, roof: THATCH2 });
    p.rect(8, gy - 4.2, 1.2, 1.4, DARK, 0); p.rect(17, gy - 4.2, 1.2, 1.4, DARK, 0);
  }

  // ---------------- churches
  function nave(p, x0, gy, w, hw, d, rh, wall, roof) {
    hut(p, { x: x0, gy, w, hw, d, rh, roof: roof || STONE, wall: wall || STONE, post: false, door: false });
    const n = Math.max(1, Math.round(w / 4)); for (let i = 0; i < n; i++) arch(p, x0 + (i + 0.5) * w / n, gy - hw * 0.35, 1.1, 2.3);
  }
  function tower(p, cx, gy, tw, th, opt) {   // a square tower seen at the same angle, round-headed belfry openings
    opt = opt || {};
    const d = tw * 0.9, dx = DV[0] * d, dy = DV[1] * d, x0 = cx - tw / 2, x1 = cx + tw / 2, top = gy - th;
    const W = opt.wall || STONE;
    p.poly([[x1, gy], [x1 + dx, gy + dy], [x1 + dx, top + dy], [x1, top]], W[1], 0.85);
    p.hatch([[x1, gy], [x1 + dx, gy + dy], [x1 + dx, top + dy], [x1, top]], 70, 1.4, 0.4, 'rgba(43,33,25,0.45)');
    p.poly([[x0, gy], [x1, gy], [x1, top], [x0, top]], W[0], 0.9);
    if (opt.stone !== false) { p.col('rgba(95,80,58,0.5)'); for (let yy = top + 1.8; yy < gy; yy += 1.8) p.line([[x0 + 0.3, yy], [x1 - 0.3, yy]], 0.3); p.col(INK); }
    arch(p, cx - tw * 0.18, top + th * 0.32, tw * 0.2, tw * 0.45); arch(p, cx + tw * 0.18, top + th * 0.32, tw * 0.2, tw * 0.45);
    if (opt.cap === 'pyr') { p.poly([[x0 - 0.4, top], [cx + dx / 2, top + dy / 2 - tw * 0.8], [x1 + dx + 0.3, top + dy], [x1 + 0.4, top]], opt.roof || SHINGLE[0], 0.9); p.poly([[x1 + 0.4, top], [x1 + dx + 0.3, top + dy], [cx + dx / 2, top + dy / 2 - tw * 0.8]], (opt.roof2 || SHINGLE[1]), 0.8); }
    else { p.poly([[x0, top], [x1, top], [x1 + dx, top + dy], [x0 + dx, top + dy]], '#C4B593', 0.7); for (let i = 0; i < 3; i++) p.rect(x0 + i * tw / 2.5, top - 1.3, tw / 5, 1.3, W[0], 0.6); }
    if (opt.cross) p.col(INK).line([[cx + dx / 2, top + dy / 2 - tw * 0.8], [cx + dx / 2, top + dy / 2 - tw * 0.8 - 3]], 0.7).line([[cx + dx / 2 - 1, top + dy / 2 - tw * 0.8 - 2], [cx + dx / 2 + 1, top + dy / 2 - tw * 0.8 - 2]], 0.6);
  }
  function churchWood(p) {    // a small timber church: nave and chancel, shingle roof, a little bell-cote and a cross
    const gy = 22;
    hut(p, { x: 3, gy, w: 11, hw: 5, d: 8, rh: 5.2, roof: SHINGLE, wall: ['#C9A97C', '#9E7F55'], door: false });
    hut(p, { x: 14, gy: gy - 0.5, w: 6, hw: 4, d: 6, rh: 4.2, roof: SHINGLE, wall: ['#C9A97C', '#9E7F55'], door: false });
    p.col(TIMBER); for (let i = 0; i < 6; i++) p.line([[4 + i * 1.9, gy], [4 + i * 1.9, gy - 5]], 0.5); p.col(INK);
    arch(p, 7.5, gy, 1.8, 3.2);
    p.rect(5.2, gy - 13.2, 2.6, 3.4, '#C9A97C', 0.8); p.poly([[4.6, gy - 13.2], [6.5, gy - 16.2], [8.4, gy - 13.2]], SHINGLE[0], 0.8);
    p.line([[6.5, gy - 16.2], [6.5, gy - 19]], 0.8).line([[5.4, gy - 18], [7.6, gy - 18]], 0.7);
  }
  function churchStone(p) {   // an early Norman stone church: a squat west tower with round-headed openings, nave and apse
    const gy = 26;
    nave(p, 9, gy, 12, 6, 9, 5.6);
    p.ell(23.8, gy - 3.2, 3.3, 3.2, STONE[0], 0.85, -Math.PI / 2, Math.PI / 2);   // the apse
    p.poly([[21, gy - 6.2], [24, gy - 5.2], [21.8, gy - 8.4]], STONE[1], 0.7);
    tower(p, 6, gy + 0.5, 6.4, 14, { cap: 'pyr', roof: '#7A6C5C', roof2: '#5C5045', cross: true });
    arch(p, 6, gy + 0.5, 1.8, 3.2);
  }
  function minster(p) {       // a minster: cruciform, a central tower, a long nave and transepts
    const gy = 30;
    nave(p, 3, gy, 14, 7, 11, 6.5);
    nave(p, 23, gy - 1, 10, 6.4, 10, 6);
    hut(p, { x: 17, gy: gy + 1, w: 6, hw: 7.6, d: 4, rh: 5, roof: STONE, wall: STONE, gable: true, post: false, door: false });   // the transept front
    tower(p, 20, gy - 6.2, 7.2, 12, { cap: 'pyr', roof: '#6E6A62', roof2: '#4F4B45', cross: true });
    arch(p, 6, gy, 2, 3.6);
  }
  function cathedral(p) {     // a great Romanesque church: twin west towers, long nave, central tower, apse
    const gy = 38;
    nave(p, 13, gy, 20, 9, 13, 7.5);
    p.ell(41.5, gy - 4.5, 4.3, 4.5, STONE[0], 0.9, -Math.PI / 2, Math.PI / 2);
    nave(p, 33, gy - 0.5, 8, 8.6, 12, 7);
    tower(p, 31, gy - 9, 8, 13, { cap: 'pyr', roof: '#6E6A62', roof2: '#4F4B45', cross: true });
    tower(p, 5, gy + 0.6, 7, 21, { cap: 'pyr', roof: '#6E6A62', roof2: '#4F4B45' });
    tower(p, 12.5, gy + 0.2, 7, 21, { cap: 'pyr', roof: '#6E6A62', roof2: '#4F4B45' });
    arch(p, 9, gy, 3, 5.2);
    p.flag(31 + 1.6, gy - 9 - 13 - 6.5, 0.7);
  }
  function abbey(p) {         // a religious house: church with tower, the cloister garth and the monks' ranges
    const gy = 32;
    p.poly([[6, gy + 1], [26, gy + 1], [26 + DV[0] * 14, gy + 1 + DV[1] * 14], [6 + DV[0] * 14, gy + 1 + DV[1] * 14]], '#C9D3A0', 0.9);   // the garth
    p.hatch([[8, gy], [24, gy], [24 + DV[0] * 10, gy + DV[1] * 10], [8 + DV[0] * 10, gy + DV[1] * 10]], 0, 2.2, 0.35, 'rgba(79,107,58,0.6)');
    hut(p, { x: 26, gy: gy + 1, w: 5, hw: 4.5, d: 14, rh: 4, roof: STONE, wall: STONE, gable: true, post: false, door: false });
    nave(p, 4, gy - 9, 18, 6.5, 6, 5.6);
    tower(p, 9, gy - 8.6, 6, 12, { cap: 'pyr', roof: '#6E6A62', roof2: '#4F4B45', cross: true });
    hut(p, { x: 6, gy: gy + 1.5, w: 20, hw: 3.8, d: 4, rh: 3.4, roof: STONE, wall: STONE, post: false, door: false });
    for (let i = 0; i < 5; i++) arch(p, 8 + i * 3.8, gy + 1.5, 1.2, 2.4);
  }

  // ---------------- the watermill: a timber mill house by a big undershot wheel turning in the stream, with its leat
  // f = frame (the wheel's angle): js/ink-1086.js animate() swaps the frames in place with map.updateImage, so nothing else redraws
  const MILL_W = 34, MILL_H = 30;
  // left: the mill house on the left of its wheel (the village lies that way); the wheel's hub is at (WX, WY), where the
  // style anchors the drawing on the stream
  function mill(p, left, f) {
    const gy = 20;
    // corner marks (all but invisible) so every frame trims to the same box
    p.rect(0, 0, 0.7, 0.7, 'rgba(243,229,191,0.08)', 0); p.rect(MILL_W - 0.7, MILL_H - 0.7, 0.7, 0.7, 'rgba(243,229,191,0.08)', 0);
    const cx = left ? 23 : 11, cy = gy + 1.6, R = 6.6, m = left ? 1 : -1;
    // the stream under the wheel, flowing across, and the leat (the mill race) brought along the bank to the wheel
    p.poly([[0.5, gy + 5.2], [33.5, gy + 3.4], [33.5, gy + 8.6], [0.5, gy + 10]], WATER, 0);
    p.col(BLUE).line([[0.5, gy + 5.2], [33.5, gy + 3.4]], 0.7).line([[0.5, gy + 10], [33.5, gy + 8.6]], 0.7);
    p.col(BLUES); for (let i = 0; i < 5; i++) { const u = 2 + i * 6.4 + (f % 3) * 2.1; if (Math.abs(u - cx) < 4) continue; p.line([[u, gy + 7.4 - u * 0.045], [u + 2.6, gy + 7.3 - u * 0.045]], 0.5); }
    const lx0 = left ? 33 : 1, lx1 = cx + m * 4.5;
    p.poly([[lx0, gy + 1.2], [lx1, gy + 2.2], [lx1, gy + 3.6], [lx0, gy + 2.8]], WATER, 0.5);
    p.col(BLUE).line([[lx0, gy + 1.2], [lx1, gy + 2.2]], 0.6).col(INK);
    // the mill house: timber-framed and thatched, its gable end over the wheel
    const hx = left ? 2 : 17;
    hut(p, { x: hx, gy: gy + 1, w: 14, hw: 6.4, d: 9, rh: 6.6, roof: THATCH2, doorAt: left ? 0.3 : 0.7, smoke: false });
    p.col(TIMBER).line([[hx, gy - 2.4], [hx + 14, gy - 2.4]], 0.6).col(INK);
    p.rect(hx + (left ? 9 : 3), gy - 4.4, 1.4, 1.4, DARK, 0);
    // the wheel: two rims, eight spokes and paddles, turning (f); the lower paddles dip into the water
    const a0 = f * Math.PI / 12;
    p.ell(cx, cy, R, R, null, 1.25); p.ell(cx, cy, R * 0.6, R * 0.6, null, 0.55);
    for (let k = 0; k < 8; k++) {
      const a = a0 + k * Math.PI / 4, c = Math.cos(a), s2 = Math.sin(a);
      p.line([[cx + c * 0.9, cy + s2 * 0.9], [cx + c * R, cy + s2 * R]], 0.6);
      p.line([[cx + c * (R - 0.4), cy + s2 * (R - 0.4)], [cx + c * (R + 1.9), cy + s2 * (R + 1.9)]], 1.15);
    }
    p.dot(cx, cy, 1.1, DARK);
    p.line([[cx, cy], [cx - m * 4.2, cy - 1.2]], 1.1);                       // the axle into the house
    // white water where the paddles bite
    p.col('rgba(255,255,255,0.95)').line([[cx - 3.2, gy + 7.2], [cx - 1.8, gy + 6.2]], 0.7).line([[cx + 1.6, gy + 6.1], [cx + 3.2, gy + 7]], 0.7).col(INK);
  }
  // ---------------- castles
  function motte(p) {         // motte and bailey in timber: the mound with its tower, the bailey palisade, ditch and bridge
    const gy = 34;
    p.ell(22, gy - 2, 16, 6.5, '#C9D3A0', 1.1);                              // the bailey
    p.ell(22, gy - 2, 18, 7.6, null, 0.6);                                    // its ditch
    fence(p, [[6, gy - 2], [10, gy + 3.4], [22, gy + 4.6], [34, gy + 3.4], [38, gy - 2]], 2.4);
    fence(p, [[6, gy - 2], [11, gy - 6.5], [22, gy - 8.2], [33, gy - 6.5], [38, gy - 2]], 2);
    hut(p, { x: 21, gy: gy - 1, w: 8, hw: 3.2, d: 6, rh: 4, roof: THATCH2 });  // a hall in the bailey
    // the motte, hatched on its shaded side, the tower on top
    p.poly([[1, gy + 1], [5, gy - 11], [13, gy - 12], [17, gy + 1]], '#CDBE8F', 1.2);
    p.hatch([[9, gy - 12], [13, gy - 12], [17, gy + 1], [10, gy + 1]], 70, 1.6, 0.5);
    fence(p, [[4.5, gy - 11], [13.5, gy - 12]], 1.6);
    p.rect(6.4, gy - 20, 6, 8.2, '#C9A97C', 1); p.col(TIMBER); for (let i = 0; i < 4; i++) p.line([[7 + i * 1.6, gy - 12], [7 + i * 1.6, gy - 20]], 0.5); p.col(INK);
    p.poly([[5.6, gy - 20], [9.4, gy - 24], [13.2, gy - 20]], SHINGLE[0], 0.9);
    p.flag(9.4, gy - 24, 0.8);
    p.line([[15, gy - 8], [20, gy - 5.6]], 1);                               // the flying bridge
  }
  function keep(p) {          // a stone keep (the White Tower, Colchester, Chepstow, Richmond): square, buttressed, corner turrets
    const gy = 36;
    p.ell(16, gy - 1, 14, 4.5, '#C9D3A0', 0.9);
    tower(p, 15, gy, 16, 21, { cap: 'cren' });
    for (const tx of [7.5, 22.5]) p.rect(tx - 1.6, gy - 24, 3.2, 3.5, STONE[0], 0.8);
    for (const tx of [9, 15, 21]) arch(p, tx, gy - 13, 1.4, 2.8);
    arch(p, 15, gy, 2.4, 4);
    p.flag(22.5, gy - 24, 0.9);
  }
  function gate(p) {          // a burh gate in the town's bank and timber wall
    const gy = 24;
    p.poly([[0, gy + 1], [3, gy - 3], [29, gy - 3], [32, gy + 1]], '#C9B98A', 0.9);   // the bank
    fence(p, [[1, gy - 3], [11, gy - 3]], 4); fence(p, [[21, gy - 3], [31, gy - 3]], 4);
    tower(p, 16, gy, 9, 13, { cap: 'pyr', wall: ['#C9A97C', '#9E7F55'], stone: false, roof: SHINGLE[0], roof2: SHINGLE[1] });
    arch(p, 16, gy, 3.6, 6.4);
  }

  // ---------------- salt, fish, vines, parks, the market
  function saltpan(p) {       // coastal salt-making: shallow pans on the marsh and a hearth boiling the brine under a lean-to
    const gy = 19;
    for (const [x, y] of [[2, gy], [10, gy + 1.5], [5, gy + 4]]) { p.poly([[x, y], [x + 7, y], [x + 7 + 2.2, y - 2.2], [x + 2.2, y - 2.2]], '#DCE7EE', 0.7); p.col(BLUES).line([[x + 1.5, y - 0.8], [x + 6, y - 0.8]], 0.4).col(INK); }
    hut(p, { x: 19, gy: gy + 1, w: 8, hw: 3, d: 6, rh: 3.5, roof: THATCH2, door: false });
    p.poly([[20, gy + 1], [21, gy - 1.2], [25, gy - 1.2], [26, gy + 1]], '#3B3029', 0.5);
    for (let i = 0; i < 3; i++) p.dot(21.8 + i * 1.5, gy + 0.2, 0.5, '#D3602B');
    p.col('rgba(140,132,124,0.7)').line([[23, gy - 8], [22, gy - 10.5], [23.5, gy - 13], [22.2, gy - 15.5]], 0.8).col(INK);
  }
  function brine(p) {         // the inland wiches: a brine pit with its frame and lead pans over wood fires
    const gy = 20;
    p.ell(7, gy - 1, 5, 2.2, '#9DBBD6', 0.9); p.ell(7, gy - 1, 3.2, 1.3, null, 0.4);
    p.line([[3.5, gy - 1], [7, gy - 8], [10.5, gy - 1]], 0.9); p.line([[7, gy - 8], [7, gy - 3]], 0.5);
    for (const x of [14, 21]) { p.poly([[x, gy], [x + 6, gy], [x + 5, gy - 2], [x + 1, gy - 2]], '#8C8C94', 0.8); for (let i = 0; i < 3; i++) p.dot(x + 1.6 + i * 1.4, gy + 0.6, 0.5, '#D3602B'); }
    p.col('rgba(140,132,124,0.7)').line([[17, gy - 3], [16, gy - 6], [17.5, gy - 9]], 0.7).line([[24, gy - 3], [23, gy - 6], [24.6, gy - 9]], 0.7).col(INK);
  }
  function fishery(p) {       // an eel weir: a V of wattle hurdles across the water, wicker traps in the gap, eels
    const gy = 18;
    p.poly([[0, gy - 7], [30, gy - 9], [30, gy + 3], [0, gy + 5]], WATER, 0);
    p.col(BLUE).line([[0, gy - 7], [30, gy - 9]], 0.6).line([[0, gy + 5], [30, gy + 3]], 0.6).col(INK);
    p.col(TIMBER).line([[3, gy - 6.5], [15, gy - 1.2]], 1.2).line([[3, gy + 4.4], [15, gy + 0.4]], 1.2);
    for (let i = 0; i < 6; i++) { p.line([[3 + i * 2, gy - 6.5 + i * 0.88], [3 + i * 2, gy - 8 + i * 0.88]], 0.5); p.line([[3 + i * 2, gy + 4.4 - i * 0.67], [3 + i * 2, gy + 2.9 - i * 0.67]], 0.5); }
    p.col(INK);
    p.ell(18.5, gy - 0.4, 3.6, 1.6, '#C9A97C', 0.8); for (let k = 0; k < 4; k++) p.line([[16 + k * 1.6, gy - 1.8], [16 + k * 1.6, gy + 1]], 0.35);   // the wicker trap
    for (const [x, y, s] of [[24, gy - 4, 1], [22, gy + 2, -1], [27, gy, 1]]) p.col(DARK).line([[x, y], [x + 1.2, y - 0.8 * s], [x + 2.6, y + 0.2 * s], [x + 3.8, y - 0.6 * s], [x + 5, y]], 0.8);
    p.col(INK);
  }
  function vineyard(p) {      // rows of vines on stakes on a sunny bank, with a little watch hut
    const gy = 22;
    p.poly([[1, gy + 1], [27, gy + 1], [29, gy - 9], [5, gy - 11]], '#D9CE97', 0.7);
    for (let r = 0; r < 4; r++) for (let k = 0; k < 6; k++) { const x = 4 + k * 3.8 + r * 0.6, y = gy - 1 - r * 2.8; p.col(TIMBER).line([[x, y], [x, y - 2.6]], 0.45); p.dot(x - 0.6, y - 2.4, 0.75, '#5E7A3A'); p.dot(x + 0.7, y - 2, 0.65, '#6E2C4E'); }
    p.col(INK);
  }
  function park(p) {          // a park for woodland beasts: the pale (a fence of split oak) round trees and deer
    const gy = 26;
    const ring = []; for (let i = 0; i <= 14; i++) { const a = Math.PI * 2 * i / 14; ring.push([18 + Math.cos(a) * 15, gy - 7 + Math.sin(a) * 6.5]); }
    p.poly(ring, '#D2D9AE', 0); fence(p, ring.slice(6, 15), 2);
    for (const [x, y] of [[10, gy - 9], [25, gy - 10]]) { p.line([[x, y + 2], [x, y - 1]], 1); p.ell(x, y - 3.5, 3.4, 3, '#9FB27A', 1); }
    deer(p, 16, gy - 4); fence(p, ring.slice(0, 7), 2);
  }
  function haia(p) {          // a hedged enclosure (haia) for taking deer: a laid hedge with an opening
    const gy = 18;
    for (let i = 0; i < 12; i++) { const x = 2 + i * 2.3, y = gy - (i < 6 ? i * 0.6 : (11 - i) * 0.6); if (i === 5 || i === 6) continue; p.ell(x, y - 1.5, 1.6, 1.4, '#8FA46A', 0.6); }
    deer(p, 14, gy - 2.5, 0.8);
  }
  function deer(p, x, y, s) {
    s = s || 1; p.poly([[x - 3 * s, y], [x - 2.6 * s, y - 2 * s], [x + 2 * s, y - 2.2 * s], [x + 2.4 * s, y]], '#B98A55', 0.6);
    p.line([[x - 2.6 * s, y], [x - 2.6 * s, y + 2 * s]], 0.5).line([[x + 2 * s, y], [x + 2 * s, y + 2 * s]], 0.5);
    p.line([[x + 2 * s, y - 2 * s], [x + 3.2 * s, y - 3.8 * s]], 0.8); p.line([[x + 3.2 * s, y - 3.8 * s], [x + 2.6 * s, y - 6 * s]], 0.4).line([[x + 3.2 * s, y - 3.8 * s], [x + 4.4 * s, y - 6 * s]], 0.4);
  }
  function market(p) {        // a market place: a cross on steps in an open space, with a well
    const gy = 20;
    p.ell(12, gy - 2, 11, 4.4, '#E4D6AE', 0.7);
    p.rect(9, gy - 2, 6, 1.4, STONE[0], 0.7); p.rect(10, gy - 3.2, 4, 1.2, STONE[0], 0.7);
    p.line([[12, gy - 3.2], [12, gy - 12]], 1.3).line([[9.6, gy - 9.6], [14.4, gy - 9.6]], 1.1);
    p.poly([[3, gy - 4], [6, gy - 6], [6, gy - 3.6]], RED, 0.6);
  }
  function stall(p) {
    p.rect(3, 9, 11, 5, PAPER, 1); p.poly([[1.5, 9.5], [15.5, 9.5], [13.5, 5], [3.5, 5]], '#B8862B', 0.9); p.dot(6, 11.5, 0.8); p.dot(9.5, 11.5, 0.8, RED);
  }
  function waste(p) {         // a wasted vill: burnt and roofless huts, with a crow
    ruin(p, 0); p.x.save(); p.x.translate(10, 4); ruin(p, 2); p.x.restore();
    p.col(DARK).line([[22, 5], [23.5, 4], [25, 5]], 0.7).line([[25, 5], [26.5, 4], [28, 5]], 0.7).col(INK);
  }

  // ---------------- beasts and the plough
  function ox(p, x, y, s, c) { s = s || 1; p.poly([[x - 2.6 * s, y], [x - 2.4 * s, y - 2.2 * s], [x + 1.8 * s, y - 2.4 * s], [x + 2.4 * s, y - 0.2 * s]], c || '#B79A72', 0.6); p.ell(x + 2.8 * s, y - 2 * s, 1.1 * s, 0.9 * s, c || '#B79A72', 0.5); p.line([[x + 2.6 * s, y - 2.8 * s], [x + 3.6 * s, y - 3.6 * s]], 0.4); for (const lx of [-2, -1, 1, 1.8]) p.line([[x + lx * s, y], [x + lx * s, y + 1.6 * s]], 0.5); }
  function plough(p) {        // a plough team: four yokes of oxen (eight to a team), the ploughman at the stilts, a goad-boy, furrows behind
    const gy = 16;
    p.col('rgba(110,86,52,0.55)'); for (let k = 0; k < 4; k++) p.line([[1, gy + 3 + k * 1.3], [12, gy + 1.4 + k * 1.3]], 0.5); p.col(INK);
    for (let i = 0; i < 4; i++) { ox(p, 15 + i * 6.2, gy - 0.6 - i * 0.4, 0.8, i % 2 ? '#A88A62' : '#C2A57C'); ox(p, 17 + i * 6.2, gy + 1.4 - i * 0.4, 0.8, i % 2 ? '#C2A57C' : '#9F8158'); }
    p.line([[13.5, gy + 0.6], [40, gy - 1.6]], 0.5);                                         // the chain
    p.poly([[9, gy + 1.6], [13.5, gy + 0.6], [12.5, gy + 2.4]], '#7A6048', 0.6);             // the plough
    p.line([[9, gy + 1.6], [6.5, gy - 3]], 0.8);                                             // stilts
    p.ell(5.8, gy - 5.2, 1.1, 1.1, '#E8C9A0', 0.5); p.poly([[5, gy - 4], [6.8, gy - 4], [7.2, gy - 0.4], [4.8, gy - 0.4]], '#8E5B3A', 0.5);   // the ploughman
    p.ell(41.5, gy - 6.4, 0.9, 0.9, '#E8C9A0', 0.4); p.poly([[40.8, gy - 5.5], [42.2, gy - 5.5], [42.6, gy - 2.8], [40.6, gy - 2.8]], '#5E7A3A', 0.4); p.line([[42.4, gy - 5], [38, gy - 7.6]], 0.4);
  }
  function sheep(p, n) {      // a flock: woolly backs, dark faces
    const pos = [[4, 12], [10, 10], [15, 13], [8, 15], [19, 10], [13, 8]];
    for (let i = 0; i < n; i++) { const [x, y] = pos[i]; p.ell(x, y, 2.8, 1.9, '#F4EEDC', 0.7); p.ell(x + 2.6, y - 0.8, 0.9, 0.8, DARK, 0); p.line([[x - 1.4, y + 1.6], [x - 1.4, y + 2.6]], 0.45).line([[x + 1.2, y + 1.6], [x + 1.2, y + 2.6]], 0.45); }
    tuft(p, 21, 15, 0.7);
  }
  function pig(p, x, y, s, c) { s = s || 1; p.ell(x, y, 3 * s, 1.9 * s, c || '#C99A86', 0.7); p.poly([[x + 2.6 * s, y - 0.8 * s], [x + 4.2 * s, y - 0.3 * s], [x + 2.8 * s, y + 0.6 * s]], c || '#C99A86', 0.5); p.line([[x + 1.8 * s, y - 1.6 * s], [x + 2.6 * s, y - 2.4 * s]], 0.5); for (const lx of [-1.8, -0.6, 0.8, 1.8]) p.line([[x + lx * s, y + 1.5 * s], [x + lx * s, y + 2.6 * s]], 0.5); p.line([[x - 3 * s, y - 0.4 * s], [x - 3.8 * s, y - 1.2 * s]], 0.4); }
  function pigs(p) { pig(p, 6, 12, 1, '#C99A86'); pig(p, 14, 13.5, 0.85, '#8E6A5A'); }
  function pigwood(p) {       // swine at pannage: pigs rooting for acorns under an oak, a swineherd knocking down mast
    p.line([[16, 16], [16, 7]], 1.6); p.ell(16, 5.5, 7, 5, '#93A86B', 1.1); p.hatch([[16, 1], [23, 5.5], [16, 10]], 60, 1.6, 0.5);
    for (let i = 0; i < 4; i++) p.dot(12 + i * 2.6, 17.2 + (i % 2) * 0.5, 0.45, '#7A5A2A');
    pig(p, 8, 16, 0.85, '#8E6A5A'); pig(p, 23, 17, 0.75, '#C99A86');
  }
  function cattle(p) { ox(p, 6, 12, 1, '#A8714A'); ox(p, 14, 14, 0.9, '#E8DCC4'); tuft(p, 20, 15, 0.7); }
  function oxen(p) { ox(p, 6, 12, 1, '#C2A57C'); ox(p, 13, 13.5, 1, '#9F8158'); }
  function goat(p, x, y, s, c) { s = s || 1; p.poly([[x - 2.2 * s, y], [x - 2 * s, y - 1.8 * s], [x + 1.6 * s, y - 1.9 * s], [x + 2 * s, y]], c || '#E3D9C4', 0.6); p.line([[x + 1.8 * s, y - 1.6 * s], [x + 2.8 * s, y - 3 * s]], 0.7); p.line([[x + 2.8 * s, y - 3 * s], [x + 2 * s, y - 4.4 * s]], 0.5); p.line([[x + 3, y - 2.2 * s], [x + 3.2, y - 1 * s]], 0.4); for (const lx of [-1.6, -0.8, 1, 1.6]) p.line([[x + lx * s, y], [x + lx * s, y + 1.8 * s]], 0.45); }
  function goats(p) { goat(p, 6, 12, 1, '#E3D9C4'); goat(p, 12, 13.5, 0.9, '#7A5E48'); }
  function horse(p, x, y, s, c, run) {
    s = s || 1; c = c || '#8E5B3A';
    p.poly([[x - 3 * s, y], [x - 2.8 * s, y - 2.4 * s], [x + 2.2 * s, y - 2.6 * s], [x + 2.6 * s, y]], c, 0.6);
    p.poly([[x + 2 * s, y - 2.4 * s], [x + 3.6 * s, y - 5 * s], [x + 4.8 * s, y - 4.4 * s], [x + 3 * s, y - 1.6 * s]], c, 0.5);
    p.col(DARK).line([[x + 2.4 * s, y - 3 * s], [x + 3.4 * s, y - 5.2 * s]], 0.6).line([[x - 3 * s, y - 2 * s], [x - 4.4 * s, y + 0.4 * s]], 0.7).col(INK);
    if (run) { p.line([[x - 2.6 * s, y], [x - 4 * s, y + 1.6 * s]], 0.5).line([[x - 1.6 * s, y], [x - 0.6 * s, y + 2 * s]], 0.5).line([[x + 1.6 * s, y], [x + 0.4 * s, y + 2 * s]], 0.5).line([[x + 2.4 * s, y], [x + 3.8 * s, y + 1.6 * s]], 0.5); }
    else for (const lx of [-2.4, -1.4, 1.4, 2.2]) p.line([[x + lx * s, y], [x + lx * s, y + 2.4 * s]], 0.5);
  }
  function cob(p) { horse(p, 9, 13, 1, '#8E5B3A'); tuft(p, 17, 15, 0.7); }
  function mares(p) { horse(p, 7, 12, 0.9, '#B9895A', true); horse(p, 16, 14.5, 0.85, '#5E4636', true); }
  function hives(p) {         // straw bee skeps on a bench, with bees
    p.line([[2, 13], [18, 13]], 1); p.line([[3, 13], [3, 15.5]], 0.6).line([[17, 13], [17, 15.5]], 0.6);
    for (const x of [5.5, 10, 14.5]) { const pts = []; for (let i = 0; i <= 10; i++) { const a = Math.PI + Math.PI * i / 10; pts.push([x + Math.cos(a) * 2.4, 13 + Math.sin(a) * 3.6]); } p.poly(pts, '#D8B66A', 0.7); p.col('rgba(90,60,20,0.6)'); for (let k = 1; k < 3; k++) p.line([[x - 2.1, 13 - k * 1.1], [x + 2.1, 13 - k * 1.1]], 0.4); p.col(INK); p.dot(x, 12.4, 0.45, DARK); }
    for (const [x, y] of [[8, 6], [12, 5], [15.5, 7.5]]) p.dot(x, y, 0.5, DARK);
  }

  // ---------------- vill glyphs for the far zooms: a few huts to the household count, a church, a town in its bank and wall
  function villGlyph(p, n, ch, town) {
    const gy = town ? 26 : 18;
    if (town) {
      p.ell(20, gy - 5, 18, 7.5, '#E6D6AE', 1.1); p.ell(20, gy - 5, 18, 7.5, null, 0.6);
      const ring = []; for (let i = 0; i <= 16; i++) { const a = Math.PI * i / 16; ring.push([20 - Math.cos(a) * 18, gy - 5 + Math.sin(a) * 7.5]); }
      fence(p, ring, 2.6);
    }
    const pos = town ? [[6, gy - 6], [12, gy - 10], [26, gy - 9], [30, gy - 4], [14, gy - 1], [22, gy], [9, gy - 1.5], [28, gy + 1], [18, gy - 11]] : [[2, gy], [9, gy + 1.2], [15, gy - 2.5], [5, gy - 4.5], [20, gy + 0.6], [11, gy - 5.8]];
    for (let i = 0; i < n; i++) { const [x, y] = pos[i % pos.length]; hut(p, { x, gy: y, w: 6, hw: 2.4, d: 5, rh: 3.6, hip: i % 2 === 0, gable: i % 2 === 1, roof: i % 3 ? THATCH : THATCH2, post: false, door: true }); }
    if (ch) { const cx = town ? 20 : 14, cy = town ? gy - 3 : gy - 0.5; hut(p, { x: cx - 3, gy: cy, w: 6, hw: 3.4, d: 5, rh: 3.2, roof: STONE, wall: STONE, post: false, door: false }); tower(p, cx - 4.4, cy + 0.3, 3.2, 7.6, { cap: 'pyr', roof: '#6E6A62', roof2: '#4F4B45', stone: false }); }
  }
  function unsurveyed(p) {    // London or Winchester: walls and a great church, no houses (the survey left them out)
    const gy = 30;
    const ring = []; for (let i = 0; i <= 20; i++) { const a = Math.PI * 2 * i / 20; ring.push([24 + Math.cos(a) * 21, gy - 8 + Math.sin(a) * 9]); }
    p.poly(ring, '#E6D6AE', 1.4);
    p.hatch(ring, 30, 2.6, 0.35, 'rgba(110,90,60,0.45)');
    for (let i = 0; i < 20; i += 3) p.rect(ring[i][0] - 1.4, ring[i][1] - 3, 2.8, 3, STONE[0], 0.8);
    tower(p, 20, gy - 6, 5, 13, { cap: 'pyr', roof: '#6E6A62', roof2: '#4F4B45', cross: true });
    nave(p, 23, gy - 6, 10, 5, 6, 4.6);
  }

  const DEFS = {
    'dh-hall': [36, 32, p => hall(p)], 'dch-wood': [24, 26, p => churchWood(p)], 'dch-stone': [32, 30, p => churchStone(p)],
    'dch-minster': [38, 36, p => minster(p)], 'dch-cathedral': [50, 52, p => cathedral(p)], 'dabbey': [36, 38, p => abbey(p)],
    'dmarket': [24, 22, p => market(p)], 'dstall': [18, 16, p => stall(p)], 'dcastle-m': [40, 40, p => motte(p)], 'dcastle-k': [32, 40, p => keep(p)],
    'dgate': [32, 28, p => gate(p)], 'dsalt': [30, 22, p => saltpan(p)], 'dsalt-w': [30, 22, p => brine(p)], 'dfish': [30, 26, p => fishery(p)],
    'dvine': [30, 24, p => vineyard(p)], 'dpark': [36, 30, p => park(p)], 'dhaia': [30, 22, p => haia(p)], 'dwaste': [30, 22, p => waste(p)],
    'da-plough': [46, 22, p => plough(p)], 'da-sheep': [24, 18, p => sheep(p, 5)], 'da-pig': [20, 18, p => pigs(p)], 'da-pigwood': [28, 20, p => pigwood(p)],
    'da-cattle': [22, 18, p => cattle(p)], 'da-goat': [18, 18, p => goats(p)], 'da-cob': [20, 18, p => cob(p)], 'da-mare': [22, 18, p => mares(p)],
    'da-hives': [20, 17, p => hives(p)], 'da-oxen': [20, 17, p => oxen(p)], 'dv-unsurveyed': [48, 34, p => unsurveyed(p)],
  };
  for (let v = 0; v < 4; v++) { DEFS['dh-l' + v] = [24, 22, p => longhouse(p, v)]; DEFS['dh-c' + v] = [18, 19, p => cottage(p, v)]; }
  for (let v = 0; v < 6; v++) DEFS['dh-b' + v] = [20, 24, p => burgage(p, v)];
  for (let v = 0; v < 3; v++) DEFS['dh-w' + v] = [16, 19, p => ruin(p, v)];
  for (let n = 1; n <= 6; n++) for (const ch of [0, 1]) DEFS['dv-' + n + (ch ? 'c' : '')] = [26, 22, p => villGlyph(p, n, ch, false)];
  for (let n = 4; n <= 9; n += 5) for (const ch of [0, 1]) DEFS['dvt-' + n + (ch ? 'c' : '')] = [40, 30, p => villGlyph(p, n, ch, true)];
  DEFS['dmill-l'] = [MILL_W, MILL_H, p => mill(p, true, 0)]; DEFS['dmill-r'] = [MILL_W, MILL_H, p => mill(p, false, 0)];

  // fill patterns for the far zooms: a wood of little trees, and the marsh (tufts and pools); corner marks keep the tile whole
  function patWood(p) {
    p.rect(0, 0, 0.6, 0.6, 'rgba(243,229,191,0.08)', 0); p.rect(31.4, 31.4, 0.6, 0.6, 'rgba(243,229,191,0.08)', 0);
    for (const [x, y, r] of [[7, 10, 3.6], [22, 6, 3.2], [16, 22, 3.8], [28, 26, 3], [4, 27, 2.8]]) { p.line([[x, y + r], [x, y + r + 2.2]], 0.8); p.ell(x, y, r, r * 0.9, '#A6B67E', 0.8); p.hatch([[x, y - r], [x + r, y], [x, y + r]], 60, 1.4, 0.4); }
  }
  function patMarsh(p) {
    p.rect(0, 0, 0.6, 0.6, 'rgba(243,229,191,0.08)', 0); p.rect(31.4, 31.4, 0.6, 0.6, 'rgba(243,229,191,0.08)', 0);
    for (const [x, y] of [[6, 8], [20, 14], [10, 25], [27, 28]]) tuft(p, x, y, 0.9);
    p.col(BLUE); for (const [x, y] of [[13, 5], [25, 6], [3, 17], [17, 30]]) p.line([[x, y], [x + 4.5, y]], 0.55); p.col(INK);
  }
  // an estimated dwelling (Domesday gives no usable figure here): the same house, pale and outlined with a dotted pen
  function estHouse(p, v) {
    const gy = 17, x0 = [4, 3, 4][v], w = [8, 10, 9][v];
    const dx = DV[0] * 7, dy = DV[1] * 7, top = gy - 3.2, R1 = [x0 + dx / 2, top + dy / 2 - 4.6], R2 = [x0 + w + dx / 2, top + dy / 2 - 4.6];
    p.x.setLineDash([0.9, 1.1]);
    p.poly([[x0 + w, gy], [x0 + w + dx, gy + dy], [x0 + w + dx, top + dy], [x0 + w, top]], 'rgba(226,214,186,0.9)', 0.7);
    p.poly([[x0, top], [x0 + w, top], R2, R1], 'rgba(222,204,160,0.9)', 0.7);
    p.poly([[x0, gy], [x0 + w, gy], [x0 + w, top], [x0, top]], 'rgba(244,236,214,0.92)', 0.7);
    p.x.setLineDash([]);
    p.rect(x0 + w * 0.42 - 0.7, gy - 2.3, 1.4, 2.3, 'rgba(90,72,52,0.6)', 0);
  }
  for (let v = 0; v < 3; v++) DEFS['dh-e' + v] = [18, 19, p => estHouse(p, v)];
  // an estimated dwelling standing empty (a waste vill with nobody counted): the roofless ruin, pale
  for (let v = 0; v < 3; v++) DEFS['dh-x' + v] = [16, 19, p => { p.x.globalAlpha = 0.42; ruin(p, v); p.x.globalAlpha = 1; }];
  // ridge and furrow: the ploughed strips of the open fields, in four directions (seamless tiles)
  function patStrips(p, d) {
    p.rect(0, 0, 0.6, 0.6, 'rgba(243,229,191,0.08)', 0); p.rect(23.4, 23.4, 0.6, 0.6, 'rgba(243,229,191,0.08)', 0);
    p.x.fillStyle = 'rgba(214,186,120,0.22)'; p.x.fillRect(0, 0, 24, 24);
    p.x.strokeStyle = 'rgba(110,84,46,0.5)'; p.x.lineWidth = 0.7; p.x.lineCap = 'butt';
    for (let k = -24; k <= 48; k += 4) {
      p.x.beginPath();
      if (d === 0) { p.x.moveTo(0, k); p.x.lineTo(24, k); }
      else if (d === 1) { p.x.moveTo(k, 0); p.x.lineTo(k, 24); }
      else if (d === 2) { p.x.moveTo(k, 0); p.x.lineTo(k - 24, 24); }
      else { p.x.moveTo(k - 24, 0); p.x.lineTo(k, 24); }
      p.x.stroke();
    }
  }
  for (let d = 0; d < 4; d++) DEFS['rf' + d] = [24, 24, p => patStrips(p, d)];
  function patMeadow(p) {
    p.rect(0, 0, 0.6, 0.6, 'rgba(243,229,191,0.08)', 0); p.rect(23.4, 23.4, 0.6, 0.6, 'rgba(243,229,191,0.08)', 0);
    p.x.fillStyle = 'rgba(150,178,104,0.35)'; p.x.fillRect(0, 0, 24, 24);
    for (const [x, y] of [[5, 7], [16, 4], [11, 15], [21, 19], [3, 21]]) tuft(p, x, y, 0.6);
  }
  DEFS['mdw86'] = [24, 24, p => patMeadow(p)];
  DEFS['wdp'] = [32, 32, p => patWood(p)]; DEFS['mrs'] = [32, 32, p => patMarsh(p)];
  let PenRef = null, trimRef = null;
  function register(add, Pen) {
    PenRef = Pen;
    for (const [id, [w, h, f]] of Object.entries(DEFS)) add(id, w, h, f);
  }
  // the turning wheel: a few frames of each mill sprite, swapped in place while the map rests with mills in view
  const FRAMES = 6;
  function millFrame(left, f) {
    const p = PenRef(MILL_W, MILL_H, 4242 + (left ? 1 : 0)); mill(p, left, f); return p.done();
  }
  function animate(map, opts) {
    if (!PenRef || map.__millAnim) return;
    opts = opts || {};
    const reduce = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return;
    const cache = { l: [], r: [] };
    const frame = (side, f) => {
      if (!cache[side][f]) {
        const c = millFrame(side === 'l', f), t = opts.trim ? opts.trim(c) : c;
        // frames must match the registered image exactly: trim the same way the first was (same bounds every frame)
        cache[side][f] = t.getContext('2d').getImageData(0, 0, t.width, t.height);
      }
      return cache[side][f];
    };
    let f = 0, moving = false, timer = null;
    map.on('movestart', () => { moving = true; }); map.on('moveend', () => { moving = false; });
    const tick = () => {
      timer = setTimeout(tick, 220);
      if (moving || document.hidden || map.getZoom() < 12.3 || map.__millsOff) return;
      f = (f + 1) % FRAMES;
      for (const side of ['l', 'r']) {
        const id = 'dmill-' + side; if (!map.hasImage(id)) continue;
        try { const im = frame(side, f); const cur = map.style.getImage(id); if (cur && cur.data && cur.data.width === im.width && cur.data.height === im.height) map.updateImage(id, im); } catch (e) { /* never break the map over a wheel */ }
      }
    };
    map.__millAnim = true; tick();
  }
  global.Ink1086 = { register, animate, DEFS };
})(window);
