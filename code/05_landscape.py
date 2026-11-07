"""Step 5. The landscape of 1086 around the vills, and the lettering of shires, hundreds and the lands beyond the survey.

Writes (data/):
  landscape.geojson   marsh (the Fens, Somerset Levels, Humberhead Levels, Romney and Pevensey marshes: ground below a set
                      height inside each basin, from Terrarium elevation at zoom 8, about 380 m a pixel; approximate), the
                      Wantsum Channel (hand-drawn, approximate), the royal forests Domesday names (the New Forest from its own
                      section of the Hampshire folios; Windsor, Melchet and Wimborne lettered where entries mention them),
                      the lands not surveyed (Britain more than 15 km from any located vill, joined to the north, Wales or Man)
  roads1086.geojson   Roman roads in Britain from Itiner-e (CC BY 4.0), and the four great highways' names along hand-set
                      approximate lines (Watling Street, Ermine Street, the Fosse Way, the Icknield Way)
  labels1086.geojson  shires (1086 names) and hundreds at the centre of their located vills; the kingdoms and lands beyond
  shires.geojson      approximate shire edges: the Voronoi cells of the located vills dissolved by county (lines)
"""
import gzip, json, math, os, pickle, re
from collections import defaultdict
import numpy as np
from PIL import Image
from scipy.spatial import Voronoi, cKDTree
from shapely.geometry import shape, Polygon, MultiPolygon, LineString, Point, mapping, box
from shapely.ops import unary_union, polygonize
from common import WORK, DATA, TERRARIUM, GEO, ROMAN

P = pickle.load(open(os.path.join(WORK, 'places.pkl'), 'rb'))['rows']
R = pickle.load(open(os.path.join(WORK, 'realm.pkl'), 'rb'))
loc = [r for r in P if r['lat'] is not None and r['lat'] == r['lat']]
feats = []
def F(geom, **props): feats.append({'type': 'Feature', 'properties': props, 'geometry': mapping(geom)})

# ---------------------------------------------------------------- land of Britain (Natural Earth 1:10m) for clipping
ne = json.load(open(os.path.join(GEO, 'ne_10m_admin_0_countries.geojson')))
gbr = [shape(f['geometry']) for f in ne['features'] if f['properties'].get('ADM0_A3') in ('GBR', 'IMN')]
GB = unary_union(gbr).intersection(box(-8.7, 49.8, 2.0, 61))
GBp = [g for g in (GB.geoms if hasattr(GB, 'geoms') else [GB]) if g.area > 0.002]
gb_main = unary_union(GBp)

# ---------------------------------------------------------------- marsh from elevation (Terrarium zoom 8)
Z = 8
def tile_xy(lat, lon, z=Z):
    n = 2 ** z; return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
def elev_grid(bb):
    lon0, lat0, lon1, lat1 = bb
    x0, y1 = tile_xy(lat0, lon0); x1, y0 = tile_xy(lat1, lon1)
    W, H = (x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256
    E = np.full((H, W), np.nan)
    for tx in range(x0, x1 + 1):
        for ty in range(y0, y1 + 1):
            f = os.path.join(TERRARIUM, str(Z), str(tx), '%d.png' % ty)
            if not os.path.exists(f): continue
            a = np.asarray(Image.open(f).convert('RGB')).astype(float)
            E[(ty - y0) * 256:(ty - y0 + 1) * 256, (tx - x0) * 256:(tx - x0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    return E, x0, y0
def px_ll(px, py, x0, y0):
    n = 2 ** Z; nx = (x0 + px / 256) / n; ny = (y0 + py / 256) / n
    return nx * 360 - 180, math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ny))))
MARSH = [  # name, bbox (lon0, lat0, lon1, lat1), height below which the ground is drawn as marsh (m)
    ('The Fens', (-0.55, 51.95, 0.65, 53.05), 3.5), ('Somerset Levels', (-3.15, 50.95, -2.55, 51.38), 7),
    ('Humberhead Levels', (-1.25, 53.42, -0.62, 53.78), 5), ('Romney Marsh', (0.65, 50.9, 1.05, 51.12), 4),
    ('Pevensey Levels', (0.24, 50.8, 0.44, 50.9), 4)]
for name, bb, h in MARSH:
    E, x0, y0 = elev_grid(bb)
    polys = []
    for py in range(E.shape[0]):
        for px in range(E.shape[1]):
            e = E[py, px]
            if not (e == e) or e > h or e <= 0.3: continue        # <= 0.3 m: the sea itself
            lo, la = px_ll(px, py, x0, y0)
            if not (bb[0] <= lo <= bb[2] and bb[1] <= la <= bb[3]): continue
            lo1, la1 = px_ll(px + 1, py + 1, x0, y0)
            polys.append(box(lo, la1, lo1, la))
    U = unary_union(polys).buffer(0.004).buffer(-0.006).simplify(0.002).intersection(gb_main)
    for g in (U.geoms if hasattr(U, 'geoms') else [U]):
        if g.area > 4e-5: F(g, kind='marsh', name=name)
    print(name, round(U.area * 111 * 70, 0), 'km2 approx')

