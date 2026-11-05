# Extrae las unidades de riesgo (polígonos rellenos) de los 10 paneles del cuadro C-04 de la tesis
import pdfplumber, collections, numpy as np, json, sys
pdf = pdfplumber.open(sys.argv[1]); p = pdf.pages[0]
CLASES = {(1.0, 0.901960784, 0.6): 2, (0.662745098, 0.819607843, 0.556862745): 1, (0.956862745, 0.694117647, 0.51372549): 3, (0.752941176, 0.0, 0.0): 4}
paneles = [(round(i['x0'], 2), round(i['top'], 2), round(i['x1'], 2), round(i['bottom'], 2)) for i in p.images if i['srcsize'] == (680, 977)]
H = float(p.height)
obj = []; otros = collections.Counter()
for c in p.curves + p.rects:
    col = c.get('non_stroking_color')
    if not c.get('fill') or not isinstance(col, (tuple, list)) or len(col) != 3: continue
    k = CLASES.get(tuple(round(v, 9) for v in col))
    if c.get('object_type') == 'curve':
        pts = [(float(x), float(y)) for x, y in c['pts']]          # pdfplumber: y medido desde arriba ('top')
    else:
        pts = [(c['x0'], c['top']), (c['x1'], c['top']), (c['x1'], c['bottom']), (c['x0'], c['bottom'])]
    a = np.array(pts); cx, cy = a.mean(0)
    pan = [i for i, b in enumerate(paneles) if b[0] - 1 <= cx <= b[2] + 1 and b[1] - 1 <= cy <= b[3] + 1]
    if k is None:
        if pan: otros[(tuple(round(v, 3) for v in col), pan[0] if pan else -1)] += 1
        continue
    obj.append({'cls': k, 'pts': pts, 'pan': pan[0] if pan else -1, 'tipo': c.get('object_type'), 'w': float(np.ptp(a[:, 0])), 'h': float(np.ptp(a[:, 1]))})
cnt = collections.Counter((o['pan'], o['cls']) for o in obj)
for i in range(len(paneles)): print('panel', i, paneles[i], {k: cnt[(i, k)] for k in (1, 2, 3, 4)}, 'total', sum(cnt[(i, k)] for k in (1, 2, 3, 4)))
print('sin panel', sum(1 for o in obj if o['pan'] < 0))
W = np.array([o['w'] for o in obj if o['pan'] == 0]); Hh = np.array([o['h'] for o in obj if o['pan'] == 0])
print('tamaños w', np.percentile(W, [5, 25, 50, 75, 95]).round(3), 'h', np.percentile(Hh, [5, 25, 50, 75, 95]).round(3))
print(collections.Counter((round(o['w'], 2), round(o['h'], 2)) for o in obj if o['pan'] == 0).most_common(8))
print(collections.Counter(o['tipo'] for o in obj))
print('otros colores rellenos dentro de paneles:', otros.most_common(12))
json.dump({'paneles': paneles, 'obj': obj}, open(sys.argv[2], 'w'))
