// ================================================================ utilidades de geometría para fachadas y muros de los hitos
// (extraídas del módulo de lotes del corredor; los hitos dibujan sobre los conjuntos H_)
function lin(h, f = 1) { return rgbLin(h, f); }
function mezcla(a, b, t) { return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
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
function puerta(M, u0, u1, y0, y1, col, mat = 'madera') {
  const G = H_;
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
function muroPlano(Gm, a, b, y0, y1, nOut, col, esc = 0.5) {
  const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
  Gm.quad([a[0], y0, a[1]], [b[0], y0, b[1]], [b[0], y1, b[1]], [a[0], y1, a[1]], [nOut[0], 0, nOut[1]], col, [[0, y0 * esc], [L * esc, y0 * esc], [L * esc, y1 * esc], [0, y1 * esc]]);
}
function normalHacia(a, b, ref) {             // normal horizontal del segmento a->b que apunta lejos de ref
  const dx = b[0] - a[0], dz = b[1] - a[1], L = Math.hypot(dx, dz) || 1; let n = [-dz / L, dx / L];
  const m = [(a[0] + b[0]) / 2 - ref[0], (a[1] + b[1]) / 2 - ref[1]];
  if (n[0] * m[0] + n[1] * m[1] < 0) n = [-n[0], -n[1]]; return n;
}
