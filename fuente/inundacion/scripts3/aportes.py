# Puntos donde los cauces entran al dominio del modelo (5,2 x 8 km) y sus cuencas aportantes fuera del dominio
import numpy as np, json, sys, os, shapely, rasterio.features, rasterio.transform
from shapely.geometry import shape, Point, mapping
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts2'))
from marco import local_a_plano
h = np.load('ext/hidro30.npz'); Z, F, D8, acc = h['Z'], h['F'], h['D8'], h['acc']; E0, N1, R = float(h['E0']), float(h['N1']), float(h['R'])
H, W = Z.shape
DR = [0, 1, 1, 1, 0, -1, -1, -1]; DC = [1, 1, 0, -1, -1, -1, 0, 1]
# dominio del modelo en el marco OSM/GLO (≈ el del plano menos ~6 m: irrelevante a 30 m)
dE0, dE1, dN0, dN1 = 421800, 427000, 8734400, 8742400
def rc(E, N): return int((N1 - N) / R), int((E - E0) / R)
dentro = np.zeros((H, W), bool)
r0, c0 = rc(dE0, dN1); r1, c1 = rc(dE1, dN0)
dentro[r0:r1, c0:c1] = True
# celdas fuera del dominio que drenan a una celda dentro
ent = {}
for r in range(r0 - 1, r1 + 1):
    for c in range(c0 - 1, c1 + 1):
        if 0 <= r < H and 0 <= c < W and not dentro[r, c] and D8[r, c] >= 0:
            r2, c2 = r + DR[D8[r, c]], c + DC[D8[r, c]]
            if dentro[r2, c2]: ent[(r2, c2)] = ent.get((r2, c2), 0) + acc[r, c]
pts = sorted([(a, k) for k, a in ent.items() if a > 0.5], reverse=True)
print('entradas con más de 0,5 km2 de cuenca externa:', len(pts), '| total externo %.1f km2' % sum(a for a, k in pts))
# cuenca externa de cada entrada: celdas fuera del dominio aguas arriba
up = {}
orden = np.argsort(F, axis=None)            # de abajo hacia arriba
lab = np.full(H * W, -1, np.int32); d8 = D8.ravel(); fuera = (~dentro).ravel()
for n, (a, (r, c)) in enumerate(pts):
    pass
# etiqueta por propagación aguas arriba desde las celdas externas que drenan a cada entrada
fuentes = {}
for r in range(r0 - 1, r1 + 1):
    for c in range(c0 - 1, c1 + 1):
        if 0 <= r < H and 0 <= c < W and not dentro[r, c] and D8[r, c] >= 0:
            r2, c2 = r + DR[D8[r, c]], c + DC[D8[r, c]]
            if dentro[r2, c2] and (r2, c2) in dict((k, 1) for a, k in pts): fuentes[r * W + c] = [k for a, k in pts].index((r2, c2))
# etiquetado aguas arriba por recorrido inverso del D8 (BFS), robusto a empates de cota
from collections import deque
lab = lab.reshape(H, W)
cola = deque()
for idx, n in fuentes.items():
    r, c = divmod(idx, W); lab[r, c] = n; cola.append((r, c))
while cola:
    r, c = cola.popleft(); n = lab[r, c]
    for k in range(8):
        r2, c2 = r - DR[k], c - DC[k]                     # vecino que drenaría hacia (r, c) en la dirección k
        if 0 <= r2 < H and 0 <= c2 < W and D8[r2, c2] == k and lab[r2, c2] < 0 and not dentro[r2, c2]:
            lab[r2, c2] = n; cola.append((r2, c2))

tr = rasterio.transform.from_origin(E0, N1, R, R)
sal = []
gy, gx = np.gradient(Z.astype(float), R)
pend = np.hypot(gx, gy)
for n, (a, (r, c)) in enumerate(pts):
    m = lab == n
    if m.sum() == 0: continue
    area = m.sum() * R * R / 1e6
    # longitud del cauce más largo (aprox.: distancia máxima por D8 dentro de la cuenca) -> se estima con Hack: L = 1,4 A^0,6 (km)
    zz = Z[m]
    E = E0 + (c + 0.5) * R; N = N1 - (r + 0.5) * R
    xl, zl = local_a_plano(np.array([E - 424400]), np.array([8738400 - N]))
    geo = [g for g, v in rasterio.features.shapes(m.astype(np.uint8), mask=m, transform=tr) if v == 1]
    poly = shapely.union_all([shape(g) for g in geo])
    sal.append({'n': n, 'E': round(E, 1), 'N': round(N, 1), 'local': [round(float(xl[0]), 1), round(float(zl[0]), 1)], 'area_km2': round(area, 3),
                'z_media': round(float(zz.mean()), 1), 'z_max': round(float(zz.max()), 1), 'z_salida': round(float(Z[r, c]), 1),
                'pend_media': round(float(np.mean(pend[m])), 3), 'poly': mapping(poly.simplify(30))})
    if area > 1: print('entrada %d: E %.0f N %.0f local (%.0f, %.0f) área externa %.2f km2, cota media %.0f, máx %.0f, pendiente media %.2f' % (n, E, N, xl[0], zl[0], area, zz.mean(), zz.max(), np.mean(pend[m])))
json.dump(sal, open('ext/aportes.json', 'w'))
np.save('ext/aportes_lab.npy', lab)
print('área total del dominio que drena a la salida (km2):', round(float(acc[rc(424805, 8741945)]), 2))
