# Ensambla Tarma_ciudad_3D.html (versión de susceptibilidad a inundaciones): plantilla original + módulos + datos embebidos
import json, sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(f'{BASE}/orig/sin_datos.html', encoding='utf-8').read()
def rep(viejo, nuevo, n=1):
    global tpl
    if tpl.count(viejo) != n: raise SystemExit(f'patrón encontrado {tpl.count(viejo)} veces (esperado {n}):\n{viejo[:200]}')
    tpl = tpl.replace(viejo, nuevo)
# ---------------------------------------------------------------- título y estilos
rep('<title>Tarma 3D</title>', '<title>Tarma 3D · Inundaciones</title>')
rep('#panel { position: fixed; top: 16px; right: 16px; width: 256px;', '#panel { position: fixed; top: 16px; right: 16px; width: 318px; max-height: calc(100vh - 32px); overflow-y: auto;')
rep('  #hidro { width: 100%; height: 40px; display: block; margin-top: 6px; }', '''  #hidro { width: 100%; height: 64px; display: block; margin-top: 6px; }
  .cab .tit1 { font-size: 14px; font-weight: 600; }
  .cab .sub, .sub { color: var(--muted); font-size: 11px; margin-top: 4px; line-height: 1.35; }
  .sel { width: 100%; margin-top: 4px; font: inherit; font-size: 12px; color: var(--text); background: var(--track); border: 1px solid var(--line); border-radius: 10px; padding: 6px 8px; }
  .sel option { color: #1d1c1a; }
  #leyenda { margin-top: 8px; font-size: 11px; color: var(--muted); }
  #leyenda .tit, .dos .tit { color: var(--text); font-weight: 600; font-size: 11px; margin-bottom: 4px; }
  .sw { display: inline-flex; align-items: center; gap: 4px; margin: 0 8px 2px 0; }
  .sw i { width: 12px; height: 12px; border-radius: 3px; display: inline-block; border: 1px solid var(--line); }
  .grad { height: 10px; border-radius: 5px; background: linear-gradient(90deg, #6bb7db, #2f6f9f 45%, #0a3366); margin: 4px 0 2px; }
  .dos { display: grid; grid-template-columns: 1fr; gap: 8px; margin-top: 8px; }
  .dos .fila { font-size: 11px; padding: 2px 0; }
  .dos .fila b { text-align: right; font-weight: 500; }
  .chipc { display: inline-block; padding: 1px 8px; border-radius: 999px; color: #1d1c1a; font-weight: 600; font-size: 11px; }
  .esc9 { display: grid; grid-template-columns: repeat(9, 1fr); gap: 3px; margin-top: 8px; }
  .esc9 div { display: flex; flex-direction: column; align-items: center; gap: 2px; font-size: 9px; color: var(--muted); }
  .esc9 i { width: 100%; height: 9px; border-radius: 2px; display: block; border: 1px solid var(--line); }
  #ficha { position: fixed; left: 16px; bottom: 16px; width: 320px; padding: 14px; border-radius: 16px; background: var(--panel);
    backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border: 1px solid var(--line); box-shadow: var(--shadow); z-index: 6;
    display: none; font-size: 12px; }
  #ficha.ver { display: block; }
  #ficha h3 { margin: 0 24px 8px 0; font-size: 14px; font-weight: 600; }
  #ficha .fila { color: var(--muted); padding: 3px 0; }
  #ficha .fila b { color: var(--text); font-weight: 500; text-align: right; }
  #ficha .ficha-t { color: var(--muted); font-size: 11px; margin-top: 8px; line-height: 1.4; }
  #fCerrar { position: absolute; top: 10px; right: 10px; height: 26px; min-width: 26px; padding: 0; }''')
rep('@media (max-width: 520px) { #panel { left: 16px; right: 16px; width: auto; top: auto; bottom: 16px; } #abrir { top: auto; bottom: 16px; } }',
    '@media (max-width: 520px) { #panel { left: 16px; right: 16px; width: auto; top: auto; bottom: 16px; max-height: 56vh; } #abrir { top: auto; bottom: 16px; } #ficha { left: 16px; right: 16px; width: auto; bottom: auto; top: 16px; } }')
