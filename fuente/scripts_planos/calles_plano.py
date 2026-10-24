# Red vial según el plano: ancho actual medido entre manzanas (Plano Total 2025), ancho propuesto (lámina 26, vías locales)
# y sección típica (lámina 25, sistema vial). Ejes: OSM vía Overture, llevados al marco del plano.
# Salida: plan/calles.json, plan/manzanas.json (coordenadas locales del modelo en el marco del plano: x = E - 424400, z = 8738400 - N)
import pickle, json, sys, os, re, collections, numpy as np, shapely, pyarrow.parquet as pq
from shapely.geometry import LineString, Point, Polygon
from pyproj import Transformer
from scipy.ndimage import median_filter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marco import local_a_plano

def a_local(g):          # UTM (marco del plano) -> local
    return shapely.transform(g, lambda a: np.c_[a[:, 0] - 424400, 8738400 - a[:, 1]])

# ---------------------------------------------------------------- secciones típicas (láminas 25 y 26)
SECC = {
    'C1': {'total': 9.30, 'comp': [['canal', 4.00], ['VR', 3.95], ['C', 0.35], ['V', 1.00]]},
    'C2': {'total': 24.00, 'comp': [['V', 1.50], ['B', 1.50], ['VR', 6.00], ['SC', 6.00], ['VR', 6.00], ['B', 1.50], ['V', 1.50]]},
    'C3': {'total': 10.50, 'comp': [['V', 1.20], ['C', 0.40], ['VR', 7.30], ['C', 0.40], ['V', 1.20]]},
    "C3'": {'total': 10.50, 'comp': [['V', 1.45], ['P', 9.05]], 'nota': 'Jr. Lima: peatonal con voladizo de 1,45 m'},
    'B1': {'total': 14.00, 'comp': [['V', 1.50], ['C', 0.30], ['E/J', 1.60], ['VR', 7.20], ['E/J', 1.60], ['C', 0.30], ['V', 1.50]]},
    'B2': {'total': 25.00, 'comp': [['V', 1.20], ['J', 1.90], ['C', 0.35], ['VR', 7.20], ['C', 0.35], ['SC', 3.00], ['C', 0.35], ['VR', 7.20], ['C', 0.35], ['J', 1.90], ['V', 1.20]]},
    'C4': {'total': 8.00, 'comp': [['V', 1.20], ['C', 0.40], ['VR', 4.80], ['C', 0.40], ['V', 1.20]]},
    'C5': {'total': 12.00, 'comp': [['V', 1.20], ['C', 0.40], ['J', 1.00], ['VR', 6.80], ['J', 1.00], ['C', 0.40], ['V', 1.20]]},
    'B3': {'total': 12.00, 'comp': [['V', 1.20], ['C', 0.30], ['VR', 9.00], ['C', 0.30], ['V', 1.20]]},
    'C6': {'total': 14.00, 'comp': [['V', 1.80], ['C', 0.40], ['E/J', 1.20], ['VR', 7.20], ['E/J', 1.20], ['C', 0.40], ['V', 1.80]]},
    'C7': {'total': 9.40, 'comp': [['V', 1.20], ['C', 0.30], ['VR', 6.40], ['C', 0.30], ['V', 1.20]]},
    'B4': {'total': 25.00, 'comp': [['V', 2.20], ['C', 0.50], ['E/J', 1.75], ['VR', 6.60], ['SC', 2.90], ['VR', 6.60], ['E/J', 1.75], ['C', 0.50], ['V', 2.20]], 'nota': 'Av. Manuel A. Odría'},
    'C8': {'total': 17.00, 'comp': [['V', 1.20], ['J', 1.00], ['VR', 4.80], ['canal', 3.00], ['VR', 4.80], ['J', 1.00], ['V', 1.20]], 'nota': 'Av. José Gálvez: lado derecho consolidado, lado izquierdo a ampliar; reubicación y canalización del río Huantay'},
    'E1': {'total': 32.40, 'comp': [['B', 3.70], ['VR', 12.50], ['VR', 12.50], ['B', 3.70]], 'nota': 'Vía de Evitamiento (sur y norte)'},
}
LOCAL = {   # vías locales (lámina 26): ancho -> componentes
    4.0: [['V', 1.25], ['J', 1.50], ['V', 1.25]],
    5.0: [['V', 1.60], ['J', 1.80], ['V', 1.60]],
    6.0: [['V', 1.00], ['C', 0.40], ['VR', 3.20], ['C', 0.40], ['V', 1.00]],
    7.0: [['V', 1.20], ['C', 0.40], ['VR', 3.80], ['C', 0.40], ['V', 1.20]],
    8.0: [['V', 1.20], ['C', 0.40], ['VR', 4.80], ['C', 0.40], ['V', 1.20]],
    9.0: [['V', 1.20], ['C', 0.40], ['VR', 5.80], ['C', 0.40], ['V', 1.20]],
    10.0: [['V', 1.20], ['C', 0.40], ['E/J', 1.50], ['VR', 3.80], ['E/J', 1.50], ['C', 0.40], ['V', 1.20]],
    12.0: [['V', 1.20], ['C', 0.40], ['J', 1.00], ['VR', 6.80], ['J', 1.00], ['C', 0.40], ['V', 1.20]],
    14.0: [['V', 1.80], ['C', 0.40], ['E/J', 1.20], ['VR', 7.20], ['E/J', 1.20], ['C', 0.40], ['V', 1.80]],
    16.0: [['V', 2.30], ['C', 0.40], ['E/J', 1.70], ['VR', 7.20], ['E/J', 1.70], ['C', 0.40], ['V', 2.30]],
}

