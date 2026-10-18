// ================================================================ HITOS REMASTERIZADOS: Plaza de Armas, Catedral Santa Ana, Estadio Unión Tarma
const grupoHitos = new THREE.Group(); grupoHitos.name = 'Hitos'; escena.add(grupoHitos);
const H_ = {}; for (const k of ['pared', 'concreto', 'teja', 'metal', 'madera', 'cesped', 'adoquin', 'tartan', 'pintura', 'vidrio', 'foco', 'calamina']) H_[k] = new Geo();
function poligonoPlano(Gm, pts, y, col, esc = 0.5, dy = 0) {         // polígono horizontal triangulado (y fija o sobre el terreno)
  const v2 = pts.map(([x, z]) => new THREE.Vector2(x, z));
  if (THREE.ShapeUtils.isClockWise(v2)) v2.reverse();
  let caras; try { caras = THREE.ShapeUtils.triangulateShape(v2, []); } catch (e) { return; }
  const Y = (x, z) => (typeof y === 'number' ? y : altura(x, z) + dy);
  for (const [a, b, c] of caras) {
    const P = i => [v2[i].x, Y(v2[i].x, v2[i].y), v2[i].y], U = i => [v2[i].x * esc, v2[i].y * esc];
    Gm.tri(P(a), P(b), P(c), ARRIBA, col, [U(a), U(b), U(c)]);
  }
}
function muroContorno(Gm, pts, y0, y1, col, esc = 0.5, haciaFuera = true) {
  const v2 = pts.map(([x, z]) => [x, z]); let cx = 0, cz = 0; v2.forEach(p => { cx += p[0]; cz += p[1]; }); cx /= v2.length; cz /= v2.length;
  for (let k = 0; k < v2.length - 1; k++) {
    const a = v2[k], b = v2[k + 1]; if (Math.hypot(b[0] - a[0], b[1] - a[1]) < 0.05) continue;
    let n = normalHacia(a, b, [cx, cz]); if (!haciaFuera) n = [-n[0], -n[1]];
    muroPlano(Gm, a, b, typeof y0 === 'function' ? y0(a, b) : y0, y1, n, col, esc);
  }
}
// ---------------------------------------------------------------- Plaza de Armas
{
  const [pcx, pcz] = C.plaza_c, gP = altura(pcx, pcz) + 0.3;
  poligonoPlano(H_.adoquin, C.plaza, gP, [1, 0.97, 0.95], 0.5);
  muroContorno(H_.concreto, C.plaza, gP - 0.6, gP, [0.85, 0.83, 0.8]);
  const rnd = azar(77);
  const flores = [];
  for (const j of HI.jardines) {
    poligonoPlano(H_.cesped, j, gP + 0.12, [1, 1, 1], 0.4);
    muroContorno(H_.concreto, j, gP, gP + 0.14, [0.92, 0.9, 0.86]);
    // macizos de flores a lo largo del borde ("Tarma, ciudad de las flores")
    for (let k = 0; k < j.length - 1; k++) {
      const a = j[k], b = j[k + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      for (let t = 0.4; t < L - 0.3; t += 0.45) {
        const x = a[0] + (b[0] - a[0]) * t / L, z = a[1] + (b[1] - a[1]) * t / L;
        let cx = 0, cz = 0; j.forEach(p => { cx += p[0]; cz += p[1]; }); cx /= j.length; cz /= j.length;
        const d = Math.hypot(cx - x, cz - z) || 1, f = 0.55 / d;
        flores.push(x + (cx - x) * f, gP + 0.2, z + (cz - z) * f, Math.floor(rnd() * 5));
      }
    }
  }
  // flores (instancias)
  const nF = flores.length / 4, geoF = new THREE.IcosahedronGeometry(0.2, 0), it = new THREE.InstancedMesh(geoF, new THREE.MeshStandardMaterial({ roughness: 0.8 }), nF);
  const m4 = new THREE.Matrix4(), cF = new THREE.Color(), PAL = [0xd7263d, 0xf4d35e, 0xc2307a, 0xf8f4ec, 0xee6c2a];
  for (let i = 0; i < nF; i++) { m4.makeTranslation(flores[i * 4], flores[i * 4 + 1], flores[i * 4 + 2]); it.setMatrixAt(i, m4); it.setColorAt(i, cF.set(PAL[flores[i * 4 + 3]])); }
  it.castShadow = true; grupoHitos.add(it);
  // pileta central de dos tazas
  const piedra = [0.9, 0.87, 0.82];
  for (let k = 0; k < 8; k++) {
    const a0 = (k + 0.5) / 8 * Math.PI * 2, a1 = (k + 1.5) / 8 * Math.PI * 2, R = 4.6;
    const p0 = [pcx + R * Math.cos(a0), pcz + R * Math.sin(a0)], p1 = [pcx + R * Math.cos(a1), pcz + R * Math.sin(a1)];
    const n = [Math.cos((a0 + a1) / 2), Math.sin((a0 + a1) / 2)];
    muroPlano(H_.concreto, p0, p1, gP, gP + 0.65, n, piedra);
    const q0 = [pcx + (R - 0.4) * Math.cos(a0), pcz + (R - 0.4) * Math.sin(a0)], q1 = [pcx + (R - 0.4) * Math.cos(a1), pcz + (R - 0.4) * Math.sin(a1)];
    muroPlano(H_.concreto, q0, q1, gP, gP + 0.65, [-n[0], -n[1]], piedra);
    H_.concreto.quad([p0[0], gP + 0.65, p0[1]], [p1[0], gP + 0.65, p1[1]], [q1[0], gP + 0.65, q1[1]], [q0[0], gP + 0.65, q0[1]], ARRIBA, [0.95, 0.93, 0.9]);
  }
  H_.concreto.cilindro(pcx, gP, pcz, 0.75, 0.55, 1.6, 16, piedra);
  H_.concreto.cilindro(pcx, gP + 1.6, pcz, 0.6, 2.2, 0.45, 20, piedra);
  H_.concreto.cilindro(pcx, gP + 2.05, pcz, 0.3, 0.25, 1.3, 12, piedra);
  H_.concreto.cilindro(pcx, gP + 3.35, pcz, 0.3, 1.1, 0.3, 16, piedra);
  H_.concreto.cilindro(pcx, gP + 3.65, pcz, 0.18, 0.08, 0.7, 10, piedra);
  const aguaP = new THREE.Mesh(new THREE.CylinderGeometry(4.15, 4.15, 0.08, 40), new THREE.MeshStandardMaterial({ color: 0x4f87a3, roughness: 0.05, metalness: 0.1, envMapIntensity: 1.3 }));
  aguaP.position.set(pcx, gP + 0.5, pcz); grupoHitos.add(aguaP);
  // chorros (conos translúcidos animados)
  const matChorro = new THREE.MeshStandardMaterial({ color: 0xd8eef7, transparent: true, opacity: 0.45, roughness: 0.1, depthWrite: false });
  window.chorros = [];
  for (const [r, h, y] of [[1.9, 1.5, gP + 0.55], [1.0, 0.9, gP + 2.0]]) {
    const ch = new THREE.Mesh(new THREE.CylinderGeometry(r, r * 0.25, h, 24, 1, true), matChorro);
    ch.position.set(pcx, y + h / 2, pcz); grupoHitos.add(ch); chorros.push(ch);
  }
  // bancas y faroles coloniales a lo largo de los senderos
  const bancas = [], faroles = [];
  for (const s of HI.senderos) for (let k = 0; k < s.length - 1; k++) {
    const a = s[k], b = s[k + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L < 6) continue;
    const ux = (b[0] - a[0]) / L, uz = (b[1] - a[1]) / L;
    for (let t = 4; t < L - 3; t += 7) {
      for (const sg of [-1, 1]) bancas.push([a[0] + ux * t - uz * 1.6 * sg, a[1] + uz * t + ux * 1.6 * sg, Math.atan2(-uz, ux), sg]);
    }
    faroles.push([a[0] + ux * L / 2 + uz * 1.9, a[1] + uz * L / 2 - ux * 1.9]);
  }
  for (const p of C.plaza) faroles.push([p[0] + (pcx - p[0]) * 0.06, p[1] + (pcz - p[1]) * 0.06]);
  for (const [x, z, ang, sg] of bancas) {
    const ux = Math.cos(ang), uz = -Math.sin(ang), wx = -uz * sg, wz = ux * sg;
    H_.madera.caja(x, gP + 0.45, z, 1.8, 0.05, 0.45, ux, uz, [0.55, 0.36, 0.2]);
    H_.madera.caja(x + wx * 0.22, gP + 0.75, z + wz * 0.22, 1.8, 0.35, 0.05, ux, uz, [0.55, 0.36, 0.2]);
    for (const t of [-0.75, 0.75]) H_.metal.caja(x + ux * t, gP + 0.22, z + uz * t, 0.06, 0.45, 0.45, ux, uz, [0.08, 0.08, 0.08]);
  }
  for (const [x, z] of faroles) {
    H_.metal.cilindro(x, gP, z, 0.12, 0.07, 3.6, 8, [0.06, 0.06, 0.06]);
    H_.metal.caja(x, gP + 3.7, z, 0.9, 0.06, 0.06, 1, 0, [0.06, 0.06, 0.06]); H_.metal.caja(x, gP + 3.7, z, 0.06, 0.06, 0.9, 1, 0, [0.06, 0.06, 0.06]);
    for (const [dx, dz] of [[0.45, 0], [-0.45, 0], [0, 0.45], [0, -0.45]]) {
      H_.foco.caja(x + dx, gP + 3.98, z + dz, 0.22, 0.42, 0.22, 1, 0, [1, 0.95, 0.82], 1, false, 1.4);
      H_.metal.caja(x + dx, gP + 4.24, z + dz, 0.3, 0.08, 0.3, 1, 0, [0.06, 0.06, 0.06]);
    }
  }
  // árboles ornamentales en los jardines
  const arbP = [];
  for (const j of HI.jardines) { let cx = 0, cz = 0; j.forEach(p => { cx += p[0]; cz += p[1]; }); cx /= j.length; cz /= j.length; arbP.push([cx, cz]); }
  const copa = new THREE.IcosahedronGeometry(1, 2).scale(2.6, 2.3, 2.6), mCopa = new THREE.MeshStandardMaterial({ color: 0x4d7a3a, roughness: 0.95, flatShading: true });
  const iCopa = new THREE.InstancedMesh(copa, mCopa, arbP.length), iTr = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.16, 0.24, 1, 7).translate(0, 0.5, 0), matTronco, arbP.length);
  arbP.forEach(([x, z], i) => {
    const s = 0.9 + 0.3 * rnd();
    m4.compose(new THREE.Vector3(x, gP + 4.6 * s, z), new THREE.Quaternion(), new THREE.Vector3(s, s, s)); iCopa.setMatrixAt(i, m4);
    iCopa.setColorAt(i, cF.set([0x4d7a3a, 0x5b8a3c, 0x456f35, 0x7a5aa6][i % 4]));
    m4.compose(new THREE.Vector3(x, gP, z), new THREE.Quaternion(), new THREE.Vector3(1, 3.2 * s, 1)); iTr.setMatrixAt(i, m4);
  });
  iCopa.castShadow = iTr.castShadow = true; grupoHitos.add(iCopa, iTr);
}
// ---------------------------------------------------------------- Catedral Santa Ana (1954, neoclásica, planta de cruz latina, dos torres con reloj)
{
  const pol = HI.catedral;
  let gmin = Infinity; for (const [x, z] of pol) gmin = Math.min(gmin, altura(x, z));
  const g0 = gmin + 0.2, hMuro = 13.5;
  const blanco = lin('#f1e9d8'), gris = lin('#c9c2b4');
  muroContorno(H_.pared, pol, g0 - 2, g0 + hMuro, blanco, 0.5);
  muroContorno(H_.pared, pol, g0 - 2, g0 + 1.2, gris, 0.5);               // zócalo de piedra
  // cornisa
  for (let k = 0; k < pol.length - 1; k++) {
    const a = pol[k], b = pol[k + 1]; if (Math.hypot(b[0] - a[0], b[1] - a[1]) < 0.2) continue;
    let cx = 0, cz = 0; pol.forEach(p => { cx += p[0]; cz += p[1]; }); cx /= pol.length; cz /= pol.length;
    const n = normalHacia(a, b, [cx, cz]);
    H_.pared.quad([a[0] + n[0] * 0.35, g0 + hMuro - 0.4, a[1] + n[1] * 0.35], [b[0] + n[0] * 0.35, g0 + hMuro - 0.4, b[1] + n[1] * 0.35], [b[0] + n[0] * 0.35, g0 + hMuro, b[1] + n[1] * 0.35], [a[0] + n[0] * 0.35, g0 + hMuro, a[1] + n[1] * 0.35], [n[0], 0, n[1]], gris);
    H_.pared.quad([a[0], g0 + hMuro, a[1]], [b[0], g0 + hMuro, b[1]], [b[0] + n[0] * 0.35, g0 + hMuro, b[1] + n[1] * 0.35], [a[0] + n[0] * 0.35, g0 + hMuro, a[1] + n[1] * 0.35], ARRIBA, gris);
  }
  poligonoPlano(H_.concreto, pol, g0 + hMuro, [0.78, 0.76, 0.72], 0.3);
  // ventanales de la nave (arcos de medio punto simplificados)
  for (let k = 0; k < pol.length - 1; k++) {
    const a = pol[k], b = pol[k + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L < 6) continue;
    let cx = 0, cz = 0; pol.forEach(p => { cx += p[0]; cz += p[1]; }); cx /= pol.length; cz /= pol.length;
    const n = normalHacia(a, b, [cx, cz]), u = [(b[0] - a[0]) / L, (b[1] - a[1]) / L];
    const Mc = Marco(a, u, n, 0);
    for (let t = 3; t < L - 2; t += 4.5) { Mc.rect(H_.vidrio, t - 0.7, t + 0.7, g0 + 5, g0 + 9.5, 0.03, [0.32, 0.28, 0.4], 0.5, 0.6); Mc.caja(H_.pared, t - 0.9, t + 0.9, g0 + 9.5, g0 + 10.1, 0, 0.12, gris); }
  }
  // cubiertas a dos aguas: nave (E-O) y crucero (N-S)
  const ejeX0 = 486, ejeX1 = 531, zc = 910.2, ancho = 15, cumb = g0 + hMuro + 4.2;
  const tejaQ = (a, b, c, d, n) => H_.teja.quad(a, b, c, d, n, [0.95, 0.9, 0.88], [[a[0] / 1.5, a[2] / 1.5], [b[0] / 1.5, b[2] / 1.5], [c[0] / 1.5, c[2] / 1.5], [d[0] / 1.5, d[2] / 1.5]]);
  const yb = g0 + hMuro;
  tejaQ([ejeX0, yb, zc - ancho / 2], [ejeX1, yb, zc - ancho / 2], [ejeX1, cumb, zc], [ejeX0, cumb, zc], [0, 0.88, -0.47]);
  tejaQ([ejeX0, cumb, zc], [ejeX1, cumb, zc], [ejeX1, yb, zc + ancho / 2], [ejeX0, yb, zc + ancho / 2], [0, 0.88, 0.47]);
  const xc = 482.5, z0 = 888.5, z1 = 936.5, at = 12;
  tejaQ([xc - at / 2, yb, z0], [xc - at / 2, yb, z1], [xc, cumb, z1], [xc, cumb, z0], [-0.47, 0.88, 0]);
  tejaQ([xc, cumb, z0], [xc, cumb, z1], [xc + at / 2, yb, z1], [xc + at / 2, yb, z0], [0.47, 0.88, 0]);
  for (const [x, z, n] of [[ejeX1, zc, [1, 0, 0]], [ejeX0, zc, [-1, 0, 0]]]) H_.pared.tri([x, yb, z - ancho / 2], [x, yb, z + ancho / 2], [x, cumb, z], n, blanco);
  for (const [z, n] of [[z0, [0, 0, -1]], [z1, [0, 0, 1]]]) H_.pared.tri([xc - at / 2, yb, z], [xc + at / 2, yb, z], [xc, cumb, z], n, blanco);
  // cúpula sobre el crucero
  {
    const yD = cumb - 1, R = 5.2;
    H_.pared.cilindro(xc, yD, zc, R, R, 4.2, 24, blanco, false);
    for (let k = 0; k < 12; k++) {         // ventanas del tambor
      const a = k / 12 * Math.PI * 2, x = xc + Math.cos(a) * (R + 0.02), z = zc + Math.sin(a) * (R + 0.02);
      H_.vidrio.caja(x, yD + 2.1, z, 0.9, 1.9, 0.05, -Math.sin(a), Math.cos(a), [0.3, 0.27, 0.36], 1, false, 0.6);
    }
    const domo = new THREE.SphereGeometry(R + 0.2, 28, 12, 0, Math.PI * 2, 0, Math.PI / 2);
    const mDomo = new THREE.Mesh(domo, new THREE.MeshStandardMaterial({ color: 0xb9c3c7, roughness: 0.45, metalness: 0.35 }));
    mDomo.position.set(xc, yD + 4.2, zc); mDomo.castShadow = true; grupoHitos.add(mDomo);
    H_.pared.cilindro(xc, yD + 4.2 + R, zc, 1.0, 1.0, 1.8, 12, blanco);
    H_.metal.cilindro(xc, yD + 6 + R, zc, 1.1, 0.05, 1.2, 12, [0.6, 0.64, 0.66]);
    H_.metal.caja(xc, yD + 8 + R, zc, 0.12, 1.6, 0.12, 1, 0, [0.15, 0.15, 0.15]); H_.metal.caja(xc, yD + 8.4 + R, zc, 0.12, 0.12, 0.8, 1, 0, [0.15, 0.15, 0.15]);
  }
  // fachada hacia la plaza con frontón, tres portadas y rosetón
  const [t1, t2] = C.torres, zA = Math.min(t1[1], t2[1]) + 3.2, zB = Math.max(t1[1], t2[1]) - 3.2;
  let fx = -Infinity; for (const [x, z] of pol) if (z > zA - 9 && z < zB + 9) fx = Math.max(fx, x);    // borde de la huella hacia la plaza
  fx += 0.06;
  const torresF = C.torres.map(([x, z]) => [fx - 3.05, z]);         // torres alineadas con la fachada
  const Mf = Marco([fx, zB], [0, -1], [1, 0], 0), Lf = zB - zA, yF = g0 + 17;
  muroConVanos(Mf, H_.pared, 0, Lf, g0 - 1, yF, 0, [[Lf / 2 - 1.3, Lf / 2 + 1.3, g0, g0 + 5.2]], blanco, 0.5);   // con el vano de la portada
  H_.pared.tri(Mf.P(0, yF, 0.02), Mf.P(Lf, yF, 0.02), Mf.P(Lf / 2, yF + 4, 0.02), [1, 0, 0], blanco);
  Mf.caja(H_.pared, -0.2, Lf + 0.2, yF - 0.2, yF + 0.25, 0, 0.45, gris);
  for (const u of [0.4, Lf / 2 - 2.2, Lf / 2 + 2.2, Lf - 0.4]) Mf.caja(H_.pared, u - 0.35, u + 0.35, g0, yF - 0.2, 0, 0.3, gris);     // pilastras
  puerta(Mf, Lf / 2 - 1.3, Lf / 2 + 1.3, g0, g0 + 5.2, lin('#4a2f1d'), 'madera');
  Mf.caja(H_.pared, Lf / 2 - 1.7, Lf / 2 + 1.7, g0 + 5.2, g0 + 5.8, 0, 0.3, gris);
  const roset = new THREE.Mesh(new THREE.CircleGeometry(1.4, 28), MAT.vidrio); roset.geometry.setAttribute('aLuz', new THREE.Float32BufferAttribute(new Array(roset.geometry.attributes.position.count).fill(0.7), 1));
  roset.geometry.setAttribute('color', new THREE.Float32BufferAttribute(new Array(roset.geometry.attributes.position.count * 3).fill(0.35), 3));
  roset.position.copy(new THREE.Vector3(...Mf.P(Lf / 2, g0 + 9.5, 0.06))); roset.lookAt(roset.position.x + 1, roset.position.y, roset.position.z); grupoHitos.add(roset);
  // torres: cuerpo, cornisas, relojes, campanario con arcos, cupulín, linterna y cruz
  const texReloj = lienzoTex(256, 256, (g, w, h) => {
    g.fillStyle = '#f5f2e8'; g.beginPath(); g.arc(128, 128, 124, 0, 7); g.fill(); g.strokeStyle = '#1d1d1d'; g.lineWidth = 8; g.stroke();
    g.fillStyle = '#1d1d1d'; for (let k = 0; k < 12; k++) { const a = k / 12 * Math.PI * 2; g.fillRect(128 + Math.cos(a) * 100 - 5, 128 + Math.sin(a) * 100 - 5, 10, 10); }
    g.lineWidth = 9; g.beginPath(); g.moveTo(128, 128); g.lineTo(128, 52); g.stroke(); g.lineWidth = 7; g.beginPath(); g.moveTo(128, 128); g.lineTo(186, 150); g.stroke();
  });
  const mReloj = new THREE.MeshStandardMaterial({ map: texReloj, roughness: 0.5, transparent: true, alphaTest: 0.5, emissive: 0xfff2d0, emissiveMap: texReloj, emissiveIntensity: 0 });
  letrerosLuz.push(mReloj);
  for (const [tx, tz] of torresF) {
    const g1 = altura(tx, tz) + 0.2, S = 6.6;
    H_.pared.caja(tx, g1 + 11, tz, S, 24, S, 1, 0, blanco, 0.5);
    for (const y of [g1 + 8, g1 + 16, g1 + 23.6]) H_.pared.caja(tx, y, tz, S + 0.5, 0.45, S + 0.5, 1, 0, gris, 0.5);
    for (const [nx, nz] of [[1, 0], [0, 1], [0, -1], [-1, 0]]) {
      const r = new THREE.Mesh(new THREE.CircleGeometry(1.15, 32), mReloj);
      r.position.set(tx + nx * (S / 2 + 0.03), g1 + 19.6, tz + nz * (S / 2 + 0.03)); r.lookAt(r.position.x + nx, r.position.y, r.position.z + nz); grupoHitos.add(r);
    }
    // campanario: cuatro pilares con arcos y vanos oscuros
    const yC = g1 + 23.8, hc = 5.6, Sc = 5.6;
    for (const [sx, sz] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) H_.pared.caja(tx + sx * (Sc / 2 - 0.6), yC + hc / 2, tz + sz * (Sc / 2 - 0.6), 1.2, hc, 1.2, 1, 0, blanco, 0.5);
    H_.metal.caja(tx, yC + hc / 2 - 0.3, tz, Sc - 2.2, hc - 1.2, Sc - 2.2, 1, 0, [0.08, 0.08, 0.08]);
    H_.metal.cilindro(tx, yC + 1.6, tz, 0.55, 0.85, 1.4, 12, [0.42, 0.33, 0.18]);      // campana
    H_.pared.caja(tx, yC + hc + 0.3, tz, Sc + 0.4, 0.6, Sc + 0.4, 1, 0, gris, 0.5);
    H_.pared.caja(tx, yC + hc + 1.2, tz, Sc - 1.2, 1.2, Sc - 1.2, 1, 0, blanco, 0.5);
    const cup = new THREE.Mesh(new THREE.SphereGeometry(2.3, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshStandardMaterial({ color: 0xb9c3c7, roughness: 0.45, metalness: 0.35 }));
    cup.position.set(tx, yC + hc + 1.8, tz); cup.castShadow = true; grupoHitos.add(cup);
    H_.pared.cilindro(tx, yC + hc + 4.0, tz, 0.55, 0.55, 1.2, 10, blanco);
    H_.metal.cilindro(tx, yC + hc + 5.2, tz, 0.6, 0.05, 0.8, 10, [0.6, 0.64, 0.66]);
    H_.metal.caja(tx, yC + hc + 6.7, tz, 0.12, 1.8, 0.12, 1, 0, [0.12, 0.12, 0.12]); H_.metal.caja(tx, yC + hc + 7.1, tz, 0.9, 0.12, 0.12, 1, 0, [0.12, 0.12, 0.12]);
  }
}
// ---------------------------------------------------------------- Estadio Unión Tarma (IPD; ~9 100 espectadores)
{
  const pitch = HI.pitch, pts = pitch.slice(0, 4);
  let gE = Infinity; for (const [x, z] of HI.pista) gE = Math.min(gE, altura(x, z));
  gE += 0.35;
  // pista atlética y carriles
  poligonoPlano(H_.tartan, HI.pista, gE, [1, 1, 1], 0.25);
  for (const c of HI.carriles) for (let k = 0; k < c.length - 1; k++) {
    const a = c[k], b = c[k + 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L < 1e-3) continue;
    const nx = -(b[1] - a[1]) / L * 0.03, nz = (b[0] - a[0]) / L * 0.03;
    H_.pintura.quad([a[0] - nx, gE + 0.02, a[1] - nz], [b[0] - nx, gE + 0.02, b[1] - nz], [b[0] + nx, gE + 0.02, b[1] + nz], [a[0] + nx, gE + 0.02, a[1] + nz], ARRIBA, [0.95, 0.95, 0.92]);
  }
  // cancha con franjas de corte
  const [p0, p1, p2] = pts;          // p0-p1 ancho (x), p1-p2 largo (z)
  const ux = [(p0[0] - p1[0]), (p0[1] - p1[1])], uz = [(p2[0] - p1[0]), (p2[1] - p1[1])];
  const W = Math.hypot(...ux), Lc = Math.hypot(...uz); ux[0] /= W; ux[1] /= W; uz[0] /= Lc; uz[1] /= Lc;
  const Q = (a, b, dy = 0) => [p1[0] + ux[0] * a + uz[0] * b, gE + 0.06 + dy, p1[1] + ux[1] * a + uz[1] * b];
  const nF = Math.round(Lc / 5.3);
  for (let k = 0; k < nF; k++) {
    const b0 = k * Lc / nF, b1 = (k + 1) * Lc / nF, t = k % 2 ? 0.86 : 1;
    H_.cesped.quad(Q(0, b0), Q(W, b0), Q(W, b1), Q(0, b1), ARRIBA, [t, t, t], [[0, b0 / 4], [W / 4, b0 / 4], [W / 4, b1 / 4], [0, b1 / 4]]);
  }
  // líneas reglamentarias (105 x 68 m dentro del rectángulo de OSM)
  const mA = (W - 68) / 2, mL = (Lc - 105) / 2, lw = 0.12;
  const linea = (a0, b0, a1, b1) => {
    const da = a1 - a0, db = b1 - b0, L = Math.hypot(da, db), na = -db / L * lw / 2, nb = da / L * lw / 2;
    H_.pintura.quad(Q(a0 - na, b0 - nb, 0.02), Q(a1 - na, b1 - nb, 0.02), Q(a1 + na, b1 + nb, 0.02), Q(a0 + na, b0 + nb, 0.02), ARRIBA, [0.97, 0.97, 0.95]);
  };
  const rect = (a0, b0, a1, b1) => { linea(a0, b0, a1, b0); linea(a1, b0, a1, b1); linea(a1, b1, a0, b1); linea(a0, b1, a0, b0); };
  rect(mA, mL, mA + 68, mL + 105); linea(mA, mL + 52.5, mA + 68, mL + 52.5);
  const arco = (ca, cb, r, t0, t1) => { const n = 40; for (let k = 0; k < n; k++) { const a = t0 + (t1 - t0) * k / n, b = t0 + (t1 - t0) * (k + 1) / n; linea(ca + r * Math.cos(a), cb + r * Math.sin(a), ca + r * Math.cos(b), cb + r * Math.sin(b)); } };
  arco(mA + 34, mL + 52.5, 9.15, 0, Math.PI * 2);
  for (const [b, sgn] of [[mL, 1], [mL + 105, -1]]) {
    rect(mA + 34 - 20.16, b, mA + 34 + 20.16, b + sgn * 16.5); rect(mA + 34 - 9.16, b, mA + 34 + 9.16, b + sgn * 5.5);
    const ang = Math.acos(5.5 / 9.15); arco(mA + 34, b + sgn * 11, 9.15, sgn > 0 ? Math.PI / 2 - ang : -Math.PI / 2 - ang, sgn > 0 ? Math.PI / 2 + ang : -Math.PI / 2 + ang);
    // arcos (porterías)
    for (const s of [-1, 1]) { const q = Q(mA + 34 + s * 3.66, b); H_.metal.cilindro(q[0], gE, q[2], 0.06, 0.06, 2.44, 8, [0.97, 0.97, 0.97]); }
    const q0 = Q(mA + 34 - 3.66, b, 2.44), q1 = Q(mA + 34 + 3.66, b, 2.44);
    H_.metal.tubo([q0[0], gE + 2.44, q0[2]], [q1[0], gE + 2.44, q1[2]], 0.06, [0.97, 0.97, 0.97], 8);
  }
  // tribuna occidente techada (huella OSM) y tribuna oriente (graderías de concreto)
  function tribuna(poligono, haciaCancha, hMax, techo) {
    const P = poligono.slice(0, -1); let cx = 0, cz = 0; P.forEach(p => { cx += p[0]; cz += p[1]; }); cx /= P.length; cz /= P.length;
    let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity; P.forEach(([x, z]) => { x0 = Math.min(x0, x); x1 = Math.max(x1, x); z0 = Math.min(z0, z); z1 = Math.max(z1, z); });
    const prof = x1 - x0, filas = Math.round(prof / 0.85);
    const frente = haciaCancha > 0 ? x1 : x0;
    const gT = gE;
    for (let k = 0; k < filas; k++) {
      const a = frente - haciaCancha * k * prof / filas, b = frente - haciaCancha * (k + 1) * prof / filas;
      const y = gT + 1.4 + k * (hMax - 1.4) / filas, yN = gT + 1.4 + (k + 1) * (hMax - 1.4) / filas;
      const col = k % 2 ? [0.78, 0.77, 0.74] : [0.84, 0.83, 0.8];
      H_.concreto.quad([a, y, z0], [b, y, z0], [b, y, z1], [a, y, z1], ARRIBA, col, [[a / 2, z0 / 2], [b / 2, z0 / 2], [b / 2, z1 / 2], [a / 2, z1 / 2]]);
      H_.concreto.quad([b, y, z0], [b, y, z1], [b, yN, z1], [b, yN, z0], [haciaCancha, 0, 0], [0.7, 0.69, 0.66]);
      // asientos en franjas de color (sector central)
      if (k % 1 === 0) for (let z = z0 + 1; z < z1 - 1; z += 0.55) H_.concreto.caja((a + b) / 2 + haciaCancha * 0.1, y + 0.21, z, 0.42, 0.42, 0.42, 1, 0, Math.abs(z - (z0 + z1) / 2) < (z1 - z0) * 0.22 ? [0.75, 0.12, 0.12] : [0.15, 0.32, 0.62]);
    }
    const atras = haciaCancha > 0 ? x0 : x1;
    muroPlano(H_.pared, [atras, z0], [atras, z1], gT - 1, gT + hMax + 2.5, [-haciaCancha, 0], lin('#e9e2d0'));
    muroPlano(H_.pared, [frente, z0], [frente, z1], gT - 1, gT + 1.4, [haciaCancha, 0], lin('#e9e2d0'));
    for (const [z, n] of [[z0, -1], [z1, 1]]) H_.pared.quad([frente, gT - 1, z], [atras, gT - 1, z], [atras, gT + hMax + 2.5, z], [frente, gT + 1.4, z], [0, 0, n], lin('#e9e2d0'));
    if (techo) {      // cubierta metálica en voladizo
      const yT = gT + hMax + 4.2, vol = prof + 4;
      const a0 = atras, a1 = atras + haciaCancha * vol;
      H_.calamina.quad([a0, yT, z0 - 1], [a1, yT - 1.2, z0 - 1], [a1, yT - 1.2, z1 + 1], [a0, yT, z1 + 1], ARRIBA, [0.92, 0.92, 0.95], [[0, 0], [vol, 0], [vol, z1 - z0], [0, z1 - z0]]);
      H_.calamina.quad([a0, yT - 0.05, z0 - 1], [a1, yT - 1.25, z0 - 1], [a1, yT - 1.25, z1 + 1], [a0, yT - 0.05, z1 + 1], [0, -1, 0], [0.7, 0.7, 0.72], [[0, 0], [vol, 0], [vol, z1 - z0], [0, z1 - z0]]);
      for (let z = z0; z <= z1 + 0.1; z += 9) {
        H_.metal.caja(a0 - haciaCancha * 0.3, (gT + yT) / 2, z, 0.4, yT - gT, 0.4, 1, 0, [0.3, 0.32, 0.36]);
        H_.metal.tubo([a0, yT + 0.1, z], [a1, yT - 1.1, z], 0.12, [0.3, 0.32, 0.36]);
        H_.metal.tubo([a0, yT + 2.2, z], [a1 - haciaCancha * 2, yT - 0.9, z], 0.06, [0.3, 0.32, 0.36]);
        H_.metal.caja(a0, yT + 1.1, z, 0.25, 2.2, 0.25, 1, 0, [0.3, 0.32, 0.36]);
      }
    }
  }
  tribuna(HI.tribunas[0], 1, 12.5, true);
  tribuna(HI.tribunas[1], -1, 7.5, false);
  // cerco perimétrico del estadio
  muroContorno(H_.pared, HI.estadio, (a, b) => Math.min(altura(a[0], a[1]), altura(b[0], b[1])) - 1, gE + 3.2, lin('#ece4d2'), 0.5);
}
