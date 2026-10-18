# Lotes del Jr. Chanchamayo derivados del ráster de alturas de Google (0,5 m) + huellas MS/Google como pistas de linderos
import json, numpy as np, shapely, pyarrow.parquet as pq
from scipy.ndimage import median_filter
from pyproj import Transformer
from PIL import Image
T = Transformer.from_crs('EPSG:4326', 'EPSG:32718', always_xy=True)
arr = np.load('data/gob_temporal_2023.npy'); PRES, ALT = arr[2], arr[1]
X0, Z0, PX = -95.0, -497.5, 0.5
def m(a, x, z):
    c = np.floor((np.asarray(x) - X0) / PX).astype(int); r = np.floor((np.asarray(z) - Z0) / PX).astype(int)
    ok = (r >= 0) & (r < a.shape[0]) & (c >= 0) & (c < a.shape[1])
    out = np.zeros(np.shape(c), dtype=np.float32); out[ok] = a[r[ok], c[ok]]; return out
def edif(x, z): return (m(PRES, x, z) > 0.5) & (m(ALT, x, z) > 2.0)
TEX = np.asarray(Image.open('orig/textura.png').convert('RGB')).astype(np.float32) / 255
def colorTex(x, z):
    u = int((x + 2600) / 5200 * TEX.shape[1]); v = int((z + 4000) / 8000 * TEX.shape[0])
    return TEX[max(0, v - 1):v + 2, max(0, u - 1):u + 2].reshape(-1, 3).mean(0)
e = np.load('data/eje_fino.npz')
S, cx, cz, nx, nz = e['S'], e['cx'], e['cz'], e['nx'], e['nz']
N = len(S); L = float(S[-1])
cruces = json.load(open('data/cruces.json'))
def P(i, o, lado): return np.array([cx[i] + nx[i] * o * lado, cz[i] + nz[i] * o * lado])
def idx(s): return int(np.clip(round(s / 0.5), 0, N - 1))
def tolocal(coords):
    xs, ys = T.transform(*zip(*coords))
    return [(x - 424400, 8738400 - y) for x, y in zip(xs, ys)]
huellas = []
for r in pq.read_table('data/buildings_building.parquet').to_pylist():
    g = shapely.from_wkb(r['geometry'])
    for p in (g.geoms if g.geom_type == 'MultiPolygon' else [g]):
        q = shapely.Polygon(tolocal(list(p.exterior.coords)))
        c = q.centroid
        if 500 < c.x < 1100 and 150 < c.y < 950: huellas.append(q)
