# Terreno del modelo con las curvas de nivel del Plano Total 2025 (marco del plano) + red D8 de 5 m recalculada
#  - MDE 5 m: residuo armónico sobre la tendencia (MDE original desplazado al marco del plano y suavizado)
#  - fuera de la cobertura de curvas: MDE original + residuo extendido (mismo datum vertical que el plano)
import pickle, json, heapq, sys, os, time, numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl, shapely
from scipy.ndimage import gaussian_filter, distance_transform_edt, map_coordinates, median_filter, generic_filter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marco import plano_a_local_orig
t0 = time.time()
D = pickle.load(open('planos/plano_total_wcs.pkl', 'rb'))
C = json.load(open('orig/datos_clean.json')); W, H, CEL, ZMIN = C['W'], C['H'], C['celda'], C['zmin']; MX, MZ = W * CEL / 2, H * CEL / 2
Z0 = np.load('orig/z.npy').astype(np.float64) + ZMIN
R5, C5 = 2 * H, 2 * W
x5 = -MX + 2.5 + 5 * np.arange(C5); z5 = -MZ + 2.5 + 5 * np.arange(R5)          # centros (locales, marco del plano)
XX, ZZ = np.meshgrid(x5, z5)
xo, zo = plano_a_local_orig(XX.ravel(), ZZ.ravel())                                # dónde estaba ese punto en el modelo original
T0 = map_coordinates(Z0, [((zo + MZ) / CEL - 0.5), ((xo + MX) / CEL - 0.5)], order=1, mode='nearest').reshape(R5, C5)
tend = gaussian_filter(T0, 4)
# ---- curvas rasterizadas (celda de 5 m)
suma = np.zeros((R5, C5)); cuenta = np.zeros((R5, C5)); zmin_c = np.full((R5, C5), np.inf); zmax_c = np.full((R5, C5), -np.inf)
for capa in ('CONT-MNR', 'CONT-MJR'):
    for d in D[capa]:
        if 'pts' not in d or len(d['pts']) < 2: continue
        a = np.array(d['pts']); z = float(np.median(a[:, 2]))
        if not (2990 < z < 3400) or abs(z / 5 - round(z / 5)) > 1e-3: continue
        seg = np.hypot(*np.diff(a[:, :2], axis=0).T); L = np.r_[0, np.cumsum(seg)]
        if L[-1] <= 0: continue
        s = np.arange(0, L[-1] + 0.5, 1.0); E = np.interp(s, L, a[:, 0]); N = np.interp(s, L, a[:, 1])
        c = np.floor((E - 424400 + MX) / 5).astype(int); r = np.floor((8738400 - N + MZ) / 5).astype(int)
        ok = (c >= 0) & (c < C5) & (r >= 0) & (r < R5)
        idx = np.unique(r[ok] * C5 + c[ok])
        np.add.at(suma.ravel(), idx, z); np.add.at(cuenta.ravel(), idx, 1)
        np.minimum.at(zmin_c.ravel(), idx, z); np.maximum.at(zmax_c.ravel(), idx, z)
fijo = cuenta > 0
zc = np.where(fijo, suma / np.maximum(cuenta, 1), np.nan)
res = np.where(fijo, zc - tend, np.nan)
med0 = float(np.nanmedian(res))
# ---- filtro de curvas erróneas: absoluto (respecto al desfase típico) y local (mediana en 150 m)
malo = fijo & (np.abs(res - med0) > 40)
rr = np.where(fijo & ~malo, res, np.nan)
# mediana local robusta en ventana de 31x31 celdas (155 m) usando bloques: aproximación por mediana de bloques de 10x10
B = 10
Rb, Cb = R5 // B, C5 // B
blq = rr[:Rb * B, :Cb * B].reshape(Rb, B, Cb, B).transpose(0, 2, 1, 3).reshape(Rb, Cb, B * B)
with np.errstate(all='ignore'):
    import warnings; warnings.simplefilter('ignore')
    medb = np.nanmedian(blq, axis=2)