# ---------------------------------------------------------------- panel
i0 = tpl.index('<div id="panel">'); i1 = tpl.index('<div id="etiquetas"></div>')
tpl = tpl[:i0] + '''<div id="panel">
  <div class="cab">
    <div class="tit1">Susceptibilidad a inundaciones · Tarma</div>
    <div class="sub">Lluvia de diseño de 25 años (CMIP5 y CMIP6) · peligro y riesgo de la tesis · simulación 2D</div>
  </div>
  <div class="fila" style="margin-top:10px">
    <button class="btn prim" id="bLluvia"></button>
    <button class="btn" id="bVista" title="Vista inicial" aria-label="Vista inicial">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v4h4"/></svg>
    </button>
    <button class="btn" id="bOcultar" title="Ocultar panel" aria-label="Ocultar panel">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>
    </button>
  </div>
  <div class="ctl"><label for="sEsc">Escenario</label><select id="sEsc" class="sel"></select></div>
  <div class="ctl"><label for="sCapa">Capa</label><select id="sCapa" class="sel"></select></div>
  <div class="ctl"><label>Tormenta <b id="vT"></b></label><input id="sT" type="range" min="0" max="1" step="1" value="0"></div>
  <canvas id="hidro"></canvas>
  <div id="leyenda"></div>
  <div class="seg" id="vistas" style="margin-top:10px">
    <button data-v="general" class="on">General</button>
    <button data-v="centro">Centro</button>
    <button data-v="norte">Norte</button>
    <button data-v="sur">Sur</button>
  </div>
  <div class="chips">
    <button class="chip on" data-k="criticos">Puntos críticos</button>
    <button class="chip" data-k="riesgoEdif">Edificios por riesgo</button>
    <button class="chip on" data-k="arboles">Árboles</button>
    <button class="chip on" data-k="nombres">Nombres</button>
    <button class="chip" data-k="giro">Giro</button>
    <button class="chip" data-k="tema">Tema claro</button>
  </div>
  <div class="ctl"><label>Hora del día <b id="vHora"></b></label><input id="sHora" type="range" min="5" max="23.5" step="0.05" value="16"></div>
  <div class="q ver" id="bloqueQ"><div id="vStats"></div><b id="vQ" hidden></b></div>
  <div class="fuente">Tesis: Ramos Chagua y López Silva (UCSS), cuadros C-01 a C-04 (lluvia de diseño, cambio, peligro y riesgo por manzana) y artículo CMIP5/CMIP6. Planos: PDU de Tarma (MPT) y Plano Total 2025 (JLORE). Datos: Copernicus GLO-30, ESA WorldCover 2021, © OpenStreetMap (vía Overture Maps), Microsoft Building Footprints (ODbL), Google Open Buildings 2.5D (CC BY 4.0), Sentinel-2. Clic en una manzana, una calle o un punto crítico para ver su ficha.</div>
</div>
''' + tpl[i1:]
rep('<div id="etiquetas"></div>', '''<div id="etiquetas"></div>
<div id="ficha"><button class="btn" id="fCerrar" title="Cerrar" aria-label="Cerrar">✕</button><h3 id="fTitulo"></h3><div id="fCuerpo"></div></div>''')
# ---------------------------------------------------------------- terreno: capa de colores (peligro, riesgo) sobre la textura
rep('''    float mc = texture2D(uMicroT, vSim).r * uMicro;
    diffuseColor.rgb = mix(diffuseColor.rgb, uAcento, mc * 0.1);''', '''    vec4 ov = texture2D(uMicroT, vSim);
    diffuseColor.rgb = mix(diffuseColor.rgb, ov.rgb, ov.a * uMicro);''')
# ---------------------------------------------------------------- edificios: inicio de vértices por edificio y tinte por riesgo
rep('const pos = [], nor = [], col = [], aW = [], aF = [];', 'const pos = [], nor = [], col = [], aW = [], aF = [];\nconst iniEd = new Uint32Array(E.cuenta + 1);')
rep('for (let b = 0; b < nEd; b++) {\n  const n = nV[b], x0 = pri[b * 2] / 10, z0 = pri[b * 2 + 1] / 10;', 'for (let b = 0; b < nEd; b++) {\n  iniEd[b] = pos.length / 3;\n  const n = nV[b], x0 = pri[b * 2] / 10, z0 = pri[b * 2 + 1] / 10;')
rep('const geoE = new THREE.BufferGeometry();', 'iniEd[nEd] = pos.length / 3;\nconst geoE = new THREE.BufferGeometry();')
rep("geoE.setAttribute('aF', new THREE.Float32BufferAttribute(aF, 1));", "geoE.setAttribute('aF', new THREE.Float32BufferAttribute(aF, 1));\ngeoE.setAttribute('aR', new THREE.BufferAttribute(new Float32Array(pos.length / 3), 1));\nconst uRiesgoEd = { value: 0 };")
rep('''  sh.uniforms.uNoche = uNoche;
  sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
    attribute vec4 aW; attribute float aF; varying vec4 vW; varying float vF; varying vec3 vPosM;`)
    .replace('#include <begin_vertex>', `#include <begin_vertex>
    vW = aW; vF = aF; vPosM = (modelMatrix * vec4(position, 1.0)).xyz;`);''', '''  sh.uniforms.uNoche = uNoche; sh.uniforms.uRiesgoEd = uRiesgoEd;
  sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
    attribute vec4 aW; attribute float aF; attribute float aR; varying vec4 vW; varying float vF; varying vec3 vPosM; varying float vR;`)
    .replace('#include <begin_vertex>', `#include <begin_vertex>
    vW = aW; vF = aF; vR = aR; vPosM = (modelMatrix * vec4(position, 1.0)).xyz;`);''')
