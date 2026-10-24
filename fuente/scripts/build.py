# Ensambla Tarma_ciudad_3D.html: plantilla original + módulos del Jr. Chanchamayo + datos embebidos
import json, sys, re, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(f'{BASE}/orig/sin_datos.html', encoding='utf-8').read()

def reemplazar(src, viejo, nuevo, n=1):
    if src.count(viejo) != n:
        raise SystemExit(f'patrón encontrado {src.count(viejo)} veces (esperado {n}):\n{viejo[:160]}')
    return src.replace(viejo, nuevo)

# ---------------- título y CSS
tpl = reemplazar(tpl, '<title>Tarma 3D</title>', '<title>Tarma 3D · Jr. Chanchamayo</title>')
tpl = reemplazar(tpl, '#panel { position: fixed; top: 16px; right: 16px; width: 256px;', '#panel { position: fixed; top: 16px; right: 16px; width: 286px; max-height: calc(100vh - 32px); overflow-y: auto;')
tpl = reemplazar(tpl, '  #hidro { width: 100%; height: 40px; display: block; margin-top: 6px; }',
'''  #hidro { width: 100%; height: 40px; display: block; margin-top: 6px; }
  #perfilQ { width: 100%; height: 46px; display: block; margin-top: 6px; }
  .q .sub { color: var(--muted); font-size: 11px; margin-top: 8px; }
  .rec { margin-top: 10px; display: none; }
  .rec.ver { display: block; }
  .pista { height: 6px; border-radius: 6px; background: var(--track); margin-top: 8px; cursor: pointer; overflow: hidden; }
  .pista div { height: 100%; width: 0; background: var(--accent); border-radius: 6px; }
  #vTramo { color: var(--muted); font-size: 11px; margin-top: 6px; min-height: 14px; }
  .btn.sec { flex: 1; gap: 6px; display: inline-flex; align-items: center; justify-content: center; white-space: nowrap; }
  #ficha { position: fixed; left: 16px; bottom: 16px; width: 300px; padding: 14px; border-radius: 16px; background: var(--panel);
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border: 1px solid var(--line); box-shadow: var(--shadow); z-index: 6;
    display: none; font-size: 12px; }
  #ficha.ver { display: block; }
  #ficha h3 { margin: 0 24px 8px 0; font-size: 14px; font-weight: 600; }
  #ficha .fila { color: var(--muted); padding: 3px 0; }
  #ficha .fila b { color: var(--text); font-weight: 500; text-align: right; }
  #ficha .ficha-t { color: var(--muted); font-size: 11px; margin-top: 8px; line-height: 1.4; }
  #fCerrar { position: absolute; top: 10px; right: 10px; height: 26px; min-width: 26px; padding: 0; }''')
tpl = reemplazar(tpl, '@media (max-width: 520px) { #panel { left: 16px; right: 16px; width: auto; top: auto; bottom: 16px; } #abrir { top: auto; bottom: 16px; } }',
'@media (max-width: 520px) { #panel { left: 16px; right: 16px; width: auto; top: auto; bottom: 16px; max-height: 56vh; } #abrir { top: auto; bottom: 16px; } #ficha { left: 16px; right: 16px; width: auto; bottom: auto; top: 16px; } }')

# ---------------- panel
tpl = reemplazar(tpl, '''  <div class="seg" id="vistas">
    <button data-v="general" class="on">General</button>
    <button data-v="plaza">Plaza</button>
    <button data-v="chanchamayo">Jr. Chanchamayo</button>
  </div>''', '''  <div class="seg" id="vistas">
    <button data-v="general" class="on">General</button>
    <button data-v="plaza">Plaza</button>
    <button data-v="chanchamayo">Chanchamayo</button>
    <button data-v="estadio">Estadio</button>
  </div>
  <div class="fila" style="margin-top:10px">
    <button class="btn sec" id="bRecorrido"></button>
  </div>
  <div class="rec" id="bloqueR">
    <div class="pista" id="pistaR" title="Ir a un punto del recorrido"><div id="barraR"></div></div>
    <div id="vTramo"></div>
    <div class="ctl"><label>Velocidad <b id="vVel">5 m/s</b></label><input id="sVel" type="range" min="1" max="15" step="0.5" value="5"></div>
    <div class="fila" style="margin-top:8px"><button class="btn sec" id="bSalirR">Salir del recorrido</button></div>
  </div>''')
