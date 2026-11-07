"""Step 1. Read realm-domesday's reference YAML once and keep it as a compact pickle in the work folder.

Writes WORK/realm.pkl: places, entries (all fields, relations), people, hundreds, counties, little-domesday figures.
"""
import glob, os, pickle, sys, time
import yaml
from common import REALM, WORK
L = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
REF = os.path.join(REALM, 'reference')

def load(pat):
    for p in sorted(glob.glob(os.path.join(REF, pat))):
        with open(p, encoding='utf-8') as f:
            for d in yaml.load(f, Loader=L) or []:
                yield d

t = time.time()
out = {}
out['places'] = [d for d in load('03-places-*.yml')]
out['entries'] = [d for d in load('05-entries-*.yml')]
out['people'] = {d['data']['personId']: d['data'] for d in load('04-people-*.yml')}
out['hundreds'] = [d for d in load('02-hundreds-*.yml')]
out['counties'] = [d['data'] for d in load('01-counties-*.yml')]
out['figures'] = [d for d in load('045-figures-*.yml')]
for k, v in out.items():
    print(k, len(v))
with open(os.path.join(WORK, 'realm.pkl'), 'wb') as f:
    pickle.dump(out, f, protocol=5)
print('done', round(time.time() - t, 1), 's')
