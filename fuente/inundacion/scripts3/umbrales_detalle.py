# Estabilidad de los umbrales para una corrida: top de combinaciones y techo con el peligro de la propia tesis
import json, sys, itertools, numpy as np
from collections import Counter
U = json.load(open('tesis/riesgo_unidades.json')); P = np.load('tesis/peligro_malla10.npz')
Z = np.load('sim/mascaras_unidades.npz'); idx, ini = Z['idx'], Z['ini']; NU = len(U['unidades'])
MAT = [[1, 2, 2, 3], [1, 2, 2, 3], [2, 2, 3, 3], [2, 3, 3, 4]]
vul = np.array([u['vuln'] for u in U['unidades']]); rt = np.array([u['riesgo']['presente'] for u in U['unidades']]); ok = vul > 0
def kappa(a, b, k):
    m = np.zeros((k, k))
    for i in range(k):
        for j in range(k): m[i, j] = ((a == i + 1) & (b == j + 1)).sum()
    n = m.sum(); po = np.trace(m) / n; pe = (m.sum(0) * m.sum(1)).sum() / n / n
    return (po - pe) / (1 - pe), po
# techo: peligro C-03 agregado por unidad con distintos estadísticos y la mejor matriz (mayoría por celda H x V)
pel = P['presente'].ravel()
for nom, fn in [('max', lambda a: a.max()), ('p90', lambda a: int(np.ceil(np.percentile(a, 90)))), ('p75', lambda a: int(np.ceil(np.percentile(a, 75)))),
                ('mediana', lambda a: int(np.ceil(np.median(a)))), ('moda', lambda a: Counter(a.tolist()).most_common(1)[0][0])]:
    hp = np.array([fn(pel[idx[ini[k]:ini[k + 1]]][pel[idx[ini[k]:ini[k + 1]]] > 0]) if (pel[idx[ini[k]:ini[k + 1]]] > 0).any() else 1 for k in range(NU)])
    M = [[Counter(rt[(hp == h) & (vul == v)].tolist()).most_common(1)[0][0] if ((hp == h) & (vul == v)).any() else MAT[h - 1][v - 1] for v in range(1, 5)] for h in range(1, 5)]
    rs = np.array([M[h - 1][v - 1] if v > 0 else 1 for h, v in zip(hp, vul)])
    print('techo', nom, 'kappa %.3f' % kappa(rs[ok], rt[ok], 4)[0], 'matriz', M, '| con matriz fija %.3f' % kappa(np.array([MAT[h - 1][v - 1] if v > 0 else 1 for h, v in zip(hp, vul)])[ok], rt[ok], 4)[0])
R = np.load(sys.argv[1]); hm = R['hmax'].ravel()
h90 = np.array([np.percentile(hm[idx[ini[k]:ini[k + 1]]], 90) if ini[k + 1] > ini[k] else 0 for k in range(NU)])
pcs = []
for c in U['criticos']:
    i = int((c['local'][0] + 2600) // 10); j = int((c['local'][1] + 4000) // 10)
    pcs.append(float(R['hmax'][max(0, j - 3):j + 4, max(0, i - 3):i + 4].max()))
print('h en puntos críticos', [round(x, 2) for x in pcs])
L = []
for u in itertools.combinations([0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0], 3):
    hc = np.where(h90 < u[0], 1, np.where(h90 < u[1], 2, np.where(h90 < u[2], 3, 4)))
    rs = np.array([MAT[h - 1][v - 1] if v > 0 else 1 for h, v in zip(hc, vul)])
    k4 = kappa(rs[ok], rt[ok], 4)[0]; k2 = kappa((rs[ok] >= 3) + 1, (rt[ok] >= 3) + 1, 2)[0]
    L.append((k4 + 0.5 * k2, u, round(k4, 3), round(k2, 3), int((rs >= 3).sum()), int(sum(p >= u[1] for p in pcs)), np.bincount(hc, minlength=5)[1:].tolist()))
L.sort(key=lambda r: -r[0])
for r in L[:12]: print(r)
print('h90 unidades: percentiles 50/75/90/95/99', np.percentile(h90, [50, 75, 90, 95, 99]).round(2))
