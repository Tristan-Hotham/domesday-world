"""Step 3a. The OpenFreeMap zoom 13 tiles round every located vill (3 km margin), for 03_ofm_water.js."""
import json, math, os
import pandas as pd
from common import DATA, WORK
d = pd.read_csv(os.path.join(DATA, 'domesday_places.csv'), low_memory=False)
d = d[d.lat.notna()]
def t(lat, lon, z=13):
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
S = set()
for la, lo in zip(d.lat, d.lng):
    dl = 3 / 111; dg = dl / math.cos(math.radians(la))
    for a in (-dl, 0, dl):
        for b in (-dg, 0, dg): S.add(t(la + a, lo + b))
json.dump(sorted(S), open(os.path.join(WORK, 'tiles13.json'), 'w'))
print(len(S))
