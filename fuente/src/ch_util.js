// ================================================================ JR. CHANCHAMAYO A DETALLE: utilidades
// Geometría generada en el navegador a partir de C.chanchamayo (lotes, eje, secciones) y C.hitos.
const CH = C.chanchamayo, HI = C.hitos;
const T0_DETALLE = performance.now();
const NEJ = CH.eje.length, PASO = CH.L / (NEJ - 1);
const MATS_DETALLE = [];                    // materiales que reciben el reflejo del cielo (se atenúa de noche)
const cl = THREE.MathUtils.clamp;
function azar(semilla) {                      // generador determinista (mulberry32)
  let a = semilla >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
const colorHex = h => new THREE.Color(h);
const cTmp = new THREE.Color();
function rgbLin(h, f = 1) { cTmp.set(h); return [cTmp.r * f, cTmp.g * f, cTmp.b * f]; }

// ---------------------------------------------------------------- eje y sección transversal
const EJN = [];
for (let i = 0; i < NEJ; i++) {
  const a = CH.eje[Math.max(0, i - 2)], b = CH.eje[Math.min(NEJ - 1, i + 2)];
  const tx = b[0] - a[0], tz = b[1] - a[1], l = Math.hypot(tx, tz) || 1;
  EJN.push([-tz / l, tx / l]);               // normal hacia el lado +1 (este / sureste)
}
function indEje(s) { const f = cl(s / PASO, 0, NEJ - 1.0001), i = f | 0; return [i, f - i]; }
function interp(arr, s) { const [i, a] = indEje(s); return arr[i] * (1 - a) + arr[i + 1] * a; }
function enEje(s) {
  const [i, a] = indEje(s), p0 = CH.eje[i], p1 = CH.eje[i + 1];
  let nx = EJN[i][0] * (1 - a) + EJN[i + 1][0] * a, nz = EJN[i][1] * (1 - a) + EJN[i + 1][1] * a;
  const l = Math.hypot(nx, nz); nx /= l; nz /= l;
  return { x: p0[0] + (p1[0] - p0[0]) * a, z: p0[1] + (p1[1] - p0[1]) * a, nx, nz, tx: nz, tz: -nx, y: CH.y[i] * (1 - a) + CH.y[i + 1] * a };
}
function enLado(s, o, lado) { const e = enEje(s); return [e.x + e.nx * o * lado, e.z + e.nz * o * lado]; }
// línea de propiedad por lado: -1 en los cruces -> se interpola entre caras
function rellenar(arr) {
  const out = arr.slice(); let ult = -1;
  for (let i = 0; i < out.length; i++) if (out[i] > 0) {
    if (ult < 0) for (let k = 0; k < i; k++) out[k] = out[i];
    else for (let k = ult + 1; k < i; k++) out[k] = out[ult] + (out[i] - out[ult]) * (k - ult) / (i - ult);
    ult = i;
  }
  for (let k = ult + 1; k < out.length; k++) out[k] = out[Math.max(0, ult)];
  return out;
}
const FE = rellenar(CH.fE), FO = rellenar(CH.fO);
const CE = new Float32Array(NEJ), CO = new Float32Array(NEJ);
for (let i = 0; i < NEJ; i++) {
  const tot = FE[i] + FO[i], v = cl(0.15 * tot, 0.9, 1.8);
  CE[i] = cl(FE[i] - v, 2.3, 4.3); CO[i] = cl(FO[i] - v, 2.3, 4.3);
}
for (let pasada = 0; pasada < 3; pasada++) for (const A of [CE, CO]) {      // suavizado de bordes de calzada
  const B = A.slice();
  for (let i = 0; i < NEJ; i++) { let s = 0, n = 0; for (let k = -4; k <= 4; k++) { const j = i + k; if (j >= 0 && j < NEJ) { s += B[j]; n++; } } A[i] = s / n; }
}
const enCara = { 1: new Uint8Array(NEJ), '-1': new Uint8Array(NEJ) };
for (const c of CH.caras) for (let i = Math.ceil(c.s0 / PASO); i <= Math.floor(c.s1 / PASO); i++) enCara[c.lado][i] = 1;
const BOMBEO = 0.02, SARD = 0.17, PEND_V = 0.015;
const fProp = (s, lado) => interp(lado > 0 ? FE : FO, s);
const cCalz = (s, lado) => interp(lado > 0 ? CE : CO, s);
function yCalzada(s, o) { return interp(CH.y, s) - BOMBEO * Math.abs(o); }          // o: desplazamiento (+E / -O)
function yVereda(s, lado, d) { const c = cCalz(s, lado); return interp(CH.y, s) - BOMBEO * c + SARD + PEND_V * Math.max(0, d - c); }

// ---------------------------------------------------------------- texturas procedurales
function lienzoTex(w, h, dibujar, srgb = true) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  dibujar(cv.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy()); return t;
}
function ruido(g, w, h, n, a0, a1, col = '0,0,0', r0 = 0.5, r1 = 2.2, rnd = azar(7)) {
  for (let i = 0; i < n; i++) { g.fillStyle = `rgba(${col},${a0 + (a1 - a0) * rnd()})`; const r = r0 + (r1 - r0) * rnd(); g.fillRect(rnd() * w, rnd() * h, r, r); }
}
const TEX = {};
TEX.revoque = lienzoTex(512, 512, (g, w, h) => {                      // tarrajeo pintado (1 tesela = 4 m)
  g.fillStyle = '#f4f4f2'; g.fillRect(0, 0, w, h);
  ruido(g, w, h, 16000, 0.015, 0.06); ruido(g, w, h, 3000, 0.02, 0.07, '255,255,255', 1, 3);
  const r = azar(11);
  for (let i = 0; i < 9; i++) {           // manchas de humedad y escorrentía, irregulares
    const x = r() * w, y = r() * h, rx = 10 + 40 * r(), ry = 6 + 26 * r();
    const gr = g.createRadialGradient(x, y, 0, x, y, Math.max(rx, ry));
    gr.addColorStop(0, `rgba(80,72,58,${0.025 + 0.035 * r()})`); gr.addColorStop(1, 'rgba(80,72,58,0)');
    g.fillStyle = gr; g.beginPath(); g.ellipse(x, y, rx, ry, r() * 3, 0, 7); g.fill();
  }
  for (let i = 0; i < 6; i++) { const x = r() * w; const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(70,64,52,0)'); gr.addColorStop(0.6, `rgba(70,64,52,${0.03 + 0.03 * r()})`); gr.addColorStop(1, 'rgba(70,64,52,0)'); g.fillStyle = gr; g.fillRect(x, 0, 2 + 6 * r(), h); }
});
TEX.ladrillo = lienzoTex(256, 256, (g, w, h) => {                     // ladrillo King Kong caravista (1 tesela = 1 m)
  g.fillStyle = '#b9b2a6'; g.fillRect(0, 0, w, h);
  const r = azar(3), fil = 11, col = 4, hh = h / fil, ww = w / col;
  for (let f = 0; f < fil; f++) for (let c = -1; c <= col; c++) {
    const x = c * ww + (f % 2) * ww / 2, y = f * hh;
    const t = r(); g.fillStyle = `rgb(${168 + 40 * t | 0},${78 + 30 * t | 0},${48 + 18 * r() | 0})`;
    g.fillRect(x + 1.5, y + 1.5, ww - 3, hh - 3);
    g.fillStyle = `rgba(0,0,0,${0.05 + 0.08 * r()})`; g.fillRect(x + 1.5, y + hh - 4, ww - 3, 2.5);
  }
  ruido(g, w, h, 3000, 0.03, 0.12);
});
TEX.concreto = lienzoTex(256, 256, (g, w, h) => {
  g.fillStyle = '#d6d4cf'; g.fillRect(0, 0, w, h); ruido(g, w, h, 7000, 0.03, 0.1); ruido(g, w, h, 1200, 0.04, 0.12, '255,255,255');
  const r = azar(5); for (let i = 0; i < 10; i++) { g.fillStyle = `rgba(60,55,50,${0.03 + 0.05 * r()})`; g.beginPath(); g.arc(r() * w, r() * h, 6 + 20 * r(), 0, 7); g.fill(); }
});
TEX.teja = lienzoTex(256, 256, (g, w, h) => {                         // teja andina (1 tesela = 1,5 m)
  g.fillStyle = '#7d3a22'; g.fillRect(0, 0, w, h);
  const r = azar(9), fil = 6, col = 7, hh = h / fil, ww = w / col;
  for (let f = 0; f < fil; f++) for (let c = 0; c <= col; c++) {
    const x = c * ww + (f % 2) * ww / 2, y = f * hh, t = r();
    const gr = g.createLinearGradient(x, 0, x + ww, 0);
    gr.addColorStop(0, `rgb(${120 + 30 * t | 0},${52 + 14 * t | 0},${30 | 0})`); gr.addColorStop(0.5, `rgb(${176 + 40 * t | 0},${84 + 26 * t | 0},${48 + 10 * t | 0})`);
    gr.addColorStop(1, `rgb(${110 + 30 * t | 0},${48 + 12 * t | 0},${28})`);
    g.fillStyle = gr; g.fillRect(x + 1, y, ww - 2, hh - 3);
    g.fillStyle = 'rgba(0,0,0,0.35)'; g.fillRect(x + 1, y + hh - 4, ww - 2, 3);
    if (r() < 0.25) { g.fillStyle = `rgba(40,45,30,${0.2 + 0.3 * r()})`; g.fillRect(x + 2, y + hh * r(), ww * 0.6, 4); }   // musgo / polvo
  }
});
TEX.calamina = lienzoTex(128, 256, (g, w, h) => {                     // calamina ondulada (1 tesela = 1 m)
  for (let x = 0; x < w; x++) { const v = 0.5 + 0.5 * Math.sin(x / w * Math.PI * 2 * 7); const c = 120 + 90 * v | 0; g.fillStyle = `rgb(${c},${c + 2},${c + 4})`; g.fillRect(x, 0, 1, h); }
  const r = azar(21); for (let i = 0; i < 40; i++) { g.fillStyle = `rgba(${120 + 60 * r() | 0},${60 + 20 * r() | 0},20,${0.12 + 0.3 * r()})`; g.beginPath(); g.ellipse(r() * w, r() * h, 3 + 18 * r(), 6 + 40 * r(), 0, 0, 7); g.fill(); }
  g.fillStyle = 'rgba(0,0,0,0.3)'; g.fillRect(0, h - 3, w, 3);
});
TEX.madera = lienzoTex(128, 256, (g, w, h) => {
  g.fillStyle = '#c8a27a'; g.fillRect(0, 0, w, h);
  const r = azar(13);
  for (let x = 0; x < w; x += 2) { g.fillStyle = `rgba(80,50,25,${0.05 + 0.12 * r()})`; g.fillRect(x, 0, 1 + r() * 1.5, h); }
  for (let k = 1; k < 4; k++) { g.fillStyle = 'rgba(40,25,10,0.45)'; g.fillRect(k * w / 4, 0, 1.5, h); }
});
TEX.pista = lienzoTex(512, 512, (g, w, h) => {                        // losas de concreto 3,6 x 4 m (1 tesela = 7,2 x 8 m)
  g.fillStyle = '#a9a7a1'; g.fillRect(0, 0, w, h);
  ruido(g, w, h, 26000, 0.02, 0.09); ruido(g, w, h, 4000, 0.03, 0.08, '255,255,255');
  const r = azar(17);
  for (let i = 0; i < 26; i++) { g.fillStyle = `rgba(30,28,25,${0.03 + 0.07 * r()})`; g.beginPath(); g.ellipse(r() * w, r() * h, 10 + 40 * r(), 6 + 22 * r(), r() * 3, 0, 7); g.fill(); }
  g.fillStyle = 'rgba(20,20,20,0.55)';
  for (let k = 0; k <= 2; k++) g.fillRect(k * w / 2 - 1.5, 0, 3, h);   // juntas longitudinales (u)
  for (let k = 0; k <= 2; k++) g.fillRect(0, k * h / 2 - 1.5, w, 3);   // juntas transversales
  g.strokeStyle = 'rgba(25,25,25,0.35)'; g.lineWidth = 1;
  for (let i = 0; i < 9; i++) { g.beginPath(); let x = r() * w, y = r() * h; g.moveTo(x, y); for (let k = 0; k < 6; k++) { x += (r() - 0.5) * 30; y += r() * 18; g.lineTo(x, y); } g.stroke(); }   // fisuras
  for (let i = 0; i < 60; i++) { g.fillStyle = `rgba(15,15,15,${0.08 + 0.1 * r()})`; g.beginPath(); g.arc(w * (0.18 + 0.64 * (i % 2)) + (r() - 0.5) * 40, r() * h, 2 + 7 * r(), 0, 7); g.fill(); }   // manchas de aceite
});
TEX.vereda = lienzoTex(256, 256, (g, w, h) => {                       // vereda con bruñas cada 1 m (1 tesela = 2 m)
  g.fillStyle = '#c9c3b6'; g.fillRect(0, 0, w, h); ruido(g, w, h, 6000, 0.03, 0.1); ruido(g, w, h, 1500, 0.03, 0.09, '255,255,255');
  g.fillStyle = 'rgba(40,36,30,0.5)'; for (let k = 0; k <= 2; k++) g.fillRect(k * w / 2 - 1, 0, 2, h);
  g.fillStyle = 'rgba(40,36,30,0.25)'; g.fillRect(0, h - 2, w, 2);
});
TEX.persiana = lienzoTex(64, 128, (g, w, h) => {
  for (let y = 0; y < h; y++) { const v = 0.5 + 0.5 * Math.sin(y / h * Math.PI * 2 * 12); const c = 170 + 70 * v | 0; g.fillStyle = `rgb(${c},${c},${c})`; g.fillRect(0, y, w, 1); }
  ruido(g, w, h, 300, 0.03, 0.1);
});
TEX.cesped = lienzoTex(256, 256, (g, w, h) => {
  g.fillStyle = '#5f8f3e'; g.fillRect(0, 0, w, h); const r = azar(23);
  for (let i = 0; i < 9000; i++) { const t = r(); g.fillStyle = `rgba(${40 + 60 * t | 0},${100 + 70 * t | 0},${30 + 30 * r() | 0},0.5)`; g.fillRect(r() * w, r() * h, 1, 2 + 2 * r()); }
});
TEX.adoquin = lienzoTex(256, 256, (g, w, h) => {                      // losetas de piedra de la plaza (1 tesela = 2 m)
  g.fillStyle = '#b9aa98'; g.fillRect(0, 0, w, h); const r = azar(31), n = 5, s = w / n;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { const t = r(); g.fillStyle = `rgb(${190 + 30 * t | 0},${172 + 26 * t | 0},${152 + 22 * t | 0})`; g.fillRect(i * s + 1.5, j * s + 1.5, s - 3, s - 3); }
  ruido(g, w, h, 3000, 0.02, 0.08);
});
TEX.tartan = lienzoTex(256, 256, (g, w, h) => { g.fillStyle = '#a5432f'; g.fillRect(0, 0, w, h); ruido(g, w, h, 9000, 0.03, 0.1); ruido(g, w, h, 2000, 0.03, 0.08, '255,200,180'); });
TEX.rejilla = lienzoTex(64, 64, (g, w, h) => {
  g.fillStyle = '#2b2b2a'; g.fillRect(0, 0, w, h); g.fillStyle = '#0c0c0c';
  for (let x = 4; x < w - 2; x += 6) g.fillRect(x, 4, 3, h - 8);
});
TEX.buzon = lienzoTex(128, 128, (g, w, h) => {
  g.fillStyle = '#3a3936'; g.beginPath(); g.arc(64, 64, 63, 0, 7); g.fill();
  g.strokeStyle = '#25241f'; g.lineWidth = 3; for (let r = 14; r < 60; r += 11) { g.beginPath(); g.arc(64, 64, r, 0, 7); g.stroke(); }
  for (let a = 0; a < 8; a++) { g.beginPath(); g.moveTo(64, 64); g.lineTo(64 + 60 * Math.cos(a * 0.785), 64 + 60 * Math.sin(a * 0.785)); g.stroke(); }
});
TEX.halo = lienzoTex(128, 128, (g, w, h) => {
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, 'rgba(255,214,150,0.95)'); gr.addColorStop(0.35, 'rgba(255,190,120,0.45)'); gr.addColorStop(1, 'rgba(255,170,90,0)');
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
});
TEX.agua = lienzoTex(256, 256, (g, w, h) => {
  g.fillStyle = '#808080'; g.fillRect(0, 0, w, h); const r = azar(41);
  for (let i = 0; i < 160; i++) { g.strokeStyle = `rgba(255,255,255,${0.05 + 0.15 * r()})`; g.lineWidth = 1 + 2 * r(); g.beginPath(); const x = r() * w, y = r() * h; g.moveTo(x, y); g.bezierCurveTo(x + 10, y + 8, x + 20, y - 6, x + 40 + 30 * r(), y + 4); g.stroke(); }
}, false);

