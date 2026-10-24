import pickle, sys, numpy as np, matplotlib, random
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
x0, x1, y0, y1, salida = *map(float, sys.argv[1:5]), sys.argv[5]
fuente = sys.argv[6] if len(sys.argv) > 6 else 'plan/manzanas_crudo.pkl'
M = pickle.load(open(fuente, 'rb'))
fig = plt.figure(figsize=(14, 14 * (y1 - y0) / (x1 - x0)), dpi=100); ax = fig.add_axes([0, 0, 1, 1])
rnd = random.Random(1)
for p in M['pols']:
    b = p.bounds
    if b[2] < x0 or b[0] > x1 or b[3] < y0 or b[1] > y1: continue
    ax.add_patch(MP(np.array(p.exterior.coords), closed=True, fc=(rnd.random() * 0.5 + 0.4, rnd.random() * 0.5 + 0.4, rnd.random() * 0.5 + 0.4), ec='k', lw=0.4))
    for h in p.interiors: ax.add_patch(MP(np.array(h.coords), closed=True, fc='white', ec='r', lw=0.4))
for g in M.get('colgantes', []):
    a = np.array(g.coords); ax.plot(a[:, 0], a[:, 1], 'r-', lw=1.2)
for g in M.get('puentes', []):
    a = np.array(g.coords); ax.plot(a[:, 0], a[:, 1], 'b-', lw=1.5)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off'); plt.savefig(salida)