# ---------------------------------------------------------------- the Wantsum Channel (hand-drawn, approximate)
wantsum = LineString([(1.205, 51.383), (1.228, 51.366), (1.245, 51.343), (1.262, 51.331), (1.300, 51.322), (1.335, 51.316), (1.365, 51.312)]).buffer(0.0075)
F(wantsum, kind='channel', name='Wantsum Channel')

# ---------------------------------------------------------------- royal forests Domesday names
byid = {r['placeId']: r for r in loc}
nf = set()
for d in R['entries']:
    if re.match(r'Hampshire NF', d['data']['ref']):
        for r in d.get('relations', []):
            if r['predicate'] == 'DESCRIBES' and r['to']['placeId'] in byid: nf.add(r['to']['placeId'])
pts = [Point(byid[p]['lng'], byid[p]['lat']) for p in nf]
nfh = unary_union([p.buffer(0.03) for p in pts]).convex_hull.buffer(0.01).intersection(gb_main)
F(nfh, kind='forest', name='The New Forest', n=len(pts))
fpl = defaultdict(list)
for d in R['entries']:
    t = d['data'].get('text') or ''
    for nm in ('Windsor Forest', 'Melchet Forest', 'Forest of Wimborne'):
        if nm in t:
            for r in d.get('relations', []):
                if r['predicate'] == 'DESCRIBES' and r['to']['placeId'] in byid: fpl[nm].append(byid[r['to']['placeId']])
for nm, lst in fpl.items():
    lo = sum(r['lng'] for r in lst) / len(lst); la = sum(r['lat'] for r in lst) / len(lst)
    F(Point(lo, la), kind='forestname', name=nm)
print('New Forest places', len(pts), 'other forests', {k: len(v) for k, v in fpl.items()})

# ---------------------------------------------------------------- not surveyed: Britain far from any located vill
vb = unary_union([Point(r['lng'], r['lat']).buffer(0.2) for r in loc])   # about 15 to 22 km
rest = gb_main.difference(vb)
SEEDS = [(-3.5, 56.5), (-3.0, 54.6), (-2.0, 55.25), (-1.7, 54.75), (-3.8, 52.6), (-4.0, 51.9), (-4.5, 54.25), (-6.5, 57.5), (-3.4, 53.0)]
keep = [g for g in (rest.geoms if hasattr(rest, 'geoms') else [rest]) if any(g.buffer(0.05).contains(Point(s)) for s in SEEDS) or g.area > 1.5]
uns = unary_union(keep).buffer(0.05).buffer(-0.05).simplify(0.01)
F(uns, kind='unsurveyed', name='Not surveyed in 1086')
print('unsurveyed area share of Great Britain', round(uns.area / gb_main.area, 3))

# ---------------------------------------------------------------- shires: approximate edges (Voronoi of vills, by county)
pts = np.array([[r['lng'], r['lat']] for r in loc]); cty = [r['county'] for r in loc]
vor = Voronoi(np.vstack([pts, [[-20, 40], [20, 40], [20, 70], [-20, 70]]]))
cells = defaultdict(list)
clipA = unary_union([gb_main.difference(uns.buffer(0.02))]).buffer(0)
for i, reg in enumerate(vor.point_region[:len(pts)]):
    v = vor.regions[reg]
    if -1 in v or not v: continue
    poly = Polygon(vor.vertices[v])
    if poly.is_valid: cells[cty[i]].append(poly)
shire_polys = {}
for c, lst in cells.items():
    shire_polys[c] = unary_union(lst).intersection(clipA).buffer(0)
lines = []
cs = list(shire_polys)
for i in range(len(cs)):
    for j in range(i + 1, len(cs)):
        b = shire_polys[cs[i]].boundary.intersection(shire_polys[cs[j]].buffer(0.002))
        if not b.is_empty and b.length > 0.02: lines.append({'type': 'Feature', 'properties': {'a': cs[i], 'b': cs[j]}, 'geometry': mapping(b.simplify(0.004))})
json.dump({'type': 'FeatureCollection', 'features': lines}, open(os.path.join(DATA, 'shires.geojson'), 'w'), separators=(',', ':'))
print('shire edge lines', len(lines))

# ---------------------------------------------------------------- lettering: shires, hundreds, the lands beyond
lab = []
CN = {r['county']: r['countyName'] for r in loc}
# Domesday's own shire names where they differ from today's (as the Phillimore edition titles them)
for c, g in shire_polys.items():
    if g.is_empty: continue
    pt = g.representative_point()
    lst = [r for r in loc if r['county'] == c]
    lab.append({'type': 'Feature', 'properties': {'kind': 'shire', 'name': CN[c], 'n': len(lst)}, 'geometry': mapping(pt)})
hund = defaultdict(list)
for r in loc:
    if r['hundred']: hund[(r['county'], r['hundred'])].append(r)
for (c, h), lst in hund.items():
    if len(lst) < 3: continue
    lo = float(np.median([r['lng'] for r in lst])); la = float(np.median([r['lat'] for r in lst]))
    lab.append({'type': 'Feature', 'properties': {'kind': 'hundred', 'name': h, 'county': CN[c], 'n': len(lst)}, 'geometry': {'type': 'Point', 'coordinates': [round(lo, 4), round(la, 4)]}})
