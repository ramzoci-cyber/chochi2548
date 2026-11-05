# Compara la versión anterior (sin corrección de patios, sim/v1) con la actual: bolsones aislados y resumen por escenario
import json, sys, numpy as np
from scipy import ndimage
sys.path.insert(0, 'scripts3'); import sim2d
M = np.load('sim/malla.npz'); rio = M['rio']; fb = M['fb']; fp = M['fp']; ed = (fb > 0.5) & ~rio
Z = M['Z'].astype(np.float64); zb = Z.copy(); zb[rio] -= 1.0; zo = zb.copy(); zo[ed] += 3.0
patio = ((sim2d.relleno(zo) - zo) - (sim2d.relleno(zb) - zb) > 0.01) & ~ed & (fp <= 0.3) & ~rio
cruz = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
def aislados(h, umb):
    moj = (h > umb) & ~ed; lab, n = ndimage.label(moj, structure=cruz)
    cp = np.unique(lab[patio & moj]); cp = cp[cp > 0]; sal = set(np.unique(lab[moj & ((fp > 0.3) | rio)]).tolist())
    a = [k for k in cp if k not in sal]; return len(a), int(np.isin(lab, a).sum())
R1 = json.load(open('sim/v1/resumen_v1.json'))['escenarios']; R2 = json.load(open('inund/resumen.json'))['escenarios']
print('%-24s | unid. R>=alto v1 -> v2 | área >10 cm | área >50 cm | edif >30 cm | críticos | bolsones en patios >30 cm v1 -> v2' % 'escenario')
for e in R2:
    h1 = np.load(f'sim/v1/res_{e}_final_v1.npz')['hmax']; h2 = np.load(f'sim/res_{e}_final.npz')['hmax']
    a1 = aislados(h1, 0.3); a2 = aislados(h2, 0.3)
    print('%-24s | %3d -> %3d | %.2f -> %.2f | %.2f -> %.2f | %d -> %d | %d -> %d | %d (%d celdas) -> %d (%d celdas)' % (
        e, R1[e]['unidades'], R2[e]['unidades'], R1[e]['area01'], R2[e]['area01'], R1[e]['area05'], R2[e]['area05'], R1[e]['edif03'], R2[e]['edif03'],
        R1[e]['criticos'], R2[e]['criticos'], a1[0], a1[1], a2[0], a2[1]))
