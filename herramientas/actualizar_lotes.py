#!/usr/bin/env python3
"""Aplica al modelo 3D los cambios hechos en datos/lotes_jr_chanchamayo.csv (p. ej. tras el levantamiento de campo).

Uso:  python herramientas/actualizar_lotes.py [Tarma_ciudad_3D.html] [datos/lotes_jr_chanchamayo.csv]
Solo usa la biblioteca estándar de Python. Reescribe el HTML en su lugar (guarda una copia .bak).
"""
import csv, json, sys, shutil, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, 'Tarma_ciudad_3D.html')
tabla = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RAIZ, 'datos', 'lotes_jr_chanchamayo.csv')

INI, FIN = '<script>window.DATOS_CIUDAD=', ';</script>'
texto = open(html, encoding='utf-8').read()
a = texto.index(INI) + len(INI); b = texto.index(FIN, a)
datos = json.loads(texto[a:b])
lotes = {l['id']: l for l in datos['chanchamayo']['lotes']}

BOOL = {'1': True, 'si': True, 'sí': True, 'true': True, 'x': True, '0': False, 'no': False, 'false': False, '': False}
TIPOS = {'adobe', 'ladrillo', 'tarrajeo'}; USOS = {'comercio', 'vivienda'}; TECHOS = {'teja', 'losa', 'calamina'}
cambios = 0; errores = []
with open(tabla, encoding='utf-8-sig', newline='') as f:
    for fila in csv.DictReader(f):
        try:
            l = lotes[int(fila['id'])]
        except (KeyError, ValueError):
            errores.append(f"id desconocido: {fila.get('id')}"); continue
        antes = json.dumps(l, sort_keys=True)
        if fila.get('pisos'): l['pisos'] = max(1, min(12, int(float(fila['pisos']))))
        if fila.get('altura_m'): l['alto'] = round(float(fila['altura_m']), 1)
        if fila.get('tipologia') in TIPOS: l['tipo'] = fila['tipologia']
        if fila.get('uso') in USOS: l['uso'] = fila['uso']
        if fila.get('techo') in TECHOS: l['techo'] = fila['techo']
        for col, clave in (('color_fachada', 'pared'), ('color_zocalo', 'zocalo')):
            v = (fila.get(col) or '').strip()
            if v.startswith('#') and len(v) == 7: l[clave] = v.upper()
        for col, clave in (('volado', 'volado'), ('balcon', 'balcon'), ('obra_inconclusa', 'inconcluso'), ('tanque', 'tanque'), ('primer_piso_tarrajeado', 'mixto')):
            v = (fila.get(col) or '').strip().lower()
            if v in BOOL: l[clave] = BOOL[v]
        if fila.get('numero_aprox'): l['num'] = int(float(fila['numero_aprox']))
        nombre = (fila.get('nombre_negocio') or '').strip()
        if nombre: l['nombre'] = nombre.upper()
        elif 'nombre' in l: l.pop('nombre')          # celda vacía: sin letrero con nombre
        if json.dumps(l, sort_keys=True) != antes: cambios += 1

shutil.copyfile(html, html + '.bak')
nuevo = texto[:a] + json.dumps(datos, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + texto[b:]
open(html, 'w', encoding='utf-8').write(nuevo)
print(f'{cambios} lotes actualizados en {html} (copia en {html}.bak)')
for e in errores: print('aviso:', e)
