// ================================================================ JR. CHANCHAMAYO: mallas finales, lámina de agua, selección y recorrido virtual
const SIN_SOMBRA = new Set(['pintura', 'rejilla', 'buzon', 'pista', 'vereda', 'cesped', 'adoquin', 'tartan']);
for (const [k, geo] of Object.entries(G)) if (!geo.vacio()) grupoDetalle.add(geo.malla(MAT[k], !SIN_SOMBRA.has(k), true));
for (const [k, geo] of Object.entries(H_)) if (!geo.vacio()) grupoHitos.add(geo.malla(MAT[k], !SIN_SOMBRA.has(k), true));
const grupoCables = new THREE.Group(); grupoDetalle.add(grupoCables);
grupoCables.add(GC.malla(matStd({ vertexColors: true, roughness: 0.6, metalness: 0.2 }), false, false));
const matHalo = new THREE.MeshBasicMaterial({ map: TEX.halo, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0, polygonOffset: true, polygonOffsetFactor: -5, polygonOffsetUnits: -5 });
grupoDetalle.add(halos.malla(matHalo, false, false));
console.info('Jr. Chanchamayo y hitos generados en', Math.round(performance.now() - T0_DETALLE), 'ms');
const pickMesh = cajasPick.malla(new THREE.MeshBasicMaterial({ visible: false }), false, false);
pickMesh.geometry.computeBoundingBox(); grupoDetalle.add(pickMesh);

