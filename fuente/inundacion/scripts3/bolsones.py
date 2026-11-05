# Diagnóstico de bolsones: agua profunda lejos del cauce, por origen (patio cerrado por edificaciones, depresión del
# terreno del plano, o ninguno), y comparación entre corridas. Uso: python bolsones.py res1.npz [res2.npz ...]
import json, sys, numpy as np, shapely, rasterio.features, rasterio.transform
from scipy import ndimage
from shapely.geometry import Polygon
sys.path.insert(0, 'scripts3'); import sim2d
M = np.load('sim/malla.npz'); Z = M['Z'].astype(np.float64); rio = M['rio']; fb = M['fb']; fp = M['fp']
ed = (fb > 0.5) & ~rio
zb = Z.copy(); zb[rio] -= 1.0; zo = zb.copy(); zo[ed] += 3.0
dep_b = sim2d.relleno(zb) - zb; extra = (sim2d.relleno(zo) - zo) - dep_b
U = json.load(open('tesis/riesgo_unidades.json'))
tr = rasterio.transform.Affine(10, 0, -2600, 0, 10, -4000)
murb = rasterio.features.rasterize([(shapely.union_all([Polygon(u['local']).buffer(0) for u in U['unidades']]), 1)], out_shape=Z.shape, transform=tr, dtype='uint8').astype(bool)
d = ndimage.distance_transform_edt(~rio) * 10
patio0 = extra > 0.01
for f in sys.argv[1:]:
    hm = np.load(f)['hmax']
    lejos = murb & (d > 150) & ~ed
    p1 = (hm >= 1.0) & lejos
    lab, n = ndimage.label(p1)
    calle = fp > 0.3
    print('%-34s | >=1 m lejos del cauce: %4d celdas en %3d bolsones | en patios: %3d | en depresiones del plano: %3d | calles: %3d | área urbana >10 cm %.2f km2, >50 cm %.2f km2 | patios con >30 cm: %d' % (
        f.split('/')[-1], p1.sum(), n, (p1 & patio0).sum(), (p1 & ~patio0 & (dep_b > 0.1)).sum(), (p1 & calle).sum(),
        ((hm >= 0.1) & murb).sum() * 1e-4, ((hm >= 0.5) & murb).sum() * 1e-4, (patio0 & ~ed & ~calle & (hm >= 0.3)).sum()))
