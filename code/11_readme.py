"""Step 11. README.md and LICENSE, with every number from data/results.json."""
import json, os
from common import ROOT, DATA
R = json.load(open(os.path.join(DATA, 'results.json')))
def n(k, dp=0):
    v = R[k]; return f'{v:,.{dp}f}' if isinstance(v, float) else f'{v:,}'
pc = lambda k: f"{round(R[k] * 100)}%"
B = R['biggest']
readme = f"""# England in 1086, drawn

A zoomable hand-inked map of England in 1086, in the style of the maps in the front of a fantasy novel, where nothing modern is drawn and every settlement, house, mill, church, castle, plough team, flock, wood, fishery, salt-pan and vineyard comes from Domesday Book itself. It is the Inked World engine (https://maps.tristanhotham.com/ink-map/) with every modern layer taken out and Domesday drawn in.

Interactive page: https://maps.tristanhotham.com/domesday-world/
Paper: {{https://doi.org/10.5281/zenodo.24045206}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/domesday-world/}}
Code and data: https://github.com/Tristan-Hotham/domesday-world

## Headline results

- One drawn dwelling for each household Domesday counts: {n('households_total', 0)} households in all, {n('dwellings_drawn')} dwellings drawn at the {n('places_located')} located places. Close in one drawing per household; at zoom 11 one per two; further out a glyph of one to six huts per vill.
- Most vills were small: the median counted {n('median_households')} households, {pc('share_vills_under_10_households')} fewer than ten, and only {n('vills_100_plus_dwellings')} are drawn with a hundred dwellings or more.
- The largest places as drawn: {B[0]['name']} ({B[0]['dwellings']:,}), {B[1]['name']} ({B[1]['dwellings']:,}), {B[2]['name']} ({B[2]['dwellings']:,}) and {B[3]['name']} ({B[3]['dwellings']:,}, an estimate). {n('town_estimates')} boroughs are drawn from Domesday's own counts of houses, messuages and burgesses, with {n('waste_dwellings_drawn')} empty or destroyed houses drawn roofless.
- {n('mills_drawn')} mills drawn, each on the nearest stream or river within 1.5 km ({n('mills_on_places', 2)} mills recorded at located places; {n('mills_rounded')} after rounding each place's total; {n('mills_no_stream')} with no stream that close are not drawn). The wheels turn close in.
- {n('plough_teams_drawn')} plough teams of eight oxen ({n('plough_teams', 1)} recorded), {n('churches_drawn')} churches, {n('fisheries_drawn')} eel weirs, {n('salt_hearths_drawn')} salt hearths, {n('vineyards_drawn')} vineyards, {n('castles_drawn')} castles named in Domesday (and {n('castles_other_drawn')} more dated to 1086 or before), {n('abbeys_drawn')} religious houses.
- Livestock where Domesday counts it ({n('animals_drawn')} drawings): Little Domesday holds {pc('sheep_share_little_domesday')} of the {n('stock_sheep')} sheep recorded. Woodland drawn over about {n('woodland_km2_drawn')} square kilometres.
- {n('waste_entries')} entries call land waste, {n('waste_entries_yorkshire')} in Yorkshire; {n('waste_vills_empty_drawn')} vills with nobody counted are drawn as burnt huddles. The lands not surveyed (the north, Wales, Scotland) are {pc('unsurveyed_share_gb')} of Great Britain and {pc('unsurveyed_share_england')} of today's England.
- Estimates, kept out of every total above: {n('est_dwellings')} dwellings at {n('est_vills')} places Domesday names without a usable household figure, drawn pale (dotted, or roofless in waste vills) and flagged in the popup: {n('est_blank_dwellings')} at {n('est_blank_vills')} places with no people counted, {n('est_waste_dwellings')} empty ones at {n('est_waste_vills')} waste vills, and {n('est_london')} for London and {n('est_winchester')} for Winchester, which the survey left out (the low end of historians' estimates, {n('est_london_people')} and {n('est_winchester_people')} people, at 4.5 a household). Method in `data/estimates.csv` and the paper.

The totals agree with the companion studies: households with Domesday Destiny ({R['checks']['households_equals_domesday_destiny']:,}), mills with Domesday mills ({R['checks']['mills_with_no_place_equals_mills_study']:,} including mills at unplaced entries), waste entries with the Harrying of the North ({R['checks']['waste_entries_equals_harrying_study']:,}) and the castles named with Norman castles ({R['checks']['castles_named_equals_norman_castles_study']}). `code/07_results.py` asserts each.

## What it does

- **1086 mode of the Inked World.** Mountains and hills from elevation, coasts with the sea wash and ripples, rivers, hand lettering, clouds and the zoom feel are kept. Roads, railways, buildings, modern place names, modern woods and fields, airports, heritage, ships, balloons and flying machines are removed (`eraStyle` in `js/ink-map.js`, `CFG.era` in `js/ink-worker.js`). Canals, drains and the Fens' later cuts are left out (by class and name, and inside the fens and levels every waterway but the old rivers), as are ponds and lakes; Roman roads are single dashed tracks so nothing reads as a railway. The view is held to Britain.
- **Vills.** Each vill is laid out offline (`code/04_place.py`): one dwelling per household, along today's village streets as a proxy for the old ones (or along a lane or round a green of its own), densest at the centre and kept off the water, its kind following Domesday's classes (villagers' longhouses, cottages, burgesses' houses), with church, hall and market at the core, open fields in ridge and furrow round it (48 ha a plough team), meadow by the stream and wood further out. Walled boroughs ({n('walled_towns')}, among them London, York, Lincoln, Chester, Colchester, Canterbury, Winchester and Exeter) take their wall line from OpenStreetMap's city walls and pack their houses along the streets inside it.
- **Mills, fisheries, salt.** Mills on the nearest stream line (OpenStreetMap at zoom 13), animated wheels; eel weirs on streams or shores; salt-pans on the shore, brine pits at the wiches.
- **Lands.** Plough teams (only in their own vill's fields), flocks, pigs, cattle, goats, cobs, wild mares, beehives and swine at pannage over each vill's own lands (its Voronoi cell within 2.6 km), at stated rates per drawing.
- **Landscape of 1086 (approximate).** Woods from Domesday's measures; the Fens, Somerset Levels, Humberhead Levels, Romney Marsh and Pevensey Levels from low ground; the Wantsum Channel; the New Forest; Roman roads from Itiner-e with the four great highways lettered; shires and {n('hundreds_lettered')} hundreds lettered; the lands beyond the survey washed paler and lettered by hand.
- **Page.** Full-screen button, layers panel (each kind of drawing, land, lettering, modern names and a faint modern map for orientation), search by Domesday or modern name, story buttons (York and the wasted north, the Fens and Ely, Droitwich salt, the New Forest, London and Westminster, around Clitheroe), and an "In 1086 ..." popup for every vill: households by class, plough teams, mills and what they render, church, woodland, livestock, values in 1066 and 1086, holders before and after the Conquest, waste, a quotation from the entry, and links to Open Domesday and the companion studies.

## Files

| File | What it is |
|---|---|
| `index.html` | The page (generated from `code/page_template.html` by `code/08_page.py`). |
| `js/ink-map.js`, `js/ink-worker.js`, `js/ink-icons.js`, `js/ink-palette.js`, `js/ink-clouds.js`, `js/ink-extras.js`, `js/ink-life-art.js`, `js/curated.js` | The Inked World engine, with its 1086 mode. |
| `js/ink-1086.js` | The period drawings: houses, hall, churches, minster, cathedral, abbey, watermill (animated), castles, gate, salt-pans, brine pits, eel weir, vineyard, park, haia, plough team, livestock, vill glyphs. |
| `js/page-1086.js` | The page: vills, layers, search, stories, popups, legend. |
| `data/domesday_places.csv` | Every Domesday place with its figures (Destiny allocation), the drawing columns (`d_*`), text features, holders and flags. CC BY-NC-SA 4.0. |
| `data/town_estimates.csv` | The dwellings drawn for each borough and the Domesday words they rest on. |
| `data/estimates.csv` | Places with estimated dwellings (no usable figure, waste with nobody counted, London and Winchester): the number and the method for each. Not in any recorded total. |
| `data/land/` | Each vill's open fields, meadow, green and lanes on a zoom 9 grid. |
| `data/vills.json`, `data/detail/` | The drawn vills (far-zoom glyphs, names, search) and the popup records by county. |
| `data/dw/`, `data/dww/` | The drawings on a zoom 9 grid (points: lon, lat, sprite, rank, vill) and the woods (rings), read by the map's worker. |
| `data/landscape.geojson`, `data/woods_far.geojson`, `data/roads1086.geojson`, `data/labels1086.geojson`, `data/shires.geojson`, `data/townwalls.geojson` | Marsh, Wantsum, forests, lands not surveyed; woods far out; Roman roads and highway names; shire, hundred and kingdom lettering; approximate shire edges; town walls (OpenStreetMap lines). |
| `data/extras.json` | Castles, religious houses and markets of 1086 matched to places. |
| `data/results.json` | Every number quoted anywhere. |
| `code/` | Numbered scripts (below), QA scripts, the page and paper sources. |
| `release/` | Paper PDF and LaTeX, blog post and figures, Zenodo files. |
| `reddit/` | Collage, `collage.py` and `post.md`. |

## Method in brief

An entry's figures go to the places it describes, shared equally (as in Domesday Destiny); for drawing, an entry naming located outlying members spreads them over head and members (head a double share). One dwelling per household, rounded half up. Where Domesday gives no usable figure, a pale estimate: the place's plough teams, ploughlands, value or hides times the county median households per unit, capped at its hundred's median vill (lower quartile of the hundred if no measure); London and Winchester from the low end of historians' population estimates at 4.5 a household; nothing for lands never surveyed. Mills (fractions rounded half up) on the nearest stream within 1.5 km. Livestock one drawing per 20 sheep, 10 pigs, 5 cattle, 10 goats, 3 cobs or horses, 5 wild mares, 5 beehives, 4 oxen, 50 pigs of pannage, and one per plough team. Woodland: 1 ha a pig, length x breadth x 0.7 for leagues and furlongs, 0.4 ha an acre (drawing conventions). The paper gives every rule.

## Limits

Domesday counts households, not people, and leaves out the north, most of Wales, London and Winchester. Estimated dwellings are conventions, not findings. Today's streets and walls stand in for the plans of 1086. Places sit at the centre of Hull's 1 km squares. Livestock is counted only in Little Domesday and the Exeter Domesday counties. Yorkshire's text is not in the transcription, so York is an estimate and Yorkshire's woods and fisheries are not read. Woods, marsh, walls, shire edges and the positions of mills, weirs and animals are plausible drawing devices, not records. Today's rivers and coasts stand in for 1086's. Travellers are decoration.

## How to rerun

Python 3 (pandas, numpy, scipy, shapely, PyYAML, Pillow, matplotlib), Node 22 with Playwright, `@mapbox/vector-tile`, `pbf`, `undici` and `maplibre-gl@4.7.1` (for renders), xelatex. Raw inputs are read in place (paths in `code/common.py`).

```
python3 code/01_extract.py        # realm-domesday reference YAML to a pickle
python3 code/02_places.py         # entries to places, borough estimates
python3 code/02b_extras.py        # castles, religious houses, markets
python3 code/03_tiles.py && node code/03_ofm_water.js   # water masks and stream lines from OpenFreeMap zoom 13
python3 code/05_landscape.py      # marsh, forests, unsurveyed lands, roads, lettering, shire edges
python3 code/04_place.py          # the layout of every vill
python3 code/06_detail.py         # popup records
python3 code/07_results.py        # results.json with checks
python3 code/08_page.py           # index.html
node code/09_renders.js && node code/legend_shot.js release/figs/legend2.png 2 760 2
python3 reddit/collage.py         # collage and header.png
python3 code/10_release.py        # chart, paper, blog, Zenodo, Reddit post
python3 code/11_readme.py         # this file
node code/qa_shots.js qa name=lat,lon,zoom [--phone] [--click]   # QA screenshots, console errors, popups
```

## Sources and licences

- Domesday Book: Hull Domesday Project database and Hull's transcription of the Phillimore translation (Professor J.J.N. Palmer, George Slater and the University of Hull), CC BY-NC-SA, via realm-domesday (https://github.com/embabel-worlds/realm-domesday). Everything derived from it here (`data/domesday_places.csv`, `data/town_estimates.csv`, `data/vills.json`, `data/detail/`, `data/dw/`, `data/dww/`, `data/woods_far.geojson`, `data/townwalls.geojson`, `data/labels1086.geojson`, `data/shires.geojson`, `data/extras.json`, `data/landscape.geojson`, `data/results.json`) is CC BY-NC-SA 4.0: non-commercial use, with attribution, under the same licence.
- Companion studies: Domesday Destiny, Domesday mills, the Harrying of the North, Norman castles (castles named in Domesday; castles dated by 1086 from Wikidata, CC0), Lost villages.
- English Monastic Archives database (UCL) and the Gazetteer of Markets and Fairs in England and Wales to 1516 (Centre for Metropolitan History), via the Mind Your Manors data set.
- Roman roads: Itiner-e (de Soto et al. 2025), CC BY 4.0.
- OpenStreetMap contributors via OpenFreeMap (OpenMapTiles schema), ODbL 1.0: read live by the page; water areas and stream lines used offline only to place drawings (no tile data in the repository).
- AWS Terrain Tiles (Terrarium); RESOLVE Ecoregions 2017 (CC BY 4.0); Natural Earth (public domain).
- Fonts: MedievalSharp, IM Fell (SIL OFL 1.1). MapLibre GL JS (BSD 3-Clause).

Code is MIT. The Domesday-derived data, the popups' text and figures that embed it are CC BY-NC-SA 4.0; other text and figures CC BY 4.0. See `LICENSE`.

The design is my own and every drawing is original; it is not connected with or endorsed by the Tolkien Estate.

## Citation

Hotham, T. (2026) England in 1086, Drawn: Turning Domesday Book's Figures into a Hand-Inked Map of Every Vill. Zenodo. {{https://doi.org/10.5281/zenodo.24045206}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
"""
open(os.path.join(ROOT, 'README.md'), 'w').write(readme)
lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This MIT licence covers the code in code/, js/, reddit/collage.py and the page scripts.

Data derived from Domesday Book (the Hull Domesday Project database, J.J.N. Palmer,
G. Slater and the University of Hull, CC BY-NC-SA): every file in data/ built from it
(domesday_places.csv, town_estimates.csv, estimates.csv, land/, vills.json, detail/, dw/, dww/, woods_far.geojson,
townwalls.geojson, labels1086.geojson, shires.geojson, extras.json, landscape.geojson,
results.json) and the figures and popup text that embed it are licensed under
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/). Attribution: Professor J.J.N. Palmer,
George Slater and the University of Hull; and Tristan Hotham.

Other text and figures: Creative Commons Attribution 4.0 International.

Third-party material: map renders contain OpenStreetMap data (c) OpenStreetMap contributors,
ODbL 1.0; Roman roads from Itiner-e (CC BY 4.0); fonts under the SIL Open Font License 1.1
(fonts/ttf/); the Inked World data files carried over keep their licences (Natural Earth
public domain; RESOLVE Ecoregions CC BY 4.0; Wikidata CC0).
"""
open(os.path.join(ROOT, 'LICENSE'), 'w').write(lic)
print('README and LICENSE written')
