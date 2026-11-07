"""Step 7. Every number quoted on the page, in the paper, blog, README, collage and Reddit post: data/results.json, with checks
against the companion studies (the same allocation must give the same totals)."""
import json, os, pickle, math
from collections import Counter
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union
from common import WORK, DATA, SCRATCH, GEO

P = pickle.load(open(os.path.join(WORK, 'places.pkl'), 'rb'))
R = pickle.load(open(os.path.join(WORK, 'realm.pkl'), 'rb'))
rows = P['rows']
d = pd.DataFrame(rows)
num = lambda c: pd.to_numeric(d[c], errors='coerce').fillna(0)
d['lat'] = pd.to_numeric(d['lat'], errors='coerce')
loc = d[d.lat.notna()]
LS = json.load(open(os.path.join(WORK, 'layout_stats.json')))
LAND = json.load(open(os.path.join(WORK, 'landscape_stats.json')))
V = json.load(open(os.path.join(DATA, 'vills.json')))
vc = V['cols']; vr = [dict(zip(vc, r)) for r in V['rows']]
E = [x['data'] for x in R['entries']]
r = {}
r['places_total'] = len(d); r['places_located'] = int(len(loc))
r['entries_total'] = len(E); r['entries_describing'] = sum(1 for x in R['entries'] if any(q['predicate'] == 'DESCRIBES' for q in x.get('relations', [])))
r['households_total'] = round(float(num('households').sum()), 1)
r['households_located'] = round(float(pd.to_numeric(loc.households, errors='coerce').fillna(0).sum()), 1)
r['places_with_households'] = int((num('households') > 0).sum())
r['vills_drawn'] = sum(1 for v in vr if v['dwell'] > 0)
r['dwellings_drawn'] = LS['houses']; r['waste_dwellings_drawn'] = LS['waste_houses']; r['dwellings_not_placed'] = LS['houses_skipped']
hh = num('households')
r['median_households'] = float(hh[hh > 0].median())
r['share_vills_under_10_households'] = round(float((hh[hh > 0] < 10).mean()), 3)
r['share_vills_under_25_households'] = round(float((hh[hh > 0] < 25).mean()), 3)
r['vills_100_plus_dwellings'] = sum(1 for v in vr if v['dwell'] >= 100)
top = sorted(vr, key=lambda v: -v['dwell'])[:12]
r['biggest'] = [{'name': v['name'], 'county': v['county'], 'dwellings': v['dwell']} for v in top]
r['town_estimates'] = int((d.town_dwellings.astype(str) != '').sum())
r['town_walls'] = LS.get('town_walls', 0)
r['walled_towns'] = LS.get('walled_towns', 0)
r['walled_town_names'] = sorted({f['properties']['n'] for f in json.load(open(os.path.join(DATA, 'townwalls.geojson')))['features']})
for k_ in ['streets', 'lane', 'green']: r['plans_' + k_] = LS.get('plan_' + k_, 0)
r['field_ha_drawn'] = int(LS.get('field_ha', 0)); r['meadow_ha_drawn'] = int(LS.get('meadow_ha', 0))
# estimates where Domesday gives no usable household figure (drawn pale, kept out of every recorded total above)
es = pd.read_csv(os.path.join(DATA, 'estimates.csv'))
r['est_vills'] = int(len(es)); r['est_dwellings'] = int(es.dwellings_estimated.sum())
r['est_dwellings_drawn'] = LS.get('houses_est', 0)
for k, lab in [('blank', 'no usable figure'), ('waste', 'waste, nobody counted'), ('unsurveyed', 'unsurveyed town')]:
    r['est_%s_vills' % k] = int((es.kind == lab).sum()); r['est_%s_dwellings' % k] = int(es.dwellings_estimated[es.kind == lab].sum())
