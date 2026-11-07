"""Step 4. Lay out every vill as Domesday describes it: one drawn dwelling per recorded household, its church, hall and
market at the centre, its mills on the nearest stream, its plough teams, flocks and herds spread over its lands, its
woodland as a wood beside it, and its salt-pans, fisheries, vineyards, parks and castles where the survey puts them.

Inputs: WORK/places.pkl (02_places.py), WORK/ofm13/ (03_ofm_water.js: water masks and waterway lines from OpenFreeMap
zoom 13 tiles, used only to keep drawings off the water and to find each mill's stream), data/extras.json (02b_extras.py).
Outputs (all CC BY-NC-SA 4.0, derived from the Hull Domesday Project's data):
  data/dw/{x}_{y}.json   drawings on a zoom 9 grid for the map's worker: points [lon*1e5, lat*1e5, sprite, rank, vill] flat,
                         and woods as rings
  data/vills.json        one row per drawn vill (for the far-zoom glyphs, names, search and popups)
  WORK/layout_stats.json counts for results.json
Every random choice is seeded by the vill's id, so the layout is the same on every run.
"""
import json, math, os, pickle, random, sys, time
from collections import OrderedDict, defaultdict, Counter
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import box, Polygon, MultiPolygon
from shapely.ops import unary_union
from common import WORK, DATA

T0 = time.time()
P = pickle.load(open(os.path.join(WORK, 'places.pkl'), 'rb'))
rows = [r for r in P['rows'] if r['lat'] is not None and r['lat'] == r['lat']]
EXTRA = P['extra']
X = json.load(open(os.path.join(DATA, 'extras.json'))) if os.path.exists(os.path.join(DATA, 'extras.json')) else {}
OFM = os.path.join(WORK, 'ofm13')
Z13 = 8192

def f0(v):
    try: return float(v) if v not in ('', None) and v == v else 0.0
    except (TypeError, ValueError): return 0.0
def mx(lon): return (lon + 180) / 360
def my(lat): return (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2
def lon_of(nx): return nx * 360 - 180
def lat_of(ny): return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ny))))
def mpn(lat): return 40075016.0 * math.cos(math.radians(lat))   # metres per unit of nx (and of ny) at this latitude

# ---------------------------------------------------------------- water (OpenFreeMap zoom 13: 256 x 256 mask per tile)
class Water:
    def __init__(self): self.c = OrderedDict(); self.miss = 0
    def tile(self, tx, ty):
        k = (tx, ty)
        if k in self.c: self.c.move_to_end(k); return self.c[k]
        f = os.path.join(OFM, '%d_%d.json' % k)
        if not os.path.exists(f): v = None; self.miss += 1
        else:
            j = json.load(open(f)); m = np.zeros((256, 256), np.uint8); r = j['r']
            for i in range(0, len(r), 3): m[r[i], r[i + 1]:r[i + 2]] = 1
            lines = []
            for cls, tun, pts in j['w']:
                if tun or cls not in ('river', 'stream'): continue
                a = np.array(pts, float)
                lines.append((cls, (tx + a[:, 0] / 4096) / Z13, (ty + a[:, 1] / 4096) / Z13))
            roads = []
            for cls, pts in j.get('t', []):
                a = np.array(pts, float)
                roads.append((cls, (tx + a[:, 0] / 4096) / Z13, (ty + a[:, 1] / 4096) / Z13))
            v = (m, lines, roads)
        self.c[k] = v
        if len(self.c) > 1800: self.c.popitem(last=False)
        return v
    def wet(self, nx, ny):
        tx, ty = int(nx * Z13), int(ny * Z13); t = self.tile(tx, ty)
        if t is None: return True                     # outside the tiles fetched: never draw there
        i = min(255, int((nx * Z13 - tx) * 256)); j = min(255, int((ny * Z13 - ty) * 256))
        return t[0][j, i] == 1
    def wet_near(self, nx, ny, rpx=1):
        tx, ty = int(nx * Z13), int(ny * Z13); t = self.tile(tx, ty)
        if t is None: return True
        i = int((nx * Z13 - tx) * 256); j = int((ny * Z13 - ty) * 256)
        return t[0][max(0, j - rpx):j + rpx + 1, max(0, i - rpx):i + rpx + 1].any()
    def roads(self, nx, ny, k=1):
        tx, ty = int(nx * Z13), int(ny * Z13); out = []
        for dx in range(-k, k + 1):
            for dy in range(-k, k + 1):
                t = self.tile(tx + dx, ty + dy)
                if t: out.extend(t[2])
        return out
    def streams(self, nx, ny):
        tx, ty = int(nx * Z13), int(ny * Z13); out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                t = self.tile(tx + dx, ty + dy)
                if t: out.extend(t[1])
        return out
W = Water()

def stream_points(lines, step_n):
    """Resample stream lines to points every step (in nx units); returns arrays (x, y, cls_is_river, heading)."""
    xs, ys, rv, hd = [], [], [], []
    for cls, lx, ly in lines:
        for k in range(len(lx) - 1):
            ax, ay, bx, by = lx[k], ly[k], lx[k + 1], ly[k + 1]
            L = math.hypot(bx - ax, by - ay)
            if L == 0: continue
            n = max(1, int(L / step_n))
            for s in range(n):
                t = (s + 0.5) / n; xs.append(ax + (bx - ax) * t); ys.append(ay + (by - ay) * t); rv.append(cls == 'river'); hd.append(math.atan2(by - ay, bx - ax))
    return np.array(xs), np.array(ys), np.array(rv, bool), np.array(hd)

def coast_point(nx, ny, mrad):
    """The nearest wet pixel (sea, mere or wide river) within mrad metres, stepping out in rings; None if none."""
    lat = lat_of(ny); u = mrad / mpn(lat)
    best = None
    for rr in np.linspace(u * 0.08, u, 14):
        for a in np.linspace(0, 2 * math.pi, 24, endpoint=False):
            x, y = nx + math.cos(a) * rr, ny + math.sin(a) * rr
            if W.wet(x, y):
                # step back to the dry edge
                for t in np.linspace(1, 0, 12):
                    x2, y2 = nx + math.cos(a) * rr * t, ny + math.sin(a) * rr * t
                    if not W.wet(x2, y2): return (x2, y2, a)
                return None
    return best

# ---------------------------------------------------------------- the vills to draw
def rhu(v): return int(math.floor(v + 0.5))
V = []
for r in rows:
    dw = f0(r['town_dwellings']) if r['town_dwellings'] not in ('', None) else f0(r['d_households'])
    V.append(r | {'nx': mx(r['lng']), 'ny': my(r['lat']), 'dwell': rhu(dw), 'wasted_dw': rhu(f0(r['town_waste']))})
