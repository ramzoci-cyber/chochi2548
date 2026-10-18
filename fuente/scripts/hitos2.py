import json, numpy as np, shapely
from shapely.geometry import Polygon, LineString
HI = json.load(open('data/hitos.json')); C = json.load(open('orig/datos_clean.json'))
plaza = Polygon(C['plaza'])
jard = [p for p in HI.get('plaza_grass', []) if plaza.buffer(1).contains(Polygon(p).centroid)]
print('jardines en plaza', len(jard), [round(Polygon(p).area) for p in jard])
pista = Polygon(HI['estadio_track']).buffer(0)
carriles = []
for k in range(0, 7):
    b = pista.buffer(-1.0 - k * 1.22, join_style=1)
    if b.is_empty: break
    g = b if b.geom_type == 'Polygon' else max(b.geoms, key=lambda q: q.area)
    carriles.append([[round(x, 2), round(z, 2)] for x, z in g.exterior.simplify(0.05).coords])
interior = pista.buffer(-1.0 - 6 * 1.22 - 0.3, join_style=1)
print('pista', round(pista.area), 'carriles', len(carriles), 'interior', round(interior.area))
out = {
    'catedral': HI['catedral'], 'tribunas': HI['tribunas'], 'pitch': HI['estadio_pitch'], 'pista': [[round(x, 2), round(z, 2)] for x, z in pista.exterior.coords],
    'carriles': carriles, 'estadio': HI['estadio_stadium'], 'jardines': jard, 'senderos': HI['plaza_senderos'],
}
json.dump(out, open('data/hitos_final.json', 'w'))
print(len(json.dumps(out)) // 1024, 'KB')
