# Reajusta el Jr. Chanchamayo al plano: eje en el marco del plano, líneas de propiedad (fachadas) desde las manzanas del
# Plano Total 2025, linderos de lotes en los quiebres del contorno de manzana, perfil longitudinal con las curvas del plano.
import json, pickle, sys, os, numpy as np, shapely
from shapely.geometry import LineString, Point
from scipy.ndimage import gaussian_filter1d, median_filter, map_coordinates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marco import local_a_plano
CH = json.load(open('data/chanchamayo.json'))
e = np.load('data/eje1m.npz')
S = e['S']; N = len(S)
cx, cz = local_a_plano(e['cx'], e['cz'])
LIN = [shapely.transform(g, lambda a: np.c_[a[:, 0] - 424400, 8738400 - a[:, 1]]) for g in pickle.load(open('plan/manzanas_crudo.pkl', 'rb'))['lineas']]
# los equipamientos (mercado, colegios, recreación, salud, parques) tienen su lindero en capas propias del plano
PT = pickle.load(open('planos/plano_total_wcs.pkl', 'rb'))
for capa in ('E.MERCADO', 'E.EDUCACION', 'E.OTROS USOS', 'E.RECREACION.', 'E.SALUD', 'parque', 'PARQUES'):
    for d in PT.get(capa, []):
        if 'pts' in d and len(d['pts']) > 1:
            a = np.array(d['pts'])[:, :2]
            if np.isfinite(a).all() and 424700 < a[:, 0].mean() < 425700 and 8737300 < a[:, 1].mean() < 8738400:
                g = LineString(np.c_[a[:, 0] - 424400, 8738400 - a[:, 1]])
                if g.length > 0.5: LIN.append(g)
arb = shapely.STRtree(LIN)
fE0 = np.array(CH['fE']); fO0 = np.array(CH['fO'])
hueco = {1: fE0 < 0, -1: fO0 < 0}            # cruces (sin fachada) del modelo anterior
def marco(cx, cz):
    tx = np.gradient(cx); tz = np.gradient(cz); n = np.hypot(tx, tz); tx /= n; tz /= n
    return tx, tz, -tz, tx
def rayos(cx, cz, nx, nz, lado, rmax=16.0):
    P = np.c_[cx, cz]; F = P + np.c_[nx, nz] * rmax * lado
    R = shapely.linestrings(np.stack([P, F], 1))
    ia, ib = arb.query(R, predicate='intersects')
    d = shapely.distance(shapely.points(P[ia]), shapely.intersection(R[ia], np.array(LIN, dtype=object)[ib]))
    out = np.full(len(P), np.nan)
    for i, v in zip(ia, d):
        if not (out[i] <= v): out[i] = v
    return out
# 1) recentrar el eje entre las líneas del plano (sólo donde hay fachada en ambos lados)
for it in range(2):
    tx, tz, nx, nz = marco(cx, cz)
    oE = rayos(cx, cz, nx, nz, 1); oO = rayos(cx, cz, nx, nz, -1)
    ok = np.isfinite(oE) & np.isfinite(oO) & ~hueco[1] & ~hueco[-1] & (oE + oO < 14) & (oE + oO > 5)
    off = np.where(ok, (oE - oO) / 2, np.nan)
    g = np.isfinite(off)
    offi = np.interp(S, S[g], off[g]); offs = np.clip(gaussian_filter1d(offi, 12), -2.5, 2.5)
    cx = cx + nx * offs; cz = cz + nz * offs
    print('recentrado', it, 'desplazamiento medio %.2f m, máx %.2f m' % (np.abs(offs).mean(), np.abs(offs).max()))
# remuestrear a 1 m exacto
d = np.r_[0, np.cumsum(np.hypot(np.diff(cx), np.diff(cz)))]; L = float(d[-1])
S2 = np.linspace(0, L, int(round(L)) + 1)
cx = np.interp(S2, d, cx); cz = np.interp(S2, d, cz); S = S2; N = len(S)
tx, tz, nx, nz = marco(cx, cz)
def remap(a): return np.interp(np.linspace(0, len(a) - 1, N), np.arange(len(a)), a)
hE = remap(hueco[1].astype(float)) > 0.5; hO = remap(hueco[-1].astype(float)) > 0.5
oE = rayos(cx, cz, nx, nz, 1); oO = rayos(cx, cz, nx, nz, -1)
print('longitud del eje %.1f m (antes %.1f)' % (L, CH['L']))
# 2) líneas de fachada: plano donde existe y es coherente; si no, la del modelo anterior
def linea(o, viejo, hue):
    v = np.where(viejo > 0, viejo, np.nan); v = remap(np.nan_to_num(v, nan=-1)); v[v < 0] = np.nan
    usar = np.isfinite(o) & ~hue & (o > 2.0) & (o < 12.5)
    # descartar saltos aislados (> 2,5 m respecto a la mediana local)
    med = median_filter(np.where(usar, o, np.nan_to_num(v, nan=5.0)), size=9, mode='nearest')
    usar &= np.abs(o - med) < 2.5
    f = np.where(usar, o, v)
    f = np.where(hue, -1.0, np.where(np.isfinite(f), f, 5.0))
    return f, usar
