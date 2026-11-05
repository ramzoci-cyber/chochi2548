# Simulación 2D de inundación (lluvia sobre malla + hidrogramas de entrada) con el esquema inercial local
# (Bates et al., 2010; de Almeida et al., 2012) en la malla de 10 m del modelo de Tarma.
# Uso: python sim2d.py <escenario> <etiqueta> [dCN] [prof_cauce_m] [n_urb] [h_ini] [h_fin]
import json, sys, time, os, numpy as np, numba as nb
G = 9.81; DX = 10.0
@nb.njit(parallel=True, fastmath=True, cache=True)
def flujos(h, z, qx, qy, n2, dt, frmax):
    H, W = h.shape
    for j in nb.prange(H):
        for i in range(W - 1):
            zl = z[j, i]; zr = z[j, i + 1]; el = zl + h[j, i]; er = zr + h[j, i + 1]
            hf = max(el, er) - max(zl, zr)
            if hf > 1e-3:
                q = qx[j, i]; nn = 0.5 * (n2[j, i] + n2[j, i + 1])
                q = (q - G * hf * dt * (er - el) / DX) / (1.0 + G * dt * nn * abs(q) / hf ** 2.3333333)
                qm = frmax * hf * (G * hf) ** 0.5
                if q > qm: q = qm
                elif q < -qm: q = -qm
                qx[j, i] = q
            else:
                qx[j, i] = 0.0
    for j in nb.prange(H - 1):
        for i in range(W):
            zl = z[j, i]; zr = z[j + 1, i]; el = zl + h[j, i]; er = zr + h[j + 1, i]
            hf = max(el, er) - max(zl, zr)
            if hf > 1e-3:
                q = qy[j, i]; nn = 0.5 * (n2[j, i] + n2[j + 1, i])
                q = (q - G * hf * dt * (er - el) / DX) / (1.0 + G * dt * nn * abs(q) / hf ** 2.3333333)
                qm = frmax * hf * (G * hf) ** 0.5
                if q > qm: q = qm
                elif q < -qm: q = -qm
                qy[j, i] = q
            else:
                qy[j, i] = 0.0
@nb.njit(parallel=True, fastmath=True, cache=True)
def limitar(h, qx, qy, dt, fac):
    # factor por celda para que la salida en dt no supere el volumen disponible
    H, W = h.shape
    for j in nb.prange(H):
        for i in range(W):
            out = 0.0
            if i < W - 1 and qx[j, i] > 0: out += qx[j, i]
            if i > 0 and qx[j, i - 1] < 0: out -= qx[j, i - 1]
            if j < H - 1 and qy[j, i] > 0: out += qy[j, i]
            if j > 0 and qy[j - 1, i] < 0: out -= qy[j - 1, i]
            out = out * dt / DX
            fac[j, i] = 1.0 if out <= h[j, i] or out <= 0 else h[j, i] / out
    for j in nb.prange(H):
        for i in range(W - 1):
            q = qx[j, i]
            if q > 0: qx[j, i] = q * fac[j, i]
            elif q < 0: qx[j, i] = q * fac[j, i + 1]
    for j in nb.prange(H - 1):
        for i in range(W):
            q = qy[j, i]
            if q > 0: qy[j, i] = q * fac[j, i]
            elif q < 0: qy[j, i] = q * fac[j + 1, i]
@nb.njit(parallel=True, fastmath=True, cache=True)
def continuidad(h, z, qx, qy, dt, fuente, hmax, vmax, tmax, t, n2, sbord):
    H, W = h.shape
    salida = 0.0
    for j in nb.prange(H):
        for i in range(W):
            dq = 0.0
            if i > 0: dq += qx[j, i - 1]
            if i < W - 1: dq -= qx[j, i]
            if j > 0: dq += qy[j - 1, i]
            if j < H - 1: dq -= qy[j, i]
            hn = h[j, i] + dt * (dq / DX + fuente[j, i])
            # borde abierto: salida con tirante normal (pendiente de borde sbord)
            if (i == 0 or j == 0 or i == W - 1 or j == H - 1) and hn > 1e-3:
                qb = hn ** 1.6666667 * sbord ** 0.5 / n2[j, i] ** 0.5
                dh = min(hn, qb * dt / DX)
                hn -= dh
            if hn < 0: hn = 0.0
            h[j, i] = hn
            if hn > hmax[j, i]:
                hmax[j, i] = hn; tmax[j, i] = t
            if hn > 0.05:
                ux = 0.5 * ((qx[j, i - 1] if i > 0 else 0.0) + (qx[j, i] if i < W - 1 else 0.0)) / hn
                uy = 0.5 * ((qy[j - 1, i] if j > 0 else 0.0) + (qy[j, i] if j < H - 1 else 0.0)) / hn
                v = (ux * ux + uy * uy) ** 0.5
                if v > vmax[j, i]: vmax[j, i] = v
    return salida
def preparar(dcn=0.0, prof=1.5, n_urb=0.20, bloque=0.0):
    M = np.load('sim/malla.npz')
    z = M['Z'].copy()
    rio = M['rio']
    z[rio] -= prof                                   # cauce excavado (sección no representada en el MDE)
    if bloque > 0:                                   # edificaciones como obstáculos: celdas con más de la mitad construida
        z[(M['fb'] > 0.5) & ~rio] += bloque
    cn = np.clip(M['cn'] + dcn, 30, 99)
    n = M['n'].copy()
    fb = M['fb']
    n = n + (n_urb - 0.20) * np.clip(fb, 0, 1)        # sensibilidad de la rugosidad equivalente de los bloques
    n[rio] = 0.035
    return z, cn, n, rio
