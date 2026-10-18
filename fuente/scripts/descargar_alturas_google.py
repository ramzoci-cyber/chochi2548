# Descarga la ventana del centro de Tarma del ráster Google Open Buildings 2.5D Temporal (2023, 0,5 m; CC BY 4.0)
# Bandas: building_fractional_count, building_height (m), building_presence (0-1). Requiere rasterio.
import rasterio, numpy as np, os
from rasterio.windows import from_bounds
os.makedirs('data', exist_ok=True)
url = '/vsicurl/https://storage.googleapis.com/open-buildings-temporal-data/v1/geotiffs/91094_2023_06_30/tile_eKCV1ndYtBc.tif'
with rasterio.open(url) as src:
    arr = src.read(window=from_bounds(424300, 8736900, 425900, 8738900, src.transform))   # UTM 18S
np.save('data/gob_temporal_2023.npy', arr)
print(arr.shape)