r['est_by_ratio'] = LS.get('est_by_ratio', 0); r['est_by_quartile'] = LS.get('est_by_quartile', 0); r['est_capped'] = LS.get('est_capped', 0)
r['est_london'] = int(es.dwellings_estimated[(es.name == 'London')].sum()); r['est_winchester'] = int(es.dwellings_estimated[(es.name == 'Winchester')].sum())
r['est_london_people'] = 10000; r['est_winchester_people'] = 5000; r['est_people_per_household'] = 4.5
assert r['est_london'] == round(10000 / 4.5) and r['est_winchester'] == round(5000 / 4.5)
assert r['est_dwellings'] == r['est_blank_dwellings'] + r['est_waste_dwellings'] + r['est_unsurveyed_dwellings']
# households by class
for k in ['villagers', 'smallholders', 'cottagers', 'slaves', 'freemen', 'freeMen', 'burgesses', 'priests']:
    r['class_' + k] = round(float(num(k).sum()), 1)
# ploughs, mills, churches, castles
r['plough_teams'] = round(float(num('ploughTeams').sum()), 1)
r['plough_teams_drawn'] = LS['da-plough']; r['oxen_in_teams'] = int(round(r['plough_teams'] * 8))
r['ploughlands'] = round(float(num('ploughlands').sum()), 1)
r['mills_on_places'] = round(float(num('mills').sum()), 2)
r['mills_drawn_records'] = round(LS['mills_rec'], 2); r['mills_rounded'] = LS['mills_rounded']; r['mills_drawn'] = LS['mills_drawn']; r['mills_no_stream'] = LS['mills_no_stream']
r['mills_drawn_share'] = round(LS['mills_drawn'] / LS['mills_rounded'], 3)
r['entries_with_church'] = sum(1 for x in E if x.get('hasChurch'))
r['places_with_church'] = int((num('church_entries') > 0).sum())
r['churches_drawn'] = LS.get('dch-wood', 0) + LS.get('dch-stone', 0) + LS.get('dch-minster', 0) + LS.get('dch-cathedral', 0)
hv = loc[pd.to_numeric(loc.households, errors='coerce').fillna(0) > 0]
r['share_vills_with_church'] = round(float((pd.to_numeric(hv.church_entries, errors='coerce').fillna(0) > 0).mean()), 3)
r['share_vills_with_mill'] = round(float((pd.to_numeric(hv.mills, errors='coerce').fillna(0) > 0).mean()), 3)
X = json.load(open(os.path.join(DATA, 'extras.json')))
r['castles_named_domesday'] = 41
r['castles_drawn'] = LS['castles']; r['castles_other_drawn'] = LS['castles_other']
r['abbeys_drawn'] = LS['abbeys']; r['markets_drawn'] = LS.get('dmarket', 0); r['markets_gazetteer_to_1086'] = len(X['markets'])
r['entries_with_market'] = sum(1 for x in E if x.get('hasMarket'))
# salt, fish, vines, parks
r['salt_houses'] = round(float(num('saltHouses').sum()), 1); r['salt_vills'] = LS['salt_vills']; r['salt_hearths_drawn'] = LS['dsalt']
r['droitwich_salt'] = round(float(num('d_saltHouses')[d.name == 'Droitwich'].sum()), 1)
r['fisheries'] = round(float(num('fisheries').sum()), 1); r['fish_vills'] = LS['fish_vills']; r['fisheries_drawn'] = LS['dfish']
r['eels'] = int(num('eels').sum())
r['vineyard_places'] = int((num('vine') > 0).sum()); r['vineyards_drawn'] = LS['dvine']
r['parks'] = int((num('park') > 0).sum()); r['haias'] = int((num('haia') > 0).sum())
# livestock
for k in ['sheep', 'pigs', 'cattle', 'cows', 'goats', 'cobs', 'horses', 'beehives', 'wildmares', 'oxen']:
    r['stock_' + k] = int(num(k).sum())