fE, uE = linea(oE, fE0, hE); fO, uO = linea(oO, fO0, hO)
print('fachada desde el plano: E %.0f %%, O %.0f %% de la longitud con fachada' % (uE[~hE].mean() * 100, uO[~hO].mean() * 100))
W = np.where((fE > 0) & (fO > 0), fE + fO, np.nan)
print('ancho entre líneas de propiedad (plano): p10 %.2f  p50 %.2f  p90 %.2f m' % tuple(np.nanpercentile(W, [10, 50, 90])))
# 3) quiebres del contorno (linderos) para ajustar los cortes entre lotes
def quiebres(f, usar):
    q = []
    for i in range(1, N - 1):
        if usar[i - 1] and usar[i + 1] and abs(f[i + 1] - f[i - 1]) > 0.35: q.append(S[i])
    return np.array(q)
QE, QO = quiebres(fE, uE), quiebres(fO, uO)
escala = L / CH['L']
lotes = CH['lotes']; cercos = CH['cercos']
for l in lotes + cercos:
    l['s0'] = round(l['s0'] * escala, 2); l['s1'] = round(l['s1'] * escala, 2)
movidos = 0
for lado, Q in ((1, QE), (-1, QO)):
    items = sorted([l for l in lotes + cercos if l['lado'] == lado], key=lambda l: l['s0'])
    for a, b in zip(items[:-1], items[1:]):
        if abs(a['s1'] - b['s0']) > 0.6 or not len(Q): continue
        k = np.argmin(np.abs(Q - a['s1']))
        if abs(Q[k] - a['s1']) < 2.5 and (Q[k] - a['s0']) > 3.5 and (b['s1'] - Q[k]) > 3.5:
            a['s1'] = b['s0'] = round(float(Q[k]), 2); movidos += 1
print('linderos movidos a quiebres del plano:', movidos)
def fval(s, lado):
    i = int(np.clip(round(s), 0, N - 1)); v = (fE if lado == 1 else fO)[i]
    return float(v) if v > 0 else None
for l in lotes + cercos:
    a = fval(l['s0'] + 0.6, l['lado']); b = fval(l['s1'] - 0.6, l['lado'])
    if a is not None and b is not None: l['f'] = [round(a, 2), round(b, 2)]
# 4) perfil longitudinal con el MDE del plano (curvas cada 5 m)
M5 = np.load('plan/mde5.npz'); Z5 = M5['Z']; ZMIN = json.load(open('orig/datos_clean.json'))['zmin']
y = map_coordinates(Z5, [(cz + 4000) / 5 - 0.5, (cx + 2600) / 5 - 0.5], order=1) - ZMIN
def pava_decreciente(v):
    res = []
    for x in list(-v):
        res.append([x, 1])
        while len(res) > 1 and res[-2][0] > res[-1][0]:
            a, b = res.pop(); c, dd = res.pop(); res.append([(a * b + c * dd) / (b + dd), b + dd])
    out = []
    for x, k in res: out += [x] * k
    return -np.array(out)
ys = gaussian_filter1d(pava_decreciente(y), 10, mode='nearest')
for k in range(1, N): ys[k] = min(ys[k], ys[k - 1] - 0.002 * (S[k] - S[k - 1]))
print('perfil (plano): %.2f -> %.2f msnm, caída %.2f m, pendiente media %.2f %%, máx dif con el MDE %.2f m' % (ys[0] + ZMIN, ys[-1] + ZMIN, ys[0] - ys[-1], (ys[0] - ys[-1]) / L * 100, np.abs(ys - y).max()))
# 5) reensamblar
CH['L'] = round(L, 2); CH['eje'] = [[round(float(a), 2), round(float(b), 2)] for a, b in zip(cx, cz)]
CH['y'] = [round(float(v), 3) for v in ys]; CH['fE'] = [round(float(v), 2) for v in fE]; CH['fO'] = [round(float(v), 2) for v in fO]
for k in ('caras', 'cuadras'):
    for c in CH[k]: c['s0'] = round(c['s0'] * escala, 1); c['s1'] = round(c['s1'] * escala, 1)
for c in CH['cruces']: c['s'] = round(c['s'] * escala, 1)
for k in ('postes', 'sumideros', 'vehiculos'):
    for c in CH[k]: c['s'] = round(c['s'] * escala, 1)
CH['buzones'] = [round(b * escala, 1) for b in CH['buzones']]
A = np.array(CH['A'], dtype=float); CH['A'] = [round(float(v)) for v in np.interp(np.linspace(0, len(A) - 1, N), np.arange(len(A)), A)]
B0 = json.load(open('plan/datos_base.json'))
eje = LineString(np.c_[cx, cz]); CH['sT01'] = round(float(eje.project(Point(B0['punto_critico']))), 1)
CH['plano'] = {'ancho_p50': round(float(np.nanpercentile(W, 50)), 2), 'ancho_p10': round(float(np.nanpercentile(W, 10)), 2), 'ancho_p90': round(float(np.nanpercentile(W, 90)), 2),
               'seccion': 'C3', 'total': 10.5, 'comp': [['V', 1.20], ['C', 0.40], ['VR', 7.30], ['C', 0.40], ['V', 1.20]],
               'cota_ini': round(float(ys[0] + ZMIN), 2), 'cota_fin': round(float(ys[-1] + ZMIN), 2)}
json.dump(CH, open('plan/chanchamayo.json', 'w'), ensure_ascii=False)
np.savez('plan/eje1m.npz', S=S, cx=cx, cz=cz, nx=nx, nz=nz, ys=ys, fE=fE, fO=fO, uE=uE, uO=uO)
print('T01 en s = %.1f m' % CH['sT01'])
