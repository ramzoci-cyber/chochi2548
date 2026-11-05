# Indicadores para la discusión: cambio respecto al presente (unidades que suben de clase, área inundada, puntos críticos)
import json, numpy as np
U = json.load(open('tesis/riesgo_unidades.json')); ESC = U['escenarios']
US = np.load('inund/unidades_sim.npz'); rs = US['riesgo'].astype(int); h90 = US['h90']
rt = np.array([[u['riesgo'][e] for e in ESC] for u in U['unidades']])
D = json.load(open('inund/datos_mod.json'))['inundacion']
E = {e['id']: e for e in D['escenarios']}
p = E['presente']['sim']
for k, e in enumerate(ESC):
    s = E[e]['sim']
    sube_t = int((rt[:, k] > rt[:, 0]).sum()); sube_s = int((rs[:, k] > rs[:, 0]).sum())
    nuevos_s = int(((rs[:, k] >= 3) & (rs[:, 0] < 3)).sum()); nuevos_t = int(((rt[:, k] >= 3) & (rt[:, 0] < 3)).sum())
    print('%-24s P24 %5.1f | área>10cm %.2f (%+.0f %%) | >50cm %.2f (%+.0f %%) | edif>30cm %d (%+.0f %%) | unidades suben: tesis %d sim %d | nuevas en alto: tesis %d sim %d | h90 medio en unidades mojadas %.2f m | PCs %d' % (
        e, E[e]['P24'], s['area01'], 100 * (s['area01'] / p['area01'] - 1), s['area05'], 100 * (s['area05'] / p['area05'] - 1), s['edif03'], 100 * (s['edif03'] / max(1, p['edif03']) - 1),
        sube_t, sube_s, nuevos_t, nuevos_s, h90[h90[:, k] >= 0.10, k].mean(), s['criticos']))
crit = D['criticos']
print('PC  ' + ' '.join('%6s' % E[e]['corto'] for e in ESC))
for c in crit: print('PC-%-2d' % c['n'] + ' '.join('%6.2f' % h for h in c['h']))
