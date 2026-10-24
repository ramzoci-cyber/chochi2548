# Extrae las secciones típicas de un bloque: grupos de cotas (DIMENSION) por dibujo, textos de nombres y etiquetas
import sys, json, ezdxf, numpy as np
from ezdxf import recover
dxf, bloque, salida = sys.argv[1], sys.argv[2], sys.argv[3]
doc, aud = recover.readfile(dxf)
blk = doc.blocks.get(bloque)
dims, textos = [], []
def recorrer(ents, nivel=0):
    for e in ents:
        t = e.dxftype()
        if t == 'DIMENSION':
            try: m = e.get_measurement()
            except Exception: m = None
            if not isinstance(m, (int, float)): continue
            p1 = e.dxf.get('defpoint2'); p2 = e.dxf.get('defpoint3'); tm = e.dxf.get('text_midpoint')
            ov = e.dxf.get('text', '')
            dims.append({'m': round(m, 3), 'ov': ov, 'x1': p1[0] if p1 else None, 'x2': p2[0] if p2 else None, 'y': (p1[1] + p2[1]) / 2 if p1 and p2 else None, 'ty': tm[1] if tm else None, 'tx': tm[0] if tm else None})
        elif t in ('TEXT', 'MTEXT'):
            ins = e.dxf.insert if t == 'MTEXT' else e.ocs().to_wcs(e.dxf.insert)
            textos.append({'txt': e.plain_text() if t == 'MTEXT' else e.dxf.text, 'x': ins.x, 'y': ins.y})
        elif t == 'INSERT' and nivel < 3:
            recorrer(list(e.virtual_entities()), nivel + 1)
recorrer(list(blk))
json.dump({'dims': dims, 'textos': textos}, open(salida, 'w'), ensure_ascii=False)
print(len(dims), 'cotas', len(textos), 'textos')
