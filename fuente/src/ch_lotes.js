// ================================================================ JR. CHANCHAMAYO: viviendas lote por lote
// Volumen y altura de cada lote: ráster Google Open Buildings 2.5D (2023). Fachadas: tipologías locales (adobe/teja,
// ladrillo caravista con pórticos de concreto, tarrajeo pintado) asignadas por reglas y editables en C.chanchamayo.lotes.
const tanques2 = [];                         // [x, y, z, tipo]
const cajasPick = new Geo();                 // volumen simple por lote para seleccionar con el ratón
const VOL = 0.7;                             // volado sobre la vereda (m)
function lin(h, f = 1) { return rgbLin(h, f); }
function mezcla(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
const GRIS_VIGA = [0.72, 0.71, 0.68], MARCO_AL = [0.78, 0.79, 0.8], MARCO_NEG = [0.12, 0.12, 0.13];

// marco local de una fachada recta: origen O, dirección U (a lo largo), normal exterior N (hacia la calle)
function Marco(O, U, N, uv0) {
  const P = (u, y, w = 0) => [O[0] + U[0] * u + N[0] * w, y, O[1] + U[1] * u + N[1] * w];
  const n3 = [N[0], 0, N[1]], u3 = [U[0], 0, U[1]];
  return {
    P, n3, u3,
    // rectángulo paralelo a la fachada (mira hacia N), uv en metros
    rect(Gm, u0, u1, y0, y1, w, col, esc = 0.5, luz = 0) {
      if (u1 - u0 < 1e-3 || y1 - y0 < 1e-3) return;
      Gm.quad(P(u0, y0, w), P(u1, y0, w), P(u1, y1, w), P(u0, y1, w), n3, col, [[(uv0 + u0) * esc, y0 * esc], [(uv0 + u1) * esc, y0 * esc], [(uv0 + u1) * esc, y1 * esc], [(uv0 + u0) * esc, y1 * esc]], luz);
    },
    // caja que sobresale de la fachada entre w0 y w1
    caja(Gm, u0, u1, y0, y1, w0, w1, col, esc = 0.5, luz = 0) {
      const um = (u0 + u1) / 2, wm = (w0 + w1) / 2, c = P(um, (y0 + y1) / 2, wm);
      Gm.caja(c[0], c[1], c[2], u1 - u0, y1 - y0, w1 - w0, U[0], U[1], col, esc, false, luz);
    },
    // vano con derrame: el muro se resuelve aparte; aquí las caras interiores del hueco y el fondo
    derrame(Gm, u0, u1, y0, y1, prof, col) {
      Gm.quad(P(u0, y0, 0), P(u0, y1, 0), P(u0, y1, -prof), P(u0, y0, -prof), u3, col);
      Gm.quad(P(u1, y0, 0), P(u1, y1, 0), P(u1, y1, -prof), P(u1, y0, -prof), [-U[0], 0, -U[1]], col);
      Gm.quad(P(u0, y1, 0), P(u1, y1, 0), P(u1, y1, -prof), P(u0, y1, -prof), [0, -1, 0], mezcla(col, [0, 0, 0], 0.25));
      Gm.quad(P(u0, y0, 0), P(u1, y0, 0), P(u1, y0, -prof), P(u0, y0, -prof), ARRIBA, col);
    },
  };
}
// muro con huecos: rectángulos de muro que rodean una lista de vanos [u0,u1,y0,y1]
function muroConVanos(M, Gm, u0, u1, y0, y1, w, vanos, col, esc) {
  const xs = [u0, u1]; for (const v of vanos) xs.push(v[0], v[1]);
  const us = [...new Set(xs.map(x => +x.toFixed(4)))].sort((a, b) => a - b);
  for (let k = 0; k < us.length - 1; k++) {
    const a = us[k], b = us[k + 1]; if (b - a < 1e-3) continue;
    const mid = (a + b) / 2, cort = vanos.filter(v => v[0] <= mid && v[1] >= mid).sort((p, q) => p[2] - q[2]);
    let y = y0;
    for (const v of cort) { if (v[2] > y) M.rect(Gm, a, b, y, v[2], w, col, esc); y = Math.max(y, v[3]); }
    if (y1 > y) M.rect(Gm, a, b, y, y1, w, col, esc);
  }
}
function ventana(M, u0, u1, y0, y1, marco, luz, conReja, rnd, madera = null) {
  const prof = 0.14;
  M.derrame(G.pared, u0, u1, y0, y1, prof, [0.82, 0.8, 0.76]);
  M.rect(G.vidrio, u0, u1, y0, y1, -prof, [0.36, 0.42, 0.48], 0.5, luz);
  const t = 0.045, Gm = madera ? G.madera : G.metal, col = madera || marco;
  M.caja(Gm, u0, u1, y0, y0 + t, -prof, -prof + 0.06, col); M.caja(Gm, u0, u1, y1 - t, y1, -prof, -prof + 0.06, col);
  M.caja(Gm, u0, u0 + t, y0, y1, -prof, -prof + 0.06, col); M.caja(Gm, u1 - t, u1, y0, y1, -prof, -prof + 0.06, col);
  const nh = (u1 - u0) > 1.2 ? 2 : 1;
  for (let k = 1; k <= nh; k++) { const um = u0 + (u1 - u0) * k / (nh + 1); M.caja(Gm, um - t / 2, um + t / 2, y0, y1, -prof, -prof + 0.06, col); }
  if (madera) M.caja(Gm, u0, u1, y0 + (y1 - y0) * 0.62, y0 + (y1 - y0) * 0.62 + t, -prof, -prof + 0.06, col);
  M.caja(G.concreto, u0 - 0.05, u1 + 0.05, y0 - 0.06, y0, 0, 0.07, [0.85, 0.84, 0.8]);       // alféizar
  if (conReja) {
    for (let u = u0 + 0.1; u < u1 - 0.05; u += 0.13) M.caja(G.metal, u, u + 0.018, y0 + 0.02, y1 - 0.02, 0.03, 0.05, [0.1, 0.1, 0.1]);
    for (const yy of [y0 + 0.1, y1 - 0.12]) M.caja(G.metal, u0 + 0.02, u1 - 0.02, yy, yy + 0.03, 0.03, 0.055, [0.1, 0.1, 0.1]);
  }
}
function puerta(M, u0, u1, y0, y1, col, mat = 'madera') {
  const prof = 0.12;
  M.derrame(G.pared, u0, u1, y0, y1, prof, [0.8, 0.78, 0.74]);
  const Gm = mat === 'madera' ? G.madera : G.metal;
  M.rect(Gm, u0, u1, y0, y1, -prof, col, 0.6);
  const t = 0.06;
  for (const [a, b] of [[u0, u0 + t], [u1 - t, u1]]) M.caja(Gm, a, b, y0, y1, -prof, -prof + 0.04, mezcla(col, [0, 0, 0], 0.3));
  const nh = (u1 - u0) > 1.3 ? 2 : 1;
  for (let k = 0; k < nh; k++) {          // tableros
    const a = u0 + 0.12 + k * (u1 - u0 - 0.12) / nh, b = a + (u1 - u0 - 0.24) / nh - 0.08;
    M.caja(Gm, a, b, y0 + 0.25, y0 + (y1 - y0) * 0.45, -prof, -prof + 0.03, mezcla(col, [1, 1, 1], 0.08));
    M.caja(Gm, a, b, y0 + (y1 - y0) * 0.52, y1 - 0.2, -prof, -prof + 0.03, mezcla(col, [1, 1, 1], 0.08));
  }
}
function tienda(M, u0, u1, y0, y1, estado, colPersiana, rnd) {
  const prof = 0.18;
  M.derrame(G.pared, u0, u1, y0, y1, prof, [0.78, 0.76, 0.72]);
  M.caja(G.metal, u0 - 0.05, u1 + 0.05, y1, y1 + 0.32, 0, 0.12, mezcla(colPersiana, [0, 0, 0], 0.2));   // cajón de la cortina
  if (estado === 0) {                                  // cortina metálica cerrada
    M.rect(G.persiana, u0, u1, y0, y1, -prof * 0.5, colPersiana, 0.5);
  } else {                                             // abierta: vitrina e interior iluminado
    const ya = estado === 2 ? y0 + (y1 - y0) * 0.55 : y1;
    if (estado === 2) M.rect(G.persiana, u0, u1, ya, y1, -prof * 0.5, colPersiana, 0.5);
    M.rect(G.vidrio, u0, u1, y0, ya, -prof - 2.2, [0.42, 0.36, 0.28], 0.5, 0.9 + 0.5 * rnd());
    // mercadería / mostrador
    const nb = Math.max(1, Math.floor((u1 - u0) / 0.9));
    for (let k = 0; k < nb; k++) {
      const a = u0 + 0.1 + k * (u1 - u0 - 0.2) / nb, b = a + (u1 - u0 - 0.2) / nb - 0.12, hh = 0.6 + 1.1 * rnd();
      M.caja(G.pared, a, b, y0, Math.min(ya - 0.1, y0 + hh), -prof - 2.1, -prof - 1.7, lin(['#c0392b', '#2471a3', '#f1c40f', '#27ae60', '#8e44ad', '#e67e22', '#ecf0f1'][Math.floor(rnd() * 7)]));
    }
    M.caja(G.madera, u0 + 0.2, u1 - 0.2, y0, y0 + 0.95, -prof - 1.2, -prof - 0.7, [0.55, 0.4, 0.28]);
    M.derrame(G.pared, u0, u1, y0, ya, 2.2 + prof, [0.55, 0.5, 0.45]);
  }
}
function letrero(M, u0, u1, y0, y1, l, rnd) {
  if (l.nombre) {
    const ancho = u1 - u0, alto = y1 - y0;
    const tex = texturaTexto([l.nombre], 1024, Math.round(1024 * alto / ancho * 1.0) || 128, ['#b71c1c', '#0d47a1', '#1b5e20', '#f9a825', '#4a148c', '#263238'][l.id % 6], '#ffffff', false);
    const c = M.P((u0 + u1) / 2, (y0 + y1) / 2, 0.075);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(ancho, alto), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.55, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0 }));
    m.position.set(...c); m.lookAt(c[0] + M.n3[0], c[1], c[2] + M.n3[2]); grupoDetalle.add(m);
    letrerosLuz.push(m.material);
    M.caja(G.metal, u0 - 0.04, u1 + 0.04, y0 - 0.04, y1 + 0.04, 0, 0.07, [0.15, 0.15, 0.16]);
  } else {                                             // letrero genérico sin texto (no se inventan negocios)
    const col = lin(['#b03a2e', '#1f618d', '#117a65', '#d4ac0d', '#6c3483', '#ca6f1e', '#f4f6f7', '#2e4053'][Math.floor(rnd() * 8)]);
    M.caja(G.pared, u0, u1, y0, y1, 0, 0.08, col);
    M.caja(G.pared, u0 + 0.12, u1 - 0.12, y0 + (y1 - y0) * 0.3, y0 + (y1 - y0) * 0.7, 0.08, 0.095, mezcla(col, [1, 1, 1], 0.7));
  }
}
const letrerosLuz = [];
function baranda(M, u0, u1, y0, alto, w, col, madera = false) {
  const Gm = madera ? G.madera : G.metal, t = madera ? 0.06 : 0.03;
  M.caja(Gm, u0, u1, y0 + alto - t, y0 + alto, w - t, w, col);
  M.caja(Gm, u0, u1, y0 + 0.08, y0 + 0.08 + t, w - t, w, col);
  const paso = madera ? 0.16 : 0.12;
  for (let u = u0; u <= u1 + 1e-3; u += paso) M.caja(Gm, u - t / 2, u + t / 2, y0, y0 + alto, w - t, w, col);
}
function fierros(Gm, x, y, z, ux, uz) {        // columna inconclusa con fierros de espera
  Gm.caja(x, y + 0.35, z, 0.25, 0.7, 0.25, ux, uz, [0.62, 0.61, 0.58]);
  const wx = -uz, wz = ux;
  for (const [a, b] of [[-0.08, -0.08], [0.08, -0.08], [0.08, 0.08], [-0.08, 0.08]]) {
    const px = x + ux * a + wx * b, pz = z + uz * a + wz * b;
    G.metal.tubo([px, y + 0.7, pz], [px + 0.02 * a * 10, y + 1.55, pz + 0.02 * b * 10], 0.008, [0.33, 0.2, 0.13], 3);
  }
}
function techoLosa(Gm, A, B, B2, A2, y, col) { Gm.quad([A[0], y, A[1]], [B[0], y, B[1]], [B2[0], y, B2[1]], [A2[0], y, A2[1]], ARRIBA, col, [[A[0] / 3, A[1] / 3], [B[0] / 3, B[1] / 3], [B2[0] / 3, B2[1] / 3], [A2[0] / 3, A2[1] / 3]]); }
function muroPlano(Gm, a, b, y0, y1, nOut, col, esc = 0.5) {
  const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
  Gm.quad([a[0], y0, a[1]], [b[0], y0, b[1]], [b[0], y1, b[1]], [a[0], y1, a[1]], [nOut[0], 0, nOut[1]], col, [[0, y0 * esc], [L * esc, y0 * esc], [L * esc, y1 * esc], [0, y1 * esc]]);
}
function normalHacia(a, b, ref) {             // normal horizontal del segmento a->b que apunta lejos de ref
  const dx = b[0] - a[0], dz = b[1] - a[1], L = Math.hypot(dx, dz) || 1; let n = [-dz / L, dx / L];
  const m = [(a[0] + b[0]) / 2 - ref[0], (a[1] + b[1]) / 2 - ref[1]];
  if (n[0] * m[0] + n[1] * m[1] < 0) n = [-n[0], -n[1]]; return n;
}