# ---- estimates where Domesday gives no usable household figure (drawn in a paler, dotted style and counted apart):
# a place with entries but no households counted, not called waste and not a named member of another entry, gets the median
# households of the places with households in its hundred (five or more), else in its county. London and Winchester, left
# out of the survey, get the LOW end of historians' estimates of their people about 1100 divided by 4.5 people a household
# (Darby used 4 to 5): London about 10,000 to 20,000 (Brooke and Keir 1975; Keene 2000), Winchester about 5,000 to 8,000
# (Biddle 1976, from the Winton Domesday of about 1110). Conservative by design.
PPH = 4.5
UNSURV_PEOPLE = {'London': 10000, 'Winchester': 5000}
hund_hh, cty_hh = defaultdict(list), defaultdict(list)
for v in V:
    h = f0(v['households'])
    if h > 0: hund_hh[(v['county'], v['hundred'])].append(h); cty_hh[v['county']].append(h)
# households per unit of each measure, county by county (all England where a county has fewer than 10 vills with both)
MEAS = [('ploughTeams', 'plough teams'), ('ploughlands', 'ploughlands'), ('value1086', 'value in 1086'), ('value1066', 'value in 1066'), ('geldUnits', 'hides or carucates')]
RAT = {}
for m, _ in MEAS:
    byc, allr = defaultdict(list), []
    for v in V:
        h, q = f0(v['households']), f0(v[m])
        if h > 0 and q > 0: byc[v['county']].append(h / q); allr.append(h / q)
    RAT[m] = ({c: float(np.median(l)) for c, l in byc.items() if len(l) >= 10}, float(np.median(allr)))
def ratio_est(v, order):
    for m, label in MEAS:
        if m not in order or f0(v[m]) <= 0: continue
        r = RAT[m][0].get(v['county'], RAT[m][1])
        return r * f0(v[m]), '%s (%s) x the county median of %.2f households per unit' % (label, format(f0(v[m]), 'g'), r)
    return None, ''
EST = Counter()
for v in V:
    v['est'] = 0; v['est_basis'] = ''; v['est_kind'] = ''
    if v['unsurveyed']:
        ppl = UNSURV_PEOPLE.get(v['name'], 0)
        v['est'] = rhu(ppl / PPH); v['est_kind'] = 'e'
        v['est_basis'] = 'the low end of historians\' estimates of its people about 1100 (%s) at %.1f people a household' % (format(ppl, ','), PPH)
        EST['unsurveyed'] += 1; EST['unsurveyed_dw'] += v['est']; continue
    if v['dwell'] > 0 or v['memberOf'] or f0(v['d_households']) > 0 or f0(v['entries']) <= 0: continue
    waste = f0(v['waste_entries']) > 0
    hl = hund_hh.get((v['county'], v['hundred']), []); cl = cty_hh.get(v['county'], [])
    cap = float(np.median(hl)) if len(hl) >= 5 else float(np.median(cl)) if cl else 10.0
    e, basis = ratio_est(v, ['value1066', 'ploughlands', 'geldUnits'] if waste else ['ploughTeams', 'ploughlands', 'value1086', 'value1066', 'geldUnits'])
    if e is None:
        pool = hl if len(hl) >= 5 else cl
        if not pool: continue
        e, basis = float(np.percentile(pool, 25)), 'the lower quartile of the households of %d vills in %s' % (len(pool), ('%s hundred' % v['hundred']) if len(hl) >= 5 else v['countyName'])
        EST['by_quartile'] += 1
    else: EST['by_ratio'] += 1
    if e > cap: basis += ', capped at the median vill of its hundred (%s)' % format(cap, 'g'); EST['capped'] += 1
    v['est'] = max(1, rhu(min(e, cap))); v['est_kind'] = 'x' if waste else 'e'
    v['est_basis'] = ('dwellings left empty, from ' if waste else '') + basis
    EST['waste_vills' if waste else 'blank_vills'] += 1; EST['waste_dw' if waste else 'blank_dw'] += v['est']
print('estimates', dict(EST), file=sys.stderr)
pts_all = np.array([[v['nx'], v['ny']] for v in V])
# ---- town walls from real geometry: OpenStreetMap's city walls (via the Inked World's walls file) within 1.5 km of a borough
INKW = os.path.join(os.path.dirname(DATA), '..', 'ink-map', 'data', 'walls.geojson')
WALLGEO = []
if os.path.exists(INKW):
    for f in json.load(open(INKW))['features']:
        if f['properties'].get('k') != 'wall': continue
        g = f['geometry']; parts = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        for part in parts:
            if all(-6.5 < c[0] < 2 and 49.8 < c[1] < 55.9 for c in part): WALLGEO.append(part)
# Winchester's circuit is not in that file: traced by hand along the line of its Roman and medieval walls (North Walls,
# the West Gate, Southgate and the Itchen on the east), approximate
WALLGEO.append([[-1.3196, 51.0632], [-1.3192, 51.0652], [-1.3150, 51.0658], [-1.3100, 51.0662], [-1.3068, 51.0660], [-1.3062, 51.0630],
                [-1.3066, 51.0600], [-1.3100, 51.0592], [-1.3150, 51.0594], [-1.3186, 51.0600], [-1.3196, 51.0632]])
# only boroughs walled by 1086 (Roman walls reused, or the burh's own circuit): later medieval circuits (Norwich, Southampton,
# Yarmouth ...) are not drawn
WALLED_1086 = {('London', 'MDX'), ('York', 'YKS'), ('Lincoln', 'LIN'), ('Chester', 'CHS'), ('Colchester', 'ESS'), ('Canterbury', 'KEN'),
               ('Winchester', 'HAM'), ('Exeter', 'DEV'), ('Chichester', 'SUS'), ('Rochester', 'KEN'), ('Oxford', 'OXF'), ('Wareham', 'DOR')}
from shapely.geometry import LineString as _LS, MultiPoint as _MP, Point as _Pt
WTREE = cKDTree(np.array([[mx(p[0][0]), my(p[0][1])] for p in WALLGEO])) if WALLGEO else None
KD = cKDTree(pts_all)

# sprites: codes are indices into SPR (js/ink-1086.js draws them; the worker maps the code back to the id)
SPR = ['dh-l0', 'dh-l1', 'dh-l2', 'dh-l3', 'dh-c0', 'dh-c1', 'dh-c2', 'dh-c3', 'dh-b0', 'dh-b1', 'dh-b2', 'dh-b3', 'dh-b4', 'dh-b5',
       'dh-w0', 'dh-w1', 'dh-w2', 'dh-hall', 'dch-wood', 'dch-stone', 'dch-minster', 'dch-cathedral', 'dmarket', 'dstall',
       'dmill-l', 'dmill-r', 'dcastle-m', 'dcastle-k', 'dsalt', 'dsalt-w', 'dfish', 'dvine', 'dpark', 'dhaia', 'dabbey', 'dwaste',
       'da-plough', 'da-sheep', 'da-pig', 'da-pigwood', 'da-cattle', 'da-goat', 'da-cob', 'da-mare', 'da-hives', 'da-oxen', 'dgate', 'dh-e0', 'dh-e1', 'dh-e2']