# ---------------------------------------------------------------- manzanas
MZU = pickle.load(open('plan/manzanas_crudo.pkl', 'rb'))['pols']
MZ = [a_local(m) for m in MZU]
UMZ = shapely.union_all(MZ); shapely.prepare(UMZ)
LIN = [a_local(g) for g in pickle.load(open('plan/manzanas_crudo.pkl', 'rb'))['lineas']]
bordes = LIN; dueno = np.arange(len(LIN))
arbB = shapely.STRtree(bordes)

# ---------------------------------------------------------------- ejes (Overture/OSM) al marco del plano
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
CL = {'trunk': 0, 'primary': 0, 'secondary': 1, 'tertiary': 2, 'residential': 3, 'unclassified': 3, 'living_street': 3, 'unknown': 3,
      'service': 4, 'track': 5, 'footway': 6, 'path': 6, 'pedestrian': 6, 'steps': 6, 'cycleway': 6}
ANCHO = [12, 10, 9, 7, 4.5, 3.5, 2.5]
B0 = json.load(open('plan/datos_base.json'))
viasM = [(LineString(v['c']), v['sp']) for v in B0['vias'] if len(v['c']) > 1]
arbV = shapely.STRtree([g for g, _ in viasM])
segs = []
for r in pq.read_table('data/transportation_segment.parquet').to_pylist():
    cls = r.get('class') or 'unknown'
    if cls not in CL: continue
    g = shapely.from_wkb(r['geometry']); x, y = T.transform(*zip(*g.coords))
    xl, zl = local_a_plano(np.array(x) - 424400, 8738400 - np.array(y))
    if np.all(np.abs(xl) > 2650) or np.all(np.abs(zl) > 4050): continue
    L = LineString(np.c_[xl, zl])
    if L.length < 1: continue
    nm = (r.get('names') or {}).get('primary') if r.get('names') else None
    sup = (r.get('road_surface') or [{}])[0].get('value')
    # superficie del modelo original (vía más cercana) si OSM no la indica
    mid = L.interpolate(0.5, normalized=True); j = arbV.nearest(mid)
    sp = viasM[j][1] if viasM[j][0].distance(mid) < 6 else (2 if sup == 'unpaved' else 0)
    if sup == 'paved' and sp == 2: sp = 0
    if sup == 'unpaved': sp = 2
    puente = any((f.get('values') or [None])[0] == 'is_bridge' for f in (r.get('road_flags') or []) if isinstance(f, dict)) if r.get('road_flags') else False
    segs.append({'g': L, 'nombre_osm': nm, 'clase': cls, 'cl': CL[cls], 'sp': int(sp), 'pu': bool(puente)})
print('segmentos', len(segs))

