# Exporta lo extraído de los planos (PDU Tarma / Plano Total 2025) a formatos de SIG y hoja de cálculo
#   manzanas_plano.geojson, vias_plano.geojson, cotas_vias_locales.geojson, secciones_viales.csv,
#   perfil_jr_chanchamayo.csv, mde_plano_5m.tif (EPSG:32718) y curvas_nivel_plano.gpkg
import json, csv, sys, pickle, re, numpy as np, shapely
from shapely.geometry import LineString, Polygon, mapping
from pyproj import Transformer
import rasterio, rasterio.transform
SAL = sys.argv[1] if len(sys.argv) > 1 else 'salida_plano'
T = Transformer.from_crs('EPSG:32718', 'EPSG:4326', always_xy=True)
def wgs_local(x, z):
    lon, lat = T.transform(np.asarray(x) + 424400, 8738400 - np.asarray(z)); return lon, lat
def coords_local(a):
    lon, lat = wgs_local(a[:, 0], a[:, 1]); return [[round(float(u), 7), round(float(v), 7)] for u, v in zip(lon, lat)]
def fc(nombre, feats): return {'type': 'FeatureCollection', 'name': nombre, 'features': feats}
CAL = json.load(open('plan/calles.json')); MZ = json.load(open('plan/manzanas.json')); DM = json.load(open('plan/datos_mod.json'))
# ---------------- manzanas
feats = []
for m in MZ:
    p = np.array(m['p'])
    if len(p) < 3: continue
    anillos = [coords_local(np.r_[p, p[:1]])] + [coords_local(np.r_[np.array(h), np.array(h)[:1]]) for h in m['h'] if len(h) >= 3]
    meta = next((q for q in DM['manzanas']['meta'] if q['id'] == m['id']), None)
    feats.append({'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': anillos},
                  'properties': {'id': m['id'], 'area_m2': m['area'], 'perimetro_m': m['per'], 'lados_m': ' · '.join(f'{v:.2f}' for v in (meta['lados'] if meta else []))}})
json.dump(fc('manzanas_plano_total_2025', feats), open(f'{SAL}/manzanas_plano.geojson', 'w'), ensure_ascii=False)
print('manzanas', len(feats))
# ---------------- vías (ejes OSM en el marco del plano) con anchos actuales y propuestos
feats = []
SEC = CAL['secciones']
for s in CAL['calles']:
    c = np.array(s['c'])
    if len(c) < 2: continue
    sec = s['secc']
    feats.append({'type': 'Feature', 'geometry': {'type': 'LineString', 'coordinates': coords_local(c)},
                  'properties': {'id': s['id'], 'nombre': s['nombre'], 'nombre_plano': s['plano'], 'clase_osm': s['clase'], 'longitud_m': s['L'],
                                 'ancho_actual_m': s['ancho'], 'ancho_min_m': s['amin'], 'ancho_max_m': s['amax'],
                                 'ancho_propuesto_m': s['prop'], 'seccion': sec,
                                 'fuente_propuesta': ('Lámina 25 Sistema vial' if sec else ('Lámina 26 Vías locales' if s['prop'] else None)),
                                 'asignada_por_vecino': bool(s['secc_h'] or s['prop_h']),
                                 'ensanche_m': round(s['prop'] - s['ancho'], 2) if (s['prop'] and s['ancho']) else None}})
json.dump(fc('vias_plano', feats), open(f'{SAL}/vias_plano.geojson', 'w'), ensure_ascii=False)
print('vías', len(feats))
# ---------------- cotas de ancho de la lámina 26 (vías locales): actual (medida) y propuesto (texto)
VL = pickle.load(open('planos/vias_locales_wcs.pkl', 'rb'))
feats = []
for d in VL['Secciones Viales Nuevas']:
    if d['t'] != 'DIMENSION' or not d.get('defpoint2') or not d.get('defpoint3'): continue
    txt = (d.get('txt') or '').strip(); m = d['med'] if isinstance(d['med'], (int, float)) else None
    mm = re.search(r'(\d+)[,.](\d+)', txt)
    prop = float(mm.group(1) + '.' + mm.group(2)) if mm else (round(m, 2) if m is not None and txt in ('', '<>', '<> ') else None)
    p2, p3 = d['defpoint2'][:2], d['defpoint3'][:2]
    if not (421500 < p2[0] < 427500 and 8734000 < p2[1] < 8743000) or m is None or prop is None: continue
    lon, lat = T.transform([p2[0], p3[0]], [p2[1], p3[1]])
    feats.append({'type': 'Feature', 'geometry': {'type': 'LineString', 'coordinates': [[round(lon[0], 7), round(lat[0], 7)], [round(lon[1], 7), round(lat[1], 7)]]},
                  'properties': {'ancho_medido_en_plano_m': round(m, 2), 'ancho_propuesto_m': prop}})