tpl = reemplazar(tpl, '''    <button class="chip" data-k="giro">Giro</button>''', '''    <button class="chip on" data-k="vehiculos">Vehículos</button>
    <button class="chip on" data-k="cables">Cables</button>
    <button class="chip" data-k="propuesta" title="Ensanches de la propuesta vial del PDU: en rojo, la franja de los lotes que quedaría dentro de la nueva sección">Propuesta PDU</button>
    <button class="chip" data-k="giro">Giro</button>''')
tpl = reemplazar(tpl, '''    <canvas id="hidro"></canvas>
  </div>''', '''    <canvas id="hidro"></canvas>
    <div class="fila entre" style="margin-top:8px"><span>Tirante y caudal en T01</span><b id="vT01" style="font-size:12px">—</b></div>
    <canvas id="perfilQ"></canvas>
    <div class="sub">Lámina en el Jr. Chanchamayo: Q = C·i·A (C = 0,75) y Manning (n = 0,016) en la sección actual del plano (línea azul) y en la sección C3 propuesta por el PDU, de 10,50 m (línea naranja). Es ilustrativo y no está calibrado.</div>
  </div>''')
tpl = reemplazar(tpl, '<div class="fuente">© OpenStreetMap · Microsoft Building Footprints (ODbL) · Copernicus Sentinel-2 y GLO-30 · ESA WorldCover. Alturas estimadas.</div>',
'<div class="fuente">Planos: PDU de Tarma (MPT), láminas 25 (Sistema vial) y 26 (Vías locales), propuesta JLORE 2025, y Plano Total 2025 (manzanas, curvas cada 5 m y secciones). © OpenStreetMap (vía Overture Maps) · Microsoft Building Footprints (ODbL) · Google Open Buildings 2.5D Temporal (CC BY 4.0) · Overture Places · Copernicus Sentinel-2 y GLO-30 · ESA WorldCover. Clic en una casa, una calle o una manzana para ver su ficha.</div>')
tpl = reemplazar(tpl, '<div id="etiquetas"></div>', '''<div id="etiquetas"></div>
<div id="ficha"><button class="btn" id="fCerrar" title="Cerrar" aria-label="Cerrar">✕</button><h3 id="fTitulo"></h3><div id="fCuerpo"></div></div>''')

# ---------------- JS: quitar torres y pileta originales (se remasterizan)
i0 = tpl.index('// catedral: torres'); i1 = tpl.index('// ---------------------------------------------------------------- vías (cintas sobre el terreno)')
tpl = tpl[:i0] + tpl[i1:]
# ---------------- insertar módulos antes de las etiquetas
mods = ''.join(open(f'{BASE}/src/{m}', encoding='utf-8').read() + '\n' for m in ['ch_util.js', 'ch_calle.js', 'ch_lotes.js', 'ch_hitos.js', 'ch_plano.js', 'ch_ui.js'])
tpl = reemplazar(tpl, '// ---------------------------------------------------------------- etiquetas\n', mods + '// ---------------------------------------------------------------- etiquetas\n')
tpl = reemplazar(tpl, 'const MATS_ENV = [matT, matE, matVia, matAgua].map(m => ({ material: m, base: m.envMapIntensity }));',
                 'const MATS_ENV = [matT, matE, matVia, matAgua, ...MATS_DETALLE].map(m => ({ material: m, base: m.envMapIntensity }));')