# ---------------------------------------------------------------- ancho actual: rayos perpendiculares hasta las manzanas
PASO = 2.0; RMAX = 30.0
muestras = []           # (seg, s, x, z, nx, nz)
for si, sg in enumerate(segs):
    L = sg['g']; n = max(2, int(np.ceil(L.length / PASO)) + 1)
    s = np.linspace(0, L.length, n)
    P = np.array([L.interpolate(v).coords[0] for v in s])
    d = np.gradient(P, axis=0); d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    sg['s'] = s; sg['P'] = P; sg['N'] = np.c_[-d[:, 1], d[:, 0]]       # normal izquierda
    for k in range(n): muestras.append((si, k))
M = np.array([segs[si]['P'][k] for si, k in muestras]); NN = np.array([segs[si]['N'][k] for si, k in muestras])
dentro = shapely.contains_xy(UMZ, M[:, 0], M[:, 1])
res = {}
for lado, sg_ in (('l', 1), ('r', -1)):
    fin = M + NN * RMAX * sg_
    rayos = shapely.linestrings(np.stack([M, fin], 1))
    ia, ib = arbB.query(rayos, predicate='intersects')
    pts = shapely.intersection(rayos[ia], np.array(bordes, dtype=object)[ib])
    dd = shapely.distance(shapely.points(M[ia]), pts)
    dist = np.full(len(M), np.nan); quien = np.full(len(M), -1)
    orden = np.lexsort((dd, ia))
    ia_o, dd_o, ib_o = ia[orden], dd[orden], ib[orden]
    primero = np.r_[True, ia_o[1:] != ia_o[:-1]]
    dist[ia_o[primero]] = dd_o[primero]; quien[ia_o[primero]] = dueno[ib_o[primero]]
    res[lado] = (dist, quien)
dl, ql = res['l']; dr, qr = res['r']
dl[dentro] = np.nan; dr[dentro] = np.nan
Wm = dl + dr
print('muestras', len(M), 'eje dentro de manzana', round(dentro.mean() * 100, 1), '%', 'con ambos lados', round((np.isfinite(dl) & np.isfinite(dr)).mean() * 100, 1), '%')

# ---------------------------------------------------------------- vereda según el ancho actual de la calle (condición existente representativa)
def vereda(W):
    if not np.isfinite(W) or W < 5: return 0.0
    return 0.9 if W < 7 else 1.2 if W < 9 else 1.5 if W < 12 else 1.8 if W < 16 else 2.2
VER = np.array([vereda(w) if np.isfinite(w) and w < 40 else np.nan for w in Wm])
# ---------------------------------------------------------------- anchos propuestos: cotas de la lámina 26 (vías locales)
VL = pickle.load(open('planos/vias_locales_wcs.pkl', 'rb'))
cotas = []
for d in VL['Secciones Viales Nuevas']:
    if d['t'] != 'DIMENSION' or not d.get('defpoint2') or not d.get('defpoint3'): continue
    txt = (d.get('txt') or '').strip(); m = d['med'] if isinstance(d['med'], (int, float)) else None
    mm = re.search(r'(\d+)[,.](\d+)', txt)
    prop = float(mm.group(1) + '.' + mm.group(2)) if mm else (round(m, 2) if m is not None and txt in ('', '<>', '<> ') else None)
    if prop is None or m is None or prop > 40 or m > 45: continue
    p2 = np.array(d['defpoint2'][:2]); p3 = np.array(d['defpoint3'][:2])
    if not (421500 < p2[0] < 427500 and 8734000 < p2[1] < 8743000): continue
    a = np.array([p2[0] - 424400, 8738400 - p2[1]]); b = np.array([p3[0] - 424400, 8738400 - p3[1]])
    cotas.append({'a': a, 'b': b, 'med': float(m), 'prop': prop})
