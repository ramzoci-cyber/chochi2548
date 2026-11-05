# Unidades de riesgo de la tesis (C-04): geometría georreferenciada (marco OSM y marco del plano), clase de riesgo en los
# 9 mapas (presente + 8 escenarios) y vulnerabilidad (exposición); 15 puntos críticos de inundación.
import json, sys, os, pdfplumber, numpy as np, shapely
from shapely.geometry import Polygon, Point, mapping
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts2'))
from marco import local_a_plano
D = json.load(open('tesis_pdf/c04_obj.json')); G = json.load(open('tesis_pdf/c04_georref.json'))
a, b, c = G['a'], G['b'], G['c']
PAN = D['paneles']
# ajuste fino: la malla de 1 ha queda centrada en múltiplos de 100 m + 50
def utm(x, y, k=0):
    dx, dy = PAN[k][0] - PAN[0][0], PAN[k][1] - PAN[0][1]
    return a * (np.asarray(x) - dx) + b, -a * (np.asarray(y) - dy) + c
celdas0 = [o for o in D['obj'] if o['pan'] == 0 and abs(o['w'] - 2.833) < 0.02 and abs(o['h'] - 2.833) < 0.02]
cc = np.array([utm(*np.array(o['pts']).mean(0)) for o in celdas0])
dE = 50 - np.median(cc[:, 0] % 100); dN = 50 - np.median(cc[:, 1] % 100)
b += dE; c += dN
print('corrección de fase de la malla: %.2f, %.2f m' % (dE, dN))
# orden de los paneles según su posición en el cuadro
ESC = ['presente', 'vulnerabilidad', 'cmip5_rcp45_2031_2060', 'cmip5_rcp45_2071_2100', 'cmip5_rcp85_2031_2060', 'cmip5_rcp85_2071_2100',
       'cmip6_ssp245_2031_2060', 'cmip6_ssp245_2071_2100', 'cmip6_ssp585_2031_2060', 'cmip6_ssp585_2071_2100']
# referencia: objetos del panel 0
ref = [o for o in D['obj'] if o['pan'] == 0]
def firma(o, k):
    p = np.array(o['pts']); dx, dy = PAN[k][0] - PAN[0][0], PAN[k][1] - PAN[0][1]
    return np.r_[p.mean(0) - [dx, dy], o['w'], o['h']]
F0 = np.array([firma(o, 0) for o in ref]); kd = cKDTree(F0)
clases = np.zeros((len(ref), len(ESC)), dtype=int)
for k in range(len(ESC)):
    obs = [o for o in D['obj'] if o['pan'] == k]
    Fk = np.array([firma(o, k) for o in obs])
    d, j = kd.query(Fk)
    assert d.max() < 0.05, (k, d.max())
    assert len(set(j)) == len(ref), (k, len(set(j)))
    for o, jj in zip(obs, j): clases[jj, k] = o['cls']
print('clases asignadas; máx. distancia de emparejamiento < 0,05 pt')
feats = []; unidades = []
for i, o in enumerate(ref):
    p = np.array(o['pts']); E, N = utm(p[:, 0], p[:, 1])
    poly = Polygon(np.c_[E, N]).buffer(0)
    xl, zl = local_a_plano(E - 424400, 8738400 - N)              # al marco del plano (el del modelo)
    es_celda = abs(o['w'] - 2.833) < 0.02 and abs(o['h'] - 2.833) < 0.02
    u = {'id': i, 'tipo': 'celda 1 ha' if es_celda else 'manzana', 'area_m2': round(poly.area, 1),
         'local': [[round(float(x), 2), round(float(z), 2)] for x, z in zip(xl, zl)],
         'vuln': int(clases[i, 1]), 'riesgo': {e: int(clases[i, k]) for k, e in enumerate(ESC) if e != 'vulnerabilidad'}}
    unidades.append(u)
print('unidades', len(unidades), 'celdas', sum(u['tipo'] == 'celda 1 ha' for u in unidades), 'manzanas', sum(u['tipo'] == 'manzana' for u in unidades))
for k, e in enumerate(ESC):
    v = clases[:, k]; print('%-26s bajo %3d medio %3d alto %3d muy alto %3d | alto+muy alto %d' % (e, (v == 1).sum(), (v == 2).sum(), (v == 3).sum(), (v == 4).sum(), ((v >= 3)).sum()))
# puntos críticos (círculos negros de 3,97 pt) y estrella
pdf = pdfplumber.open('tesis_pdf/C04.pdf'); p = pdf.pages[0]
pts = []
for cobj in p.curves:
    col = cobj.get('non_stroking_color')
    if not cobj.get('fill') or not isinstance(col, (tuple, list)) or tuple(round(v, 3) for v in col) != (0.078, 0.078, 0.078): continue
    q = np.array([(float(x), float(y)) for x, y in cobj['pts']])
    if abs(np.ptp(q[:, 0]) - 3.97) < 0.05 and abs(np.ptp(q[:, 1]) - 3.97) < 0.05:
        cx, cy = (q[:, 0].min() + q[:, 0].max()) / 2, (q[:, 1].min() + q[:, 1].max()) / 2
        if PAN[0][0] <= cx <= PAN[0][2] and PAN[0][1] <= cy <= PAN[0][3]: pts.append((cx, cy))
pts = sorted(pts, key=lambda t: (t[1], t[0]))
criticos = []
for n, (x, y) in enumerate(pts, 1):
    E, N = utm(x, y); xl, zl = local_a_plano(np.array([E - 424400]), np.array([8738400 - N]))
    # unidad que lo contiene y su riesgo en cada mapa
    P = Point(E, N); dentro = [u for u, o in zip(unidades, ref) if Polygon(np.c_[utm(*np.array(o['pts']).T)]).buffer(0).buffer(1).contains(P)]
    criticos.append({'n': n, 'E_osm': round(float(E), 1), 'N_osm': round(float(N), 1), 'local': [round(float(xl[0]), 2), round(float(zl[0]), 2)],
                     'unidad': dentro[0]['id'] if dentro else None})
print('puntos críticos', len(criticos))
json.dump({'escenarios': [e for e in ESC if e != 'vulnerabilidad'], 'unidades': unidades, 'criticos': criticos,
           'georref': {'a': a, 'b': b, 'c': c, 'nota': 'E = a·x + b ; N = −a·y + c (x, y en puntos PDF del panel «Presente», marco OSM/Microsoft)'}},
          open('tesis/riesgo_unidades.json', 'w'), ensure_ascii=False)