BEYOND = [  # name, lon, lat, kind, note
    ('Kingdom of the Scots', -4.1, 56.6, 'kingdom', 'King Malcolm III'), ('Lothian', -2.75, 55.85, 'land', ''), ('Strathclyde', -4.4, 55.55, 'land', ''),
    ('Cumbria', -3.05, 54.62, 'land', 'not surveyed in 1086'), ('Northumbria beyond the Tees', -1.95, 55.05, 'land', 'not surveyed in 1086'),
    ('Gwynedd', -3.95, 52.95, 'kingdom', ''), ('Powys', -3.4, 52.55, 'kingdom', ''), ('Deheubarth', -4.25, 52.05, 'kingdom', ''),
    ('Morgannwg', -3.5, 51.62, 'kingdom', ''), ('Gwent', -2.95, 51.72, 'kingdom', ''), ('Isle of Man', -4.53, 54.24, 'land', 'Norse kingdom'),
    ('Ireland', -6.9, 53.6, 'kingdom', ''), ('Normandy', 0.2, 49.3, 'kingdom', ''), ('Flanders', 2.9, 51.05, 'kingdom', ''), ('Brittany', -3.2, 48.25, 'kingdom', ''),
    ('Thanet (an island in 1086)', 1.36, 51.355, 'land', ''), ('The Weald', 0.3, 51.03, 'land', ''), ('The Fens', 0.05, 52.5, 'land', ''),
]
for n, lo, la, k, note in BEYOND:
    lab.append({'type': 'Feature', 'properties': {'kind': k, 'name': n, 'note': note}, 'geometry': {'type': 'Point', 'coordinates': [lo, la]}})
for f in feats:
    if f['properties']['kind'] == 'forest':
        c = shape(f['geometry']).representative_point(); lab.append({'type': 'Feature', 'properties': {'kind': 'forest', 'name': f['properties']['name']}, 'geometry': mapping(c)})
    if f['properties']['kind'] == 'forestname':
        lab.append({'type': 'Feature', 'properties': {'kind': 'forest', 'name': f['properties']['name']}, 'geometry': f['geometry']})
    if f['properties']['kind'] == 'marsh' and f['properties']['name'] != 'The Fens':
        pass
json.dump({'type': 'FeatureCollection', 'features': lab}, open(os.path.join(DATA, 'labels1086.geojson'), 'w'), separators=(',', ':'))
print('labels', len(lab), 'hundreds', sum(1 for l in lab if l['properties']['kind'] == 'hundred'))

# ---------------------------------------------------------------- roads: Itiner-e in Britain, and the great highways' names
d = json.load(gzip.open(ROMAN))
rf = []
for f in d['features']:
    g = shape(f['geometry'])
    if not g.intersects(box(-8.5, 49.6, 2.2, 56.2)): continue
    p = f['properties']
    rf.append({'type': 'Feature', 'properties': {'kind': 'roman', 'main': 1 if p.get('type') == 'Main Road' else 0, 'name': p.get('name') or '', 'cert': p.get('certainty') or ''},
               'geometry': mapping(g.simplify(0.002))})
HW = {  # approximate courses (well-known towns along each), only to letter the names along the roads
    'Watling Street': [(1.31, 51.13), (1.08, 51.28), (0.51, 51.39), (-0.10, 51.51), (-0.34, 51.75), (-0.62, 51.95), (-0.98, 52.13), (-1.33, 52.52), (-1.70, 52.66), (-2.12, 52.69), (-2.65, 52.67)],
    'Ermine Street': [(-0.09, 51.52), (-0.03, 51.81), (-0.02, 52.05), (-0.18, 52.32), (-0.37, 52.57), (-0.48, 52.65), (-0.53, 52.93), (-0.54, 53.23), (-0.58, 53.62)],
    'Fosse Way': [(-3.53, 50.72), (-2.68, 51.00), (-2.36, 51.38), (-1.97, 51.72), (-1.62, 52.06), (-1.33, 52.52), (-1.13, 52.64), (-0.84, 52.98), (-0.54, 53.23)],
    'Icknield Way': [(0.72, 52.42), (0.42, 52.25), (0.02, 52.04), (-0.32, 51.92), (-0.52, 51.88), (-0.75, 51.76), (-1.05, 51.65), (-1.15, 51.53)],
}
for n, c in HW.items():
    rf.append({'type': 'Feature', 'properties': {'kind': 'highway', 'name': n}, 'geometry': {'type': 'LineString', 'coordinates': c}})
json.dump({'type': 'FeatureCollection', 'features': rf}, open(os.path.join(DATA, 'roads1086.geojson'), 'w'), separators=(',', ':'))
print('roman road features', len(rf))
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(DATA, 'landscape.geojson'), 'w'), separators=(',', ':'))
json.dump({'unsurveyed_share_gb': round(uns.area / gb_main.area, 4), 'new_forest_places': len(nf),
           'marsh': {n: h for n, _, h in MARSH}}, open(os.path.join(WORK, 'landscape_stats.json'), 'w'))
