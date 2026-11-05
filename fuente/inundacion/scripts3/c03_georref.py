# Georreferencia los paneles del cuadro C-03 (1:400 000): estrella de la Plaza + ajuste del contorno del «área urbana
# evaluada» contra la unión de las unidades de riesgo de C-04 (ya georreferenciadas). Sirve también para C-01 y C-02.
import json, sys, pdfplumber, numpy as np, shapely
from shapely.geometry import Polygon, LineString
from scipy.spatial import cKDTree
pdfp, salida = sys.argv[1], sys.argv[2]
p = pdfplumber.open(pdfp).pages[0]
pan = []
for i in p.images:
    if i['srcsize'][0] in (966, 1088) and i['srcsize'][1] in (660, 742):
        b = (round(i['x0'], 2), round(i['top'], 2), round(i['x1'], 2), round(i['bottom'], 2))
        if b not in pan: pan.append(b)
P0 = pan[0]
estrella = None; contorno = []
for c in p.curves + p.lines:
    q = np.array([(float(x), float(y)) for x, y in (c.get('pts') or [])]) if c.get('pts') else None
    if q is None or len(q) < 2: continue
    cx, cy = q.mean(0)
    if not (P0[0] <= cx <= P0[2] and P0[1] <= cy <= P0[3]): continue
    nf = c.get('non_stroking_color'); sc = c.get('stroking_color')
    if c.get('fill') and isinstance(nf, (tuple, list)) and tuple(round(v, 3) for v in nf) == (0.0, 0.0, 0.0) and len(q) == 11:
        estrella = ((q[:, 0].min() + q[:, 0].max()) / 2, (q[:, 1].min() + q[:, 1].max()) / 2)
    if c.get('stroke') and isinstance(sc, (tuple, list)) and tuple(round(v, 3) for v in sc) == (0.275, 0.275, 0.275): contorno.append(q)
print('paneles', len(pan), 'estrella', estrella, 'trazos del área urbana', len(contorno))
U = json.load(open('tesis/riesgo_unidades.json'))
G = U['georref']; a4, b4, c4 = G['a'], G['b'], G['c']
# contorno de la unión de unidades en UTM (marco OSM)
D = json.load(open('tesis_pdf/c04_obj.json'))
polys = [Polygon(np.c_[a4 * np.array(o['pts'])[:, 0] + b4, -a4 * np.array(o['pts'])[:, 1] + c4]).buffer(0.5) for o in D['obj'] if o['pan'] == 0]
Uu = shapely.union_all(polys).buffer(-0.5)
borde = shapely.get_coordinates(Uu.boundary)
kd = cKDTree(borde)
Q = np.vstack([np.array(LineString(q).segmentize(0.5).coords) for q in contorno])
E0, N0 = 424981.0, 8737499.0                      # Plaza de Armas (marco OSM del modelo original)
s = 4 * a4
b, c = E0 - estrella[0] * s, N0 + estrella[1] * s
for it in range(25):
    E = s * Q[:, 0] + b; N = -s * Q[:, 1] + c
    d, j = kd.query(np.c_[E, N]); ok = d < (120 if it < 8 else 60)
    T = borde[j[ok]]
    A = np.r_[np.c_[Q[ok, 0], np.ones(ok.sum()), np.zeros(ok.sum())], np.c_[-Q[ok, 1], np.zeros(ok.sum()), np.ones(ok.sum())]]
    s, b, c = np.linalg.lstsq(A, np.r_[T[:, 0], T[:, 1]], rcond=None)[0]
    if it in (4, 12, 24): print('iter', it, 'puntos', ok.sum(), 'dist mediana %.1f m' % np.median(d[ok]), 'escala %.3f m/pt (nominal %.3f)' % (s, 4 * 25.4 / 72 * 100))
print('estrella -> Plaza: (%.1f, %.1f) m' % (s * estrella[0] + b - E0, -s * estrella[1] + c - N0))
json.dump({'s': s, 'b': b, 'c': c, 'paneles': pan, 'nota': 'E = s·(x − dx) + b ; N = −s·(y − dy) + c ; (dx, dy) = origen del panel − origen del panel 0'}, open(salida, 'w'))