tpl = reemplazar(tpl, '''  chanchamayo: { t: [centroEje[0], 0, centroEje[1]], o: [-320, 260, 330] }
};''', '''  chanchamayo: { t: [878, 0, 690], o: [-210, 150, 190] },
  estadio: { t: [1040, 0, 245], o: [-210, 120, 150] }
};''')
tpl = reemplazar(tpl, "document.querySelectorAll('#vistas button').forEach(b => b.onclick = () => irA(b.dataset.v));",
                 "document.querySelectorAll('#vistas button').forEach(b => b.onclick = () => { if (recorrido.activo) salirRecorrido(); irA(b.dataset.v); });")
tpl = reemplazar(tpl, "const estado = { arboles: true, nombres: true, micro: true, giro: false };",
                 "const estado = { arboles: true, nombres: true, micro: true, giro: false, vehiculos: true, cables: true, propuesta: false };")
tpl = reemplazar(tpl, "stop: '<svg viewBox=\"0 0 24 24\" fill=\"currentColor\"><rect x=\"7\" y=\"7\" width=\"10\" height=\"10\" rx=\"2\"/></svg>' };",
                 "stop: '<svg viewBox=\"0 0 24 24\" fill=\"currentColor\"><rect x=\"7\" y=\"7\" width=\"10\" height=\"10\" rx=\"2\"/></svg>',\n  pausa: '<svg viewBox=\"0 0 24 24\" fill=\"currentColor\"><rect x=\"6.5\" y=\"5.5\" width=\"4\" height=\"13\" rx=\"1\"/><rect x=\"13.5\" y=\"5.5\" width=\"4\" height=\"13\" rx=\"1\"/></svg>' };")
tpl = reemplazar(tpl, "function aplicarEstado() { grupoArb.visible = estado.arboles; grupoMicro.visible = estado.micro; uMicro.value = estado.micro ? 1 : 0; controles.autoRotate = estado.giro; }",
                 "function aplicarEstado() { grupoArb.visible = estado.arboles; grupoMicro.visible = estado.micro; uMicro.value = estado.micro ? 1 : 0; controles.autoRotate = estado.giro; grupoVehic.visible = estado.vehiculos; grupoCables.visible = estado.cables; grupoProp.visible = estado.propuesta; }")
tpl = reemplazar(tpl, "function aplicarTema() { raiz.dataset.theme = tema; document.querySelector('[data-k=tema]').classList.toggle('on', tema === 'light'); dibujarHidro(); }",
                 "function aplicarTema() { raiz.dataset.theme = tema; document.querySelector('[data-k=tema]').classList.toggle('on', tema === 'light'); dibujarHidro(); dibujarPerfil(); }")
tpl = reemplazar(tpl, "  controles.update();\n  const d = camara.position.distanceTo(controles.target);",
                 "  controles.update();\n  actualizarDetalle(dt);\n  const d = camara.position.distanceTo(controles.target);")
tpl = reemplazar(tpl, "  paso(dt);\n  anillo.scale", "  paso(dt);\n  anillo.scale")
tpl = reemplazar(tpl, "irA('general', true); actualizarSol(); regenerarEnv(); aplicarTema(); aplicarEstado(); pintar();",
                 "irA('general', true); actualizarSol(); regenerarEnv(); aplicarTema(); aplicarEstado(); pintar();\n$('bRecorrido').innerHTML = ico.play + 'Recorrido virtual';\nwindow.TARMA = { camara, controles, irA, escena, renderer, recorrido, iniciarRecorrido, CH, lamina, HID, tirante, tiranteP, nivel, secc, latW, grupoPlano, grupoProp, CALLES, MANZ, abrirFichaCalle, abrirFichaManzana, abrirFichaCorredor, altura, salirRecorrido, estado, aplicarEstado, recalcularAgua, caudal, kT01, PS };")
tpl = reemplazar(tpl, "function pintar() {\n  $('bLluvia').innerHTML = lloviendo ? ico.stop + 'Detener lluvia' : ico.play + 'Llover';",
                 "function pintar() {\n  $('bLluvia').innerHTML = lloviendo ? ico.stop + 'Detener lluvia' : ico.play + 'Llover';\n  dibujarPerfil();")

