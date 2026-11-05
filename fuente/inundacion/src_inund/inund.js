// ================================================================ SUSCEPTIBILIDAD A INUNDACIONES (tesis CMIP5 / CMIP6, Ramos Chagua y López Silva)
// Mapas de peligro y de riesgo por manzana de la tesis (cuadros C-03 y C-04, georreferenciados), 15 puntos críticos
// y simulación 2D de la inundación con la lluvia de diseño de 25 años de cada escenario.
const IN = C.inundacion, ESCS = IN.escenarios, RC = IN.recorte, TI = IN.tiempo;
const COL_CL = ['rgba(0,0,0,0)', '#A9D18E', '#FFE699', '#F4B183', '#C00000'];
const NOM_CL = ['—', 'Bajo', 'Medio', 'Alto', 'Muy alto'];
const fmtN = (v, d = 1) => v.toLocaleString('es-PE', { minimumFractionDigits: d, maximumFractionDigits: d });
const hhmm = s => { const m = Math.round(s / 60); return `${String(Math.floor(m / 60) % 24).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`; };
// ---------------------------------------------------------------- unidades de riesgo (manzanas cerradas y celdas de 1 ha)
const UNI = { n: IN.unidades.n };
{
  const B = IN.unidades;
  const [nv, vv, tipo, vuln, rt, rs, hs, ne] = await Promise.all([inflar(B.nv, Uint16Array), inflar(B.v, Float32Array), inflar(B.tipo, Uint8Array),
    inflar(B.vuln, Uint8Array), inflar(B.riesgo, Uint8Array), inflar(B.riesgo_sim, Uint8Array), inflar(B.h_sim, Uint8Array), inflar(B.edif, Uint16Array)]);
  UNI.pol = []; let o = 0;
  for (let k = 0; k < UNI.n; k++) { UNI.pol.push(vv.subarray(o * 2, (o + nv[k]) * 2)); o += nv[k]; }
  Object.assign(UNI, { tipo, vuln, rt, rs, hs, ne, area: B.area });
  UNI.caja = UNI.pol.map(P => { let a = Infinity, b = Infinity, c = -Infinity, d = -Infinity; for (let j = 0; j < P.length; j += 2) { a = Math.min(a, P[j]); c = Math.max(c, P[j]); b = Math.min(b, P[j + 1]); d = Math.max(d, P[j + 1]); } return [a, b, c, d]; });
}
const NE = ESCS.length;
const riesgoT = (u, e) => UNI.rt[u * NE + e], riesgoS = (u, e) => UNI.rs[u * NE + e], hSimU = (u, e) => UNI.hs[u * NE + e] * 0.02;
const IDX_U = new Map(), CEL_U = 60;
UNI.caja.forEach((b, k) => { for (let a = Math.floor(b[0] / CEL_U); a <= Math.floor(b[2] / CEL_U); a++) for (let c = Math.floor(b[1] / CEL_U); c <= Math.floor(b[3] / CEL_U); c++) { const key = a * 100000 + c; if (!IDX_U.has(key)) IDX_U.set(key, []); IDX_U.get(key).push(k); } });
function dentroPol(P, x, z) {
  let d = false;
  for (let i = 0, j = P.length / 2 - 1; i < P.length / 2; j = i++) {
    const xi = P[i * 2], zi = P[i * 2 + 1], xj = P[j * 2], zj = P[j * 2 + 1];
    if ((zi > z) !== (zj > z) && x < (xj - xi) * (z - zi) / (zj - zi) + xi) d = !d;
  }
  return d;
}
function unidadEn(x, z) { for (const k of IDX_U.get(Math.floor(x / CEL_U) * 100000 + Math.floor(z / CEL_U)) || []) if (dentroPol(UNI.pol[k], x, z)) return k; return -1; }
// ---------------------------------------------------------------- escenarios: datos comprimidos (se inflan al elegirlos)
const N_REC = RC.w * RC.h;
const cache = new Map();
async function datosEscenario(e) {
  if (cache.has(e)) return cache.get(e);
  const B = ESCS[e].b64;
  const [hmax, vmax, tmax, pel, snaps] = await Promise.all([inflar(B.hmax, Uint8Array), inflar(B.vmax, Uint8Array), inflar(B.tmax, Uint8Array), inflar(B.peligro, Uint8Array), inflar(B.snaps, Uint8Array)]);
  const d = { hmax, vmax, tmax, pel, snaps }; cache.set(e, d); return d;
}
function celdaRec(x, z) {          // índice en el recorte (malla de 10 m) o -1
  const i = Math.floor((x + MX) / CEL) - RC.i0, j = Math.floor((z + MZ) / CEL) - RC.j0;
  return (i >= 0 && i < RC.w && j >= 0 && j < RC.h) ? j * RC.w + i : -1;
}
// ---------------------------------------------------------------- superficie de agua animada (instantáneas cada TI.dt_min)
const texA = new THREE.DataTexture(new Uint8Array(N_REC), RC.w, RC.h, THREE.RedFormat, THREE.UnsignedByteType);
const texB = new THREE.DataTexture(new Uint8Array(N_REC), RC.w, RC.h, THREE.RedFormat, THREE.UnsignedByteType);
for (const t of [texA, texB]) { t.magFilter = t.minFilter = THREE.LinearFilter; t.needsUpdate = true; }
const uMezcla = { value: 0 }, uAguaOn = { value: 1 };
const geoAgua = new THREE.BufferGeometry();
{
  const pos = new Float32Array(N_REC * 3), uv = new Float32Array(N_REC * 2);
  for (let j = 0; j < RC.h; j++) for (let i = 0; i < RC.w; i++) {
    const k = j * RC.w + i, gi = RC.i0 + i, gj = RC.j0 + j;
    pos.set([-MX + CEL / 2 + CEL * gi, elev[gj * W + gi], -MZ + CEL / 2 + CEL * gj], k * 3);
    uv.set([(i + 0.5) / RC.w, (j + 0.5) / RC.h], k * 2);
  }
  const ind = new Uint32Array((RC.w - 1) * (RC.h - 1) * 6); let q = 0;
  for (let j = 0; j < RC.h - 1; j++) for (let i = 0; i < RC.w - 1; i++) { const a = j * RC.w + i, b = a + 1, d = a + RC.w, e2 = d + 1; ind[q++] = a; ind[q++] = d; ind[q++] = b; ind[q++] = b; ind[q++] = d; ind[q++] = e2; }
  geoAgua.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geoAgua.setAttribute('aUV', new THREE.BufferAttribute(uv, 2));
  geoAgua.setIndex(new THREE.BufferAttribute(ind, 1)); geoAgua.computeVertexNormals();
}
const matInund = new THREE.MeshStandardMaterial({ color: 0x2f6f9f, roughness: 0.12, metalness: 0.0, transparent: true, depthWrite: false, envMapIntensity: 0.9 });
matInund.onBeforeCompile = sh => {
  Object.assign(sh.uniforms, { tA: { value: texA }, tB: { value: texB }, uMezcla, uTiempo, uAguaOn });
  sh.vertexShader = sh.vertexShader.replace('#include <common>', `#include <common>
    attribute vec2 aUV; uniform sampler2D tA; uniform sampler2D tB; uniform float uMezcla; varying float vH; varying vec2 vXZ;`)
    .replace('#include <begin_vertex>', `#include <begin_vertex>
    float hA = texture2D(tA, aUV).r * 5.1, hB = texture2D(tB, aUV).r * 5.1;
    vH = mix(hA, hB, uMezcla); vXZ = position.xz;
    transformed.y += vH + 0.07;`);
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
    varying float vH; varying vec2 vXZ; uniform float uTiempo; uniform float uAguaOn;`)
    .replace('#include <color_fragment>', `#include <color_fragment>
    if (vH < 0.025 || uAguaOn < 0.5) discard;
    float p = smoothstep(0.03, 1.6, vH);
    diffuseColor.rgb = mix(vec3(0.42, 0.72, 0.86), vec3(0.04, 0.2, 0.42), p);
    diffuseColor.rgb += 0.05 * sin(vXZ.x * 0.35 + vXZ.y * 0.27 - uTiempo * 2.6);
    diffuseColor.a = 0.42 + 0.48 * smoothstep(0.03, 0.8, vH);`);
};
MATS_DETALLE.push(matInund);
const agua2D = new THREE.Mesh(geoAgua, matInund); agua2D.renderOrder = 2; agua2D.frustumCulled = false; escena.add(agua2D);
// ---------------------------------------------------------------- capa sobre el terreno (lienzo de la microcuenca original, 5 m por píxel)
texMicro.colorSpace = THREE.SRGBColorSpace;
const cvRec = document.createElement('canvas'); cvRec.width = RC.w; cvRec.height = RC.h;
function pintarRaster(cls, alfa = 0.78) {
  const g = cvRec.getContext('2d'), img = g.createImageData(RC.w, RC.h), RGB = [null, [169, 209, 142], [255, 230, 153], [244, 177, 131], [192, 0, 0]];
  for (let k = 0; k < N_REC; k++) { const c = cls[k]; if (!c) continue; img.data.set([...RGB[c], 255 * alfa], k * 4); }
  g.putImageData(img, 0, 0);
  const G2 = lienzoM.getContext('2d'); G2.imageSmoothingEnabled = false;
  G2.clearRect(0, 0, lienzoM.width, lienzoM.height);
  const s = lienzoM.width / (2 * MX);
  G2.drawImage(cvRec, RC.i0 * CEL * s, RC.j0 * CEL * s, RC.w * CEL * s, RC.h * CEL * s);
}
function pintarUnidades(claseDe, alfa = 0.8) {
  const G2 = lienzoM.getContext('2d'); G2.clearRect(0, 0, lienzoM.width, lienzoM.height);
  const s = lienzoM.width / (2 * MX);
  G2.lineWidth = 0.6; G2.strokeStyle = 'rgba(40,40,40,0.55)';
  for (let k = 0; k < UNI.n; k++) {
    const P = UNI.pol[k], c = claseDe(k); if (!c) continue;
    G2.beginPath();
    for (let j = 0; j < P.length; j += 2) { const u = (P[j] + MX) * s, v = (P[j + 1] + MZ) * s; j ? G2.lineTo(u, v) : G2.moveTo(u, v); }
    G2.closePath(); G2.globalAlpha = alfa; G2.fillStyle = COL_CL[c]; G2.fill(); G2.globalAlpha = 1; G2.stroke();
  }
}
// ---------------------------------------------------------------- edificios teñidos por el riesgo de su unidad
let unidadEd = null;
{ unidadEd = await inflar(C.edificios.unidad, Int16Array); }
const aR = geoE.getAttribute('aR');
function teñirEdificios(claseDe) {
  const a = aR.array;
  for (let b = 0; b < nEd; b++) {
    const u = unidadEd[b], c = (claseDe && u >= 0) ? claseDe(u) : 0;
    a.fill(c, iniEd[b], iniEd[b + 1]);
  }
  aR.needsUpdate = true;
}
// ---------------------------------------------------------------- puntos críticos (plan de prevención del distrito, 15)
const grupoPC = new THREE.Group(); escena.add(grupoPC);
const matPC = new THREE.MeshStandardMaterial({ color: 0xd9534f, emissive: 0x6a1010, roughness: 0.5 });
const geoPoste = new THREE.CylinderGeometry(0.5, 0.5, 14, 10), geoBola = new THREE.SphereGeometry(2.2, 18, 12);
const pcMallas = [];
for (const p of IN.criticos) {
  const [x, z] = p.local, y = altura(x, z);
  const poste = new THREE.Mesh(geoPoste, matPC); poste.position.set(x, y + 7, z);
  const bola = new THREE.Mesh(geoBola, matPC); bola.position.set(x, y + 15, z);
  poste.userData.pc = bola.userData.pc = p.n; grupoPC.add(poste, bola); pcMallas.push(poste, bola);
}
function etiquetasCriticos() { for (const p of IN.criticos) agregarEtiqueta(`PC-${p.n}`, p.local[0], p.local[1], 22, true, 2600); }
// ---------------------------------------------------------------- estado de la vista
const VIS = { esc: 0, capa: 'hmax', t: TI.t0_h * 3600, jugando: false, vel: 900, datos: null, idx: -1 };
const CAPAS = {
  sim: 'Inundación simulada (tirante)',
  hmax: 'Tirante máximo simulado',
  peligro: 'Peligro hidrológico (tesis, C-03)',
  riesgo: 'Riesgo por manzana (tesis, C-04)',
  susc: 'Peligro simulado (tirante calibrado)',
  riesgo_sim: 'Riesgo simulado por manzana',
  vuln: 'Vulnerabilidad · exposición (tesis)',
  ninguna: 'Sin capa',
};
const T_FIN = (TI.t0_h * 3600) + (TI.n - 1) * TI.dt_min * 60;
function hietIntensidad(t) {           // mm/h en el instante t (s), bloques de 10 min
  const h = ESCS[VIS.esc].hiet, b = Math.floor(t / 600); return b >= 0 && b < h.length ? h[b] * 6 : 0;
}
function lluviaAcum(t) { const h = ESCS[VIS.esc].hiet; let s = 0; const b = Math.floor(t / 600); for (let k = 0; k < Math.min(b, h.length); k++) s += h[k]; if (b < h.length && b >= 0) s += h[b] * ((t % 600) / 600); return s; }
function ponerTiempo(t) {
  VIS.t = THREE.MathUtils.clamp(t, TI.t0_h * 3600, T_FIN);
  const f = (VIS.t - TI.t0_h * 3600) / (TI.dt_min * 60), k = Math.min(TI.n - 2, Math.floor(f));
  if (VIS.datos && VIS.capa === 'sim') {
    if (k !== VIS.idx) {
      VIS.idx = k;
      texA.image.data.set(VIS.datos.snaps.subarray(k * N_REC, (k + 1) * N_REC)); texA.needsUpdate = true;
      texB.image.data.set(VIS.datos.snaps.subarray((k + 1) * N_REC, (k + 2) * N_REC)); texB.needsUpdate = true;
    }
    uMezcla.value = THREE.MathUtils.clamp(f - k, 0, 1);
  }
  const i = hietIntensidad(VIS.t);
  lloviendo = VIS.jugando && i > 0.4; intensidad = Math.round(THREE.MathUtils.clamp(i, 5, 120));
  $('sT').value = String((VIS.t - TI.t0_h * 3600) / 60);
  $('vT').textContent = `${hhmm(VIS.t)} · ${fmtN(i, 1)} mm/h · ${fmtN(lluviaAcum(VIS.t), 1)} mm`;
  dibujarGrafico();
}
async function ponerEscenario(e) {
  if (+$('sEsc').value !== e) $('sEsc').value = String(e);
  VIS.esc = e; VIS.datos = await datosEscenario(e); VIS.idx = -1;
  aplicarCapa(); ponerTiempo(VIS.t); pintarStats();
}
function aplicarCapa() {
  const d = VIS.datos, e = VIS.esc, c = VIS.capa;
  if ($('sCapa').value !== c) $('sCapa').value = c;
  uAguaOn.value = (c === 'sim' || c === 'hmax') ? 1 : 0;
  if (c === 'hmax' && d) { texA.image.data.set(d.hmax); texB.image.data.set(d.hmax); texA.needsUpdate = texB.needsUpdate = true; uMezcla.value = 0; VIS.idx = -1; }
  if (c === 'peligro' && d) pintarRaster(d.pel);
  else if (c === 'susc' && d) { const U = IN.umbrales, cls = new Uint8Array(N_REC); for (let k = 0; k < N_REC; k++) { const h = d.hmax[k] * 0.02; cls[k] = h < 0.02 ? 0 : h < U[0] ? 1 : h < U[1] ? 2 : h < U[2] ? 3 : 4; } pintarRaster(cls, 0.72); }
  else if (c === 'riesgo') pintarUnidades(u => riesgoT(u, e));
  else if (c === 'riesgo_sim') pintarUnidades(u => riesgoS(u, e));
  else if (c === 'vuln') pintarUnidades(u => UNI.vuln[u]);
  else { const G2 = lienzoM.getContext('2d'); G2.clearRect(0, 0, lienzoM.width, lienzoM.height); }
  texMicro.needsUpdate = true; uMicro.value = (c === 'sim' || c === 'hmax' || c === 'ninguna') ? 0 : 1;
  // en las capas por manzana los edificios toman el color de su unidad (el suelo queda tapado por los techos);
  // el botón «Edificios por riesgo» mantiene el tinte también en las capas de agua y de peligro
  const porUnidad = c === 'riesgo' || c === 'riesgo_sim' || c === 'vuln';
  const tinte = (estado.riesgoEdif || porUnidad) ? (c === 'riesgo_sim' ? (u => riesgoS(u, e)) : c === 'vuln' ? (u => UNI.vuln[u]) : (u => riesgoT(u, e))) : null;
  teñirEdificios(tinte); uRiesgoEd.value = tinte ? 1 : 0;
  dibujarLeyenda(); pintarStats();
}
// ---------------------------------------------------------------- panel
function opciones(sel, items) { sel.innerHTML = items.map(([v, t]) => `<option value="${v}">${t}</option>`).join(''); }
opciones($('sEsc'), ESCS.map((s, k) => [k, s.nombre]));
opciones($('sCapa'), Object.entries(CAPAS));
$('sEsc').onchange = e => ponerEscenario(+e.target.value);
$('sCapa').onchange = e => { VIS.capa = e.target.value; VIS.idx = -1; aplicarCapa(); ponerTiempo(VIS.t); };
$('sT').min = '0'; $('sT').max = String((T_FIN - TI.t0_h * 3600) / 60); $('sT').step = '1';
$('sT').oninput = e => { VIS.jugando = false; pintarBoton(); ponerTiempo(TI.t0_h * 3600 + +e.target.value * 60); };
function pintarBoton() { $('bLluvia').innerHTML = VIS.jugando ? ico.pausa + 'Pausar' : ico.play + (VIS.t >= T_FIN - 1 ? 'Repetir tormenta' : 'Simular tormenta'); }
$('bLluvia').onclick = () => {
  if (!VIS.jugando && VIS.t >= T_FIN - 1) VIS.t = TI.t0_h * 3600;
  VIS.jugando = !VIS.jugando; if (VIS.jugando && VIS.capa !== 'sim') { VIS.capa = 'sim'; $('sCapa').value = 'sim'; aplicarCapa(); }
  pintarBoton();
};
function pintarStats() {
  const s = ESCS[VIS.esc], T = s.tesis, S = s.sim;
  const fila = (a, b) => `<div class="fila entre"><span>${a}</span><b>${b}</b></div>`;
  $('vStats').innerHTML = `
    <div class="sub">Lluvia de diseño (25 años, 24 h) en la Plaza: <b>${fmtN(s.P24, 1)} mm</b>${s.cambio ? ` · ${s.cambio > 0 ? '+' : ''}${fmtN(s.cambio, 1)} %` : ''}</div>
    <div class="dos">
      <div><div class="tit">Tesis</div>${fila('Ciudad en peligro alto o muy alto', fmtN(T.pct_ciudad, 1) + ' %')}${fila('Cuenca en peligro alto o muy alto', fmtN(T.pct_cuenca, 1) + ' %')}${fila('Unidades en riesgo alto o muy alto', T.unidades)}${fila('Edificaciones en riesgo alto o muy alto', T.edificaciones.toLocaleString('es-PE'))}${fila('Puntos críticos en peligro alto', T.criticos + '/15')}</div>
      <div><div class="tit">Simulación 2D</div>${fila('Área urbana con tirante > 10 cm', fmtN(S.area01, 2) + ' km²')}${fila('Área urbana con tirante > 50 cm', fmtN(S.area05, 2) + ' km²')}${fila('Unidades en riesgo simulado alto o muy alto', S.unidades)}${fila('Edificaciones con agua > 30 cm al pie', S.edif03.toLocaleString('es-PE'))}${fila('Puntos críticos en peligro simulado alto (≥ ' + fmtN(IN.umbrales[1], 2) + ' m)', S.criticos + '/15')}${fila('Caudal pico de los aportes oeste · sur', fmtN(s.qpico[0], 0) + ' · ' + fmtN(s.qpico[1], 0) + ' m³/s')}${fila('Área evaluada en peligro alto: simulación · mapa C-03', fmtN(S.pct_ama, 1) + ' % · ' + fmtN(T.pct_mapa_unidades, 1) + ' %')}${fila('Concordancia con C-04 (κ por unidad)', fmtN(S.kappa_unidades, 2))}</div>
    </div>`;
}
function dibujarLeyenda() {
  const c = VIS.capa;
  let h = '';
  if (c === 'sim' || c === 'hmax') h = `<div class="grad"></div><div class="fila entre"><span>2 cm</span><span>0,5 m</span><span>1 m</span><span>≥ 1,6 m</span></div>`;
  else if (c !== 'ninguna') {
    const nom = c === 'vuln' ? ['', 'Baja', 'Media', 'Alta', 'Muy alta'] : NOM_CL;
    h = [1, 2, 3, 4].map(k => `<span class="sw"><i style="background:${COL_CL[k]}"></i>${nom[k]}</span>`).join('');
    if (c === 'susc') h += `<div class="sub">Tirante máximo: bajo &lt; ${fmtN(IN.umbrales[0], 2)} m · medio &lt; ${fmtN(IN.umbrales[1], 2)} m · alto &lt; ${fmtN(IN.umbrales[2], 2)} m · muy alto ≥ ${fmtN(IN.umbrales[2], 2)} m</div>`;
  }
  $('leyenda').innerHTML = `<div class="tit">${CAPAS[c]}</div>${h}`;
}
const lienzoG = $('hidro'), ctxG = lienzoG.getContext('2d');
function dibujarGrafico() {
  const dpr = devicePixelRatio || 1, w = lienzoG.clientWidth, h = lienzoG.clientHeight; if (!w) return;
  if (lienzoG.width !== w * dpr) { lienzoG.width = w * dpr; lienzoG.height = h * dpr; }
  const g = ctxG; g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, h);
  const s = ESCS[VIS.esc], t0 = TI.t0_h * 3600, X = t => (t - t0) / (T_FIN - t0) * w;
  const mut = getComputedStyle(raiz).getPropertyValue('--muted').trim(), acc = getComputedStyle(raiz).getPropertyValue('--accent').trim();
  let imax = 1; for (const v of s.hiet) imax = Math.max(imax, v * 6);
  g.fillStyle = 'rgba(79,143,192,0.55)';
  s.hiet.forEach((v, b) => { const ta = b * 600, tb = ta + 600; if (tb < t0 || ta > T_FIN) return; const x0 = X(Math.max(ta, t0)), x1 = X(Math.min(tb, T_FIN)), y = v * 6 / imax * (h * 0.55); g.fillRect(x0, 0, Math.max(0.5, x1 - x0 - 0.3), y); });
  const A = s.sim.serie; let amax = 0.01; for (const v of A) amax = Math.max(amax, v);
  g.beginPath(); A.forEach((v, k) => { const x = k / (A.length - 1) * w, y = h - 3 - v / amax * (h * 0.55); k ? g.lineTo(x, y) : g.moveTo(x, y); });
  g.strokeStyle = acc; g.lineWidth = 1.6; g.stroke();
  g.strokeStyle = mut; g.setLineDash([3, 3]); g.beginPath(); g.moveTo(X(VIS.t), 0); g.lineTo(X(VIS.t), h); g.stroke(); g.setLineDash([]);
  g.fillStyle = mut; g.font = '10px Inter, sans-serif'; g.fillText(`lluvia (máx. ${fmtN(imax, 0)} mm/h)`, 4, h * 0.55 + 11);
  g.textAlign = 'right'; g.fillStyle = acc; g.fillText(`área inundada (máx. ${fmtN(amax, 2)} km²)`, w - 4, 10); g.textAlign = 'left';
}
// ---------------------------------------------------------------- fichas (clic)
const rayoI = new THREE.Raycaster(), ptrI = new THREE.Vector2();
let selU = null, abajoI = null;
function chip(c, nom = NOM_CL) { return `<span class="chipc" style="background:${COL_CL[c]}">${nom[c] || '—'}</span>`; }
function cerrarFicha() { $('ficha').classList.remove('ver'); if (selU) { escena.remove(selU); selU.geometry.dispose(); selU = null; } anillo.visible = false; }
$('fCerrar').onclick = cerrarFicha;
function marcarUnidad(k) {
  if (selU) { escena.remove(selU); selU.geometry.dispose(); }
  const P = UNI.pol[k], v = [];
  for (let j = 0; j < P.length; j += 2) { const a = j, b = (j + 2) % P.length; v.push(P[a], altura(P[a], P[a + 1]) + 1, P[a + 1], P[b], altura(P[b], P[b + 1]) + 1, P[b + 1]); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
  selU = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0xd97757, depthTest: false, transparent: true })); selU.renderOrder = 6; escena.add(selU);
}
function tablaEscenarios(fn) {
  return `<div class="esc9">${ESCS.map((s, e) => `<div title="${s.nombre}"><i style="background:${COL_CL[fn(e)[0]]}"></i><i style="background:${COL_CL[fn(e)[1]]}"></i><span>${s.corto}</span></div>`).join('')}</div>
    <div class="ficha-t">Arriba: tesis · abajo: simulación 2D, en los 9 escenarios.</div>`;
}
function fichaUnidad(k, punto) {
  const e = VIS.esc, d = VIS.datos, ic = punto ? celdaRec(punto.x, punto.z) : -1;
  $('fTitulo').textContent = `${UNI.tipo[k] ? 'Celda de 1 ha' : 'Manzana'} N° ${k + 1}`;
  $('fCuerpo').innerHTML = `
    <div class="fila entre"><span>Riesgo (tesis)</span><b>${chip(riesgoT(k, e))}</b></div>
    <div class="fila entre"><span>Vulnerabilidad (exposición)</span><b>${chip(UNI.vuln[k], ['', 'Baja', 'Media', 'Alta', 'Muy alta'])}</b></div>
    <div class="fila entre"><span>Tirante simulado (P90 en la unidad)</span><b>${fmtN(hSimU(k, e) * 100, 0)} cm</b></div>
    <div class="fila entre"><span>Riesgo simulado</span><b>${chip(riesgoS(k, e))}</b></div>
    ${ic >= 0 && d ? `<div class="fila entre"><span>En el punto: tirante máx. · velocidad</span><b>${fmtN(d.hmax[ic] * 0.02, 2)} m · ${fmtN(d.vmax[ic] * 0.05, 1)} m/s</b></div>` : ''}
    <div class="fila entre"><span>Edificaciones · área</span><b>${UNI.ne[k]} · ${fmtN(UNI.area[k], 0)} m²</b></div>
    ${tablaEscenarios(e2 => [riesgoT(k, e2), riesgoS(k, e2)])}
    <div class="ficha-t">Escenario: ${ESCS[e].nombre}. Riesgo de la tesis: cuadro C-04 (peligro × vulnerabilidad). Simulación: tirante máximo de la tormenta de 25 años y la misma matriz de riesgo.</div>`;
  $('ficha').classList.add('ver'); marcarUnidad(k);
}
function fichaCritico(n) {
  const p = IN.criticos.find(q => q.n === n), e = VIS.esc;
  $('fTitulo').textContent = `Punto crítico PC-${n}`;
  $('fCuerpo').innerHTML = `
    <div class="fila entre"><span>Riesgo de su unidad (tesis)</span><b>${p.unidad >= 0 ? chip(riesgoT(p.unidad, e)) : '—'}</b></div>
    <div class="fila entre"><span>Tirante máximo simulado</span><b>${fmtN(p.h[e], 2)} m</b></div>
    <div class="fila entre"><span>Velocidad máxima simulada</span><b>${fmtN(p.v[e], 1)} m/s</b></div>
    ${tablaEscenarios(e2 => [p.unidad >= 0 ? riesgoT(p.unidad, e2) : 0, p.h[e2] >= IN.umbrales[2] ? 4 : p.h[e2] >= IN.umbrales[1] ? 3 : p.h[e2] >= IN.umbrales[0] ? 2 : 1])}
    <div class="ficha-t">Punto crítico de inundación del Plan de prevención y reducción del riesgo de desastres del distrito de Tarma 2024-2030, tal como aparece en el cuadro C-04 de la tesis. Abajo: clase del tirante simulado en un radio de 30 m.</div>`;
  $('ficha').classList.add('ver');
  anillo.position.set(p.local[0], altura(p.local[0], p.local[1]) + 0.6, p.local[1]); anillo.visible = true;
}
function fichaPunto(punto, calle) {
  const d = VIS.datos, ic = celdaRec(punto.x, punto.z);
  $('fTitulo').textContent = calle && calle.nombre ? calle.nombre : 'Punto del terreno';
  $('fCuerpo').innerHTML = ic >= 0 && d ? `
    <div class="fila entre"><span>Tirante máximo simulado</span><b>${fmtN(d.hmax[ic] * 0.02, 2)} m</b></div>
    <div class="fila entre"><span>Velocidad máxima</span><b>${fmtN(d.vmax[ic] * 0.05, 1)} m/s</b></div>
    <div class="fila entre"><span>Hora del máximo</span><b>${d.tmax[ic] ? hhmm(TI.t0_h * 3600 + d.tmax[ic] * 300) : '—'}</b></div>
    ${calle && calle.ancho ? `<div class="fila entre"><span>Ancho de la calle (plano)</span><b>${fmtN(calle.ancho, 1)} m</b></div>` : ''}
    <div class="ficha-t">Escenario: ${ESCS[VIS.esc].nombre}. Celda de 10 m de la simulación 2D.</div>` : '<div class="ficha-t">Fuera de la zona simulada en detalle.</div>';
  $('ficha').classList.add('ver');
}
renderer.domElement.addEventListener('pointerdown', ev => { abajoI = [ev.clientX, ev.clientY]; });
renderer.domElement.addEventListener('pointerup', ev => {
  if (!abajoI || Math.hypot(ev.clientX - abajoI[0], ev.clientY - abajoI[1]) > 5) return;
  ptrI.set(ev.clientX / innerWidth * 2 - 1, -(ev.clientY / innerHeight) * 2 + 1); rayoI.setFromCamera(ptrI, camara);
  const hp = grupoPC.visible ? rayoI.intersectObjects(pcMallas, false)[0] : null;
  if (hp) { fichaCritico(hp.object.userData.pc); return; }
  const ht = rayoI.intersectObject(terreno, false)[0], hc = calleTocada(rayoI);
  const punto = hc ? hc.punto : ht ? ht.point : null;
  if (!punto) { cerrarFicha(); return; }
  const u = unidadEn(punto.x, punto.z);
  if (u >= 0 && !hc) fichaUnidad(u, punto); else fichaPunto(punto, hc ? hc.calle : null);
});
// ---------------------------------------------------------------- ciclo
function actualizarInundacion(dt) {
  if (VIS.jugando) { ponerTiempo(VIS.t + dt * VIS.vel); if (VIS.t >= T_FIN) { VIS.jugando = false; pintarBoton(); } }
  for (const l of letrerosLuz) l.emissiveIntensity = 0.55 * uNoche.value;
}
etiquetasCriticos();
await ponerEscenario(0);
pintarBoton();
