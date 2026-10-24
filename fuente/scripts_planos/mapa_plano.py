import pickle, sys, json, numpy as np, matplotlib, shapely, pyarrow.parquet as pq
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from pyproj import Transformer
n, x0, x1, y0, y1, salida = sys.argv[1], *map(float, sys.argv[2:6]), sys.argv[6]
capas = sys.argv[7].split(',') if len(sys.argv) > 7 else None
D = pickle.load(open(f'planos/{n}_wcs.pkl', 'rb'))
fig = plt.figure(figsize=(14, 14 * (y1 - y0) / (x1 - x0)), dpi=110); ax = fig.add_axes([0, 0, 1, 1])
COL = {'manzana ok': 'black', 'CONT-MNR': '#c9b79c', 'CONT-MJR': '#a5835a', 'gradas': '#4a90d9', 'SECCION VIAL': 'red', 'Calles': 'blue', 'canales': 'cyan',
       'quebradas': 'teal', 'propuestita': 'magenta', 'Eje': 'orange', 'CARRETERA': 'purple', 'VIA PRINCIPAL': 'red', 'VIA SECUNDARIA': 'orange', 'retiro vial': 'green',
       'puentes': 'brown', 'nuevo rio': 'navy', 'LOSA': 'olive', 'SECCIONES': 'darkred', 'Secciones Viales Nuevas': 'crimson', '0': 'gray', 'Cotas': 'gray', 'COTAS PROPIEDADES': 'darkgreen'}
for capa, L in D.items():
    if capas and capa not in capas: continue
    c = COL.get(capa, '#bbbbbb'); lw = 0.25 if capa.startswith('CONT') else 0.6
    for d in L:
        if 'pts' in d and len(d['pts']) > 1:
            a = np.array(d['pts'])
            if a[:, 0].max() < x0 or a[:, 0].min() > x1 or a[:, 1].max() < y0 or a[:, 1].min() > y1: continue
            ax.plot(a[:, 0], a[:, 1], color=c, lw=lw)
        elif d['t'] in ('TEXT', 'MTEXT') and x0 < d['p'][0] < x1 and y0 < d['p'][1] < y1:
            ax.text(d['p'][0], d['p'][1], d['txt'][:30], fontsize=5, color=c, rotation=d.get('rot', 0) if abs(d.get('rot', 0)) < 360 else 0)
        elif d['t'] == 'DIMENSION' and 'defpoint' in d:
            p = d.get('text_midpoint') or d['defpoint']
            m = d.get('med'); m = f'{m:.2f}' if isinstance(m, (int, float)) else ''
            if x0 < p[0] < x1 and y0 < p[1] < y1: ax.text(p[0], p[1], d['txt'] or m, fontsize=5, color='crimson')
if len(sys.argv) > 8 and sys.argv[8] == 'osm':
    T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
    for r in pq.read_table('data/transportation_segment.parquet').to_pylist():
        g = shapely.from_wkb(r['geometry']); xs, ys = T.transform(*zip(*g.coords))
        ax.plot(xs, ys, color='lime', lw=1.2, alpha=0.7)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off')
plt.savefig(salida)
