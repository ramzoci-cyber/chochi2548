# Ensambla los datos del modelo en el marco del plano: terreno con curvas del plano, edificios recortados a manzanas,
# calzadas y veredas según el plano, corredor del Jr. Chanchamayo reajustado, hitos, árboles, postes y red D8 de 5 m.
import json, base64, zlib, sys, os, heapq, numpy as np, shapely
from shapely.geometry import Polygon, Point, LineString
from scipy.ndimage import distance_transform_edt, map_coordinates, zoom
import rasterio.features, rasterio.transform
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marco import local_a_plano
C = json.load(open('plan/datos_base.json'))
W, H, CEL, ZMIN = C['W'], C['H'], C['celda'], C['zmin']; MX, MZ = W * CEL / 2, H * CEL / 2
def desinflar(a): return base64.b64encode(zlib.compress(np.ascontiguousarray(a).tobytes(), 9)).decode()
def inflar(b64, dt): return np.frombuffer(zlib.decompress(base64.b64decode(b64)), dtype=dt)
CH = json.load(open('plan/chanchamayo.json')); CAL = json.load(open('plan/calles.json')); MZS = json.load(open('plan/manzanas.json'))
e = np.load('plan/eje1m.npz'); S, cx, cz, nx, nz, ys, fE, fO = [e[k] for k in ('S', 'cx', 'cz', 'nx', 'nz', 'ys', 'fE', 'fO')]
N = len(S)
# ---------------- hitos al marco del plano
def mover(o):
    if isinstance(o, list) and o and isinstance(o[0], (int, float)) and len(o) == 2:
        x, z = local_a_plano(np.array([o[0]]), np.array([o[1]])); return [round(float(x[0]), 2), round(float(z[0]), 2)]
    if isinstance(o, list): return [mover(v) for v in o]
    if isinstance(o, dict): return {k: mover(v) for k, v in o.items()}
    return o
HI = mover(json.load(open('data/hitos_final.json'))); json.dump(HI, open('plan/hitos_plano.json', 'w'))
HI1 = mover(json.load(open('data/hitos.json')))
# ---------------- zona del corredor (calzada + lotes + cercos)
def P(s, o, lado):
    i = int(np.clip(round(s), 0, N - 1)); return (cx[i] + nx[i] * o * lado, cz[i] + nz[i] * o * lado)
def fval(s, lado):
    i = int(np.clip(round(s), 0, N - 1)); v = (fE if lado == 1 else fO)[i]; return v if v > 0 else 5.0
izq = [P(s, fval(s, 1) + 0.3, 1) for s in S]; der = [P(s, fval(s, -1) + 0.3, -1) for s in S[::-1]]
calle = Polygon(izq + der).buffer(0)
partes = [calle]
for l in CH['lotes']:
    s0, s1, lado = l['s0'], l['s1'], l['lado']; f0, f1 = l['f']; prof = l['ret'] + max(l['Dt'], l['D'])
    partes.append(Polygon([P(s0, f0, lado), P(s1, f1, lado), P(s1, f1 + prof, lado), P(s0, f0 + prof, lado)]).buffer(0.2))
for c in CH['cercos']:
    s0, s1, lado = c['s0'], c['s1'], c['lado']; f0, f1 = c['f']
    partes.append(Polygon([P(s0, f0, lado), P(s1, f1, lado), P(s1, f1 + 6, lado), P(s0, f0 + 6, lado)]).buffer(0.2))
zona = shapely.union_all(partes)
est = Polygon(HI1['estadio_stadium']).buffer(2); cat = Polygon(HI1['catedral']).buffer(1.5)
plaza = Polygon(C['plaza']).buffer(-0.5)
# ---------------- calzadas según el plano (sin el Jr. Chanchamayo, que tiene su calle detallada)
ejeCH = LineString(np.c_[cx, cz]); callesCH = calle.buffer(1.0)
def normales(c):
    d = np.gradient(c, axis=0); d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9); return np.c_[-d[:, 1], d[:, 0]]
