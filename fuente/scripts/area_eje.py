import json, numpy as np, shapely
from shapely.geometry import Polygon, Point, LineString
C = json.load(open('orig/datos_clean.json'))
mc = shapely.union_all([Polygon(p).buffer(0) for p in C['microcuenca']])
print('microcuenca: área %.3f km2' % (mc.area / 1e6), 'bounds', mc.bounds)
e = np.load('data/eje1m.npz'); S, cx, cz = e['S'], e['cx'], e['cz']
eje = LineString(np.c_[cx, cz])
sT = eje.project(Point(C['punto_critico']))
print('estación de T01: %.1f m, dist al eje %.1f' % (sT, eje.distance(Point(C['punto_critico']))))
minx, minz, maxx, maxz = mc.bounds
xs = np.arange(minx + 2.5, maxx, 5.0); zs = np.arange(minz + 2.5, maxz, 5.0)
gx, gz = np.meshgrid(xs, zs); pts = np.c_[gx.ravel(), gz.ravel()]
dentro = shapely.contains_xy(mc, pts[:, 0], pts[:, 1]); pts = pts[dentro]
sp = np.array([eje.project(Point(p)) for p in pts])
sp = np.minimum(sp, sT)
cnt = np.bincount(np.clip(sp.astype(int), 0, len(S) - 1), minlength=len(S))
A = np.cumsum(cnt) * 25.0
for s in range(0, len(S), 60): print(int(S[s]), int(A[s]))
print('A en T01 %.0f m2' % A[int(sT)])
json.dump({'A': [round(float(v)) for v in A], 'sT01': round(float(sT), 1), 'Amc': round(mc.area)}, open('data/area_eje.json', 'w'))
