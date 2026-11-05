# Calibración a escala de manzana: compara el riesgo simulado por unidad (P90 del tirante máximo en la unidad + 10 m,
# clase de peligro por umbrales de tirante y matriz peligro x vulnerabilidad inferida de C-04) con el riesgo de la tesis
# (C-04, escenario presente). Recorre las corridas candidatas y una grilla de umbrales; informa kappa, conteos y puntos
# críticos. Uso: python calibrar_unidades.py res1.npz res2.npz ...
import json, sys, os, itertools, numpy as np, shapely, rasterio.features, rasterio.transform
from shapely.geometry import Polygon
U = json.load(open('tesis/riesgo_unidades.json')); P = np.load('tesis/peligro_malla10.npz')
MAT = [[1, 2, 2, 3], [1, 2, 2, 3], [2, 2, 3, 3], [2, 3, 3, 4]]          # riesgo[peligro-1][vulnerabilidad-1], inferida de C-04
W, H = 520, 800
tr = rasterio.transform.Affine(10, 0, -2600, 0, 10, -4000)
CACHE = 'sim/mascaras_unidades.npz'
if os.path.exists(CACHE):
    Z = np.load(CACHE); idx, ini = Z['idx'], Z['ini']
else:
    partes = []; ini = [0]
    for u in U['unidades']:
        g = Polygon(u['local']).buffer(0).buffer(10)
        m = rasterio.features.rasterize([(g, 1)], out_shape=(H, W), transform=tr, dtype='uint8', all_touched=True).astype(bool)
        f = np.flatnonzero(m); partes.append(f); ini.append(ini[-1] + len(f))
    idx = np.concatenate(partes).astype(np.int32); ini = np.array(ini)
    np.savez_compressed(CACHE, idx=idx, ini=ini)
NU = len(U['unidades'])
vul = np.array([u['vuln'] for u in U['unidades']])
rt = np.array([u['riesgo']['presente'] for u in U['unidades']])
pel_t = P['presente'].ravel()
# peligro de la tesis por unidad (máximo y P90 de C-03 en la unidad), para referencia
pt_max = np.array([pel_t[idx[ini[k]:ini[k + 1]]].max() if ini[k + 1] > ini[k] else 0 for k in range(NU)])
def kappa(a, b, k):
    m = np.zeros((k, k))
    for i in range(k):
        for j in range(k): m[i, j] = ((a == i + 1) & (b == j + 1)).sum()
    n = m.sum(); po = np.trace(m) / n; pe = (m.sum(0) * m.sum(1)).sum() / n / n
    return ((po - pe) / (1 - pe) if pe < 1 else 0.0), po
def kappa_pond(a, b, k=4):
    # kappa con pesos cuadráticos (clases ordinales)
    m = np.zeros((k, k))
    for i in range(k):
        for j in range(k): m[i, j] = ((a == i + 1) & (b == j + 1)).sum()
    n = m.sum(); w = np.array([[(i - j) ** 2 for j in range(k)] for i in range(k)]) / (k - 1) ** 2
    e = np.outer(m.sum(1), m.sum(0)) / n
    return 1 - (w * m).sum() / (w * e).sum()
ok = vul > 0
print('referencia: kappa riesgo C-04 vs matriz(peligro C-03 máx por unidad, V) =',
      round(kappa(np.array([MAT[h - 1][v - 1] if h > 0 and v > 0 else 1 for h, v in zip(pt_max, vul)])[ok], rt[ok], 4)[0], 3))
cand = [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0]
res = []
for f in sys.argv[1:]:
    R = np.load(f); hm = R['hmax'].ravel()
    h90 = np.array([np.percentile(hm[idx[ini[k]:ini[k + 1]]], 90) if ini[k + 1] > ini[k] else 0 for k in range(NU)])
    # puntos críticos: tirante máximo en 30 m
    pcs = []
    for c in U['criticos']:
        i = int((c['local'][0] + 2600) // 10); j = int((c['local'][1] + 4000) // 10)
        pcs.append(float(R['hmax'][max(0, j - 3):j + 4, max(0, i - 3):i + 4].max()))
    pcs = np.array(pcs)
    mejor = None
    for u in itertools.combinations(cand, 3):
        hc = np.where(h90 < u[0], 1, np.where(h90 < u[1], 2, np.where(h90 < u[2], 3, 4)))
        rs = np.array([MAT[h - 1][v - 1] if v > 0 else 1 for h, v in zip(hc, vul)])
        k4, po4 = kappa(rs[ok], rt[ok], 4); kw = kappa_pond(rs[ok], rt[ok])
        k2, po2 = kappa((rs[ok] >= 3).astype(int) + 1, (rt[ok] >= 3).astype(int) + 1, 2)
        n3 = int((rs >= 3).sum()); n3t = int((rt >= 3).sum())
        sc = kw + 0.5 * k2 - 0.004 * abs(n3 - n3t)
        if mejor is None or sc > mejor[0]: mejor = (sc, u, dict(k4=round(k4, 3), kw=round(kw, 3), k2=round(k2, 3), po4=round(po4, 3), n3=n3, n3t=n3t))
    sc, u, d = mejor
    d['pc10'] = int((pcs >= 0.10).sum()); d['pc30'] = int((pcs >= 0.30).sum())
    p = R['params'] if 'params' in R.files else None
    res.append((sc, f, u, d))
    print(os.path.basename(f), 'params', None if p is None else [float(x) for x in p], '| umbrales', u, d, flush=True)
res.sort(key=lambda r: -r[0])
print('MEJOR', res[0][1], res[0][2], res[0][3])
# tabla para la documentación (orden de entrada)
sal = []
for sc, f, u, d in sorted(res, key=lambda r: sys.argv.index(r[1])):
    p = [float(x) for x in np.load(f)['params']]
    sal.append({'corrida': os.path.basename(f)[len('res_presente_'):-4], 'dCN': p[0], 'prof_cauce_m': p[1], 'n_bloque': p[2],
                'edificaciones_m': p[5] if len(p) > 5 else 0.0, 'umbrales': list(u), **{k: (float(v) if not isinstance(v, int) else v) for k, v in d.items()}})
json.dump(sal, open('sim/calibracion_unidades.json', 'w'), ensure_ascii=False, indent=1)
