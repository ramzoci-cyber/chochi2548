// ================================================================ JR. CHANCHAMAYO: calzada, veredas, cruces y mobiliario
const ARRIBA = [0, 1, 0];
const BLANCO = [1, 1, 1];
// ---------------------------------------------------------------- calzada (losas de concreto, bombeo 2 %, cuneta junto al sardinel)
{
  const filas = [];
  for (let i = 0; i < NEJ; i++) {
    const s = i * PASO, e = enEje(s), ce = CE[i], co = CO[i];
    const offs = [-co, -co + 0.4, -co * 0.5, 0, ce * 0.5, ce - 0.4, ce];
    filas.push(offs.map(o => [e.x + e.nx * o, yCalzada(s, o), e.z + e.nz * o, o, s]));
  }
  for (let i = 0; i < NEJ - 1; i++) for (let k = 0; k < 6; k++) {
    const a = filas[i][k], b = filas[i][k + 1], c = filas[i + 1][k + 1], d = filas[i + 1][k];
    const cuneta = (k === 0 || k === 5) ? 0.82 : 1;
    const uv = [a, b, c, d].map(p => [p[3] / 7.2 + 0.5, p[4] / 8]);
    G.pista.quad(a.slice(0, 3), b.slice(0, 3), c.slice(0, 3), d.slice(0, 3), ARRIBA, [cuneta, cuneta, cuneta * 0.98], uv);
  }
}
// ---------------------------------------------------------------- veredas y sardineles (solo frente a las caras de manzana)
for (const cara of CH.caras) {
  const lado = cara.lado, n = Math.max(2, Math.round((cara.s1 - cara.s0) / 1.0));
  let prev = null;
  for (let k = 0; k <= n; k++) {
    const s = cara.s0 + (cara.s1 - cara.s0) * k / n, e = enEje(s), c = cCalz(s, lado), f = fProp(s, lado) + 0.3;
    const yb = yCalzada(s, c), yt = yVereda(s, lado, c), yf = yVereda(s, lado, f);
    const P = (o, y) => [e.x + e.nx * o * lado, y, e.z + e.nz * o * lado];
    const fila = { s, c, f, borde: P(c, yb), canto: P(c, yt), canto2: P(c + 0.15, yt + 0.002), fondo: P(f, yf), nx: e.nx * lado, nz: e.nz * lado };
    if (prev) {
      // cara vertical del sardinel (mira a la calzada)
      G.concreto.quad(prev.borde, fila.borde, fila.canto, prev.canto, [-fila.nx, 0, -fila.nz], [0.86, 0.85, 0.82], [[prev.s / 2, 0], [s / 2, 0], [s / 2, 0.09], [prev.s / 2, 0.09]]);
      // remate del sardinel
      G.concreto.quad(prev.canto, fila.canto, fila.canto2, prev.canto2, ARRIBA, [0.93, 0.92, 0.89], [[prev.s / 2, 0], [s / 2, 0], [s / 2, 0.08], [prev.s / 2, 0.08]]);
      // superficie de la vereda
      G.vereda.quad(prev.canto2, fila.canto2, fila.fondo, prev.fondo, ARRIBA, [1, 1, 1],
        [[prev.s / 2, (c + 0.15) / 2], [s / 2, (c + 0.15) / 2], [s / 2, f / 2], [prev.s / 2, f / 2]]);
    }
    prev = fila;
  }
  // remates de esquina: cara del sardinel que mira al cruce
  for (const [s, sgn] of [[cara.s0, -1], [cara.s1, 1]]) {
    if (s <= 0.5 || s >= CH.L - 0.5) continue;
    const e = enEje(s), c = cCalz(s, lado), f = fProp(s, lado) + 0.3;
    const P = (o, y) => [e.x + e.nx * o * lado, y, e.z + e.nz * o * lado];
    G.concreto.quad(P(c, yCalzada(s, c)), P(f, yCalzada(s, c)), P(f, yVereda(s, lado, f)), P(c, yVereda(s, lado, c)), [e.tx * sgn, 0, e.tz * sgn], [0.86, 0.85, 0.82]);
  }
}
// ---------------------------------------------------------------- empalmes de calles transversales (16 m) con veredas y cruceros
const FRANJAS = [];
function cebra(G_, origen, dirLargo, dirAncho, largo, ancho0, ancho1, y) {      // franjas paralelas a dirLargo
  for (let o = ancho0 + 0.35; o + 0.45 <= ancho1 - 0.2; o += 0.9) {
    const P = (l, a) => [origen[0] + dirLargo[0] * l + dirAncho[0] * a, y, origen[1] + dirLargo[1] * l + dirAncho[1] * a];
    G_.quad(P(0, o), P(largo, o), P(largo, o + 0.45), P(0, o + 0.45), ARRIBA, [0.93, 0.93, 0.9]);
  }
}
for (const cr of CH.cruces) {
  const e = enEje(cr.s);
  for (const r of cr.ramas) {
    const lado = r.lado, d = r.dir, p = [-d[1], d[0]];
    const c = cCalz(cr.s, lado), T = 16, t0 = Math.max(0, c - 0.6);
    const J = [e.x, e.z];
    const y0 = yCalzada(cr.s, c * lado), pf = [J[0] + d[0] * T, J[1] + d[1] * T], y1 = altura(pf[0], pf[1]) + 0.25;
    const Y = t => y0 - 0.015 + (y1 - y0 + 0.015) * cl((t - t0) / (T - t0), 0, 1);    // un poco bajo la calzada principal al empalmar
    const n = 8;
    for (let k = 0; k < n; k++) {
      const ta = t0 + (T - t0) * k / n, tb = t0 + (T - t0) * (k + 1) / n;
      const P = (t, a, dy = 0) => [J[0] + d[0] * t + p[0] * a, Y(t) - BOMBEO * Math.abs(a) + dy, J[1] + d[1] * t + p[1] * a];
      for (const [a0, a1] of [[-3.3, 0], [0, 3.3]])
        G.pista.quad(P(ta, a0), P(tb, a0), P(tb, a1), P(ta, a1), ARRIBA, [0.97, 0.97, 0.95], [[a0 / 7.2 + 0.5, ta / 8], [a0 / 7.2 + 0.5, tb / 8], [a1 / 7.2 + 0.5, tb / 8], [a1 / 7.2 + 0.5, ta / 8]]);
      // veredas de la transversal (desde la línea de propiedad del jirón)
      const tv = fProp(cr.s, lado) - 0.2;
      if (tb > tv) {
        const tA = Math.max(ta, tv);
        for (const sg of [-1, 1]) {
          const a0 = sg * 3.3, a1 = sg * 4.6;
          const Q = (t, a, h) => [J[0] + d[0] * t + p[0] * a, Y(t) - BOMBEO * 3.3 + h, J[1] + d[1] * t + p[1] * a];
          G.vereda.quad(Q(tA, a0, SARD), Q(tb, a0, SARD), Q(tb, a1, SARD + 0.02), Q(tA, a1, SARD + 0.02), ARRIBA, [1, 1, 1], [[tA / 2, a0 / 2], [tb / 2, a0 / 2], [tb / 2, a1 / 2], [tA / 2, a1 / 2]]);
          G.concreto.quad(Q(tA, a0, 0), Q(tb, a0, 0), Q(tb, a0, SARD), Q(tA, a0, SARD), [-p[0] * sg, 0, -p[1] * sg], [0.86, 0.85, 0.82]);
        }
      }
    }
    // crucero sobre la transversal
    const tc = fProp(cr.s, lado) + 0.6;
    cebra(G.pintura, [J[0] + d[0] * tc, J[1] + d[1] * tc], d, p, 3, -3.3, 3.3, Y(tc + 1.5) + 0.03);
  }
  // cruceros sobre el Jr. Chanchamayo, a ambos lados del cruce
  for (const sg of [-1, 1]) {
    const sc = cr.s + sg * 4.6;
    if (sc < 0.5 || sc > CH.L - 3.5) continue;
    const s0 = sg < 0 ? sc - 3 : sc, ee = enEje(s0), co = cCalz(s0, -1), ce = cCalz(s0, 1);
    const largo = 3, t = [ee.tx, ee.tz], n = [ee.nx, ee.nz];
    for (let o = -co + 0.35; o + 0.45 <= ce - 0.2; o += 0.9) {
      const P = (l, a) => { const q = enEje(s0 + l); return [q.x + q.nx * a, yCalzada(s0 + l, a) + 0.025, q.z + q.nz * a]; };
      G.pintura.quad(P(0, o), P(largo, o), P(largo, o + 0.45), P(0, o + 0.45), ARRIBA, [0.93, 0.93, 0.9]);
    }
  }
}
// ---------------------------------------------------------------- buzones (desagüe) y sumideros (rejillas pluviales)
for (const s of CH.buzones) {
  const e = enEje(s), o = 0.0, y = yCalzada(s, o) + 0.015, r = 0.36;
  const P = (a, b) => [e.x + e.tx * a + e.nx * b, y, e.z + e.tz * a + e.nz * b];
  G.buzon.quad(P(-r, -r), P(r, -r), P(r, r), P(-r, r), ARRIBA, BLANCO, [[0, 0], [1, 0], [1, 1], [0, 1]]);
}
for (const sm of CH.sumideros) {
  const e = enEje(sm.s), c = cCalz(sm.s, sm.lado), o = (c - 0.3) * sm.lado, y = yCalzada(sm.s, o) + 0.012;
  const P = (a, b) => [e.x + e.tx * a + e.nx * (o + b), y, e.z + e.tz * a + e.nz * (o + b)];
  G.rejilla.quad(P(-0.5, -0.22), P(0.5, -0.22), P(0.5, 0.22), P(-0.5, 0.22), ARRIBA, BLANCO, [[0, 0], [1, 0], [1, 1], [0, 1]]);
}
// ---------------------------------------------------------------- postes de concreto, alumbrado, transformadores y cables
const posPostes = [];
const halos = new Geo();
for (const pt of CH.postes) {
  const e = enEje(pt.s), c = cCalz(pt.s, pt.lado), o = c + 0.4;
  const x = e.x + e.nx * o * pt.lado, z = e.z + e.nz * o * pt.lado, y = yVereda(pt.s, pt.lado, o);
  G.concreto.cilindro(x, y - 0.5, z, 0.16, 0.1, 11.5, 8, [0.84, 0.83, 0.8]);
  const tx = e.tx, tz = e.tz, hx = -e.nx * pt.lado, hz = -e.nz * pt.lado;     // h: hacia el centro de la calle
  G.concreto.caja(x, y + 10.25, z, 1.9, 0.12, 0.12, tx, tz, [0.78, 0.77, 0.74]);     // cruceta
  const aisl = [];
  for (const a of [-0.8, 0, 0.8]) { const ax = x + tx * a, az = z + tz * a; G.metal.cilindro(ax, y + 10.31, az, 0.05, 0.035, 0.18, 6, [0.55, 0.42, 0.3]); aisl.push([ax, y + 10.5, az]); }
  G.metal.caja(x + hx * 0.12, y + 7.6, z + hz * 0.12, 0.08, 0.7, 0.05, tx, tz, [0.35, 0.36, 0.37]);              // rack de baja tensión
  // pastoral de alumbrado
  const brazo0 = [x + hx * 0.12, y + 8.6, z + hz * 0.12], brazo1 = [x + hx * 1.9, y + 9.0, z + hz * 1.9];
  G.metal.tubo(brazo0, brazo1, 0.035, [0.42, 0.43, 0.44], 5);
  G.metal.caja(brazo1[0] + hx * 0.25, brazo1[1] - 0.02, brazo1[2] + hz * 0.25, 0.62, 0.1, 0.26, hx, hz, [0.3, 0.31, 0.32]);
  G.foco.caja(brazo1[0] + hx * 0.25, brazo1[1] - 0.085, brazo1[2] + hz * 0.25, 0.5, 0.03, 0.18, hx, hz, [0.95, 0.93, 0.85], 1, false, 1);
  if (pt.trafo) G.metal.cilindro(x - hx * 0.45, y + 8.3, z - hz * 0.45, 0.33, 0.33, 1.0, 10, [0.55, 0.58, 0.6]);
  // halo de luz sobre la calle (de noche)
  const lx = brazo1[0] + hx * 0.25, lz = brazo1[2] + hz * 0.25, R = 8, yl = yCalzada(pt.s, 0) + 0.04;
  halos.quad([lx - R, yl, lz - R], [lx + R, yl, lz - R], [lx + R, yl, lz + R], [lx - R, yl, lz + R], ARRIBA, BLANCO, [[0, 0], [1, 0], [1, 1], [0, 1]]);
  posPostes.push({ s: pt.s, lado: pt.lado, x, y, z, aisl, bt: [x + hx * 0.16, y + 7.75, z + hz * 0.16], tel: [x + hx * 0.16, y + 6.4, z + hz * 0.16], foco: [lx, brazo1[1] - 0.1, lz] });
}
function catenaria(Gm, a, b, flecha, r, col) {
  const n = Math.max(4, Math.round(Math.hypot(b[0] - a[0], b[2] - a[2]) / 3));
  let p0 = a;
  for (let k = 1; k <= n; k++) {
    const t = k / n, p1 = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t - flecha * 4 * t * (1 - t), a[2] + (b[2] - a[2]) * t];
    Gm.tubo(p0, p1, r, col, 3); p0 = p1;
  }
}
const GC = new Geo();          // cables (no proyectan sombra)
posPostes.sort((a, b) => a.s - b.s);
for (let k = 0; k < posPostes.length - 1; k++) {
  const A = posPostes[k], B = posPostes[k + 1];
  if (B.s - A.s > 70) continue;
  for (let q = 0; q < 3; q++) catenaria(GC, A.aisl[q], B.aisl[q], 0.45, 0.011, [0.12, 0.12, 0.12]);
  catenaria(GC, A.bt, B.bt, 0.6, 0.016, [0.08, 0.08, 0.08]);
  catenaria(GC, A.tel, B.tel, 0.7, 0.013, [0.1, 0.1, 0.1]);
  catenaria(GC, [A.tel[0], A.tel[1] - 0.3, A.tel[2]], [B.tel[0], B.tel[1] - 0.3, B.tel[2]], 0.8, 0.01, [0.15, 0.15, 0.15]);
}
// ---------------------------------------------------------------- semáforos en los cruces con señal (OSM)
const semaforos = [];
{
  const mRojo = new THREE.MeshStandardMaterial({ color: 0x3a0a08, emissive: 0xff2a12, emissiveIntensity: 0 });
  const geoLente = new THREE.CircleGeometry(0.1, 14);
  let fase = 0;
  for (const cr of CH.cruces) {
    if (!cr.semaforo) continue;
    fase += 9;
    for (const [sg, lado] of [[-1, 1], [1, -1]]) {
      const s = cl(cr.s + sg * 7.5, 1, CH.L - 1), e = enEje(s), c = cCalz(s, lado), o = c + 0.45;
      const x = e.x + e.nx * o * lado, z = e.z + e.nz * o * lado, y = yVereda(s, lado, o);
      G.metal.cilindro(x, y, z, 0.07, 0.06, 3.6, 8, [0.32, 0.33, 0.35]);
      const mira = [-e.tx * sg, -e.tz * sg];                  // la cara mira al tránsito que llega
      const cx = x + mira[0] * 0.18, cz = z + mira[1] * 0.18;
      G.metal.caja(cx, y + 3.15, cz, 0.32, 0.95, 0.24, -mira[1], mira[0], [0.08, 0.08, 0.09]);
      const luces = [];
      for (const [k, col] of [[0, 0xff2a12], [1, 0xffb000], [2, 0x18e05a]]) {
        const m = new THREE.MeshStandardMaterial({ color: 0x111111, emissive: col, emissiveIntensity: 0.05, roughness: 0.3 });
        const lente = new THREE.Mesh(geoLente, m);
        lente.position.set(cx + mira[0] * 0.125, y + 3.45 - k * 0.3, cz + mira[1] * 0.125);
        lente.lookAt(lente.position.x + mira[0], lente.position.y, lente.position.z + mira[1]);
        grupoDetalle.add(lente); luces.push(m);
      }
      semaforos.push({ luces, fase: fase + (sg > 0 ? 15 : 0) });
    }
  }
}
function actualizarSemaforos(t) {
  for (const sm of semaforos) {
    const c = (t + sm.fase) % 30, est = c < 13 ? 2 : c < 16 ? 1 : 0;
    sm.luces.forEach((m, k) => { m.emissiveIntensity = k === est ? 2.6 : 0.04; });
  }
}
// ---------------------------------------------------------------- placas con nombres de calles (esquinas)
function texturaTexto(lineas, ancho, alto, fondo, tinta, borde = true) {
  return lienzoTex(ancho, alto, (g, w, h) => {
    g.fillStyle = fondo; g.fillRect(0, 0, w, h);
    if (borde) { g.strokeStyle = tinta; g.lineWidth = Math.max(3, h * 0.05); g.strokeRect(h * 0.06, h * 0.06, w - h * 0.12, h - h * 0.12); }
    g.fillStyle = tinta; g.textAlign = 'center'; g.textBaseline = 'middle';
    const n = lineas.length;
    lineas.forEach((t, k) => {
      let fs = h * (n > 1 ? (k === 0 ? 0.36 : 0.24) : 0.5);
      g.font = `600 ${fs}px Inter, "Segoe UI", Arial, sans-serif`;
      while (g.measureText(t).width > w * 0.9 && fs > 8) { fs -= 1; g.font = `600 ${fs}px Inter, "Segoe UI", Arial, sans-serif`; }
      g.fillText(t, w / 2, h * (n > 1 ? (k === 0 ? 0.38 : 0.74) : 0.53));
    });
  });
}
const geoPlaca = new THREE.PlaneGeometry(1, 1);
function cartel(tex, x, y, z, ancho, alto, nx, nz, doble = false) {
  const mat = new THREE.MeshStandardMaterial({ map: tex, roughness: 0.6 });
  for (const sg of doble ? [1, -1] : [1]) {       // placa de dos caras: cada cara se lee al derecho
    const m = new THREE.Mesh(geoPlaca, mat); m.scale.set(ancho, alto, 1);
    m.position.set(x + nx * 0.012 * sg, y, z + nz * 0.012 * sg); m.lookAt(m.position.x + nx * sg, y, m.position.z + nz * sg); grupoDetalle.add(m);
  }
}
const abrev = n => n.replace('Jirón', 'JR.').replace('Avenida', 'AV.').replace('Ayacuho', 'Ayacucho').toUpperCase();
function cuadraDe(s) { for (const c of CH.cuadras) if (s >= c.s0 && s < c.s1) return c.n; return 1; }
for (const cr of CH.cruces) {
  const r = cr.ramas.find(q => q.nombre !== '(sin nombre)'); if (!r) continue;
  const lado = r.lado, sg = cr.s > CH.L - 5 ? -1 : 1;
  const s = cl(cr.s + sg * 6.2, 0.5, CH.L - 0.5), e = enEje(s), c = cCalz(s, lado), o = c + 0.35;
  const x = e.x + e.nx * o * lado, z = e.z + e.nz * o * lado, y = yVereda(s, lado, o);
  G.metal.cilindro(x, y, z, 0.035, 0.035, 2.75, 6, [0.3, 0.32, 0.34]);
  const t1 = texturaTexto([abrev(r.nombre)], 512, 128, '#1f4e8c', '#ffffff');
  const t2 = texturaTexto(['JR. CHANCHAMAYO', `CUADRA ${cuadraDe(s)}`], 512, 160, '#1f4e8c', '#ffffff');
  // placa de la transversal: paralela a la transversal, visible desde el jirón
  cartel(t1, x, y + 2.55, z, 0.8, 0.2, e.tx, e.tz, true);
  cartel(t2, x, y + 2.27, z, 0.8, 0.25, -e.nx * lado, -e.nz * lado, true);
}
// ---------------------------------------------------------------- vehículos estacionados (autos, mototaxis, combis, camionetas)
const grupoVehic = new THREE.Group(); grupoDetalle.add(grupoVehic);
function prisma(Gm, xb0, xb1, wb, xt0, xt1, wt, y0, y1, col, tapa = true) {     // tronco de pirámide (cabina)
  const B = [[xb0, y0, -wb], [xb1, y0, -wb], [xb1, y0, wb], [xb0, y0, wb]], T = [[xt0, y1, -wt], [xt1, y1, -wt], [xt1, y1, wt], [xt0, y1, wt]];
  const cx = (xb0 + xb1 + xt0 + xt1) / 4, cy = (y0 + y1) / 2;
  for (let k = 0; k < 4; k++) {
    const a = B[k], b = B[(k + 1) % 4], c = T[(k + 1) % 4], d = T[k];
    const m = [(a[0] + b[0] + c[0] + d[0]) / 4 - cx, (a[1] + b[1] + c[1] + d[1]) / 4 - cy, (a[2] + b[2] + c[2] + d[2]) / 4];
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = d[0] - a[0], vy = d[1] - a[1], vz = d[2] - a[2];
    let n = [uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx]; const l = Math.hypot(...n) || 1; n = n.map(v => v / l);
    if (n[0] * m[0] + n[1] * m[1] + n[2] * m[2] < 0) n = n.map(v => -v);
    Gm.quad(a, b, c, d, n, col);
  }
  if (tapa) Gm.quad(T[0], T[1], T[2], T[3], ARRIBA, col);
}
function plantillaVehiculo(tipo) {
  const cuerpo = new Geo(), oscuro = new Geo(), vidrio = new Geo();
  const caja = (Gm, x, y, z, lu, al, lw, col) => Gm.caja(x, y, z, lu, al, lw, 1, 0, col);
  const NEG = [0.07, 0.07, 0.08], FARO = [1, 0.97, 0.85], STOP = [0.75, 0.05, 0.05], VID = [0.16, 0.19, 0.23];
  oscuro._extra = [];
  const ruedas = (xs, zs, r, ancho = 0.22) => { for (const x of xs) for (const z of zs) { const g = new THREE.CylinderGeometry(r, r, ancho, 14); g.rotateX(Math.PI / 2); g.translate(x, r, z); oscuro._extra.push(g); const a = new THREE.CylinderGeometry(r * 0.55, r * 0.55, ancho + 0.02, 10); a.rotateX(Math.PI / 2); a.translate(x, r, z); vidrio._extra = vidrio._extra || []; vidrio._extra.push(a); } };
  if (tipo === 'auto') {                     // sedán
    caja(cuerpo, 0, 0.62, 0, 4.35, 0.56, 1.74, BLANCO);
    prisma(cuerpo, -2.18, 2.18, 0.87, -2.0, 2.05, 0.84, 0.9, 1.0, BLANCO);              // cintura
    prisma(vidrio, -1.35, 1.05, 0.83, -0.95, 0.35, 0.72, 1.0, 1.42, VID, false);         // cabina vidriada
    prisma(cuerpo, -0.95, 0.35, 0.72, -0.85, 0.28, 0.7, 1.42, 1.47, BLANCO);             // techo
    caja(oscuro, 2.19, 0.48, 0, 0.06, 0.2, 1.62, NEG); caja(oscuro, -2.19, 0.48, 0, 0.06, 0.2, 1.62, NEG);
    for (const z of [-0.62, 0.62]) { caja(vidrio, 2.18, 0.78, z, 0.04, 0.12, 0.3, FARO); caja(vidrio, -2.18, 0.8, z, 0.04, 0.12, 0.28, STOP); }
    ruedas([-1.35, 1.35], [-0.76, 0.76], 0.31);
  } else if (tipo === 'camioneta') {         // pick-up
    caja(cuerpo, 0, 0.86, 0, 5.25, 0.6, 1.86, BLANCO);
    prisma(vidrio, 0.0, 2.0, 0.9, 0.25, 1.35, 0.8, 1.16, 1.72, VID, false);
    prisma(cuerpo, 0.25, 1.35, 0.8, 0.3, 1.3, 0.78, 1.72, 1.78, BLANCO);
    for (const z of [-0.9, 0.9]) caja(cuerpo, -1.4, 1.36, z, 2.4, 0.42, 0.06, BLANCO);
    caja(cuerpo, -2.6, 1.36, 0, 0.06, 0.42, 1.86, BLANCO);
    caja(oscuro, -1.4, 1.17, 0, 2.3, 0.04, 1.74, [0.2, 0.2, 0.2]);
    for (const z of [-0.7, 0.7]) { caja(vidrio, 2.63, 0.98, z, 0.04, 0.14, 0.32, FARO); caja(vidrio, -2.63, 1.0, z, 0.04, 0.2, 0.2, STOP); }
    ruedas([-1.65, 1.6], [-0.8, 0.8], 0.39, 0.26);
  } else if (tipo === 'combi') {             // combi de transporte urbano
    caja(cuerpo, -0.15, 1.2, 0, 4.4, 1.62, 1.84, BLANCO);
    prisma(cuerpo, 2.05, 2.45, 0.92, 2.05, 2.25, 0.9, 0.39, 1.25, BLANCO);
    prisma(vidrio, 2.06, 2.25, 0.86, 2.06, 2.12, 0.86, 1.25, 1.92, VID, false);
    caja(vidrio, -0.2, 1.6, 0, 4.0, 0.55, 1.86, VID);
    caja(cuerpo, -0.15, 0.62, 0, 4.45, 0.12, 1.86, [0.85, 0.85, 0.85]);
    for (const z of [-0.65, 0.65]) { caja(vidrio, 2.46, 0.8, z, 0.04, 0.16, 0.3, FARO); caja(vidrio, -2.36, 0.85, z, 0.04, 0.3, 0.2, STOP); }
    ruedas([-1.55, 1.55], [-0.8, 0.8], 0.33);
  } else {                                   // mototaxi
    caja(cuerpo, -0.45, 0.6, 0, 1.5, 0.42, 1.24, BLANCO);                                 // carrocería trasera
    caja(oscuro, -0.55, 0.95, 0, 0.6, 0.3, 1.1, [0.12, 0.1, 0.1]);                        // asiento
    caja(oscuro, -0.95, 1.25, 0, 0.12, 0.5, 1.1, [0.12, 0.1, 0.1]);                       // respaldar
    prisma(cuerpo, -1.25, 1.1, 0.7, -1.15, 0.95, 0.68, 1.88, 1.98, BLANCO);                // toldo
    for (const [x, z] of [[0.95, 0.6], [0.95, -0.6], [-1.15, 0.62], [-1.15, -0.62]]) caja(oscuro, x, 1.32, z, 0.04, 1.12, 0.04, NEG);
    caja(vidrio, 1.0, 1.42, 0, 0.03, 0.62, 1.06, [0.3, 0.33, 0.36]);                     // parabrisas
    caja(cuerpo, 0.55, 0.62, 0, 0.7, 0.28, 0.42, BLANCO);                                   // tanque
    caja(oscuro, 0.75, 0.9, 0, 0.5, 0.12, 0.3, NEG);                                        // asiento conductor
    caja(oscuro, 1.18, 1.05, 0, 0.05, 0.05, 0.75, NEG);                                     // timón
    Geo.prototype.tubo.call(oscuro, [1.15, 1.02, 0], [1.38, 0.3, 0], 0.035, NEG);          // horquilla
    caja(vidrio, 1.22, 0.95, 0, 0.06, 0.12, 0.14, FARO);
    caja(vidrio, -1.2, 0.66, 0.5, 0.03, 0.1, 0.12, STOP); caja(vidrio, -1.2, 0.66, -0.5, 0.03, 0.1, 0.12, STOP);
    ruedas([1.38], [0], 0.25, 0.12); ruedas([-0.75], [-0.56, 0.56], 0.25, 0.14);
  }
  const unir = (Gm, extra, tono = 0.06) => {
    const m = Gm.malla(null); let g = m.geometry; g.deleteAttribute('aLuz');
    if (extra) {
      const ex = extra.map(e => { const q = e.index ? e.toNonIndexed() : e; q.deleteAttribute('uv'); q.setAttribute('color', new THREE.BufferAttribute(new Float32Array(q.attributes.position.count * 3).fill(tono), 3)); return q; });
      g.deleteAttribute('uv'); g = mergeGeos([g, ...ex]);
    }
    return g;
  };
  return { cuerpo: unir(cuerpo), oscuro: unir(oscuro, oscuro._extra), vidrio: unir(vidrio, vidrio._extra, 0.62) };
}
function mergeGeos(geos) {
  let n = 0; for (const g of geos) n += g.attributes.position.count;
  const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), col = new Float32Array(n * 3); let o = 0;
  for (const g of geos) {
    const c = g.attributes.position.count;
    pos.set(g.attributes.position.array, o * 3); nor.set(g.attributes.normal.array, o * 3);
    if (g.attributes.color) col.set(g.attributes.color.array, o * 3); else col.fill(1, o * 3, (o + c) * 3);
    o += c;
  }
  const r = new THREE.BufferGeometry();
  r.setAttribute('position', new THREE.BufferAttribute(pos, 3)); r.setAttribute('normal', new THREE.BufferAttribute(nor, 3)); r.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return r;
}
{
  const tipos = ['auto', 'mototaxi', 'combi', 'camioneta'];
  const matCuerpo = matStd({ vertexColors: true, roughness: 0.35, metalness: 0.5, envMapIntensity: 1.0 });
  const matOscuro = matStd({ vertexColors: true, roughness: 0.7, metalness: 0.1 });
  const matVid = matStd({ vertexColors: true, roughness: 0.05, metalness: 0.6, envMapIntensity: 1.4 });
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(1, 1, 1), p = new THREE.Vector3(), col = new THREE.Color();
  for (const tipo of tipos) {
    const lista = CH.vehiculos.filter(v => v.tipo === tipo); if (!lista.length) continue;
    const pl = plantillaVehiculo(tipo);
    const ic = new THREE.InstancedMesh(pl.cuerpo, matCuerpo, lista.length), io = new THREE.InstancedMesh(pl.oscuro, matOscuro, lista.length), iv = new THREE.InstancedMesh(pl.vidrio, matVid, lista.length);
    lista.forEach((v, k) => {
      const e = enEje(v.s), c = cCalz(v.s, v.lado), o = (c - (tipo === 'mototaxi' ? 0.85 : 1.05)) * v.lado;
      p.set(e.x + e.nx * o, yCalzada(v.s, o), e.z + e.nz * o);
      q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), Math.atan2(-e.tz, e.tx));
      m4.compose(p, q, sc); ic.setMatrixAt(k, m4); io.setMatrixAt(k, m4); iv.setMatrixAt(k, m4);
      ic.setColorAt(k, col.set(tipo === 'mototaxi' ? ['#c0392b', '#2457a6', '#e1b12c', '#1e8449'][k % 4] : v.color));
    });
    for (const m of [ic, io, iv]) { m.castShadow = true; m.receiveShadow = true; grupoVehic.add(m); }
  }
}
