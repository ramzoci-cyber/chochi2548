# Poligoniza la capa "manzana ok" del Plano Total 2025 (JLORE) -> polígonos de manzana en UTM 18S
# 1) agrupa extremos a < 0.6 m (esquinas que no cierran), 2) prolonga extremos libres hasta la línea vecina (< 1.2 m), 3) poligoniza
import pickle, json, sys, numpy as np, shapely, collections
from shapely.geometry import LineString, Point
from shapely.ops import polygonize_full, unary_union, nearest_points
from scipy.spatial import cKDTree
fuente = sys.argv[1] if len(sys.argv) > 1 else 'planos/plano_total_wcs.pkl'
D = pickle.load(open(fuente, 'rb'))
L = []
for d in D['manzana ok']:
    if 'pts' not in d or len(d['pts']) < 2: continue
    a = np.array(d['pts'])[:, :2]
    if not (421000 < a[:, 0].mean() < 427500 and 8734000 < a[:, 1].mean() < 8743500): continue
    if d.get('cerrada') and len(a) > 2 and np.hypot(*(a[0] - a[-1])) > 1e-6: a = np.vstack([a, a[:1]])
    if LineString(a).length < 0.05: continue
    L.append(a.copy())
print('líneas', len(L))
# 1) agrupar extremos
ext = np.array([a[k] for a in L for k in (0, -1)])
arb = cKDTree(ext)
par = list(range(len(ext)))
def raiz(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
for i, j in arb.query_pairs(0.6):
    par[raiz(i)] = raiz(j)
grupos = collections.defaultdict(list)
for i in range(len(ext)): grupos[raiz(i)].append(i)
cen = {}
for g in grupos.values():
    c = ext[g].mean(0)
    for i in g: cen[i] = c
n_mov = 0
for li, a in enumerate(L):
    for k, idx in ((0, 2 * li), (-1, 2 * li + 1)):
        if np.hypot(*(a[k] - cen[idx])) > 1e-9: n_mov += 1
        a[k] = cen[idx]
print('extremos movidos', n_mov)
lineas = [LineString(a) for a in L if LineString(a).length > 0.05]
# 2) extremos libres -> línea más cercana
red = unary_union(lineas)
grado = collections.Counter()
for g in red.geoms:
    for p in (g.coords[0], g.coords[-1]): grado[p] += 1
libres = [p for p, k in grado.items() if k == 1]
geoms = list(red.geoms); arbol = shapely.STRtree(geoms)
puentes = []
for p in libres:
    P = Point(p); best = None
    for i in arbol.query(P.buffer(1.2)):
        g = geoms[i]
        if p in (g.coords[0], g.coords[-1]) and grado[g.coords[0]] + grado[g.coords[-1]] >= 1:
            # descartar la propia línea (el extremo libre pertenece a ella)
            if Point(g.coords[0]).distance(P) < 1e-9 or Point(g.coords[-1]).distance(P) < 1e-9: continue
        d = g.distance(P)
        if d < 1.2 and (best is None or d < best[0]): best = (d, g)
    if best:
        q = nearest_points(P, best[1])[1]
        if q.distance(P) > 1e-9: puentes.append(LineString([p, (q.x, q.y)]))
# 3) pares de extremos libres mutuamente más cercanos a < 3 m (tramos de contorno que no se tocan)
lib = np.array(libres)
if len(lib) > 1:
    ka = cKDTree(lib); dd, jj = ka.query(lib, k=2)
    for i in range(len(lib)):
        j = jj[i, 1]
        if dd[i, 1] < 3.0 and jj[j, 1] == i and i < j:
            puentes.append(LineString([tuple(lib[i]), tuple(lib[j])]))
print('extremos libres', len(libres), 'puentes', len(puentes))
red2 = unary_union(geoms + puentes)
pols, cuelgan, cortes, invalidas = polygonize_full(red2)
P = list(pols.geoms)
A = np.array([p.area for p in P])
print('polígonos', len(P), 'colgantes', len(cuelgan.geoms), 'área total ha', round(A.sum() / 1e4, 1), 'percentiles área', np.percentile(A, [5, 25, 50, 75, 95, 99]).round(0), 'max', A.max().round(0))
# 4) unir caras contiguas (subdivisiones internas de una misma manzana)
arb = shapely.STRtree(P); par = list(range(len(P)))
def r2(i):
    while par[i] != i: par[i] = par[par[i]]; i = par[i]
    return i
for i, p in enumerate(P):
    for j in arb.query(p):
        if j <= i: continue
        inter = p.boundary.intersection(P[j].boundary)
        if inter.length > 0.3: par[r2(i)] = r2(j)
comp = collections.defaultdict(list)
for i in range(len(P)): comp[r2(i)].append(i)
M = []
for idx in comp.values():
    u = unary_union([P[i] for i in idx]).buffer(0.01).buffer(-0.01)
    for g in (u.geoms if u.geom_type == 'MultiPolygon' else [u]):
        if g.area > 4: M.append(g)
A = np.array([m.area for m in M])
print('manzanas (caras unidas)', len(M), 'área ha', round(A.sum() / 1e4, 1), 'percentiles', np.percentile(A, [5, 25, 50, 75, 95]).round(0))
pickle.dump({'pols': M, 'caras': P, 'puentes': puentes, 'colgantes': list(cuelgan.geoms), 'lineas': list(red2.geoms)}, open('plan/manzanas_crudo.pkl', 'wb'))