# mediana de 3x3 bloques (150 m)
from numpy.lib.stride_tricks import sliding_window_view
pad = np.pad(medb, 1, constant_values=np.nan)
med3 = np.nanmedian(sliding_window_view(pad, (3, 3)).reshape(Rb, Cb, 9), axis=2)
medloc = np.kron(np.nan_to_num(med3, nan=med0), np.ones((B, B)))
medloc = np.pad(medloc, ((0, R5 - medloc.shape[0]), (0, C5 - medloc.shape[1])), mode='edge')
malo |= fijo & (np.abs(res - medloc) > 22)
# celdas con curvas de niveles muy distintos (amontonadas) -> poco fiables
malo |= fijo & ((zmax_c - zmin_c) > 12)
fijo2 = fijo & ~malo
# el plano manda en la zona urbana: curvas a menos de 200 m de una manzana del plano
import rasterio.features, rasterio.transform
MZS = pickle.load(open('plan/manzanas_crudo.pkl', 'rb'))['pols']
tr = rasterio.transform.from_origin(424400 - MX, 8738400 + MZ, 5, 5)
mz5 = rasterio.features.rasterize([(m, 1) for m in MZS], out_shape=(R5, C5), transform=tr, dtype='uint8').astype(bool)
dmz = distance_transform_edt(~mz5) * 5
fuera_urb = fijo2 & (dmz > 60)
fijo2 &= dmz <= 60
print('curvas fuera de la zona urbana (no se usan):', int(fuera_urb.sum()))
print('celdas de curva', int(fijo.sum()), 'descartadas', int(malo.sum()), 'desfase vertical típico (plano - GLO-30) %.2f m' % med0)
# ---- Laplace del residuo: Dirichlet en curvas y lejos (> 450 m) con el desfase típico
dist = distance_transform_edt(~fijo2) * 5
lejos = dist > 260
r0 = np.where(fijo2, res, np.where(lejos, med0, 0.0))
inc = ~fijo2 & ~lejos
idx = -np.ones((R5, C5), dtype=np.int64); idx[inc] = np.arange(inc.sum()); nI = int(inc.sum())
rr_, cc_ = np.nonzero(inc); k0 = idx[rr_, cc_]
filas, cols, vals = [], [], []; b = np.zeros(nI); diag = np.zeros(nI)
for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    r2, c2 = rr_ + dr, cc_ + dc
    dentro = (r2 >= 0) & (r2 < R5) & (c2 >= 0) & (c2 < C5)
    diag[dentro] += 1
    r2c, c2c = np.clip(r2, 0, R5 - 1), np.clip(c2, 0, C5 - 1)
    vi = dentro & inc[r2c, c2c]
    filas.append(k0[vi]); cols.append(idx[r2c[vi], c2c[vi]]); vals.append(-np.ones(vi.sum()))
    vf = dentro & ~inc[r2c, c2c]
    np.add.at(b, k0[vf], r0[r2c[vf], c2c[vf]])
A = sp.csr_matrix((np.concatenate(vals + [diag]), (np.concatenate(filas + [k0]), np.concatenate(cols + [k0]))), shape=(nI, nI))
x, info = spl.cg(A, b, x0=np.full(nI, med0), rtol=1e-8, maxiter=40000)
print('incógnitas', nI, 'CG', info, 'tiempo', round(time.time() - t0, 1))
rf = r0.copy(); rf[inc] = x
# base: tendencia suavizada cerca de las curvas, original lejos
w = np.clip((160 - dist) / 90, 0, 1); w = w * w * (3 - 2 * w)
base = w * tend + (1 - w) * T0
Z5 = base + rf
print('error en curvas usadas: %.3f m' % np.abs(Z5[fijo2] - zc[fijo2]).max())
# fuera del casco (laderas) se suaviza un poco para evitar facetas entre curvas muy irregulares
ws = np.clip((dmz - 40) / 60, 0, 1); ws = ws * ws * (3 - 2 * ws)
Z5 = (1 - ws) * Z5 + ws * gaussian_filter(Z5, 2.0)
print('error en curvas dentro del casco (< 40 m de manzanas): %.3f m' % np.abs(Z5[fijo2 & (dmz < 40)] - zc[fijo2 & (dmz < 40)]).max())
# ---- malla de 10 m del modelo (promedio 2x2 = valor en el centro de la celda de 10 m)
Z10 = Z5.reshape(H, 2, W, 2).mean(axis=(1, 3))
cob10 = (dist.reshape(H, 2, W, 2).min(axis=(1, 3)) < 120)
np.save('plan/z10.npy', Z10.astype(np.float32))
np.savez_compressed('plan/mde5.npz', Z=Z5.astype(np.float32), dist=dist.astype(np.float32), fijo=fijo2, mz=mz5, x0=float(x5[0]), z0=float(z5[0]), paso=5.0, med0=med0)
print('Z10 min %.1f max %.1f | cobertura del plano (10 m): %.1f km2' % (Z10.min(), Z10.max(), cob10.sum() * 100 / 1e6))
def cota(xl, zl):
    return float(map_coordinates(Z5, [[(zl + MZ) / 5 - 0.5], [(xl + MX) / 5 - 0.5]], order=1)[0])
B0 = json.load(open('plan/datos_base.json'))
print('Plaza de Armas %.2f | punto crítico T01 %.2f' % (cota(*B0['plaza_c']), cota(*B0['punto_critico'])))