json.dump(fc('cotas_ancho_vias_locales_lamina26', feats), open(f'{SAL}/cotas_vias_locales.geojson', 'w'), ensure_ascii=False)
print('cotas', len(feats))
# ---------------- secciones típicas
NOM = {'V': 'vereda', 'C': 'cuneta', 'VR': 'vía rodada', 'J': 'jardín', 'E/J': 'estacionamiento/jardín', 'SC': 'separador central', 'canal': 'canal', 'P': 'peatonal', 'B': 'berma'}
with open(f'{SAL}/secciones_viales.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['lamina', 'seccion', 'ancho_total_m', 'componentes', 'nota'])
    for k, v in SEC.items():
        w.writerow(['25 Sistema vial', k, v['total'], ' | '.join(f'{NOM.get(t, t)} {a:.2f}' for t, a in v['comp']), v.get('nota', '')])
    for k, v in CAL['locales'].items():
        w.writerow(['26 Vías locales', f'Local {float(k):.2f} m', float(k), ' | '.join(f'{NOM.get(t, t)} {a:.2f}' for t, a in v), ''])
# ---------------- perfil y anchos del Jr. Chanchamayo
CH = json.load(open('plan/chanchamayo.json')); e = np.load('plan/eje1m.npz')
M5 = np.load('plan/mde5.npz'); Z5 = M5['Z']; ZMIN = DM['zmin']; MIT = CH['plano']['total'] / 2
from scipy.ndimage import map_coordinates
zt = map_coordinates(Z5, [(e['cz'] + 4000) / 5 - 0.5, (e['cx'] + 2600) / 5 - 0.5], order=1)
lon, lat = wgs_local(e['cx'], e['cz'])
with open(f'{SAL}/perfil_jr_chanchamayo.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['estacion_m', 'utm18s_este', 'utm18s_norte', 'lat', 'lon', 'cota_calzada_msnm', 'cota_terreno_plano_msnm', 'linea_prop_este_m', 'linea_prop_oeste_m',
                'ancho_actual_m', 'afectacion_C3_este_m', 'afectacion_C3_oeste_m', 'area_aportante_m2'])
    for i in range(0, len(e['S']), 2):
        fE, fO = float(e['fE'][i]), float(e['fO'][i])
        w.writerow([round(float(e['S'][i]), 1), round(float(e['cx'][i] + 424400), 2), round(float(8738400 - e['cz'][i]), 2), round(float(lat[i]), 7), round(float(lon[i]), 7),
                    round(float(e['ys'][i] + ZMIN), 3), round(float(zt[i]), 2), fE if fE > 0 else '', fO if fO > 0 else '',
                    round(fE + fO, 2) if fE > 0 and fO > 0 else '', round(max(0, MIT - fE), 2) if fE > 0 else '', round(max(0, MIT - fO), 2) if fO > 0 else '',
                    CH['A'][i] if i < len(CH['A']) else ''])
# ---------------- MDE de 5 m (cotas del plano) en GeoTIFF
tr = rasterio.transform.from_origin(421800, 8742400, 5, 5)
with rasterio.open(f'{SAL}/mde_plano_5m.tif', 'w', driver='GTiff', height=Z5.shape[0], width=Z5.shape[1], count=1, dtype='float32', crs='EPSG:32718',
                   transform=tr, compress='deflate', predictor=3, tiled=True) as r:
    r.write(Z5.astype('float32'), 1)
    r.update_tags(fuente='Curvas CONT-MNR (5 m) y CONT-MJR (25 m) del Plano Total 2025; fuera del casco urbano: Copernicus GLO-30 + 10,2 m',
                  metodo='residuo armónico sobre tendencia suavizada')
# ---------------- curvas de nivel del plano (Shapefile, UTM 18S)
import shapefile, os
PT = pickle.load(open('planos/plano_total_wcs.pkl', 'rb'))
os.makedirs(f'{SAL}/curvas_nivel_plano', exist_ok=True)
w = shapefile.Writer(f'{SAL}/curvas_nivel_plano/curvas_nivel_plano', shapeType=shapefile.POLYLINE, encoding='utf-8')
w.field('cota', 'N', 8, 2); w.field('tipo', 'C', 12)
n = 0
for capa, tipo in (('CONT-MNR', 'menor 5 m'), ('CONT-MJR', 'mayor 25 m')):
    for d in PT[capa]:
        if 'pts' not in d or len(d['pts']) < 2: continue
        a = np.array(d['pts']); z = float(np.median(a[:, 2]))
        if not (2990 < z < 3400): continue
        w.line([[(round(float(x), 2), round(float(y), 2)) for x, y in a[:, :2]]]); w.record(z, tipo); n += 1
w.close()
open(f'{SAL}/curvas_nivel_plano/curvas_nivel_plano.prj', 'w').write('PROJCS["WGS_1984_UTM_Zone_18S",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",10000000.0],PARAMETER["Central_Meridian",-75.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]')
print('curvas', n)
