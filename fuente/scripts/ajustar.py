# Ajusta los datos originales: terreno bajo el corredor, edificios superpuestos, vías y árboles del Jr. Chanchamayo, hitos
import json, base64, zlib, numpy as np, shapely
from shapely.geometry import Polygon, Point, LineString
from shapely import STRtree
C = json.load(open('orig/datos_clean.json'))
W, H, CEL = C['W'], C['H'], C['celda']; MX, MZ = W * CEL / 2, H * CEL / 2
def inflar(b64, dt): return np.frombuffer(zlib.decompress(base64.b64decode(b64)), dtype=dt)
def desinflar(a): return base64.b64encode(zlib.compress(np.ascontiguousarray(a).tobytes(), 9)).decode()
CH = json.load(open('data/chanchamayo.json'))
HI = json.load(open('data/hitos.json'))
e = np.load('data/eje1m.npz'); S, cx, cz, nx, nz, ys, fE, fO = [e[k] for k in ('S', 'cx', 'cz', 'nx', 'nz', 'ys', 'fE', 'fO')]
N = len(S)
def P(s, o, lado):
    i = int(np.clip(round(s), 0, N - 1)); return (cx[i] + nx[i] * o * lado, cz[i] + nz[i] * o * lado)
def fval(s, lado):
    i = int(np.clip(round(s), 0, N - 1)); v = (fE if lado == 1 else fO)[i]; return v if v > 0 else 5.0
# ---------------- zona del corredor
izq = [P(s, fval(s, 1) + 0.3, 1) for s in S]; der = [P(s, fval(s, -1) + 0.3, -1) for s in S[::-1]]
calle = Polygon(izq + der).buffer(0)
partes = [calle]
for l in CH['lotes']:
    s0, s1, lado = l['s0'], l['s1'], l['lado']; f0, f1 = l['f']
    prof = l['ret'] + max(l['Dt'], l['D'])
    pts = [P(s0, f0, lado), P(s1, f1, lado), P(s1, f1 + prof, lado), P(s0, f0 + prof, lado)]
    partes.append(Polygon(pts).buffer(0.2))
for c in CH['cercos']:
    s0, s1, lado = c['s0'], c['s1'], c['lado']; f0, f1 = c['f']
    partes.append(Polygon([P(s0, f0, lado), P(s1, f1, lado), P(s1, f1 + 6, lado), P(s0, f0 + 6, lado)]).buffer(0.2))
zona = shapely.union_all(partes)
est = Polygon(HI['estadio_stadium']).buffer(2)
cat = Polygon(HI['catedral']).buffer(1.5)
plaza = Polygon(C['plaza']).buffer(-0.5)
print('zona corredor m2', round(zona.area), 'estadio', round(est.area))
# ---------------- edificios originales
E = C['edificios']
nV = inflar(E['n'], np.uint16); pri = inflar(E['pri'], np.int32); dlt = inflar(E['dlt'], np.int16); at = inflar(E['at'], np.uint8)
blds = []; iD = 0
for b in range(E['cuenta']):
    n = int(nV[b]); x0 = pri[b * 2] / 10; z0 = pri[b * 2 + 1] / 10
    pts = [(x0, z0)]
    for k in range(1, n): pts.append((x0 + dlt[iD * 2] / 10, z0 + dlt[iD * 2 + 1] / 10)); iD += 1
    blds.append((pts, at[b * 10:b * 10 + 10].copy()))
nuevos = []; quitados = 0; recortados = 0
for pts, a in blds:
    if len(pts) < 3: continue
    pol = Polygon(pts)
    if not pol.is_valid: pol = pol.buffer(0)
    if pol.is_empty: continue
    area = pol.area
    quitar = False
    for z_ in (zona, est, cat):
        if pol.intersects(z_):
            inter = pol.intersection(z_).area
            if z_ is zona and inter / area > 0.2: quitar = True
            elif z_ is not zona and inter / area > 0.3: quitar = True
            elif inter > 0.5:
                pol = pol.difference(z_)
                if pol.geom_type == 'MultiPolygon': pol = max(pol.geoms, key=lambda q: q.area)
                recortados += 1
    if plaza.contains(pol.centroid): quitar = True
    if quitar or pol.is_empty or pol.area < 8:
        quitados += 1; continue
    if pol.geom_type != 'Polygon': continue
    pol = pol.simplify(0.15)
    ext = list(pol.exterior.coords)[:-1]
    if len(ext) < 3: continue
    # mantener la orientación original (antihoraria en x,z como el original)
    if Polygon(ext).exterior.is_ccw != Polygon(pts).exterior.is_ccw: ext = ext[::-1]
    nuevos.append((ext, a))
print('edificios: originales', len(blds), 'quedan', len(nuevos), 'quitados', quitados, 'recortados', recortados)
n_arr = np.array([len(p) for p, a in nuevos], dtype=np.uint16)
pri_arr = np.array([[round(p[0][0] * 10), round(p[0][1] * 10)] for p, a in nuevos], dtype=np.int32).ravel()
dl = []
for p, a in nuevos:
    x0, z0 = round(p[0][0] * 10), round(p[0][1] * 10)
    for q in p[1:]: dl.append([round(q[0] * 10) - x0, round(q[1] * 10) - z0])