calles = []; pav = []; quitadas = 0
for s in CAL['calles']:
    c = np.array(s['c'])
    if len(c) < 2: continue
    g = LineString(c)
    if g.length > 2 and g.intersection(callesCH).length / g.length > 0.6: quitadas += 1; continue
    if plaza.buffer(-2).contains(g.interpolate(0.5, normalized=True)) and s['cl'] == 6: quitadas += 1; continue
    n = normales(c); el, er = np.array(s['el']), np.array(s['er'])
    poly = Polygon(np.r_[c + n * el[:, None], (c - n * er[:, None])[::-1]]).buffer(0)
    calles.append(s); pav.append(poly)
PAV = shapely.union_all(pav); shapely.prepare(PAV)
print('calles', len(calles), 'quitadas (corredor/plaza)', quitadas)
# simplificar vértices (eje con DP 0,25 m + cambios de ancho > 0,25 m) para aligerar
def simplificar(c, el, er):
    keep = np.zeros(len(c), bool); keep[[0, -1]] = True
    def dp(i0, i1):
        if i1 <= i0 + 1: return
        a, b = c[i0], c[i1]; ab = b - a; L = np.hypot(*ab) or 1e-9
        t = np.clip(((c[i0 + 1:i1] - a) @ ab) / L ** 2, 0, 1)
        d = np.hypot(*(c[i0 + 1:i1] - (a + t[:, None] * ab)).T)
        dw = np.maximum(np.abs(el[i0 + 1:i1] - (el[i0] + (el[i1] - el[i0]) * t)), np.abs(er[i0 + 1:i1] - (er[i0] + (er[i1] - er[i0]) * t)))
        k = np.argmax(np.maximum(d / 0.25, dw / 0.25))
        if max(d[k] / 0.25, dw[k] / 0.25) > 1: keep[i0 + 1 + k] = True; dp(i0, i0 + 1 + k); dp(i0 + 1 + k, i1)
    dp(0, len(c) - 1)
    return keep
meta = []; nv = []; vv = []
for s in calles:
    c = np.array(s['c']); el = np.array(s['el']); er = np.array(s['er']); fl = np.array(s['fl']); fr = np.array(s['fr'])
    k = simplificar(c, el, er)
    meta.append({kk: s[kk] for kk in ('id', 'nombre', 'osm', 'plano', 'cl', 'clase', 'sp', 'pu', 'ancho', 'amin', 'amax', 'prop', 'secc', 'secc_h', 'prop_h', 'L')})
    meta[-1]['nc'] = len(s['cotas'])
    nv.append(int(k.sum())); vv.append(np.c_[c[k], el[k], er[k], fl[k], fr[k]])
VV = np.vstack(vv).astype(np.float32)
C['calles'] = {'meta': meta, 'n': desinflar(np.array(nv, dtype=np.uint16)), 'v': desinflar(VV)}
C['secciones'] = CAL['secciones']; C['locales'] = CAL['locales']
print('vértices de calzada', len(VV), 'KB', len(C['calles']['v']) // 1024)
# ---------------- veredas (sin las del corredor, la plaza y el estadio)
vmeta = []; vn = []; vv = []
for v in CAL['veredas']:
    p = np.array(v['p']); g = LineString(p); mid = g.interpolate(0.5, normalized=True)
    if g.distance(ejeCH) < 12 and calle.buffer(3).contains(mid): continue
    if plaza.buffer(6).contains(mid) or est.contains(mid): continue
    vmeta.append([v['w'], v['lado']]); vn.append(len(p)); vv.append(p)
C['veredas'] = {'meta': vmeta, 'n': desinflar(np.array(vn, dtype=np.uint16)), 'v': desinflar(np.vstack(vv).astype(np.float32))}
print('tramos de vereda', len(vmeta))
# ---------------- manzanas (para la ficha de manzana)
mm = []; mn = []; mv = []
for m in MZS:
    p = np.array(m['p'])
    if len(p) < 3: continue
    q = Polygon(p)
    lados = q.simplify(1.5)
    lp = np.array(lados.exterior.coords)[:-1] if lados.geom_type == 'Polygon' and not lados.is_empty else p.copy()
    # fusionar lados casi colineales (< 12°) y quitar vértices de lados muy cortos
    cambio = True
    while cambio and len(lp) > 3:
        cambio = False
        for j in range(len(lp)):
            a0, a1, a2 = lp[j - 1], lp[j], lp[(j + 1) % len(lp)]
            u, v = a1 - a0, a2 - a1
            ang = np.degrees(np.arccos(np.clip(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-9), -1, 1)))
            if ang < 12 or min(np.linalg.norm(u), np.linalg.norm(v)) < 1.0:
                lp = np.delete(lp, j, axis=0); cambio = True; break
    lp = np.r_[lp, lp[:1]]
    ls = [round(float(np.hypot(*(b - a))), 2) for a, b in zip(lp[:-1], lp[1:])]
    mm.append({'id': m['id'], 'a': m['area'], 'per': m['per'], 'nl': len(lp) - 1}); mn.append(len(p)); mv.append(p)
    mm[-1]['lados'] = ls; mm[-1]['lp'] = [[round(float(x), 2), round(float(z), 2)] for x, z in lp[:-1]]
