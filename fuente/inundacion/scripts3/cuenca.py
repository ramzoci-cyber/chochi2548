# Cuenca del río Tarma hasta la ciudad con Copernicus GLO-30 (igual que la tesis): reproyección a UTM 18S (30 m),
# relleno de depresiones (priority-flood), D8, acumulación; salida donde el área aportante ≈ 419,66 km².
import numpy as np, heapq, json, rasterio, rasterio.warp, rasterio.features, rasterio.transform, shapely
from rasterio.enums import Resampling
from shapely.geometry import shape, Point
src = rasterio.open('ext/dem/glo30_S12_W076.tif')
E0, E1, N0, N1, R = 392000, 442000, 8712000, 8762000, 30.0
W, H = int((E1 - E0) / R), int((N1 - N0) / R)
tr = rasterio.transform.from_origin(E0, N1, R, R)
Z = np.zeros((H, W), np.float32)
rasterio.warp.reproject(rasterio.band(src, 1), Z, dst_transform=tr, dst_crs='EPSG:32718', resampling=Resampling.bilinear)
print('DEM', Z.shape, Z.min(), Z.max())
# priority-flood con épsilon desde el borde
DR = [0, 1, 1, 1, 0, -1, -1, -1]; DC = [1, 1, 0, -1, -1, -1, 0, 1]
F = Z.astype(np.float64).copy(); vis = np.zeros(Z.shape, bool); pq = []
for r in range(H):
    for c in (0, W - 1): heapq.heappush(pq, (F[r, c], r, c)); vis[r, c] = True
for c in range(1, W - 1):
    for r in (0, H - 1): heapq.heappush(pq, (F[r, c], r, c)); vis[r, c] = True
while pq:
    z0, r, c = heapq.heappop(pq)
    for k in range(8):
        r2, c2 = r + DR[k], c + DC[k]
        if 0 <= r2 < H and 0 <= c2 < W and not vis[r2, c2]:
            vis[r2, c2] = True
            if F[r2, c2] <= z0: F[r2, c2] = z0 + 1e-4
            heapq.heappush(pq, (F[r2, c2], r2, c2))
best = np.zeros(F.shape); D8 = np.full(F.shape, -1, np.int8)
for k in range(8):
    sh = np.full_like(F, np.inf); r0, r1 = max(0, -DR[k]), H - max(0, DR[k]); c0, c1 = max(0, -DC[k]), W - max(0, DC[k])
    sh[r0:r1, c0:c1] = F[r0 + DR[k]:r1 + DR[k], c0 + DC[k]:c1 + DC[k]]
    p = (F - sh) / (1.4142 if k % 2 else 1.0); m = p > best; best[m] = p[m]; D8[m] = k
# acumulación (orden por cota descendente)
orden = np.argsort(-F, axis=None)
acc = np.ones(H * W)
d8 = D8.ravel()
for idx in orden:
    k = d8[idx]
    if k < 0: continue
    r, c = divmod(idx, W); r2, c2 = r + DR[k], c + DC[k]
    if 0 <= r2 < H and 0 <= c2 < W: acc[r2 * W + c2] += acc[idx]
acc = acc.reshape(H, W) * R * R / 1e6           # km2
np.savez_compressed('ext/hidro30.npz', Z=Z, F=F.astype(np.float32), D8=D8, acc=acc.astype(np.float32), E0=E0, N1=N1, R=R)
# salida: celda del cauce cerca de la ciudad con área más cercana a 419,66 km2 (zona del modelo E 421800-427000, N 8734400-8742400)
r0 = int((N1 - 8742400) / R); r1 = int((N1 - 8734400) / R); c0 = int((421800 - E0) / R); c1 = int((427000 - E0) / R)
sub = acc[r0:r1, c0:c1]
i = np.argmin(np.abs(sub - 419.66)); rr, cc = divmod(i, sub.shape[1]); rr += r0; cc += c0
print('salida candidata: E %.0f N %.0f, área %.2f km2, cota %.1f' % (E0 + (cc + 0.5) * R, N1 - (rr + 0.5) * R, acc[rr, cc], Z[rr, cc]))
# cuencas en el cauce principal dentro del dominio (para ubicar los aportes)
for a in (100, 200, 300, 400, 419.66, 450):
    j = np.argmin(np.abs(sub - a)); r_, c_ = divmod(j, sub.shape[1])
    print('  área %.1f -> E %.0f N %.0f (%.2f km2)' % (a, E0 + (c_ + c0 + 0.5) * R, N1 - (r_ + r0 + 0.5) * R, sub[r_, c_]))