rep('''    varying vec4 vW; varying float vF; varying vec3 vPosM; uniform float uNoche;''', '''    varying vec4 vW; varying float vF; varying vec3 vPosM; uniform float uNoche; varying float vR; uniform float uRiesgoEd;''')
rep('''      diffuseColor.rgb *= 0.92 + 0.12 * h21(floor(vPosM.xz * 0.9));       // textura leve del techo
    }`)''', '''      diffuseColor.rgb *= 0.92 + 0.12 * h21(floor(vPosM.xz * 0.9));       // textura leve del techo
    }
    if (uRiesgoEd > 0.5 && vR > 0.5) {                                     // tinte por la clase de riesgo de la unidad
      vec3 cR = vR < 1.5 ? vec3(0.40, 0.63, 0.27) : vR < 2.5 ? vec3(1.0, 0.79, 0.32) : vR < 3.5 ? vec3(0.91, 0.43, 0.22) : vec3(0.53, 0.0, 0.0);
      diffuseColor.rgb = mix(diffuseColor.rgb, cR, 0.72);
    }`)''')
# ---------------------------------------------------------------- módulos: utilidades, calles e hitos (antes de las etiquetas)
temprano = ''.join(open(f'{BASE}/src_inund/{m}', encoding='utf-8').read() + '\n' for m in ['base_util.js', 'calles.js', 'geom_muros.js', 'ch_hitos.js', 'hitos_final.js'])
rep('// ---------------------------------------------------------------- etiquetas\n', temprano + '// ---------------------------------------------------------------- etiquetas\n')
rep("function agregarEtiqueta(texto, x, z, h, acento = false) {\n  const el = document.createElement('div'); el.className = 'marca' + (acento ? ' acento' : ''); el.textContent = texto; capaEt.appendChild(el);\n  etiquetas.push({ el, p: new THREE.Vector3(x, altura(x, z) + h, z), acento });\n}",
    "function agregarEtiqueta(texto, x, z, h, acento = false, cerca = 0) {\n  const el = document.createElement('div'); el.className = 'marca' + (acento ? ' acento' : ''); el.textContent = texto; capaEt.appendChild(el);\n  etiquetas.push({ el, p: new THREE.Vector3(x, altura(x, z) + h, z), acento, cerca });\n}\netiquetasCalles();")
rep("agregarEtiqueta('Punto crítico T01', pcx, pcz, 9, true);", '')
rep('// ---------------------------------------------------------------- Jr. Chanchamayo y microcuenca', '// ---------------------------------------------------------------- anillo de selección de puntos críticos (sin microcuenca ni eje en esta versión)')
rep("for (const [t, x, z, h] of C.etiquetas) agregarEtiqueta(t, x, z, h, t.startsWith('Jr.'));", "for (const [t, x, z, h] of C.etiquetas) agregarEtiqueta(t, x, z, h, false, t.startsWith('Catedral') ? 1500 : 0);")
rep("const vis = estado.nombres && !(e.acento && !estado.micro);", "const vis = e.acento ? estado.criticos : estado.nombres;")
rep("const ok = vis && v3.z < 1 && Math.abs(v3.x) < 1.05 && Math.abs(v3.y) < 1.05 && dist < Math.max(2600, d * 2.2);",
    "const ok = vis && v3.z < 1 && Math.abs(v3.x) < 1.05 && Math.abs(v3.y) < 1.05 && dist < Math.max(2600, d * 2.2) && (!e.cerca || dist < e.cerca);")
