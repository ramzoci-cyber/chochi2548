# Fuente de la versión de inundaciones

Aquí están el código y los insumos procesados para regenerar `Tarma_ciudad_3D.html` (susceptibilidad a inundaciones), la simulación 2D y las capas de `datos/inundacion/`. El método está en `docs/metodologia_inundaciones.md`.

Ejecuta todos los comandos desde esta carpeta (`fuente/inundacion`).

**Dependencias:**

```bash
pip install numpy scipy numba shapely pyproj rasterio pillow pdfplumber
```

Para los pasos 1 y 2 también hace falta `pdfimages` (poppler-utils).

## Regenerar el HTML con simulaciones nuevas (unos 30 minutos)

```bash
python scripts3/sim2d.py presente final 0 1.0 0.10 6 18 3.0   # escenario presente, parámetros calibrados
bash scripts3/lote_final.sh                                     # los 8 escenarios futuros
python scripts3/exportar_inund.py final                          # empaqueta resultados y mapas de la tesis -> inund/datos_mod.json
python scripts3/build_inund.py                                   # escribe ../../Tarma_ciudad_3D.html
python scripts3/exportar_sig.py ../../datos/inundacion           # GeoJSON, GeoTIFF y CSV
```

Los resultados `sim/res_<escenario>_final.npz` (unos 20 MB cada uno) no están en el repositorio.

## Contenido

| Carpeta / archivo | Contenido |
|---|---|
| `orig/sin_datos.html` | Plantilla del visor (terreno, ciudad, panel) sin datos |
| `src_inund/base_util.js` | Utilidades: azar, texturas, materiales, acumulador de geometría |
| `src_inund/calles.js` | Calzadas, veredas y sardineles del plano y nombres de calles |
| `src_inund/geom_muros.js`, `ch_hitos.js`, `hitos_final.js` | Plaza de Armas, Catedral Santa Ana y Estadio |
| `src_inund/inund.js` | Visor de inundaciones: escenarios, capas, animación de la tormenta, fichas, leyenda y gráfico |
| `inund/datos_base.json` | Ciudad en el marco del plano, sin el corredor del Jr. Chanchamayo: terreno, calles, veredas, edificios con su unidad de riesgo e hitos |
| `inund/edificios_unidad.json` | Unidad de C-04 de cada edificio |
| `inund/resumen.json` | Estadísticas por escenario (tesis y simulación) |
| `tesis/riesgo_unidades.json` | 887 unidades de C-04 con geometría, vulnerabilidad, riesgo en 9 escenarios y 15 puntos críticos |
| `tesis/peligro_malla10.npz` | Peligro de C-03 en la malla de 10 m del modelo, 9 escenarios |
| `tesis/lluvia_diseno.json` | P24 de 25 años por escenario: tabla del artículo, mapa C-01 en la Plaza y en cada cuenca aportante |
| `sim/malla.npz` | Malla de 10 m: cota, CN, Manning, cobertura, fracción construida, fracción pavimentada y cauces |
| `sim/entradas.json` | Hietogramas de diseño (10 min) por escenario y cuencas aportantes (área, longitud, pendiente, tc, CN) |
| `sim/calibracion_final.json` | Parámetros, umbrales, matriz de riesgo, métricas de calibración y caudales pico |
| `sim/calibracion_unidades.json`, `sim/calibracion.txt` | Resultados de las corridas de calibración (escala de manzana y de celda) |
| `ext/aportes.json` | Cuencas aportantes delimitadas con GLO-30 |

## Rehacer todo desde los PDF de la tesis (requiere internet)

Copia los PDF de los cuadros a `tesis_pdf/` como `C01.pdf`, `C03.pdf` y `C04.pdf`; esta copia no está en el repositorio. Extrae las imágenes con:

```bash
pdfimages -png tesis_pdf/C03.pdf tesis_pdf/img/c03
pdfimages -png tesis_pdf/C01.pdf tesis_pdf/img/c01
```

1. **C-04.** `python scripts3/c04_extraer.py tesis_pdf/C04.pdf tesis_pdf/c04_obj.json`, luego `python scripts3/c04_georref.py`, luego `python scripts3/c04_unidades.py`. Escribe `tesis/riesgo_unidades.json`.
2. **C-03 y C-01.** `python scripts3/c03_georref.py tesis_pdf/C03.pdf tesis_pdf/c03_georref.json`, luego `python scripts3/c03_peligro.py`, luego `python scripts3/c01_lluvia.py`. Usa el mismo ajuste para C-01: copia `c03_georref.json` como `c01_georref.json`.
3. **Cuenca y aportes.** `python scripts3/cuenca.py` lee el GLO-30 de `ext/dem/glo30_S12_W076.tif`. Luego ejecuta `python scripts3/aportes.py` y `python scripts3/worldcover.py`; este último lee ESA WorldCover 2021 desde AWS.
4. **Ciudad base.** `python scripts3/ensamblar_inund.py`.
5. **Insumos de la simulación.** `python scripts3/entradas_sim.py`.

Los pasos 3 a 5 necesitan insumos que no están en el repositorio por su tamaño:

- el DEM GLO-30 y el ráster WorldCover;
- `ext/hidro30.npz` y `ext/aportes_lab.npy`;
- los intermedios del procesamiento de los planos (`plan/datos_base.json`, `plan/edificios_plano.json` y `plan/z10.npy`), que genera `fuente/scripts_planos` (ver `fuente/README.md`).

Sus salidas sí están en el repositorio (`inund/datos_base.json`, `sim/malla.npz`, `sim/entradas.json` y `ext/aportes.json`), así que la simulación se puede repetir sin rehacerlos.
6. **Calibración.** `bash scripts3/lote_calib.sh` y `bash scripts3/lote_calib2.sh` hacen las corridas del presente. Después ejecuta `python scripts3/calibrar_unidades.py sim/res_presente_*.npz` y `python scripts3/umbrales_detalle.py sim/res_presente_b3_c0.npz`.
7. **Escenarios, empaquetado y HTML.** Como en la primera sección.
