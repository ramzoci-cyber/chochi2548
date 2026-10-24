import pickle, sys, numpy as np, matplotlib, random
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
x0, x1, y0, y1, salida = *map(float, sys.argv[1:5]), sys.argv[5]
fuente = sys.argv[6] if len(sys.argv) > 6 else 'plan/manzanas_crudo.pkl'
M = pickle.load(open(fuente, 'rb'))
D = pickle.load(open('planos/plano_total_wcs.pkl', 'rb'))
fig = plt.figure(figsize=(14, 14 * (y1 - y0) / (x1 - x0)), dpi=100); ax = fig.add_axes([0, 0, 1, 1])
rnd = random.Random(1)
for p in M['pols']:
    b = p.bounds
    if b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1: continue
    ax.add_patch(MP(np.array(p.exterior.coords), closed=True, fc=(rnd.random() * 0.4 + 0.55, rnd.random() * 0.4 + 0.55, rnd.random() * 0.4 + 0.55), ec='none'))
capas = sys.argv[7].split(',') if len(sys.argv) > 7 else ['manzana ok']
cols = ['k', 'b', 'g', 'm', 'c', 'orange', 'r']
for ci, capa in enumerate(capas):
    for d in D.get(capa, []):
        if 'pts' in d and len(d['pts']) > 1:
            a = np.array(d['pts'])
            if a[:, 0].max() < x0 or a[:, 0].min() > x1 or a[:, 1].max() < y0 or a[:, 1].min() > y1: continue
            ax.plot(a[:, 0], a[:, 1], color=cols[ci % len(cols)], lw=0.5)
            if not d.get('cerrada'): ax.plot([a[0, 0], a[-1, 0]], [a[0, 1], a[-1, 1]], 'r.', ms=3)
        elif d['t'] in ('TEXT', 'MTEXT') and x0 < d['p'][0] < x1 and y0 < d['p'][1] < y1:
            ax.text(d['p'][0], d['p'][1], d['txt'][:25], fontsize=5, color=cols[ci % len(cols)])
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off'); plt.savefig(salida)
