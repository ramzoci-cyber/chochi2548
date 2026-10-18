import json, numpy as np, shapely, pyarrow.parquet as pq
from pyproj import Transformer
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
arr = np.load('data/gob_temporal_2023.npy'); pres = arr[2]
X0, Z0, PX = -100.0, -500.0, 0.5
s = pq.read_table('data/transportation_segment.parquet').to_pylist()
P = []
for r in s:
    if r['class'] in ('footway', 'path', 'steps', 'track'): continue
    g = shapely.from_wkb(r['geometry'])
    xs, ys = T.transform(*zip(*g.coords))
    pts = np.array([(x - 424400, 8738400 - y) for x, y in zip(xs, ys)])
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.hypot(*(b - a)) / 1.0))
        for t in np.linspace(0, 1, n, endpoint=False):
            p = a + (b - a) * t
            if 0 < p[0] < 1400 and 0 < p[1] < 1400: P.append(p)
P = np.array(P); print(len(P), 'puntos de vía')
def score(dx, dz):
    c = ((P[:, 0] + dx - X0) / PX).astype(int); r = ((P[:, 1] + dz - Z0) / PX).astype(int)
    return pres[r, c].mean()
best = []
for dx in np.arange(-12, 12.1, 1):
    for dz in np.arange(-12, 12.1, 1):
        best.append((score(dx, dz), dx, dz))
best.sort()
print(best[:8])
print('sin desplazamiento', score(0, 0))
# solo puntos cerca del jr chanchamayo
segs = json.load(open('data/chanchamayo_segs.json'))
Q = []
for sg in segs:
    pts = np.array(sg['pts'])
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.hypot(*(b - a))))
        for t in np.linspace(0, 1, n, endpoint=False): Q.append(a + (b - a) * t)
Q = np.array(Q)
def score2(dx, dz):
    c = ((Q[:, 0] + dx - X0) / PX).astype(int); r = ((Q[:, 1] + dz - Z0) / PX).astype(int)
    return pres[r, c].mean()
b2 = sorted((score2(dx, dz), dx, dz) for dx in np.arange(-12, 12.1, 0.5) for dz in np.arange(-12, 12.1, 0.5))
print('chanchamayo', b2[:8], 'sin', score2(0, 0))
