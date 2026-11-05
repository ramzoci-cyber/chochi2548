# Empaqueta para el visor: mapas de la tesis (peligro y riesgo por escenario), unidades, puntos críticos y resultados de
# la simulación 2D (tirante máximo, velocidad, hora del máximo, instantáneas) recortados a la zona urbana; estadísticas
# y comparación tesis/simulación. Salida: inund/datos_mod.json (datos base + C.inundacion) e inund/resumen.json
import json, base64, zlib, sys, numpy as np, shapely, rasterio.features, rasterio.transform
from shapely.geometry import Polygon
from scipy.ndimage import maximum_filter
ETQ = sys.argv[1] if len(sys.argv) > 1 else 'final'
def b64(a): return base64.b64encode(zlib.compress(np.ascontiguousarray(a).tobytes(), 9)).decode()
C = json.load(open('inund/datos_base.json'))
U = json.load(open('tesis/riesgo_unidades.json')); P = np.load('tesis/peligro_malla10.npz')
LL = json.load(open('tesis/lluvia_diseno.json')); E = json.load(open('sim/entradas.json'))
CAL = json.load(open('sim/calibracion_final.json'))
UMB = CAL['umbrales']; MAT = CAL['matriz']
ESC = U['escenarios']
NOMBRES = {'presente': ('Presente 1981-2020', 'Pres.', 'Presente', '—', '1981-2020'),
           'cmip5_rcp45_2031_2060': ('CMIP5 · emisiones moderadas (RCP 4.5) · 2031-2060', 'Q-M1', 'CMIP5', 'Moderadas', '2031-2060'),
           'cmip5_rcp45_2071_2100': ('CMIP5 · emisiones moderadas (RCP 4.5) · 2071-2100', 'Q-M2', 'CMIP5', 'Moderadas', '2071-2100'),
           'cmip5_rcp85_2031_2060': ('CMIP5 · emisiones altas (RCP 8.5) · 2031-2060', 'Q-A1', 'CMIP5', 'Altas', '2031-2060'),
           'cmip5_rcp85_2071_2100': ('CMIP5 · emisiones altas (RCP 8.5) · 2071-2100', 'Q-A2', 'CMIP5', 'Altas', '2071-2100'),
           'cmip6_ssp245_2031_2060': ('CMIP6 · emisiones moderadas (SSP2-4.5) · 2031-2060', 'S-M1', 'CMIP6', 'Moderadas', '2031-2060'),
           'cmip6_ssp245_2071_2100': ('CMIP6 · emisiones moderadas (SSP2-4.5) · 2071-2100', 'S-M2', 'CMIP6', 'Moderadas', '2071-2100'),
           'cmip6_ssp585_2031_2060': ('CMIP6 · emisiones altas (SSP5-8.5) · 2031-2060', 'S-A1', 'CMIP6', 'Altas', '2031-2060'),
           'cmip6_ssp585_2071_2100': ('CMIP6 · emisiones altas (SSP5-8.5) · 2071-2100', 'S-A2', 'CMIP6', 'Altas', '2071-2100')}
TESIS = {  # cuadros C-01, C-03 y C-04 (tabla 5 del artículo)
    'presente': (21.6, 6.1, 63, 2606, 90, 9, None), 'cmip5_rcp45_2031_2060': (23.4, 8.0, 63, 2606, 90, 9, 'sí'), 'cmip5_rcp45_2071_2100': (24.1, 9.5, 63, 2606, 90, 9, 'sí'),
    'cmip5_rcp85_2031_2060': (39.1, 12.4, 76, 2913, 96, 11, 'no'), 'cmip5_rcp85_2071_2100': (97.3, 95.6, 203, 5714, 108, 15, 'sí'),
    'cmip6_ssp245_2031_2060': (22.6, 7.7, 63, 2606, 90, 9, 'sí'), 'cmip6_ssp245_2071_2100': (46.3, 22.1, 77, 2921, 96, 11, 'sí'),
    'cmip6_ssp585_2031_2060': (23.0, 7.8, 63, 2606, 90, 9, 'sí'), 'cmip6_ssp585_2071_2100': (48.3, 28.8, 78, 2943, 97, 11, 'sí')}
