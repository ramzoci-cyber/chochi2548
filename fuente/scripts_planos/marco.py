# Marco del plano: desplazamiento suave (modelo -> plano) y conversión de coordenadas
# Local del modelo: x = E - 424400, z = 8738400 - N  (UTM 18S, WGS84)
import os, numpy as np
from scipy.ndimage import map_coordinates
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_F = np.load(os.path.join(_BASE, 'plan', 'campo.npz'))
_E, _N, _DX, _DY = _F['E'], _F['N'], _F['DX'], _F['DY']
def desp(E, N):
    """desplazamiento (dE, dN) en m que lleva un punto del marco del modelo al marco del plano"""
    E = np.asarray(E, dtype=float); N = np.asarray(N, dtype=float)
    c = (E - _E[0]) / (_E[1] - _E[0]); r = (N - _N[0]) / (_N[1] - _N[0])
    dE = map_coordinates(_DX, [np.atleast_1d(r).ravel(), np.atleast_1d(c).ravel()], order=1, mode='nearest').reshape(np.shape(E))
    dN = map_coordinates(_DY, [np.atleast_1d(r).ravel(), np.atleast_1d(c).ravel()], order=1, mode='nearest').reshape(np.shape(E))
    return dE, dN
def local_a_plano(x, z):
    """coordenadas locales del modelo original -> locales en el marco del plano"""
    x = np.asarray(x, dtype=float); z = np.asarray(z, dtype=float)
    dE, dN = desp(x + 424400, 8738400 - z)
    return x + dE, z - dN
def plano_a_local_orig(x, z, it=3):
    """inversa aproximada (punto fijo): local en marco del plano -> local en el marco original"""
    x = np.asarray(x, dtype=float); z = np.asarray(z, dtype=float); xo, zo = x.copy(), z.copy()
    for _ in range(it):
        dE, dN = desp(xo + 424400, 8738400 - zo); xo = x - dE; zo = z + dN
    return xo, zo
def utm_a_local(E, N): return np.asarray(E, dtype=float) - 424400, 8738400 - np.asarray(N, dtype=float)
def local_a_utm(x, z): return np.asarray(x, dtype=float) + 424400, 8738400 - np.asarray(z, dtype=float)
