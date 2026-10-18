# Fuente del modelo

`Tarma_ciudad_3D.html` se arma juntando la plantilla original del autor, los módulos JavaScript del Jr. Chanchamayo y los datos procesados.

## Regenerar el HTML (rápido, sin internet)

```bash
cd fuente
python scripts/build.py            # escribe ../Tarma_ciudad_3D.html
python scripts/exportar_lotes.py ../datos   # vuelve a exportar CSV y GeoJSON (necesita numpy y pyproj)
```

| Archivo | Contenido |
|---|---|
| `orig/sin_datos.html` | Plantilla original (panel, terreno, ciudad, lluvia) sin los datos |
| `src/ch_util.js` | Eje, sección transversal, texturas procedurales, materiales, acumulador de geometría |
| `src/ch_calle.js` | Calzada, veredas, cruces, cruceros, buzones, sumideros, postes, cables, semáforos, placas y vehículos |
| `src/ch_lotes.js` | Generador de viviendas lote por lote y cercos |
| `src/ch_hitos.js` | Plaza de Armas, Catedral Santa Ana y Estadio Unión Tarma |
| `src/ch_ui.js` | Mallas finales, lámina de agua (racional + Manning), ficha de lote y recorrido virtual |
| `data/datos_mod.json` | Datos de la ciudad del modelo original, ajustados: terreno asentado bajo la calle, edificios superpuestos retirados |
| `data/chanchamayo.json` | Eje, perfil, líneas de propiedad, caras, cruces, lotes, cercos, mobiliario y área aportante |
| `data/hitos_final.json` | Huellas OSM de la catedral, la plaza y el estadio (cancha, pista y carriles) |

## Rehacer todo el procesamiento (requiere internet y el HTML original)

Dependencias: `pip install pyarrow shapely pyproj rasterio numpy scipy pillow`.

1. `python scripts/extraer_original.py Tarma_ciudad_3D_original.html` separa la plantilla y los datos.
2. `python scripts/decode.py` decodifica el terreno, los edificios, el flujo y la textura.
3. `python scripts/overture.py data places/place transportation/segment buildings/building base/infrastructure base/land_use base/water` descarga Overture Maps desde S3.
4. `python scripts/seg2.py` extrae los segmentos del Jr. Chanchamayo.
5. `python scripts/descargar_alturas_google.py` descarga el ráster Google Open Buildings 2.5D (2023, 0,5 m).
6. `python scripts/alinea.py` y `python scripts/alinea2.py` son diagnósticos del desplazamiento entre el ráster y OSM. El resultado, 5,0 m E y 2,5 m S, ya está fijado en los scripts siguientes.
7. `python scripts/calle.py`, luego `python scripts/cruces.py`, luego `python scripts/derivar.py`: eje recentrado, bordes y cruces.
8. `python scripts/lotes.py` segmenta los lotes y calcula profundidades y retiros. `plot_lotes.py` dibuja mapas de control.
9. `python scripts/hitos.py` y luego `python scripts/hitos2.py` preparan la plaza, la catedral y el estadio.
10. `python scripts/construir.py`, luego `python scripts/area_eje.py`, luego otra vez `python scripts/construir.py`: tipologías, numeración, negocios, mobiliario y área aportante.
11. `python scripts/ajustar.py` asienta el terreno y recorta la ciudad original.
12. `python scripts/build.py` y `python scripts/exportar_lotes.py ../datos` generan el HTML, el CSV y el GeoJSON.
