# Campo de desplazamiento (datos del modelo -> marco del plano) estimado por ventanas
import json, pickle, numpy as np, shapely, pyarrow.parquet as pq
from shapely.geometry import Polygon
from pyproj import Transformer
M = pickle.load(open('plan/manzanas_crudo.pkl', 'rb'))['pols']
U = shapely.union_all(M); shapely.prepare(U)
E = json.load(open('orig/edificios.json'))
BP = []
for b in E:
    P = np.array(b['P']); q = Polygon(np.c_[P[:, 0] + 424400, 8738400 - P[:, 1]])
    if not q.is_valid or q.area < 20: continue
    minx, miny, maxx, maxy = q.bounds
    xs, ys = np.meshgrid(np.arange(minx, maxx, 1.5), np.arange(miny, maxy, 1.5))
    m = shapely.contains_xy(q, xs.ravel(), ys.ravel()); BP.append(np.c_[xs.ravel()[m], ys.ravel()[m]])
BP = np.vstack(BP)
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
V = []
for r in pq.read_table('data/transportation_segment.parquet').to_pylist():
    if r.get('class') in ('footway', 'path', 'steps', 'track', None): continue
    g = shapely.from_wkb(r['geometry']); xs, ys = T.transform(*zip(*g.coords)); a = np.c_[xs, ys]
    for p, q in zip(a[:-1], a[1:]):
        n = max(1, int(np.hypot(*(q - p)) / 2))
        for t in np.linspace(0, 1, n, endpoint=False): V.append(p + (q - p) * t)
V = np.array(V)
# sólo puntos cerca de manzanas (zona cubierta por el plano)
cerca = shapely.union_all([m.buffer(25) for m in M]); shapely.prepare(cerca)
BP = BP[shapely.contains_xy(cerca, BP[:, 0], BP[:, 1])]; V = V[shapely.contains_xy(cerca, V[:, 0], V[:, 1])]
print('puntos edificio', len(BP), 'puntos vía', len(V))
def estimar(cx, cy, R):
    mb = (np.abs(BP[:, 0] - cx) < R) & (np.abs(BP[:, 1] - cy) < R); mv = (np.abs(V[:, 0] - cx) < R) & (np.abs(V[:, 1] - cy) < R)
    B, Q = BP[mb], V[mv]
    if len(B) < 3000 or len(Q) < 300: return None
    def f(dx, dy):
        return 0.5 * shapely.contains_xy(U, B[:, 0] + dx, B[:, 1] + dy).mean() + 0.5 * (1 - shapely.contains_xy(U, Q[:, 0] + dx, Q[:, 1] + dy).mean())
    best = max(((f(dx, dy), dx, dy) for dx in np.arange(-10, 10.1, 1) for dy in np.arange(-6, 14.1, 1)))
    b2 = max(((f(dx, dy), dx, dy) for dx in np.arange(best[1] - 1, best[1] + 1.01, 0.25) for dy in np.arange(best[2] - 1, best[2] + 1.01, 0.25)))
    # nitidez: caída del puntaje a 2 m
    nit = b2[0] - np.mean([f(b2[1] + a, b2[2] + b) for a, b in ((2, 0), (-2, 0), (0, 2), (0, -2))])
    return b2[1], b2[2], b2[0], nit, len(B), len(Q), f(0, 0)
from multiprocessing import Pool
def tarea(c):
    r = estimar(c[0], c[1], 225)
    return None if r is None else [float(c[0]), float(c[1])] + [float(v) for v in r]
if __name__ == '__main__':
    centros = [(cx, cy) for cy in np.arange(8735000, 8742600, 250) for cx in np.arange(421800, 426300, 250)]
    with Pool(4) as pool: res = [r for r in pool.map(tarea, centros) if r]
    for r in res: print(r[0], r[1], 'dx %.2f dy %.2f puntaje %.3f nitidez %.3f nB %d nV %d sin %.3f' % tuple(r[2:]))
    json.dump(res, open('plan/desfase_ventanas.json', 'w'))