C['manzanas'] = {'meta': mm, 'n': desinflar(np.array(mn, dtype=np.uint16)), 'v': desinflar(np.vstack(mv).astype(np.float32))}
# ---------------- edificios: fuera del corredor, recortados a las manzanas del plano y sin invadir calzadas
EDF = json.load(open('plan/edificios_plano.json'))
UMZ = shapely.union_all([Polygon(m['p']).buffer(0) for m in MZS]).buffer(0.15); shapely.prepare(UMZ)
nuevos = []; q_cor = q_mz = q_pav = rec = 0
for b in EDF:
    pts = b['P']; a = np.array(b['at'], dtype=np.uint8)
    if len(pts) < 3: continue
    pol = Polygon(pts)
    if not pol.is_valid: pol = pol.buffer(0)
    if pol.is_empty or pol.geom_type != 'Polygon': continue
    area = pol.area; quitar = False
    for z_ in (zona, est, cat):
        if pol.intersects(z_):
            inter = pol.intersection(z_).area
            if (z_ is zona and inter / area > 0.2) or (z_ is not zona and inter / area > 0.3): quitar = True
            elif inter > 0.5:
                pol = pol.difference(z_)
                if pol.geom_type == 'MultiPolygon': pol = max(pol.geoms, key=lambda q: q.area)
    if quitar or plaza.contains(pol.centroid): q_cor += 1; continue
    dentro = pol.intersection(UMZ) if pol.intersects(UMZ) else Polygon()
    if dentro.geom_type in ('MultiPolygon', 'GeometryCollection'):
        parts = [g for g in getattr(dentro, 'geoms', []) if g.geom_type == 'Polygon']
        dentro = max(parts, key=lambda q: q.area) if parts else Polygon()
    if not dentro.is_empty and dentro.area >= max(12, 0.5 * area):
        if dentro.area < area - 0.5: rec += 1
        pol = dentro
    else:                               # fuera de las manzanas cerradas del plano: sólo se quita lo que invade la calzada
        fuera = pol.difference(PAV)
        if fuera.geom_type == 'MultiPolygon': fuera = max(fuera.geoms, key=lambda q: q.area)
        if fuera.is_empty or fuera.area < 0.6 * area: q_pav += 1; continue
        if not dentro.is_empty: q_mz += 1
        pol = fuera
    if pol.geom_type != 'Polygon' or pol.area < 8: continue
    pol = pol.simplify(0.15)
    ext = list(pol.exterior.coords)[:-1]
    if len(ext) < 3: continue
    if Polygon(ext).exterior.is_ccw != Polygon(pts).exterior.is_ccw: ext = ext[::-1]
    nuevos.append((ext, a))