// ---------------------------------------------------------------- lámina de agua: método racional (Q = C·i·A) + Manning en la sección real
// Supuestos (editables): C = 0,75 (zona urbana), n = 0,016 (concreto), área aportante = microcuenca de la tesis
// repartida a lo largo del eje hasta T01 (CH.A), pendiente longitudinal del perfil suavizado (mín. 0,5 %).
const HID = { C: 0.75, n: 0.016, tau: 6, iEf: 0, iCalc: -1 };
const PS = 2;                                     // paso de estaciones (m)
const NW = Math.floor(CH.L / PS) + 1, NL = 17;     // estaciones x puntos laterales
const secc = [];                                   // perfil transversal por estación: lista de [o, y]
const pendL = new Float32Array(NW), nivel = new Float32Array(NW), tirante = new Float32Array(NW), caudal = new Float32Array(NW);
for (let k = 0; k < NW; k++) {
  const s = Math.min(CH.L, k * PS), ce = cCalz(s, 1), co = cCalz(s, -1), fe = fProp(s, 1), fo = fProp(s, -1);
  const sinVE = !enCara[1][Math.round(s / PASO)], sinVO = !enCara['-1'][Math.round(s / PASO)];
  const pts = [];
  pts.push([-fo, sinVO ? yCalzada(s, -co) + 0.25 : yVereda(s, -1, fo)]);
  if (!sinVO) { pts.push([-co - 0.15, yVereda(s, -1, co + 0.15)]); pts.push([-co - 0.001, yVereda(s, -1, co)]); }
  pts.push([-co, yCalzada(s, -co)], [0, yCalzada(s, 0)], [ce, yCalzada(s, ce)]);
  if (!sinVE) { pts.push([ce + 0.001, yVereda(s, 1, ce)]); pts.push([ce + 0.15, yVereda(s, 1, ce + 0.15)]); }
  pts.push([fe, sinVE ? yCalzada(s, ce) + 0.25 : yVereda(s, 1, fe)]);
  secc.push(pts);
  const a = Math.max(0, s - 12), b = Math.min(CH.L, s + 12);
  pendL[k] = Math.max(0.005, (interp(CH.y, a) - interp(CH.y, b)) / (b - a));
}
function hidraulica(Am2, i_mmh, sec, S) {        // devuelve [nivel, tirante, Q]
  const Q = HID.C * i_mmh * Am2 / 3.6e6;
  let ymin = Infinity; for (const p of sec) ymin = Math.min(ymin, p[1]);
  if (Q <= 1e-5) return [ymin - 0.01, 0, 0];
  const qDe = h => {
    let A = 0, P = 0;
    for (let j = 0; j < sec.length - 1; j++) {
      const [o0, y0] = sec[j], [o1, y1] = sec[j + 1], d0 = h - y0, d1 = h - y1;
      if (d0 <= 0 && d1 <= 0) continue;
      let oa = o0, ob = o1, da = d0, db = d1;
      if (d0 < 0) { const t = d0 / (d0 - d1); oa = o0 + (o1 - o0) * t; da = 0; }
      if (d1 < 0) { const t = d1 / (d1 - d0); ob = o1 + (o0 - o1) * t; db = 0; }
      A += (ob - oa) * (da + db) / 2; P += Math.hypot(ob - oa, db - da);
    }
    if (A <= 0) return 0;
    return (1 / HID.n) * A * Math.pow(A / P, 2 / 3) * Math.sqrt(S);
  };
  let lo = ymin, hi = ymin + 1.5;
  for (let it = 0; it < 32; it++) { const m = (lo + hi) / 2; if (qDe(m) < Q) lo = m; else hi = m; }
  return [hi, hi - ymin, Q];
}
function recalcularAgua(i) {
  for (let k = 0; k < NW; k++) {
    const s = Math.min(CH.L, k * PS), A = interp(CH.A, s);
    const [h, d, Q] = hidraulica(A, i, secc[k], pendL[k]); nivel[k] = h; tirante[k] = d; caudal[k] = Q;
  }
}
// malla de agua: NW x NL vértices, se actualizan las alturas y la opacidad
const geoW = new THREE.BufferGeometry();
const posW = new Float32Array(NW * NL * 3), colW = new Float32Array(NW * NL * 4), dW = new Float32Array(NW * NL * 2), latW = [];
for (let k = 0; k < NW; k++) {
  const s = Math.min(CH.L, k * PS), e = enEje(s), sec = secc[k], o0 = sec[0][0], o1 = sec[sec.length - 1][0];
  const fila = [];
  for (let j = 0; j < NL; j++) {
    const o = o0 + (o1 - o0) * j / (NL - 1);
    let y = sec[0][1]; for (let q = 0; q < sec.length - 1; q++) if (o >= sec[q][0] && o <= sec[q + 1][0]) { const t = (o - sec[q][0]) / Math.max(1e-6, sec[q + 1][0] - sec[q][0]); y = sec[q][1] + (sec[q + 1][1] - sec[q][1]) * t; }
    const v = k * NL + j; posW.set([e.x + e.nx * o, y, e.z + e.nz * o], v * 3); dW.set([s, (o - o0) / (o1 - o0)], v * 2); fila.push(y);
  }
  latW.push(fila);
}
const idxW = [];
for (let k = 0; k < NW - 1; k++) for (let j = 0; j < NL - 1; j++) { const a = k * NL + j, b = a + 1, c = a + NL, d = c + 1; idxW.push(a, b, c, b, d, c); }   // caras hacia arriba
geoW.setAttribute('position', new THREE.BufferAttribute(posW, 3).setUsage(THREE.DynamicDrawUsage));
geoW.setAttribute('color', new THREE.BufferAttribute(colW, 4).setUsage(THREE.DynamicDrawUsage));
geoW.setAttribute('aD', new THREE.BufferAttribute(dW, 2)); geoW.setIndex(idxW); geoW.computeVertexNormals();
const matLamina = new THREE.MeshStandardMaterial({ vertexColors: true, transparent: true, roughness: 0.38, metalness: 0.0, envMapIntensity: 0.18, depthWrite: false,
  polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -6 });
