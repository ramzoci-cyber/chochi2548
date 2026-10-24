# Lleva todas las capas del modelo original al marco del plano (campo de desplazamiento suave) -> plan/datos_base.json
import json, base64, zlib, io, numpy as np, sys, os
from PIL import Image
from scipy.ndimage import map_coordinates
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marco import local_a_plano, plano_a_local_orig
C = json.load(open('orig/datos_clean.json'))
W, H, CEL = C['W'], C['H'], C['celda']; MX, MZ = W * CEL / 2, H * CEL / 2
def inflar(b64, dt): return np.frombuffer(zlib.decompress(base64.b64decode(b64)), dtype=dt)
def desinflar(a): return base64.b64encode(zlib.compress(np.ascontiguousarray(a).tobytes(), 9)).decode()
def mover_lista(pts):
    a = np.asarray(pts, dtype=float).reshape(-1, 2); x, z = local_a_plano(a[:, 0], a[:, 1])
    return [[round(float(u), 2), round(float(v), 2)] for u, v in zip(x, z)]
# ---- edificios
E = C['edificios']
nV = inflar(E['n'], np.uint16); pri = inflar(E['pri'], np.int32).reshape(-1, 2); dlt = inflar(E['dlt'], np.int16).reshape(-1, 2); at = inflar(E['at'], np.uint8)
blds = []; iD = 0
for b in range(E['cuenta']):
    n = int(nV[b]); x0 = pri[b, 0] / 10; z0 = pri[b, 1] / 10
    P = [[x0, z0]] + [[x0 + dlt[iD + k, 0] / 10, z0 + dlt[iD + k, 1] / 10] for k in range(n - 1)]; iD += n - 1
    blds.append({'P': mover_lista(P), 'at': at[b * 10:b * 10 + 10].tolist()})
json.dump(blds, open('plan/edificios_plano.json', 'w'))
# ---- vías, agua, árboles, postes, puntos y polígonos
C['vias'] = [dict(v, c=mover_lista(v['c'])) for v in C['vias']]
C['agua'] = [dict(g, c=mover_lista(g['c'])) for g in C['agua']]
arb = inflar(C['arboles'], np.int16).reshape(-1, 4).astype(float)
x, z = local_a_plano(arb[:, 0] / 4, arb[:, 1] / 4); arb[:, 0] = np.round(x * 4); arb[:, 1] = np.round(z * 4)
C['arboles'] = desinflar(arb.astype(np.int16).ravel())
pos = inflar(C['postes'], np.int16).reshape(-1, 2).astype(float)
x, z = local_a_plano(pos[:, 0] / 4, pos[:, 1] / 4); pos[:, 0] = np.round(x * 4); pos[:, 1] = np.round(z * 4)
C['postes'] = desinflar(pos.astype(np.int16).ravel())
C['plaza'] = mover_lista(C['plaza']); C['plaza_c'] = mover_lista([C['plaza_c']])[0]; C['torres'] = mover_lista(C['torres'])
C['punto_critico'] = mover_lista([C['punto_critico']])[0]
C['microcuenca'] = [mover_lista(p) for p in C['microcuenca']]
C['eje'] = [mover_lista(l) for l in C['eje']]
C['etiquetas'] = [[t] + mover_lista([[x, z]])[0] + [h] for t, x, z, h in C['etiquetas']]
# ---- texturas (suelo y luces nocturnas): remuestreo con el campo inverso
def deformar(img):
    a = np.asarray(img).astype(np.float32); Ht, Wt = a.shape[:2]
    u = np.arange(Wt) + 0.5; v = np.arange(Ht) + 0.5
    xs = -MX + u / Wt * 2 * MX; zs = -MZ + v / Ht * 2 * MZ
    XX, ZZ = np.meshgrid(xs, zs)
    xo, zo = plano_a_local_orig(XX.ravel(), ZZ.ravel())
    cu = (xo + MX) / (2 * MX) * Wt - 0.5; rv = (zo + MZ) / (2 * MZ) * Ht - 0.5
    out = np.stack([map_coordinates(a[..., k], [rv, cu], order=1, mode='nearest').reshape(Ht, Wt) for k in range(a.shape[2])], -1)
    return Image.fromarray(np.clip(np.round(out), 0, 255).astype(np.uint8))
tex = deformar(Image.open(io.BytesIO(base64.b64decode(C['textura']))).convert('RGB'))
tex.save('plan/textura_plano.png')
buf = io.BytesIO(); tex.save(buf, 'WEBP', quality=82, method=6); C['textura'] = base64.b64encode(buf.getvalue()).decode()
luz = deformar(Image.open(io.BytesIO(base64.b64decode(C['luz']))).convert('RGB'))
buf = io.BytesIO(); luz.save(buf, 'WEBP', quality=80, method=6); C['luz'] = base64.b64encode(buf.getvalue()).decode()
C['marco'] = 'plano'
json.dump(C, open('plan/datos_base.json', 'w'), ensure_ascii=False)
print('edificios', len(blds), 'vías', len(C['vias']), 'árboles', len(arb), 'postes', len(pos), 'textura KB', len(C['textura']) * 3 // 4 // 1024, 'luz KB', len(C['luz']) * 3 // 4 // 1024)
print('plaza_c', C['plaza_c'], 'punto crítico', C['punto_critico'])