W, H = 520, 800
tr = rasterio.transform.Affine(10, 0, -2600, 0, 10, -4000)
upol = [Polygon(u['local']).buffer(0) for u in U['unidades']]
urb = shapely.union_all(upol)
murb = rasterio.features.rasterize([(urb, 1)], out_shape=(H, W), transform=tr, dtype='uint8').astype(bool)
x0, z0, x1, z1 = urb.bounds
i0 = max(0, int((x0 - 150 + 2600) // 10)); i1 = min(W, int((x1 + 150 + 2600) // 10) + 1)
j0 = max(0, int((z0 - 150 + 4000) // 10)); j1 = min(H, int((z1 + 150 + 4000) // 10) + 1)
RC = {'i0': i0, 'j0': j0, 'w': i1 - i0, 'h': j1 - j0}
rec = (slice(j0, j1), slice(i0, i1))
print('recorte', RC)
# máscaras por unidad (con 10 m de borde para incluir la calle contigua)
mU = [rasterio.features.rasterize([(g.buffer(10), 1)], out_shape=(H, W), transform=tr, dtype='uint8', all_touched=True).astype(bool) for g in upol]
# edificios: celdas de su huella (centroide + representative)
EDU = json.load(open('inund/edificios_unidad.json'))
from shapely.geometry import Point
import base64 as _b, zlib as _z
def inflar(s, dt): return np.frombuffer(_z.decompress(_b.b64decode(s)), dtype=dt)
nV = inflar(C['edificios']['n'], np.uint16); pri = inflar(C['edificios']['pri'], np.int32).reshape(-1, 2); dlt = inflar(C['edificios']['dlt'], np.int16).reshape(-1, 2)
celdas_ed = []; iD = 0
for b in range(C['edificios']['cuenta']):
    n = int(nV[b]); x = pri[b, 0] / 10; z = pri[b, 1] / 10
    pts = [(x, z)] + [(x + dlt[iD + k, 0] / 10, z + dlt[iD + k, 1] / 10) for k in range(n - 1)]; iD += n - 1
    q = Polygon(pts).buffer(3)                                            # agua al pie de la edificación (3 m alrededor)
    bx = q.bounds; ii = np.arange(int((bx[0] + 2600) // 10), int((bx[2] + 2600) // 10) + 1); jj = np.arange(int((bx[1] + 4000) // 10), int((bx[3] + 4000) // 10) + 1)
    celdas_ed.append((np.clip(jj, 0, H - 1), np.clip(ii, 0, W - 1)))
def kappa(a, b, k):
    m = np.zeros((k, k))
    for i in range(k):
        for j in range(k): m[i, j] = ((a == i + 1) & (b == j + 1)).sum()
    n = m.sum(); po = np.trace(m) / n; pe = (m.sum(0) * m.sum(1)).sum() / n / n
    return (po - pe) / (1 - pe) if pe < 1 else 0.0, po
def clase(h): return np.where(h < UMB[0], 1, np.where(h < UMB[1], 2, np.where(h < UMB[2], 3, 4)))
escs = []; resumen = {}
uni_rs = np.zeros((len(upol), len(ESC)), np.uint8); uni_hs = np.zeros((len(upol), len(ESC)), np.uint8)
crit = [{'n': c['n'], 'local': c['local'], 'unidad': c['unidad'] if c['unidad'] is not None else -1, 'h': [], 'v': []} for c in U['criticos']]
T0, T1, DTS = 10.0, 17.0, 15
for k, e in enumerate(ESC):
    R = np.load(f'sim/res_{e}_{ETQ}.npz')
    hmax, vmax, tmax, snaps, tsn = R['hmax'], R['vmax'], R['tmax'], R['snaps'].astype(np.float32), R['t_snap']
    sel = [i for i, t in enumerate(tsn) if T0 * 3600 - 1 <= t <= T1 * 3600 + 1 and int(round((t - T0 * 3600) / 60)) % DTS == 0]
    S = np.stack([snaps[i][rec] for i in sel])
    q8 = lambda a, paso, tope=255: np.clip(np.round(a / paso), 0, tope).astype(np.uint8)
    S8 = q8(np.where(S < 0.03, 0, S), 0.02); H8 = q8(np.where(hmax[rec] < 0.03, 0, hmax[rec]), 0.02)
    V8 = q8(vmax[rec], 0.05); T8 = np.where(hmax[rec] >= 0.03, np.clip(np.round((tmax[rec] - T0 * 3600) / 300), 0, 255), 0).astype(np.uint8)
    # estadísticas en la zona urbana evaluada
    a01 = float(((hmax >= 0.10) & murb).sum() * 100 / 1e6); a05 = float(((hmax >= 0.50) & murb).sum() * 100 / 1e6)
    serie = [round(float(((s >= 0.10) & murb[rec]).sum() * 100 / 1e6), 3) for s in S]
    ed03 = int(sum(1 for (jj, ii) in celdas_ed if hmax[np.ix_(jj, ii)].max() >= 0.30))
    # peligro simulado (celdas, agregación a ~30 m) y comparación con la tesis
    hv = maximum_filter(hmax, size=3); cs = clase(hv); ct = P[e]; m = murb & (ct > 0)
    k2, po2 = kappa((cs[m] >= 3).astype(int) + 1, (ct[m] >= 3).astype(int) + 1, 2)
    # por unidad: P90 del tirante (unidad + 10 m), peligro y riesgo simulados
    for u, mm in enumerate(mU):
        h90 = float(np.percentile(hmax[mm], 90)) if mm.any() else 0.0
        hc = int(clase(np.array([h90]))[0]); v = U['unidades'][u]['vuln']
        uni_hs[u, k] = min(255, int(round(h90 / 0.02))); uni_rs[u, k] = MAT[hc - 1][v - 1] if v > 0 else 0
    rt = np.array([u['riesgo'][e] for u in U['unidades']])
    ku, pou = kappa(uni_rs[:, k].astype(int), rt, 4)
    nc = 0
    for c in crit:
        i = int((c['local'][0] + 2600) // 10); j = int((c['local'][1] + 4000) // 10)
        h3 = float(hmax[max(0, j - 3):j + 4, max(0, i - 3):i + 4].max()); v3 = float(vmax[max(0, j - 3):j + 4, max(0, i - 3):i + 4].max())
        c['h'].append(round(h3, 2)); c['v'].append(round(v3, 2)); nc += h3 >= UMB[1]          # punto en peligro alto o muy alto
    nom = NOMBRES[e]; tt = TESIS[e]
    sim = {'area01': round(a01, 3), 'area05': round(a05, 3), 'edif03': ed03, 'criticos': nc, 'unidades': int((uni_rs[:, k] >= 3).sum()),
           'kappa_celdas': round(k2, 3), 'acuerdo_celdas': round(po2, 3), 'kappa_unidades': round(ku, 3), 'acuerdo_unidades': round(pou, 3),
           'pct_ama': round(float(100 * (cs[m] >= 3).mean()), 1), 'serie': serie}
    escs.append({'id': e, 'nombre': nom[0], 'corto': nom[1], 'gen': nom[2], 'emis': nom[3], 'horiz': nom[4],
                 'P24': LL['plaza_tabla'][k], 'cambio': round(100 * (LL['plaza_tabla'][k] / LL['plaza_tabla'][0] - 1), 1) if k else 0,
                 'hiet': E['hietogramas'][e]['mm10'], 'qpico': CAL['qpico'][e],
                 'tesis': {'pct_ciudad': tt[0], 'pct_cuenca': tt[1], 'unidades': tt[2], 'edificaciones': tt[3], 'servicios': tt[4], 'criticos': tt[5], 'hipotesis3': tt[6],
                           'unidades_mapa': int((rt >= 3).sum()), 'pct_mapa_unidades': round(float(100 * (ct[m] >= 3).mean()), 1)},
                 'sim': sim,
                 'b64': {'hmax': b64(H8), 'vmax': b64(V8), 'tmax': b64(T8), 'peligro': b64(P[e][rec].astype(np.uint8)), 'snaps': b64(S8)}})
    resumen[e] = {kk: vv for kk, vv in sim.items() if kk != 'serie'}
    print('%-24s P24 %.1f | inundado>10cm %.2f km2 | >50cm %.2f | edif>30cm %d | críticos %d/15 | unidades R>=alto sim %d (tesis %d) | kappa celdas %.2f unidades %.2f | %d KB' % (
        e, LL['plaza_tabla'][k], a01, a05, ed03, nc, sim['unidades'], (rt >= 3).sum(), k2, ku, sum(len(v) for v in escs[-1]['b64'].values()) // 1024))
np.savez_compressed('inund/unidades_sim.npz', h90=uni_hs.astype(np.float32) * 0.02, riesgo=uni_rs, esc=np.array(ESC))
UB = U['unidades']
nv = np.array([len(u['local']) for u in UB], np.uint16); vv = np.vstack([np.array(u['local']) for u in UB]).astype(np.float32)
ne = np.zeros(len(UB), np.uint16)
for u_, a_ in EDU:
    if u_ >= 0: ne[u_] += 1
C['inundacion'] = {
    'escenarios': escs, 'recorte': RC, 'tiempo': {'t0_h': T0, 'dt_min': DTS, 'n': len(sel)}, 'umbrales': UMB, 'matriz': MAT,
    'unidades': {'n': len(UB), 'nv': b64(nv), 'v': b64(vv), 'tipo': b64(np.array([1 if u['tipo'] == 'celda 1 ha' else 0 for u in UB], np.uint8)),
                 'vuln': b64(np.array([u['vuln'] for u in UB], np.uint8)), 'riesgo': b64(np.array([[u['riesgo'][e] for e in ESC] for u in UB], np.uint8)),
                 'riesgo_sim': b64(uni_rs), 'h_sim': b64(uni_hs), 'edif': b64(ne), 'area': [u['area_m2'] for u in UB]},
    'criticos': crit, 'calibracion': {'parametros': CAL['parametros'], 'metricas': CAL['metricas_presente']},
}
pc = C['inundacion']['criticos'][0]['local']; C['punto_critico'] = pc
json.dump(C, open('inund/datos_mod.json', 'w'), ensure_ascii=False)
json.dump({'recorte': RC, 'umbrales': UMB, 'escenarios': resumen, 'criticos': crit}, open('inund/resumen.json', 'w'), ensure_ascii=False, indent=1)
print('inund/datos_mod.json', len(json.dumps(C)) // 1024, 'KB')
