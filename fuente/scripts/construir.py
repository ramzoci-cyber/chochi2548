# Ensambla los datos del Jr. Chanchamayo detallado y ajusta los datos originales del modelo de Tarma
import json, base64, zlib, random, math, numpy as np, shapely
from shapely.geometry import Polygon, Point, LineString
from scipy.ndimage import gaussian_filter1d
C = json.load(open('orig/datos_clean.json'))
W, H, CEL = C['W'], C['H'], C['celda']; MX, MZ = W * CEL / 2, H * CEL / 2
Z = np.load('orig/z.npy').astype(np.float64)          # relativo a zmin
def altura(x, z, A=Z):
    fi = (x + MX) / CEL - 0.5; fj = (z + MZ) / CEL - 0.5
    fi = min(W - 1.001, max(0, fi)); fj = min(H - 1.001, max(0, fj))
    i = int(fi); j = int(fj); a = fi - i; b = fj - j
    return (A[j, i] * (1 - a) + A[j, i + 1] * a) * (1 - b) + (A[j + 1, i] * (1 - a) + A[j + 1, i + 1] * a) * b
e = np.load('data/eje_fino.npz'); fl = np.load('data/fline.npz')
S5, cx5, cz5 = e['S'], e['cx'], e['cz']
L = float(S5[-1])
# eje cada 1 m
S = np.linspace(0, L, int(round(L)) + 1)          # paso ~1 m exacto (L / (n-1))
cx = np.interp(S, S5, cx5); cz = np.interp(S, S5, cz5)
def muestrear(arr):           # sin interpolar contra los huecos (NaN = cruce)
    idx = np.clip(np.round(S / 0.5).astype(int), 0, len(arr) - 1)
    v = arr[idx]; return np.where(np.isfinite(v), v, -1.0)
fE = muestrear(fl['E']); fO = muestrear(fl['O'])
tx = np.gradient(cx); tz = np.gradient(cz); nn = np.hypot(tx, tz); tx /= nn; tz /= nn
nx, nz = -tz, tx                                    # lado +1 = Este/Sureste
# ---------- perfil longitudinal: isotónico (no creciente hacia el norte) + suavizado
y = np.array([altura(a, b) for a, b in zip(cx, cz)])
def pava_decreciente(v):
    # regresión isotónica no creciente (pool adjacent violators)
    v = list(-v); bloques = [[x, 1] for x in v]; i = 0
    res = []
    for x in v:
        res.append([x, 1])
        while len(res) > 1 and res[-2][0] > res[-1][0]:
            a, b = res.pop(); c, d = res.pop(); res.append([(a * b + c * d) / (b + d), b + d])
    out = []
    for x, k in res: out += [x] * k
    return -np.array(out)
yi = pava_decreciente(y)
ys = gaussian_filter1d(yi, 12, mode='nearest')
for k in range(1, len(ys)):          # garantiza pendiente mínima 0,2 % para drenaje
    ys[k] = min(ys[k], ys[k - 1] - 0.002 * (S[k] - S[k - 1]))
print('perfil: %.2f -> %.2f m (rel), caída %.2f m, max dif con DEM %.2f' % (ys[0], ys[-1], ys[0] - ys[-1], np.abs(ys - y).max()))
# ---------- datos de lotes
D = json.load(open('data/lotes.json'))
cruces = json.load(open('data/cruces.json'))
lotes = [l for l in D['lotes'] if not (l['lado'] == 1 and l['s0'] > 730)]       # tribuna del estadio: se modela aparte
cercos = [c for c in D['cercos'] if not (c['lado'] == 1 and c['s0'] > 735)]
print('lotes', len(lotes), 'cercos', len(cercos))
# cuadras (numeración crece hacia la Plaza: C1 al norte)
CUADRAS = [(7, 0.0, 74.0), (6, 74.0, 288.7), (5, 288.7, 378.7), (4, 378.7, 463.0), (3, 463.0, 540.8), (2, 540.8, 612.1), (1, 612.1, 682.7)]
def cuadra_de(s):
    for k, a, b in CUADRAS:
        if a <= s < b: return k, a, b
    return 0, 682.7, L
def numero(s, lado):
    k, a, b = cuadra_de(s)
    if k == 0: return None
    t = (b - s) / (b - a)
    n = k * 100 + int(round(2 + t * 95))
    par = (lado == -1)
    if (n % 2 == 0) != par: n += 1 if n % 100 < 98 else -1
    return n
