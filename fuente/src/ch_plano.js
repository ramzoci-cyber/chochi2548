// ================================================================ PLANOS DEL PDU DE TARMA (MPT) · propuesta vial JLORE 2025
// Calzadas y veredas con los anchos medidos entre manzanas del Plano Total 2025, fichas de vía (sección típica de las
// láminas 25 y 26) y de manzana (lados y área), y capa de propuesta con las franjas que afectaría el ensanche.
const grupoPlano = new THREE.Group(); escena.add(grupoPlano);
const grupoProp = new THREE.Group(); grupoProp.visible = false; escena.add(grupoProp);
const CALLES = [], VEREDAS = [], MANZ = [];
{
  const [nC, vC, nV, vV, nM, vM] = await Promise.all([
    inflar(C.calles.n, Uint16Array), inflar(C.calles.v, Float32Array), inflar(C.veredas.n, Uint16Array), inflar(C.veredas.v, Float32Array),
    inflar(C.manzanas.n, Uint16Array), inflar(C.manzanas.v, Float32Array)]);
  let o = 0;
  C.calles.meta.forEach((m, i) => { const n = nC[i]; m.pts = vC.subarray(o * 6, (o + n) * 6); o += n; CALLES.push(m); });
  o = 0;
  C.veredas.meta.forEach(([w, lado], i) => { const n = nV[i]; VEREDAS.push({ w, lado, pts: vV.subarray(o * 2, (o + n) * 2) }); o += n; });
  o = 0;
  C.manzanas.meta.forEach((m, i) => { const n = nM[i]; m.pts = vM.subarray(o * 2, (o + n) * 2); o += n; MANZ.push(m); });
}
const H_CALZ = 0.16, H_SARD = 0.15;
// polilínea densificada (paso máx. en m) con los atributos por vértice (k valores por vértice)
function densificar(P, k, paso) {
  const n = P.length / k, out = [];
  for (let j = 0; j < n - 1; j++) {
    const a = j * k, b = a + k, L = Math.hypot(P[b] - P[a], P[b + 1] - P[a + 1]), m = Math.max(1, Math.ceil(L / paso));
    for (let t = 0; t < m; t++) {
      const f = t / m, v = [];
      for (let q = 0; q < k; q++) v.push((P[a + q] < 0 || P[b + q] < 0) && q >= 4 ? (f < 0.5 ? P[a + q] : P[b + q]) : P[a + q] + (P[b + q] - P[a + q]) * f);
      out.push(v);
    }
  }
  const v = []; for (let q = 0; q < k; q++) v.push(P[(n - 1) * k + q]); out.push(v);
  return out;
}
function tangente(pts, k) {
  const a = pts[Math.max(0, k - 1)], b = pts[Math.min(pts.length - 1, k + 1)];
  let tx = b[0] - a[0], tz = b[1] - a[1]; const l = Math.hypot(tx, tz) || 1; return [tx / l, tz / l];
}
// ---------------------------------------------------------------- calzadas (ancho del plano) y eje pintado en las vías principales
const SUPP = [0x4b4d50, 0x9a9890, 0x8f7457, 0xb7ae9f].map(h => new THREE.Color(h));
const rcPl = { v: [], c: [], i: [], d: [] }, rmPl = { v: [], c: [], i: [], d: [] }, triCalle = [];
for (let ci = 0; ci < CALLES.length; ci++) {
  const m = CALLES[ci]; if (m.pts.length < 12) continue;
  const col = m.cl === 6 ? SUPP[3] : SUPP[m.sp], pts = densificar(m.pts, 6, 5);
  m.dens = pts;
  let dist = 0;
  for (let k = 0; k < pts.length; k++) {
    const p = pts[k], [tx, tz] = tangente(pts, k), nx = -tz, nz = tx;
    if (k) dist += Math.hypot(p[0] - pts[k - 1][0], p[1] - pts[k - 1][1]);
    const xl = p[0] + nx * p[2], zl = p[1] + nz * p[2], xr = p[0] - nx * p[3], zr = p[1] - nz * p[3];
    rcPl.v.push(xl, altura(xl, zl) + H_CALZ, zl, xr, altura(xr, zr) + H_CALZ, zr);
    rcPl.c.push(col.r, col.g, col.b, col.r, col.g, col.b); rcPl.d.push(dist, 0, dist, 1);
    if (k) { const i = rcPl.v.length / 3 - 4; rcPl.i.push(i, i + 2, i + 1, i + 1, i + 2, i + 3); triCalle.push(ci, ci); }
    if (m.cl <= 2 && m.sp !== 2) {                       // eje discontinuo amarillo
      const oc = (p[2] - p[3]) / 2, xc = p[0] + nx * oc, zc = p[1] + nz * oc, y = altura(xc, zc) + H_CALZ + 0.04;
      rmPl.v.push(xc + nx * 0.06, y, zc + nz * 0.06, xc - nx * 0.06, y, zc - nz * 0.06); rmPl.c.push(0.92, 0.8, 0.35, 0.92, 0.8, 0.35); rmPl.d.push(dist, 0, dist, 1);
      if (k) { const i = rmPl.v.length / 3 - 4; rmPl.i.push(i, i + 2, i + 1, i + 1, i + 2, i + 3); }
    }
  }
}
const callesPlano = mallaCinta(rcPl, matVia); callesPlano.receiveShadow = true; grupoPlano.add(callesPlano);
grupoPlano.add(mallaCinta(rmPl, matMarca));
// ---------------------------------------------------------------- veredas y sardineles a lo largo de las líneas de manzana
const GV = new Geo(), GS = new Geo();
for (const v of VEREDAS) {
  const P = v.pts, n = P.length / 2; if (n < 2) continue;
  const nor = [];                                        // normal hacia la calle en cada vértice (inglete limitado)
  for (let j = 0; j < n; j++) {
    let sx = 0, sz = 0;
    for (const [a, b] of [[j - 1, j], [j, j + 1]]) {
      if (a < 0 || b >= n) continue;
      const dx = P[b * 2] - P[a * 2], dz = P[b * 2 + 1] - P[a * 2 + 1], l = Math.hypot(dx, dz) || 1;
      sx += -dz / l; sz += dx / l;
    }
    const l = Math.hypot(sx, sz) || 1; let nx = sx / l * v.lado, nz = sz / l * v.lado;
    let esc = 1;
    if (j > 0 && j < n - 1) { const dx = P[(j + 1) * 2] - P[j * 2], dz = P[(j + 1) * 2 + 1] - P[j * 2 + 1], ll = Math.hypot(dx, dz) || 1; esc = 1 / Math.max(0.5, Math.abs((-dz / ll) * nx * v.lado + (dx / ll) * nz * v.lado)); }
    nor.push([nx * Math.min(esc, 2), nz * Math.min(esc, 2)]);
  }
  let s = 0;
  for (let j = 0; j < n - 1; j++) {
    const ax = P[j * 2], az = P[j * 2 + 1], bx = P[j * 2 + 2], bz = P[j * 2 + 3], L = Math.hypot(bx - ax, bz - az), m = Math.max(1, Math.ceil(L / 4));
    const dx = (bx - ax) / (L || 1), dz = (bz - az) / (L || 1), nC = [-dz * v.lado, dx * v.lado];
    for (let t = 0; t < m; t++) {
      const f0 = t / m, f1 = (t + 1) / m;
      const p0 = [ax + (bx - ax) * f0, az + (bz - az) * f0], p1 = [ax + (bx - ax) * f1, az + (bz - az) * f1];
      const n0 = [nor[j][0] * (1 - f0) + nor[j + 1][0] * f0, nor[j][1] * (1 - f0) + nor[j + 1][1] * f0];
      const n1 = [nor[j][0] * (1 - f1) + nor[j + 1][0] * f1, nor[j][1] * (1 - f1) + nor[j + 1][1] * f1];
      const q0 = [p0[0] + n0[0] * v.w, p0[1] + n0[1] * v.w], q1 = [p1[0] + n1[0] * v.w, p1[1] + n1[1] * v.w];
      const yq0 = altura(q0[0], q0[1]) + H_CALZ, yq1 = altura(q1[0], q1[1]) + H_CALZ;
      const yp0 = Math.max(altura(p0[0], p0[1]) + H_CALZ, yq0) + H_SARD + 0.02, yp1 = Math.max(altura(p1[0], p1[1]) + H_CALZ, yq1) + H_SARD + 0.02;
      const sa = s + L * f0, sb = s + L * f1;
      GV.quad([p0[0], yp0, p0[1]], [p1[0], yp1, p1[1]], [q1[0], yq1 + H_SARD, q1[1]], [q0[0], yq0 + H_SARD, q0[1]], ARRIBA, [1, 1, 1],
        [[sa / 2, v.w / 2], [sb / 2, v.w / 2], [sb / 2, 0], [sa / 2, 0]]);
      GS.quad([q0[0], yq0 - 0.06, q0[1]], [q1[0], yq1 - 0.06, q1[1]], [q1[0], yq1 + H_SARD, q1[1]], [q0[0], yq0 + H_SARD, q0[1]], [nC[0], 0, nC[1]], [0.86, 0.85, 0.82],
        [[sa / 2, 0], [sb / 2, 0], [sb / 2, 0.09], [sa / 2, 0.09]]);
    }
    s += L;
  }
}
grupoPlano.add(GV.malla(MAT.vereda, false, true), GS.malla(MAT.concreto, false, true));
// ---------------------------------------------------------------- índice espacial de manzanas (clic sobre el terreno)
const IDX_M = new Map(), CEL_M = 60;
MANZ.forEach((m, k) => {
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity;
  for (let j = 0; j < m.pts.length; j += 2) { x0 = Math.min(x0, m.pts[j]); x1 = Math.max(x1, m.pts[j]); z0 = Math.min(z0, m.pts[j + 1]); z1 = Math.max(z1, m.pts[j + 1]); }
  m.caja = [x0, z0, x1, z1];
  for (let a = Math.floor(x0 / CEL_M); a <= Math.floor(x1 / CEL_M); a++) for (let b = Math.floor(z0 / CEL_M); b <= Math.floor(z1 / CEL_M); b++) {
    const key = a * 100000 + b; if (!IDX_M.has(key)) IDX_M.set(key, []); IDX_M.get(key).push(k);
  }
});
function dentroPol(P, x, z) {
  let d = false;
  for (let i = 0, j = P.length / 2 - 1; i < P.length / 2; j = i++) {
    const xi = P[i * 2], zi = P[i * 2 + 1], xj = P[j * 2], zj = P[j * 2 + 1];
    if ((zi > z) !== (zj > z) && x < (xj - xi) * (z - zi) / (zj - zi) + xi) d = !d;
  }
  return d;
}
function manzanaEn(x, z) {
  for (const k of IDX_M.get(Math.floor(x / CEL_M) * 100000 + Math.floor(z / CEL_M)) || []) if (dentroPol(MANZ[k].pts, x, z)) return MANZ[k];
  return null;
}
// ---------------------------------------------------------------- propuesta del PDU: franjas afectadas por el ensanche
// se dibuja como una capa de plano (sin prueba de profundidad): la franja se ve a través de los techos, como en el CAD
const matAfect = new THREE.MeshBasicMaterial({ color: 0xe5484d, transparent: true, opacity: 0.5, depthWrite: false, depthTest: false, side: THREE.DoubleSide });
const matLinProp = new THREE.LineBasicMaterial({ color: 0xffd166, transparent: true, opacity: 0.95, depthTest: false });
const PA = { v: [], i: [] }, PLv = [];
function franja(o, a, b, c, d) {          // cuadrilátero en el suelo (x,z de 4 puntos)
  const i = o.v.length / 3;
  for (const p of [a, b, c, d]) o.v.push(p[0], altura(p[0], p[1]) + 0.45, p[1]);
  o.i.push(i, i + 1, i + 2, i, i + 2, i + 3);
}
function linea(a, b) { PLv.push(a[0], altura(a[0], a[1]) + 0.5, a[1], b[0], altura(b[0], b[1]) + 0.5, b[1]); }
let afectadoTotal = 0;
function marcarEnsanche(pts, fl, fr, cen, mitad) {       // pts: [[x,z,nx,nz]], fl/fr: caras actuales, cen: centro, mitad: medio ancho propuesto
  for (let k = 0; k < pts.length - 1; k++) {
    const A = pts[k], B = pts[k + 1];
    if (fl[k] < 0 || fl[k + 1] < 0 || fr[k] < 0 || fr[k + 1] < 0) continue;
    const L = Math.hypot(B[0] - A[0], B[1] - A[1]);
    for (const sg of [1, -1]) {
      const fa = sg > 0 ? fl[k] : fr[k], fb = sg > 0 ? fl[k + 1] : fr[k + 1];
      const na = cen[k] * sg + mitad, nb = cen[k + 1] * sg + mitad;           // nueva línea de propiedad medida hacia ese lado
      if (na <= fa + 0.05 && nb <= fb + 0.05) continue;
      const ea = Math.max(na, fa), eb = Math.max(nb, fb);
      const P = (q, o) => [q[0] + q[2] * o * sg, q[1] + q[3] * o * sg];
      franja(PA, P(A, fa), P(B, fb), P(B, eb), P(A, ea)); linea(P(A, ea), P(B, eb));
      afectadoTotal += L * ((ea - fa) + (eb - fb)) / 2;
    }
  }
}
for (const m of CALLES) {
  if (!m.prop || !m.ancho || m.prop <= m.ancho + 0.25 || !m.dens) continue;
  const pts = m.dens.map((p, k) => { const [tx, tz] = tangente(m.dens, k); return [p[0], p[1], -tz, tx]; });
  const fl = m.dens.map(p => p[4]), fr = m.dens.map(p => p[5]);
  const cen = m.dens.map(p => (p[4] >= 0 && p[5] >= 0) ? (p[4] - p[5]) / 2 : 0);
  marcarEnsanche(pts, fl, fr, cen, m.prop / 2);
}
{ // Jr. Chanchamayo: sección C3 de 10,50 m centrada en el eje
  const pts = [], fl = [], fr = [], cen = [];
  for (let s = 0; s <= CH.L; s += 2) { const e = enEje(s); pts.push([e.x, e.z, e.nx, e.nz]); const i = Math.round(s / PASO); fl.push(CH.fE[i] > 0 ? FE[i] : -1); fr.push(CH.fO[i] > 0 ? FO[i] : -1); cen.push(0); }
  marcarEnsanche(pts, fl, fr, cen, (CH.plano ? CH.plano.total : 10.5) / 2);
}
function mallaSimple(o, mat) {
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(o.v, 3)); g.setIndex(o.i);
  const m = new THREE.Mesh(g, mat); m.renderOrder = 3; return m;
}
grupoProp.add(mallaSimple(PA, matAfect));
{ const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(PLv, 3)); const l = new THREE.LineSegments(g, matLinProp); l.renderOrder = 4; grupoProp.add(l); }
console.info('Propuesta PDU: franja afectada por ensanches ≈', Math.round(afectadoTotal), 'm²');
// ---------------------------------------------------------------- nombres de calles (de cerca; se llama al crear las etiquetas)
function etiquetasCalles() {
  const usados = [];
  for (const m of CALLES) {
    if (!m.nombre || !m.dens || m.L < 45 || m.cl > 4) continue;
    const p = m.dens[Math.floor(m.dens.length / 2)];
    if (usados.some(u => u[0] === m.nombre && Math.hypot(u[1] - p[0], u[2] - p[1]) < 170)) continue;
    usados.push([m.nombre, p[0], p[1]]);
    agregarEtiqueta(m.nombre.replace('Jirón', 'Jr.').replace('Avenida', 'Av.').replace('Pasaje', 'Pje.'), p[0], p[1], 6, false, 230);
  }
}
// ---------------------------------------------------------------- selección: vía y manzana
let selPlano = null; const etqSel = [];
function limpiarSelPlano() {
  if (selPlano) { escena.remove(selPlano); selPlano.geometry.dispose(); selPlano = null; }
  for (const e of etqSel) e.el.remove(); etqSel.length = 0;
}
function lineaSel(segs) {             // segs: lista de [x,z,x,z]
  const v = [];
  for (const [ax, az, bx, bz] of segs) v.push(ax, altura(ax, az) + 0.7, az, bx, altura(bx, bz) + 0.7, bz);
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
  const l = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0xd97757, depthTest: false, transparent: true }));
  l.renderOrder = 6; return l;
}
const NOM_CLASE = { trunk: 'Troncal (carretera)', primary: 'Primaria', secondary: 'Secundaria', tertiary: 'Terciaria', residential: 'Local residencial',
  unclassified: 'Local', living_street: 'Local compartida', service: 'Servicio / acceso', track: 'Trocha', footway: 'Peatonal', path: 'Sendero',
  pedestrian: 'Peatonal', steps: 'Escalinata (gradas)', unknown: 'Sin clasificar' };
