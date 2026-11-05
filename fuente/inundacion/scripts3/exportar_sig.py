# Capas SIG y tablas de la versión de inundaciones:
#   unidades_riesgo.geojson   manzanas y celdas de 1 ha de C-04 con vulnerabilidad, riesgo de la tesis y riesgo simulado por escenario
#   puntos_criticos.geojson   15 puntos críticos con tirante y velocidad máximos simulados por escenario
#   tirante_max_<esc>.tif     tirante máximo simulado (m), malla de 10 m, EPSG:32718 (marco del Plano Total 2025)
#   resumen_escenarios.csv    lluvia, tesis y simulación por escenario
#   calibracion.csv           corridas de calibración (escenario presente) y su acuerdo con C-04
# Uso: python exportar_sig.py <carpeta_salida>
import json, sys, os, csv, numpy as np, rasterio, rasterio.transform
from pyproj import Transformer
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
U = json.load(open('tesis/riesgo_unidades.json')); ESC = U['escenarios']
CAL = json.load(open('sim/calibracion_final.json')); RES = json.load(open('inund/resumen.json'))
LL = json.load(open('tesis/lluvia_diseno.json')); US = np.load('inund/unidades_sim.npz')
D = json.load(open('inund/datos_mod.json'))['inundacion']
CORTO = {e['id']: e['corto'].replace('.', '').replace('-', '').upper() for e in D['escenarios']}   # PRES, QM1 ... SA2 (sin puntos ni guiones)
NOM = ['', 'bajo', 'medio', 'alto', 'muy alto']; NOMV = ['', 'baja', 'media', 'alta', 'muy alta']
a_geo = Transformer.from_crs(32718, 4326, always_xy=True)
def geo(x, z):                       # marco local del modelo -> UTM 18S -> WGS84
    lon, lat = a_geo.transform(np.asarray(x) + 424400.0, 8738400.0 - np.asarray(z)); return lon, lat
# ---- unidades
feats = []
for k, u in enumerate(U['unidades']):
    p = np.array(u['local']); lon, lat = geo(p[:, 0], p[:, 1])
    anillo = [[round(float(a), 7), round(float(b), 7)] for a, b in zip(lon, lat)]
    if anillo[0] != anillo[-1]: anillo.append(anillo[0])
    pr = {'id': k, 'tipo': u['tipo'], 'area_m2': round(u['area_m2'], 1), 'vulnerabilidad': NOMV[u['vuln']] if u['vuln'] else None}
    for j, e in enumerate(ESC):
        c = CORTO[e]
        pr[f'riesgo_tesis_{c}'] = NOM[u['riesgo'][e]] if u['riesgo'][e] else None
        pr[f'riesgo_sim_{c}'] = NOM[int(US['riesgo'][k, j])] if US['riesgo'][k, j] else None
        pr[f'h90_sim_{c}_m'] = round(float(US['h90'][k, j]), 2)
    feats.append({'type': 'Feature', 'properties': pr, 'geometry': {'type': 'Polygon', 'coordinates': [anillo]}})
leyenda = {CORTO[e['id']]: e['nombre'] for e in D['escenarios']}
json.dump({'type': 'FeatureCollection', 'name': 'unidades_riesgo', 'escenarios': leyenda, 'features': feats}, open(f'{OUT}/unidades_riesgo.geojson', 'w'), ensure_ascii=False)
# ---- puntos críticos
feats = []
for c, ci in zip(D['criticos'], U['criticos']):
    lon, lat = geo(c['local'][0], c['local'][1])
    pr = {'punto': f"PC-{c['n']}", 'E_utm': round(c['local'][0] + 424400.0, 1), 'N_utm': round(8738400.0 - c['local'][1], 1)}
    for j, e in enumerate(ESC):
        pr[f'h_max_{CORTO[e]}_m'] = c['h'][j]; pr[f'v_max_{CORTO[e]}_ms'] = c['v'][j]
    feats.append({'type': 'Feature', 'properties': pr, 'geometry': {'type': 'Point', 'coordinates': [round(float(lon), 7), round(float(lat), 7)]}})
json.dump({'type': 'FeatureCollection', 'name': 'puntos_criticos', 'escenarios': leyenda, 'features': feats}, open(f'{OUT}/puntos_criticos.geojson', 'w'), ensure_ascii=False)
# ---- tirante máximo por escenario (GeoTIFF norte arriba: fila 0 = z mínimo = norte)
tr = rasterio.transform.from_origin(424400.0 - 2600.0, 8738400.0 + 4000.0, 10.0, 10.0)
for e in ESC:
    hm = np.load(f'sim/res_{e}_final.npz')['hmax'].astype(np.float32)
    hm = np.where(hm < 0.02, 0, np.round(hm, 2)).astype(np.float32)
    with rasterio.open(f'{OUT}/tirante_max_{CORTO[e]}.tif', 'w', driver='GTiff', width=hm.shape[1], height=hm.shape[0], count=1, dtype='float32',
                       crs='EPSG:32718', transform=tr, compress='deflate', predictor=3, nodata=None) as f:
        f.write(hm, 1); f.update_tags(escenario=e, unidad='m', umbrales_peligro=','.join(str(x) for x in CAL['umbrales']))
# ---- resumen por escenario
with open(f'{OUT}/resumen_escenarios.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['escenario', 'codigo', 'P24_plaza_mm', 'cambio_pct', 'tesis_pct_ciudad_peligro_alto', 'tesis_pct_cuenca_peligro_alto', 'tesis_unidades_riesgo_alto',
                'tesis_edificaciones_riesgo_alto', 'tesis_criticos', 'mapa_unidades_riesgo_alto', 'sim_area_10cm_km2', 'sim_area_50cm_km2',
                'sim_unidades_riesgo_alto', 'sim_edificaciones_30cm', 'sim_criticos_peligro_alto', 'kappa_unidades', 'acuerdo_unidades',
                'kappa_celdas_2clases', 'sim_pct_peligro_alto_unidades', 'q_pico_oeste_m3s', 'q_pico_sur_m3s'])
    for e in D['escenarios']:
        T = e['tesis']; S = e['sim']
        w.writerow([e['nombre'], CORTO[e['id']], e['P24'], e['cambio'], T['pct_ciudad'], T['pct_cuenca'], T['unidades'], T['edificaciones'], T['criticos'],
                    T['unidades_mapa'], S['area01'], S['area05'], S['unidades'], S['edif03'], S['criticos'], S['kappa_unidades'], S['acuerdo_unidades'],
                    S['kappa_celdas'], S['pct_ama'], e['qpico'][0], e['qpico'][1]])
# ---- calibración
if os.path.exists('sim/calibracion_unidades.json'):
    C = json.load(open('sim/calibracion_unidades.json'))
    with open(f'{OUT}/calibracion.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); cols = ['corrida', 'dCN', 'prof_cauce_m', 'n_bloque', 'edificaciones_m', 'umbrales', 'k4', 'kw', 'k2', 'po4', 'n3', 'n3t', 'pc10', 'pc30']
        w.writerow(cols)
        for r in C: w.writerow([' / '.join(str(x) for x in r[c]) if c == 'umbrales' else r[c] for c in cols])
for n in sorted(os.listdir(OUT)): print('%-36s %8.1f KB' % (n, os.path.getsize(f'{OUT}/{n}') / 1024))
