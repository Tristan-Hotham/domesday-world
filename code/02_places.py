"""Step 2. Domesday entries to places: what each vill had in 1086, ready to draw.

Reads WORK/realm.pkl (01_extract.py) and the companion studies; writes
  data/domesday_places.csv      one row per Domesday place (located or not): figures, features, holders, flags
  data/town_estimates.csv       the dwellings drawn for the boroughs, with the Domesday words each estimate rests on
  WORK/places.pkl               the same rows plus long fields (quotes, holders) for the page builder

Allocation (as in the Domesday Destiny study, so totals agree with it): an entry's figures go to the places it
DESCRIBES, shared equally when it describes several. For DRAWING only, an entry that also names dependent members
(INCLUDES) that Hull located has its households and resources spread over the head and those members, the head taking
a double share; the popup says so. Text features (vineyards, salt, eels, woodland measures, parks, wild mares) are read
from Hull's transcription of the Phillimore text, which omits Yorkshire.
"""
import csv, math, os, pickle, re
from collections import defaultdict, Counter
from common import WORK, DATA, SCRATCH

R = pickle.load(open(os.path.join(WORK, 'realm.pkl'), 'rb'))
PL = {d['data']['placeId']: d['data'] for d in R['places']}
PEOPLE = R['people']

NUM = r'(\d+(?:\s?1/2)?|1/2|a|one|two|three|four|five|six)'
WORDN = {'a': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, '1/2': 0.5}
def num(s):
    s = s.strip().lower()
    if s in WORDN: return WORDN[s]
    m = re.match(r'(\d+)\s?1/2', s)
    if m: return int(m.group(1)) + 0.5
    try: return float(s.replace(',', ''))
    except ValueError: return 0

LEAGUE_KM, FURLONG_KM = 12 * 0.2012, 0.2012        # a Domesday league taken as 12 furlongs (about 2.4 km)
def dim_km(n, unit):
    return n * (LEAGUE_KM if unit.startswith('league') else FURLONG_KM if unit.startswith('furlong') else 0.0201 * 0.2)

# woodland, as Domesday measures it: by the pigs it fed, or by its length and breadth in leagues and furlongs, or in acres
RX_WPIGS = re.compile(r'woodland[^.;]{0,25}?(?:for|at|,)\s*(\d[\d,]*)\s+pigs', re.I)
RX_WLEN = re.compile(r'woodland,?\s*(?:pasture,?\s*)?(\d+(?:\s?1/2)?|1/2)\s+(leagues?|furlongs?)\s+(?:long|in length)?(?:\s+and\s+(\d+(?:\s?1/2)?|1/2)\s*(leagues?|furlongs?)?\s+(?:wide|in width|broad))?', re.I)
RX_WASWIDE = re.compile(r'woodland,?\s*(\d+(?:\s?1/2)?|1/2)\s+(leagues?|furlongs?)\s+long and as (?:much )?wide', re.I)
RX_WACRES = re.compile(r'woodland,?\s*(\d[\d,]*)\s+acres', re.I)
RX_VINE = re.compile(r'(\d+(?:\s?1/2)?|1/2)?\s*arpents? of vines?|vineyard(?:,\s*(\d+(?:\s?1/2)?)\s*(arpents?|acres?))?|vines? newly planted', re.I)
RX_SALT = re.compile(r'(\d+(?:\s?1/2)?|1/2|a|one)?\s*(?:salt[- ]?houses?|salt[- ]?pans?|salt[- ]?workers?|salt[- ]?boilers?|salt-?works?|brine[- ]pits?|saltern)', re.I)
RX_FISH = re.compile(r'(\d+(?:\s?1/2)?|1/2|a|one|two|three)?\s*(?:fisheries|fishery|fishponds?|weirs?)\b', re.I)
RX_EELS = re.compile(r'(\d[\d,]*)\s+eels', re.I)
RX_PARK = re.compile(r'\bpark\b', re.I)
RX_HAIA = re.compile(r'hedged enclosures?|\bhay\b|\bhaia\b', re.I)
RX_FOREST = re.compile(r"(?:King's\s+)?forest", re.I)
RX_MARES = re.compile(r'(\d+)\s+(?:wild|unbroken)\s+mares', re.I)
RX_ROUNCEY = re.compile(r'(\d+|a|one)\s+(?:cob|rouncey|riding horse|horses?)s?\b', re.I)
RX_MILLV = re.compile(r'((?:\d+(?:\s?1/2)?|1/2|a|one|two|three|four|five|six)\s+(?:and a half\s+)?mills?|(?:a|the)\s+(?:half|share of a|part of a)\s+mill|mill)\s*,?\s*(?:which\s+pays?|paying|pays?|at|of|rendering)?\s*,?\s*((?:£\s?\d+(?:\s\d+s)?(?:\s\d+d)?)|(?:\d+s(?:\s\d+d)?)|(?:\d+d))', re.I)
RX_MINSTER = re.compile(r'minster|canons|monks|abbey|abbot|cathedral', re.I)
RX_TOTAL = re.compile(r'\b(in total|altogether)\b', re.I)

