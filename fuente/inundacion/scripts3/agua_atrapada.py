# Agua atrapada en depresiones cerradas del terreno de cada simulación (vecindad de 4 celdas): celdas en depresión,
# volumen de agua por debajo del nivel de rebalse y cuántas depresiones guardan más de 30 cm. Uso: python agua_atrapada.py res1.npz ...
import sys, numpy as np
from scipy import ndimage
sys.path.insert(0, 'scripts3'); import sim2d
M = np.load('sim/malla.npz'); fp = M['fp']
cruz = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], bool)
for f in sys.argv[1:]:
    R = np.load(f); z = R['z'].astype(np.float64); h = R['hmax'].astype(np.float64)
    dep = sim2d.relleno(z) - z; m = dep > 0.01
    lab, n = ndimage.label(m, structure=cruz)
    atrap = np.minimum(h, dep) * m
    llenas = sum(1 for k in range(1, n + 1) if atrap[lab == k].max() > 0.3) if n else 0
    calle = m & (fp > 0.3)
    print('%-40s | depresiones %4d (%5d celdas, %d en calles) | agua atrapada %7.0f m3 | depresiones con > 30 cm de agua: %d' % (
        f.split('/')[-1], n, m.sum(), calle.sum(), atrap.sum() * 100, llenas))
