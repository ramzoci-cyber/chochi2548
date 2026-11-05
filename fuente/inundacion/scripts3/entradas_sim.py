# Insumos de la simulación en la malla del modelo (10 m, marco del plano): cota, CN, rugosidad, cauces;
# hietogramas de diseño (bloques alternos con la IDF de la tesis) e hidrogramas de entrada de las cuencas externas.
import json, sys, os, numpy as np, shapely, rasterio, rasterio.features, rasterio.transform, rasterio.warp
from rasterio.enums import Resampling
from shapely.geometry import shape, Polygon, LineString
from scipy.ndimage import map_coordinates
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts2'))
from marco import plano_a_local_orig
W, H, CEL = 520, 800, 10.0
tr_loc = rasterio.transform.Affine(CEL, 0, -2600, 0, CEL, -4000)          # local: x, z (z hacia el sur)
Z = np.load('plan/z10.npy').astype(np.float64)                              # cotas del plano (msnm)
# ---------------- cobertura (WorldCover) remuestreada a la malla local (centro de celda -> marco OSM -> UTM)
wc = rasterio.open('ext/wc/worldcover_utm10.tif'); WC = wc.read(1)
xs = -2595 + 10 * np.arange(W); zs = -3995 + 10 * np.arange(H); XX, ZZ = np.meshgrid(xs, zs)
xo, zo = plano_a_local_orig(XX.ravel(), ZZ.ravel()); E, N = xo + 424400, 8738400 - zo
cc, rr = ~wc.transform * (E, N)
cob = WC[np.clip(rr.astype(int), 0, WC.shape[0] - 1), np.clip(cc.astype(int), 0, WC.shape[1] - 1)].reshape(H, W)
# ---------------- edificios y calzadas del modelo (fracción por celda, supermuestreo 2,5 m)
C = json.load(open('plan/datos_base.json'))
EDF = json.load(open('plan/edificios_plano.json'))
blds = [Polygon(b['P']).buffer(0) for b in EDF if len(b['P']) >= 3]
tr4 = rasterio.transform.Affine(2.5, 0, -2600, 0, 2.5, -4000)
fb = rasterio.features.rasterize([(g, 1) for g in blds if not g.is_empty], out_shape=(H * 4, W * 4), transform=tr4, dtype='uint8').reshape(H, 4, W, 4).mean(axis=(1, 3))
CAL = json.load(open('plan/calles.json'))
def normales(c):
    d = np.gradient(c, axis=0); d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9); return np.c_[-d[:, 1], d[:, 0]]
pav = []
for s in CAL['calles']:
    c = np.array(s['c'])
    if len(c) < 2 or s['sp'] == 2: continue
    n = normales(c); el, er = np.array(s['el']), np.array(s['er'])
    pav.append(Polygon(np.r_[c + n * el[:, None], (c - n * er[:, None])[::-1]]).buffer(0))
fp = rasterio.features.rasterize([(g, 1) for g in pav if not g.is_empty], out_shape=(H * 4, W * 4), transform=tr4, dtype='uint8').reshape(H, 4, W, 4).mean(axis=(1, 3))
# ---------------- número de curva (CN, AMC II, suelo C) y rugosidad de Manning
CN_WC = {10: 73, 20: 77, 30: 79, 40: 85, 50: 92, 60: 91, 80: 100, 90: 95, 0: 79}
N_WC = {10: 0.10, 20: 0.07, 30: 0.045, 40: 0.05, 50: 0.035, 60: 0.035, 80: 0.03, 90: 0.06, 0: 0.045}
cn = np.vectorize(lambda v: CN_WC.get(int(v), 79))(cob).astype(np.float64)
nm = np.vectorize(lambda v: N_WC.get(int(v), 0.045))(cob).astype(np.float64)
imp = np.clip(fb + fp, 0, 1)
cn = cn * (1 - imp) + 98 * imp
nm = np.where(fp > 0.3, 0.016 + (nm - 0.016) * (1 - fp), nm)                  # calzadas
nm = nm + (0.20 - nm) * np.clip(fb, 0, 1)                                     # bloques edificados: rugosidad equivalente
# ---------------- cauces: ríos del modelo (OSM) -> máscara y ancho
rios = []
for g in C['agua']:
    if len(g['c']) > 1 and g['w'] >= 4: rios.append(LineString(g['c']).buffer(max(5.0, g['w'] / 2)))
mr = rasterio.features.rasterize([(g, 1) for g in rios], out_shape=(H, W), transform=tr_loc, dtype='uint8').astype(bool)
np.savez_compressed('sim/malla.npz', Z=Z, cn=cn, n=nm, cob=cob, fb=fb, fp=fp, rio=mr)
print('malla: CN medio %.1f | impermeable %.1f %% | celdas de cauce %d' % (cn.mean(), 100 * imp.mean(), mr.sum()))
# ---------------- hietogramas de diseño (bloques alternos de 10 min, IDF de la tesis; total = P24 del escenario)
LL = json.load(open('tesis/lluvia_diseno.json'))
ESC = LL['escenarios']
K0, mT, nD, T = 205.39, 0.1296, 0.75, 25.0
dt_b = 10.0; nb = int(1440 / dt_b)
dur = dt_b * np.arange(1, nb + 1)
prof = K0 * T ** mT / dur ** nD * dur / 60.0                     # lámina acumulada (mm) para cada duración
inc = np.diff(np.r_[0, prof])
orden = np.argsort(-inc)
bloques = np.zeros(nb); centro = nb // 2
pos = []                                                          # alterna izquierda y derecha del centro
for off in range(nb):
    for p_ in ((centro - off - 1, centro + off) if off else (centro,)):
        if 0 <= p_ < nb and p_ not in pos: pos.append(p_)