UH_t = np.array([0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4, 4.5, 5])
UH_q = np.array([0, .03, .1, .19, .31, .47, .66, .82, .93, .99, 1, .99, .93, .86, .78, .68, .56, .46, .39, .33, .28, .207, .147, .107, .077, .055, .04, .029, .021, .015, .011, .005, 0])
def hidrogramas(esc, dcn=0.0):
    """Hidrogramas de entrada de las microcuencas aportantes (m3/s cada 10 min desde t = 0):
    lluvia del escenario en cada microcuenca (C-01) con la forma del hietograma, pérdidas SCS-CN e hidrograma unitario
    adimensional del SCS (tp = D/2 + 0.6 tc). Devuelve [(entrada, Q, caudal base)]."""
    E = json.load(open('sim/entradas.json')); LL = json.load(open('tesis/lluvia_diseno.json'))
    k = E['escenarios'].index(esc)
    mm10 = np.array(E['hietogramas'][esc]['mm10']); forma = mm10 / mm10.sum()
    f = LL['plaza_tabla'][k] / LL['plaza_mapa'][esc]
    ents = []
    for en in E['entradas']:
        P = (LL['aportes'][esc].get(str(en['n'])) or LL['plaza_mapa'][esc]) * f
        cnv = min(99.0, en['CN'] + dcn); Sx = 25400.0 / cnv - 254.0; Iax = 0.2 * Sx
        Pcx = np.cumsum(forma * P); Qcx = np.where(Pcx > Iax, (Pcx - Iax) ** 2 / (Pcx - Iax + Sx), 0.0)
        Pe = np.diff(np.r_[0, Qcx]); tp = 1 / 12 + 0.6 * en['tc_min'] / 60.0
        tt = np.arange(0, 5 * tp + 1e-9, 1 / 6); uh = np.interp(tt / tp, UH_t, UH_q) * 2.08 * en['area_km2'] / tp / 10.0
        ents.append((en, np.convolve(Pe, uh), 0.01 * en['area_km2']))
    return ents
def correr(esc, etiqueta, dcn=0.0, prof=1.5, n_urb=0.20, h0=6.0, h1=20.0, guardar_cada=900.0, verbose=True, bloque=0.0):
    E = json.load(open('sim/entradas.json'))
    z, cn, n, rio = preparar(dcn, prof, n_urb, bloque)
    H, W = z.shape
    n2 = (n * n).astype(np.float64)
    h = np.zeros((H, W)); qx = np.zeros((H, W)); qy = np.zeros((H, W)); fac = np.ones((H, W))
    hmax = np.zeros((H, W)); vmax = np.zeros((H, W)); tmax = np.zeros((H, W))
    # lluvia efectiva por bloque (SCS-CN por celda)
    mm10 = np.array(E['hietogramas'][esc]['mm10']); Pc = np.cumsum(mm10)
    S = 25400.0 / cn - 254.0; Ia = 0.2 * S
    def Qacum(P): return np.where(P > Ia, (P - Ia) ** 2 / (P - Ia + S), 0.0)
    # hidrogramas de entrada, aplicados en parches de 3 x 3 celdas
    ents = []
    for en, Q, base in hidrogramas(esc, dcn):
        xl, zl = en['local']; i0 = int(np.clip((xl + 2600) / DX, 2, W - 3)); j0 = int(np.clip((zl + 4000) / DX, 2, H - 3))
        ents.append((j0, i0, Q, base))
    t = h0 * 3600.0; t_fin = h1 * 3600.0; dtmax = 2.0; paso = 0; prox = t
    snaps = []; t0 = time.time(); vol_in = 0.0
    bloque_act = -1
    while t < t_fin:
        b = int(t // 600)
        if b != bloque_act:
            bloque_act = b
            p_ant = Pc[b - 1] if b > 0 else 0.0
            exc = (Qacum(Pc[b]) - Qacum(p_ant)) / 1000.0 / 600.0          # m/s durante el bloque
            fuente = exc.copy()
        fu = fuente.copy()
        for (j0, i0, Q, base) in ents:
            tb = t / 600.0; q = (np.interp(tb, np.arange(len(Q)), Q) if tb < len(Q) else 0.0) + base
            fu[j0 - 1:j0 + 2, i0 - 1:i0 + 2] += q / (9 * DX * DX)
        hm = h.max()
        dt = min(dtmax, 0.7 * DX / np.sqrt(G * max(hm, 0.01)))
        flujos(h, z, qx, qy, n2, dt, 1.0)
        limitar(h, qx, qy, dt, fac)
        continuidad(h, z, qx, qy, dt, fu, hmax, vmax, tmax, t, n2, 0.01)
        t += dt; paso += 1
        if t >= prox:
            snaps.append(h.astype(np.float16)); prox += guardar_cada
            if verbose: print('t = %5.2f h | dt %.2f s | h máx %.2f m | celdas > 10 cm: %d | %.0f s' % (t / 3600, dt, hm, (h > 0.1).sum(), time.time() - t0), flush=True)
    np.savez_compressed(f'sim/res_{esc}_{etiqueta}.npz', hmax=hmax.astype(np.float32), vmax=vmax.astype(np.float32), tmax=tmax.astype(np.float32),
                        snaps=np.array(snaps), t_snap=np.arange(len(snaps)) * guardar_cada + h0 * 3600, z=z.astype(np.float32),
                        params=np.array([dcn, prof, n_urb, h0, h1, bloque]))
    return hmax, vmax
if __name__ == '__main__':
    a = sys.argv
    correr(a[1], a[2], float(a[3]) if len(a) > 3 else 0.0, float(a[4]) if len(a) > 4 else 1.5, float(a[5]) if len(a) > 5 else 0.20,
           float(a[6]) if len(a) > 6 else 6.0, float(a[7]) if len(a) > 7 else 20.0, bloque=float(a[8]) if len(a) > 8 else 0.0)
