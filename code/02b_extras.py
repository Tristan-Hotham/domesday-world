"""Step 2b. Castles, religious houses and markets of 1086, matched to Domesday places.

- Castles: the 41 castles Domesday names (Norman Castles study, data/domesday_castles.csv), any other place whose entries
  Hull codes with a castle (York, for one), and castles that later records date to 1086 or before (castles_dated.csv,
  Wikidata inception) that Domesday does not name, kept apart and marked so. Stone keeps only where one is documented by 1086.
- Religious houses: the English Monastic Archives database (UCL, via the Mind Your Manors hack weekend), houses founded by
  1086 and not dissolved before it, matched by name and county to a Domesday place (a few outside the survey placed by hand).
- Markets: the Gazetteer of Markets and Fairs in England and Wales to 1516 (Letters et al., Centre for Metropolitan
  History): markets first recorded in 1086 or before, matched to the nearest Domesday place of the same name.
Writes data/extras.json.
"""
import csv, glob, io, json, math, os, pickle, re, zipfile
from collections import defaultdict
import pandas as pd
from common import WORK, DATA, SCRATCH, MYM

P = pickle.load(open(os.path.join(WORK, 'places.pkl'), 'rb'))['rows']
loc = [r for r in P if r['lat'] is not None and r['lat'] == r['lat']]
def norm(s): return re.sub(r'[^a-z ]', '', re.sub(r'\[.*?\]|\(.*?\)', '', str(s).lower())).strip()
byname = defaultdict(list)
for r in loc: byname[norm(r['name'])].append(r)
def km(a, b, c, d): return math.hypot((c - a) * 111.2, (d - b) * 111.2 * math.cos(math.radians(a)))

# OS grid (eastings, northings) to WGS84, Helmert-free approximation good to ~100 m (enough for a market's place)
def os_to_ll(E, N):
    a, b = 6377563.396, 6356256.909; F0 = 0.9996012717; lat0 = math.radians(49); lon0 = math.radians(-2); N0, E0 = -100000, 400000
    e2 = 1 - (b * b) / (a * a); n = (a - b) / (a + b); lat = lat0; M = 0
    while True:
        lat = (N - N0 - M) / (a * F0) + lat
        Ma = (1 + n + 5 / 4 * n ** 2 + 5 / 4 * n ** 3) * (lat - lat0); Mb = (3 * n + 3 * n ** 2 + 21 / 8 * n ** 3) * math.sin(lat - lat0) * math.cos(lat + lat0)
        Mc = (15 / 8 * n ** 2 + 15 / 8 * n ** 3) * math.sin(2 * (lat - lat0)) * math.cos(2 * (lat + lat0)); Md = 35 / 24 * n ** 3 * math.sin(3 * (lat - lat0)) * math.cos(3 * (lat + lat0))
        M = b * F0 * (Ma - Mb + Mc - Md)
        if abs(N - N0 - M) < 0.01: break
    s = math.sin(lat); nu = a * F0 / math.sqrt(1 - e2 * s * s); rho = a * F0 * (1 - e2) / (1 - e2 * s * s) ** 1.5; eta2 = nu / rho - 1
    t = math.tan(lat); sec = 1 / math.cos(lat); dE = E - E0
    VII = t / (2 * rho * nu); VIII = t / (24 * rho * nu ** 3) * (5 + 3 * t * t + eta2 - 9 * t * t * eta2); X = sec / nu; XI = sec / (6 * nu ** 3) * (nu / rho + 2 * t * t)
    lat2 = lat - VII * dE ** 2 + VIII * dE ** 4; lon2 = lon0 + X * dE - XI * dE ** 3
    return math.degrees(lat2) + 0.0005, math.degrees(lon2) - 0.0015   # rough OSGB36 to WGS84 shift

out = {'castles': [], 'castles_other': [], 'abbeys': [], 'abbeys_unmatched': [], 'markets': [], 'markets_unmatched': []}