arbS = shapely.STRtree([s['g'] for s in segs])
for s in segs: s['cotas'] = []
asign = 0
for c in cotas:
    u = c['b'] - c['a']; Lu = np.linalg.norm(u); u /= max(Lu, 1e-9)
    lin = LineString([c['a'] - u * 2, c['b'] + u * 2]); mid = Point((c['a'] + c['b']) / 2)
    cand = [i for i in arbS.query(lin, predicate='intersects')]
    if not cand: continue
    i = min(cand, key=lambda i: segs[i]['g'].intersection(lin).distance(mid))
    st = segs[i]['g'].project(mid)
    segs[i]['cotas'].append([round(float(st), 1), round(c['med'], 2), c['prop']]); asign += 1
print('cotas de ancho', len(cotas), 'asignadas a ejes', asign)

# ---------------------------------------------------------------- secciones del sistema vial (lámina 25): cortes + etiquetas
SV = pickle.load(open('planos/sistema_vial_wcs.pkl', 'rb'))
etq = []
for d in SV['SECCIONES']:
    if d['t'] in ('MTEXT', 'TEXT'):
        t = d['txt'].strip().replace('´', "'")
        if t in SECC and 421500 < d['p'][0] < 427500: etq.append((np.array([d['p'][0] - 424400, 8738400 - d['p'][1]]), t))
cortes = []
for d in SV['SECCIONES']:
    if 'pts' in d and len(d['pts']) >= 2:
        a = np.array(d['pts'])[:, :2]
        if not (421500 < a[0, 0] < 427500): continue
        cortes.append(LineString(np.c_[a[:, 0] - 424400, 8738400 - a[:, 1]]))
# deduplicar cortes
uniq = []
for g in cortes:
    if all(g.hausdorff_distance(h) > 0.5 for h in uniq[-50:]): uniq.append(g)
cortes = uniq
for s in segs: s['secc'] = []
n_sec = 0
for g in cortes:
    mid = g.interpolate(0.5, normalized=True)
    cand = sorted(etq, key=lambda e: g.distance(Point(e[0])))
    if not cand or g.distance(Point(cand[0][0])) > 25: continue
    cod = cand[0][1]
    hits = [i for i in arbS.query(g, predicate='intersects') if segs[i]['cl'] <= 4]
    if not hits: continue
    i = min(hits, key=lambda i: segs[i]['g'].intersection(g).distance(mid))
    segs[i]['secc'].append([round(float(segs[i]['g'].project(mid)), 1), cod]); n_sec += 1
print('cortes de sección', len(cortes), 'etiquetas', len(etq), 'asignados', n_sec)

# ---------------------------------------------------------------- nombres del plano (capa Calles)
PT = pickle.load(open('planos/plano_total_wcs.pkl', 'rb'))
nombres = []
for capa in ('Calles', '31 - nombres de calles y distritos'):
    for d in PT.get(capa, []):
        if d['t'] in ('MTEXT', 'TEXT'):
            t = ' '.join(d['txt'].replace('\t', ' ').split())
            if len(t) > 3 and re.match(r'^(JR|AV|CALLE|PJE|PASAJE|PROL|MALEC|CARRETERA|CAMINO|ALAMEDA|BOULEVARD|PSJE|CA\.|PROLONG)', t.upper()):
                nombres.append((Point(d['p'][0] - 424400, 8738400 - d['p'][1]), t))
for s in segs:
    cand = [(s['g'].distance(p), t) for p, t in nombres if s['g'].distance(p) < 22]
    s['nombre_plano'] = min(cand)[1] if cand else None

def titulo(t):
    if not t: return None
    t = t.upper().replace('JR.', 'JR. ').replace('AV.', 'AV. ').replace('PJE.', 'PJE. ')
    t = ' '.join(t.split())
    pal = []
    for w in t.split(' '):
        lw = w.lower()
        if lw in ('de', 'del', 'la', 'las', 'los', 'y', 'el'): pal.append(lw)
        elif lw in ('jr.', 'av.', 'pje.', 'prol.'): pal.append(lw.capitalize())
        else: pal.append(lw[:1].upper() + lw[1:])
    s = ' '.join(pal)
    return s[:1].upper() + s[1:]

# ---------------------------------------------------------------- propagación por nombre (mismo jirón)
def clave(s): return (s['nombre_osm'] or s['nombre_plano'] or '').upper()
por_nombre = collections.defaultdict(list)
for i, s in enumerate(segs):
    if clave(s): por_nombre[clave(s)].append(i)