print('edificios: entrada', len(EDF), 'quedan', len(nuevos), '| quitados corredor/hitos', q_cor, 'mayormente fuera de manzana (conservados)', q_mz, 'en calzada', q_pav, '| recortados a manzana', rec)
n_arr = np.array([len(p) for p, a in nuevos], dtype=np.uint16)
pri_arr = np.array([[round(p[0][0] * 10), round(p[0][1] * 10)] for p, a in nuevos], dtype=np.int32).ravel()
dl = []
for p, a in nuevos:
    x0, z0 = round(p[0][0] * 10), round(p[0][1] * 10)
    for q in p[1:]: dl.append([round(q[0] * 10) - x0, round(q[1] * 10) - z0])
C['edificios'] = {'n': desinflar(n_arr), 'pri': desinflar(pri_arr), 'dlt': desinflar(np.array(dl, dtype=np.int16).ravel()), 'at': desinflar(np.concatenate([a for p, a in nuevos]).astype(np.uint8)), 'cuenta': len(nuevos)}
# ---------------- vías originales: se reemplazan por las calzadas del plano
C['vias'] = []
# ---------------- árboles y postes
arb = inflar(C['arboles'], np.int16).reshape(-1, 4)
xa, za = arb[:, 0] / 4, arb[:, 1] / 4
malo = shapely.contains_xy(PAV, xa, za) | shapely.contains_xy(zona, xa, za) | shapely.contains_xy(est, xa, za) | shapely.contains_xy(plaza, xa, za)
print('árboles', len(arb), '->', int((~malo).sum())); C['arboles'] = desinflar(arb[~malo].ravel())
pos = inflar(C['postes'], np.int16).reshape(-1, 2)
xp, zp = pos[:, 0] / 4, pos[:, 1] / 4
malo = shapely.contains_xy(PAV, xp, zp) | shapely.contains_xy(zona.buffer(2), xp, zp) | shapely.contains_xy(plaza, xp, zp)
print('postes', len(pos), '->', int((~malo).sum())); C['postes'] = desinflar(pos[~malo].ravel())
# ---------------- terreno: curvas del plano + calle asentada (perfil) + plaza y estadio nivelados
zn = np.load('plan/z10.npy').astype(np.float64) - ZMIN
xc = -MX + CEL / 2 + CEL * np.arange(W); zc = -MZ + CEL / 2 + CEL * np.arange(H)
XX, ZZ = np.meshgrid(xc, zc)
sel = (XX > cx.min() - 40) & (XX < cx.max() + 40) & (ZZ > cz.min() - 40) & (ZZ < cz.max() + 40)
pts = shapely.points(XX[sel], ZZ[sel])
d = shapely.distance(calle, pts); sP = shapely.line_locate_point(ejeCH, pts)
k = np.clip(np.round(sP).astype(int), 0, N - 1); obj = ys[k] - 0.32
w = np.clip((d - 9.0) / 13.0, 0, 1); w = w * w * (3 - 2 * w)
zsel = zn[sel]; nuevo = np.where(d <= 9.0, obj, obj * (1 - w) + zsel * w); nuevo = np.where(d > 22, zsel, nuevo)
print('vértices de terreno asentados bajo la calle', int((d <= 22).sum()), 'máx cambio %.2f m' % np.abs(nuevo - zsel).max())
zn[sel] = nuevo
for poly, extra, nombre in ((Polygon(C['plaza']), 4.0, 'plaza'), (Polygon(HI['pista']).union(Polygon(HI['estadio'])), 3.0, 'estadio')):
    m = shapely.contains_xy(poly, XX, ZZ)
    nivel = float(np.percentile(zn[m], 30)) - 0.15
    dd = shapely.distance(poly, shapely.points(XX, ZZ))
    w = np.clip((dd - extra) / 10, 0, 1)
    zona_n = dd < extra + 10
    zn[zona_n] = nivel * (1 - w[zona_n]) + zn[zona_n] * w[zona_n]
    print(nombre, 'nivelado a %.2f msnm' % (nivel + ZMIN))
