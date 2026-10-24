# Dibuja manzanas + geometría de las cotas de ancho de vía (p2-p3 y línea de cota) en una ventana
import pickle, sys, json, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
x0, x1, y0, y1, salida = *map(float, sys.argv[1:5]), sys.argv[5]
D = pickle.load(open('planos/vias_locales_wcs.pkl', 'rb'))
fig = plt.figure(figsize=(14, 14 * (y1 - y0) / (x1 - x0)), dpi=110); ax = fig.add_axes([0, 0, 1, 1])
for capa, col in [('manzana ok', 'black'), ('VIA SECUNDARIA', 'orange'), ('VIA PRINCIPAL', 'red'), ('propuestita', 'magenta')]:
    for d in D.get(capa, []):
        if 'pts' in d and len(d['pts']) > 1:
            a = np.array(d['pts'])
            if a[:, 0].max() < x0 or a[:, 0].min() > x1 or a[:, 1].max() < y0 or a[:, 1].min() > y1: continue
            ax.plot(a[:, 0], a[:, 1], color=col, lw=0.6)
for d in D['Secciones Viales Nuevas']:
    if d['t'] != 'DIMENSION': continue
    tm = d.get('text_midpoint'); p1, p2, p3 = d.get('defpoint'), d.get('defpoint2'), d.get('defpoint3')
    if not tm or not (x0 < tm[0] < x1 and y0 < tm[1] < y1): continue
    if p2 and p3:
        ax.plot([p2[0], p3[0]], [p2[1], p3[1]], color='blue', lw=1.2)
        ax.plot([p2[0]], [p2[1]], 'b.', ms=3); ax.plot([p3[0]], [p3[1]], 'g.', ms=3)
    if p1: ax.plot([p1[0]], [p1[1]], 'rx', ms=4)
    m = d.get('med'); m = f'{m:.2f}' if isinstance(m, (int, float)) else '?'
    ax.text(tm[0], tm[1], (d['txt'] or '') + '|' + m + f'|t{d.get("dimtype")}', fontsize=6, color='crimson')
for d in D.get('Calles', []):
    if d['t'] in ('TEXT', 'MTEXT') and x0 < d['p'][0] < x1 and y0 < d['p'][1] < y1:
        ax.text(d['p'][0], d['p'][1], d['txt'][:30], fontsize=6, color='blue', rotation=d.get('rot', 0) if abs(d.get('rot', 0)) < 360 else 0)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.axis('off')
plt.savefig(salida)