SC = {s: i for i, s in enumerate(SPR)}
GOLD = math.pi * (3 - math.sqrt(5))

cells = defaultdict(lambda: {'p': [], 'w': [], 'f': [], 'm': [], 'l': [], 'g': []})
def cell_of(nx, ny): return (int(nx * 512), int(ny * 512))
def enc(pts):
    """[[lon, lat], ...] in degrees -> flat delta-coded integers of 1e-5 degrees (js/page-1086.js decodes)"""
    out, px, py = [], 0, 0
    for lo, la in pts:
        x, y = round(lo * 1e5), round(la * 1e5); out += [x - px, y - py]; px, py = x, y
    return out
def ringenc(geom, tol):
    g = geom.simplify(tol)
    return enc([(lon_of(x), lat_of(y)) for x, y in g.exterior.coords]) if not g.is_empty and g.geom_type == 'Polygon' else None
def emit(nx, ny, spr, rank, vi):
    if spr not in SC: SPR.append(spr); SC[spr] = len(SPR) - 1
    c = cells[cell_of(nx, ny)]
    c['p'].extend([round(lon_of(nx) * 1e5), round(lat_of(ny) * 1e5), SC[spr], int(rank * 10), vi])

ST = Counter()
CASTLES = {str(c['placeId']): c for c in X.get('castles', [])}
ABBEYS = defaultdict(list)
for a in X.get('abbeys', []): ABBEYS[str(a['placeId'])].append(a)
MARKETS = {str(m['placeId']) for m in X.get('markets', [])}
CATHEDRAL = {'Canterbury', 'Rochester', 'Lincoln', 'Durham', 'Winchester', 'Worcester', 'Hereford', 'Exeter', 'Wells', 'Lichfield',
             'Chichester', 'Old Sarum', 'Salisbury', 'Thetford', 'Chester', 'London', 'York', 'Norwich', 'Dorchester', 'Sherborne', 'Elmham',
             'Selsey', 'Coventry', 'Bath'}
CATHEDRAL_1086 = {('Canterbury', 'KEN'), ('Rochester', 'KEN'), ('Lincoln', 'LIN'), ('Worcester', 'WOR'), ('Hereford', 'HEF'), ('Exeter', 'DEV'),
                  ('Wells', 'SOM'), ('Lichfield', 'STS'), ('Chichester', 'SUS'), ('York', 'YKS'), ('Thetford', 'NFK'), ('Chester', 'CHS'),
                  ('Salisbury', 'WIL'), ('Winchester', 'HAM'), ('London', 'MDX')}
