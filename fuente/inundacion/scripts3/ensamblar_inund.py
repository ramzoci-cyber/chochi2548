# Datos base del modelo de susceptibilidad a inundaciones (marco del plano): ciudad sin el corredor detallado ni la
# propuesta vial; calles y veredas del plano, edificios recortados a manzanas con su unidad de riesgo de la tesis,
# terreno con las curvas del plano, hitos, árboles, postes y red D8 de 5 m.
import json, base64, zlib, sys, os, heapq, numpy as np, shapely
from shapely.geometry import Polygon, Point, LineString
from scipy.ndimage import zoom
import rasterio.features, rasterio.transform
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts2'))
C = json.load(open('plan/datos_base.json'))
W, H, CEL, ZMIN = C['W'], C['H'], C['celda'], C['zmin']; MX, MZ = W * CEL / 2, H * CEL / 2
def desinflar(a): return base64.b64encode(zlib.compress(np.ascontiguousarray(a).tobytes(), 9)).decode()
def inflar(b64, dt): return np.frombuffer(zlib.decompress(base64.b64decode(b64)), dtype=dt)
CAL = json.load(open('plan/calles.json')); MZS = json.load(open('plan/manzanas.json'))
HI = json.load(open('plan/hitos_plano.json'))
from marco import local_a_plano
def mover(o):
    if isinstance(o, list) and o and isinstance(o[0], (int, float)) and len(o) == 2:
        x, z = local_a_plano(np.array([o[0]]), np.array([o[1]])); return [round(float(x[0]), 2), round(float(z[0]), 2)]
    if isinstance(o, list): return [mover(v) for v in o]
    if isinstance(o, dict): return {k: mover(v) for k, v in o.items()}
    return o
HI1 = mover(json.load(open('data/hitos.json')))
est = Polygon(HI1['estadio_stadium']).buffer(2); cat = Polygon(HI1['catedral']).buffer(1.5)
plaza = Polygon(C['plaza']).buffer(-0.5)
U = json.load(open('tesis/riesgo_unidades.json'))
# ---------------- calzadas (todas las calles del plano)
def normales(c):
    d = np.gradient(c, axis=0); d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9); return np.c_[-d[:, 1], d[:, 0]]
calles, pav = [], []
for s in CAL['calles']:
    c = np.array(s['c'])
    if len(c) < 2: continue
    if plaza.buffer(-2).contains(LineString(c).interpolate(0.5, normalized=True)) and s['cl'] == 6: continue
    n = normales(c); el, er = np.array(s['el']), np.array(s['er'])
    calles.append(s); pav.append(Polygon(np.r_[c + n * el[:, None], (c - n * er[:, None])[::-1]]).buffer(0))
PAV = shapely.union_all(pav); shapely.prepare(PAV)
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
meta, nv, vv = [], [], []
for s in calles:
    c = np.array(s['c']); el = np.array(s['el']); er = np.array(s['er'])
    k = simplificar(c, el, er)
    meta.append({kk: s[kk] for kk in ('id', 'nombre', 'cl', 'clase', 'sp', 'ancho', 'L')})
    nv.append(int(k.sum())); vv.append(np.c_[c[k], el[k], er[k]])
C['calles'] = {'meta': meta, 'n': desinflar(np.array(nv, dtype=np.uint16)), 'v': desinflar(np.vstack(vv).astype(np.float32))}
print('calles', len(meta))
vmeta, vn, vvv = [], [], []
for v in CAL['veredas']:
    p = np.array(v['p']); mid = LineString(p).interpolate(0.5, normalized=True)
    if plaza.buffer(6).contains(mid) or est.contains(mid): continue
    vmeta.append([v['w'], v['lado']]); vn.append(len(p)); vvv.append(p)
