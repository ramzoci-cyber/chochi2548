# Lluvia de diseño (P24, 25 años) por escenario desde las isoyetas del cuadro C-01: clase de color -> mm (centro de clase),
# media en cada cuenca externa (aportes) y en el dominio; contraste con la tabla (Plaza de Armas) del cuadro.
import json, numpy as np, shapely, rasterio, rasterio.transform, rasterio.features
from PIL import Image
from shapely.geometry import shape, Point
G = json.load(open('tesis_pdf/c01_georref.json')); s, b, c = G['s'], G['b'], G['c']; PAN = G['paneles']
ESC = ['presente', 'cmip5_rcp45_2031_2060', 'cmip5_rcp45_2071_2100', 'cmip5_rcp85_2031_2060', 'cmip5_rcp85_2071_2100',
       'cmip6_ssp245_2031_2060', 'cmip6_ssp245_2071_2100', 'cmip6_ssp585_2031_2060', 'cmip6_ssp585_2071_2100']
PLAZA_TABLA = [37.2, 42.4, 42.6, 45.7, 63.6, 41.4, 50.2, 41.5, 50.7]
LEY = np.array([(255, 255, 217), (237, 248, 177), (199, 233, 180), (127, 205, 187), (65, 182, 196), (29, 145, 192), (34, 94, 168), (37, 52, 148), (8, 29, 88), (4, 14, 44)], float)
MED = np.array([38.0, 42, 46, 50, 54, 58, 62, 66, 70, 74])
AP = json.load(open('ext/aportes.json'))
res = {'escenarios': ESC, 'plaza_tabla': PLAZA_TABLA, 'aportes': {}, 'dominio': {}, 'plaza_mapa': {}}
for k, e in enumerate(ESC):
    im = np.asarray(Image.open(f'tesis_pdf/img/c01-{4 + 4 * k:03d}.png').convert('RGB')).astype(float)
    m = np.asarray(Image.open(f'tesis_pdf/img/c01-{5 + 4 * k:03d}.png')).astype(float)
    d = ((im[:, :, None, :] - LEY[None, None]) ** 2).sum(-1)
    P = MED[np.argmin(d, -1)]; P[m < 128] = np.nan
    hgt, wid = P.shape; x0, y0, x1, y1 = PAN[k]; dx, dy = x0 - PAN[0][0], y0 - PAN[0][1]
    tr = rasterio.transform.Affine(s * (x1 - x0) / wid, 0, s * (x0 - dx) + b, 0, -s * (y1 - y0) / hgt, -s * (y0 - dy) + c)
    inv = ~tr
    def valor(E, N, rad=3):
        cc, rr = inv * (E, N); cc, rr = int(cc), int(rr)
        v = P[max(0, rr - rad):rr + rad + 1, max(0, cc - rad):cc + rad + 1]; return float(np.nanmean(v))
    res['plaza_mapa'][e] = round(valor(424981, 8737499), 1)
    dom = rasterio.features.rasterize([(shapely.box(421800, 8734400, 427000, 8742400), 1)], out_shape=P.shape, transform=tr, dtype='uint8').astype(bool)
    res['dominio'][e] = round(float(np.nanmean(P[dom])), 1)
    res['aportes'][e] = {}
    for a in AP:
        if a['area_km2'] < 1: continue
        msk = rasterio.features.rasterize([(shape(a['poly']), 1)], out_shape=P.shape, transform=tr, dtype='uint8').astype(bool)
        v = P[msk]; v = v[np.isfinite(v)]
        res['aportes'][e][str(a['n'])] = round(float(v.mean()), 1) if len(v) else None
    print('%-24s Plaza mapa %.1f (tabla %.1f) | dominio %.1f | cuencas externas %s' % (e, res['plaza_mapa'][e], PLAZA_TABLA[k], res['dominio'][e], res['aportes'][e]))
json.dump(res, open('tesis/lluvia_diseno.json', 'w'), indent=1)
