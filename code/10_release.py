"""Step 10. Release: the chart, the paper (xelatex), the blog post and its meta, the Zenodo files and the Reddit post.
Every number comes from data/results.json. Placeholders 10.5281/zenodo.24045206, https://doi.org/10.5281/zenodo.24045206 and https://blog.tristanhotham.com/2026/10/31/domesday-world/ are filled by the publisher."""
import json, os, re, shutil, subprocess, zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from common import ROOT, DATA

R = json.load(open(os.path.join(DATA, 'results.json')))
REL = os.path.join(ROOT, 'release'); FIG = os.path.join(REL, 'figs')
for d in ('paper', 'blog', 'zenodo'): os.makedirs(os.path.join(REL, d), exist_ok=True)
def n(k, dp=0):
    v = R[k]; return f'{v:,.{dp}f}' if isinstance(v, float) else f'{v:,}'
def pc(k): return f"{round(R[k] * 100)}%"
B = {b['name']: b['dwellings'] for b in R['biggest']}
SLUG = 'domesday-world'; PAGE = 'https://maps.tristanhotham.com/domesday-world/'; REPO = 'https://github.com/Tristan-Hotham/domesday-world'
AI = 'I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.'
TITLE = 'England in 1086, drawn: every Domesday vill on a hand-inked map'

# ---------------------------------------------------------------- a chart: how small the vills were
d = pd.read_csv(os.path.join(DATA, 'domesday_places.csv'), low_memory=False)
hh = pd.to_numeric(d.households, errors='coerce'); hh = hh[hh > 0]
bins = [0, 5, 10, 15, 20, 30, 40, 60, 100, 200, 5000]; lab = ['under 5', '5 to 9', '10 to 14', '15 to 19', '20 to 29', '30 to 39', '40 to 59', '60 to 99', '100 to 199', '200 or more']
cnt = pd.cut(hh, bins, right=False, labels=lab).value_counts().reindex(lab)
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=200)
fig.patch.set_facecolor('#F6EED8'); ax.set_facecolor('#F6EED8')
ax.bar(range(len(lab)), cnt.values, color='#A3261B', width=0.72)
ax.set_xticks(range(len(lab))); ax.set_xticklabels(lab, rotation=0, fontsize=8.5, color='#2B2119')
for s in ('top', 'right'): ax.spines[s].set_visible(False)
ax.spines['left'].set_color('#6E604E'); ax.spines['bottom'].set_color('#6E604E'); ax.tick_params(colors='#6E604E')
ax.set_ylabel('places', color='#2B2119'); ax.set_xlabel('households counted in 1086', color='#2B2119')
ax.set_title('Most vills of 1086 were small', loc='left', fontsize=13, color='#2B2119', fontweight='bold')
for i, v in enumerate(cnt.values): ax.text(i, v + 25, f'{v:,}', ha='center', fontsize=8, color='#2B2119')
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'b_sizes.png'), facecolor=fig.get_facecolor()); plt.close(fig)
R_chart = {lab[i]: int(cnt.values[i]) for i in range(len(lab))}