C['veredas'] = {'meta': vmeta, 'n': desinflar(np.array(vn, dtype=np.uint16)), 'v': desinflar(np.vstack(vvv).astype(np.float32))}
print('tramos de vereda', len(vmeta))
# ---------------- edificios recortados a manzanas; unidad de riesgo de la tesis de cada edificio
EDF = json.load(open('plan/edificios_plano.json'))
UMZ = shapely.union_all([Polygon(m['p']).buffer(0) for m in MZS]).buffer(0.15); shapely.prepare(UMZ)
upol = [Polygon(u['local']).buffer(0) for u in U['unidades']]; arbU = shapely.STRtree(upol)
nuevos, q_hit, q_pav, rec = [], 0, 0, 0
for b in EDF:
    pts = b['P']; a = np.array(b['at'], dtype=np.uint8)
    if len(pts) < 3: continue
    pol = Polygon(pts)
    if not pol.is_valid: pol = pol.buffer(0)
    if pol.is_empty or pol.geom_type != 'Polygon': continue
    area = pol.area
    if pol.intersects(est) and pol.intersection(est).area / area > 0.3 or pol.intersects(cat) and pol.intersection(cat).area / area > 0.3 or plaza.contains(pol.centroid):
        q_hit += 1; continue
    for z_ in (est, cat):
        if pol.intersects(z_):
            pol = pol.difference(z_)
            if pol.geom_type == 'MultiPolygon': pol = max(pol.geoms, key=lambda q: q.area)
    dentro = pol.intersection(UMZ) if pol.intersects(UMZ) else Polygon()
    if dentro.geom_type in ('MultiPolygon', 'GeometryCollection'):
        parts = [g for g in getattr(dentro, 'geoms', []) if g.geom_type == 'Polygon']
        dentro = max(parts, key=lambda q: q.area) if parts else Polygon()
    if not dentro.is_empty and dentro.area >= max(12, 0.5 * area):
        if dentro.area < area - 0.5: rec += 1
        pol = dentro
    else:
        fuera = pol.difference(PAV)
        if fuera.geom_type == 'MultiPolygon': fuera = max(fuera.geoms, key=lambda q: q.area)
        if fuera.is_empty or fuera.area < 0.6 * area: q_pav += 1; continue
        pol = fuera
    if pol.geom_type != 'Polygon' or pol.area < 8: continue
    pol = pol.simplify(0.15)
    ext = list(pol.exterior.coords)[:-1]
    if len(ext) < 3: continue
    if Polygon(ext).exterior.is_ccw != Polygon(pts).exterior.is_ccw: ext = ext[::-1]
    cpt = pol.representative_point()
    cand = [i for i in arbU.query(cpt) if upol[i].contains(cpt)]
    nuevos.append((ext, a, int(cand[0]) if cand else -1, float(pol.area)))
print('edificios: entrada', len(EDF), 'quedan', len(nuevos), '| hitos', q_hit, 'en calzada', q_pav, '| recortados', rec, '| dentro de unidades de la tesis', sum(1 for n in nuevos if n[2] >= 0))
n_arr = np.array([len(p) for p, a, u, s in nuevos], dtype=np.uint16)
pri_arr = np.array([[round(p[0][0] * 10), round(p[0][1] * 10)] for p, a, u, s in nuevos], dtype=np.int32).ravel()
dl = []
for p, a, u, s in nuevos:
    x0, z0 = round(p[0][0] * 10), round(p[0][1] * 10)
    for q in p[1:]: dl.append([round(q[0] * 10) - x0, round(q[1] * 10) - z0])
C['edificios'] = {'n': desinflar(n_arr), 'pri': desinflar(pri_arr), 'dlt': desinflar(np.array(dl, dtype=np.int16).ravel()),
                  'at': desinflar(np.concatenate([a for p, a, u, s in nuevos]).astype(np.uint8)), 'cuenta': len(nuevos),
                  'unidad': desinflar(np.array([u for p, a, u, s in nuevos], dtype=np.int16))}
json.dump([[u, round(s, 1)] for p, a, u, s in nuevos], open('inund/edificios_unidad.json', 'w'))
C['vias'] = []
# ---------------- árboles y postes
arb = inflar(C['arboles'], np.int16).reshape(-1, 4)
xa, za = arb[:, 0] / 4, arb[:, 1] / 4
malo = shapely.contains_xy(PAV, xa, za) | shapely.contains_xy(est, xa, za) | shapely.contains_xy(plaza, xa, za)
C['arboles'] = desinflar(arb[~malo].ravel())
pos = inflar(C['postes'], np.int16).reshape(-1, 2)
xp, zp = pos[:, 0] / 4, pos[:, 1] / 4
malo = shapely.contains_xy(PAV, xp, zp) | shapely.contains_xy(plaza, xp, zp)
C['postes'] = desinflar(pos[~malo].ravel())
# ---------------- terreno: curvas del plano + plaza y estadio nivelados
zn = np.load('plan/z10.npy').astype(np.float64) - ZMIN
xc = -MX + CEL / 2 + CEL * np.arange(W); zc = -MZ + CEL / 2 + CEL * np.arange(H)
XX, ZZ = np.meshgrid(xc, zc)
for poly, extra, nombre in ((Polygon(C['plaza']), 4.0, 'plaza'), (Polygon(HI['pista']).union(Polygon(HI['estadio'])), 3.0, 'estadio')):
    m = shapely.contains_xy(poly, XX, ZZ)
    nivel = float(np.percentile(zn[m], 30)) - 0.15
    dd = shapely.distance(poly, shapely.points(XX, ZZ)); w = np.clip((dd - extra) / 10, 0, 1); zona_n = dd < extra + 10
    zn[zona_n] = nivel * (1 - w[zona_n]) + zn[zona_n] * w[zona_n]