# ---------------- capas de la microcuenca: se desvanecen de cerca para no tapar la calle detallada
tpl = reemplazar(tpl, "grupoMicro.add(mallaCinta(rmc, matAcento), mallaCinta(rej, matAcentoEje));",
"""for (const m of [matAcento, matAcentoEje]) {          // de cerca se desvanecen para no tapar la calle detallada
  m.transparent = true;
  m.onBeforeCompile = sh => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\\nvarying vec3 vMundo;').replace('#include <begin_vertex>', '#include <begin_vertex>\\nvMundo = (modelMatrix * vec4(position, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\\nvarying vec3 vMundo;')
      .replace('#include <dithering_fragment>', '#include <dithering_fragment>\\ngl_FragColor.a *= smoothstep(120.0, 420.0, distance(vMundo, cameraPosition));');
  };
}
grupoMicro.add(mallaCinta(rmc, matAcento), mallaCinta(rej, matAcentoEje));""")
tpl = reemplazar(tpl, "anillo.material.opacity = 0.65 + 0.35 * Math.sin(uTiempo.value * 3);",
                 "anillo.material.opacity = (0.65 + 0.35 * Math.sin(uTiempo.value * 3)) * THREE.MathUtils.smoothstep(camara.position.distanceTo(anillo.position), 35, 110);")
tpl = reemplazar(tpl, "const ok = vis && v3.z < 1 && Math.abs(v3.x) < 1.05 && Math.abs(v3.y) < 1.05 && dist < Math.max(2600, d * 2.2);",
                 "const ok = vis && v3.z < 1 && Math.abs(v3.x) < 1.05 && Math.abs(v3.y) < 1.05 && dist < (recorrido.activo ? 160 : Math.max(2600, d * 2.2));")
# ---------------- etiquetas de cuadras (solo de cerca)
tpl = reemplazar(tpl, "function agregarEtiqueta(texto, x, z, h, acento = false) {\n  const el = document.createElement('div'); el.className = 'marca' + (acento ? ' acento' : ''); el.textContent = texto; capaEt.appendChild(el);\n  etiquetas.push({ el, p: new THREE.Vector3(x, altura(x, z) + h, z), acento });\n}",
"function agregarEtiqueta(texto, x, z, h, acento = false, cerca = 0) {\n  const el = document.createElement('div'); el.className = 'marca' + (acento ? ' acento' : ''); el.textContent = texto; capaEt.appendChild(el);\n  etiquetas.push({ el, p: new THREE.Vector3(x, altura(x, z) + h, z), acento, cerca });\n}\nfor (const c of CH.cuadras) { const e = enEje((c.s0 + c.s1) / 2); agregarEtiqueta(`Cdra. ${c.n}`, e.x, e.z, 13, false, 650); }\netiquetasCalles();")
tpl = reemplazar(tpl, "&& dist < (recorrido.activo ? 160 : Math.max(2600, d * 2.2));", "&& dist < (recorrido.activo ? 160 : Math.max(2600, d * 2.2)) && (!e.cerca || dist < e.cerca);")
# ---------------- datos
D = json.load(open(f'{BASE}/plan/datos_mod.json', encoding='utf-8'))
D['chanchamayo'] = json.load(open(f'{BASE}/plan/chanchamayo.json', encoding='utf-8'))
D['hitos'] = json.load(open(f'{BASE}/plan/hitos_plano.json', encoding='utf-8'))
datos = '<script>window.DATOS_CIUDAD=' + json.dumps(D, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ';</script>\n'
tpl = reemplazar(tpl, '<script type="importmap">', datos + '<script type="importmap">')
salida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(BASE), 'Tarma_ciudad_3D.html')
open(salida, 'w', encoding='utf-8').write(tpl)
print('escrito', salida, round(len(tpl.encode()) / 1e6, 2), 'MB')