for i, s in enumerate(segs):
    # ancho actual (mediana robusta) y bordes de calzada por vértice
    idx = [k for k, (si, _) in enumerate(muestras) if si == i] if False else None
for i, s in enumerate(segs):
    s['secc_cod'] = collections.Counter(c for _, c in s['secc']).most_common(1)[0][0] if s['secc'] else None
    s['prop'] = float(np.median([c[2] for c in s['cotas']])) if s['cotas'] else None
for k, lst in por_nombre.items():
    for i in lst:
        s = segs[i]; mid = s['g'].interpolate(0.5, normalized=True)
        if s['secc_cod'] is None:
            c = [(segs[j]['g'].distance(mid), segs[j]['secc_cod']) for j in lst if j != i and segs[j]['secc_cod']]
            c = [t for t in c if t[0] < 450]
            if c: s['secc_cod'] = min(c)[1]; s['secc_heredada'] = True
        if s['prop'] is None and s['secc_cod'] is None:
            c = [(segs[j]['g'].distance(mid), segs[j]['prop']) for j in lst if j != i and segs[j]['prop'] and segs[j]['cotas']]
            c = [t for t in c if t[0] < 220]
            if c: s['prop'] = min(c)[1]; s['prop_heredada'] = True

# ---------------------------------------------------------------- salida
inicio = 0; salida = []; nsin = 0
off = collections.Counter()
for i, s in enumerate(segs):
    n = len(s['s']); sl = slice(inicio, inicio + n); inicio += n
    a, b = dl[sl].copy(), dr[sl].copy(); qa, qb = ql[sl], qr[sl]
    W = a + b
    ok = np.isfinite(W) & (W < 40)
    ancho = float(np.median(W[ok])) if ok.sum() >= max(2, 0.3 * n) else None
    if ancho is None: nsin += 1
    # bordes de calzada (hasta el sardinel): distancia a la manzana menos su vereda; sin manzana -> ancho nominal
    medio = ANCHO[s['cl']] / 2
    v = VER[sl]
    def borde(d, q):
        e = np.where(np.isfinite(d) & (d < medio * 2.6 + 6), d - np.where(np.isfinite(v), v, 1.2), np.nan)
        e = np.where(np.isfinite(e), e, medio)
        e = median_filter(e, size=5, mode='nearest')
        return np.clip(e, 0.6, 22)
    el, er = borde(a, qa), borde(b, qb)
    # remuestrear a ~4 m para la cinta
    keep = np.unique(np.r_[np.arange(0, n, 2), n - 1])
    P = s['P'][keep]
    sec = s['secc_cod']
    salida.append({
        'id': i, 'nombre': s['nombre_osm'] or (titulo(s['nombre_plano']) if s['nombre_plano'] else None), 'osm': s['nombre_osm'], 'plano': titulo(s['nombre_plano']) if s['nombre_plano'] else None,
        'cl': s['cl'], 'clase': s['clase'], 'sp': s['sp'], 'pu': s['pu'],
        'c': [[round(float(x), 2), round(float(z), 2)] for x, z in P],
        'el': [round(float(v), 2) for v in el[keep]], 'er': [round(float(v), 2) for v in er[keep]],
        'fl': [round(float(v), 2) if np.isfinite(v) and v < 30 else -1 for v in median_filter(np.nan_to_num(a, nan=99), size=3, mode='nearest')[keep]],
        'fr': [round(float(v), 2) if np.isfinite(v) and v < 30 else -1 for v in median_filter(np.nan_to_num(b, nan=99), size=3, mode='nearest')[keep]],
        'ancho': None if ancho is None else round(ancho, 2),
        'amin': None if ancho is None else round(float(np.percentile(W[ok], 10)), 2), 'amax': None if ancho is None else round(float(np.percentile(W[ok], 90)), 2),
        'prop': s['prop'] if sec is None else SECC[sec]['total'], 'secc': sec, 'secc_h': bool(s.get('secc_heredada')), 'prop_h': bool(s.get('prop_heredada')),
        'cotas': s['cotas'], 'cortes': s['secc'], 'L': round(s['g'].length, 1),
    })