LDc = d.county.isin(['ESS', 'NFK', 'SUF'])
r['sheep_share_little_domesday'] = round(float(num('sheep')[LDc].sum() / max(1, num('sheep').sum())), 3)
r['sheep_flocks_drawn'] = LS['da-sheep']
r['animals_drawn'] = sum(LS.get(k, 0) for k in ['da-sheep', 'da-cattle', 'da-goat', 'da-cob', 'da-mare', 'da-pig', 'da-hives', 'da-oxen', 'da-pigwood'])
r['woodland_pigs'] = int(num('woodlandPigs').sum())
r['places_with_woodland'] = int(((num('wood_ha') > 0) | (num('woodlandPigs') > 0)).sum())
r['woodland_ha_estimate'] = int(LS['wood_ha_rec']); r['woodland_ha_drawn'] = int(LS['wood_ha_drawn'])
r['woodland_km2_drawn'] = int(LS['wood_ha_drawn'] / 100)
# waste
r['waste_entries_all'] = sum(1 for x in E if x.get('isWaste'))
# as the Harrying of the North study counts them: entries about a place (kind manor or urban)
r['waste_entries'] = sum(1 for x in R['entries'] if x['data'].get('isWaste') and x['data'].get('kind') in ('manor', 'urban'))
r['waste_entries_yorkshire'] = sum(1 for x in E if x.get('isWaste') and x.get('county') == 'YKS')
r['waste_vills'] = LS['waste_vills']; r['waste_vills_empty_drawn'] = LS['dwaste']
# values
r['value1066_pence'] = int(num('value1066').sum()); r['value1086_pence'] = int(num('value1086').sum())
# landscape and lettering
r['unsurveyed_share_gb'] = LAND['unsurveyed_share_gb']
cu = json.load(open(os.path.join(GEO, 'counties_uk.geojson')))
lab = json.load(open(os.path.join(DATA, 'labels1086.geojson')))
r['hundreds_lettered'] = sum(1 for f in lab['features'] if f['properties']['kind'] == 'hundred')
r['shires'] = len(set(d.county))
land = json.load(open(os.path.join(DATA, 'landscape.geojson')))
uns = unary_union([shape(f['geometry']) for f in land['features'] if f['properties']['kind'] == 'unsurveyed'])
eng = [shape(f['geometry']).buffer(0) for f in cu['features'] if f['properties'].get('nation') == 'England']
if eng:
    E_ = unary_union(eng).buffer(0)
    r['unsurveyed_share_england'] = round(E_.intersection(uns).area / E_.area, 3)
r['marsh_areas'] = list(LAND['marsh'].keys())
r['new_forest_places'] = LAND['new_forest_places']
r['travellers_drawn'] = LS.get('travellers', 0)
r['drawn_points_total'] = sum(c[2] for c in json.load(open(os.path.join(DATA, 'dw', 'index.json')))['cells'])
# ---------------------------------------------------------------- checks against the companion studies
dd = json.load(open(os.path.join(SCRATCH, 'domesday-destiny', 'data', 'results.json')))
mm = json.load(open(os.path.join(SCRATCH, 'domesday-mills', 'data', 'results.json')))
hn = json.load(open(os.path.join(SCRATCH, 'harrying-of-the-north', 'data', 'results.json')))
nc = json.load(open(os.path.join(SCRATCH, 'norman-castles', 'data', 'results.json')))
assert abs(r['households_total'] - dd['households_1086_total']) < 1, (r['households_total'], dd['households_1086_total'])
assert r['places_total'] == dd['places_total'] and r['places_located'] == dd['places_located']
assert abs(r['mills_on_places'] + mm['domesday']['mills_no_place'] - mm['domesday']['mills_total']) < 0.01
assert r['waste_entries'] == hn['n_waste_entries'], (r['waste_entries'], hn['n_waste_entries'])
assert nc['n_domesday_castles'] == r['castles_named_domesday']
assert r['dwellings_drawn'] > 0.9 * r['households_located']
r['checks'] = {'households_equals_domesday_destiny': dd['households_1086_total'], 'mills_with_no_place_equals_mills_study': mm['domesday']['mills_total'],
               'waste_entries_equals_harrying_study': hn['n_waste_entries'], 'castles_named_equals_norman_castles_study': nc['n_domesday_castles']}
json.dump(r, open(os.path.join(DATA, 'results.json'), 'w'), indent=1)
for k, v in r.items():
    if not isinstance(v, (list, dict)): print(k, v)
print(r['biggest'])
