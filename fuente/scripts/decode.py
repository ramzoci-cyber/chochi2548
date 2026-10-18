import json, base64, zlib, numpy as np
C = json.load(open('orig/datos_clean.json'))
def inflar(b64, dt):
    return np.frombuffer(zlib.decompress(base64.b64decode(b64)), dtype=dt)
W, H, CEL = C['W'], C['H'], C['celda']
z = inflar(C['z'], np.uint16).astype(np.float32).reshape(H, W) / 20
E = C['edificios']
print('edificios keys', list(E.keys()), E.get('cuenta'))
nV = inflar(E['n'], np.uint16); pri = inflar(E['pri'], np.int32); dlt = inflar(E['dlt'], np.int16); at = inflar(E['at'], np.uint8)
print(len(nV), nV.sum(), len(pri), len(dlt), len(at))
arb = inflar(C['arboles'], np.int16); post = inflar(C['postes'], np.int16); flujo = inflar(C['flujo'], np.uint8)
print('arboles', len(arb)//4, 'postes', len(post)//2, 'flujo', flujo.shape, C['WF']*C['HF'])
np.save('orig/z.npy', z)
# edificios a lista
MX, MZ = W*CEL/2, H*CEL/2
blds = []; iD = 0
for b in range(E['cuenta']):
    n = int(nV[b]); x0 = pri[b*2]/10; z0 = pri[b*2+1]/10
    P = [[x0, z0]]
    for k in range(1, n):
        P.append([x0 + dlt[iD*2]/10, z0 + dlt[iD*2+1]/10]); iD += 1
    a = at[b*10:b*10+10]
    blds.append({'P': P, 'alto': a[0]/4, 'techo': int(a[1]), 'cA': a[2:5].tolist(), 'cB': a[5:8].tolist(), 'flags': int(a[8]), 'rnd': int(a[9])})
json.dump(blds, open('orig/edificios.json', 'w'))
fl = flujo.reshape(C['HF'], C['WF'])
np.save('orig/flujo.npy', fl)
# textura satelital del modelo original (para inferir el color de techos)
import io
from PIL import Image
Image.open(io.BytesIO(base64.b64decode(C['textura']))).save('orig/textura.png')
print('z range', z.min(), z.max())
# perfil del eje
def altura(x, zz):
    fi = (x + MX)/CEL - 0.5; fj = (zz + MZ)/CEL - 0.5
    i = int(fi); j = int(fj); a = fi - i; b = fj - j
    return (z[j,i]*(1-a) + z[j,i+1]*a)*(1-b) + (z[j+1,i]*(1-a) + z[j+1,i+1]*a)*b
for l in C['eje']:
    print([ (p, round(altura(*p),1)) for p in l[::2]])
print('pc', C['punto_critico'], altura(*C['punto_critico']))
print('plaza', C['plaza_c'], altura(*C['plaza_c']))
import collections
print(collections.Counter(int(v)//9 for v in flujo))
