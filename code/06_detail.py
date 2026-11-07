"""Step 6. What the popups say: one record per drawn vill, in one file per county (data/detail/{county}.json), fetched when a
vill is first clicked. Figures are Domesday's own (by the Domesday Destiny allocation: an entry's figures shared equally among
the places it describes), the drawing counts are what 04_place.py drew, and the notes say plainly where a figure is missing,
estimated or shared. CC BY-NC-SA 4.0 (derived from the Hull Domesday Project's data and its transcription of the Phillimore text).
"""
import json, os, pickle
from collections import defaultdict
from common import WORK, DATA

P = pickle.load(open(os.path.join(WORK, 'places.pkl'), 'rb'))
rows = {r['placeId']: r for r in P['rows']}
EX = P['extra']
V = json.load(open(os.path.join(DATA, 'vills.json')))
X = json.load(open(os.path.join(DATA, 'extras.json')))
castles = {c['placeId']: c for c in X['castles']}
abbeys = defaultdict(list)
for a in X['abbeys']:
    if a.get('placeId'): abbeys[a['placeId']].append(a)
markets = {m['placeId']: m for m in X['markets']}
LD = {'ESS', 'NFK', 'SUF'}
EXON = {'DEV', 'CON', 'SOM', 'DOR', 'WIL'}

def num(v):
    try: return round(float(v), 2) if v not in ('', None) and float(v) == float(v) else None
    except (TypeError, ValueError): return None

out = defaultdict(dict)
cols = V['cols']
for row in V['rows']:
    v = dict(zip(cols, row)); r = rows[v['id']]; e = EX.get(v['id'], {})
    hh = {k: num(r[k]) for k in ['villagers', 'smallholders', 'cottagers', 'slaves', 'freemen', 'freeMen', 'priests', 'burgesses', 'riders', 'ploughmen', 'frenchmen', 'smiths', 'swineherds', 'fishermen', 'menAtArms'] if num(r[k])}
    stock = {k: num(r[k]) for k in ['sheep', 'pigs', 'cattle', 'cows', 'goats', 'cobs', 'horses', 'oxen', 'beehives', 'wildmares'] if num(r[k])}
    notes = []
    if r['county'] == 'YKS': notes.append("Yorkshire's text is not in the Hull transcription, so only its coded figures are shown; woodland, vineyards and fisheries are not read for Yorkshire.")
    if r['county'] in LD: notes.append('Little Domesday (Essex, Norfolk, Suffolk) counts livestock in full; its figures are parsed from the translation.')
    elif r['county'] in EXON: notes.append('The livestock here come from the Exeter Domesday additions.')
    else: notes.append('Great Domesday seldom counts livestock outside the south-west, so no flocks are drawn unless the entry gives them.')
    if r['memberOf']: notes.append('Named as a member of ' + r['memberOf'].split('; ')[0] + ('' if '; ' not in r['memberOf'] else ' and other entries') + '; its people may be counted with that manor, and part of that manor\'s households is drawn here (an estimate).')
    if num(r['households']) and v['dwell'] < num(r['households']) - 0.5 and not r['town_basis']: notes.append('Its entry also names outlying members; its households are drawn spread over them (this vill a double share), so fewer dwellings are drawn here than the entry counts.')
    if r['town_basis']: notes.append('Dwellings drawn: ' + str(r['town_dwellings']) + (' and ' + str(r['town_waste']) + ' empty or wasted' if r['town_waste'] not in ('', 0, '0') else '') + '. Basis: ' + r['town_basis'] + '.')
    if r['totalClauseHouseholds'] not in ('', None): notes.append('Part of the households here come from an entry that gives a total for a whole group of places ("in total"), so this vill may be drawn too large.')
    if r['unsurveyed']: notes.append('Left out of the survey: its ' + str(v['est']) + ' houses are an estimate (pale, dotted), from ' + v['estBasis'] + '; not counted in the recorded totals.')
    if v.get('est') and not r['unsurveyed']: notes.append(('Domesday calls this vill waste and counts nobody; ' + str(v['est']) + ' empty dwellings are drawn pale and roofless as an estimate: ' if v.get('estKind') == 'x' else 'Domesday gives no usable household figure here; ' + str(v['est']) + ' dwellings are drawn pale and dotted as an estimate: ') + v['estBasis'] + '. Not counted in the recorded totals.')
    d = {
        'n': r['name'], 'c': r['countyName'], 'h': r['hundred'], 'g': r['gridRef'], 'od': r['openDomesdayPath'], 'w': r['wikipedia'], 'm': r['modernPlaceName'],
        'lost': bool(r['likelyLost']), 'e': r['entries'], 'refs': e.get('refs', [])[:6], 'hh': num(r['households']), 'cls': hh,
        'pt': num(r['ploughTeams']), 'pl': num(r['ploughlands']), 'mills': num(r['mills']), 'mt': e.get('mills_txt', []), 'ch': r['church_entries'],
        'v66': num(r['value1066']), 'v86': num(r['value1086']), 'mead': num(r['meadowAcres']), 'wp': num(r['woodlandPigs']), 'wha': num(r['wood_ha']),
        'fish': num(r['fisheries']) or num(r['fish_t']), 'eels': num(r['eels']), 'salt': num(r['saltHouses']) or num(r['salt_t']), 'vine': bool(num(r['vine'])),
        'park': bool(num(r['park'])), 'haia': bool(num(r['haia'])), 'stock': stock, 'waste': r['waste_entries'], 'l66': r['lords1066'], 'tic': r['tenantsInChief'], 't86': r['tenants1086'],
        'q': e.get('quotes', [])[:1], 'dw': v['dwell'], 'md': v['millsDrawn'], 'mr': v['mills'],
        'castle': (castles[v['id']]['name'] + (' ("' + castles[v['id']]['quote'] + '")' if castles[v['id']].get('quote') and castles[v['id']]['quote'] == castles[v['id']]['quote'] else '')) if v['id'] in castles else '',
        'abbey': [a['name'] + ' (' + str(a['order']) + ', founded ' + (a['modifier'] + ' ' if a['modifier'] else '') + str(a['founded']) + ')' for a in abbeys.get(v['id'], [])],
        'market': (markets[v['id']]['first'] + ', ' + markets[v['id']]['source']) if v['id'] in markets else '', 'notes': notes,
    }
    out[r['county']][v['i']] = {k: x for k, x in d.items() if x not in (None, '', [], {}, False, 0) or k in ('dw',)}
od = os.path.join(DATA, 'detail'); os.makedirs(od, exist_ok=True)
tot = 0
for c, recs in out.items():
    json.dump(recs, open(os.path.join(od, c + '.json'), 'w'), separators=(',', ':')); tot += len(recs)
print('detail records', tot, 'files', len(out))
