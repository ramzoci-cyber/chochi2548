# Extrae entidades de un DXF en coordenadas WCS (x, y, z) agrupadas por capa -> pickle
import sys, pickle, time, collections
import ezdxf
from ezdxf import recover, path as zpath
ruta, salida = sys.argv[1], sys.argv[2]
t0 = time.time()
doc, aud = recover.readfile(ruta)
msp = doc.modelspace()
out = collections.defaultdict(list); fallos = collections.Counter()
for e in msp:
    t = e.dxftype()
    try: capa = e.dxf.get('layer', '0')
    except Exception: continue
    try:
        if t in ('LWPOLYLINE', 'POLYLINE', 'SPLINE', 'ARC', 'CIRCLE', 'ELLIPSE', 'LINE'):
            p = zpath.make_path(e)
            pts = [(v.x, v.y, v.z) for v in p.flattening(0.15, segments=8)] if len(p) else [(v.x, v.y, v.z) for v in [p.start]]
            d = {'t': t, 'pts': pts}
            if t == 'LWPOLYLINE': d['cerrada'] = e.closed
            elif t == 'POLYLINE': d['cerrada'] = e.is_closed
            elif t == 'CIRCLE': d['cerrada'] = True; d['r'] = e.dxf.radius
            out[capa].append(d)
        elif t == 'HATCH':
            caminos = [[(v.x, v.y, v.z) for v in p.flattening(0.25, segments=8)] for p in zpath.from_hatch(e)]
            out[capa].append({'t': t, 'caminos': caminos, 'patron': e.dxf.get('pattern_name', ''), 'color': e.dxf.get('color', 256)})
        elif t == 'TEXT':
            ins = e.ocs().to_wcs(e.dxf.insert)
            out[capa].append({'t': t, 'txt': e.dxf.text, 'p': (ins.x, ins.y, ins.z), 'h': e.dxf.get('height', 0), 'rot': e.dxf.get('rotation', 0)})
        elif t == 'MTEXT':
            ins = e.dxf.insert
            out[capa].append({'t': t, 'txt': e.plain_text(), 'p': (ins.x, ins.y, ins.z), 'h': e.dxf.get('char_height', 0), 'rot': e.get_rotation() if hasattr(e, 'get_rotation') else e.dxf.get('rotation', 0)})
        elif t == 'DIMENSION':
            d = {'t': t, 'txt': e.dxf.get('text', ''), 'dimtype': e.dimtype}
            try: d['med'] = e.get_measurement()
            except Exception: d['med'] = None
            for k in ('defpoint', 'defpoint2', 'defpoint3', 'defpoint4', 'text_midpoint'):
                if e.dxf.hasattr(k): v = e.dxf.get(k); d[k] = (v[0], v[1], v[2])
            out[capa].append(d)
        elif t == 'INSERT':
            ins = e.ocs().to_wcs(e.dxf.insert)
            out[capa].append({'t': t, 'bloque': e.dxf.name, 'p': (ins.x, ins.y, ins.z), 'atrib': {a.dxf.tag: a.dxf.text for a in e.attribs}})
    except Exception as ex:
        fallos[t] += 1
pickle.dump(dict(out), open(salida, 'wb'))
print('capas', len(out), 'fallos', dict(fallos), 'tiempo', round(time.time() - t0, 1), 's')
