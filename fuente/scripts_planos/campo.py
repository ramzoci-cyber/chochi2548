# Campo de desplazamiento suave (modelo -> plano): TPS con suavizado sobre las ventanas, mezclado a la mediana lejos de los datos
import json, numpy as np, matplotlib
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree
matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = np.array(json.load(open('plan/desfase_ventanas.json')))
cx, cy, dx, dy, sc, nit, nB, nV, sin = R.T
ok = (sc - sin > 0.02) & (nit > 0.006)
P = np.c_[(cx - 424400) / 1000, (cy - 8738400) / 1000][ok]
V = np.c_[dx, dy][ok]
med = np.median(V, 0)
rbf = RBFInterpolator(P, V, kernel='thin_plate_spline', smoothing=1.5, degree=1)
# rejilla de 50 m sobre todo el modelo (E 421800-427000, N 8734400-8742400)
E = np.arange(421800, 427001, 50.0); N = np.arange(8734400, 8742401, 50.0)
EE, NN = np.meshgrid(E, N)
Q = np.c_[(EE.ravel() - 424400) / 1000, (NN.ravel() - 8738400) / 1000]
F = rbf(Q)
d, _ = cKDTree(P).query(Q)
w = np.exp(-(np.maximum(d - 0.25, 0) / 0.6) ** 2)[:, None]
F = w * F + (1 - w) * med
DX = F[:, 0].reshape(EE.shape); DY = F[:, 1].reshape(EE.shape)
np.savez('plan/campo.npz', E=E, N=N, DX=DX, DY=DY, med=med)
res = V - rbf(P)
print('ventanas usadas', ok.sum(), 'de', len(ok), 'mediana', med.round(2), 'residuo rms', np.sqrt((res ** 2).mean(0)).round(2), 'rango DX', DX.min().round(2), DX.max().round(2), 'DY', DY.min().round(2), DY.max().round(2))
fig, ax = plt.subplots(figsize=(8, 12), dpi=90)
k = 4
ax.quiver(EE[::k, ::k], NN[::k, ::k], DX[::k, ::k], DY[::k, ::k], angles='xy', scale_units='xy', scale=0.02, color='gray')
ax.quiver(cx[ok], cy[ok], dx[ok], dy[ok], angles='xy', scale_units='xy', scale=0.02, color='r')
ax.set_aspect('equal'); plt.tight_layout(); plt.savefig('planos/campo_desfase.png')
