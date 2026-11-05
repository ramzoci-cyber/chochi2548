// ================================================================ CALLES DEL PLANO (Plano Total 2025): calzadas con el ancho medido entre manzanas,
// veredas y sardineles a lo largo de las líneas de manzana, y nombres de calles de cerca.
const grupoPlano = new THREE.Group(); escena.add(grupoPlano);
const CALLES = [], VEREDAS = [];
{
  const [nC, vC, nV, vV] = await Promise.all([
    inflar(C.calles.n, Uint16Array), inflar(C.calles.v, Float32Array), inflar(C.veredas.n, Uint16Array), inflar(C.veredas.v, Float32Array)]);
  let o = 0;
  C.calles.meta.forEach((m, i) => { const n = nC[i]; m.pts = vC.subarray(o * 4, (o + n) * 4); o += n; CALLES.push(m); });
  o = 0;
  C.veredas.meta.forEach(([w, lado], i) => { const n = nV[i]; VEREDAS.push({ w, lado, pts: vV.subarray(o * 2, (o + n) * 2) }); o += n; });
}
const H_CALZ = 0.16, H_SARD = 0.15;
function densificar(P, k, paso) {           // polilínea con k valores por vértice, tramos de paso máximo dado
  const n = P.length / k, out = [];
  for (let j = 0; j < n - 1; j++) {
    const a = j * k, b = a + k, L = Math.hypot(P[b] - P[a], P[b + 1] - P[a + 1]), m = Math.max(1, Math.ceil(L / paso));
    for (let t = 0; t < m; t++) { const f = t / m, v = []; for (let q = 0; q < k; q++) v.push(P[a + q] + (P[b + q] - P[a + q]) * f); out.push(v); }
  }
  const v = []; for (let q = 0; q < k; q++) v.push(P[(n - 1) * k + q]); out.push(v);
  return out;
}
function tangente(pts, k) {
  const a = pts[Math.max(0, k - 1)], b = pts[Math.min(pts.length - 1, k + 1)];
  let tx = b[0] - a[0], tz = b[1] - a[1]; const l = Math.hypot(tx, tz) || 1; return [tx / l, tz / l];
}
// ---------------------------------------------------------------- calzadas y eje pintado en las vías principales
const SUPP = [0x4b4d50, 0x9a9890, 0x8f7457, 0xb7ae9f].map(h => new THREE.Color(h));
const rcPl = { v: [], c: [], i: [], d: [] }, rmPl = { v: [], c: [], i: [], d: [] }, triCalle = [];
for (let ci = 0; ci < CALLES.length; ci++) {
  const m = CALLES[ci]; if (m.pts.length < 8) continue;
  const col = m.cl === 6 ? SUPP[3] : SUPP[m.sp], pts = densificar(m.pts, 4, 5);
  m.dens = pts;
  let dist = 0;
  for (let k = 0; k < pts.length; k++) {
    const p = pts[k], [tx, tz] = tangente(pts, k), nx = -tz, nz = tx;
    if (k) dist += Math.hypot(p[0] - pts[k - 1][0], p[1] - pts[k - 1][1]);
    const xl = p[0] + nx * p[2], zl = p[1] + nz * p[2], xr = p[0] - nx * p[3], zr = p[1] - nz * p[3];
    rcPl.v.push(xl, altura(xl, zl) + H_CALZ, zl, xr, altura(xr, zr) + H_CALZ, zr);
    rcPl.c.push(col.r, col.g, col.b, col.r, col.g, col.b); rcPl.d.push(dist, 0, dist, 1);
    if (k) { const i = rcPl.v.length / 3 - 4; rcPl.i.push(i, i + 2, i + 1, i + 1, i + 2, i + 3); triCalle.push(ci, ci); }
    if (m.cl <= 2 && m.sp !== 2) {
      const oc = (p[2] - p[3]) / 2, xc = p[0] + nx * oc, zc = p[1] + nz * oc, y = altura(xc, zc) + H_CALZ + 0.04;
      rmPl.v.push(xc + nx * 0.06, y, zc + nz * 0.06, xc - nx * 0.06, y, zc - nz * 0.06); rmPl.c.push(0.92, 0.8, 0.35, 0.92, 0.8, 0.35); rmPl.d.push(dist, 0, dist, 1);
      if (k) { const i = rmPl.v.length / 3 - 4; rmPl.i.push(i, i + 2, i + 1, i + 1, i + 2, i + 3); }
    }
  }
}
const callesPlano = mallaCinta(rcPl, matVia); callesPlano.receiveShadow = true; grupoPlano.add(callesPlano);
grupoPlano.add(mallaCinta(rmPl, matMarca));
// ---------------------------------------------------------------- veredas y sardineles
const GV = new Geo(), GS = new Geo();
for (const v of VEREDAS) {
  const P = v.pts, n = P.length / 2; if (n < 2) continue;
  const nor = [];
  for (let j = 0; j < n; j++) {
    let sx = 0, sz = 0;
    for (const [a, b] of [[j - 1, j], [j, j + 1]]) {
      if (a < 0 || b >= n) continue;
      const dx = P[b * 2] - P[a * 2], dz = P[b * 2 + 1] - P[a * 2 + 1], l = Math.hypot(dx, dz) || 1; sx += -dz / l; sz += dx / l;
    }
    const l = Math.hypot(sx, sz) || 1, nx = sx / l * v.lado, nz = sz / l * v.lado;
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
// ---------------------------------------------------------------- nombres de calles (se llama al crear las etiquetas)
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
function calleTocada(r) {
  const h = r.intersectObject(callesPlano, false)[0];
  return h && triCalle[h.faceIndex] !== undefined ? { calle: CALLES[triCalle[h.faceIndex]], punto: h.point } : null;
}