# ---------------------------------------------------------------- castles
STONE = {'Chepstow', 'Colchester', 'Richmond', 'Exeter', 'Ludlow', 'Tower of London', 'London'}
dc = pd.read_csv(os.path.join(SCRATCH, 'norman-castles', 'data', 'domesday_castles.csv'))
named = set()
for _, c in dc.iterrows():
    pid = str(int(c['placeId'])) if c['placeId'] == c['placeId'] else None
    if not pid: continue
    named.add(pid)
    out['castles'].append({'placeId': pid, 'name': c['castle'], 'ref': c['domesday_ref'], 'quote': c['quote'], 'stone': any(s in c['castle'] for s in STONE), 'source': 'named in Domesday (Norman Castles study)'})
cd0 = pd.read_csv(os.path.join(SCRATCH, 'norman-castles', 'data', 'castles_dated.csv'))
cd0 = cd0[(cd0.year >= 1066) & (cd0.year <= 1086)]
for r in loc:
    # a place Hull codes with a castle counts as named only where a castle of 1086 or before stands within 3 km (York, Nottingham)
    if (r['castle_entries'] or 0) > 0 and r['placeId'] not in named and any(km(c.lat, c.lon, r['lat'], r['lng']) < 3 for c in cd0.itertuples()):
        named.add(r['placeId'])
        out['castles'].append({'placeId': r['placeId'], 'name': r['name'], 'ref': '', 'quote': '', 'stone': r['name'] in STONE, 'source': "an entry Hull codes with a castle"})
cd = pd.read_csv(os.path.join(SCRATCH, 'norman-castles', 'data', 'castles_dated.csv'))
cd = cd[(cd.year >= 1066) & (cd.year <= 1086)]
for _, c in cd.iterrows():
    if any(km(c.lat, c.lon, r['lat'], r['lng']) < 5 for r in loc if r['placeId'] in named): continue
    out['castles_other'].append({'name': c.label, 'lat': c.lat, 'lon': c.lon, 'year': int(c.year), 'qid': c.qid, 'stone': any(s in c.label for s in STONE), 'county': c.county})
print('castles named', len(out['castles']), 'other dated by 1086', len(out['castles_other']))

# ---------------------------------------------------------------- religious houses
CT = {'Beds.': 'BDF', 'Berks.': 'BRK', 'Bucks.': 'BUK', 'Cambs.': 'CAM', 'Ches.': 'CHS', 'Cornw.': 'CON', 'Derb.': 'DBY', 'Devon': 'DEV', 'Dors.': 'DOR',
      'Essex': 'ESS', 'Glos.': 'GLS', 'Hants.': 'HAM', 'Herefs.': 'HEF', 'Herts.': 'HRT', 'Hunts.': 'HUN', 'Kent': 'KEN', 'Leics.': 'LEC', 'Lincs.': 'LIN',
      'Mdx.': 'MDX', 'London': 'MDX', 'Norf.': 'NFK', 'Northants.': 'NTH', 'Notts.': 'NTT', 'Oxon.': 'OXF', 'Rut.': 'RUT', 'Salop.': 'SHR', 'Som.': 'SOM',
      'Staffs.': 'STS', 'Suff.': 'SUF', 'Surr.': 'SUR', 'Suss.': 'SUS', 'Warws.': 'WAR', 'Wilts.': 'WIL', 'Worcs.': 'WOR', 'York': 'YKS', 'Yorks. ER': 'YKS',
      'Yorks. NR': 'YKS', 'Yorks. WR': 'YKS', 'Lancs.': 'YKS'}
HAND = {'Durham Cathedral': (54.7733, -1.5762), 'Jarrow': (54.9806, -1.4716), 'Wearmouth': (54.9131, -1.3833), 'Farne': (55.6161, -1.6545)}   # outside the survey: placed by hand
ALIAS = {'Buckfast or Buckfastleigh': 'Buckfast', 'Christchurch (Twyneham)': 'Twynham', 'Docco or Docco, at Lanow, near St Kew': 'St Kew', 'Perranzabuloe or Perran': 'Lanpiran',
         'St Benet of Hulme or St Benet of Holm': 'Horning', 'Molycourt or St Mary de Bello Loco': 'Outwell', 'Welle or Well Hall in Gayton': 'Gayton', 'Minster in Sheppey': 'Minster',
         'Waltham Holy Cross': 'Waltham', 'Westbury-on-Trym': 'Westbury', 'Monks Kirby': 'Kirby', 'Stoke by Clare': 'Stoke', 'Great Malvern': 'Malvern', 'Bury St Edmunds': 'Bury', 'Pontefract': 'Tanshelf',
         'Coventry Cathedral': 'Coventry', 'Ely Cathedral': 'Ely', 'Rochester Cathedral': 'Rochester', 'Worcester Cathedral': 'Worcester', 'Thetford, St George & St Gregory': 'Thetford',
         "St Michael's Mount": "St Michael's Mount", 'Battle': 'Battle'}
