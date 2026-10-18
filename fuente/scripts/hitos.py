import json, numpy as np, shapely, pyarrow.parquet as pq
from pyproj import Transformer
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
def tolocal(coords):
    xs, ys = T.transform(*zip(*coords))
    return [[round(x - 424400, 2), round(8738400 - y, 2)] for x, y in zip(xs, ys)]
out = {}
# catedral y tribunas
for r in pq.read_table('data/buildings_building.parquet').to_pylist():
    if r['sources'][0]['dataset'] != 'OpenStreetMap': continue
    g = shapely.from_wkb(r['geometry']); g = g if g.geom_type == 'Polygon' else max(g.geoms, key=lambda q: q.area)
    pts = tolocal(list(g.exterior.coords)); c = shapely.Polygon(pts).centroid
    nm = (r['names'] or {}).get('primary')
    if nm == 'Catedral Santa Ana': out['catedral'] = pts
    if r['class'] == 'stadium': out.setdefault('tribunas', []).append(pts)
    if nm and 'Bomberos' in nm: out['bomberos'] = pts
for r in pq.read_table('data/base_land_use.parquet').to_pylist():
    g = shapely.from_wkb(r['geometry'])
    if g.geom_type != 'Polygon': continue
    pts = tolocal(list(g.exterior.coords)); c = shapely.Polygon(pts).centroid
    if r['class'] in ('stadium', 'pitch', 'track') and 950 < c.x < 1150 and 150 < c.y < 330:
        out['estadio_' + r['class']] = pts
    if r['class'] in ('grass', 'park') and 480 < c.x < 620 and 860 < c.y < 950:
        out.setdefault('plaza_' + r['class'], []).append(pts)
# senderos de la plaza
sen = []
for r in pq.read_table('data/transportation_segment.parquet').to_pylist():
    if r['class'] not in ('footway', 'pedestrian', 'path', 'steps'): continue
    g = shapely.from_wkb(r['geometry']); pts = tolocal(list(g.coords))
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    if 545 < np.mean(xs) < 615 and 870 < np.mean(zs) < 945: sen.append(pts)
out['plaza_senderos'] = sen
for k, v in out.items():
    if isinstance(v, list) and v and isinstance(v[0][0], list): print(k, len(v), [len(q) for q in v])
    else: print(k, len(v), v[:3])
json.dump(out, open('data/hitos.json', 'w'))