# ---------------------------------------------------------------- the paper
TOWNS = pd.read_csv(os.path.join(DATA, 'town_estimates.csv'))
def tex(s): return s.replace('&', '\\&').replace('%', '\\%').replace('#', '\\#').replace('_', '\\_').replace('£', '\\pounds{}').replace('"', "''")
top_rows = '\n'.join(f"{tex(b['name'].replace('[', '').replace(']', ''))} & {tex(b['county'])} & {b['dwellings']:,} \\\\" for b in R['biggest'][:10])
glyph_rows = r"""
Dwelling (longhouse, cottage, burgess's house) & one per household counted, rounded half up; the kind follows the classes the entry counts & every vill \\
Empty or wasted dwelling & the borough's own count of waste or empty houses & 73 boroughs \\
Lord's hall & three households or more, and demesne ploughs or a value of \pounds 2 or more & rural vills \\
Church; stone church; minster; cathedral & an entry mentions a church; 40 or more dwellings or a borough; canons, monks or a minster named; the see of 1086 & every vill \\
Watermill & one per mill, fractions rounded half up, on the nearest stream or river within 1.5 km & every vill \\
Fishery (eel weir) & a fishery or eels recorded; nearest stream within 2 km, or shore within 3 km & non-Yorkshire text and fields \\
Salt-pans; brine pits & salt-houses recorded, one hearth per three; nearest shore within 6 km, or the inland wiches & every vill \\
Vineyard; park; hedged enclosure & named in the text & non-Yorkshire text \\
Plough team & one per team (eight oxen) & every vill \\
Sheep; pigs; cattle; goats & one per 20; 10; 5; 10 & where counted \\
Cobs and horses; wild mares; beehives; oxen & one per 3; 5; 5; 4 & where counted \\
Swine at pannage & one per 50 pigs of woodland & where woodland is measured in pigs \\
Woodland & 1 ha a pig; length $\times$ breadth $\times$ 0.7; 0.4 ha an acre & where woodland is measured \\
Castle & named in Domesday, or dated to 1086 or before (marked) & 41 named \\
Religious house & founded by 1086 in the English Monastic Archives & 103 \\
Market & recorded in Domesday or by 1086 in the Gazetteer & every vill \\
Town wall & the line of the city walls in OpenStreetMap (Roman and medieval) within 1.5 km of a borough & 34 towns \\
Estimated dwelling (pale, dotted) & no usable household figure: see Section~\ref{sec:est}; not in any total & @est_blank_vills@ vills \\
Estimated empty dwelling (pale, roofless) & a waste vill with nobody counted: see Section~\ref{sec:est} & @est_waste_vills@ vills \\
Open fields; meadow & ridge and furrow round the village, 48 ha a plough team; Domesday's meadow acres by the stream & every vill \\"""
glyph_rows = glyph_rows.replace('73 boroughs', f"{R['town_estimates']} boroughs").replace('34 towns', f"{R['walled_towns']} towns").replace('& 103 \\\\', f"& {R['abbeys_drawn']} \\\\")
paper = r"""\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}
\setmainfont{TeX Gyre Pagella}
\newfontfamily\headfont{Inter}[UprightFont=*-ExtraBold,BoldFont=*-ExtraBold,Extension=.otf,Path=/usr/share/fonts/opentype/inter/]
\usepackage[a4paper,margin=2.3cm]{geometry}
\usepackage{graphicx,booktabs,float,caption,array,xcolor,longtable}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{setspace}
\setstretch{1.05}
\setlength{\parindent}{0pt}\setlength{\parskip}{0.55em}
\titleformat{\section}{\headfont\Large}{\thesection}{0.8em}{}
\titleformat{\subsection}{\headfont\large}{\thesubsection}{0.8em}{}
\captionsetup{font=small,labelfont=bf}
\urlstyle{same}
\hypersetup{pdftitle={England in 1086, drawn},pdfauthor={Tristan Hotham}}
\begin{document}
\begin{center}
{\Large\bfseries England in 1086, Drawn\par}
\vspace{0.4em}
{\large Turning Domesday Book's figures into a hand-inked map of every vill\par}
\vspace{1.2em}
{\large Tristan Hotham\par}
\vspace{0.3em}
{\small Independent researcher\\ ORCID: 0000-0003-4931-9349\\ DOI: \href{https://doi.org/10.5281/zenodo.24045206}{10.5281/zenodo.24045206}\par}
\vspace{0.8em}
2026
\end{center}
\begin{quote}\small
\begin{center}\textbf{Abstract}\end{center}
Domesday Book records, for most of England in 1086, how many households each vill had, its plough teams, mills, churches, woodland, fisheries, salt-pans and, in some counties, its livestock. I draw those records as a zoomable map in the style of a hand-inked fantasy map, in which nothing modern appears and every mark stands for something the survey counted. Using the Hull Domesday Project's coded database, I place one dwelling for each of the @households_total@ households counted (@dwellings_drawn@ at the @places_located@ located places), one water wheel for each mill on the nearest stream (@mills_drawn@ drawn), @plough_teams_drawn@ plough teams of eight oxen and @animals_drawn@ drawings of flocks, herds and hives over each vill's lands, and woods where the survey measures woodland. The boroughs are drawn from the houses each borough entry counts, including the empty and destroyed ones. This methods note sets out how each glyph is derived, the thresholds and conventions used, and what Domesday does not record. The map shows how sparsely England was settled: the median vill counted @median_households@ households, @share_vills_under_25_households_pc@ had fewer than 25, and only @vills_100_plus_dwellings@ are drawn with a hundred dwellings or more.

\textbf{Keywords:} Domesday Book; 1086; historical GIS; settlement; mills; cartography; fantasy map; visualisation
\end{quote}

\section{Introduction}
Domesday Book is the most complete account of a medieval kingdom that survives. In 1086 the King's commissioners asked, of every manor, who held it in 1066 and who held it now, how many hides it paid tax on, how many ploughs and people it had, its mills, meadow, woodland, pasture, fisheries and salt-pans, and what it was worth then and now \citep{darby}. Historians have long turned those answers into maps of densities and distributions. This study does something more literal: it draws each vill as the survey describes it, on a map in the manner of the inked maps in the front of fantasy novels, so that a reader can zoom from the whole kingdom to a single village and see what Domesday says was there.

The map is built on my earlier Inked World engine \citep{inkmap}, which draws mountains from elevation, coasts, rivers and lettering in one hand-drawn style. For 1086 every modern layer is removed and replaced with drawings derived from Domesday. The page is at \url{@PAGE@}. This note documents the rules behind each mark so that the picture can be read critically: what is counted, what is estimated and what is decoration.

\section{Data}
\textbf{Domesday.} The Hull Domesday Project's coded database of Great Domesday and its transcription of the Phillimore translation (Professor J.J.N. Palmer, George Slater and the University of Hull), as packaged entry by entry in the realm-domesday repository \citep{realm}. It holds @entries_total@ entries, of which @entries_describing@ describe a place, and @places_total@ places, of which @places_located@ are located to a 1 km grid square. Little Domesday (Essex, Norfolk and Suffolk) is parsed from the translation. Each entry carries households by class, plough teams, ploughlands, mills, meadow, woodland measured in pigs, fisheries, salt-houses, livestock, values in 1066 and 1086, a church, castle, market or waste flag, and the people who held it before and after the Conquest. Hull's transcription omits Yorkshire's text, so its coded figures are used but nothing is read from its words. The data are licensed CC BY-NC-SA, and so are the files derived from them here.

\textbf{Companion studies.} The allocation of figures follows my Domesday Destiny study \citep{destiny}; mill totals agree with the Domesday mills study \citep{mills}, waste entries with the Harrying of the North study \citep{harrying} and the castles named with the Norman castles study \citep{castles}.

\textbf{Other sources.} Religious houses founded by 1086 come from the English Monastic Archives database (UCL) and markets recorded by 1086 from the Gazetteer of Markets and Fairs in England and Wales to 1516 \citep{markets}, both from the Mind Your Manors data set; Roman roads from Itiner-e \citep{itinere}; castles dated to 1086 or before but not named in Domesday from Wikidata through the Norman castles study. Water areas and stream lines come from OpenStreetMap through OpenFreeMap's vector tiles \citep{osm}, used only to keep drawings off the water and to place mills; elevation from the AWS Terrain Tiles \citep{terrain}.

\section{Methods}
\subsection{From entries to vills}
An entry's figures are given to the places it describes, shared equally when it describes several \citep{destiny}; this gives @households_total@ households, the same total as the companion study. For the drawing only, an entry that also names located dependent members (outliers or sokeland) spreads its households and resources over the head and the members, the head taking a double share, so that a great manor such as Leominster is not drawn as one town of several hundred houses. Members that are boroughs take no share of a rural manor's people (an entry that owns houses in London does not move its villagers there), and salt-houses held in the inland wiches are moved to the wich.

\subsection{Dwellings}
Domesday counts heads of household: villagers, smallholders, cottagers, slaves, freemen and free men, priests, burgesses and others. A household is roughly a family, so each is drawn as one dwelling, rounded half up. Each vill is given a simple plan. Plots are laid every 80 m (105 m in a hamlet of fewer than six, 55 m or less in a borough) along both sides of the streets and lanes of today's OpenStreetMap within 650 m of the vill's point (1.6 km in a borough), used as a proxy for the old village street, and filled nearest the centre first, so the core is dense and the edges thin; only plots nearer to this vill than to any other are used. Where today's lanes give too few plots, the vill gets a lane of its own through its centre (a cross lane in vills of more than 40 households) or, in a share of vills of 8 to 40 households, a green with houses round it (@plans_streets@ vills on streets, @plans_lane@ on a lane of their own, @plans_green@ round a green). The church and the lord's hall stand at the core. Each plot is tested against the water areas of OpenStreetMap at zoom 13 (256 pixels to a tile, about 19 m); @dwellings_not_placed@ dwellings could not be placed. The drawing of each follows the classes counted: longhouses for villagers and freemen, cottages for smallholders, cottagers, slaves and priests, town houses for burgesses. The map thins them with the zoom in proportion: one drawing per household from zoom 12, one for every two at zoom 11, and further out a single glyph per vill with one to six huts by its size (under 5, 5 to 9, 10 to 19, 20 to 39, 40 to 79 and 80 or more households).

\subsection{Boroughs}
Domesday describes the boroughs in their own terms: houses, messuages, sites and burgesses, with counts before 1066 and in 1086 and of houses empty or destroyed. For @town_estimates@ boroughs I take the dwellings from those counts, by hand for the largest and as the sum of the 1086 counts for the rest, and draw the empty and destroyed ones roofless (@waste_dwellings_drawn@ in all). Table~\ref{tab:towns} lists the largest. Lincoln, for example, had ``970 inhabited messuages before 1066'', of which ``166 were destroyed because of the castle'' and ``760 are now inhabited''. York's text is not in the transcription, so it is drawn from an estimate of 540 inhabited and 540 empty dwellings, and the popup says so. London and Winchester were left out of the survey; their houses are estimated (Section~\ref{sec:est}). Where OpenStreetMap maps a city wall within 1.5 km of a borough (the Roman walls of London, York, Lincoln, Chester, Colchester, Canterbury, Winchester and Exeter, and later medieval circuits that mostly follow them), that wall is drawn and its outline becomes the walled core: houses fill the streets inside it first, densest at the centre, before spilling along the roads outside (@walled_towns@ boroughs). The walls are those mapped today, so some stretches are later than 1086.

\subsection{Estimates for places without a usable figure}\label{sec:est}
Some places Domesday names give no usable household figure: an entry with land, ploughs or a value but no people, a vill called waste with nobody counted, and the two great towns left out of the survey. Drawn literally they would be empty. They are instead given estimated dwellings, drawn visibly paler (dotted outlines; roofless for waste), flagged in the popup with the method, listed in \texttt{data/estimates.csv}, and kept out of every recorded total in this paper. The method is deliberately conservative. For a place with no households, the first available of its plough teams, ploughlands, value in 1086, value in 1066 and hides or carucates is multiplied by the county median of households per unit of that measure among vills with both (all England where a county has fewer than ten); for a waste vill, only measures that describe it before or apart from its wasting (value in 1066, ploughlands, hides or carucates). The result is capped at the median households of the vills of its hundred (@est_capped@ capped), with at least one dwelling. Where no measure is given, the lower quartile of the hundred's vills is used (@est_by_quartile@ places; @est_by_ratio@ by a ratio). For London and Winchester I take the low end of historians' estimates of their people around 1100, about @est_london_people@ for London \cite{brooke,keene} and @est_winchester_people@ for Winchester \cite{biddle}, at @est_people_per_household@ people a household (Darby used 4 to 5), giving @est_london@ and @est_winchester@ dwellings. In all @est_dwellings@ dwellings are estimated at @est_vills@ places: @est_blank_dwellings@ at @est_blank_vills@ places with no usable figure, @est_waste_dwellings@ empty ones at @est_waste_vills@ waste vills, and @est_unsurveyed_dwellings@ in the two towns. Nothing is estimated for lands the survey did not cover.

\begin{table}[H]\centering\small
\caption{The largest places as drawn (dwellings, including borough estimates).}\label{tab:towns}
\begin{tabular}{llr}\toprule Place & County & Dwellings drawn \\ \midrule
@TOP@
\bottomrule\end{tabular}\end{table}

\subsection{What each glyph means}
Table~\ref{tab:glyphs} lists every drawing and the rule behind it. Two principles hold throughout: a glyph stands for something the survey records at that vill, and the number of glyphs follows the number recorded, at a stated rate where one drawing per item would be unreadable.

\begin{table}[H]\centering\footnotesize
\caption{The glyphs and their rules.}\label{tab:glyphs}
\begin{tabular}{p{4.2cm}p{7.8cm}p{2.6cm}}\toprule Glyph & Rule & Coverage \\ \midrule
@GLYPHS@
\bottomrule\end{tabular}\end{table}

\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{legend2.png}\caption{The period drawings, in the Inked World's pen.}\end{figure}

\subsection{Mills and water}
No source says where on its land each mill stood, but a watermill needs moving water. Each mill is therefore set on the nearest stream or river line in today's OpenStreetMap within 1.5 km of its vill, at points 110 m apart along the water, with the mill house on the village side of the wheel. Domesday counts @mills_on_places@ mills at located places, with many halves and thirds shared between manors; rounding each place's total half up gives @mills_rounded@, of which @mills_drawn@ (@mills_drawn_share_pc@) have a stream within 1.5 km and are drawn. The other @mills_no_stream@ are listed in the popup but not drawn: a mill on dry land would be a worse error than a missing wheel. Fisheries go on the nearest stream within 2 km or the nearest shore within 3 km; coastal salt-pans on the nearest shore within 6 km; the brine pits and hearths of Droitwich and the Cheshire wiches round the town itself.

\subsection{The vill's lands}
Round the houses lie the open fields, drawn as ridge and furrow in two or three great fields with the strips running different ways, at 48 ha (about 120 acres) a plough team (half the ploughlands where no teams are counted), up to 60\% of the vill's land: @field_ha_drawn@ ha in all. Meadow is laid by the nearest stream at 0.4 ha a Domesday acre (@meadow_ha_drawn@ ha), and woodland further out. Plough teams are drawn only in their own vill's fields, or within 700 m of its houses where no field is drawn. Flocks and herds are scattered over the vill's own lands: points nearer to it than to any other located vill (a Voronoi cell), within 2.6 km, dry, outside the drawn houses and at least 60 m apart. Flocks and wild mares furthest out, pigs, cattle and hives at the village edge, swine at pannage inside the woods. The rates are one drawing per plough team, per 20 sheep, 10 pigs, 5 cattle, 10 goats, 3 cobs or horses, 5 wild mares, 5 beehives and 4 oxen counted apart from the teams, and at least one where any are recorded. Domesday counts livestock almost only in Little Domesday and the Exeter Domesday counties; elsewhere the absence of flocks is an absence of counting.

\subsection{Woodland, marsh and the lands beyond}
Domesday measures woodland in pigs (the swine it could feed), in leagues and furlongs, or in acres. These measures do not convert reliably to area \citep{darby}, so I use drawing conventions: one hectare a pig; length times breadth times 0.7 for linear measures (a league taken as 12 furlongs, about 2.4 km; one dimension alone as a strip a quarter as wide); 0.4 ha an acre; and 10 ha where woodland is named without a measure. The wood is laid on a 150 m grid on the far side of the vill's lands, up to 70\% of them. The marshes are drawn where the ground lies below a set height inside five basins on today's elevation (Terrarium tiles at zoom 8): the Fens (3.5 m), the Somerset Levels (7 m), the Humberhead Levels (5 m), Romney Marsh and the Pevensey Levels (4 m). The Wantsum Channel, which made Thanet an island, is drawn by hand; the New Forest's outline joins the @new_forest_places@ vills the Hampshire folios list in it. Britain more than about 15 km from any located vill and joined to the north, Wales or Man is washed paler and lettered as not surveyed: @unsurveyed_share_gb_pc@ of Great Britain and @unsurveyed_share_england_pc@ of today's England.

\subsection{Removing the modern}
The engine's modern layers are removed: roads, railways, buildings, modern names, modern woods and fields, airports, heritage, ships and flying machines. Canals and drains, the straight cuts of the Fens by their names, and inside the fens and levels every waterway except the old rivers by name (so the Nene's straight channel below Peterborough, the Bedford rivers and the Dutch River go) are left out. Roman roads are drawn as single dashed tracks, so they cannot be mistaken for railways. Ponds and lakes are left out entirely, since in lowland England nearly all are modern pits, ponds and reservoirs and the tiles cannot tell them from the few natural meres. Coasts, rivers and relief remain those of today. Roman roads, still the country's main roads in 1086, come from Itiner-e, and the four great highways are lettered along approximate lines. Shire edges are approximate (the Voronoi cells of each shire's vills) and @hundreds_lettered@ hundreds and wapentakes are lettered at the median of their vills.

\section{Results}
The map draws @dwellings_drawn@ dwellings at @vills_drawn@ vills (Figure~\ref{fig:eng}). Settlement was thin: @share_vills_under_10_households_pc@ of vills with people counted fewer than ten households and the median counted @median_households@ (Figure~\ref{fig:sizes}). The largest places as drawn are Norwich (@B_Norwich@ dwellings), Lincoln (@B_Lincoln@), Thetford (@B_Thetford@) and York (@B_York@, an estimate), and several great manors whose households were spread over many hamlets (Table~\ref{tab:towns}).

\begin{figure}[H]\centering\includegraphics[width=0.78\textwidth]{b_england.png}\caption{England in 1086 at the scale of the kingdom: a glyph per vill, sized to its households, with Domesday's woods, the marshes and the Roman roads.}\label{fig:eng}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.85\textwidth]{b_sizes.png}\caption{Places by the households Domesday counts.}\label{fig:sizes}\end{figure}

The working countryside dominates once one zooms in: @plough_teams_drawn@ plough teams (Domesday counts @plough_teams@, so about @oxen_in_teams@ oxen), @mills_drawn@ mills turning on their streams (Figure~\ref{fig:mills}), @churches_drawn@ churches, @fisheries_drawn@ eel weirs and @salt_hearths_drawn@ salt hearths. Churches are recorded at @share_vills_with_church_pc@ of vills with people and mills at @share_vills_with_mill_pc@. Livestock are drawn where counted, which is mostly East Anglia and the south-west: Little Domesday holds @sheep_share_little_domesday_pc@ of the @stock_sheep@ sheep the survey records (Figure~\ref{fig:suffolk}). Woodland is drawn over about @woodland_km2_drawn@ square kilometres.

\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{b_mills.png}\caption{Alresford, Hampshire: mills set on the River Alre, the village's houses one per household.}\label{fig:mills}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{b_suffolk.png}\caption{Desning, Suffolk: a large vill with five mills, plough teams, flocks and herds over its lands.}\label{fig:suffolk}\end{figure}

The towns carry the scars of the Conquest (Figure~\ref{fig:york}). @waste_entries@ entries call land waste, @waste_entries_yorkshire@ of them in Yorkshire, after the Harrying of the North of 1069 to 1070; @waste_vills_empty_drawn@ vills with nobody counted are drawn as burnt and roofless huddles.

\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{b_york.png}\caption{York, drawn from an estimate of 540 inhabited and 540 empty dwellings, packed along its streets inside the line of its walls, with minster, castle and abbey.}\label{fig:york}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=0.92\textwidth]{b_fens.png}\caption{The Fens and Ely: marsh drawn from low ground, vills on the fen islands and edges.}\end{figure}

\section{Limitations}
Domesday counts households, not people, and omits many: lords' households, many priests, and townsfolk not liable to dues. It also leaves out the north beyond the Tees and the Ribble, most of Wales, London and Winchester. Hull located @places_located@ of @places_total@ places, each at the centre of a 1 km square. The allocation shares an entry's figures equally among the places it describes, and the drawing spreads them over named members; both are conventions. The borough estimates rest on Domesday's own counts but those counts mix houses, messuages and burgesses. The estimated dwellings (Section~\ref{sec:est}) are conventions to avoid drawing named places empty, not findings. Today's streets and walls stand in for the plans of 1086. Woodland, marsh, the town walls, the shire edges and the New Forest are approximate drawing devices; the mill, fishery and salt positions are plausible, not known. Today's rivers and coasts stand in for those of 1086, and some Fen channels and lakes are later. Travellers on the roads are decoration. The map is a picture of the record, to be read with its popups, not a reconstruction of the landscape.

\section{Data availability}
The map, code and data are at \url{@REPO@} and archived with this paper at \href{https://doi.org/10.5281/zenodo.24045206}{10.5281/zenodo.24045206}. Code is MIT; the files derived from the Hull Domesday data are CC BY-NC-SA 4.0; other text and figures CC BY 4.0. Map renders contain OpenStreetMap data (ODbL).

\section*{AI assistance}
@AI@

\begin{thebibliography}{99}
\bibitem[Biddle(1976)]{biddle} Biddle, M. (ed.) (1976) \emph{Winchester in the Early Middle Ages: an edition and discussion of the Winton Domesday}. Winchester Studies 1. Oxford: Clarendon Press.
\bibitem[Brooke and Keir(1975)]{brooke} Brooke, C. N. L. and Keir, G. (1975) \emph{London 800 to 1216: the shaping of a city}. London: Secker and Warburg.
\bibitem[Keene(2000)]{keene} Keene, D. (2000) London from the post-Roman period to 1300. In D. M. Palliser (ed.) \emph{The Cambridge Urban History of Britain, vol. 1}. Cambridge: Cambridge University Press.
\bibitem[Darby(1977)]{darby} Darby, H. C. (1977) \emph{Domesday England}. Cambridge: Cambridge University Press.
\bibitem[Palmer et al.]{hull} Palmer, J. J. N., Slater, G. and the University of Hull. Hull Domesday Project database and Domesday Explorer. \url{https://digitalcollections.hull.ac.uk/collections/3t945r28b} (CC BY-NC-SA).
\bibitem[Embabel Worlds(2026)]{realm} realm-domesday: Domesday Book as a graph. \url{https://github.com/embabel-worlds/realm-domesday}.
\bibitem[Hotham(2026a)]{inkmap} Hotham, T. (2026) The Inked World. Zenodo. \url{https://doi.org/10.5281/zenodo.23860253}.
\bibitem[Hotham(2026b)]{destiny} Hotham, T. (2026) Domesday Destiny. \url{https://maps.tristanhotham.com/domesday-destiny/}.
\bibitem[Hotham(2026c)]{mills} Hotham, T. (2026) Domesday mills. \url{https://maps.tristanhotham.com/domesday-mills/}.
\bibitem[Hotham(2026d)]{harrying} Hotham, T. (2026) The Harrying of the North. \url{https://maps.tristanhotham.com/harrying-of-the-north/}.
\bibitem[Hotham(2026e)]{castles} Hotham, T. (2026) Norman castles. \url{https://maps.tristanhotham.com/norman-castles/}.
\bibitem[Letters et al.]{markets} Letters, S. et al. Gazetteer of Markets and Fairs in England and Wales to 1516. Centre for Metropolitan History; and the English Monastic Archives database, UCL; via the Mind Your Manors data set.
\bibitem[de Soto et al.(2025)]{itinere} de Soto, P. et al. (2025) Itiner-e: the digital atlas of ancient roads. CC BY 4.0.
\bibitem[OpenStreetMap]{osm} OpenStreetMap contributors, via OpenFreeMap (OpenMapTiles schema). ODbL 1.0.
\bibitem[Mapzen]{terrain} AWS Terrain Tiles (Terrarium). \url{https://registry.opendata.aws/terrain-tiles/}.
\end{thebibliography}
\end{document}
"""
def fill(t):
    t = t.replace('@TOP@', top_rows).replace('@GLYPHS@', glyph_rows).replace('@PAGE@', PAGE).replace('@REPO@', REPO).replace('@AI@', AI)
    for k in ['Norwich', 'Lincoln', 'Thetford', 'York']: t = t.replace('@B_' + k + '@', f'{B[k]:,}')
    def rep(m):
        k = m.group(1)
        if k.endswith('_pc'): return f"{round(R[k[:-3]] * 1000) / 10:g}\\%"
        return n(k, 0 if isinstance(R[k], int) or float(R[k]).is_integer() else 1)
    return re.sub(r'@([a-z0-9_]+)@', rep, t)
