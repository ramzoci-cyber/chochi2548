# Deriva eje, anchos y perfiles de altura del Jr. Chanchamayo a partir del ráster de Google (0,5 m)
import json, numpy as np
arr = np.load('data/gob_temporal_2023.npy')
pres, alt = arr[2], arr[1]
X0, Z0, PX = -95.0, -497.5, 0.5           # esquina NO del ráster (corregida al marco OSM)
def muestra(a, x, z):
    c = int((x - X0) / PX); r = int((z - Z0) / PX)
    if 0 <= r < a.shape[0] and 0 <= c < a.shape[1]: return a[r, c]
    return 0.0
segs = json.load(open('data/chanchamayo_segs.json'))
# encadenar segmentos desde la plaza (614,868) hacia el norte
pts = []
rest = [s['pts'] for s in segs]
cur = [614.08, 867.89]
pts.append(cur)
while rest:
    for i, s in enumerate(rest):
        if abs(s[0][0]-cur[0]) < 0.05 and abs(s[0][1]-cur[1]) < 0.05: seq = s; break
        if abs(s[-1][0]-cur[0]) < 0.05 and abs(s[-1][1]-cur[1]) < 0.05: seq = s[::-1]; break
    else:
        print('no encadena', cur, len(rest)); break
    rest.pop(i); pts += seq[1:]; cur = seq[-1]
pts = np.array(pts)
print('vertices', len(pts), pts[0], pts[-1])
# densificar cada 1 m
d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
L = d[-1]; s = np.arange(0, L, 1.0)
cx = np.interp(s, d, pts[:, 0]); cz = np.interp(s, d, pts[:, 1])
print('longitud', L)
def tangente(cx, cz):
    tx = np.gradient(cx); tz = np.gradient(cz); n = np.hypot(tx, tz); return tx / n, tz / n
tx, tz = tangente(cx, cz)
nx, nz = -tz, tx            # normal izquierda (respecto a avance plaza->norte)
def borde(i, signo, umbral=0.5):
    for k in range(1, 61):  # hasta 30 m
        o = k * 0.5 * signo
        x, z = cx[i] + nx[i] * o, cz[i] + nz[i] * o
        if muestra(pres, x, z) > umbral and muestra(alt, x, z) > 2.0:
            return abs(o)
    return np.nan
izq = np.array([borde(i, 1) for i in range(len(s))])
der = np.array([borde(i, -1) for i in range(len(s))])
np.savez('data/calle_bruto.npz', s=s, cx=cx, cz=cz, nx=nx, nz=nz, izq=izq, der=der)
for i in range(0, len(s), 10):
    print(int(s[i]), round(cx[i], 1), round(cz[i], 1), 'izq', izq[i], 'der', der[i], 'ancho', round(izq[i] + der[i], 1) if not np.isnan(izq[i] + der[i]) else '-')
