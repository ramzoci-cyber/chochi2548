import json, numpy as np, shapely, pyarrow.parquet as pq, matplotlib, sys
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyproj import Transformer
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
C = json.load(open('orig/datos_clean.json'))
def tolocal(coords):
    xs, ys = T.transform(*zip(*coords))
    return [(x - 424400, 8738400 - y) for x, y in zip(xs, ys)]
arr = np.load('data/gob_temporal_2023.npy')
pres, alt = arr[2], arr[1]
ext = [-100, 1500, 1500, -500]
x0, x1, z0, z1 = [float(v) for v in sys.argv[1:5]]
fig, ax = plt.subplots(figsize=(12, 12 * (z1 - z0) / (x1 - x0)), dpi=110)
h = np.where(pres > 0.3, alt, np.nan)
im = ax.imshow(h, extent=ext, cmap='turbo', vmin=0, vmax=15, interpolation='nearest')
plt.colorbar(im, ax=ax, fraction=0.03)
s = pq.read_table('data/transportation_segment.parquet').to_pylist()
for r in s:
    g = shapely.from_wkb(r['geometry'])
    pts = tolocal(list(g.coords)); xs, zs = zip(*pts)
    if max(xs) < x0 or min(xs) > x1 or max(zs) < z0 or min(zs) > z1: continue
    ax.plot(xs, zs, color='white', lw=0.8, alpha=0.9)
    nm = (r['names'] or {}).get('primary')
    if nm:
        m = len(pts) // 2
        ax.text(pts[m][0], pts[m][1], nm.replace('Jirón', 'Jr.').replace('Avenida', 'Av.'), fontsize=8, color='white')
ax.set_xlim(x0, x1); ax.set_ylim(z1, z0); ax.set_aspect('equal'); ax.grid(alpha=0.25)
ax.set_facecolor('#222')
plt.savefig(sys.argv[5], bbox_inches='tight')
