import pyarrow.parquet as pq, shapely, json
from pyproj import Transformer
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
def local(lon, lat):
    e, n = T.transform(lon, lat)
    return [round(e - 424400, 2), round(8738400 - n, 2)]
t = pq.read_table('data/transportation_segment.parquet').to_pylist()
out = []
for r in t:
    nm = (r['names'] or {}).get('primary') or ''
    if 'Chanchamayo' in nm:
        g = shapely.from_wkb(r['geometry'])
        pts = [local(x, y) for x, y in g.coords]
        L = sum(((pts[i+1][0]-pts[i][0])**2 + (pts[i+1][1]-pts[i][1])**2) ** 0.5 for i in range(len(pts)-1))
        print(r['id'][:12], nm, r['class'], r['subclass'], 'surf', r['road_surface'], 'width', r['width_rules'], 'flags', r['road_flags'], 'L=%.1f' % L)
        print('   ', pts[0], '->', pts[-1], len(pts), 'pts', [s['dataset'] + ':' + (s['record_id'] or '') for s in r['sources']])
        out.append({'id': r['id'], 'pts': pts, 'cls': r['class'], 'surf': r['road_surface']})
json.dump(out, open('data/chanchamayo_segs.json', 'w'))
