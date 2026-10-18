# Deriva la geometría detallada del Jr. Chanchamayo (eje, líneas de fachada, cruces, lotes)
# Fuentes: OSM (vía Overture 2026-09-23.1), Google Open Buildings 2.5D Temporal 2023 (presencia y altura, 0,5 m),
#          Microsoft/Google building footprints (Overture). Coordenadas locales del modelo: x = E - 424400, z = 8738400 - N.
import json, numpy as np, shapely, pyarrow.parquet as pq
from scipy.ndimage import gaussian_filter1d, median_filter
from pyproj import Transformer
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
def tolocal(coords):
    xs, ys = T.transform(*zip(*coords))
    return [(x - 424400, 8738400 - y) for x, y in zip(xs, ys)]
arr = np.load('data/gob_temporal_2023.npy'); PRES, ALT = arr[2], arr[1]
X0, Z0, PX = -95.0, -497.5, 0.5          # ráster alineado al marco OSM (desplazamiento medido: 5,0 m E, 2,5 m S)
def m(a, x, z):
    c = np.floor((np.asarray(x) - X0) / PX).astype(int); r = np.floor((np.asarray(z) - Z0) / PX).astype(int)
    ok = (r >= 0) & (r < a.shape[0]) & (c >= 0) & (c < a.shape[1])
    out = np.zeros(np.shape(c), dtype=np.float32); out[ok] = a[r[ok], c[ok]]; return out
def edif(x, z): return (m(PRES, x, z) > 0.5) & (m(ALT, x, z) > 2.0)

b = np.load('data/calle_bruto.npz')
cx, cz = b['cx'].copy(), b['cz'].copy()
cruces = json.load(open('data/cruces_bruto.json'))

def marco(cx, cz):
    tx = np.gradient(cx); tz = np.gradient(cz); n = np.hypot(tx, tz); tx /= n; tz /= n
    return tx, tz, -tz, tx          # tangente y normal izquierda
def bordes(cx, cz, nx, nz, maxd=30.0, paso=0.25):
    o = np.arange(paso, maxd, paso)
    res = []
    for sg in (1, -1):
        X = cx[:, None] + nx[:, None] * o[None, :] * sg; Z = cz[:, None] + nz[:, None] * o[None, :] * sg
        E = edif(X, Z)
        first = np.where(E.any(1), o[np.argmax(E, 1)], np.nan)
        res.append(first)
    return res
# 1) recentrar el eje
for it in range(2):
    tx, tz, nx, nz = marco(cx, cz)
    izq, der = bordes(cx, cz, nx, nz)
    ok = np.isfinite(izq) & np.isfinite(der) & (izq + der < 13.5) & (izq + der > 5)
    s = np.arange(len(cx), dtype=float)
    for c in cruces:
        ok &= np.abs(s - c[0]) > 9
    off = np.where(ok, (izq - der) / 2, np.nan)
    good = np.isfinite(off)
    offi = np.interp(s, s[good], off[good])
    offs = np.clip(gaussian_filter1d(offi, 7), -3.5, 3.5)
    cx = cx + nx * offs; cz = cz + nz * offs
    cx = gaussian_filter1d(cx, 2, mode='nearest'); cz = gaussian_filter1d(cz, 2, mode='nearest')
    print('iter', it, 'desplazamiento medio', np.mean(np.abs(offs)).round(2), 'max', np.abs(offs).max().round(2))
# remuestrear cada 0.5 m
d = np.r_[0, np.cumsum(np.hypot(np.diff(cx), np.diff(cz)))]
S = np.arange(0, d[-1], 0.5)
cx = np.interp(S, d, cx); cz = np.interp(S, d, cz)
tx, tz, nx, nz = marco(cx, cz)
izq, der = bordes(cx, cz, nx, nz)
L = S[-1]
print('longitud eje', round(L, 1))
# estaciones de los cruces sobre el nuevo eje
eje = shapely.LineString(np.c_[cx, cz])
X = []
for c in cruces:
    st0, nm, cls, a, nxt = c
    pa = shapely.Point(a); st = eje.project(pa)
    i = int(round(st / 0.5)); i = min(i, len(S) - 1)
    v = np.array(nxt) - np.array(a); v /= np.linalg.norm(v)
    lado = 1 if v[0] * nx[i] + v[1] * nz[i] > 0 else -1
    ang = float(np.degrees(np.arccos(np.clip(abs(v[0] * tx[i] + v[1] * tz[i]), 0, 1))))
    X.append({'s': round(float(st), 1), 'nombre': nm, 'clase': cls, 'lado': lado, 'dir': [round(float(v[0]), 3), round(float(v[1]), 3)], 'ang': round(ang)})
# fusionar cruces en la misma estación
print(json.dumps(X, ensure_ascii=False)[:2000])
np.savez('data/eje_fino.npz', S=S, cx=cx, cz=cz, nx=nx, nz=nz, tx=tx, tz=tz, izq=izq, der=der)
json.dump(X, open('data/cruces.json', 'w'), ensure_ascii=False)