C['z'] = desinflar(np.clip(np.round(zn * 20), 0, 65535).astype(np.uint16).ravel())
np.save('plan/z10_final.npy', (zn + ZMIN).astype(np.float32))
# ---------------- red D8 de 5 m sobre el terreno final (calles y ríos marcados)
WF, HF, CF = C['WF'], C['HF'], C['celdaF']
z5 = zoom(zn, 2, order=1)[:HF, :WF]
tr = rasterio.transform.from_origin(-MX, -MZ, CF, -CF)        # filas crecen con z (hacia el sur)
tr = rasterio.transform.Affine(CF, 0, -MX, 0, CF, -MZ)
m_calle = rasterio.features.rasterize([(g, 1) for g in pav] + [(calle, 1)], out_shape=(HF, WF), transform=tr, dtype='uint8').astype(bool)
rios = []
for g in C['agua']:
    if len(g['c']) > 1: rios.append(LineString(g['c']).buffer(max(1.5, g['w'] / 2)))
m_rio = rasterio.features.rasterize([(g, 1) for g in rios], out_shape=(HF, WF), transform=tr, dtype='uint8').astype(bool)
zr = z5 - 0.45 * m_calle - 2.5 * m_rio
# priority-flood con épsilon (Barnes 2014): todas las celdas drenan al borde o a un río
lleno = np.full_like(zr, np.inf); visto = np.zeros(zr.shape, bool); pq = []
for r in range(HF):
    for c in (0, WF - 1): heapq.heappush(pq, (zr[r, c], r, c)); visto[r, c] = True
for c in range(1, WF - 1):
    for r in (0, HF - 1): heapq.heappush(pq, (zr[r, c], r, c)); visto[r, c] = True
rr, cc = np.nonzero(m_rio)
for r, c in zip(rr, cc):
    if not visto[r, c]: heapq.heappush(pq, (zr[r, c], r, c)); visto[r, c] = True
DCo = [1, 1, 0, -1, -1, -1, 0, 1]; DRo = [0, 1, 1, 1, 0, -1, -1, -1]
EPS = 1e-4
zf = zr.copy()
while pq:
    z0, r, c = heapq.heappop(pq)
    for k in range(8):
        r2, c2 = r + DRo[k], c + DCo[k]
        if 0 <= r2 < HF and 0 <= c2 < WF and not visto[r2, c2]:
            visto[r2, c2] = True
            if zf[r2, c2] <= z0: zf[r2, c2] = z0 + EPS
            heapq.heappush(pq, (zf[r2, c2], r2, c2))
# D8 de máxima pendiente sobre el terreno relleno
best = np.zeros(zf.shape); dirn = np.full(zf.shape, 8, np.uint8)
for k in range(8):
    sh = np.full_like(zf, np.inf)
    r0, r1 = max(0, -DRo[k]), HF - max(0, DRo[k]); c0, c1 = max(0, -DCo[k]), WF - max(0, DCo[k])
    sh[r0:r1, c0:c1] = zf[r0 + DRo[k]:r1 + DRo[k], c0 + DCo[k]:c1 + DCo[k]]
    pend = (zf - sh) / (1.4142 if k % 2 else 1.0)
    mejor = pend > best; best[mejor] = pend[mejor]; dirn[mejor] = k
tipo = np.where(m_rio, 2, np.where(m_calle, 1, 0)).astype(np.uint8)
dirn[m_rio] = np.where(dirn[m_rio] == 8, 8, dirn[m_rio])
fl = (tipo * 9 + dirn).astype(np.uint8)
C['flujo'] = desinflar(fl.ravel())
print('D8: celdas calle', int(m_calle.sum()), 'río', int(m_rio.sum()), 'sumideros', int((dirn == 8).sum()))
# ---------------- datos finales
C['plaza_c'] = C['plaza_c']
json.dump(C, open('plan/datos_mod.json', 'w'), ensure_ascii=False)
json.dump(CH, open('plan/chanchamayo.json', 'w'), ensure_ascii=False)
print('datos_mod.json', len(json.dumps(C)) // 1024, 'KB')
