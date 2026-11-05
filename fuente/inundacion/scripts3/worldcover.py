# Lee una ventana de ESA WorldCover 2021 v200 (10 m) desde AWS (COG, peticiones por rango) y la guarda en UTM 18S a 10 m
import os, numpy as np, rasterio, rasterio.warp, rasterio.windows, rasterio.transform
from rasterio.enums import Resampling
os.environ.setdefault('CURL_CA_BUNDLE', '/root/.ccr/ca-bundle.crt')
os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
url = '/vsicurl/https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S12W078_Map.tif'
with rasterio.open(url) as src:
    print(src.crs, src.res, src.bounds)
    win = rasterio.windows.from_bounds(-75.92, -11.70, -75.50, -11.33, transform=src.transform)
    win = win.round_offsets().round_lengths()
    a = src.read(1, window=win); trw = src.window_transform(win)
print('ventana', a.shape, np.unique(a, return_counts=True))
E0, E1, N0, N1, R = 392000, 442000, 8712000, 8762000, 10.0
W, H = int((E1 - E0) / R), int((N1 - N0) / R)
tr = rasterio.transform.from_origin(E0, N1, R, R)
out = np.zeros((H, W), np.uint8)
rasterio.warp.reproject(a, out, src_transform=trw, src_crs='EPSG:4326', dst_transform=tr, dst_crs='EPSG:32718', resampling=Resampling.nearest)
with rasterio.open('ext/wc/worldcover_utm10.tif', 'w', driver='GTiff', height=H, width=W, count=1, dtype='uint8', crs='EPSG:32718', transform=tr, compress='deflate') as r: r.write(out, 1)
v, n = np.unique(out, return_counts=True); print(dict(zip(v.tolist(), (n / n.sum() * 100).round(1).tolist())))