C['z'] = desinflar(np.clip(np.round(zn * 20), 0, 65535).astype(np.uint16).ravel())
np.save('inund/z10_final.npy', (zn + ZMIN).astype(np.float32))
# ---------------- red D8 de 5 m (lluvia de partículas: calles y ríos marcados)
WF, HF, CF = C['WF'], C['HF'], C['celdaF']
z5 = zoom(zn, 2, order=1)[:HF, :WF]
tr = rasterio.transform.Affine(CF, 0, -MX, 0, CF, -MZ)
m_calle = rasterio.features.rasterize([(g, 1) for g in pav], out_shape=(HF, WF), transform=tr, dtype='uint8').astype(bool)
rios = [LineString(g['c']).buffer(max(1.5, g['w'] / 2)) for g in C['agua'] if len(g['c']) > 1]
m_rio = rasterio.features.rasterize([(g, 1) for g in rios], out_shape=(HF, WF), transform=tr, dtype='uint8').astype(bool)
zr = z5 - 0.45 * m_calle - 2.5 * m_rio
vis = np.zeros(zr.shape, bool); pq = []; zf = zr.copy()
for r in range(HF):
    for c in (0, WF - 1): heapq.heappush(pq, (zr[r, c], r, c)); vis[r, c] = True
for c in range(1, WF - 1):
    for r in (0, HF - 1): heapq.heappush(pq, (zr[r, c], r, c)); vis[r, c] = True
for r, c in zip(*np.nonzero(m_rio)):
    if not vis[r, c]: heapq.heappush(pq, (zr[r, c], r, c)); vis[r, c] = True
DCo = [1, 1, 0, -1, -1, -1, 0, 1]; DRo = [0, 1, 1, 1, 0, -1, -1, -1]
while pq:
    z0, r, c = heapq.heappop(pq)
    for k in range(8):
        r2, c2 = r + DRo[k], c + DCo[k]
        if 0 <= r2 < HF and 0 <= c2 < WF and not vis[r2, c2]:
            vis[r2, c2] = True
            if zf[r2, c2] <= z0: zf[r2, c2] = z0 + 1e-4
            heapq.heappush(pq, (zf[r2, c2], r2, c2))
best = np.zeros(zf.shape); dirn = np.full(zf.shape, 8, np.uint8)
for k in range(8):
    sh = np.full_like(zf, np.inf); r0, r1 = max(0, -DRo[k]), HF - max(0, DRo[k]); c0, c1 = max(0, -DCo[k]), WF - max(0, DCo[k])
    sh[r0:r1, c0:c1] = zf[r0 + DRo[k]:r1 + DRo[k], c0 + DCo[k]:c1 + DCo[k]]
    pend = (zf - sh) / (1.4142 if k % 2 else 1.0); mejor = pend > best; best[mejor] = pend[mejor]; dirn[mejor] = k
tipo = np.where(m_rio, 2, np.where(m_calle, 1, 0)).astype(np.uint8)
C['flujo'] = desinflar((tipo * 9 + dirn).astype(np.uint8).ravel())
# ---------------- limpieza: microcuenca, eje y T01 del enfoque anterior; etiquetas
C['microcuenca'] = []; C['eje'] = []
C['etiquetas'] = [e for e in C['etiquetas'] if e[0] not in ('Jr. Chanchamayo',)]
for k in ('secciones', 'locales', 'manzanas'): C.pop(k, None)
C['hitos'] = HI
json.dump(C, open('inund/datos_base.json', 'w'), ensure_ascii=False)
print('inund/datos_base.json', len(json.dumps(C)) // 1024, 'KB')