// ---------------------------------------------------------------- un lote
function construirLote(l) {
  const rnd = azar(l.semilla), sg = l.lado;
  const e0 = enEje(l.s0), e1 = enEje(l.s1), em = enEje((l.s0 + l.s1) / 2);
  const fr0 = l.f[0] + l.ret, fr1 = l.f[1] + l.ret;
  const A = [e0.x + e0.nx * fr0 * sg, e0.z + e0.nz * fr0 * sg], B = [e1.x + e1.nx * fr1 * sg, e1.z + e1.nz * fr1 * sg];
  const A2 = [e0.x + e0.nx * (fr0 + l.D) * sg, e0.z + e0.nz * (fr0 + l.D) * sg], B2 = [e1.x + e1.nx * (fr1 + l.D) * sg, e1.z + e1.nz * (fr1 + l.D) * sg];
  const Wd = Math.hypot(B[0] - A[0], B[1] - A[1]); if (Wd < 2) return;
  const U = [(B[0] - A[0]) / Wd, (B[1] - A[1]) / Wd];
  let N = [-U[1], U[0]]; if (N[0] * (em.x - A[0]) + N[1] * (em.z - A[1]) < 0) N = [-N[0], -N[1]];
  const centro = [(A[0] + B[0] + A2[0] + B2[0]) / 4, (A[1] + B[1] + A2[1] + B2[1]) / 4];
  // niveles
  const fm = (l.f[0] + l.f[1]) / 2;
  const g = yVereda((l.s0 + l.s1) / 2, sg, fm) + 0.02;
  let gmin = Math.min(altura(A[0], A[1]), altura(B[0], B[1]), altura(A2[0], A2[1]), altura(B2[0], B2[1]), g);
  const base = gmin - 1.2;
  const adobe = l.tipo === 'adobe', ladr = l.tipo === 'ladrillo';
  const pisos = l.pisos;
  const hp = adobe ? 3.1 : cl((l.alto - (l.inconcluso ? 0.1 : 0.7)) / pisos, 2.55, 3.2);
  const hTecho = g + pisos * hp;                          // cara superior de la última losa / alero
  const parapeto = (l.techo === 'losa' && !l.inconcluso) ? 0.85 : (l.techo === 'calamina' ? 0.5 : 0);
  const hTop = hTecho + parapeto;
  const M = Marco(A, U, N, l.s0);
  const colPared = lin(l.pared), colZoc = lin(l.zocalo), colMad = lin(l.madera), colMet = lin(l.metal);
  const volado = l.volado && pisos >= 2 ? VOL : 0;
  const matMuro = ladr ? G.ladrillo : G.pared, colMuro = ladr ? [1, 1, 1] : colPared;
  const escMuro = ladr ? 1 : 0.25;
  // ---------- distribución de vanos
  const nb = Math.max(1, Math.round(Wd / (adobe ? 3.0 : 3.3))), wb = Wd / nb;
  const puertaEn = Math.floor(rnd() * nb);
  // ---------- primer piso
  const y0 = g, y1 = g + hp;
  const vanos0 = [];
  const esCom = l.uso === 'comercio';
  const conGaraje = !esCom && !adobe && wb >= 2.9 && rnd() < 0.3;
  for (let j = 0; j < nb; j++) {
    const u0 = j * wb, u1 = u0 + wb;
    if (adobe) {
      if (j === puertaEn) { const a = (u0 + u1) / 2 - 0.8, b = a + 1.6; vanos0.push([a, b, y0, y0 + 2.55, 'portón']); }
      else { const a = (u0 + u1) / 2 - 0.5, b = a + 1.0; vanos0.push([a, b, y0 + 0.75, y0 + 2.35, 'ventanaA']); }
    } else if (esCom && !(pisos >= 2 && nb >= 2 && j === puertaEn && rnd() < 0.7)) {
      vanos0.push([u0 + 0.22, u1 - 0.22, y0, y0 + Math.min(2.6, hp - 0.45), 'tienda']);
    } else if (j === puertaEn) {
      if (conGaraje) vanos0.push([(u0 + u1) / 2 - 1.3, (u0 + u1) / 2 + 1.3, y0, y0 + 2.4, 'garaje']);
      else vanos0.push([(u0 + u1) / 2 - 0.55, (u0 + u1) / 2 + 0.55, y0, y0 + 2.2, 'puerta']);
    } else {
      const a = (u0 + u1) / 2 - Math.min(0.75, wb / 2 - 0.4);
      vanos0.push([a, (u0 + u1) - a, y0 + 1.0, y0 + 2.2, 'ventana']);
    }
  }
  const colMuro0 = (ladr && l.mixto) ? colPared : colMuro, matMuro0 = (ladr && l.mixto) ? G.pared : matMuro;
  muroConVanos(M, matMuro0, 0, Wd, base, y1, 0, vanos0, colMuro0, (ladr && !l.mixto) ? 1 : 0.25);
  // zócalo (tramos entre vanos que llegan al piso)
  if (!ladr || l.mixto) {
    const cortes = vanos0.filter(v => v[2] <= y0 + 0.01).map(v => [v[0], v[1]]).sort((a, b) => a[0] - b[0]);
    let u = 0;
    for (const [a, b] of [...cortes, [Wd, Wd]]) { if (a - u > 0.05) M.caja(G.pared, u, a, base + 1, y0 + 0.9, 0, 0.025, colZoc); u = b; }
  }
  for (const v of vanos0) {
    const [a, b, ya, yb, tipo] = v;
    if (tipo === 'tienda') tienda(M, a, b, ya, yb, rnd() < 0.55 ? 1 : (rnd() < 0.5 ? 2 : 0), colMet, rnd);
    else if (tipo === 'puerta') puerta(M, a, b, ya, yb, rnd() < 0.5 ? colMad : colMet, rnd() < 0.5 ? 'madera' : 'metal');
    else if (tipo === 'portón') { puerta(M, a, b, ya, yb, colMad, 'madera'); M.caja(G.madera, a - 0.12, b + 0.12, yb, yb + 0.15, 0, 0.08, colMad); }
    else if (tipo === 'garaje') { M.derrame(G.pared, a, b, ya, yb, 0.1, [0.8, 0.78, 0.74]); M.rect(G.persiana, a, b, ya, yb, -0.1, colMet, 0.5); }
    else if (tipo === 'ventana') ventana(M, a, b, ya, yb, rnd() < 0.5 ? MARCO_AL : MARCO_NEG, rnd() < 0.3 ? 0.8 : 0, true, rnd);
    else if (tipo === 'ventanaA') ventana(M, a, b, ya, yb, null, rnd() < 0.3 ? 0.7 : 0, true, rnd, colMad);
  }
  // letrero comercial
  if (esCom && !adobe) {
    const ts = vanos0.filter(v => v[4] === 'tienda');
    if (ts.length) {
      const a = Math.min(...ts.map(v => v[0])) + 0.05, b = Math.max(...ts.map(v => v[1])) - 0.05, yb = Math.max(...ts.map(v => v[3]));
      if (b - a > 1.2 && y1 - (yb + 0.42) > 0.35) letrero(M, a, b, yb + 0.4, Math.min(y1 - 0.08, yb + 1.05), l, rnd);
    }
  } else if (esCom && adobe && l.nombre) letrero(M, 0.3, Math.min(Wd - 0.3, 4.5), y0 + 2.7, y0 + 3.0, l, rnd);
  // ---------- pisos superiores
  for (let k = 1; k < pisos; k++) {
    const ya = g + k * hp, yb = ya + hp, w = volado;
    const vanos = [];
    for (let j = 0; j < nb; j++) {
      const u0 = j * wb, u1 = u0 + wb;
      const conBalcon = l.balcon && (j === Math.floor(nb / 2)) && (k === 1 || rnd() < 0.5);
      if (adobe) {
        const a = (u0 + u1) / 2 - 0.55;
        vanos.push(l.balcon ? [a, a + 1.1, ya + 0.05, ya + 2.25, 'puertaB'] : [a, a + 1.1, ya + 0.75, ya + 2.2, 'ventanaA']);
      } else if (conBalcon) {
        const a = (u0 + u1) / 2 - 0.7; vanos.push([a, a + 1.4, ya + 0.05, ya + 2.25, 'balcon']);
      } else {
        const a = (u0 + u1) / 2 - Math.min(0.9, wb / 2 - 0.45);
        vanos.push([a, (u0 + u1) - a, ya + 0.95, ya + Math.min(2.25, hp - 0.35), 'ventana']);
      }
    }
    // muro del piso (con volado, desplazado hacia la calle)
    const Mv = w > 0 ? Marco([A[0] + N[0] * w, A[1] + N[1] * w], U, N, l.s0) : M;
    muroConVanos(Mv, matMuro, 0, Wd, ya, yb, 0, vanos, colMuro, escMuro);
    for (const v of vanos) {
      const [a, b, yA, yB, tipo] = v;
      if (tipo === 'ventana') ventana(Mv, a, b, yA, yB, rnd() < 0.55 ? MARCO_AL : MARCO_NEG, rnd() < 0.3 ? 0.55 + 0.45 * rnd() : 0, false, rnd);
      else if (tipo === 'ventanaA') ventana(Mv, a, b, yA, yB, null, rnd() < 0.3 ? 0.7 : 0, false, rnd, colMad);
      else if (tipo === 'balcon') {
        puerta(Mv, a, b, yA, yB, [0.3, 0.33, 0.36], 'metal');
        Mv.rect(G.vidrio, a + 0.08, b - 0.08, yA + 1.0, yB - 0.1, -0.11, [0.36, 0.42, 0.48], 0.5, rnd() < 0.3 ? 0.7 : 0);
        Mv.caja(G.concreto, a - 0.35, b + 0.35, ya - 0.12, ya + 0.03, 0, 0.75, [0.8, 0.79, 0.76]);
        baranda(Mv, a - 0.33, b + 0.33, ya + 0.03, 1.0, 0.73, [0.12, 0.12, 0.13]);
      } else if (tipo === 'puertaB') puerta(Mv, a, b, yA, yB, colMad, 'madera');
    }
    if (adobe && l.balcon && k === 1) {                  // balcón de madera corrido (tipología tradicional)
      const a = Math.max(0.3, Wd * 0.12), b = Math.min(Wd - 0.3, Wd * 0.88);
      M.caja(G.madera, a, b, ya - 0.1, ya + 0.06, 0, 0.85, colMad);
      baranda(M, a, b, ya + 0.06, 0.95, 0.83, colMad, true);
      for (const u of [a + 0.05, b - 0.05]) M.caja(G.madera, u - 0.05, u + 0.05, ya + 0.06, ya + 2.35, 0.78, 0.86, colMad);
      M.caja(G.madera, a - 0.05, b + 0.05, ya + 2.35, ya + 2.45, 0.0, 0.9, colMad);
      for (let u = a + 0.3; u < b; u += 0.5) M.caja(G.madera, u - 0.03, u + 0.03, ya - 0.28, ya - 0.1, 0.05, 0.75, mezcla(colMad, [0, 0, 0], 0.2));   // canecillos
    }
    if (w > 0) {      // losa del volado: canto y fondo
      M.caja(G.concreto, 0, Wd, ya - 0.2, ya, 0, w + 0.03, ladr ? GRIS_VIGA : mezcla(colPared, [1, 1, 1], 0.35));
      if (k === 1) for (const [u, n] of [[0, [-U[0], 0, -U[1]]], [Wd, [U[0], 0, U[1]]]]) {
        const p0 = M.P(u, ya, 0), p1 = M.P(u, ya, w), p2 = M.P(u, hTecho, w), p3 = M.P(u, hTecho, 0);
        matMuro.quad(p0, p1, p2, p3, n, colMuro);
      }
    }
  }
  // ---------- columnas y vigas (ladrillo caravista: pórticos de concreto a la vista)
  if (ladr) {
    for (let k = 1; k <= pisos; k++) {
      const yv = g + k * hp, w = (k >= 2 || (k === 1 && pisos > 1)) ? volado : 0;
      const Mv = w > 0 ? Marco([A[0] + N[0] * w, A[1] + N[1] * w], U, N, l.s0) : M;
      Mv.caja(G.concreto, 0, Wd, yv - 0.25, yv, 0, 0.03, GRIS_VIGA);
    }
    const colU = [0, Wd]; for (let j = 2; j < nb; j += 2) colU.push(j * wb);
    for (const u of colU) {
      const a = cl(u - 0.13, 0, Wd - 0.26), b = a + 0.26;
      M.caja(G.concreto, a, b, base + 1, g + hp, 0, 0.03, GRIS_VIGA);
      if (pisos > 1) { const Mv = volado > 0 ? Marco([A[0] + N[0] * volado, A[1] + N[1] * volado], U, N, l.s0) : M; Mv.caja(G.concreto, a, b, g + hp, hTecho, 0, 0.03, GRIS_VIGA); }
    }
  } else if (!adobe) {                                   // cornisas / bandas de piso
    for (let k = 1; k <= pisos; k++) {
      const yv = g + k * hp, w = (k >= 2 || (k === 1 && pisos > 1)) ? volado : 0;
      const Mv = w > 0 ? Marco([A[0] + N[0] * w, A[1] + N[1] * w], U, N, l.s0) : M;
      Mv.caja(G.pared, 0, Wd, yv - 0.18, yv, 0, 0.04, mezcla(colPared, [1, 1, 1], 0.45));
    }
  }
  // ---------- muros laterales y posterior del volumen frontal
  const nA = normalHacia(A, A2, centro), nB = normalHacia(B, B2, centro), nR = normalHacia(A2, B2, centro);
  const colLat = adobe ? lin('#cdb79a') : [1, 1, 1], matLat = adobe ? G.pared : G.ladrillo, escLat = adobe ? 0.5 : 1;
  const topLat = adobe ? hTecho : hTop;
  for (const [p, q, n, esq] of [[A, A2, nA, l.esq[0]], [B, B2, nB, l.esq[1]]]) {
    if (esq && !adobe) {                          // esquina: fachada lateral con ventanas
      const L2 = Math.hypot(q[0] - p[0], q[1] - p[1]), U2 = [(q[0] - p[0]) / L2, (q[1] - p[1]) / L2];
      const M2 = Marco(p, U2, n, 0), nv = Math.max(1, Math.floor((L2 - 1) / 3.4));
      for (let k = 0; k < pisos; k++) {
        const ya = g + k * hp, vs = [];
        for (let j = 0; j < nv; j++) { const um = 1.2 + (j + 0.5) * (L2 - 2) / nv; vs.push([um - 0.6, um + 0.6, ya + 1.0, ya + 2.2]); }
        muroConVanos(M2, k === 0 && l.mixto ? G.pared : matMuro, 0, L2, k === 0 ? base : ya, ya + hp, 0, vs, k === 0 && l.mixto ? colPared : colMuro, escMuro);
        for (const v of vs) ventana(M2, v[0], v[1], v[2], v[3], MARCO_AL, rnd() < 0.3 ? 0.7 : 0, k === 0, rnd);
      }
      if (hTop > hTecho) M2.rect(matMuro, 0, L2, hTecho, hTop, 0, colMuro, escMuro);
    } else muroPlano(matLat, p, q, base, topLat, n, colLat, escLat);
  }
  muroPlano(matLat, A2, B2, base, topLat, nR, colLat, escLat);
  if (parapeto > 0 || l.inconcluso) { if (hTop > hTecho) M.rect(matMuro, 0, Wd, hTecho, hTop, volado, colMuro, escMuro); }
  // ---------- techo
  const Av = volado ? [A[0] + N[0] * volado, A[1] + N[1] * volado] : A, Bv = volado ? [B[0] + N[0] * volado, B[1] + N[1] * volado] : B;
  if (l.techo === 'teja') {
    const alero = 0.65, prof = Math.hypot(A2[0] - A[0], A2[1] - A[1]);
    const cum = hTecho + Math.min(2.4, prof * 0.5 * 0.4);
    const Ae = [A[0] + N[0] * alero - U[0] * 0.25, A[1] + N[1] * alero - U[1] * 0.25], Be = [B[0] + N[0] * alero + U[0] * 0.25, B[1] + N[1] * alero + U[1] * 0.25];
    const Ra = [(A[0] + A2[0]) / 2, (A[1] + A2[1]) / 2], Rb = [(B[0] + B2[0]) / 2, (B[1] + B2[1]) / 2];
    const A2e = [A2[0] - U[0] * 0.25 - N[0] * 0.3, A2[1] - U[1] * 0.25 - N[1] * 0.3], B2e = [B2[0] + U[0] * 0.25 - N[0] * 0.3, B2[1] + U[1] * 0.25 - N[1] * 0.3];
    const yAl = hTecho - alero * 0.4;
    const uvT = (p) => [(p[0] * U[0] + p[1] * U[1]) / 1.5, (p[0] * N[0] + p[1] * N[1]) / 1.5];
    const T = (p, y) => [p[0], y, p[1]];
    const nf = [N[0] * 0.37, 0.93, N[1] * 0.37], nb_ = [-N[0] * 0.37, 0.93, -N[1] * 0.37];
    G.teja.quad(T(Ae, yAl), T(Be, yAl), T(Rb, cum), T(Ra, cum), nf, [1, 1, 1], [uvT(Ae), uvT(Be), uvT(Rb), uvT(Ra)]);
    G.teja.quad(T(Ra, cum), T(Rb, cum), T(B2e, yAl), T(A2e, yAl), nb_, [0.92, 0.92, 0.92], [uvT(Ra), uvT(Rb), uvT(B2e), uvT(A2e)]);
    // hastiales
    G.pared.tri(T(A, hTecho), T(A2, hTecho), T(Ra, cum - 0.05), [nA[0], 0, nA[1]], colLat);
    G.pared.tri(T(B, hTecho), T(B2, hTecho), T(Rb, cum - 0.05), [nB[0], 0, nB[1]], colLat);
    // canecillos bajo el alero
    for (let u = 0.3; u < Wd - 0.2; u += 0.6) M.caja(G.madera, u - 0.04, u + 0.04, hTecho - 0.32, hTecho - 0.2, 0, alero, colMad);
    G.madera.quad(T(Ae, yAl - 0.04), T(Be, yAl - 0.04), T(B, hTecho - 0.04), T(A, hTecho - 0.04), [0, -1, 0], mezcla(colMad, [0, 0, 0], 0.2));
    M.rect(G.pared, 0, Wd, hTecho - 0.05, hTecho + 0.3, 0.001, colPared);
  } else if (l.techo === 'calamina') {
    const yf = hTecho + 0.35, yb = hTecho + 0.05;
    const uvC = (p) => [(p[0] * U[0] + p[1] * U[1]) / 1.0, (p[0] * N[0] + p[1] * N[1]) / 1.0];
    G.calamina.quad([A[0], yf, A[1]], [B[0], yf, B[1]], [B2[0], yb, B2[1]], [A2[0], yb, A2[1]], ARRIBA, rnd() < 0.5 ? [1, 1, 1] : [0.85, 0.72, 0.62], [uvC(A), uvC(B), uvC(B2), uvC(A2)]);
    M.rect(matMuro, 0, Wd, hTecho, hTop + 0.1, 0, colMuro, escMuro);
  } else {
    techoLosa(G.concreto, Av, Bv, B2, A2, hTecho, [0.66, 0.65, 0.62]);
    if (!l.inconcluso) {                                // parapeto: caras interiores y remate
      const inset = 0.15;
      const ring = [Av, Bv, B2, A2];
      for (let k = 0; k < 4; k++) {
        const p = ring[k], q = ring[(k + 1) % 4];
        const nIn = normalHacia(p, q, centro).map(v => -v);
        const pi = [p[0] + nIn[0] * inset, p[1] + nIn[1] * inset], qi = [q[0] + nIn[0] * inset, q[1] + nIn[1] * inset];
        muroPlano(G.pared, pi, qi, hTecho, hTop, nIn, mezcla(colPared, [0.7, 0.7, 0.7], ladr ? 0.6 : 0.2));
        G.concreto.quad([p[0], hTop, p[1]], [q[0], hTop, q[1]], [qi[0], hTop, qi[1]], [pi[0], hTop, pi[1]], ARRIBA, [0.8, 0.79, 0.76]);
      }
    } else {                                            // obra en curso: columnas con fierros
      const cs = [Av, Bv, A2, B2];
      for (let j = 2; j < nb; j += 2) cs.push([Av[0] + U[0] * j * wb, Av[1] + U[1] * j * wb]);
      for (const p of cs) {
        const q = [p[0] + (centro[0] - p[0]) * 0.04, p[1] + (centro[1] - p[1]) * 0.04];
        fierros(G.concreto, q[0], hTecho, q[1], U[0], U[1]);
      }
      if (rnd() < 0.5) {                                // muro a medio levantar
        const a = 0.3, b = Math.min(Wd - 0.3, a + Wd * (0.3 + 0.4 * rnd()));
        const Mv = volado ? Marco(Av, U, N, l.s0) : M;
        Mv.caja(G.ladrillo, a, b, hTecho, hTecho + 0.6 + rnd() * 1.2, -0.13, 0, [1, 1, 1], 1);
      }
    }
    // tanques de agua (Rotoplas) y cuarto de azotea
    if (l.tanque) {
      const t = 0.3 + 0.4 * rnd(), q = [Av[0] + (B2[0] - Av[0]) * (0.55 + 0.25 * rnd()) , Av[1] + (B2[1] - Av[1]) * (0.55 + 0.25 * rnd())];
      tanques2.push(q[0], hTecho, q[1], rnd() < 0.72 ? 0 : (rnd() < 0.5 ? 1 : 2));
      if (rnd() < 0.35) { const r2 = [q[0] + U[0] * 1.3, q[1] + U[1] * 1.3]; tanques2.push(r2[0], hTecho, r2[1], 0); }
    }
    if (!l.inconcluso && rnd() < 0.3 && Wd > 6) {
      const c = [(A2[0] + B2[0]) / 2 + N[0] * 2.2, (A2[1] + B2[1]) / 2 + N[1] * 2.2];
      G.pared.caja(c[0], hTecho + 1.15, c[1], 2.6, 2.3, 2.4, U[0], U[1], mezcla(colPared, [0.8, 0.8, 0.8], 0.3), 0.5);
    }
  }
  // ---------- volumen posterior (patio techado / ampliaciones)
  if (l.hb && l.Dt > l.D + 1) {
    const A3 = [e0.x + e0.nx * (fr0 + l.Dt) * sg, e0.z + e0.nz * (fr0 + l.Dt) * sg], B3 = [e1.x + e1.nx * (fr1 + l.Dt) * sg, e1.z + e1.nz * (fr1 + l.Dt) * sg];
    const hb = Math.max(2.6, Math.min(l.hb, 18)), yT = g + hb;
    const c2 = [(A2[0] + B2[0] + A3[0] + B3[0]) / 4, (A2[1] + B2[1] + A3[1] + B3[1]) / 4];
    for (const [p, q] of [[A2, A3], [A3, B3], [B3, B2], [B2, A2]]) muroPlano(adobe ? G.pared : G.ladrillo, p, q, base, yT, normalHacia(p, q, c2), adobe ? lin('#cdb79a') : [1, 1, 1], adobe ? 0.5 : 1);
    if (adobe || rnd() < 0.35) G.calamina.quad([A2[0], yT + 0.2, A2[1]], [B2[0], yT + 0.2, B2[1]], [B3[0], yT, B3[1]], [A3[0], yT, A3[1]], ARRIBA, [0.85, 0.75, 0.66]);
    else techoLosa(G.concreto, A2, B2, B3, A3, yT, [0.62, 0.61, 0.58]);
  }
  // ---------- retiro frontal: cerco con reja y jardín
  if (l.ret > 0) {
    const P0 = enLado(l.s0, l.f[0], sg), P1 = enLado(l.s1, l.f[1], sg);
    const L2 = Math.hypot(P1[0] - P0[0], P1[1] - P0[1]), U2 = [(P1[0] - P0[0]) / L2, (P1[1] - P0[1]) / L2];
    const M2 = Marco(P0, U2, N, l.s0);
    M2.caja(G.pared, 0, L2, base + 1, g + 0.9, -0.15, 0, colPared);
    baranda(M2, 0, L2 * 0.4, g + 0.9, 1.3, -0.04, [0.1, 0.1, 0.1]); baranda(M2, L2 * 0.4 + 2.2, L2, g + 0.9, 1.3, -0.04, [0.1, 0.1, 0.1]);
    M2.caja(G.metal, L2 * 0.4, L2 * 0.4 + 2.2, g, g + 2.1, -0.08, -0.03, colMet);
    G.cesped.quad([P0[0], g - 0.05, P0[1]], [P1[0], g - 0.05, P1[1]], [B[0], g - 0.05, B[1]], [A[0], g - 0.05, A[1]], ARRIBA, [0.9, 0.95, 0.85],
      [[0, 0], [L2 / 3, 0], [L2 / 3, l.ret / 3], [0, l.ret / 3]]);
  }
  // ---------- volumen para selección
  const id = l.id;
  const pk = (p, y) => [p[0], y, p[1]];
  for (const [p, q] of [[A, B], [B, B2], [B2, A2], [A2, A]]) cajasPick.quad(pk(p, base), pk(q, base), pk(q, hTop + 0.5), pk(p, hTop + 0.5), [0, 0, 1], BLANCO, null, 0, id);
  cajasPick.quad(pk(A, hTop + 0.5), pk(B, hTop + 0.5), pk(B2, hTop + 0.5), pk(A2, hTop + 0.5), ARRIBA, BLANCO, null, 0, id);
  l._centro = [(A[0] + B[0]) / 2 + N[0] * 3, g + Math.min(hTop - g, 8) * 0.6, (A[1] + B[1]) / 2 + N[1] * 3];
  l._A = A; l._B = B; l._g = g; l._top = hTop;
}
// ---------------------------------------------------------------- cercos de terrenos sin edificar o patios
function construirCerco(c) {
  const rnd = azar(Math.round(c.s0 * 97) + (c.lado > 0 ? 1 : 2));
  const sg = c.lado, P0 = enLado(c.s0, c.f[0], sg), P1 = enLado(c.s1, c.f[1], sg);
  const L2 = Math.hypot(P1[0] - P0[0], P1[1] - P0[1]); if (L2 < 1) return;
  const U2 = [(P1[0] - P0[0]) / L2, (P1[1] - P0[1]) / L2], em = enEje((c.s0 + c.s1) / 2);
  let N = [-U2[1], U2[0]]; if (N[0] * (em.x - P0[0]) + N[1] * (em.z - P0[1]) < 0) N = [-N[0], -N[1]];
  const M = Marco(P0, U2, N, c.s0);
  const g = yVereda((c.s0 + c.s1) / 2, sg, (c.f[0] + c.f[1]) / 2), base = Math.min(g, altura(P0[0], P0[1]), altura(P1[0], P1[1])) - 1;
  const h = g + c.alto, col = c.ladrillo ? [1, 1, 1] : lin(c.color), Gm = c.ladrillo ? G.ladrillo : G.pared, esc = c.ladrillo ? 1 : 0.5;
  const vanos = [];
  if (L2 > 4.2) { const a = L2 * (0.2 + 0.5 * rnd()), b = Math.min(L2 - 0.4, a + (c.porton === 'madera' ? 1.6 : 3.0)); vanos.push([a, b, g, g + 2.3]); }
  muroConVanos(M, Gm, 0, L2, base, h, 0, vanos, col, esc);
  // cara posterior, cabezas del muro y remate
  Gm.quad(M.P(0, base, -0.2), M.P(L2, base, -0.2), M.P(L2, h, -0.2), M.P(0, h, -0.2), [-N[0], 0, -N[1]], col, [[0, base * esc], [L2 * esc, base * esc], [L2 * esc, h * esc], [0, h * esc]]);
  for (const [u, n] of [[0, [-U2[0], 0, -U2[1]]], [L2, [U2[0], 0, U2[1]]]]) Gm.quad(M.P(u, base, 0), M.P(u, base, -0.2), M.P(u, h, -0.2), M.P(u, h, 0), n, col);
  M.caja(G.concreto, -0.02, L2 + 0.02, h, h + 0.08, -0.22, 0.03, [0.82, 0.81, 0.78]);
  for (let u = 0; u <= L2 + 0.01; u += 3.2) M.caja(G.concreto, cl(u - 0.14, 0, L2 - 0.28), cl(u + 0.14, 0.28, L2), base + 1, h + 0.12, -0.22, 0.04, c.ladrillo ? GRIS_VIGA : mezcla(col, [1, 1, 1], 0.3));
  for (const v of vanos) {
    const [a, b, ya, yb] = v;
    if (c.porton === 'reja') { baranda(M, a, b, ya, yb - ya, -0.08, [0.12, 0.12, 0.12]); }
    else if (c.porton === 'madera') puerta(M, a, b, ya, yb, [0.4, 0.27, 0.16], 'madera');
    else { M.rect(G.persiana, a, b, ya, yb, -0.1, lin(['#3d5c45', '#4a6b8a', '#7b2e2e', '#2b2d30'][Math.floor(rnd() * 4)]), 0.5); }
  }
  if (c.porton === 'reja') { const a = vanos[0]; if (a) G.cesped.quad(M.P(a[0], g - 0.03, -0.2), M.P(a[1], g - 0.03, -0.2), M.P(a[1], g - 0.03, -6), M.P(a[0], g - 0.03, -6), ARRIBA, [0.8, 0.85, 0.7], [[0, 0], [1, 0], [1, 2], [0, 2]]); }
}
for (const l of CH.lotes) construirLote(l);
for (const c of CH.cercos) construirCerco(c);
// ---------------------------------------------------------------- tanques de agua (instancias)
{
  const n = tanques2.length / 4;
  const geo = new THREE.CylinderGeometry(0.55, 0.6, 1.25, 14).translate(0, 0.625, 0);
  const tapa = new THREE.CylinderGeometry(0.3, 0.3, 0.12, 12).translate(0, 1.31, 0);
  const geoT = mergeGeos([geo.toNonIndexed(), tapa.toNonIndexed()]);
  const it = new THREE.InstancedMesh(geoT, matStd({ vertexColors: true, roughness: 0.55, envMapIntensity: 0.5 }), n);
  const m4 = new THREE.Matrix4(), c = new THREE.Color();
  for (let i = 0; i < n; i++) {
    m4.makeTranslation(tanques2[i * 4], tanques2[i * 4 + 1], tanques2[i * 4 + 2]); it.setMatrixAt(i, m4);
    it.setColorAt(i, c.set([0x1c1d1f, 0x2d5f9a, 0xd9cfb8][tanques2[i * 4 + 3]]));
  }
  it.castShadow = it.receiveShadow = true; grupoDetalle.add(it);
}
