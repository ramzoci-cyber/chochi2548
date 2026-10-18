# Exporta la tabla de lotes del Jr. Chanchamayo a CSV (editable) y GeoJSON (WGS84) para SIG
import json, csv, sys, numpy as np
from pyproj import Transformer
SAL = sys.argv[1] if len(sys.argv) > 1 else 'salida'
T = Transformer.from_crs('EPSG:32718', 'EPSG:4326', always_xy=True)
CH = json.load(open('data/chanchamayo.json'))
e = np.load('data/eje1m.npz'); S, cx, cz, nx, nz = e['S'], e['cx'], e['cz'], e['nx'], e['nz']
def P(s, o, lado):
    i = s / (S[1] - S[0]); i0 = int(np.clip(np.floor(i), 0, len(S) - 2)); a = i - i0
    x = cx[i0] * (1 - a) + cx[i0 + 1] * a; z = cz[i0] * (1 - a) + cz[i0 + 1] * a
    vx = nx[i0] * (1 - a) + nx[i0 + 1] * a; vz = nz[i0] * (1 - a) + nz[i0 + 1] * a; l = np.hypot(vx, vz)
    return x + vx / l * o * lado, z + vz / l * o * lado
def utm(x, z): return x + 424400, 8738400 - z
def wgs(x, z): return T.transform(*utm(x, z))
campos = ['id', 'lado', 'cuadra', 'numero_aprox', 'estacion_ini_m', 'estacion_fin_m', 'frente_m', 'fondo_m', 'retiro_m', 'altura_m', 'pisos',
          'tipologia', 'uso', 'techo', 'color_fachada', 'color_zocalo', 'volado', 'balcon', 'obra_inconclusa', 'tanque', 'primer_piso_tarrajeado',
          'nombre_negocio', 'fuente_nombre', 'lat_fachada', 'lon_fachada', 'utm18s_este', 'utm18s_norte', 'verificado_en_campo', 'observaciones']
filas = []; feats = []
for l in CH['lotes']:
    sm = (l['s0'] + l['s1']) / 2; fm = (l['f'][0] + l['f'][1]) / 2 + l['ret']
    xm, zm = P(sm, fm, l['lado']); lon, lat = wgs(xm, zm); E, Nn = utm(xm, zm)
    filas.append({
        'id': l['id'], 'lado': 'E' if l['lado'] > 0 else 'O', 'cuadra': l['cuadra'] or '1 (prolong.)', 'numero_aprox': l['num'] or '',
        'estacion_ini_m': round(l['s0'], 1), 'estacion_fin_m': round(l['s1'], 1), 'frente_m': round(l['s1'] - l['s0'], 1), 'fondo_m': round(max(l['D'], l['Dt']), 1),
        'retiro_m': l['ret'], 'altura_m': l['alto'], 'pisos': l['pisos'], 'tipologia': l['tipo'], 'uso': l['uso'], 'techo': l['techo'],
        'color_fachada': l['pared'], 'color_zocalo': l['zocalo'], 'volado': int(l['volado']), 'balcon': int(l['balcon']), 'obra_inconclusa': int(l['inconcluso']),
        'tanque': int(l['tanque']), 'primer_piso_tarrajeado': int(l['mixto']), 'nombre_negocio': l.get('nombre', ''),
        'fuente_nombre': 'Overture Places / web (ubicación aprox.)' if l.get('nombre') else '',
        'lat_fachada': round(lat, 7), 'lon_fachada': round(lon, 7), 'utm18s_este': round(E, 1), 'utm18s_norte': round(Nn, 1),
        'verificado_en_campo': '', 'observaciones': ''})
    D = max(l['D'], l['Dt']); f0 = l['f'][0] + l['ret']; f1 = l['f'][1] + l['ret']
    anillo = [P(l['s0'], f0, l['lado']), P(l['s1'], f1, l['lado']), P(l['s1'], f1 + D, l['lado']), P(l['s0'], f0 + D, l['lado'])]
    coords = [list(map(lambda v: round(v, 7), wgs(*p))) for p in anillo]; coords.append(coords[0])
    feats.append({'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [coords]},
                  'properties': {k: filas[-1][k] for k in ('id', 'lado', 'cuadra', 'numero_aprox', 'altura_m', 'pisos', 'tipologia', 'uso', 'techo', 'nombre_negocio')}})
with open(f'{SAL}/lotes_jr_chanchamayo.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=campos); w.writeheader(); w.writerows(filas)
json.dump({'type': 'FeatureCollection', 'name': 'lotes_jr_chanchamayo', 'features': feats}, open(f'{SAL}/lotes_jr_chanchamayo.geojson', 'w'), ensure_ascii=False)
# eje y punto crítico
eje = [list(map(lambda v: round(v, 7), wgs(a, b))) for a, b in zip(cx[::2], cz[::2])]
json.dump({'type': 'FeatureCollection', 'name': 'eje_jr_chanchamayo', 'features': [
    {'type': 'Feature', 'geometry': {'type': 'LineString', 'coordinates': eje}, 'properties': {'nombre': 'Jr. Chanchamayo (eje recentrado)', 'longitud_m': round(float(S[-1]), 1)}}]},
    open(f'{SAL}/eje_jr_chanchamayo.geojson', 'w'), ensure_ascii=False)
print(len(filas), 'lotes exportados a', SAL)
