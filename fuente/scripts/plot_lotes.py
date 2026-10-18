import json, numpy as np, matplotlib, sys
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
arr = np.load('data/gob_temporal_2023.npy'); PRES, ALT = arr[2], arr[1]
X0, Z0, PX = -95.0, -497.5, 0.5
e = np.load('data/eje_fino.npz'); S, cx, cz, nx, nz = e['S'], e['cx'], e['cz'], e['nx'], e['nz']; N = len(S)
def idx(s): return int(np.clip(round(s / 0.5), 0, N - 1))
def P(s, o, lado):
    i = idx(s); return [cx[i] + nx[i] * o * lado, cz[i] + nz[i] * o * lado]
d = json.load(open('data/lotes.json'))
x0, x1, z0, z1 = [float(v) for v in sys.argv[1:5]]
fig = plt.figure(figsize=(10, 10 * (z1 - z0) / (x1 - x0)), dpi=120); ax = fig.add_axes([0, 0, 1, 1])
h = np.where(PRES > 0.5, ALT, np.nan)
ext = [X0, X0 + PX * PRES.shape[1], Z0 + PX * PRES.shape[0], Z0]
ax.imshow(h, extent=ext, cmap='gray', vmin=0, vmax=18, interpolation='nearest', alpha=0.6)
ax.plot(cx, cz, 'y-', lw=0.8)
cm = plt.get_cmap('turbo')
for l in d['lotes']:
    s0, s1, (f0, f1), lado = l['s0'], l['s1'], l['f'], l['lado']
    ss = np.linspace(s0, s1, max(2, int((s1 - s0) / 1.0)))
    fr = [P(s, f0 + (f1 - f0) * (s - s0) / max(1e-6, s1 - s0), lado) for s in ss]
    bk = [P(s, f0 + (f1 - f0) * (s - s0) / max(1e-6, s1 - s0) + l['D'], lado) for s in ss[::-1]]
    ax.add_patch(MPoly(fr + bk, closed=True, fc=cm(min(1, l['h'] / 15)), ec='k', lw=0.5, alpha=0.75))
    if l['hb'] is not None:
        bk2 = [P(s, f0 + (f1 - f0) * (s - s0) / max(1e-6, s1 - s0) + l['Dt'], lado) for s in ss[::-1]]
        ax.add_patch(MPoly(bk[::-1] + bk2, closed=True, fc=cm(min(1, l['hb'] / 15)), ec='k', lw=0.3, alpha=0.5))
    c = P((s0 + s1) / 2, (f0 + f1) / 2 + 2, lado)
    ax.text(c[0], c[1], f"{l['h']:.0f}", fontsize=6, ha='center')
for c in d['cercos']:
    s0, s1, (f0, f1), lado = c['s0'], c['s1'], c['f'], c['lado']
    ss = np.linspace(s0, s1, 8)
    pts = np.array([P(s, f0 + (f1 - f0) * (s - s0) / max(1e-6, s1 - s0), lado) for s in ss])
    ax.plot(pts[:, 0], pts[:, 1], 'm-', lw=2)
ax.set_xlim(x0, x1); ax.set_ylim(z1, z0); ax.set_aspect('equal'); ax.axis('off')
plt.savefig(sys.argv[5])
