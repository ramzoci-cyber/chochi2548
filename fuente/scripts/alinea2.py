import json, numpy as np, shapely, pyarrow.parquet as pq
from shapely import STRtree
from pyproj import Transformer
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
arr = np.load('data/gob_temporal_2023.npy'); pres = arr[2]
X0, Z0, PX = -100.0, -500.0, 0.5
def tolocal(coords):
    xs, ys = T.transform(*zip(*coords))
    return [(x - 424400, 8738400 - y) for x, y in zip(xs, ys)]
t = pq.read_table('data/buildings_building.parquet').to_pylist()
polys = {'Microsoft ML Buildings': [], 'Google Open Buildings': [], 'OpenStreetMap': []}
for r in t:
    g = shapely.from_wkb(r['geometry'])
    for p in (g.geoms if g.geom_type == 'MultiPolygon' else [g]):
        q = shapely.Polygon(tolocal(list(p.exterior.coords)))
        c = q.centroid
        if 0 < c.x < 1400 and 0 < c.y < 1400: polys[r['sources'][0]['dataset']].append(q)
# raster vs huellas: para cada fuente, presencia media dentro de sus polígonos con desplazamientos
def puntos(qs, paso=1.0):
    P = []
    for q in qs:
        minx, minz, maxx, maxz = q.bounds
        xs = np.arange(minx, maxx, paso); zs = np.arange(minz, maxz, paso)
        if len(xs) == 0 or len(zs) == 0: continue
        gx, gz = np.meshgrid(xs, zs); pts = np.c_[gx.ravel(), gz.ravel()]
        m = shapely.contains_xy(q, pts[:, 0], pts[:, 1]); P.append(pts[m])
    return np.vstack(P)
for k, qs in polys.items():
    P = puntos(qs)
    def sc(dx, dz):
        c = ((P[:, 0] + dx - X0) / PX).astype(int); r = ((P[:, 1] + dz - Z0) / PX).astype(int)
        return pres[r, c].mean()
    b = sorted(((sc(dx, dz), dx, dz) for dx in np.arange(-10, 10.1, 1) for dz in np.arange(-10, 10.1, 1)), reverse=True)
    print(k, len(qs), 'mejor', b[:3], 'sin', sc(0, 0))
# OSM vías vs huellas Microsoft: fracción de puntos de vía dentro de huellas
s = pq.read_table('data/transportation_segment.parquet').to_pylist()
V = []
for r in s:
    if r['class'] in ('footway', 'path', 'steps', 'track'): continue
    g = shapely.from_wkb(r['geometry'])
    pts = np.array(tolocal(list(g.coords)))
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.hypot(*(b - a))))
        for tt in np.linspace(0, 1, n, endpoint=False):
            p = a + (b - a) * tt
            if 0 < p[0] < 1400 and 0 < p[1] < 1400: V.append(p)
V = np.array(V)
for k in ['Microsoft ML Buildings', 'Google Open Buildings']:
    U = shapely.union_all(polys[k])
    def f(dx, dz):
        return shapely.contains_xy(U, V[:, 0] + dx, V[:, 1] + dz).mean()
    b = sorted((f(dx, dz), dx, dz) for dx in np.arange(-10, 10.1, 2) for dz in np.arange(-10, 10.1, 2))
    print('vias OSM en huellas', k, 'mejor', b[:3], 'sin', f(0, 0))