rh = pd.read_excel(os.path.join(MYM, 'Monastic Database full.xlsx'), sheet_name='EMA List of Religious Houses')
rh['fd'] = pd.to_numeric(rh['Founded date'], errors='coerce'); rh['dd'] = pd.to_numeric(rh['Dissolved date'], errors='coerce')
rh = rh[(rh.fd <= 1086) & ((rh.dd >= 1086) | rh.dd.isna())]
for _, h in rh.iterrows():
    nm = h['House Name']; base = ALIAS.get(nm, nm.split(',')[0].split(' or ')[0])
    rec = {'name': nm, 'type': h['House Type'], 'order': h['order'], 'founded': int(h.fd), 'modifier': h['Founded modifier'] if h['Founded modifier'] == h['Founded modifier'] else '', 'county': h['County']}
    if nm in HAND:
        rec.update({'lat': HAND[nm][0], 'lon': HAND[nm][1], 'placeId': None}); out['abbeys'].append(rec); continue
    cc = CT.get(h['County']); cands = [r for r in byname.get(norm(base), []) if r['county'] == cc] or byname.get(norm(base), [])
    if cands:
        r = cands[0]; rec.update({'placeId': r['placeId'], 'lat': r['lat'], 'lon': r['lng'], 'place': r['name']}); out['abbeys'].append(rec)
    else: out['abbeys_unmatched'].append(rec)
print('abbeys matched', len(out['abbeys']), 'unmatched', [a['name'] for a in out['abbeys_unmatched']])

# ---------------------------------------------------------------- markets
zp = os.path.join(MYM, 'Markets and Fairs in England and Wales to 1516.zip')
rows = []
with zipfile.ZipFile(zp) as z:
    for n in z.namelist():
        if not n.endswith('.tab'): continue
        L = z.read(n).decode('latin-1').split('\n'); h = L[0].split('\t')
        for l in L[1:]:
            if l.strip(): rows.append(dict(zip(h, l.split('\t'))))
def yr(s):
    m = re.search(r'(\d{3,4})', s or ''); return int(m.group(1)) if m else None
for r in rows:
    y = yr(r.get('M1_1st_Recorded'))
    if y is None or y > 1086 or 'wales' in r.get('Country_GAZ', '').lower(): continue
    try: lat, lon = os_to_ll(float(r['GridX']) * 100, float(r['GridY']) * 100)
    except (ValueError, KeyError): continue
    nm = norm(r['MODNAME'])
    cands = [p for p in loc if km(lat, lon, p['lat'], p['lng']) < 4]
    best = None
    for p in sorted(cands, key=lambda p: km(lat, lon, p['lat'], p['lng'])):
        pn = norm(p['name'])
        if pn and (pn in nm or nm in pn or pn.split()[0] == nm.split()[0]): best = p; break
    rec = {'name': r['MODNAME'].title(), 'county': r['County'].title(), 'first': r.get('M1_1st_Recorded', '').strip('"'), 'source': r.get('M1_Source', '').strip('"')[:120], 'lat': round(lat, 5), 'lon': round(lon, 5)}
    if best: rec['placeId'] = best['placeId']; out['markets'].append(rec)
    else: out['markets_unmatched'].append(rec)
print('markets to 1086 matched', len(out['markets']), 'unmatched', [m['name'] for m in out['markets_unmatched']])
json.dump(out, open(os.path.join(DATA, 'extras.json'), 'w'), indent=0, default=str)