bordes_h = shapely.union_all([h.boundary for h in huellas])
MAXRET = 9.0
lotes = []; cercos = []; tramos = []
FLINE = {1: np.full(N, np.nan), -1: np.full(N, np.nan)}
for lado in (1, -1):
    o = np.arange(0.25, 32, 0.25)
    X = cx[:, None] + nx[:, None] * o[None, :] * lado; Z = cz[:, None] + nz[:, None] * o[None, :] * lado
    E = edif(X, Z)
    bl = np.where(E.any(1), o[np.argmax(E, 1)], np.nan)
    huecos = []
    for c in cruces:
        if c['lado'] != lado: continue
        sc = c['s']; ang = max(35, c['ang'])
        semi = 4.6 / np.sin(np.radians(ang)) + 1.8
        huecos.append([max(0.0, sc - semi), min(L, sc + semi), c['nombre']])
    huecos.sort()
    caras = []; ini = 0.0
    for a, b, nm in huecos:
        if a - ini > 6: caras.append([ini, a, ini == 0.0])
        ini = max(ini, b)
    if L - ini > 6: caras.append([ini, L, False])
    for (sa, sb, _) in caras:
        ia, ib = idx(sa), idx(sb)
        ii = np.arange(ia, ib + 1); ss = S[ii]
        seg = bl[ii]
        ok = np.isfinite(seg) & (seg < 12)
        if ok.sum() >= 6:
            fl = np.full(len(ii), np.nan)
            for q in range(len(ii)):
                w = np.abs(ss - ss[q]) <= 16
                v = seg[w & ok]
                if len(v) >= 6: fl[q] = np.percentile(v, 30)
            good = np.isfinite(fl)
            fl = np.interp(ss, ss[good], fl[good]) if good.any() else np.full(len(ii), 5.0)
            from scipy.ndimage import gaussian_filter1d as _g
            fl = _g(fl, 10, mode='nearest')
        else:
            fl = np.full(len(ii), 5.0)
        fl = np.clip(fl, 2.4, 14)
        FLINE[lado][ii] = fl
        tramos.append({'lado': lado, 's0': round(float(sa), 1), 's1': round(float(sb), 1), 'f': [round(float(fl[0]), 2), round(float(fl[-1]), 2)]})
        ret = np.where(np.isfinite(seg), np.maximum(0, seg - fl), np.inf)
        ret = median_filter(np.where(np.isfinite(ret), ret, 99), 5)
        construido = ret <= MAXRET
        # alturas al frente del edificio (desde la línea de edificación real)
        prof = np.arange(0.5, 5.01, 0.5)
        base = np.where(construido, fl + np.minimum(ret, MAXRET), fl)
        Xs = cx[ii, None] + nx[ii, None] * (base[:, None] + prof[None, :]) * lado
        Zs = cz[ii, None] + nz[ii, None] * (base[:, None] + prof[None, :]) * lado
        pr = m(PRES, Xs, Zs); al = m(ALT, Xs, Zs)
        h = np.array([np.median(al[q][pr[q] > 0.5]) if (pr[q] > 0.5).sum() >= 3 else 0 for q in range(len(ii))])
        h = np.where(construido, h, 0.0); h = median_filter(h, 3)
        linea = shapely.LineString([P(i, fl[i - ia] + 2.5, lado) for i in ii])
        cand = np.zeros(len(ii)); inter = linea.intersection(bordes_h)
        for g in getattr(inter, 'geoms', [inter]):
            if g.is_empty or g.geom_type != 'Point': continue
            q = int(round(linea.project(g) / 0.5))
            if 0 <= q < len(ii): cand[max(0, q - 1):q + 2] = 1
        n = len(ii); MINW, MAXW = 9, 36
        cs = np.r_[0, np.cumsum(h)]; cs2 = np.r_[0, np.cumsum(h * h)]
        def sse(a, b):
            kq = b - a; mu = (cs[b] - cs[a]) / kq; return (cs2[b] - cs2[a]) - kq * mu * mu
        LAM = 20.0
        best = np.full(n + 1, np.inf); prev = np.zeros(n + 1, int); best[0] = 0
        for b in range(1, n + 1):
            for a in range(max(0, b - MAXW), b - MINW + 1 if b >= MINW else 0):
                if best[a] == np.inf: continue
                c = best[a] + sse(a, b) + LAM - (7.0 if (a > 0 and cand[a]) else 0.0)
                if c < best[b]: best[b] = c; prev[b] = a
        if best[n] == np.inf: prev[n] = 0
        cortes = []; b = n
        while b > 0: cortes.append(b); b = prev[b]
        cortes = [0] + cortes[::-1]
        for qa, qb in zip(cortes[:-1], cortes[1:]):
            hs = h[qa:qb]; frac = (hs > 0).mean()
            i0, i1 = ii[qa], ii[qb - 1]
            s0 = float(S[i0]); s1 = float(min(S[i1] + 0.5, sb))
            f0, f1 = float(fl[qa]), float(fl[qb - 1])
            esq0 = abs(s0 - sa) < 0.6 and sa > 0.0; esq1 = abs(s1 - sb) < 0.6 and sb < L
            if frac < 0.45:
                cercos.append({'lado': lado, 's0': round(s0, 2), 's1': round(s1, 2), 'f': [round(f0, 2), round(f1, 2)]})
                continue
            hf = float(np.median(hs[hs > 0]))
            rr = ret[qa:qb][construido[qa:qb]]; retiro = float(np.median(rr)) if len(rr) else 0.0
            retiro = 0.0 if retiro < 2.0 else round(retiro, 1)
            prof = np.arange(0.5, 40, 0.5); deps = []; perfs = []
            for q in range(qa, qb, 2):
                i = ii[q]; o0 = fl[q] + retiro
                xs = cx[i] + nx[i] * (o0 + prof) * lado; zs = cz[i] + nz[i] * (o0 + prof) * lado
                pz = m(PRES, xs, zs) > 0.5
                vac = np.convolve(~pz, np.ones(5), 'same') >= 5
                j = int(np.argmax(vac)) if vac.any() else len(prof) - 1
                deps.append(prof[j]); perfs.append(m(ALT, xs, zs)[:j])
            D = float(np.clip(np.median(deps), 5, 30))
            nt = int(D / 0.5)
            perf = np.array([np.median([x[t] for x in perfs if len(x) > t]) if any(len(x) > t for x in perfs) else hf for t in range(nt)])
            Df, hb = D, None
            if D > 11:
                hfm = np.median(perf[:12])
                for t in range(14, nt - 6):
                    if abs(np.median(perf[t:t + 6]) - hfm) > 2.2:
                        Df = t * 0.5; hb = float(np.median(perf[t:])); break
            cen = P(idx((s0 + s1) / 2), (f0 + f1) / 2 + retiro + min(Df, 8) / 2, lado)
            lotes.append({'lado': lado, 's0': round(s0, 2), 's1': round(s1, 2), 'f': [round(f0, 2), round(f1, 2)], 'ret': retiro,
                          'h': round(hf, 1), 'D': round(Df, 1), 'Dt': round(D, 1), 'hb': None if hb is None else round(hb, 1),
                          'esq': [bool(esq0), bool(esq1)], 'tex': [round(float(c), 3) for c in colorTex(*cen)]})
print('lotes', len(lotes), 'cercos', len(cercos), 'tramos', len(tramos), 'con retiro', sum(1 for l in lotes if l['ret'] > 0))
w = np.array([l['s1'] - l['s0'] for l in lotes]); hh = np.array([l['h'] for l in lotes])
print('frente medio', w.mean().round(1), 'min', w.min(), 'max', w.max(), '| altura', hh.mean().round(1), np.percentile(hh, [10, 50, 90]))
print('cercos long', sorted(round(c['s1'] - c['s0'], 1) for c in cercos))
json.dump({'lotes': lotes, 'cercos': cercos, 'tramos': tramos}, open('data/lotes.json', 'w'))
np.savez('data/fline.npz', E=FLINE[1], O=FLINE[-1])
