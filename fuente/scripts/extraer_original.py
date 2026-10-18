# Paso 0: separa el HTML original (Tarma_ciudad_3D.html subido por el autor) en plantilla y datos
# Uso: python scripts/extraer_original.py ruta/al/Tarma_ciudad_3D_original.html
import json, sys, os
os.makedirs('orig', exist_ok=True)
lineas = open(sys.argv[1], encoding='utf-8').read().split('\n')
k = next(i for i, l in enumerate(lineas) if l.startswith('<script>window.DATOS_CIUDAD='))
s = lineas[k][len('<script>window.DATOS_CIUDAD='):]; s = s[:s.rfind('}') + 1]
json.dump(json.loads(s), open('orig/datos_clean.json', 'w'))
open('orig/sin_datos.html', 'w', encoding='utf-8').write('\n'.join(lineas[:k] + lineas[k + 1:]))
print('orig/datos_clean.json y orig/sin_datos.html listos')
