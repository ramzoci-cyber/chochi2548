import json, numpy as np, shapely, pyarrow.parquet as pq
from pyproj import Transformer
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
def tolocal(coords):
    xs, ys = T.transform(*zip(*coords))
    return [(x - 424400, 8738400 - y) for x, y in zip(xs, ys)]
d = np.load('data/calle_bruto.npz')
eje = shapely.LineString(np.c_[d['cx'], d['cz']])
s = pq.read_table('data/transportation_segment.parquet').to_pylist()
res = []
for r in s:
    nm = (r['names'] or {}).get('primary') or ''
    if 'Chanchamayo' in nm: continue
    if r['subtype'] != 'road': continue
    g = shapely.from_wkb(r['geometry']); pts = tolocal(list(g.coords))
    for end, nxt in ((pts[0], pts[1]), (pts[-1], pts[-2])):
        p = shapely.Point(end)
        if eje.distance(p) < 1.5:
            st = eje.project(p)
            ang = np.degrees(np.arctan2(nxt[1] - end[1], nxt[0] - end[0]))
            res.append((round(st, 1), nm or '(sin nombre)', r['class'], [round(end[0], 1), round(end[1], 1)], [round(nxt[0], 1), round(nxt[1], 1)]))
res.sort()
for x in res: print(x)
json.dump(res, open('data/cruces_bruto.json', 'w'))