FIG = ['households', 'villagers', 'smallholders', 'slaves', 'cottagers', 'freemen', 'freeMen', 'priests', 'burgesses',
       'ploughmen', 'riders', 'menAtArms', 'frenchmen', 'englishmen', 'smiths', 'swineherds', 'beekeepers', 'fishermen',
       'ploughTeams', 'lordsTeams', 'mensTeams', 'ploughlands', 'mills', 'value1066', 'valueLater', 'value1086', 'geldUnits',
       'meadowAcres', 'woodlandPigs', 'fisheries', 'saltHouses', 'pigs', 'cobs', 'beehives', 'oxen', 'horses', 'cows',
       'pastureSheep', 'sheep', 'cattle', 'goats']
TXT = ['wood_ha', 'vine', 'vine_arpents', 'salt_t', 'fish_t', 'eels', 'park', 'haia', 'forest', 'wildmares', 'minster_t']

def text_features(t):
    f = defaultdict(float)
    if not t: return f
    # woodland area in hectares (a drawing estimate; see the paper): pigs at 1 ha a pig; length x breadth x 0.7;
    # length alone as a strip a quarter as wide; acres at 0.4 ha (a Domesday acre is uncertain)
    wha = 0
    for m in RX_WPIGS.finditer(t): wha += num(m.group(1)) * 1.0
    seen = set()
    for m in RX_WASWIDE.finditer(t):
        L = dim_km(num(m.group(1)), m.group(2).lower()); wha += L * L * 0.7 * 100; seen.add(m.start())
    for m in RX_WLEN.finditer(t):
        if m.start() in seen: continue
        L = dim_km(num(m.group(1)), m.group(2).lower())
        if m.group(3):
            W = dim_km(num(m.group(3)), (m.group(4) or m.group(2)).lower()); wha += L * W * 0.7 * 100
        else:
            wha += L * L * 0.25 * 100
    for m in RX_WACRES.finditer(t): wha += num(m.group(1)) * 0.4
    if 'woodland' in t.lower() and wha == 0: wha = 10       # woodland named but not measured: a small wood
    f['wood_ha'] = wha
    for m in RX_VINE.finditer(t):
        f['vine'] = 1
        a = m.group(1) or m.group(2)
        if a: f['vine_arpents'] += num(a)
    for m in RX_SALT.finditer(t):
        f['salt_t'] += num(m.group(1)) if m.group(1) else 1
    for m in RX_FISH.finditer(t):
        f['fish_t'] += num(m.group(1)) if m.group(1) else 1
    for m in RX_EELS.finditer(t): f['eels'] += num(m.group(1))
    if RX_PARK.search(t): f['park'] = 1
    if RX_HAIA.search(t): f['haia'] = 1
    if RX_FOREST.search(t): f['forest'] = 1
    for m in RX_MARES.finditer(t): f['wildmares'] += num(m.group(1))
    if RX_MINSTER.search(t): f['minster_t'] = 1
    return f