# negocios con dirección en el Jr. Chanchamayo (Overture Places / Meta; web) -> estación aprox.
POIS = [('TRATTORIA TARMA', 698, (686.8, 841.6)), ('MAVYS BEAUTY STUDIO', 676, (737.1, 817.0)), ('RECEPCIONES CRUZ', 663, (735.3, 778.8)),
        ('NOTARÍA PAULO VIVAS SIERRA', 617, (846.6, 737.6)), ('DECOR MUEBLES 3D', 545, (895.5, 664.8)), ('SALÓN DE BELLEZA HILDA', 532, (880.2, 668.5)),
        ('PARADISE SUITE HOTEL', 484, (902.2, 645.9)), ('PLAZA SEIKO', 466, (900.5, 614.1)), ('POWER GYM', 463, (907.8, 609.9)),
        ('RESTAURANTE MARCELITA 2', 228, (934.7, 433.6)), ('BOTICAS ECONOPHAR', 343, None), ('MINISTERIO PÚBLICO', 512, None)]
eje_ls = LineString(np.c_[cx, cz])
def s_de_numero(n):
    k = n // 100
    for kk, a, b in CUADRAS:
        if kk == k: return b - (n % 100) / 100 * (b - a)
asign = {}
for nom, n, xy in POIS:
    s_n = s_de_numero(n); lado = -1 if n % 2 == 0 else 1
    if xy is not None:
        s_m = eje_ls.project(Point(xy))
        if abs(s_m - s_n) < 35: s_n = 0.5 * (s_n + s_m)
    cands = [i for i, l in enumerate(lotes) if l['lado'] == lado]
    i = min(cands, key=lambda i: 0 if lotes[i]['s0'] <= s_n <= lotes[i]['s1'] else min(abs(lotes[i]['s0'] - s_n), abs(lotes[i]['s1'] - s_n)))
    while i in asign:        # siguiente lote libre más cercano
        cands = [j for j in cands if j not in asign]
        i = min(cands, key=lambda j: min(abs(lotes[j]['s0'] - s_n), abs(lotes[j]['s1'] - s_n)))
    asign[i] = (nom, n)
    print('POI', nom, n, '-> lote', i, lotes[i]['s0'], lotes[i]['s1'], 'lado', lado)
# ---------- tipologías (reglas + azar con semilla fija; editable)
PINTURA = ['#E9DCC0', '#EFE8D8', '#E8C25A', '#D9A441', '#E9A27C', '#C8643B', '#9FC6DD', '#A8D5BA', '#C9D86B', '#B9A2C8', '#E7A3B1',
           '#5C7FB0', '#E98B3A', '#F2E6C9', '#BDB9B0', '#D7C49E', '#8FB3A0', '#F0D7A8']
ZOCALO = ['#7A3B2E', '#3F5B43', '#5A4636', '#44546A', '#8C8C86', '#6B2E2E', '#2F4B5C']
MADERA = ['#5B3A24', '#6E4529', '#3E2A1C', '#2F4A3A', '#2E4466']
METAL = ['#6F7377', '#4A6B8A', '#3D5C45', '#8A8F93', '#7B2E2E', '#C9C6BE', '#2B2D30']
for i, l in enumerate(lotes):
    rnd = random.Random(1000 + i * 7919)
    s = 0.5 * (l['s0'] + l['s1'])
    h = float(np.clip(l['h'], 3.0, 21.0))
    pisos = int(np.clip(round((h - 0.6) / 2.75), 1, 7))
    r, g, b = l['tex']; rojizo = (r - b) > 0.12
    p_ad = 0.42 if s < 290 else (0.28 if s < 480 else 0.2)
    if rojizo: p_ad += 0.15
    if pisos <= 2 and rnd.random() < p_ad: tipo = 'adobe'
    else: tipo = 'ladrillo' if rnd.random() < 0.42 else 'tarrajeo'
    p_com = 0.65 if s < 480 else 0.45
    uso = 'comercio' if rnd.random() < p_com else 'vivienda'
    if i in asign: uso = 'comercio'
    l.update({
        'id': i, 'pisos': pisos, 'alto': round(h, 1), 'tipo': tipo, 'uso': uso,
        'cuadra': cuadra_de(s)[0], 'num': numero(s, l['lado']),
        'pared': rnd.choice(PINTURA) if tipo != 'adobe' else rnd.choice(['#F1ECE0', '#EDE3CF', '#F3EBD9', '#E8D9B8', '#DDE6EA', '#F2E3C6']),
        'zocalo': rnd.choice(ZOCALO), 'madera': rnd.choice(MADERA), 'metal': rnd.choice(METAL),
        'volado': bool(tipo != 'adobe' and pisos >= 2 and rnd.random() < 0.45),
        'balcon': bool(pisos >= 2 and rnd.random() < (0.55 if tipo == 'adobe' else 0.35)),
        'inconcluso': bool(tipo != 'adobe' and rnd.random() < (0.55 if tipo == 'ladrillo' else 0.22)),
        'tanque': bool(tipo != 'adobe' and rnd.random() < 0.78),
        'techo': 'teja' if tipo == 'adobe' else ('calamina' if (pisos == 1 and rnd.random() < 0.45) else 'losa'),
        'mixto': bool(tipo == 'ladrillo' and rnd.random() < 0.5),       # 1er piso tarrajeado y pintado
        'semilla': rnd.randint(0, 99999),
    })
    if i in asign: l['nombre'], l['num'] = asign[i][0], asign[i][1]
