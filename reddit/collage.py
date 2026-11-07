"""The Reddit collage (light paper background) and the social card header.png, from the renders in release/figs
(code/09_renders.js) and the legend (code/legend_shot.js). Every number from data/results.json.
    python3 reddit/collage.py"""
import json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, 'release', 'figs'); R = json.load(open(os.path.join(ROOT, 'data', 'results.json')))
F = '/home/claude/ref/fonts/'; FT = os.path.join(ROOT, 'fonts', 'ttf')
def font(f, s): return ImageFont.truetype(f, s)
FR = lambda s: font(F + 'FrauncesVar.ttf', s); SS = lambda s: font(F + 'SourceSerif4-Regular.ttf', s); SI = lambda s: font(F + 'SourceSerif4-It.ttf', s)
MONO = lambda s: font(F + 'IBMPlexMono-Regular.ttf', s); HAND = lambda s: font(os.path.join(FT, 'MedievalSharp.ttf'), s); FELL = lambda s: font(os.path.join(FT, 'IMFeENsc28P.ttf'), s)
PAPER, INK, RED, MUTED = (246, 238, 216), (43, 33, 25), (163, 38, 27), (110, 96, 78)
n = lambda k: f"{R[k]:,.0f}" if isinstance(R[k], float) else f"{R[k]:,}"

def framed(im, w):
    im = im.convert('RGB'); h = round(im.height * w / im.width); im = im.resize((w, h), Image.LANCZOS)
    out = Image.new('RGB', (w + 12, h + 12), PAPER); out.paste(im, (6, 6)); d = ImageDraw.Draw(out)
    d.rectangle([2, 2, w + 9, h + 9], outline=INK, width=3); d.rectangle([7, 7, w + 4, h + 4], outline=INK, width=1)
    return out

# ---------------------------------------------------------------- collage
W = 2800
C = Image.new('RGB', (W, 4600), PAPER); D = ImageDraw.Draw(C)
D.text((90, 70), 'England in 1086, drawn', font=FR(118), fill=INK)
D.text((92, 215), f"Every vill in Domesday Book as the survey recorded it: one house for each of the {n('households_total')} households counted,", font=SS(44), fill=INK)
D.text((92, 272), f"a water wheel for every mill on its stream, {n('plough_teams_drawn')} plough teams, flocks, churches and castles where the entries list them.", font=SS(44), fill=INK)
eng = framed(Image.open(os.path.join(FIG, 'c_england.png')), 1500)
C.paste(eng, (80, 380))
D.text((96, 380 + eng.height + 12), 'All England and the Welsh march: a glyph of huts per vill, sized to its households; woods, fens and Roman roads', font=SI(30), fill=MUTED)
ins = [('c_york.png', 'York', 'packed inside the line of its walls; 540 houses and 540 empty (an estimate)'),
       ('c_fens.png', 'The Fens round Ely', 'vills on the fen islands; only the old rivers'),
       ('c_droitwich.png', 'Droitwich', 'brine pits and salt hearths round the wich'),
       ('c_village.png', 'Alresford, Hampshire', 'houses along its lanes, a house per household, mills on the Alre')]
x0, y0, iw = 1640, 380, 520
for i, (f, t, s) in enumerate(ins):
    im = framed(Image.open(os.path.join(FIG, f)), iw)
    x = x0 + (i % 2) * (iw + 50); y = y0 + (i // 2) * (iw + 170)
    D.text((x + 2, y), t, font=FR(40), fill=RED)
    C.paste(im, (x, y + 52))
    yy = y + 52 + im.height + 6
    # caption wrapped to the panel width, on paper
    words, line = s.split(), ''
    for w_ in words:
        if D.textlength(line + ' ' + w_, font=SI(25)) > iw and line: D.text((x + 2, yy), line, font=SI(25), fill=MUTED); yy += 31; line = w_
        else: line = (line + ' ' + w_).strip()
    D.text((x + 2, yy), line, font=SI(25), fill=MUTED)
# what the map shows, in numbers, beside the map under the close-ups
fy = y0 + 2 * (iw + 170) + 20
facts = [f"{n('dwellings_drawn')} houses, one per household", f"{n('mills_drawn')} mills on their streams", f"{n('plough_teams_drawn')} plough teams in their fields",
         f"median vill: {n('median_households')} households", f"{n('waste_dwellings_drawn')} empty town houses drawn roofless",
         f"{n('est_dwellings')} estimated houses drawn pale,", "   kept out of every total"]
D.text((x0, fy), 'In numbers', font=FR(40), fill=INK); fy += 64
for t in facts: D.text((x0, fy), t, font=MONO(30), fill=RED); fy += 44
bottom = max(380 + eng.height + 70, fy + 20)
leg = Image.open(os.path.join(FIG, 'legend4.png')).convert('RGB')
lw = W - 160; leg = leg.resize((lw, round(leg.height * lw / leg.width)), Image.LANCZOS)
D.text((80, bottom), 'Key: what each drawing stands for', font=FR(44), fill=INK)
C.paste(leg, (80, bottom + 66))
bottom = bottom + 66 + leg.height + 40
foot = 'Source: Domesday Book, Hull Domesday Project (J.J.N. Palmer, Univ. of Hull; CC BY-NC-SA) via realm-domesday; Itiner-e; OpenStreetMap (ODbL); AWS Terrain Tiles.'
D.text((90, bottom), foot, font=MONO(23), fill=MUTED)
D.text((90, bottom + 40), 'Dr Tristan Hotham · Independent researcher · 2026 · maps.tristanhotham.com/domesday-world', font=MONO(26), fill=INK)
C = C.crop((0, 0, W, bottom + 100))
C.save(os.path.join(ROOT, 'reddit', 'england_in_1086_drawn.png'), optimize=True)
print('collage', C.size)

# ---------------------------------------------------------------- header.png (1200 x 630)
H = Image.open(os.path.join(FIG, 'header_map.png')).convert('RGB').resize((1200, 630))
d = ImageDraw.Draw(H)
box = (40, 40, 560, 300)
ov = Image.new('RGBA', H.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
od.rectangle(box, fill=(251, 243, 220, 242)); H = Image.alpha_composite(H.convert('RGBA'), ov).convert('RGB'); d = ImageDraw.Draw(H)
d.rectangle(box, outline=INK, width=3); d.rectangle((box[0] + 7, box[1] + 7, box[2] - 7, box[3] - 7), outline=INK, width=1)
d.text((66, 64), 'DATA STUDY  ·  2026', font=MONO(17), fill=MUTED)
d.text((64, 92), 'England in 1086,', font=FR(54), fill=INK)
d.text((66, 152), 'drawn', font=HAND(58), fill=RED)
d.text((66, 226), f"Every Domesday vill: a house per household,", font=SS(21), fill=INK)
d.text((66, 254), f"a wheel for every mill.", font=SS(21), fill=INK)
d.rectangle((30, 588, 850, 620), fill=(251, 243, 220)); d.rectangle((30, 588, 850, 620), outline=INK, width=1)
d.text((40, 596), 'Dr Tristan Hotham · Independent researcher · maps.tristanhotham.com/domesday-world', font=MONO(16), fill=INK)
H.save(os.path.join(ROOT, 'header.png'), optimize=True)
print('header', H.size)