pos = pos[:nb]
for k, p_ in enumerate(pos): bloques[p_] = inc[k]
forma = bloques / bloques.sum()
hiet = {}
for k, e in enumerate(ESC):
    P_dom = LL['plaza_tabla'][k]
    hiet[e] = {'P24': P_dom, 'mm10': (forma * P_dom).round(4).tolist()}
print('hietograma: pico de 10 min = %.1f %% de la P24 (presente %.2f mm en 10 min)' % (100 * forma.max(), forma.max() * 37.2))
# ---------------- hidrogramas de entrada (SCS-CN + hidrograma unitario adimensional del SCS, tc de Kirpich)
AP = json.load(open('ext/aportes.json'))
h = np.load('ext/hidro30.npz'); Zg, D8, acc = h['Z'], h['D8'], h['acc']; E0g, N1g, Rg = float(h['E0']), float(h['N1']), float(h['R'])
lab = np.load('ext/aportes_lab.npy')
DR = [0, 1, 1, 1, 0, -1, -1, -1]; DC = [1, 1, 0, -1, -1, -1, 0, 1]
UH_t = np.array([0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4, 4.5, 5])
UH_q = np.array([0, .03, .1, .19, .31, .47, .66, .82, .93, .99, 1, .99, .93, .86, .78, .68, .56, .46, .39, .33, .28, .207, .147, .107, .077, .055, .04, .029, .021, .015, .011, .005, 0])
wcG = rasterio.open('ext/wc/worldcover_utm10.tif')
entradas = []
for a in AP:
    if a['area_km2'] < 1.0: continue
    n = a['n']; m = lab == n
    # longitud de flujo: distancia por D8 hasta la salida de la cuenca externa (máxima)
    rr0, cc0 = np.nonzero(m)
    dist = {}
    # celda de salida (externa) = la etiquetada más cercana al punto de entrada
    ia = np.argmax(acc[rr0, cc0]); s0 = (int(rr0[ia]), int(cc0[ia]))      # salida de la cuenca externa = mayor acumulación
    from collections import deque
    q = deque([s0]); dist[s0] = 0.0
    while q:
        r, c = q.popleft()
        for k in range(8):
            r2, c2 = r - DR[k], c - DC[k]
            if 0 <= r2 < m.shape[0] and 0 <= c2 < m.shape[1] and m[r2, c2] and D8[r2, c2] == k and (r2, c2) not in dist:
                dist[(r2, c2)] = dist[(r, c)] + Rg * (1.4142 if k % 2 else 1.0); q.append((r2, c2))
    far = max(dist, key=dist.get); L = dist[far]
    Sl = max(0.005, (Zg[far] - Zg[s0]) / max(L, 1))
    tc = 0.0195 * L ** 0.77 * Sl ** -0.385                            # Kirpich (min)
    # CN medio de la cuenca externa (WorldCover)
    poly = shape(a['poly'])
    mk = rasterio.features.rasterize([(poly, 1)], out_shape=WC.shape, transform=wcG.transform, dtype='uint8').astype(bool)
    vals = WC[mk]; cn_c = float(np.mean([CN_WC.get(int(v), 79) for v in vals[vals > 0]])) if (vals > 0).any() else 79.0
    xl, zl = a['local']
    entradas.append({'n': n, 'local': [xl, zl], 'area_km2': a['area_km2'], 'L_km': round(float(L) / 1000, 2), 'S': round(float(Sl), 4), 'tc_min': round(float(tc), 1), 'CN': round(cn_c, 1)})
print('entradas:', [(e['n'], e['area_km2'], e['L_km'], e['tc_min'], e['CN']) for e in entradas])
def hidrograma(area, tc, cnv, P24_cat, forma, dcn=0.0):
    cnv = min(99.0, cnv + dcn)
    S = 25400.0 / cnv - 254.0; Ia = 0.2 * S
    Pc = np.cumsum(forma * P24_cat); Qc = np.where(Pc > Ia, (Pc - Ia) ** 2 / (Pc - Ia + S), 0.0)
    Pe = np.diff(np.r_[0, Qc])                                        # mm por bloque de 10 min
    D = dt_b / 60.0; tp = D / 2 + 0.6 * tc / 60.0                     # h
    qp = 2.08 * area / tp                                             # m3/s por cm de escorrentía
    tt = np.arange(0, 5 * tp + 1e-9, D)
    uh = np.interp(tt / tp, UH_t, UH_q) * qp / 10.0                   # m3/s por mm
    Q = np.convolve(Pe, uh)[:nb + 72]
    return Q, float(Qc[-1])
json.dump({'escenarios': ESC, 'hietogramas': hiet, 'entradas': entradas, 'dt_bloque_min': dt_b, 'CN_WC': CN_WC, 'N_WC': N_WC}, open('sim/entradas.json', 'w'))
# ejemplo de caudales pico (presente y peor escenario)
for k, e in enumerate(ESC):
    f = LL['plaza_tabla'][k] / LL['plaza_mapa'][e]
    picos = []
    for en in entradas:
        Pm = LL['aportes'][e].get(str(en['n'])) or LL['plaza_mapa'][e]
        Q, R_ = hidrograma(en['area_km2'], en['tc_min'], en['CN'], Pm * f, forma)
        picos.append((en['n'], round(float(Q.max()), 1), round(R_, 1)))
    print('%-24s caudales pico (m3/s, escorrentía mm): %s' % (e, picos[:4]))
