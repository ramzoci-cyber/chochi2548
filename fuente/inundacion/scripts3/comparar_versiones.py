# Compara versiones de la simulación por escenario: v1 (original), v2 (patios corregidos) y la actual (terreno corregido).
# Bolsones aislados (agua > 30 cm sin conexión a calle o cauce), unidades en riesgo alto, áreas, edificaciones y puntos críticos.
import json, sys, os, numpy as np
from scipy import ndimage
sys.path.insert(0, 'scripts3'); import sim2d
M = np.load('sim/malla.npz'); fb = M['fb']; fp = M['fp']
rio_c = sim2d.cauce_continuo(M['rio'], M['Z'].astype(np.float64))
cruz = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
def aislados(h, rio, umb=0.3):
    ed = (fb > 0.5) & ~rio
    moj = (h > umb) & ~ed; lab, n = ndimage.label(moj, structure=cruz)
    sal = set(np.unique(lab[moj & ((fp > 0.3) | rio)]).tolist())
    a = [k for k in range(1, n + 1) if k not in sal]
    return len(a), int(np.isin(lab, a).sum())
V = [('v1', 'sim/v1/res_{e}_final_v1.npz', 'sim/v1/resumen_v1.json', M['rio']),
     ('v2', 'sim/v2/res_{e}_final_v2.npz', 'sim/v2/resumen_v2.json', M['rio']),
     ('v3', 'sim/res_{e}_final.npz', 'inund/resumen.json', rio_c)]
V = [v for v in V if os.path.exists(v[2])]
R = {v[0]: json.load(open(v[2]))['escenarios'] for v in V}
cols = ['unidades', 'area01', 'area05', 'edif03', 'criticos']
print('escenario                | ' + ' | '.join('%s: %s' % (c, ' -> '.join(v[0] for v in V)) for c in cols + ['bolsones>30cm']))
for e in R[V[-1][0]]:
    fila = []
    for c in cols: fila.append(' -> '.join(str(R[v[0]][e][c]) for v in V))
    b = []
    for v in V:
        f = v[1].format(e=e)
        b.append('%d' % aislados(np.load(f)['hmax'], v[3])[0] if os.path.exists(f) else '-')
    fila.append(' -> '.join(b))
    print('%-24s | ' % e + ' | '.join(fila))
