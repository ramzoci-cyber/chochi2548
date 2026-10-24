# Lee un DXF convertido y guarda un pickle con las entidades útiles (geometría simplificada) para análisis rápido
import sys, pickle, time, math
import ezdxf
from ezdxf import recover
ruta, salida = sys.argv[1], sys.argv[2]
t0 = time.time()
doc, auditor = recover.readfile(ruta)
print('leído en', round(time.time() - t0, 1), 's; errores', len(auditor.errors), 'arreglos', len(auditor.fixes))
msp = doc.modelspace()
print('unidades', doc.header.get('$INSUNITS'), 'versión', doc.dxfversion)
ents = []
from collections import Counter
c = Counter()
for e in msp:
    t = e.dxftype(); c[t] += 1
    try: capa = e.dxf.get('layer', '0')
    except Exception: continue
    d = {'t': t, 'capa': capa}
    try:
        if t == 'LWPOLYLINE':
            d['pts'] = [(p[0], p[1]) for p in e.get_points('xy')]
            d['bul'] = [p[4] for p in e.get_points('xyseb')] if any(p[4] for p in e.get_points('xyseb')) else None
            d['cerrada'] = e.closed; d['z'] = e.dxf.get('elevation', 0.0)
        elif t == 'POLYLINE':
            vs = [v.dxf.location for v in e.vertices]
            d['pts'] = [(v[0], v[1]) for v in vs]; d['zs'] = [v[2] for v in vs]; d['cerrada'] = e.is_closed
        elif t == 'LINE':
            s, f = e.dxf.start, e.dxf.end; d['pts'] = [(s[0], s[1]), (f[0], f[1])]; d['zs'] = [s[2], f[2]]
        elif t in ('TEXT', 'MTEXT'):
            d['txt'] = e.plain_text() if t == 'MTEXT' else e.dxf.text
            p = e.dxf.insert; d['p'] = (p[0], p[1], p[2]); d['h'] = e.dxf.get('char_height' if t == 'MTEXT' else 'height', 0)
            d['rot'] = e.dxf.get('rotation', 0)
        elif t == 'DIMENSION':
            d['med'] = e.get_measurement() if hasattr(e, 'get_measurement') else None
            d['txt'] = e.dxf.get('text', '')
            for k in ('defpoint', 'defpoint2', 'defpoint3', 'text_midpoint'):
                if e.dxf.hasattr(k): v = e.dxf.get(k); d[k] = (v[0], v[1], v[2])
        elif t == 'CIRCLE':
            p = e.dxf.center; d['p'] = (p[0], p[1], p[2]); d['r'] = e.dxf.radius
        elif t == 'ARC':
            p = e.dxf.center; d['p'] = (p[0], p[1], p[2]); d['r'] = e.dxf.radius; d['a'] = (e.dxf.start_angle, e.dxf.end_angle)
        elif t == 'SPLINE':
            d['pts'] = [(p[0], p[1]) for p in e.flattening(0.5)]
        elif t == 'HATCH':
            caminos = []
            for path in e.paths:
                try:
                    if path.type == 1 or hasattr(path, 'vertices'):
                        vs = [(v[0], v[1]) for v in path.vertices]
                    else:
                        vs = []
                        for ed in path.edges:
                            if ed.EDGE_TYPE == 'LineEdge': vs += [(ed.start[0], ed.start[1]), (ed.end[0], ed.end[1])]
                    if vs: caminos.append(vs)
                except Exception: pass
            d['caminos'] = caminos; d['patron'] = e.dxf.get('pattern_name', '')
        elif t == 'INSERT':
            p = e.dxf.insert; d['p'] = (p[0], p[1], p[2]); d['bloque'] = e.dxf.name
            d['atrib'] = {a.dxf.tag: a.dxf.text for a in e.attribs}
        else:
            continue
    except Exception as ex:
        d['error'] = str(ex)[:80]
    ents.append(d)
print(c.most_common(20))
pickle.dump(ents, open(salida, 'wb'))
print('guardadas', len(ents), 'entidades en', round(time.time() - t0, 1), 's')