paper = fill(paper).replace('\\citep{', '\\cite{')
pdir = os.path.join(REL, 'paper')
for f in ['legend2.png', 'b_england.png', 'b_sizes.png', 'b_mills.png', 'b_suffolk.png', 'b_york.png', 'b_fens.png']:
    im = Image.open(os.path.join(FIG, f)).convert('RGB'); im.thumbnail((1600, 1600))
    if f.startswith('b_') and f != 'b_sizes.png': im.save(os.path.join(pdir, f.replace('.png', '.jpg')), quality=86, optimize=True)
    else: im.save(os.path.join(pdir, f), optimize=True)
for f in os.listdir(pdir):
    if f.startswith('b_') and f.endswith('.png') and f != 'b_sizes.png': os.remove(os.path.join(pdir, f))
paper = re.sub(r'\{(b_(?:england|mills|suffolk|york|fens))\.png\}', r'{\1.jpg}', paper)
tp = os.path.join(pdir, 'England_in_1086_drawn.tex')
open(tp, 'w').write(paper.replace('https://doi.org/10.5281/zenodo.24045206', 'https://doi.org/10.5281/zenodo.24045206'))
for _ in range(2):
    rr = subprocess.run(['xelatex', '-interaction=nonstopmode', os.path.basename(tp)], cwd=pdir, capture_output=True, text=True)