MATS_DETALLE.push(matLamina);
matLamina.onBeforeCompile = sh => {
  sh.uniforms.uTiempo = uTiempo;
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute vec2 aD; varying vec2 vD;').replace('#include <begin_vertex>', '#include <begin_vertex>\nvD = aD;');
  sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec2 vD; uniform float uTiempo;')
    .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
    float f1 = sin(vD.x * 2.2 - uTiempo * 6.0 + sin(vD.y * 23.0) * 1.3), f2 = sin(vD.x * 5.1 - uTiempo * 9.0 + vD.y * 31.0);
    normal = normalize(normal + vec3(f1 * 0.07 + f2 * 0.05, 0.0, f2 * 0.06));`)
    .replace('#include <color_fragment>', `#include <color_fragment>
    float fase = vD.x * 1.7 - uTiempo * 4.2 + sin(vD.y * 17.0 + vD.x * 0.31) * 1.6;
    float espuma = smoothstep(0.86, 1.0, sin(fase)) * (0.5 + 0.5 * sin(vD.y * 41.0 + vD.x * 0.9))
                 + 0.5 * smoothstep(0.93, 1.0, sin(vD.x * 4.1 - uTiempo * 6.5 + sin(vD.y * 29.0) * 2.3));
    diffuseColor.rgb = mix(diffuseColor.rgb, vec3(0.78, 0.72, 0.62), 0.35 * espuma);`);
};
const lamina = new THREE.Mesh(geoW, matLamina); lamina.visible = false; lamina.renderOrder = 2; grupoDetalle.add(lamina);
function actualizarLamina() {
  for (let k = 0; k < NW; k++) for (let j = 0; j < NL; j++) {
    const v = k * NL + j, yS = latW[k][j], d = nivel[k] - yS;
    posW[v * 3 + 1] = Math.max(yS, nivel[k]) + 0.012;
    const a = cl(d / 0.015, 0, 1) * cl(0.55 + d * 5, 0, 0.93);
    colW.set([0.5 - 0.12 * cl(d * 3, 0, 1), 0.4 - 0.1 * cl(d * 3, 0, 1), 0.27 - 0.05 * cl(d * 3, 0, 1), a], v * 4);
  }
  geoW.attributes.position.needsUpdate = true; geoW.attributes.color.needsUpdate = true;
  lamina.visible = HID.iEf > 0.3;
}
const kT01 = Math.round(CH.sT01 / PS);
function pasoAgua(dt) {
  const objetivo = lloviendo ? intensidad : 0;
  HID.iEf += (objetivo - HID.iEf) * (1 - Math.exp(-dt / HID.tau));
  if (Math.abs(HID.iEf - HID.iCalc) > 0.25 || (HID.iEf < 0.3 && HID.iCalc !== 0)) {
    HID.iCalc = HID.iEf < 0.3 ? 0 : HID.iEf; recalcularAgua(HID.iCalc); actualizarLamina(); dibujarPerfil();
    $('vT01').textContent = `${(tirante[kT01] * 100).toFixed(1)} cm · ${caudal[kT01].toFixed(2)} m³/s`;
  }
}
const lienzoP = $('perfilQ'), ctxP = lienzoP.getContext('2d');
function dibujarPerfil() {
  const dpr = devicePixelRatio || 1, w = lienzoP.clientWidth, h = lienzoP.clientHeight; if (!w) return;
  if (lienzoP.width !== w * dpr) { lienzoP.width = w * dpr; lienzoP.height = h * dpr; }
  ctxP.setTransform(dpr, 0, 0, dpr, 0, 0); ctxP.clearRect(0, 0, w, h);
  const acc = getComputedStyle(raiz).getPropertyValue('--accent').trim(), mut = getComputedStyle(raiz).getPropertyValue('--muted').trim();
  let dmax = 0.05; for (let k = 0; k < NW; k++) dmax = Math.max(dmax, tirante[k]);
  ctxP.beginPath();
  for (let k = 0; k < NW; k++) { const x = k / (NW - 1) * w, y = h - 4 - tirante[k] / dmax * (h - 10); k ? ctxP.lineTo(x, y) : ctxP.moveTo(x, y); }
  ctxP.strokeStyle = '#4f8fc0'; ctxP.lineWidth = 1.6; ctxP.stroke(); ctxP.lineTo(w, h); ctxP.lineTo(0, h); ctxP.closePath();
  const gr = ctxP.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(79,143,192,0.45)'); gr.addColorStop(1, 'rgba(79,143,192,0)'); ctxP.fillStyle = gr; ctxP.fill();
  const xT = CH.sT01 / CH.L * w; ctxP.strokeStyle = acc; ctxP.setLineDash([3, 3]); ctxP.beginPath(); ctxP.moveTo(xT, 0); ctxP.lineTo(xT, h); ctxP.stroke(); ctxP.setLineDash([]);
  ctxP.fillStyle = mut; ctxP.font = '10px Inter, sans-serif'; ctxP.fillText('Plaza', 2, 10); ctxP.fillText('T01', Math.min(w - 22, xT + 3), 10);
  ctxP.textAlign = 'right'; ctxP.fillText(`${(dmax * 100).toFixed(0)} cm`, w - 2, h - 4); ctxP.textAlign = 'left';
}

// ---------------------------------------------------------------- selección de lotes (clic) y ficha
const rayo = new THREE.Raycaster(), ptr = new THREE.Vector2();
let selMarco = null, abajoXY = null;
renderer.domElement.addEventListener('pointerdown', e => { abajoXY = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => {
  if (!abajoXY || Math.hypot(e.clientX - abajoXY[0], e.clientY - abajoXY[1]) > 5 || recorrido.activo) return;
  ptr.set(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  rayo.setFromCamera(ptr, camara);
  const hit = rayo.intersectObject(pickMesh, false)[0];
  if (!hit) { cerrarFicha(); return; }
  const id = cajasPick.lote[hit.faceIndex * 3];
  const l = CH.lotes.find(q => q.id === id); if (l) abrirFicha(l);
});
const TIPOS_TXT = { adobe: 'Tradicional: adobe y teja, balcón de madera', ladrillo: 'Ladrillo caravista con pórticos de concreto', tarrajeo: 'Tarrajeo pintado (concreto y ladrillo)' };
function abrirFicha(l) {
  const lado = l.lado > 0 ? 'este / sureste (impares)' : 'oeste / noroeste (pares)';
  $('fTitulo').textContent = l.nombre || (l.num ? `Jr. Chanchamayo ${l.num}` : 'Jr. Chanchamayo s/n');
  $('fCuerpo').innerHTML = `
    <div class="fila entre"><span>Cuadra</span><b>${l.cuadra || '1 (prolongación)'}</b></div>
    <div class="fila entre"><span>Lado</span><b>${lado}</b></div>
    <div class="fila entre"><span>N° aprox.</span><b>${l.num ?? 's/n'}</b></div>
    <div class="fila entre"><span>Pisos · altura</span><b>${l.pisos} · ${l.alto.toFixed(1)} m</b></div>
    <div class="fila entre"><span>Frente · fondo</span><b>${(l.s1 - l.s0).toFixed(1)} m · ${l.Dt.toFixed(0)} m</b></div>
    <div class="fila entre"><span>Uso (asignado)</span><b>${l.uso === 'comercio' ? 'Comercio en 1.er piso' : 'Vivienda'}</b></div>
    <div class="ficha-t">${TIPOS_TXT[l.tipo]}${l.inconcluso ? ' · último piso en obra' : ''}${l.volado ? ' · volado' : ''}</div>
    ${l.nombre ? '<div class="ficha-t">Negocio según Overture Places (ubicación aproximada).</div>' : ''}
    <div class="ficha-t">Altura y volumen: Google Open Buildings 2.5D (2023). Tipología, colores y vanos: estimados — verificar en campo.</div>`;
  $('ficha').classList.add('ver');
  if (selMarco) { grupoDetalle.remove(selMarco); selMarco.geometry.dispose(); }
  const e0 = enEje(l.s0), e1 = enEje(l.s1), sg = l.lado, f0 = l.f[0] + l.ret, f1 = l.f[1] + l.ret, D = Math.max(l.D, l.Dt);
  const Pq = (e, f) => [e.x + e.nx * f * sg, e.z + e.nz * f * sg];
  const c4 = [Pq(e0, f0), Pq(e1, f1), Pq(e1, f1 + D), Pq(e0, f0 + D)], y0 = l._g - 0.1, y1 = l._top + 0.3, v = [];
  for (let k = 0; k < 4; k++) { const a = c4[k], b = c4[(k + 1) % 4]; v.push(a[0], y0, a[1], b[0], y0, b[1], a[0], y1, a[1], b[0], y1, b[1], a[0], y0, a[1], a[0], y1, a[1]); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
  selMarco = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0xd97757, depthTest: false, transparent: true }));
  selMarco.renderOrder = 5; grupoDetalle.add(selMarco);
}
function cerrarFicha() { $('ficha').classList.remove('ver'); if (selMarco) { grupoDetalle.remove(selMarco); selMarco = null; } }
$('fCerrar').onclick = cerrarFicha;

// ---------------------------------------------------------------- recorrido virtual a nivel de calle (Plaza de Armas -> Av. Manuel Odría)
const recorrido = { activo: false, pausa: false, s: 0, vel: 5, alto: 2.4 };
const nombresCruce = CH.cruces.map(c => ({ s: c.s, n: (c.ramas.find(r => r.nombre !== '(sin nombre)') || { nombre: 'pasaje' }).nombre.replace('Jirón', 'Jr.').replace('Avenida', 'Av.').replace('Ayacuho', 'Ayacucho') }));
function tramoTexto(s) {
  let a = null, b = null; for (const c of nombresCruce) { if (c.s <= s) a = c; else if (!b) b = c; }
  const cd = cuadraDe(s);
  return `Cdra. ${cd}${a && b ? ` · entre ${a.n} y ${b.n}` : ''}`;
}
function camRecorrido(dt) {
  if (!recorrido.pausa) recorrido.s = Math.min(CH.L - 2, recorrido.s + recorrido.vel * dt);
  const s = recorrido.s, e = enEje(s), ad = enEje(Math.min(CH.L, s + 22)), o = -0.7;      // carril libre (se estaciona a la derecha)
  const y = yCalzada(s, o) + recorrido.alto;
  if (!recorrido.pausa) {
    camara.position.set(e.x + e.nx * o, y, e.z + e.nz * o);
    controles.target.set(ad.x + ad.nx * o, yCalzada(Math.min(CH.L, s + 22), o) + recorrido.alto - 0.6, ad.z + ad.nz * o);
    camara.lookAt(controles.target);
  }
  $('barraR').style.width = (s / CH.L * 100).toFixed(1) + '%';
  $('vTramo').textContent = tramoTexto(s);
  if (recorrido.s >= CH.L - 2.01 && !recorrido.pausa) pausarRecorrido(true);
}
function iniciarRecorrido() {
  recorrido.activo = true; recorrido.pausa = false; if (recorrido.s >= CH.L - 3) recorrido.s = 0;
  anim = null; controles.enabled = false; cerrarFicha();
  $('bRecorrido').innerHTML = ico.pausa + 'Pausar'; $('bloqueR').classList.add('ver');
  document.querySelectorAll('#vistas button').forEach(b => b.classList.remove('on'));
}
function pausarRecorrido(fin = false) {
  recorrido.pausa = true; controles.enabled = true;
  // mirar alrededor desde el punto: el pivote queda a 1 m delante de la cámara
  const dir = new THREE.Vector3().subVectors(controles.target, camara.position).normalize();
  controles.minDistance = 0.4; controles.target.copy(camara.position).addScaledVector(dir, 1.0); controles.update();
  $('bRecorrido').innerHTML = ico.play + (fin ? 'Reiniciar recorrido' : 'Continuar');
}
function salirRecorrido() { recorrido.activo = false; recorrido.pausa = false; controles.enabled = true; controles.minDistance = 25; $('bloqueR').classList.remove('ver'); $('bRecorrido').innerHTML = ico.play + 'Recorrido virtual'; }
$('bRecorrido').onclick = () => {
  if (!recorrido.activo) iniciarRecorrido();
  else if (recorrido.pausa) { if (recorrido.s >= CH.L - 2.5) recorrido.s = 0; recorrido.pausa = false; controles.enabled = false; controles.minDistance = 25; $('bRecorrido').innerHTML = ico.pausa + 'Pausar'; }
  else pausarRecorrido();
};
$('bSalirR').onclick = () => { salirRecorrido(); irA('chanchamayo'); };
$('sVel').oninput = e => { recorrido.vel = +e.target.value; $('vVel').textContent = recorrido.vel + ' m/s'; };
$('pistaR').onclick = e => { const r = e.currentTarget.getBoundingClientRect(); recorrido.s = cl((e.clientX - r.left) / r.width, 0, 1) * (CH.L - 2); if (recorrido.pausa) { recorrido.pausa = false; camRecorrido(0); recorrido.pausa = true; } };
controles.addEventListener('start', () => { if (recorrido.activo && !recorrido.pausa) pausarRecorrido(); });

// ---------------------------------------------------------------- ciclo del detalle
function actualizarDetalle(dt) {
  pasoAgua(dt);
  if (recorrido.activo) camRecorrido(dt);
  actualizarSemaforos(uTiempo.value);
  matHalo.opacity = uNoche.value * 0.55;
  for (const m of letrerosLuz) m.emissiveIntensity = 0.55 * uNoche.value;
  if (window.chorros) chorros.forEach((c, k) => { c.scale.y = 1 + 0.06 * Math.sin(uTiempo.value * 7 + k); c.material.opacity = 0.35 + 0.1 * Math.sin(uTiempo.value * 5 + k); });
}