def mill_render(t):
    """'2 mills at 10s' -> list of (count text, render) pairs as the text gives them."""
    out = []
    for m in RX_MILLV.finditer(t or ''):
        out.append(m.group(0).strip(' ,;'))
    return out[:3]

def holders(d, preds):
    out = []
    for r in d.get('relations', []):
        if r['predicate'] in preds:
            p = PEOPLE.get(r['to'].get('personId'))
            if p:
                n = p.get('canonicalName') or p.get('name')
                if n and n not in out: out.append(n)
    return out

def quote_of(t):
    if not t: return ''
    t = re.sub(r'\[!1!\s*|\s*!1!\]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    s = re.split(r'(?<=[.;])\s+', t)
    q = ''
    for x in s:
        if len(q) + len(x) > 230 and q: break
        q = (q + ' ' + x).strip()
    if len(q) > 260: q = q[:257].rsplit(' ', 1)[0] + '...'
    return q

# ---------------------------------------------------------------- entries
acc = defaultdict(lambda: defaultdict(float))      # by DESCRIBES, equal shares (totals and popups)
draw = defaultdict(lambda: defaultdict(float))     # spread over members too (drawing)
has = defaultdict(set)
ent = defaultdict(list)                            # refs and roles per place
quotes = defaultdict(list)
mills_txt = defaultdict(list)
lords66 = defaultdict(Counter); tic = defaultdict(Counter); ten86 = defaultdict(Counter)
member_of = defaultdict(set)
waste_n = defaultdict(int); church_n = defaultdict(int); castle_n = defaultdict(int); market_n = defaultdict(int)
total_clause = defaultdict(float)
nE = Counter()
kinds_used = ('manor', 'urban', 'Wales')
SALTTOWNS = {'Droitwich', 'Nantwich', 'Middlewich', 'Northwich'}
URBANP = {r['to']['placeId'] for d in R['entries'] if d['data'].get('kind') == 'urban' for r in d.get('relations', []) if r['predicate'] == 'DESCRIBES'}
URBANP |= {pid for pid, p in PL.items() if (p.get('name'), p.get('county')) in {('London', 'MDX'), ('Winchester', 'HAM')}}
for d in R['entries']:
    e = d['data']
    rel = d.get('relations', [])
    tg = [r['to']['placeId'] for r in rel if r['predicate'] == 'DESCRIBES' and r['to'].get('type') == 'DomesdayPlace']
    inc = [r['to']['placeId'] for r in rel if r['predicate'] == 'INCLUDES' and r['to'].get('type') == 'DomesdayPlace']
    if not tg: continue
    nE['describing'] += 1
    k = len(tg)
    txt = e.get('text') or ''
    tf = text_features(txt) if e.get('kind') in kinds_used else {}
    # members Hull located and that are not themselves described by this entry
    mem = [p for p in inc if p not in tg and PL.get(p, {}).get('lat') is not None]
    for pid in tg:
        ent[pid].append(e['ref'])
        for f in FIG:
            v = e.get(f)
            if v is None or isinstance(v, bool): continue
            acc[pid][f] += float(v) / k; has[pid].add(f)
        for f, v in tf.items():
            acc[pid][f] += v / k; has[pid].add(f)
        if e.get('isWaste'): waste_n[pid] += 1
        if e.get('hasChurch'): church_n[pid] += 1
        if e.get('hasCastle'): castle_n[pid] += 1
        if e.get('hasMarket'): market_n[pid] += 1
        q = quote_of(txt)
        if q and e.get('kind') in kinds_used: quotes[pid].append((e['ref'], q))
        for mt in mill_render(txt): mills_txt[pid].append(mt)
        for n in holders(d, ('LORD_1066',)): lords66[pid][n] += 1
        for n in holders(d, ('TENANT_IN_CHIEF',)): tic[pid][n] += 1
        for n in holders(d, ('TENANT_1086',)): ten86[pid][n] += 1
        if e.get('households') is not None and RX_TOTAL.search(txt): total_clause[pid] += float(e['households']) / k
    # drawing shares: head(s) 2 parts each, rural members 1 part each. Boroughs and unsurveyed cities named as members
    # (houses in London or Winchester that belong to a manor) take no share of the manor's people or land; salt-houses
    # in the salt towns (Droitwich and the Cheshire wiches) go to the salt town itself
    salt_mem = [p for p in mem if PL[p]['name'] in SALTTOWNS]
    mem = [p for p in mem if p not in URBANP]
    parts = {p: 2.0 for p in tg}
    for p in mem: parts[p] = parts.get(p, 0) + 1.0
    tot = sum(parts.values())
    for f in FIG + TXT:
        v = e.get(f) if f in FIG else (tf.get(f) if tf else None)
        if v is None or isinstance(v, bool) or not v: continue
        if f in ('saltHouses', 'salt_t') and salt_mem:
            for p in salt_mem: draw[p][f] += float(v) / len(salt_mem)
            continue
        for p, w in parts.items(): draw[p][f] += float(v) * w / tot
    for p in mem:
        member_of[p].add(e['ref'])
print('entries describing places', nE['describing'])

# ---------------------------------------------------------------- boroughs: dwellings from the words of the entries
URB = defaultdict(lambda: [0, 0])  # occupied, waste
RX_HOUSE = re.compile(r'(\d[\d,]*)\s+((?:\w+\s){0,3}?)(houses|dwellings|residences|messuages|burgesses|sites|plots|mansiones|lodgings)', re.I)
for d in R['entries']:
    e = d['data']
    if e.get('kind') != 'urban': continue
    tg = [r['to']['placeId'] for r in d.get('relations', []) if r['predicate'] == 'DESCRIBES']
    t = e.get('text') or ''
    for s in re.split(r'(?<=[.;])\s+', t):
        if re.search(r'before 1066|in 1066|then there were|there used to be|formerly', s, re.I): continue
        for m in RX_HOUSE.finditer(s):
            n = num(m.group(1)); pre = m.group(2).lower()
            ctx = s[max(0, m.start() - 40):m.end() + 40].lower()
            waste = re.search(r'empty|waste|destroyed|unoccupied|uninhabited|vacant', pre + ' ' + ctx) is not None
            for pid in tg: URB[pid][1 if waste else 0] += n / len(tg)

# hand-checked estimates for the great boroughs, each resting on Domesday's own count (overrides the automatic sum)
TOWNS = {  # name, county: (occupied dwellings drawn, waste dwellings drawn, basis)
    ('York', 'YKS'): (540, 540, "an estimate: Domesday's account of York (its text is not in the Hull transcription, which omits Yorkshire) records several hundred dwellings still inhabited and some 540 standing empty after 1069; drawn as 540 inhabited and 540 empty"),
    ('Lincoln', 'LIN'): (760, 240, '"970 inhabited messuages before 1066"; "166 were destroyed because of the castle; the remaining 74 are unoccupied"; "760 are now inhabited"'),
    ('Norwich', 'NFK'): (1145, 297, '"665 English burgesses" and "480 smallholders who, because of their poverty, pay no customary dues"; 9, 17 and 190 empty messuages and 81 taken by the castle'),
    ('Thetford', 'NFK'): (720, 224, '"Now there are 720 burgesses and 224 empty messuages" (943 burgesses before 1066)'),
    ('Oxford', 'OXF'): (243, 478, '"243 houses which pay tax" and "500 houses less 22 so derelict and destroyed that they cannot pay tax"'),
    ('Wallingford', 'BRK'): (263, 8, '"276 sites" before 1066, "13 fewer sites" now, "8 were destroyed for the castle"'),
    ('Chester', 'CHS'): (226, 205, '"431 houses" paying tax before 1066; when Earl Hugh acquired it "there were 205 houses less", and now "as many as he found"'),
    ('Exeter', 'DEV'): (285, 48, 'the King has "300 houses less 15" paying customary dues; "48 houses destroyed" since the King came'),
    ('Colchester', 'ESS'): (None, 0, "Colchester's burgesses' houses are listed one by one in Little Domesday; drawn from the households and houses counted"),
    ('Ipswich', 'SUF'): (None, 328, '"328 messuages" laid waste; the burgesses who remain are drawn from the houses and burgesses counted'),
    ('Shrewsbury', 'SHR'): (200, 51, '"252 houses" before 1066; 51 messuages destroyed for the castle and 50 others waste'),
    ('Canterbury', 'KEN'): (275, 0, '"19 burgesses who pay tribute", "212 burgesses over whom the King has full jurisdiction" and the Archbishop\'s "12 burgesses and 32 messuages"'),
    ('Stamford', 'LIN'): (310, 5, '141 messuages in the King\'s part and others held by lords; about 310 in all'),
    ('Nottingham', 'NTT'): (173, 0, '"173 burgesses" (with 19 smallholders) and houses held by lords'),
    ('Derby', 'DBY'): (140, 103, '"100 burgesses" and 40 lesser burgesses; "103 messuages" waste'),
    ('Leicester', 'LEC'): (None, 4, 'the houses of the King and barons, listed one by one and summed ("4 unoccupied houses")'),
    ('Huntingdon', 'HUN'): (256, 132, '"116 burgesses" and "140 burgesses" in its quarters; 60, 8 and 44 "unoccupied messuages" and 20 on the castle site'),
    ('Hereford', 'HEF'): (130, 0, '"103 men dwelling inside and outside the wall" before 1066, "27 burgesses" of Earl Harold and the bishop\'s 60 messuages found by Bishop Robert; an estimate'),
    ('Warwick', 'WAR'): (225, 4, '"113 houses" in the King\'s lordship and 112 of the barons'),
    ('Dunwich', 'SUF'): (236, 0, '236 burgesses'),
    ('Torksey', 'LIN'): (102, 111, '"102 burgesses" and "111 messuages" waste'),
    ('Gloucester', 'GLS'): (None, 30, '"16 houses" where the castle is sited "which do not exist now" and "14 houses ... destroyed"; occupied houses from those counted'),
    ('Worcester', 'WOR'): (143, 0, '"90 houses" belonging to the bishop\'s manor, "25 houses" in the market place and the 28 messuages of Evesham'),
    ('Northampton', 'NTH'): (None, 0, '"60 burgesses" before 1066, "40 burgesses in the new Borough" and the houses of the barons, summed'),
    ('Cambridge', 'CAM'): (None, 27, 'the houses and messuages of its wards, summed; "27 houses have been destroyed for the castle"'),
    ('Hertford', 'HRT'): (146, 0, '"146 burgesses"'),
    ('Bath', 'SOM'): (178, 6, '"64 burgesses", "90 burgesses" and 24 others; "6 unoccupied houses"'),
    ('Dorchester', 'DOR'): (88, 84, '"172 houses" before 1066; "now there are 88"'),
    ('Wareham', 'DOR'): (135, 77, '"70 houses" of the King, "45 houses standing and 17 unoccupied" and "20 houses standing and 60 have been destroyed"'),
    ('Shaftesbury', 'DOR'): (177, 58, '"66 houses" and "111 houses" now; "38 houses have been destroyed" and "20 empty messuages"'),
    ('Bridport', 'DOR'): (100, 0, '"120 houses" before 1066; "now there are 100"'),
    ('Sandwich', 'KEN'): (339, 0, '"307 habitable messuages" and the Archbishop\'s "32 messuages"'),
    ('Lewes', 'SUS'): (None, 20, 'the burgesses and sites counted; "20 uninhabited" messuages'),
    ('Chichester', 'SUS'): (157, 0, '"100 sites less 2 1/2" before 1066 and "60 more houses than there were before"'),
    ('Guildford', 'SUR'): (75, 0, '"75 sites, whereon dwell 175 men"'),
    ('Southampton', 'HAM'): (None, 0, 'the houses and men counted, summed'),
    ('Bedford', 'BDF'): (None, 0, 'the burgesses and houses counted'),
    ('Buckingham', 'BUK'): (52, 0, '26 burgesses and 26 more of the barons'),
    ('Stafford', 'STS'): (156, 8, 'the King\'s "18 burgesses" and the messuages of the earls and barons, summed; "8 unoccupied messuages"'),
    ('Rochester', 'KEN'): (80, 0, '"80 messuages"'),
    ('Totnes', 'DEV'): (110, 0, '"100 burgesses, less 5" within the Borough "and 15 outside"'),
    ('Barnstaple', 'DEV'): (66, 36, '"40 burgesses within the Borough, 9 outside" and 17 of the bishop and Baldwin; "23 houses destroyed" and 13 more'),
    ('Bodmin', 'CON'): (68, 0, '"68 houses"'),
    ('Malmesbury', 'WIL'): (40, 31, '"26 inhabited messuages" of the King and others of the abbots; "25 messuages ... which do not pay tax any more than waste land" and 6 unoccupied'),
    ('Reading', 'BRK'): (58, 0, '"28 sites" and 30 more'),
    ('Windsor', 'BRK'): (100, 0, '"100 sites"'),
    ('Pevensey', 'SUS'): (None, 0, '"60 burgesses" of the Count and those of the monks and others, summed'),
    ('Hastings', 'SUS'): (None, 0, 'the burgesses and houses counted'),
    ('Romney', 'KEN'): (50, 0, '"50 burgesses in the Borough of ROMNEY"'),
    ('Dover', 'KEN'): (None, 0, 'the houses counted ("29 messuages whose customary dues the King has lost")'),
    ('Fordwich', 'KEN'): (79, 0, '"73 messuages" and 6 burgesses'),
    ('Sudbury', 'SUF'): (123, 0, '"63 burgesses who dwell at the hall", "55 burgesses in lordship" and 5 in Essex'),
    ('Yarmouth', 'NFK'): (70, 0, '"70 burgesses"'),
    ('Maldon', 'ESS'): (180, 18, 'about 180 houses; 18 waste'),
    ('Grantham', 'LIN'): (111, 0, '"111 burgesses"'),
    ('Louth', 'LIN'): (80, 0, '"80 burgesses"'),
    ('Newark', 'NTT'): (56, 0, '"56 burgesses"'),
    ('St Albans', 'HRT'): (46, 0, '"46 burgesses"'),
    ('Tamworth', 'STS'): (None, 0, 'the burgesses and houses counted'),
    ('Droitwich', 'WOR'): (None, 0, 'the burgesses counted among the manors with salt-houses, summed'),
    ('Wilton', 'WIL'): (None, 0, 'the burgesses and houses counted'),
    ('Marlborough', 'WIL'): (None, 0, 'the burgesses and houses counted'),
    ('Ilchester', 'SOM'): (None, 0, 'the burgesses and houses counted'),
    ('Taunton', 'SOM'): (64, 0, '"64 burgesses"'),
    ('Arundel', 'SUS'): (None, 0, 'the burgesses and sites counted'),
    ('Bristol', 'GLS'): (None, 0, 'the households counted at Barton by Bristol'),
    ('Steyning', 'SUS'): (123, 0, '123 burgesses'),
    ('Tutbury', 'STS'): (42, 0, '"42 men in trade in the market"'),
    ('Rhuddlan', 'CHS'): (18, 0, '"18 burgesses"'),
}
# London and Winchester were left out of the survey: drawn with walls and their great churches, not with houses
UNSURVEYED = {('London', 'MDX'), ('Winchester', 'HAM')}

# ---------------------------------------------------------------- the place table
def top(c, n=3): return [k for k, _ in c.most_common(n)]
rows, extra = [], {}
for pid, p in PL.items():
    a, w = acc.get(pid, {}), draw.get(pid, {})
    r = {'placeId': pid, 'name': p.get('name'), 'county': p.get('county'), 'countyName': p.get('countyName'),
         'hundred': p.get('hundred') or '', 'area': p.get('area') or '', 'lat': p.get('lat'), 'lng': p.get('lng'),
         'gridRef': p.get('gridRef') or '', 'openDomesdayPath': p.get('openDomesdayPath') or '',
         'inLittleDomesday': bool(p.get('inLittleDomesday')), 'likelyLost': bool(p.get('likelyLost')),
         'modernPlaceName': p.get('modernPlaceName') or '', 'wikipedia': p.get('wikipedia') or '',
         'entries': len(ent.get(pid, [])), 'memberOf': '; '.join(sorted(member_of.get(pid, [])))}
    for f in FIG + TXT:
        r[f] = round(a[f], 3) if f in has.get(pid, set()) else ''
    for f in ['households', 'burgesses', 'ploughTeams', 'mills', 'woodlandPigs', 'wood_ha', 'fisheries', 'fish_t', 'eels',
              'saltHouses', 'salt_t', 'vine', 'sheep', 'pigs', 'cattle', 'cows', 'goats', 'cobs', 'horses', 'oxen',
              'beehives', 'wildmares', 'pastureSheep', 'meadowAcres', 'park', 'haia', 'forest', 'minster_t']:
        r['d_' + f] = round(w.get(f, 0), 3)
    r['waste_entries'] = waste_n.get(pid, 0); r['church_entries'] = church_n.get(pid, 0)
    r['castle_entries'] = castle_n.get(pid, 0); r['market_entries'] = market_n.get(pid, 0)
    r['totalClauseHouseholds'] = round(total_clause[pid], 2) if pid in total_clause else ''
    key = (p.get('name'), p.get('county'))
    r['unsurveyed'] = key in UNSURVEYED
    r['urban'] = pid in URBANP
    occ, wst = URB.get(pid, (0, 0))
    if key in TOWNS:
        o = TOWNS[key][0]
        if o is None: o = int(round(max(occ, w.get('households', 0) or 0)))
        r['town_dwellings'], r['town_waste'], r['town_basis'] = o, TOWNS[key][1], TOWNS[key][2]
    elif occ >= 20 and occ > (w.get('households', 0) or 0):
        r['town_dwellings'], r['town_waste'] = int(round(occ)), int(round(URB[pid][1]))
        r['town_basis'] = 'sum of the houses, messuages, sites and burgesses its borough entries count for 1086 (automatic)'
    else:
        r['town_dwellings'], r['town_waste'], r['town_basis'] = '', '', ''
    r['lords1066'] = '; '.join(top(lords66.get(pid, Counter())))
    r['tenantsInChief'] = '; '.join(top(tic.get(pid, Counter())))
    r['tenants1086'] = '; '.join(top(ten86.get(pid, Counter())))
    rows.append(r)
    extra[pid] = {'quotes': quotes.get(pid, [])[:2], 'mills_txt': mills_txt.get(pid, [])[:3], 'refs': ent.get(pid, [])}

missing = [k for k in TOWNS if not any((r['name'], r['county']) == k for r in rows)]
print('town keys not found:', missing)
cols = list(rows[0].keys())
rows.sort(key=lambda r: int(r['placeId']))
with open(os.path.join(DATA, 'domesday_places.csv'), 'w', newline='', encoding='utf-8') as f:
    wr = csv.DictWriter(f, fieldnames=cols); wr.writeheader(); wr.writerows(rows)
with open(os.path.join(DATA, 'town_estimates.csv'), 'w', newline='', encoding='utf-8') as f:
    wr = csv.writer(f); wr.writerow(['placeId', 'name', 'county', 'households_recorded', 'dwellings_drawn', 'waste_dwellings_drawn', 'basis'])
    for r in rows:
        if r['town_dwellings'] != '':
            wr.writerow([r['placeId'], r['name'], r['countyName'], r['households'], r['town_dwellings'], r['town_waste'], r['town_basis']])
pickle.dump({'rows': rows, 'extra': extra}, open(os.path.join(WORK, 'places.pkl'), 'wb'))
hh = sum(r['households'] or 0 for r in rows)
print('places', len(rows), 'households (DESCRIBES shares)', round(hh, 1), 'mills', round(sum(r['mills'] or 0 for r in rows), 2))
print('towns with estimates', sum(1 for r in rows if r['town_dwellings'] != ''))