pdf = tp.replace('.tex', '.pdf')
print('paper', os.path.exists(pdf), rr.stdout[-400:] if not os.path.exists(pdf) else '')
pages = int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
print('pages', pages)
for f in os.listdir(pdir):
    if f.endswith(('.aux', '.log', '.out')): os.remove(os.path.join(pdir, f))

# ---------------------------------------------------------------- blog
bdir = os.path.join(REL, 'blog')
for f in ['b_england.png', 'b_york.png', 'b_mills.png', 'b_suffolk.png', 'b_fens.png', 'b_droitwich.png', 'b_waste.png', 'b_sizes.png']:
    im = Image.open(os.path.join(FIG, f)).convert('RGB'); im.thumbnail((1600, 1600)); im.save(os.path.join(bdir, f), optimize=True)
    if os.path.getsize(os.path.join(bdir, f)) > 1500000: im.quantize(256, method=Image.Quantize.FASTOCTREE).save(os.path.join(bdir, f), optimize=True)
P = lambda t: f'<!-- wp:paragraph -->\n<p>{t}</p>\n<!-- /wp:paragraph -->\n'
H = lambda t: f'<!-- wp:heading -->\n<h2 class="wp-block-heading">{t}</h2>\n<!-- /wp:heading -->\n'
IMG = lambda f, a, c: f'{{{{IMG|{f}|{a}|{c}}}}}\n'
BTN = lambda pairs: '<!-- wp:buttons -->\n<div class="wp-block-buttons">' + ''.join(f'<!-- wp:button -->\n<div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="{u}">{t}</a></div>\n<!-- /wp:button -->' for t, u in pairs) + '</div>\n<!-- /wp:buttons -->\n'
blog = ''.join([
    '<!-- wp:paragraph -->\n<p><em>What if the map in the front of a fantasy novel were real, and every village on it came from Domesday Book? I drew England in 1086 that way: one little house for every household the survey counted, a water wheel for every mill, a plough team for every team of oxen.</em></p>\n<!-- /wp:paragraph -->\n',
    BTN([('Explore the interactive version', PAGE), ('Read the paper', 'https://doi.org/10.5281/zenodo.24045206')]),
    P(f"In 1086 William the Conqueror's commissioners rode round England asking the same questions of every vill: who held it, how many people and ploughs it had, its mills, meadow and woodland, and what it was worth. The answers became Domesday Book. Hull's Domesday Project turned them into a database, and it is extraordinarily detailed: {n('entries_total')} entries, {n('places_total')} places, {n('households_total', 0)} households."),
    P("I have spent a while making a map engine that draws the real world like a hand-inked fantasy map, with little mountains, rippled coasts and red lettering. For this map I took everything modern out of it and drew Domesday back in. There are no roads but the Roman ones, no names but Domesday's, and nothing on the land that the survey does not record."),
    IMG('b_england.png', 'Hand-inked map of England in 1086: small glyphs of huts for each Domesday vill scattered across the country, woods in green, the Fens as marsh, Roman roads as faint tracks and shires lettered in red', 'England in 1086, each vill a few huts sized to its households.'),
    H('One house for every household'),
    P(f"Zoom in and every vill fills with houses: one for each household Domesday counts, so {n('dwellings_drawn')} in all. Villagers get longhouses, smallholders and cottagers small cottages, burgesses town houses. The lord's hall sits in its fenced court, the church at the centre if the entry mentions one. A hamlet of three households is three huts. That is the point: most vills were tiny. The median counted {n('median_households')} households and {pc('share_vills_under_10_households')} had fewer than ten."),
    IMG('b_sizes.png', 'Bar chart of places by number of households in 1086, most between 5 and 30 households, very few above 100', 'Most vills counted fewer than 25 households.'),
    H('Towns, and the empty houses'),
    P(f"The towns are where Domesday turns dramatic. It counts their houses in its own way, often with the empty ones. Lincoln had \"970 inhabited messuages before 1066\"; \"166 were destroyed because of the castle\" and \"760 are now inhabited\". Oxford had \"243 houses which pay tax\" and \"500 houses less 22 so derelict and destroyed that they cannot pay tax\". So the map draws them as Domesday tells it, with the empty houses roofless: {n('waste_dwellings_drawn')} of them across {n('town_estimates')} boroughs."),
    IMG('b_york.png', 'Close view of York in 1086: small thatched houses packed along the streets inside the line of the city walls, the Ouse running through, a minster, castle and abbey, and pale roofless houses among them', 'York, packed inside the line of its walls: many of its houses stood empty in 1086.'),
    H('Filling the gaps, carefully'),
    P(f"Some places Domesday names give no usable figure for people: an entry with ploughs or a value but nobody counted, a vill called waste, and the two great towns the survey left out, London and Winchester. Drawn literally they would be blank, which is not true either. So they get estimated houses, drawn pale with dotted outlines (or pale and roofless in a waste vill), and the popup says how each was worked out. The rule is cautious: the place's ploughs, ploughlands, value or hides times the county's usual households per unit, never more than the typical vill of its hundred. For London and Winchester I took the low end of historians' estimates of their people around 1100, about {n('est_london_people')} and {n('est_winchester_people')}, at 4.5 people a house. In all {n('est_dwellings')} houses at {n('est_vills')} places are estimated, and none of them is counted in any total I quote."),
    '<!-- wp:pullquote -->\n<figure class="wp-block-pullquote"><blockquote><p>A hamlet of three households is three huts. A village of sixty with a church and two mills is sixty houses, a church and two wheels on the stream.</p></blockquote></figure>\n<!-- /wp:pullquote -->\n',
    H('Mills on their streams'),
    P(f"Domesday records about six thousand mills, often in halves and thirds shared between manors. Each one gets a timber mill house with a big undershot wheel, set on the nearest stream or river to its vill, and the wheels turn when you are close in. Where today's map has no stream within 1.5 km I would rather leave a mill out than put it on dry land, so {n('mills_drawn')} of {n('mills_rounded')} are drawn."),
    IMG('b_mills.png', 'Close view of Alresford in Hampshire: thatched cottages scattered along the River Alre with several watermills, each a timber house with a large wheel in the stream', 'Alresford: its mills on the River Alre.'),
    H('Ploughs, sheep and pigs'),
    P(f"Around each village lie its lands, and on them what Domesday counts: {n('plough_teams_drawn')} plough teams of eight oxen, flocks of sheep, pigs, cattle, goats, cobs, wild mares and bee skeps, spread over the fields and pasture nearer to that vill than to any other. The catch is honest and interesting: Domesday only counts livestock in a few counties. Little Domesday, for Essex, Norfolk and Suffolk, holds {pc('sheep_share_little_domesday')} of the {n('stock_sheep')} sheep recorded, so East Anglia is full of flocks and the Midlands look empty. They were not; nobody counted them."),
    IMG('b_suffolk.png', 'Close view of Desning in Suffolk: a cluster of houses with a church, five watermills along a stream and many plough teams and small flocks across the surrounding fields', 'Desning, Suffolk: five mills, plough teams and flocks.'),
    IMG('b_droitwich.png', 'Close view of Droitwich: a cluster of houses with brine pits and salt hearths around it', 'Droitwich and its salt.'),
    H('Woods, fens and the waste'),
    P(f"Woodland is drawn where Domesday measures it, in pigs or in leagues, about {n('woodland_km2_drawn')} square kilometres of it. The Fens, the Somerset Levels and the other great marshes are drawn from low ground, and Thanet is an island again. In the north, {n('waste_entries_yorkshire')} Yorkshire entries call land waste after the Harrying of 1069 to 1070, and vills with nobody counted are drawn as burnt huddles."),
    IMG('b_fens.png', 'Medium view of the Fens around Ely: pale marsh with tufts, vills on the higher ground and fen edges, woods and rivers', 'The Fens and Ely.'),
    IMG('b_waste.png', 'View of Yorkshire with red rings marking vills Domesday calls waste, dense across the Vale of York and the uplands', 'Every vill Domesday calls waste, ringed in red.'),
    P("Beyond the survey, the north, Wales and Scotland are washed paler and lettered by hand. People lived there; Domesday just did not count them. Domesday Lancashire, around Clitheroe and the Ribble, is folded into Yorkshire and Cheshire and thinly recorded, and the map shows that honestly."),
    H('How I did this'),
    P("The figures come from the Hull Domesday Project's database (CC BY-NC-SA), entry by entry through the realm-domesday repository, allocated to places as in my Domesday Destiny study so the totals match. Houses are laid out along today's village streets as a stand-in for the old ones (or along a lane or round a green of their own), packed inside the line of the walls in the walled towns, with open fields, meadow and wood around, and kept off the water using OpenStreetMap's water areas; mills are snapped to the nearest stream line. Livestock are drawn at one per 20 sheep, 10 pigs, 5 cattle and so on; woodland and marsh are drawing conventions, explained in the paper. The map itself is my Inked World engine with every modern layer removed. Click anything on the map and the popup says what the entry records and what is estimated."),
    BTN([('Explore the interactive version', PAGE), ('Read the paper', 'https://doi.org/10.5281/zenodo.24045206'), ('Data and code', REPO)]),
    H('Notes and sources'),
    '<!-- wp:list -->\n<ul class="wp-block-list">' + ''.join(f'<!-- wp:list-item -->\n<li>{x}</li>\n<!-- /wp:list-item -->' for x in [
        'Domesday Book: Hull Domesday Project database and transcription of the Phillimore translation (J.J.N. Palmer, G. Slater and the University of Hull), CC BY-NC-SA, via the realm-domesday repository.',
        'Companion studies: Domesday Destiny, Domesday mills, the Harrying of the North, Norman castles and Lost villages, at maps.tristanhotham.com.',
        'Religious houses: English Monastic Archives (UCL); markets: Gazetteer of Markets and Fairs in England and Wales to 1516; both via the Mind Your Manors data set.',
        'Roman roads: Itiner-e (de Soto et al. 2025), CC BY 4.0. Water and rivers: OpenStreetMap contributors via OpenFreeMap (ODbL). Elevation: AWS Terrain Tiles.',
        'Darby, H. C. (1977) Domesday England. Cambridge University Press.',
        'Estimates for London and Winchester: Brooke, C. and Keir, G. (1975) London 800 to 1216; Keene, D. (2000) in the Cambridge Urban History of Britain, vol. 1; Biddle, M. (ed.) (1976) Winchester in the Early Middle Ages.',
        AI]) + '</ul>\n<!-- /wp:list -->\n',
])
open(os.path.join(bdir, 'post.html'), 'w').write(blog)
meta = {'title': 'England in 1086, drawn: every Domesday vill on a hand-inked map', 'slug': SLUG,
        'excerpt': 'A fantasy-novel map of the real England of 1086, where every house, mill, plough team and flock comes from Domesday Book.',
        'seo_description': 'A hand-inked map of England in 1086: one house per Domesday household, every mill on its stream, every plough team and flock.',
        'tags': ['Domesday Book', '1086', 'maps', 'medieval history', 'fantasy maps', 'data visualisation', 'mills'],
        'header_alt': 'Hand-inked map of England in 1086 with small huts for every Domesday vill, red lettering and blue coasts'}