dlt_arr = np.array(dl, dtype=np.int16).ravel()
at_arr = np.concatenate([a for p, a in nuevos]).astype(np.uint8)
C['edificios'] = {'n': desinflar(n_arr), 'pri': desinflar(pri_arr), 'dlt': desinflar(dlt_arr), 'at': desinflar(at_arr), 'cuenta': len(nuevos)}
# ---------------- vías: quitar las cintas del Jr. Chanchamayo (las reemplaza la calle detallada)
ejeOSM = LineString(np.array(json.load(open('orig/datos_clean.json'))['eje'][0] + [[921.14, 551.06]]))
ejes = shapely.union_all([LineString(l) for l in C['eje']])
vias = []; qv = 0
for v in C['vias']:
    pts = np.array(v['c'])
    d = np.array([ejes.distance(Point(p)) for p in pts])
    if len(pts) >= 2 and (d < 2.5).mean() > 0.6 and LineString(pts).length > 3: qv += 1; continue
    vias.append(v)
C['vias'] = vias; print('vías quitadas', qv)
# ---------------- árboles y postes dentro del corredor / estadio / plaza
arb = inflar(C['arboles'], np.int16).reshape(-1, 4)
tree = [i for i in range(len(arb)) if not (zona.contains(Point(arb[i, 0] / 4, arb[i, 1] / 4)) or est.contains(Point(arb[i, 0] / 4, arb[i, 1] / 4)) or plaza.contains(Point(arb[i, 0] / 4, arb[i, 1] / 4)))]
print('árboles', len(arb), '->', len(tree)); C['arboles'] = desinflar(arb[tree].ravel())
pos = inflar(C['postes'], np.int16).reshape(-1, 2)
keep = [i for i in range(len(pos)) if not (zona.buffer(2).contains(Point(pos[i, 0] / 4, pos[i, 1] / 4)) or plaza.contains(Point(pos[i, 0] / 4, pos[i, 1] / 4)))]
print('postes', len(pos), '->', len(keep)); C['postes'] = desinflar(pos[keep].ravel())
# ---------------- terreno: asentar la calle (perfil suavizado) y transición de 12 m
z16 = inflar(C['z'], np.uint16).astype(np.float64).reshape(H, W) / 20
zn = z16.copy()
ejeL = LineString(np.c_[cx, cz])
banda = calle.buffer(6)
cambio = 0
for j in range(H):
    zc = -MZ + CEL / 2 + CEL * j
    if zc < 150 or zc > 950: continue
    for i in range(W):
        xc = -MX + CEL / 2 + CEL * i
        if xc < 520 or xc > 1080: continue
        p = Point(xc, zc)
        d = calle.distance(p)
        if d > 22: continue
        s = ejeL.project(p); k = int(np.clip(round(s), 0, N - 1))
        objetivo = ys[k] - 0.32
        if d <= 9.0: zn[j, i] = objetivo
        else:
            w = (d - 9.0) / 13.0; w = w * w * (3 - 2 * w)
            zn[j, i] = objetivo * (1 - w) + z16[j, i] * w
        cambio += 1
print('vértices de terreno ajustados', cambio, 'máx cambio %.2f m' % np.abs(zn - z16).max())
# plaza y estadio: plataformas niveladas
HF_ = json.load(open('data/hitos_final.json'))
for poly, extra, nombre in ((Polygon(C['plaza']), 4.0, 'plaza'), (Polygon(HF_['pista']).union(Polygon(HF_['estadio'])), 3.0, 'estadio')):
    vals = []
    for j in range(H):
        zc = -MZ + CEL / 2 + CEL * j
        for i in range(W):
            xc = -MX + CEL / 2 + CEL * i
            if poly.contains(Point(xc, zc)): vals.append(zn[j, i])
    nivel = float(np.percentile(vals, 30)) if vals else None
    if nivel is None: continue
    n = 0
    for j in range(H):
        zc = -MZ + CEL / 2 + CEL * j
        for i in range(W):
            xc = -MX + CEL / 2 + CEL * i
            d = poly.distance(Point(xc, zc))
            if d == 0: zn[j, i] = nivel - 0.15; n += 1
            elif d < extra + 10:
                w = min(1.0, max(0.0, (d - extra) / 10)); zn[j, i] = (nivel - 0.15) * (1 - w) + zn[j, i] * w
    print(nombre, 'nivelado a', round(nivel, 2), 'vértices', n)
C['z'] = desinflar(np.clip(np.round(zn * 20), 0, 65535).astype(np.uint16).ravel())
json.dump(C, open('data/datos_mod.json', 'w'), ensure_ascii=False)
print('datos_mod.json', len(json.dumps(C)) // 1024, 'KB')