// ---------------------------------------------------------------- materiales
function matStd(op) { const m = new THREE.MeshStandardMaterial(op); MATS_DETALLE.push(m); return m; }
const MAT = {
  pared: matStd({ map: TEX.revoque, vertexColors: true, roughness: 0.92, envMapIntensity: 0.35 }),
  ladrillo: matStd({ map: TEX.ladrillo, vertexColors: true, roughness: 0.95, envMapIntensity: 0.25 }),
  concreto: matStd({ map: TEX.concreto, vertexColors: true, roughness: 0.9, envMapIntensity: 0.3 }),
  teja: matStd({ map: TEX.teja, vertexColors: true, roughness: 0.85, envMapIntensity: 0.3 }),
  calamina: matStd({ map: TEX.calamina, vertexColors: true, roughness: 0.55, metalness: 0.35, envMapIntensity: 0.6 }),
  madera: matStd({ map: TEX.madera, vertexColors: true, roughness: 0.8, envMapIntensity: 0.25 }),
  metal: matStd({ vertexColors: true, roughness: 0.45, metalness: 0.55, envMapIntensity: 0.7 }),
  persiana: matStd({ map: TEX.persiana, vertexColors: true, roughness: 0.5, metalness: 0.45, envMapIntensity: 0.6 }),
  pista: matStd({ map: TEX.pista, vertexColors: true, roughness: 0.93, envMapIntensity: 0.4 }),
  vereda: matStd({ map: TEX.vereda, vertexColors: true, roughness: 0.9, envMapIntensity: 0.35 }),
  cesped: matStd({ map: TEX.cesped, vertexColors: true, roughness: 1, envMapIntensity: 0.2 }),
  adoquin: matStd({ map: TEX.adoquin, vertexColors: true, roughness: 0.88, envMapIntensity: 0.35 }),
  tartan: matStd({ map: TEX.tartan, vertexColors: true, roughness: 0.95, envMapIntensity: 0.2 }),
  rejilla: matStd({ map: TEX.rejilla, roughness: 0.7, metalness: 0.4 }),
  buzon: matStd({ map: TEX.buzon, roughness: 0.6, metalness: 0.5, transparent: true, alphaTest: 0.5 }),
  pintura: new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.6, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 }),
};
// vidrio y focos: brillan de noche según el atributo aLuz (ventanas encendidas al azar)
function matLuminoso(base, tono) {
  const m = matStd(base);
  m.onBeforeCompile = sh => {
    sh.uniforms.uNoche = uNoche;
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aLuz; varying float vLuz;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvLuz = aLuz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vLuz; uniform float uNoche;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
      totalEmissiveRadiance += vec3(${tono}) * vLuz * uNoche;`);
  };
  return m;
}
MAT.vidrio = matLuminoso({ vertexColors: true, roughness: 0.08, metalness: 0.35, envMapIntensity: 1.25 }, '1.0, 0.74, 0.44');
MAT.foco = matLuminoso({ vertexColors: true, roughness: 0.4, envMapIntensity: 0.3 }, '1.6, 1.25, 0.85');

// ---------------------------------------------------------------- acumulador de geometría
class Geo {
  constructor() { this.p = []; this.n = []; this.c = []; this.u = []; this.l = []; this.lote = []; }
  vert(p, n, c, u, luz, id) { this.p.push(p[0], p[1], p[2]); this.n.push(n[0], n[1], n[2]); this.c.push(c[0], c[1], c[2]); this.u.push(u[0], u[1]); this.l.push(luz); this.lote.push(id); }
  // cuadrilátero a,b,c,d (en orden perimetral) con normal n; uv por vértice
  quad(a, b, c, d, n, col, uv = null, luz = 0, id = -1) {
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    const gx = uy * vz - uz * vy, gy = uz * vx - ux * vz, gz = ux * vy - uy * vx;
    uv = uv || [[0, 0], [1, 0], [1, 1], [0, 1]];
    if (gx * n[0] + gy * n[1] + gz * n[2] >= 0) {
      this.vert(a, n, col, uv[0], luz, id); this.vert(b, n, col, uv[1], luz, id); this.vert(c, n, col, uv[2], luz, id);
      this.vert(a, n, col, uv[0], luz, id); this.vert(c, n, col, uv[2], luz, id); this.vert(d, n, col, uv[3], luz, id);
    } else {
      this.vert(a, n, col, uv[0], luz, id); this.vert(c, n, col, uv[2], luz, id); this.vert(b, n, col, uv[1], luz, id);
      this.vert(a, n, col, uv[0], luz, id); this.vert(d, n, col, uv[3], luz, id); this.vert(c, n, col, uv[2], luz, id);
    }
  }
  tri(a, b, c, n, col, uv = null, luz = 0, id = -1) {
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2], vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    const gx = uy * vz - uz * vy, gy = uz * vx - ux * vz, gz = ux * vy - uy * vx;
    uv = uv || [[0, 0], [1, 0], [0.5, 1]];
    if (gx * n[0] + gy * n[1] + gz * n[2] >= 0) { this.vert(a, n, col, uv[0], luz, id); this.vert(b, n, col, uv[1], luz, id); this.vert(c, n, col, uv[2], luz, id); }
    else { this.vert(a, n, col, uv[0], luz, id); this.vert(c, n, col, uv[2], luz, id); this.vert(b, n, col, uv[1], luz, id); }
  }
  // caja orientada: centro (x,y,z), medidas (a lo largo de u, alto, a lo largo de w), ejes horizontales u=(ux,uz), w=(-uz,ux)
  caja(x, y, z, lu, alto, lw, ux, uz, col, escalaUV = 1, sinFondo = true, luz = 0) {
    const wx = -uz, wz = ux, hu = lu / 2, hw = lw / 2;
    const P = (su, sy, sw) => [x + ux * hu * su + wx * hw * sw, y + sy * alto / 2, z + uz * hu * su + wz * hw * sw];
    const e = escalaUV;
    const caras = [
      [[1, -1, -1], [1, -1, 1], [1, 1, 1], [1, 1, -1], [ux, 0, uz], lw, alto],
      [[-1, -1, 1], [-1, -1, -1], [-1, 1, -1], [-1, 1, 1], [-ux, 0, -uz], lw, alto],
      [[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1], [wx, 0, wz], lu, alto],
      [[1, -1, -1], [-1, -1, -1], [-1, 1, -1], [1, 1, -1], [-wx, 0, -wz], lu, alto],
      [[-1, 1, -1], [1, 1, -1], [1, 1, 1], [-1, 1, 1], [0, 1, 0], lu, lw]];
    if (!sinFondo) caras.push([[-1, -1, 1], [1, -1, 1], [1, -1, -1], [-1, -1, -1], [0, -1, 0], lu, lw]);
    for (const [a, b, c, d, n, du, dv] of caras)
      this.quad(P(...a), P(...b), P(...c), P(...d), n, col, [[0, 0], [du * e, 0], [du * e, dv * e], [0, dv * e]], luz);
  }
  // cilindro vertical (n lados)
  cilindro(x, y0, z, r0, r1, alto, lados, col, tapa = true) {
    for (let k = 0; k < lados; k++) {
      const a0 = k / lados * Math.PI * 2, a1 = (k + 1) / lados * Math.PI * 2, am = (a0 + a1) / 2;
      const n = [Math.cos(am), (r0 - r1) / alto, Math.sin(am)];
      this.quad([x + r0 * Math.cos(a0), y0, z + r0 * Math.sin(a0)], [x + r0 * Math.cos(a1), y0, z + r0 * Math.sin(a1)],
        [x + r1 * Math.cos(a1), y0 + alto, z + r1 * Math.sin(a1)], [x + r1 * Math.cos(a0), y0 + alto, z + r1 * Math.sin(a0)], n, col,
        [[k / lados, 0], [(k + 1) / lados, 0], [(k + 1) / lados, 1], [k / lados, 1]]);
      if (tapa) this.tri([x, y0 + alto, z], [x + r1 * Math.cos(a1), y0 + alto, z + r1 * Math.sin(a1)], [x + r1 * Math.cos(a0), y0 + alto, z + r1 * Math.sin(a0)], [0, 1, 0], col);
    }
  }
  // tubo entre dos puntos 3D (cables, barandas, fierros)
  tubo(a, b, r, col, lados = 4) {
    const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], L = Math.hypot(...d); if (L < 1e-4) return;
    const t = [d[0] / L, d[1] / L, d[2] / L];
    let u = Math.abs(t[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
    let p = [t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0]]; const lp = Math.hypot(...p); p = p.map(v => v / lp);
    const q = [t[1] * p[2] - t[2] * p[1], t[2] * p[0] - t[0] * p[2], t[0] * p[1] - t[1] * p[0]];
    for (let k = 0; k < lados; k++) {
      const a0 = k / lados * Math.PI * 2, a1 = (k + 1) / lados * Math.PI * 2;
      const o0 = [p[0] * Math.cos(a0) + q[0] * Math.sin(a0), p[1] * Math.cos(a0) + q[1] * Math.sin(a0), p[2] * Math.cos(a0) + q[2] * Math.sin(a0)];
      const o1 = [p[0] * Math.cos(a1) + q[0] * Math.sin(a1), p[1] * Math.cos(a1) + q[1] * Math.sin(a1), p[2] * Math.cos(a1) + q[2] * Math.sin(a1)];
      const n = [(o0[0] + o1[0]) / 2, (o0[1] + o1[1]) / 2, (o0[2] + o1[2]) / 2];
      this.quad([a[0] + o0[0] * r, a[1] + o0[1] * r, a[2] + o0[2] * r], [a[0] + o1[0] * r, a[1] + o1[1] * r, a[2] + o1[2] * r],
        [b[0] + o1[0] * r, b[1] + o1[1] * r, b[2] + o1[2] * r], [b[0] + o0[0] * r, b[1] + o0[1] * r, b[2] + o0[2] * r], n, col);
    }
  }
  vacio() { return this.p.length === 0; }
  malla(mat, sombra = true, recibe = true) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.c, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.u, 2));
    g.setAttribute('aLuz', new THREE.Float32BufferAttribute(this.l, 1));
    g.computeBoundingSphere();
    const m = new THREE.Mesh(g, mat); m.castShadow = sombra; m.receiveShadow = recibe; return m;
  }
}
const grupoDetalle = new THREE.Group(); grupoDetalle.name = 'JrChanchamayo'; escena.add(grupoDetalle);
const G = {}; for (const k of ['pared', 'ladrillo', 'concreto', 'teja', 'calamina', 'madera', 'metal', 'persiana', 'pista', 'vereda', 'vidrio', 'foco', 'cesped', 'adoquin', 'tartan', 'pintura', 'rejilla', 'buzon']) G[k] = new Geo();