assert len(meta['seo_description']) < 160
json.dump(meta, open(os.path.join(bdir, 'meta.json'), 'w'), indent=1)
words = len(re.sub(r'<[^>]+>|\{\{[^}]+\}\}', ' ', blog).split()); print('blog words', words)

# ---------------------------------------------------------------- Reddit post
post = f"""## Title

[OC] I drew every village in Domesday Book (1086) as a fantasy-novel map: {n('dwellings_drawn')} houses, one per household, and every mill on its stream

## Body

Every vill in Domesday Book, drawn as the survey recorded it: one house for each of the {n('households_total', 0)} households counted, a water wheel for each mill on the nearest stream ({n('mills_drawn')} drawn), {n('plough_teams_drawn')} plough teams of eight oxen, and flocks, churches, castles, salt-pans and eel weirs where the entries list them. Most vills were tiny: the median had {n('median_households')} households. Towns are drawn from Domesday's own house counts, empty houses roofless (Oxford: "500 houses less 22 so derelict and destroyed that they cannot pay tax"). Livestock is only counted in a few counties, so East Anglia is full of sheep and the Midlands look empty. Places Domesday names without a usable figure (blank or waste entries, and London and Winchester, which the survey skipped) get {n('est_dwellings')} pale estimated houses, flagged as such and kept out of every total. Interactive map: {PAGE}

## Source comment

Source: Domesday Book via the Hull Domesday Project database (J.J.N. Palmer, University of Hull; CC BY-NC-SA) and the realm-domesday repository; religious houses (English Monastic Archives, UCL) and markets (Gazetteer of Markets and Fairs to 1516); Roman roads from Itiner-e (CC BY 4.0); water and rivers from OpenStreetMap via OpenFreeMap (ODbL); elevation from AWS Terrain Tiles.

Tools: Python (pandas, shapely, scipy) for the layout; MapLibre GL JS with my own hand-inked map engine (every drawing original).

Interactive version: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24045206}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/domesday-world/}}
"""
os.makedirs(os.path.join(ROOT, 'reddit'), exist_ok=True)
open(os.path.join(ROOT, 'reddit', 'post.md'), 'w').write(post)

