# Georreferencia los paneles del cuadro C-04 (1:100 000): estrella de la Plaza de Armas como punto inicial y ajuste fino
# (ICP de semejanza sin rotación) de los centroides de las manzanas de la tesis contra las manzanas del Plano Total 2025.
import json, sys, os, pickle, numpy as np, shapely
from shapely.geometry import Polygon
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts2'))
from marco import plano_a_local_orig
D = json.load(open('tesis_pdf/c04_obj.json'))
S = 25.4 / 72 / 1000 * 100000            # m por punto a 1:100 000
ESTRELLA = (405.56, 221.85)               # centroide de la estrella (panel 0)
C0 = json.load(open('orig/datos_clean.json'))
E0, N0 = C0['plaza_c'][0] + 424400, 8738400 - C0['plaza_c'][1]          # Plaza (marco OSM del modelo original)
pan0 = D['paneles'][0]
uni = [o for o in D['obj'] if o['pan'] == 0]
def centroide(pts): 
    q = Polygon(pts); return (q.centroid.x, q.centroid.y, abs(q.area)) if q.is_valid and q.area > 0 else (np.mean(np.array(pts)[:, 0]), np.mean(np.array(pts)[:, 1]), 0)
cen = np.array([centroide(o['pts']) for o in uni])
celdas = np.array([abs(o['w'] - 2.833) < 0.02 and abs(o['h'] - 2.833) < 0.02 for o in uni])
# manzanas del plano en el marco OSM (local original) -> UTM
MZ = pickle.load(open('plan/manzanas_crudo.pkl', 'rb'))['pols']
Mc = []
for m in MZ:
    if 400 < m.area < 20000:
        x, z = plano_a_local_orig(np.array([m.centroid.x - 424400]), np.array([8738400 - m.centroid.y]))
        Mc.append((x[0] + 424400, 8738400 - z[0]))
Mc = np.array(Mc); kd = cKDTree(Mc)
# manzanas pequeñas de la tesis (no celdas), área en m2
peq = (~celdas) & (cen[:, 2] * S * S > 1500) & (cen[:, 2] * S * S < 15000)
P = cen[peq, :2]
a, b, c = S, E0 - ESTRELLA[0] * S, N0 + ESTRELLA[1] * S       # E = a x + b ; N = -a y + c
for it in range(30):
    E = a * P[:, 0] + b; N = -a * P[:, 1] + c
    d, j = kd.query(np.c_[E, N])
    lim = 40 if it < 10 else 20
    ok = d < lim
    # mínimos cuadrados para a, b, c con pares (x,y)->(E',N')
    Q = Mc[j[ok]]; x = P[ok, 0]; y = P[ok, 1]
    A = np.r_[np.c_[x, np.ones_like(x), np.zeros_like(x)], np.c_[-y, np.zeros_like(y), np.ones_like(y)]]
    B = np.r_[Q[:, 0], Q[:, 1]]
    a, b, c = np.linalg.lstsq(A, B, rcond=None)[0]
    if it % 5 == 4 or it == 29: print('iter', it, 'pares', ok.sum(), 'dist mediana %.2f m' % np.median(d[ok]), 'escala %.4f (nominal %.4f)' % (a, S))
desplaz = (a * ESTRELLA[0] + b - E0, -a * ESTRELLA[1] + c - N0)
print('la estrella queda a (%.1f, %.1f) m de la Plaza del modelo' % desplaz)
# fase de la malla de 1 ha
cx = a * cen[celdas, 0] + b; cy = -a * cen[celdas, 1] + c
print('centros de celdas mod 100 m: E %.1f ± %.1f, N %.1f ± %.1f' % (np.median(cx % 100), np.std(cx % 100), np.median(cy % 100), np.std(cy % 100)))
json.dump({'a': a, 'b': b, 'c': c, 'paneles': D['paneles']}, open('tesis_pdf/c04_georref.json', 'w'))