const fmt2 = (v, d = 2) => v.toLocaleString('es-PE', { minimumFractionDigits: d, maximumFractionDigits: d });
function compSeccion(m) {
  if (m.secc && C.secciones[m.secc]) return { cod: m.secc, ...C.secciones[m.secc], fuente: 'Lámina 25 · Sistema vial (propuesta)' };
  if (m.prop && C.locales[m.prop.toFixed(1)]) return { cod: null, total: m.prop, comp: C.locales[m.prop.toFixed(1)], fuente: 'Lámina 26 · Vías locales (propuesta)' };
  if (m.prop) return { cod: null, total: m.prop, comp: null, fuente: 'Lámina 26 · Vías locales (propuesta)' };
  return null;
}
const COL_COMP = { V: '#cfcac0', C: '#8a8780', VR: '#55585c', J: '#7fae6a', 'E/J': '#9fb58a', SC: '#6f9f5d', canal: '#5f97c4', P: '#d9cfb8', B: '#a39e94' };
const NOM_COMP = { V: 'Vereda', C: 'Cuneta', VR: 'Vía rodada', J: 'Jardín', 'E/J': 'Estac./jardín', SC: 'Separador', canal: 'Canal', P: 'Peatonal', B: 'Berma' };
function dibujarSeccion(cv, sec, actual) {
  const dpr = devicePixelRatio || 1, w = cv.clientWidth, h = cv.clientHeight; cv.width = w * dpr; cv.height = h * dpr;
  const g = cv.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, w, h);
  const txt = getComputedStyle(raiz).getPropertyValue('--text').trim(), mut = getComputedStyle(raiz).getPropertyValue('--muted').trim();
  const tot = Math.max(sec.total, actual || 0), esc = (w - 16) / tot, x0 = 8 + (tot - sec.total) * esc / 2, yb = h - 26;
  g.font = '10px Inter, sans-serif'; g.textAlign = 'center';
  let x = x0;
  for (const [t, a] of sec.comp || [['VR', sec.total]]) {
    const ww = a * esc, alto = (t === 'V' || t === 'SC' || t === 'P' || t === 'B') ? 9 : (t === 'J' || t === 'E/J') ? 7 : t === 'canal' ? -6 : 4;
    g.fillStyle = COL_COMP[t] || '#999'; g.fillRect(x, yb - Math.max(alto, 0), ww, Math.abs(alto) + 3);
    g.fillStyle = mut; if (ww > 16) g.fillText(t, x + ww / 2, yb + 13);
    g.fillStyle = txt; if (ww > 22) g.fillText(fmt2(a), x + ww / 2, yb - 13 - (alto > 6 ? 0 : 0));
    x += ww;
  }
  g.strokeStyle = mut; g.setLineDash([3, 3]);
  for (const xx of [x0, x]) { g.beginPath(); g.moveTo(xx, 6); g.lineTo(xx, yb + 4); g.stroke(); }
  g.setLineDash([]); g.fillStyle = txt; g.fillText(`LP — ${fmt2(sec.total)} m — LP`, (x0 + x) / 2, 12);
  if (actual) {
    const xa = 8 + (tot - actual) * esc / 2;
    g.strokeStyle = '#d9534f'; g.lineWidth = 1.5; g.beginPath(); g.moveTo(xa, h - 6); g.lineTo(xa + actual * esc, h - 6); g.stroke();
    g.fillStyle = '#d9534f'; g.textAlign = 'left'; g.fillText(`actual ${fmt2(actual, 1)} m`, Math.min(w - 70, xa + actual * esc + 4), h - 3);
  }
}
function abrirFichaCalle(m) {
  cerrarFicha(); limpiarSelPlano();
  const sec = compSeccion(m);
  $('fTitulo').textContent = m.nombre || 'Vía sin nombre';
  const otroNombre = m.plano && m.nombre && m.plano.toLowerCase().replace(/[^a-záéíóúñ0-9]/g, '') !== m.nombre.toLowerCase().replace(/jirón|avenida|pasaje|calle/g, x => ({ 'jirón': 'jr', avenida: 'av', pasaje: 'pje', calle: 'calle' })[x]).replace(/[^a-záéíóúñ0-9]/g, '');
  const dif = (m.prop && m.ancho) ? m.prop - m.ancho : null;
  $('fCuerpo').innerHTML = `
    ${otroNombre ? `<div class="fila entre"><span>Nombre en el plano</span><b>${m.plano}</b></div>` : ''}
    <div class="fila entre"><span>Tipo (OSM)</span><b>${NOM_CLASE[m.clase] || m.clase || '—'}</b></div>
    <div class="fila entre"><span>Ancho actual (plano)</span><b>${m.ancho ? `${fmt2(m.ancho)} m` : 'sin manzanas a ambos lados'}</b></div>
    ${m.ancho ? `<div class="fila entre"><span>Rango en el tramo</span><b>${fmt2(m.amin, 1)} – ${fmt2(m.amax, 1)} m</b></div>` : ''}
    <div class="fila entre"><span>Ancho propuesto (PDU)</span><b>${m.prop ? `${fmt2(m.prop)} m${sec && sec.cod ? ` · sección ${sec.cod}` : ''}` : 'sin cota en la propuesta'}</b></div>
    ${dif !== null ? `<div class="fila entre"><span>Diferencia</span><b>${dif > 0.25 ? `+${fmt2(dif)} m (ensanche)` : dif < -0.25 ? `${fmt2(dif)} m` : 'conforme'}</b></div>` : ''}
    ${sec ? `<canvas id="fSec" style="width:100%;height:92px;display:block;margin-top:8px"></canvas>
    <div class="ficha-t">${(sec.comp || []).map(([t, a]) => `${NOM_COMP[t] || t} ${fmt2(a)}`).join(' · ')}</div>` : ''}
    <div class="ficha-t">${sec ? sec.fuente + (sec.nota ? ` · ${sec.nota}` : '') + (m.secc_h || m.prop_h ? ' · asignada desde el tramo vecino del mismo jirón' : '') + '. ' : ''}Ancho actual: distancia entre líneas de manzana del Plano Total 2025 (JLORE), medida cada 2 m sobre el eje OSM.</div>`;
  $('ficha').classList.add('ver');
  if (sec) requestAnimationFrame(() => { const cv = $('fSec'); if (cv) dibujarSeccion(cv, sec, m.ancho); });
  const s = [];
  for (let k = 0; k < m.dens.length - 1; k++) {
    const a = m.dens[k], b = m.dens[k + 1], [tx, tz] = tangente(m.dens, k), [ux, uz] = tangente(m.dens, k + 1);
    s.push([a[0] - tz * a[2], a[1] + tx * a[2], b[0] - uz * b[2], b[1] + ux * b[2]], [a[0] + tz * a[3], a[1] - tx * a[3], b[0] + uz * b[3], b[1] - ux * b[3]]);
  }
  selPlano = lineaSel(s); escena.add(selPlano);
}
function abrirFichaManzana(m) {
  cerrarFicha(); limpiarSelPlano();
  const lados = m.lados.map((l, j) => [j + 1, l]).filter(([, l]) => l >= 4);
  $('fTitulo').textContent = 'Manzana (Plano Total 2025)';
  $('fCuerpo').innerHTML = `
    <div class="fila entre"><span>Área</span><b>${fmt2(m.a, 0)} m² · ${fmt2(m.a / 1e4, 3)} ha</b></div>
    <div class="fila entre"><span>Perímetro</span><b>${fmt2(m.per, 1)} m</b></div>
    <div class="fila entre"><span>Lados principales</span><b>${lados.length}</b></div>
    <div class="ficha-t">${lados.map(([j, l]) => `L${j} ${fmt2(l)}`).join(' · ')} m</div>
    <div class="ficha-t">Contorno de la capa «manzana ok» del Plano Total 2025. Los lados se miden sobre el contorno simplificado (tolerancia 1,5 m; se unen tramos casi alineados). Las cotas de cada lado aparecen sobre el modelo.</div>`;
  $('ficha').classList.add('ver');
  const s = [], P = m.pts, n = P.length / 2;
  for (let j = 0; j < n; j++) { const k = (j + 1) % n; s.push([P[j * 2], P[j * 2 + 1], P[k * 2], P[k * 2 + 1]]); }
  selPlano = lineaSel(s); escena.add(selPlano);
  const L = m.lp, nl = L.length;
  for (let j = 0; j < nl; j++) {
    const a = L[j], b = L[(j + 1) % nl], d = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (d < 4) continue;
    const el = document.createElement('div'); el.className = 'marca'; el.textContent = `L${j + 1} · ${fmt2(d)} m`; capaEt.appendChild(el);
    const x = (a[0] + b[0]) / 2, z = (a[1] + b[1]) / 2;
    etqSel.push({ el, p: new THREE.Vector3(x, altura(x, z) + 2.5, z) });
  }
}
function abrirFichaCorredor(s) {
  cerrarFicha(); limpiarSelPlano();
  const i = Math.round(s / PASO), fe = CH.fE[i] > 0 ? FE[i] : null, fo = CH.fO[i] > 0 ? FO[i] : null, ce = CE[i], co = CO[i];
  const sec = { cod: 'C3', ...(CH.plano || {}), fuente: 'Lámina 25 · Sistema vial (propuesta)' }, mit = sec.total / 2;
  const a = Math.max(0, s - 12), b = Math.min(CH.L, s + 12), pend = (interp(CH.y, a) - interp(CH.y, b)) / (b - a) * 100;
  const ancho = fe && fo ? fe + fo : null;
  $('fTitulo').textContent = `Jr. Chanchamayo · cdra. ${cuadraDe(s)}`;
  $('fCuerpo').innerHTML = `
    <div class="fila entre"><span>Estación</span><b>${fmt2(s, 0)} m desde la Plaza${Math.abs(s - CH.sT01) < 15 ? ' · T01' : ''}</b></div>
    <div class="fila entre"><span>Cota de calzada</span><b>${fmt2(interp(CH.y, s) + C.zmin)} msnm · pendiente ${fmt2(pend)} %</b></div>
    <div class="fila entre"><span>Ancho entre líneas de propiedad</span><b>${ancho ? fmt2(ancho) + ' m' : 'cruce / sin manzana'}</b></div>
    <div class="fila entre"><span>Calzada (sardinel a sardinel)</span><b>${fmt2(ce + co)} m</b></div>
    <div class="fila entre"><span>Sección propuesta (PDU)</span><b>C3 · ${fmt2(sec.total)} m</b></div>
    <div class="fila entre"><span>Afectación C3</span><b>${[['E', fe], ['O', fo]].map(([l, f]) => f === null ? `${l} —` : `${l} ${fmt2(Math.max(0, mit - f))} m`).join(' · ')}</b></div>
    <div class="fila entre"><span>Área aportante acumulada</span><b>${fmt2(interp(CH.A, s) / 1e4, 2)} ha</b></div>
    <canvas id="fSec" style="width:100%;height:92px;display:block;margin-top:8px"></canvas>
    <div class="ficha-t">Vereda 1,20 · cuneta 0,40 · vía rodada 7,30 · cuneta 0,40 · vereda 1,20 (lámina 25, PDU de Tarma, propuesta JLORE 2025). Líneas de propiedad: contorno de manzana del Plano Total 2025; cotas: curvas de nivel del mismo plano.</div>`;
  $('ficha').classList.add('ver');
  requestAnimationFrame(() => { const cv = $('fSec'); if (cv) dibujarSeccion(cv, sec, ancho); });
  const e = enEje(s), w = Math.max(mit, fe || 0, fo || 0) + 1;
  selPlano = lineaSel([[e.x - e.nx * w, e.z - e.nz * w, e.x + e.nx * w, e.z + e.nz * w]]); escena.add(selPlano);
}
function enCorredor(x, z) {           // estación del Jr. Chanchamayo si (x, z) cae dentro de su sección actual
  let best = Infinity, ib = -1;
  for (let i = 0; i < NEJ; i += 2) { const d = (CH.eje[i][0] - x) ** 2 + (CH.eje[i][1] - z) ** 2; if (d < best) { best = d; ib = i; } }
  if (ib < 0 || best > 400) return null;
  const e = enEje(ib * PASO), o = (x - e.x) * e.nx + (z - e.z) * e.nz;
  return (o >= 0 ? o <= FE[ib] + 0.2 : -o <= FO[ib] + 0.2) ? ib * PASO : null;
}
function pickPlano(r) {
  const h0 = r.intersectObject(terreno, false)[0];
  if (h0) { const s = enCorredor(h0.point.x, h0.point.z); if (s !== null) { abrirFichaCorredor(s); return true; } }
  const h1 = r.intersectObject(callesPlano, false)[0];
  if (h1 && triCalle[h1.faceIndex] !== undefined) { abrirFichaCalle(CALLES[triCalle[h1.faceIndex]]); return true; }
  if (h0) { const m = manzanaEn(h0.point.x, h0.point.z); if (m) { abrirFichaManzana(m); return true; } }
  return false;
}
const v3p = new THREE.Vector3();
function actualizarPlano() {
  for (const e of etqSel) {
    v3p.copy(e.p).project(camara);
    const ok = v3p.z < 1 && Math.abs(v3p.x) < 1.05 && Math.abs(v3p.y) < 1.05;
    e.el.style.display = ok ? '' : 'none';
    if (ok) { e.el.style.left = ((v3p.x + 1) / 2 * innerWidth) + 'px'; e.el.style.top = ((1 - v3p.y) / 2 * innerHeight) + 'px'; }
  }
}