# ---------------------------------------------------------------- Zenodo
zdir = os.path.join(REL, 'zenodo')
shutil.copy(pdf, os.path.join(zdir, 'England_in_1086_drawn.pdf'))
zp = os.path.join(zdir, 'domesday-world_code_and_data.zip')
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
    for top in ['code', 'data', 'js']:
        for root, _, files in os.walk(os.path.join(ROOT, top)):
            if '__pycache__' in root: continue
            for f in files: z.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), ROOT))
    for f in ['index.html', 'README.md', 'LICENSE']:
        if os.path.exists(os.path.join(ROOT, f)): z.write(os.path.join(ROOT, f), f)
desc = (f"<p>A zoomable hand-inked map of England in 1086 in which every settlement, mill, church, castle, plough team, flock, woodland, fishery and salt-pan comes from Domesday Book. "
        f"One dwelling is drawn for each of the {n('households_total', 0)} households the survey counts ({n('dwellings_drawn')} at located places), one water wheel for each mill on the nearest stream ({n('mills_drawn')}), "
        f"{n('plough_teams_drawn')} plough teams and {n('animals_drawn')} drawings of livestock over each vill's lands. Boroughs are drawn from Domesday's own house counts, including the empty and destroyed houses, and the walled boroughs inside the line of their walls. "
        f"Places named without a usable household figure, and London and Winchester, get {n('est_dwellings')} conservatively estimated dwellings, drawn pale, documented in data/estimates.csv and kept out of every total. "
        f"This methods note documents every glyph, threshold and convention, and what Domesday does not record.</p><p>Interactive map: <a href=\"{PAGE}\">{PAGE}</a>. Code and data: <a href=\"{REPO}\">{REPO}</a>.</p>"
        f"<p>Licences: code MIT; Domesday-derived data CC BY-NC-SA 4.0 (Hull Domesday Project, University of Hull); other text and figures CC BY 4.0 unless they embed the Domesday data.</p><p>{AI}</p>")
