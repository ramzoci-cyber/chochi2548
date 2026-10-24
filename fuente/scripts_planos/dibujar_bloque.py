import sys, ezdxf, matplotlib
from ezdxf import recover, path as zpath
matplotlib.use('Agg'); import matplotlib.pyplot as plt
dxf, bloque, salida = sys.argv[1], sys.argv[2], sys.argv[3]
recorte = [float(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 else None
doc, aud = recover.readfile(dxf)
blk = doc.blocks.get(bloque)
fig = plt.figure(figsize=(30, 20), dpi=100); ax = fig.add_axes([0, 0, 1, 1])
def dibujar(ents, nivel=0):
    for e in ents:
        t = e.dxftype()
        try:
            if t in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE', 'SPLINE', 'ELLIPSE'):
                p = zpath.make_path(e); v = list(p.flattening(0.05))
                if len(v) > 1: ax.plot([q.x for q in v], [q.y for q in v], color='black' if t != 'ELLIPSE' else 'green', lw=0.5)
            elif t in ('TEXT', 'MTEXT', 'ATTRIB'):
                ins = e.dxf.insert if t == 'MTEXT' else e.ocs().to_wcs(e.dxf.insert)
                txt = e.plain_text() if t == 'MTEXT' else e.dxf.text
                ax.text(ins.x, ins.y, txt, fontsize=7, color='blue', rotation=e.dxf.get('rotation', 0) if t != 'MTEXT' else 0)
            elif t == 'DIMENSION':
                for v in e.virtual_entities():
                    if v.dxftype() in ('TEXT', 'MTEXT'):
                        ins = v.dxf.insert if v.dxftype() == 'MTEXT' else v.ocs().to_wcs(v.dxf.insert)
                        txt = v.plain_text() if v.dxftype() == 'MTEXT' else v.dxf.text
                        ax.text(ins.x, ins.y, txt, fontsize=7, color='red')
                    elif v.dxftype() in ('LINE',):
                        ax.plot([v.dxf.start.x, v.dxf.end.x], [v.dxf.start.y, v.dxf.end.y], color='red', lw=0.3)
            elif t == 'INSERT' and nivel < 3:
                dibujar(list(e.virtual_entities()), nivel + 1)
            elif t == 'HATCH':
                for p in zpath.from_hatch(e):
                    v = list(p.flattening(0.05)); ax.fill([q.x for q in v], [q.y for q in v], color='#dddddd', lw=0)
        except Exception as ex:
            pass
dibujar(list(blk))
ax.set_aspect('equal'); ax.autoscale()
if recorte: ax.set_xlim(recorte[0], recorte[1]); ax.set_ylim(recorte[2], recorte[3])
fig.savefig(salida, facecolor='white')
print('ok', ax.get_xlim(), ax.get_ylim())
