# Fuente del modelo

`Tarma_ciudad_3D.html` se arma juntando la plantilla original del autor, los módulos JavaScript del Jr. Chanchamayo y los datos procesados.

## Regenerar el HTML (rápido, sin internet)

```bash
cd fuente
python scripts/build.py            # escribe ../Tarma_ciudad_3D.html (lee plan/datos_mod.json, plan/chanchamayo.json y plan/hitos_plano.json)
python scripts_planos/exportar_lotes.py ../datos   # vuelve a exportar el CSV y el GeoJSON de lotes (necesita numpy y pyproj)
```

| Archivo | Contenido |
|---|---|
| `orig/sin_datos.html` | Plantilla original (panel, terreno, ciudad, lluvia) sin los datos |
| `src/ch_util.js` | Eje, sección transversal, texturas procedurales, materiales, acumulador de geometría |
| `src/ch_calle.js` | Calzada, veredas, cruces, cruceros, buzones, sumideros, postes, cables, semáforos, placas y vehículos |
| `src/ch_lotes.js` | Generador de viviendas lote por lote y cercos |
| `src/ch_hitos.js` | Plaza de Armas, Catedral Santa Ana y Estadio Unión Tarma |
| `src/ch_plano.js` | Planos del PDU: calzadas con el ancho del plano, veredas y sardineles, fichas de vía, manzana y estación del jirón, capa «Propuesta PDU» |
| `src/ch_ui.js` | Mallas finales, lámina de agua (racional + Manning, sección actual y C3), ficha de lote y recorrido virtual |
| `plan/datos_mod.json` | Datos de la ciudad en el marco del plano: terreno con las curvas del plano, edificios recortados a manzanas, calles, veredas, manzanas, red D8 |
| `plan/chanchamayo.json` | Jr. Chanchamayo reajustado al plano (eje, líneas de propiedad, perfil, lotes, sección C3) |
| `plan/hitos_plano.json` | Plaza, catedral y estadio en el marco del plano |
| `plan/calles.json`, `plan/manzanas.json` | Anchos actuales y propuestos por tramo, veredas y polígonos de manzana |
| `plan/campo.npz`, `plan/desfase_ventanas.json` | Campo de desplazamiento modelo → plano y sus estimaciones por ventana |
| `data/datos_mod.json` | Primera versión (marco OSM): datos de la ciudad con el terreno asentado bajo la calle |
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

## Procesamiento de los planos del PDU (2025)

Dependencias: las de arriba más `pip install ezdxf pyshp`, y Node.js para convertir los DWG. Los DWG no están en el repositorio. Tienen datos de propietarios, así que se trabajan en local. Se usan en estos pasos:

1. **Conversión de los DWG a DXF.** En `dwg/`, ejecuta `npm install` y luego `node convertir.mjs <plano>.dwg ../planos/<nombre>`. Se hace con `plano_total`, `sistema_vial` y `vias_locales`.
2. **Entidades en WCS.** `python scripts_planos/extraer_wcs.py planos/<nombre>.dxf planos/<nombre>_wcs.pkl` pasa las entidades por capa a coordenadas WCS. Las curvas guardadas en planos verticales (OCS) quedan con su cota real. `inventario.py` y `mapa_plano.py` sirven para revisar las capas.
3. **Secciones típicas.** `python scripts_planos/secciones_bloque.py` lee las cotas de las secciones típicas de los bloques VIAS2 y 111. Los valores ya están transcritos en `calles_plano.py`.
4. **Manzanas.** `python scripts_planos/manzanas.py` cierra y poligoniza la capa `manzana ok` y escribe `plan/manzanas_crudo.pkl`.
5. **Desplazamiento.** `python scripts_planos/campo_desfase.py` estima el desfase por ventanas. Luego `python scripts_planos/campo.py` ajusta el campo suave (`plan/campo.npz`). `marco.py` aplica el campo.
6. **Capas del modelo al marco del plano.** `python scripts_planos/base_plano.py` mueve las capas del modelo original (requiere `orig/datos_clean.json`; ver el paso 1 de la sección anterior).
7. **Terreno.** `python scripts_planos/terreno_plano.py` arma el MDE de 5 m con las curvas y la malla de 10 m.
8. **Calles.** `python scripts_planos/calles_plano.py` calcula anchos actuales, anchos propuestos, secciones y veredas.
9. **Jr. Chanchamayo.** `python scripts_planos/corredor_plano.py` reajusta el corredor: eje, líneas de propiedad, linderos y perfil.
10. **Ensamblado.** `python scripts_planos/ajustar_plano.py` arma `plan/datos_mod.json`: edificios recortados, árboles, postes, terreno asentado y red D8.
11. **HTML.** `python scripts/build.py` genera el modelo.
12. **Exportación.** `python scripts_planos/exportar_plano.py ../datos/plano` y `python scripts_planos/exportar_lotes.py ../datos` exportan las capas para SIG.

Los scripts se ejecutan desde `fuente/` y leen y escriben rutas relativas: `planos/`, `plan/`, `orig/` y `data/`.
