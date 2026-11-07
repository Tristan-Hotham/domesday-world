"""Shared paths for England in 1086, drawn (domesday-world). Raw inputs are read in place."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
WORK = os.environ.get('DW_WORK', '/home/claude/work/domesday-world')   # intermediates (not in the repository)
REALM = os.environ.get('DW_REALM', '/home/claude/scratch/realm')      # github.com/embabel-worlds/realm-domesday
SCRATCH = os.environ.get('DW_SCRATCH', '/home/claude/scratch')        # companion studies
STUDIES = os.environ.get('DW_STUDIES', '/home/claude/studies')
INK = os.path.join(STUDIES, 'ink-map')                                # the Inked World engine this fork starts from
MYM = os.path.join(SCRATCH, 'mym')                                    # monasteries and markets
ROMAN = os.path.join(STUDIES, 'roman-roads', 'data', 'roads.geojson.gz')
TERRARIUM = os.environ.get('DW_DEM', '/home/claude/newdata/raw9/terrarium')
GEO = '/home/claude/newdata/raw/geo'
OFM_TILES = 'https://tiles.openfreemap.org/planet/20261101_080013_pt/{z}/{x}/{y}.pbf'
os.makedirs(WORK, exist_ok=True)