for c in cercos:
    rnd = random.Random(int(c['s0'] * 100) + c['lado'])
    c['alto'] = round(rnd.uniform(2.2, 3.0), 2); c['color'] = rnd.choice(PINTURA + ['#B8B2A7', '#C9A27E'])
    c['porton'] = rnd.choice(['metal', 'madera', 'reja']); c['ladrillo'] = rnd.random() < 0.45
# ---------- caras de manzana (veredas)
caras = [{'lado': t['lado'], 's0': t['s0'], 's1': t['s1']} for t in D['tramos']]
# ---------- cruces (fusionados por estación)
SEMAF = [(906, 619), (848, 719), (963, 247)]
cr = {}
for c in cruces:
    k = round(c['s'])
    cr.setdefault(k, []).append(c)
crs = []
for k, lst in sorted(cr.items()):
    s = lst[0]['s']; i = int(round(s))
    semaf = any(math.hypot(cx[min(i, len(cx) - 1)] - a, cz[min(i, len(cz) - 1)] - b) < 12 for a, b in SEMAF)
    crs.append({'s': round(s, 1), 'semaforo': semaf, 'ramas': [{'nombre': c['nombre'], 'lado': c['lado'], 'dir': c['dir']} for c in lst]})
# ---------- mobiliario
rnd = random.Random(42)
postes = []; s = 8.0; lado = 1
while s < L - 4:
    # evitar cruces
    if all(abs(s - c['s']) > 7 for c in crs):
        postes.append({'s': round(s, 1), 'lado': lado, 'luz': True, 'trafo': rnd.random() < 0.12})
        lado = -lado; s += rnd.uniform(28, 36)
    else: s += 3
buzones = [round(c['s'] + (6 if c['s'] < L - 10 else -6), 1) for c in crs] + [round(v, 1) for v in np.arange(40, L, 55)]
buzones = sorted(set(b for b in buzones if 2 < b < L - 2))
sumideros = []
for c in crs:
    for d in (-7.5, 7.5):
        sv = c['s'] + d
        if 1 < sv < L - 1:
            for ld in (1, -1): sumideros.append({'s': round(sv, 1), 'lado': ld})
vehic = []
for k in range(70):
    sv = rnd.uniform(6, L - 6)
    if any(abs(sv - c['s']) < 9 for c in crs): continue
    ld = 1 if rnd.random() < 0.85 else -1
    t = rnd.choices(['auto', 'mototaxi', 'combi', 'camioneta'], [0.5, 0.3, 0.08, 0.12])[0]
    if all(abs(sv - v['s']) > 7 or v['lado'] != ld for v in vehic):
        vehic.append({'s': round(sv, 1), 'lado': ld, 'tipo': t, 'color': rnd.choice(['#C8C8C8', '#1F1F22', '#B22222', '#F2F2F2', '#2D4F8A', '#E6C229', '#6E7B85', '#7A1F1F', '#2E6B4F'])})
print('postes', len(postes), 'buzones', len(buzones), 'sumideros', len(sumideros), 'vehiculos', len(vehic))
# ---------- veredas: ancho por lado y estación
def ancho_vereda(ftot):
    return float(np.clip(0.15 * ftot, 0.9, 1.8))
CH = {
    'L': round(L, 2), 'eje': [[round(float(a), 2), round(float(b), 2)] for a, b in zip(cx, cz)],
    'y': [round(float(v), 3) for v in ys],
    'fE': [round(float(v), 2) for v in fE], 'fO': [round(float(v), 2) for v in fO],
    'caras': caras, 'cruces': crs, 'lotes': lotes, 'cercos': cercos,
    'postes': postes, 'buzones': buzones, 'sumideros': sumideros, 'vehiculos': vehic,
    'cuadras': [{'n': k, 's0': a, 's1': b} for k, a, b in CUADRAS],
}
import os
if os.path.exists('data/area_eje.json'):
    AE = json.load(open('data/area_eje.json'))
    Aa = np.array(AE['A'], dtype=float)
    CH['A'] = [round(float(v)) for v in np.interp(np.arange(len(S)), np.linspace(0, len(S) - 1, len(Aa)), Aa)]
    CH['sT01'] = AE['sT01']; CH['Amc'] = AE['Amc']
json.dump(CH, open('data/chanchamayo.json', 'w'), ensure_ascii=False)
np.savez('data/eje1m.npz', S=S, cx=cx, cz=cz, nx=nx, nz=nz, ys=ys, fE=fE, fO=fO)
print('chanchamayo.json', len(json.dumps(CH, ensure_ascii=False)) // 1024, 'KB')
