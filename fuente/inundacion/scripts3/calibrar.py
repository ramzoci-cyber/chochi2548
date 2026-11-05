# Compara la simulación con el mapa de peligro de la tesis (C-03, presente) en la zona urbana evaluada (unidades de C-04)
# y con los 15 puntos críticos; busca los umbrales de tirante que mejor reproducen la zonificación.
import json, sys, numpy as np, shapely, rasterio.features, rasterio.transform, itertools
from shapely.geometry import Polygon
from scipy.ndimage import maximum_filter, uniform_filter
U = json.load(open('tesis/riesgo_unidades.json'))
P = np.load('tesis/peligro_malla10.npz')
tr = rasterio.transform.Affine(10, 0, -2600, 0, 10, -4000)
H, W = 800, 520
urb = shapely.union_all([Polygon(u['local']).buffer(0) for u in U['unidades']])
murb = rasterio.features.rasterize([(urb, 1)], out_shape=(H, W), transform=tr, dtype='uint8').astype(bool)
def clases_sim(hmax, vmax, umb, agreg=3):
    """clase de peligro simulada: tirante máximo agregado a ~30 m (máximo en ventana agreg x agreg) con umbrales (h1, h2, h3)"""
    hv = maximum_filter(hmax, size=agreg) if agreg > 1 else hmax
    c = np.ones_like(hv, dtype=np.uint8)
    c[hv >= umb[0]] = 2; c[hv >= umb[1]] = 3; c[hv >= umb[2]] = 4
    return c
def kappa(a, b, k=4):
    m = np.zeros((k, k))
    for i in range(k):
        for j in range(k): m[i, j] = ((a == i + 1) & (b == j + 1)).sum()
    n = m.sum(); po = np.trace(m) / n; pe = (m.sum(0) * m.sum(1)).sum() / n / n
    return (po - pe) / (1 - pe), po
def evaluar(hmax, vmax, umb, ref='presente', agreg=3, verbose=False):
    cs = clases_sim(hmax, vmax, umb, agreg); ct = P[ref]
    m = murb & (ct > 0)
    a, b = cs[m], ct[m]
    k4, po4 = kappa(a, b, 4)
    a2 = (a >= 3).astype(int) + 1; b2 = (b >= 3).astype(int) + 1
    k2, po2 = kappa(a2, b2, 2)
    pa = 100 * (a >= 3).mean(); pb = 100 * (b >= 3).mean()
    # puntos críticos: clase simulada en un radio de 30 m
    pc = 0
    for c in U['criticos']:
        i = int((c['local'][0] + 2600) / 10); j = int((c['local'][1] + 4000) / 10)
        if cs[max(0, j - 3):j + 4, max(0, i - 3):i + 4].max() >= 3: pc += 1
    return {'k4': k4, 'po4': po4, 'k2': k2, 'po2': po2, 'pct_sim': pa, 'pct_tesis': pb, 'criticos': pc}
def mejores_umbrales(hmax, vmax, ref='presente'):
    cand = [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5]
    mejor = None
    for u in itertools.combinations(cand, 3):
        r = evaluar(hmax, vmax, u, ref)
        sc = r['k2'] + 0.5 * r['k4'] - 0.02 * abs(r['pct_sim'] - r['pct_tesis'])
        if mejor is None or sc > mejor[0]: mejor = (sc, u, r)
    return mejor
if __name__ == '__main__':
    f = sys.argv[1]
    R = np.load(f)
    s, u, r = mejores_umbrales(R['hmax'], R['vmax'])
    print(f, 'umbrales', u, {k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()})
