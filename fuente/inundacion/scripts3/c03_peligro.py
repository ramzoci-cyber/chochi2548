# Clases de peligro (C-03) por escenario: imagen del panel -> clase por color -> ráster georreferenciado (marco OSM, ~34 m)
# y remuestreo a la malla del modelo (marco del plano, 10 m). Verificación con la tabla de la tesis (% del área urbana).
import json, sys, os, numpy as np, shapely, rasterio, rasterio.transform, rasterio.features
from PIL import Image
from shapely.geometry import Polygon
from scipy.ndimage import map_coordinates
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts2'))
from marco import plano_a_local_orig
G = json.load(open('tesis_pdf/c03_georref.json')); s, b, c = G['s'], G['b'], G['c']; PAN = G['paneles']
ESC = ['presente', 'cmip5_rcp45_2031_2060', 'cmip5_rcp45_2071_2100', 'cmip5_rcp85_2031_2060', 'cmip5_rcp85_2071_2100',
       'cmip6_ssp245_2031_2060', 'cmip6_ssp245_2071_2100', 'cmip6_ssp585_2031_2060', 'cmip6_ssp585_2071_2100']
TABLA = [21.6, 23.4, 24.1, 39.1, 97.3, 22.6, 46.3, 23.0, 48.3]          # % de la ciudad en peligro alto o muy alto (tesis)
TABLA_C = [6.1, 8.0, 9.5, 12.4, 95.6, 7.7, 22.1, 7.8, 28.8]              # % de la cuenca
COL = np.array([[169, 209, 142], [255, 230, 153], [244, 177, 131], [192, 0, 0]], float)   # bajo, medio, alto, muy alto
U = json.load(open('tesis/riesgo_unidades.json')); Gu = U['georref']
D = json.load(open('tesis_pdf/c04_obj.json'))
urb = shapely.union_all([Polygon(np.c_[Gu['a'] * np.array(o['pts'])[:, 0] + Gu['b'], -Gu['a'] * np.array(o['pts'])[:, 1] + Gu['c']]).buffer(0.5) for o in D['obj'] if o['pan'] == 0]).buffer(-0.5)
# malla del modelo (marco del plano) a 10 m: centros
W, H, CEL = 520, 800, 10.0
xs = -2600 + 5 + 10 * np.arange(W); zs = -4000 + 5 + 10 * np.arange(H)
XX, ZZ = np.meshgrid(xs, zs)
xo, zo = plano_a_local_orig(XX.ravel(), ZZ.ravel()); Eo, No = xo + 424400, 8738400 - zo        # en marco OSM
salida = {}
for k, e in enumerate(ESC):
    im = np.asarray(Image.open(f'tesis_pdf/img/c03-{4 + 4 * k:03d}.png').convert('RGB')).astype(float)
    m = np.asarray(Image.open(f'tesis_pdf/img/c03-{5 + 4 * k:03d}.png')).astype(float)
    d = ((im[:, :, None, :] - COL[None, None]) ** 2).sum(-1)
    cls = (np.argmin(d, -1) + 1).astype(np.uint8); cls[m < 128] = 0
    hgt, wid = cls.shape
    x0, y0, x1, y1 = PAN[k]; dx, dy = x0 - PAN[0][0], y0 - PAN[0][1]
    # píxel (col, fila) -> punto PDF -> UTM (centro del píxel)
    ppx = (x1 - x0) / wid; ppy = (y1 - y0) / hgt
    tr = rasterio.transform.Affine(s * ppx, 0, s * (x0 - dx) + b, 0, -s * ppy, -s * (y0 - dy) + c)
    if k == 0:
        with rasterio.open('tesis/peligro_presente_cuenca.tif', 'w', driver='GTiff', height=hgt, width=wid, count=1, dtype='uint8', crs='EPSG:32718', transform=tr, nodata=0, compress='deflate') as r: r.write(cls, 1)
    # % del área urbana y de la cuenca en alto/muy alto
    murb = rasterio.features.rasterize([(urb, 1)], out_shape=cls.shape, transform=tr, dtype='uint8').astype(bool)
    v = cls[murb & (cls > 0)]; vc = cls[cls > 0]
    pu = 100 * (v >= 3).mean(); pc = 100 * (vc >= 3).mean()
    # remuestreo (vecino más cercano) a la malla del modelo
    inv = ~tr
    col_, fil_ = inv * (Eo, No)
    ci = np.floor(col_).astype(int); fi = np.floor(fil_).astype(int)
    ok = (ci >= 0) & (ci < wid) & (fi >= 0) & (fi < hgt)
    g = np.zeros(W * H, np.uint8); g[ok] = cls[fi[ok], ci[ok]]
    salida[e] = g.reshape(H, W)
    print('%-24s ciudad alto+muy alto %5.1f %% (tesis %4.1f) | cuenca %5.1f %% (tesis %4.1f) | celdas del modelo con dato %d' % (e, pu, TABLA[k], pc, TABLA_C[k], (salida[e] > 0).sum()))
np.savez_compressed('tesis/peligro_malla10.npz', **salida)