# ---------------------------------------------------------------- gráfico, panel y vistas
rep('function dibujarHidro() {', 'function dibujarHidro() {\n  if (typeof dibujarGrafico === "function") { dibujarGrafico(); return; }')
rep('''const centroEje = (() => { const l = C.eje[0]; return l[Math.floor(l.length / 2)]; })();
const VISTAS = {
  general: { t: [PLAZA[0] - 80, 0, PLAZA[1] - 380], o: [620, 1750, -1650] },
  plaza: { t: [PLAZA[0], 0, PLAZA[1]], o: [150, 95, 185] },
  chanchamayo: { t: [centroEje[0], 0, centroEje[1]], o: [-320, 260, 330] }
};''', '''const VISTAS = {
  general: { t: [PLAZA[0] + 72, 0, PLAZA[1] - 645], o: [350, 2600, 2300] },
  centro: { t: [PLAZA[0] + 120, 0, PLAZA[1] - 120], o: [-420, 520, 760] },
  norte: { t: [PLAZA[0] + 722, 0, PLAZA[1] - 995], o: [-850, 950, 1100] },
  sur: { t: [PLAZA[0] - 28, 0, PLAZA[1] + 355], o: [-250, 900, 1000] }
};''')
rep("const estado = { arboles: true, nombres: true, micro: true, giro: false };", "const estado = { arboles: true, nombres: true, criticos: true, riesgoEdif: false, giro: false };")
rep("stop: '<svg viewBox=\"0 0 24 24\" fill=\"currentColor\"><rect x=\"7\" y=\"7\" width=\"10\" height=\"10\" rx=\"2\"/></svg>' };",
    "stop: '<svg viewBox=\"0 0 24 24\" fill=\"currentColor\"><rect x=\"7\" y=\"7\" width=\"10\" height=\"10\" rx=\"2\"/></svg>',\n  pausa: '<svg viewBox=\"0 0 24 24\" fill=\"currentColor\"><rect x=\"6.5\" y=\"5.5\" width=\"4\" height=\"13\" rx=\"1\"/><rect x=\"13.5\" y=\"5.5\" width=\"4\" height=\"13\" rx=\"1\"/></svg>' };")
rep('''function pintar() {
  $('bLluvia').innerHTML = lloviendo ? ico.stop + 'Detener lluvia' : ico.play + 'Llover';
  $('bloqueQ').classList.toggle('ver', lloviendo || serie[NQ - 1] > 0.01);
  $('vInt').textContent = intensidad + ' mm/h';
}''', '''function pintar() { if (typeof pintarBoton === 'function') pintarBoton(); }''')
rep("$('sInt').oninput = e => { intensidad = +e.target.value; pintar(); };", '')
rep("function aplicarEstado() { grupoArb.visible = estado.arboles; grupoMicro.visible = estado.micro; uMicro.value = estado.micro ? 1 : 0; controles.autoRotate = estado.giro; }",
    "function aplicarEstado() { grupoArb.visible = estado.arboles; controles.autoRotate = estado.giro; if (typeof aplicarCapa === 'function') { grupoPC.visible = estado.criticos; aplicarCapa(); } }")
rep("const MATS_ENV = [matT, matE, matVia, matAgua].map(m => ({ material: m, base: m.envMapIntensity }));",
    "const MATS_ENV = [matT, matE, matVia, matAgua, ...MATS_DETALLE].map(m => ({ material: m, base: m.envMapIntensity }));")
# ---------------------------------------------------------------- módulo de inundaciones (después del panel, antes del ciclo)
tarde = open(f'{BASE}/src_inund/inund.js', encoding='utf-8').read() + '\n'
rep('// ---------------------------------------------------------------- ciclo\n', tarde + '// ---------------------------------------------------------------- ciclo\n')
rep("  controles.update();\n  const d = camara.position.distanceTo(controles.target);", "  controles.update();\n  actualizarInundacion(dt);\n  const d = camara.position.distanceTo(controles.target);")
rep("irA('general', true); actualizarSol(); regenerarEnv(); aplicarTema(); aplicarEstado(); pintar();",
    "irA('general', true); actualizarSol(); regenerarEnv(); aplicarTema(); aplicarEstado(); pintar();\nanillo.visible = false;\nwindow.TARMA = { camara, controles, irA, escena, renderer, VIS, ponerEscenario, ponerTiempo, aplicarCapa, estado, aplicarEstado, IN, UNI, altura, fichaUnidad, fichaCritico, unidadEn, cerrarFicha };")
# ---------------------------------------------------------------- datos
D = json.load(open(f'{BASE}/inund/datos_mod.json', encoding='utf-8'))
datos = '<script>window.DATOS_CIUDAD=' + json.dumps(D, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ';</script>\n'
rep('<script type="importmap">', datos + '<script type="importmap">')
salida = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(BASE, '..', '..', 'Tarma_ciudad_3D.html'))   # fuente/inundacion -> raíz del repositorio
open(salida, 'w', encoding='utf-8').write(tpl)
print('escrito', salida, round(len(tpl.encode()) / 1e6, 2), 'MB')
