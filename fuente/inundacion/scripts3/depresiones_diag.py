# Diagnóstico de las depresiones cerradas del terreno base (MDE del plano con el cauce excavado), vecindad de 4 celdas:
# tamaño, profundidad, cercanía al cauce y costo de abrirles una salida (zanja desde el fondo hasta una celda más baja)
import sys, heapq, numpy as np
from scipy import ndimage
sys.path.insert(0, 'scripts3'); import sim2d
M = np.load('sim/malla.npz'); Z = M['Z'].astype(np.float64); rio = M['rio']; fp = M['fp']; fb = M['fb']
z = Z.copy(); z[rio] -= 1.0
H, W = z.shape
F = sim2d.relleno(z); dep = F - z
mdep = dep > 0.01
cruz = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
lab, n = ndimage.label(mdep, structure=cruz)
d = ndimage.distance_transform_edt(~rio) * 10
print('depresiones (> 1 cm):', n, '| celdas', int(mdep.sum()), '| volumen %.0f m3' % (dep[mdep].sum() * 100))
# costo de la zanja: búsqueda de menor corte desde el fondo hasta una celda más baja que el fondo (Dijkstra, costo = suma de cortes)
def zanja(p, zmax_len=400):
    zp = z[p]; dist = {p: 0.0}; prev = {}; hq = [(0.0, 0, p)]; vis = set()
    while hq:
        c, L, q = heapq.heappop(hq)
        if q in vis: continue
        vis.add(q)
        j, i = q
        if (z[q] < zp - 1e-6 and q != p) or j in (0, H - 1) or i in (0, W - 1):
            cam = [q]
            while cam[-1] != p: cam.append(prev[cam[-1]])
            cortes = [max(0.0, z[c_] - zp) for c_ in cam]
            return max(cortes), len(cam) - 1
        if L >= zmax_len: continue
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r = (j + dj, i + di)
            if 0 <= r[0] < H and 0 <= r[1] < W and r not in vis:
                nc = c + max(0.0, z[r] - zp)
                if nc < dist.get(r, 1e18): dist[r] = nc; prev[r] = q; heapq.heappush(hq, (nc, L + 1, r))
    return None, None
filas = []
for k in range(1, n + 1):
    g = lab == k; idx = np.argwhere(g); zz = z[g]; p = tuple(idx[zz.argmin()])
    corte, largo = zanja(p)
    filas.append((int(g.sum()), float(dep[g].max()), float(d[g].min()), int((fp[g] > 0.3).sum()), corte, largo))
A = np.array(filas, dtype=float)
cerca = A[:, 2] <= 50
for nom, m in [('junto al cauce (<= 50 m)', cerca), ('lejos del cauce', ~cerca)]:
    print('%-26s grupos %4d | celdas %6d | prof. máx mediana %.2f, P90 %.2f, máx %.2f | corte de zanja mediana %.2f, P90 %.2f, máx %.2f | largo mediana %.0f, P90 %.0f, máx %.0f celdas | con calle %d' % (
        nom, m.sum(), A[m, 0].sum(), np.median(A[m, 1]), np.percentile(A[m, 1], 90), A[m, 1].max(), np.median(A[m, 4]), np.percentile(A[m, 4], 90), A[m, 4].max(),
        np.median(A[m, 5]), np.percentile(A[m, 5], 90), A[m, 5].max(), (A[m, 3] > 0).sum()))
for lim in [0.5, 1.0, 2.0, 3.0]:
    ok = A[:, 4] <= lim
    print('zanja con corte <= %.1f m: %d de %d grupos (%d de %d celdas)' % (lim, ok.sum(), len(A), A[ok, 0].sum(), A[:, 0].sum()))