vrows = []
WALLS = []
order = sorted(range(len(V)), key=lambda i: (int(V[i]['ny'] * 1024), int(V[i]['nx'] * 1024)))
for n_done, vi in enumerate(order):
    v = V[vi]
    rnd = random.Random(int(v['placeId']) * 7919 + 17)
    nx0, ny0, lat = v['nx'], v['ny'], v['lat']
    M = mpn(lat); m2n = 1.0 / M                      # metres to nx units
    dwell, wd = v['dwell'], v['wasted_dw']
    burg = f0(v['burgesses']) > 0 or v['town_dwellings'] not in ('', None)
    town = (burg and dwell >= 40) or v['unsurveyed']
    S = (55 if town else 80 if dwell >= 6 else 105) * m2n
    # class shares for the house drawings (Domesday's own households where it gives them)
    cls = {'l': f0(v['villagers']) + f0(v['freemen']) + f0(v['freeMen']) + f0(v['riders']), 'c': f0(v['smallholders']) + f0(v['cottagers']) + f0(v['slaves']) + f0(v['priests']) + f0(v['ploughmen']),
           'b': f0(v['burgesses'])}
    tot = sum(cls.values())
    nh = dwell
    if v['unsurveyed']: nh = 0
    kinds = []
    if v['town_dwellings'] not in ('', None) and town: kinds = ['b'] * nh
    elif tot > 0:
        for k, s in cls.items(): kinds += [k] * rhu(nh * s / tot)
        kinds = (kinds + ['c'] * nh)[:nh]
    else: kinds = ['c'] * nh
    rnd.shuffle(kinds)
    # ---- the centre: market, church (or minster), the lord's hall
    church = f0(v['church_entries']) > 0
    minster = f0(v['d_minster_t']) > 0 and (dwell >= 60 or town)
    key = (v['name'], v['county'])
    cath = key in CATHEDRAL_1086
    has_market = f0(v['market_entries']) > 0 or v['placeId'] in MARKETS
    nest = v['est']
    ntot = nh + wd + nest
    if v['unsurveyed']: S = 40 * m2n
    # ---- the walls: real wall lines (OpenStreetMap city walls) near a borough; their hull is the walled core
    core = None
    if town and WTREE is not None and (v['name'], v['county']) in WALLED_1086:
        idxw = WTREE.query_ball_point([nx0, ny0], 1500 * m2n)
        segs = [WALLGEO[i] for i in idxw]
        if segs:
            ptsw = [(mx(c[0]), my(c[1])) for part in segs for c in part]
            hull = _MP(ptsw).convex_hull
            area_m2 = hull.area * M * M
            if 0.04e6 < area_m2 < 4e6 and hull.contains(_Pt(nx0, ny0)) or (0.04e6 < area_m2 < 4e6 and hull.distance(_Pt(nx0, ny0)) * M < 500):
                core = hull
                for part in segs:
                    WALLS.append({'type': 'Feature', 'properties': {'i': vi, 'n': v['name']}, 'geometry': {'type': 'LineString', 'coordinates': [[round(c[0], 5), round(c[1], 5)] for c in part]}})
                ST['walled_towns'] += 1
                if core.distance(_Pt(nx0, ny0)) > 0: nx0, ny0 = core.centroid.x, core.centroid.y
                if town and ntot > 200: S = max(26, min(55, math.sqrt(core.area * M * M * 0.8 / max(1, ntot)))) * m2n
    # the centre's buildings
    centre = []
    if has_market and ntot: centre.append(('dmarket', 0, 0))
    if cath: centre.append(('dch-cathedral', 0.9, 0.35))
    elif church or minster: centre.append(('dch-minster' if minster else ('dch-stone' if town or dwell >= 40 else 'dch-wood'), 0.75, 0.3))
    if ntot >= 3 and not town and (f0(v['lordsTeams']) > 0 or f0(v['value1086']) >= 480): centre.append(('dh-hall', -0.85, -0.25))
    cpos = []
    for spr, dx, dy in centre:
        x, y = nx0 + dx * S * 1.6, ny0 + dy * S * 1.6
        if W.wet(x, y): x, y = nx0, ny0
        emit(x, y, spr, 9.5 if spr.startswith('dch-cath') else 10.6 if spr.startswith('dch') or spr == 'dmarket' else 11.2, vi)
        ST[spr] += 1; cpos.append((x, y))
    if has_market and ntot:
        for k in range(2 if ntot < 60 else 4):
            a = rnd.random() * 6.283; x, y = nx0 + math.cos(a) * S * 0.9, ny0 + math.sin(a) * S * 0.6 + S * 0.5
            if not W.wet(x, y): emit(x, y, 'dstall', 12, vi)
    # ---- dwellings along streets and lanes. Plots are laid every S along both sides of the streets near the centre
    # (OpenStreetMap's streets and lanes as a proxy for the old ones; inside the walls first where there are walls), nearest
    # the centre first, so the core is dense and the edges thin. Where there are too few, the vill gets a lane (or a green)
    # of its own through the centre.
    allk = kinds + [v['est_kind'] or 'e'] * nest + ['w'] * wd
    rnd.shuffle(allk)
    hcount = Counter(); house_xy = []
    plots = []
    rmax = (1600 if town else 650) * m2n
    used_roads = []
    if allk:
        road_list = list(W.roads(nx0, ny0, 1 if not town else 2))
        if core is not None:
            # inside the walls today's map has few through streets (the old lanes are footways the tiles leave out), so
            # the core gets streets of its own: a cross of main streets from the gates through the centre and back lanes
            # parallel to the longer one, 2.4 plots apart, so each row of houses has its garden behind
            mrr = core.minimum_rotated_rectangle; cs = list(mrr.exterior.coords)
            e1 = (cs[1][0] - cs[0][0], cs[1][1] - cs[0][1]); e2 = (cs[2][0] - cs[1][0], cs[2][1] - cs[1][1])
            if math.hypot(*e2) > math.hypot(*e1): e1, e2 = e2, e1
            L1 = math.hypot(*e1); L2 = math.hypot(*e2); u1 = (e1[0] / L1, e1[1] / L1); u2 = (e2[0] / L2, e2[1] / L2)
            cc = core.centroid; synth = []
            for k in np.arange(-L2 / 2, L2 / 2, S * 2.4):
                a = (cc.x + u2[0] * k - u1[0] * L1, cc.y + u2[1] * k - u1[1] * L1); b = (cc.x + u2[0] * k + u1[0] * L1, cc.y + u2[1] * k + u1[1] * L1)
                synth.append((2 if abs(k) > S else 1, _LS([a, b])))
            synth.append((1, _LS([(cc.x - u2[0] * L2, cc.y - u2[1] * L2), (cc.x + u2[0] * L2, cc.y + u2[1] * L2)])))
            inner = core.buffer(-S * 0.9)
            for c_, ln_ in synth:
                g_ = ln_.intersection(inner)
                for part in (g_.geoms if hasattr(g_, 'geoms') else [g_]):
                    if part.is_empty or part.geom_type != 'LineString' or part.length < S * 2: continue
                    a_ = np.array(part.coords); road_list.append((c_, a_[:, 0], a_[:, 1]))
        wall_line = core.exterior if core is not None else None
        for cls_, lx, ly in road_list:
            if (np.hypot(lx - nx0, ly - ny0) > rmax).all(): continue
            seg_used = False
            for q in range(len(lx) - 1):
                ax, ay, bx, by = lx[q], ly[q], lx[q + 1], ly[q + 1]
                L = math.hypot(bx - ax, by - ay)
                if L == 0: continue
                ux, uy = (bx - ax) / L, (by - ay) / L
                for t in np.arange(S * 0.5, L, S):
                    cxp, cyp = ax + ux * t, ay + uy * t
                    dc = math.hypot(cxp - nx0, cyp - ny0)
                    if dc > rmax: continue
                    for side in (1, -1):
                        off = S * (0.48 + 0.12 * rnd.random())
                        px_, py_ = cxp - uy * off * side, cyp + ux * off * side
                        if wall_line is not None and wall_line.distance(_Pt(px_, py_)) < S * 0.8: continue   # not on the wall
                        w_ = dc * (0.35 if core is not None and core.contains(_Pt(px_, py_)) else 1.0) * (1 + 0.15 * cls_ / 3)
                        plots.append((w_ + rnd.random() * S * 0.4, px_, py_))
                    seg_used = True
            if seg_used: used_roads.append((lx, ly))
        plots.sort()
        taken = set()
        def okey2(x, y): return (int(x / (S * 0.8)), int(y / (S * 0.8)))
        for (cx_, cy_) in cpos:
            for ddx in (-1, 0, 1):
                for ddy in (-1, 0, 1): taken.add((okey2(cx_, cy_)[0] + ddx, okey2(cx_, cy_)[1] + ddy))
        sel = []
        for w_, x, y in plots:
            if len(sel) >= len(allk): break
            k_ = okey2(x, y)
            if k_ in taken or W.wet(x, y): continue
            if not town and KD.query([x, y])[1] != vi: continue
            taken.add(k_); sel.append((x, y))
        plan = 'streets'
        if len(sel) < len(allk) * 0.85 or (not town and len(sel) < len(allk)):
            # a lane of its own (or a green): houses both sides of a lane through the centre, a cross lane for larger vills
            sel = []; taken = set(okey2(cx_, cy_) for cx_, cy_ in cpos)
            n = len(allk)
            if 8 <= n <= 40 and rnd.random() < 0.45 and not town:
                plan = 'green'
                rg = max(2.2 * S, n * S / (2 * math.pi) * 0.9)
                th0 = rnd.random() * 6.283; el_ = 0.6 + rnd.random() * 0.3
                ring = []
                for i in range(n * 2):
                    a = th0 + i * 2 * math.pi / n
                    x, y = nx0 + math.cos(a) * rg, ny0 + math.sin(a) * rg * el_
                    if len(sel) < n and not W.wet(x, y): sel.append((x, y))
                gpts = [(nx0 + math.cos(a) * rg * 0.72, ny0 + math.sin(a) * rg * el_ * 0.72) for a in np.linspace(0, 6.283, 24)]
                cells[cell_of(nx0, ny0)]['g'].append([vi, enc([(lon_of(x), lat_of(y)) for x, y in gpts])])
            else:
                plan = 'lane'
                th = rnd.random() * math.pi
                lanes = [th] + ([th + math.pi / 2 + (rnd.random() - 0.5) * 0.5] if n > 40 else []) + ([th + math.pi / 4] if n > 160 else [])
                i = 0
                while len(sel) < n and i < n * 4:
                    ln = lanes[i % len(lanes)]; j_ = i // len(lanes)
                    d_ = S * (0.9 + j_ // 4) * (1 if (j_ // 2) % 2 == 0 else -1)
                    side = 1 if j_ % 2 == 0 else -1
                    off = S * 0.5 * side
                    x = nx0 + math.cos(ln) * d_ - math.sin(ln) * off + (rnd.random() - 0.5) * S * 0.2
                    y = ny0 + math.sin(ln) * d_ + math.cos(ln) * off + (rnd.random() - 0.5) * S * 0.2
                    i += 1
                    if W.wet(x, y): continue
                    sel.append((x, y))
                if sel:
                    for ln in lanes:
                        ext = max(math.hypot(x - nx0, y - ny0) for x, y in sel) + S
                        cells[cell_of(nx0, ny0)]['l'].append([vi, enc([(lon_of(nx0 - math.cos(ln) * ext), lat_of(ny0 - math.sin(ln) * ext)), (lon_of(nx0 + math.cos(ln) * ext), lat_of(ny0 + math.sin(ln) * ext))])])
        else:
            # the streets the houses line, drawn as lanes: only the stretches with houses along them (within 1.3 plots),
            # so today's wider street grid never shows
            if sel:
                ht = cKDTree(np.array(sel))
                for lx, ly in used_roads:
                    pts_ = []
                    for q in range(len(lx) - 1):
                        L = math.hypot(lx[q + 1] - lx[q], ly[q + 1] - ly[q]); k_ = max(1, int(L / (S * 0.5)))
                        for t in range(k_): pts_.append((lx[q] + (lx[q + 1] - lx[q]) * t / k_, ly[q] + (ly[q + 1] - ly[q]) * t / k_))
                    pts_.append((lx[-1], ly[-1]))
                    dd_, _ = ht.query(np.array(pts_))
                    run = []
                    for pt_, d_ in zip(pts_ + [None], list(dd_) + [9e9]):
                        if pt_ is not None and d_ <= S * 1.3: run.append(pt_); continue
                        if len(run) >= 2:
                            ls_ = _LS(run).simplify(6 * m2n)
                            cells[cell_of(nx0, ny0)]['l'].append([vi, enc([(lon_of(a_), lat_of(b_)) for a_, b_ in ls_.coords])])
                        run = []
        ST['plan_' + plan] += 1
        for i, (x, y) in enumerate(sel):
            kd = allk[i]
            spr = {'l': 'dh-l%d' % rnd.randrange(4), 'c': 'dh-c%d' % rnd.randrange(4), 'b': 'dh-b%d' % rnd.randrange(6), 'w': 'dh-w%d' % rnd.randrange(3), 'e': 'dh-e%d' % rnd.randrange(3), 'x': 'dh-x%d' % rnd.randrange(3)}[kd]
            emit(x, y, spr, 11 if (i % 2 == 0) else 12, vi)
            house_xy.append((x, y)); hcount[kd] += 1
    placed = len(house_xy)
    drawn_houses = hcount['l'] + hcount['c'] + hcount['b']
    ST['houses'] += drawn_houses; ST['waste_houses'] += hcount['w']; ST['houses_est'] += hcount['e'] + hcount['x']; ST['houses_est_empty'] += hcount['x']; ST['houses_skipped'] += len(allk) - placed
    if hcount['e'] or hcount['x']: ST['vills_est'] += 1
    if house_xy:
        hd = np.hypot(np.array(house_xy)[:, 0] - nx0, np.array(house_xy)[:, 1] - ny0)
        rc = float(np.percentile(hd, 90)) + S
    else: rc = S * 1.5
    if core is not None: rc = max(rc, math.sqrt(core.area / math.pi))
    # ---- the vill's lands: its Voronoi cell within 2.6 km, on a 100 m grid: open fields nearest the village, meadow by the
    # stream, pasture and wood beyond
    RV = 2600 * m2n
    g1 = 100 * m2n; R1 = int(RV / g1) + 1
    ii, jj2 = np.meshgrid(np.arange(-R1, R1 + 1), np.arange(-R1, R1 + 1))
    gx, gy = nx0 + ii.ravel() * g1 + (rnd.random() - 0.5) * g1, ny0 + jj2.ravel() * g1 + (rnd.random() - 0.5) * g1
    gr = np.hypot(gx - nx0, gy - ny0)
    selg = (gr > rc + 20 * m2n) & (gr < RV)
    gx, gy, gr = gx[selg], gy[selg], gr[selg]
    own = KD.query(np.c_[gx, gy])[1] == vi if len(gx) else np.array([], bool)
    landc = [(x, y, r_) for x, y, r_, o in zip(gx, gy, gr, own) if o and not W.wet(x, y)]
    landc.sort(key=lambda q: q[2])
    teams = f0(v['d_ploughTeams'])
    arable_ha = (teams if teams > 0 else 0.5 * f0(v['ploughlands'])) * 48.0       # a plough team to about 120 acres (48 ha)
    nfield = min(int(len(landc) * 0.6), int(round(arable_ha)))                     # one 100 m cell is 1 ha
    fieldc = landc[:nfield]
    rest = landc[nfield:]
    field_xy = []
    if fieldc:
        th0 = rnd.random() * 6.283; nf = 2 if nfield < 60 else 3
        groups = defaultdict(list)
        for x, y, r_ in fieldc:
            a = (math.atan2(y - ny0, x - nx0) - th0) % (2 * math.pi)
            groups[int(a / (2 * math.pi / nf))].append((x, y))
        for gi, lst in groups.items():
            U = unary_union([box(x - g1 * 0.52, y - g1 * 0.52, x + g1 * 0.52, y + g1 * 0.52) for x, y in lst]).buffer(-g1 * 0.3).buffer(g1 * 0.3)
            for pg in (U.geoms if hasattr(U, 'geoms') else [U]):
                if pg.is_empty or pg.area < g1 * g1 * 2: continue
                r_ = ringenc(pg, g1 * 0.45)
                if r_: cells[cell_of(nx0, ny0)]['f'].append([vi, (gi + int(th0 * 3)) % 4, r_])
        field_xy = [(x, y) for x, y, _ in fieldc]
        ST['field_ha'] += nfield
    # meadow: Domesday's acres (taken as 0.4 ha each) on the cells nearest the stream
    mead_ha = f0(v['meadowAcres']) * 0.4
    if mead_ha > 0.5:
        sl = W.streams(nx0, ny0)
        if sl:
            xs_, ys_, _, _ = stream_points(sl, 40 * m2n)
            near = np.hypot(xs_ - nx0, ys_ - ny0) < 1500 * m2n
            if near.any():
                st_tree = cKDTree(np.c_[xs_[near], ys_[near]])
                g2 = 50 * m2n; cand = []
                for x, y in [(nx0 + i * g2, ny0 + j * g2) for i in range(-30, 31) for j in range(-30, 31)]:
                    dd, _ = st_tree.query([x, y])
                    if dd < 160 * m2n and math.hypot(x - nx0, y - ny0) > rc and not W.wet(x, y): cand.append((dd + math.hypot(x - nx0, y - ny0) * 0.15, x, y))
                cand.sort(); take_n = min(len(cand), int(mead_ha * 4))   # a 50 m cell is a quarter hectare
                if take_n >= 2:
                    U = unary_union([box(x - g2 * 0.55, y - g2 * 0.55, x + g2 * 0.55, y + g2 * 0.55) for _, x, y in cand[:take_n]])
                    for pg in (U.geoms if hasattr(U, 'geoms') else [U]):
                        r_ = ringenc(pg, g2 * 0.45) if not pg.is_empty else None
                        if r_: cells[cell_of(nx0, ny0)]['m'].append([vi, r_])
                    ST['meadow_ha'] += take_n / 4
    land = [(x, y, r_) for x, y, r_ in rest]
    used = set()
    def okey(x, y, g): return (int(x / g), int(y / g))
    G = 60 * m2n
    def place(pool, far=False):
        cand = [p for p in pool if okey(p[0], p[1], G) not in used]
        if not cand: return None
        p = max(cand, key=lambda q: q[2] + rnd.random() * 600 * m2n) if far else cand[rnd.randrange(len(cand))]
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1): used.add((int(p[0] / G) + ddx, int(p[1] / G) + ddy))
        return p
    fieldpool = [(x, y, 0) for x, y in field_xy]
    def scatter(spr, n, rmin, rmax, r0=11, far=False, pool=None):
        got = 0
        base = pool if pool is not None else [p for p in land if rmin * m2n + rc <= p[2] <= rmax * m2n + rc] or land
        for i in range(n):
            p = place(base, far)
            if p is None: break
            emit(p[0] + (rnd.random() - 0.5) * 40 * m2n, p[1] + (rnd.random() - 0.5) * 40 * m2n, spr, r0 if i == 0 else (12 if i < n / 2 else 13), vi); got += 1
        ST[spr] += got
        return got
    def n_of(c, N): return 0 if c <= 0 else max(1, rhu(c / N))
    ST['teams_rec'] += teams
    # plough teams only in the vill's own open fields (or, with none drawn, on its own land within 700 m of the houses)
    scatter('da-plough', n_of(teams, 1), 0, 9e9, pool=fieldpool if fieldpool else [p for p in land if p[2] <= rc + 700 * m2n])
    scatter('da-sheep', n_of(f0(v['d_sheep']), 20), 0, 2400, far=True)
    scatter('da-cattle', n_of(f0(v['d_cattle']) + f0(v['d_cows']), 5), 0, 700)
    scatter('da-goat', n_of(f0(v['d_goats']), 10), 80, 1800)
    scatter('da-cob', n_of(f0(v['d_cobs']) + f0(v['d_horses']), 3), 0, 900)
    scatter('da-mare', n_of(f0(v['d_wildmares']), 5), 400, 2400, far=True)
    scatter('da-pig', n_of(f0(v['d_pigs']), 10), 0, 350)
    scatter('da-hives', n_of(f0(v['d_beehives']), 5), 0, 200)
    scatter('da-oxen', n_of(f0(v['d_oxen']), 4), 0, 600)
    if f0(v['d_vine']) > 0: scatter('dvine', min(4, 1 + int(f0(v['vine_arpents']) / 4)), 0, 600, r0=10.6)
    # ---- woodland: a wood of about the area Domesday's measure suggests (see 02_places.py), on the far side of the lands
    wood_ha = max(f0(v['d_wood_ha']), f0(v['d_woodlandPigs']) * 1.0)
    woodpts = []
    if wood_ha > 0:
        g = 150.0
        need = wood_ha * 10000 / (g * g)
        cand = sorted([p for p in land if p[2] > rc + 250 * m2n], key=lambda q: -(q[2] + rnd.random() * 500 * m2n))
        # the lands sample is random; lay a regular grid over the cell for the wood itself
        gn = g * m2n; R = int(RV / gn) + 1
        ii, jj2 = np.meshgrid(np.arange(-R, R + 1), np.arange(-R, R + 1))
        gx, gy = nx0 + ii.ravel() * gn, ny0 + jj2.ravel() * gn
        rr = np.hypot(gx - nx0, gy - ny0)
        sel = (rr >= rc + 250 * m2n) & (rr <= RV)
        gx, gy, rr = gx[sel], gy[sel], rr[sel]
        grid = []
        if len(gx):
            _, own = KD.query(np.c_[gx, gy])
            for x, y, r_, o in zip(gx, gy, rr, own):
                if o != vi or W.wet(x, y): continue
                grid.append((x, y, r_ + rnd.random() * 700 * m2n))
        if field_xy and grid:
            ft_ = cKDTree(np.array(field_xy)); dd_, _ = ft_.query(np.array([(x, y) for x, y, _ in grid]))
            grid = [g_ for g_, d_ in zip(grid, dd_) if d_ > 70 * m2n]
        grid.sort(key=lambda q: -q[2])
        cap = int(len(grid) * 0.7)
        take_n = min(cap, max(1, int(round(need))))
        woodpts = grid[:take_n]
        if woodpts:
            sq = [box(x - gn * 0.55, y - gn * 0.55, x + gn * 0.55, y + gn * 0.55) for x, y, _ in woodpts]
            U = unary_union(sq).simplify(gn * 0.35)
            polys = list(U.geoms) if isinstance(U, MultiPolygon) else [U]
            for pg in polys:
                if pg.is_empty: continue
                ring = [[round(lon_of(x) * 1e5), round(lat_of(y) * 1e5)] for x, y in pg.exterior.coords]
                holes = [[[round(lon_of(x) * 1e5), round(lat_of(y) * 1e5)] for x, y in h.coords] for h in pg.interiors]
                c = pg.centroid
                cells[cell_of(c.x, c.y)]['w'].append([vi, ring] + ([holes] if holes else []))
            ST['wood_cells'] += len(woodpts); ST['wood_ha_drawn'] += len(woodpts) * g * g / 10000
            ST['wood_ha_rec'] += wood_ha
        # pigs feeding in the wood: one per 50 of the pannage Domesday gives
        np_ = n_of(f0(v['d_woodlandPigs']), 50)
        got = 0
        for i in range(min(np_, len(woodpts))):
            x, y, _ = woodpts[rnd.randrange(len(woodpts))]
            emit(x + (rnd.random() - 0.5) * gn * 0.6, y + (rnd.random() - 0.5) * gn * 0.6, 'da-pigwood', 11 if i == 0 else (12 if i < np_ / 2 else 13), vi); got += 1
        ST['da-pigwood'] += got
    if f0(v['d_park']) > 0:
        if woodpts: x, y, _ = woodpts[len(woodpts) // 2]; emit(x, y, 'dpark', 10.6, vi); ST['dpark'] += 1
        else: scatter('dpark', 1, 500, 2000, r0=10.6, far=True)
    if f0(v['d_haia']) > 0:
        if woodpts: x, y, _ = woodpts[-1]; emit(x, y, 'dhaia', 11, vi); ST['dhaia'] += 1
        else: scatter('dhaia', 1, 400, 2000, r0=11, far=True)
    # ---- mills: one per recorded mill (fractions rounded half up), each on the nearest stream or river within 1.5 km,
    # spaced 110 m apart along the water; none drawn where today's map has no stream that close
    nm = rhu(f0(v['d_mills']))
    ST['mills_rec'] += f0(v['d_mills'])
    mill_pos = []
    if nm:
        lines = W.streams(nx0, ny0)
        if lines:
            xs, ys, rv, hd = stream_points(lines, 20 * m2n)
            if len(xs):
                d = np.hypot(xs - nx0, ys - ny0)
                ok = d < 1500 * m2n
                idx = np.where(ok)[0]
                idx = idx[np.argsort(d[idx])]
                for i in idx:
                    if len(mill_pos) >= nm: break
                    if any(math.hypot(xs[i] - a, ys[i] - b) < 110 * m2n for a, b in mill_pos): continue
                    mill_pos.append((xs[i], ys[i]))
                    side = 'dmill-l' if xs[i] > nx0 else 'dmill-r'      # the mill house on the village side of its wheel
                    emit(xs[i], ys[i], side, 10.6 if len(mill_pos) == 1 else 11.2, vi)
        ST['mills_drawn'] += len(mill_pos); ST['mills_rounded'] += nm
        if len(mill_pos) < nm: ST['mills_no_stream'] += nm - len(mill_pos); ST['vills_mill_no_stream'] += 1
    # ---- fisheries: an eel weir on the nearest stream, or at the edge of the nearest sea, mere or river within 3 km
    nf = rhu(max(f0(v['d_fisheries']), f0(v['d_fish_t']))) or (1 if f0(v['d_eels']) > 0 else 0)
    if nf:
        got = 0
        lines = W.streams(nx0, ny0)
        if lines:
            xs, ys, rv, hd = stream_points(lines, 25 * m2n)
            if len(xs):
                d = np.hypot(xs - nx0, ys - ny0); idx = np.argsort(d)
                for i in idx:
                    if got >= min(nf, 4) or d[i] > 2000 * m2n: break
                    if any(math.hypot(xs[i] - a, ys[i] - b) < 140 * m2n for a, b in mill_pos): continue
                    emit(xs[i], ys[i], 'dfish', 10.6 if got == 0 else 11.5, vi); got += 1; mill_pos.append((xs[i], ys[i]))
        if not got:
            cp = coast_point(nx0, ny0, 3000)
            if cp: emit(cp[0], cp[1], 'dfish', 10.6, vi); got = 1
        ST['dfish'] += got; ST['fish_vills'] += 1; ST['fish_vills_drawn'] += 1 if got else 0
    # ---- salt: boiling hearths. At the inland wiches beside the brine; elsewhere at the edge of the nearest sea or marsh
    ns = max(f0(v['d_saltHouses']), f0(v['d_salt_t']))
    if ns > 0:
        wich = v['name'] in ('Droitwich', 'Nantwich', 'Middlewich', 'Northwich')
        n = min(40, max(1, rhu(ns / 3)))
        got = 0
        if wich:
            for i in range(n):
                a = rnd.random() * 6.283; rr = rc * (0.9 + rnd.random() * 0.8)
                x, y = nx0 + math.cos(a) * rr, ny0 + math.sin(a) * rr
                if not W.wet(x, y): emit(x, y, 'dsalt-w', 10.6 if i == 0 else 11.5, vi); got += 1
        else:
            cp = coast_point(nx0, ny0, 6000)
            if cp:
                x0, y0, a = cp
                for i in range(min(n, 8)):
                    t = (i - min(n, 8) / 2) * 90 * m2n
                    x, y = x0 + math.cos(a + 1.57) * t - math.cos(a) * 40 * m2n, y0 + math.sin(a + 1.57) * t - math.sin(a) * 40 * m2n
                    if not W.wet(x, y): emit(x, y, 'dsalt', 10.6 if i == 0 else 11.5, vi); got += 1
            if not got:     # an inland holding with salt-houses elsewhere: one hearth at the edge of the village
                x, y = nx0 + rc * 0.8, ny0
                if not W.wet(x, y): emit(x, y, 'dsalt', 11, vi); got = 1
        ST['dsalt'] += got; ST['salt_vills'] += 1
    # ---- castles named in Domesday, and religious houses standing in 1086
    if v['placeId'] in CASTLES:
        c = CASTLES[v['placeId']]
        a = 2.2; x, y = nx0 + math.cos(a) * rc * 0.85, ny0 + math.sin(a) * rc * 0.85
        if W.wet(x, y): x, y = nx0 - rc * 0.5, ny0
        emit(x, y, 'dcastle-k' if c.get('stone') else 'dcastle-m', 9.5 if dwell >= 100 else 10, vi); ST['castles'] += 1
    for ab in ABBEYS.get(v['placeId'], []):
        a = 5.4; x, y = nx0 + math.cos(a) * rc * 0.9, ny0 + math.sin(a) * rc * 0.9
        if W.wet(x, y): x, y = nx0 + rc * 0.5, ny0
        emit(x, y, 'dabbey', 10, vi); ST['abbeys'] += 1
    # ---- waste: a burnt and roofless huddle where Domesday calls the vill waste and counts nobody living there
    if f0(v['waste_entries']) > 0:
        ST['waste_vills'] += 1
        if nh == 0:
            emit(nx0, ny0, 'dwaste', 10, vi); ST['dwaste'] += 1
    # ---- the row for the far zooms, names and popups
    vrows.append([vi, v['placeId'], v['name'], v['county'], round(v['lng'], 5), round(v['lat'], 5), dwell, rhu(f0(v['d_mills'])), len(mill_pos) if nm else 0,
                  1 if church else 0, 1 if town else 0, 1 if f0(v['waste_entries']) > 0 else 0, 1 if v['placeId'] in CASTLES else 0, 1 if has_market else 0,
                  1 if v['unsurveyed'] else 0, 1 if ABBEYS.get(v['placeId']) else 0, 1 if cath else 0,
                  v['modernPlaceName'] if v['modernPlaceName'] and v['modernPlaceName'].lower() != v['name'].lower() else '', v['est'], v['est_basis'], v['est_kind']])
    if n_done % 1000 == 0: print(n_done, round(time.time() - T0), 's', dict(ST.most_common(6)), file=sys.stderr)

# ---------------------------------------------------------------- sites outside any vill: castles of 1086 that Domesday does not
# name, and religious houses beyond the survey (placed by hand), each with an id from 100000 for its popup
sites = []
for c in X.get('castles_other', []):
    nx, ny = mx(c['lon']), my(c['lat'])
    if W.wet(nx, ny) and W.miss == 0: pass
    sid = 100000 + len(sites); sites.append({'i': sid, 'kind': 'castle', 'name': c['name'], 'lon': c['lon'], 'lat': c['lat'], 'year': c['year'], 'qid': c['qid'], 'stone': c['stone']})
    emit(nx, ny, 'dcastle-k' if c['stone'] else 'dcastle-m', 9.5, sid); ST['castles_other'] += 1
for a_ in X.get('abbeys', []):
    if a_.get('placeId'): continue
    nx, ny = mx(a_['lon']), my(a_['lat'])
    sid = 100000 + len(sites); sites.append({'i': sid, 'kind': 'abbey', 'name': a_['name'], 'lon': a_['lon'], 'lat': a_['lat'], 'founded': a_['founded'], 'order': a_['order']})
    emit(nx, ny, 'dabbey', 9.5, sid); ST['abbeys'] += 1

# ---------------------------------------------------------------- travellers on the old roads: peasants, ox carts, mounted knights,
# monks, packhorses and drovers (js/ink-life-art.js drawings), one every 7 km or so along the Roman roads in the surveyed land,
# kept off the water and out of the vills' cores. Decoration: Domesday records no traffic.
RD = os.path.join(DATA, 'roads1086.geojson')
TRAV = ['lr-walker', 'lr-oxcart', 'lr-knight', 'lr-friars', 'lr-packtrain', 'lr-sheepdrove', 'lr-cattledrove', 'lr-rider', 'lr-pedlar', 'lr-pilgrims', 'lr-messenger', 'lr-cart', 'lr-geese']
for t in TRAV:
    if t not in SC: SPR.append(t); SC[t] = len(SPR) - 1
if os.path.exists(RD):
    rr_ = random.Random(1086); nt_ = 0
    for f in json.load(open(RD))['features']:
        if f['properties'].get('kind') != 'roman': continue
        cs = f['geometry']['coordinates'] if f['geometry']['type'] == 'LineString' else [c for part in f['geometry']['coordinates'] for c in part]
        acc_ = rr_.random() * 7000
        for a_, b_ in zip(cs[:-1], cs[1:]):
            lat_ = (a_[1] + b_[1]) / 2; L_ = math.hypot((b_[0] - a_[0]) * 111320 * math.cos(math.radians(lat_)), (b_[1] - a_[1]) * 110540)
            acc_ += L_
            if acc_ < 7000: continue
            acc_ = rr_.random() * 1500
            x, y = mx(b_[0]), my(b_[1])
            d_, j_ = KD.query([x, y])
            if d_ * mpn(lat_) < 400 or d_ * mpn(lat_) > 6000 or W.wet(x, y): continue    # not in a vill, not beyond the surveyed land
            t = TRAV[rr_.randrange(len(TRAV))]
            if t in ('lr-cart',) and rr_.random() < 0.5: t = 'lr-oxcart'
            emit(x, y, t + ('-l' if rr_.random() < 0.5 else ''), 11.5, -1); nt_ += 1
    ST['travellers'] = nt_

# ---------------------------------------------------------------- write
od = os.path.join(DATA, 'dw'); odw = os.path.join(DATA, 'dww'); odl = os.path.join(DATA, 'land'); lidx = []
for d_ in (od, odw, odl):
    os.makedirs(d_, exist_ok=True)
    for f in os.listdir(d_): os.remove(os.path.join(d_, f))
idx = []
far = []
for (cx, cy), c in cells.items():
    if c['p']: json.dump({'p': c['p']}, open(os.path.join(od, '%d_%d.json' % (cx, cy)), 'w'), separators=(',', ':'))
    if c['w']: json.dump({'w': c['w']}, open(os.path.join(odw, '%d_%d.json' % (cx, cy)), 'w'), separators=(',', ':'))
    if c['f'] or c['m'] or c['l'] or c['g']:
        json.dump({'f': c['f'], 'm': c['m'], 'l': c['l'], 'g': c['g']}, open(os.path.join(odl, '%d_%d.json' % (cx, cy)), 'w'), separators=(',', ':')); lidx.append([cx, cy])
    idx.append([cx, cy, len(c['p']) // 5, len(c['w'])])
    for w in c['w']:
        far.append(Polygon([(q[0] / 1e5, q[1] / 1e5) for q in w[1]]).buffer(0))
json.dump({'type': 'FeatureCollection', 'features': WALLS}, open(os.path.join(DATA, 'townwalls.geojson'), 'w'), separators=(',', ':'))
ST['town_walls'] = len(WALLS)
json.dump({'z': 9, 'cells': lidx}, open(os.path.join(odl, 'index.json'), 'w'))
json.dump({'z': 9, 'cells': idx, 'sprites': SPR}, open(os.path.join(od, 'index.json'), 'w'), separators=(',', ':'))
# the woods far out: merged and simplified (about 300 m), for the forest wash at zoom 5 to 9
U = unary_union([g.buffer(0.0025) for g in far if not g.is_empty]).buffer(-0.0025).simplify(0.003)
geoms = list(U.geoms) if hasattr(U, 'geoms') else [U]
feats = [{'type': 'Feature', 'properties': {}, 'geometry': {'type': 'Polygon', 'coordinates': [[[round(x, 4), round(y, 4)] for x, y in g.exterior.coords]] + [[[round(x, 4), round(y, 4)] for x, y in h.coords] for h in g.interiors]}} for g in geoms if g.area > 2e-6]
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(DATA, 'woods_far.geojson'), 'w'), separators=(',', ':'))
ST['woods_far_polys'] = len(feats)
vrows.sort()
json.dump({'cols': ['i', 'id', 'name', 'county', 'lon', 'lat', 'dwell', 'mills', 'millsDrawn', 'church', 'town', 'waste', 'castle', 'market', 'unsurveyed', 'abbey', 'cathedral', 'modern', 'est', 'estBasis', 'estKind'],
           'rows': vrows, 'sites': sites}, open(os.path.join(DATA, 'vills.json'), 'w'), separators=(',', ':'))
ST.update({'est_' + k: v_ for k, v_ in EST.items()})
json.dump(dict(ST), open(os.path.join(WORK, 'layout_stats.json'), 'w'), indent=1)
# the estimates, one row per vill, for reuse and checking (data/estimates.csv)
import csv
with open(os.path.join(DATA, 'estimates.csv'), 'w', newline='') as fh:
    wr = csv.writer(fh); wr.writerow(['placeId', 'name', 'county', 'hundred', 'kind', 'dwellings_estimated', 'method'])
    for v in sorted(V, key=lambda q: (q['county'], q['name'])):
        if v['est']: wr.writerow([v['placeId'], v['name'], v['county'], v['hundred'], 'unsurveyed town' if v['unsurveyed'] else 'waste, nobody counted' if v['est_kind'] == 'x' else 'no usable figure', v['est'], v['est_basis']])
print('done', round(time.time() - T0), 's; water tiles missing', W.miss)
print(json.dumps(dict(ST), indent=0))