print('segmentos sin ancho medido', nsin, 'de', len(segs))
# ---------------------------------------------------------------- veredas a lo largo de las líneas de manzana
from scipy.spatial import cKDTree
okW = np.isfinite(Wm) & (Wm < 40)
kdW = cKDTree(M[okW]); WW = Wm[okW]
ejes = shapely.STRtree([sg['g'] for sg in segs])
pav = np.array([sg['sp'] != 2 and sg['cl'] <= 5 for sg in segs])
veredas = []
for g in LIN:
    a = np.asarray(g.coords)
    if len(a) < 2: continue
    run = None
    def cerrar():
        global run
        if run and len(run['p']) >= 2 and sum(np.hypot(*np.diff(np.array(run['p']), axis=0).T)) > 1.0: veredas.append(run)
        run = None
    for p, q in zip(a[:-1], a[1:]):
        L = np.hypot(*(q - p))
        if L < 0.05: continue
        t = (q - p) / L; n = np.array([-t[1], t[0]]); m = (p + q) / 2
        iz, de = m + n * 0.8, m - n * 0.8
        din = shapely.contains_xy(UMZ, [iz[0], de[0]], [iz[1], de[1]])
        if din[0] and not din[1]: lado = -1
        elif din[1] and not din[0]: lado = 1
        else:
            j1 = ejes.nearest(Point(iz)); j2 = ejes.nearest(Point(de))
            d1 = segs[j1]['g'].distance(Point(iz)); d2 = segs[j2]['g'].distance(Point(de))
            lado = 1 if d1 < d2 else -1
            if min(d1, d2) > 14: lado = 0
        # ancho de la calle frente a este tramo
        pr = m + n * lado * 2.0
        dd, kk = kdW.query(pr)
        w = vereda(WW[kk]) if (lado != 0 and dd < 12) else 0.0
        jn = ejes.nearest(Point(pr)); 
        if lado != 0 and (segs[jn]['g'].distance(Point(pr)) > 16 or not pav[jn]): w = 0.0
        if w <= 0 or lado == 0:
            cerrar(); continue
        if run and run['lado'] == lado and abs(run['w'] - w) < 0.01 and np.allclose(run['p'][-1], p): run['p'].append([round(float(q[0]), 2), round(float(q[1]), 2)])
        else:
            cerrar(); run = {'lado': lado, 'w': w, 'p': [[round(float(p[0]), 2), round(float(p[1]), 2)], [round(float(q[0]), 2), round(float(q[1]), 2)]]}
    cerrar()
print('tramos de vereda', len(veredas), 'longitud km', round(sum(sum(np.hypot(*np.diff(np.array(v['p']), axis=0).T)) for v in veredas) / 1000, 1))
json.dump({'secciones': SECC, 'locales': {str(k): v for k, v in LOCAL.items()}, 'calles': salida, 'veredas': veredas}, open('plan/calles.json', 'w'), ensure_ascii=False)
mz_out = []
for k, m in enumerate(MZ):
    ms = m.simplify(0.12)
    if ms.is_empty or ms.geom_type != 'Polygon': ms = m
    mz_out.append({'id': k, 'p': [[round(x, 2), round(z, 2)] for x, z in ms.exterior.coords[:-1]],
                   'h': [[[round(x, 2), round(z, 2)] for x, z in r.coords[:-1]] for r in ms.interiors],
                   'area': round(m.area, 1), 'per': round(m.length, 1)})
json.dump(mz_out, open('plan/manzanas.json', 'w'))
print('manzanas', len(mz_out))
# resumen de anchos
A = np.array([s['ancho'] for s in salida if s['ancho']]); Pp = [s for s in salida if s['prop']]
print('ancho actual: p10 %.1f p50 %.1f p90 %.1f' % tuple(np.percentile(A, [10, 50, 90])), '| con ancho propuesto', len(Pp), '| con sección', sum(1 for s in salida if s['secc']))
for s in salida:
    if s['nombre'] and 'chanchamayo' in s['nombre'].lower(): print('Chanchamayo seg', s['id'], 'L', s['L'], 'ancho', s['ancho'], s['amin'], s['amax'], 'prop', s['prop'], 'secc', s['secc'], s['secc_h'], 'cortes', s['cortes'])