json.dump({'metadata': {'title': 'England in 1086, Drawn: Turning Domesday Book’s Figures into a Hand-Inked Map of Every Vill', 'upload_type': 'publication', 'publication_type': 'workingpaper',
           'description': desc, 'creators': [{'name': 'Hotham, Tristan', 'affiliation': 'Independent researcher', 'orcid': '0000-0003-4931-9349'}],
           'keywords': ['Domesday Book', '1086', 'historical GIS', 'medieval England', 'mills', 'settlement', 'cartography', 'fantasy map', 'visualisation', 'Hull Domesday Project'],
           'license': 'cc-by-nc-sa-4.0', 'language': 'eng', 'publication_date': '2026',
           'related_identifiers': [{'identifier': PAGE, 'relation': 'isSupplementedBy', 'scheme': 'url'}, {'identifier': REPO, 'relation': 'isSupplementedBy', 'scheme': 'url'}]}},
          open(os.path.join(zdir, 'metadata.json'), 'w'), indent=1)
print('zip KB', os.path.getsize(zp) // 1024)
R2 = dict(R); R2['chart_sizes'] = R_chart; R2['paper_pages'] = pages; R2['blog_words'] = words
json.dump(R2, open(os.path.join(DATA, 'results.json'), 'w'), indent=1)
