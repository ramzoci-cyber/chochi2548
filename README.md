# Tarma 3D · Susceptibilidad a inundaciones

Modelo 3D interactivo de la ciudad de Tarma (Junín, Perú) con una **simulación 2D de inundación** para los 9 escenarios de lluvia de la tesis: el presente y CMIP5/CMIP6, con emisiones moderadas y altas, en 2031–2060 y 2071–2100. La simulación está calibrada con los mapas de peligro y riesgo de la tesis. Es el apoyo visual y numérico del artículo *Influencia espacio-temporal de las lluvias extremas proyectadas con CMIP5 y CMIP6 en el peligro hidrológico de la ciudad de Tarma* (Ramos Chagua y López Silva, UCSS).

Abre `Tarma_ciudad_3D.html` con doble clic en Chrome, Edge o Firefox. Necesita internet la primera vez, porque carga three.js desde jsDelivr. Funciona mejor en una computadora con tarjeta gráfica.

![Tormenta de diseño de 25 años en el centro de Tarma (escenario presente, 12:45)](docs/capturas/04_centro_tormenta_pico.jpg)

## Qué incluye

| | |
|---|---|
| **Mapas de la tesis** | **Riesgo (C-04).** 887 unidades (573 manzanas y 314 celdas de 1 ha) con su vulnerabilidad y su riesgo en los 9 escenarios. **Peligro (C-03).** Los 9 escenarios. **Puntos críticos.** Los 15 del cuadro C-04. Todo extraído de los PDF y georreferenciado al Plano Total 2025 |
| **Simulación 2D** | Tormenta de diseño de 25 años (24 h, bloques alternos con la IDF de la tesis) sobre una malla de 10 m (5,2 × 8 km). Usa el esquema inercial local y el terreno de las curvas del plano corregido: cauce continuo y depresiones cerradas con salida. Incluye las edificaciones como obstáculos (con los patios desaguando a la calle) y los hidrogramas de 10 cuencas aportantes (SCS-CN e hidrograma unitario del SCS) |
| **Calibración** | Escenario presente, contra el riesgo por manzana de C-04: κ = 0,48, κ ponderado = 0,61 y 70,3 % de acuerdo. Es el mismo nivel que logra el propio mapa C-03 de la tesis pasado por la matriz de riesgo. Umbrales de peligro por tirante: 0,10, 0,20 y 2,0 m |
| **Animación de la tormenta** | El agua sube y baja en las calles de 10:00 a 17:00, con el hietograma y el área inundada en el gráfico |
| **Capas** | Inundación en el tiempo, tirante máximo, peligro de la tesis, riesgo de la tesis, peligro simulado, riesgo simulado y vulnerabilidad |
| **Fichas** | Por manzana: riesgo de la tesis y simulado en los 9 escenarios. Por punto crítico: tirante y velocidad. Por calle: tirante, velocidad, hora del máximo y ancho del plano |
| **Ciudad** | Terreno de las curvas del Plano Total 2025, 1 238 manzanas y calles del plano con veredas, edificios recortados a manzanas, y la Plaza de Armas, la Catedral y el Estadio como referencias |

| Riesgo por manzana · tesis (C-04), presente | Riesgo por manzana · simulación, presente | Peligro de la tesis (C-03), presente |
|---|---|---|
| ![](docs/capturas/01_general_riesgo_tesis.jpg) | ![](docs/capturas/02_general_riesgo_sim.jpg) | ![](docs/capturas/03_general_peligro_tesis.jpg) |
| **Riesgo · tesis, CMIP5 RCP 8.5 2071–2100** | **Riesgo · simulación, CMIP5 RCP 8.5 2071–2100** | **Tirante máximo, CMIP5 RCP 8.5 2071–2100** |
| ![](docs/capturas/06_general_riesgo_tesis_QA2.jpg) | ![](docs/capturas/07_general_riesgo_sim_QA2.jpg) | ![](docs/capturas/05_centro_tirante_max_QA2.jpg) |
| **Ficha de manzana** | **Ficha de punto crítico** | **Peligro simulado (sur)** |
| ![](docs/capturas/10_ficha_manzana.jpg) | ![](docs/capturas/11_ficha_punto_critico.jpg) | ![](docs/capturas/09_sur_peligro_sim.jpg) |

## Resultados por escenario

| Escenario | P24 en la Plaza | Unidades en riesgo alto: tesis · simulación | Área urbana con > 10 cm | Puntos críticos en peligro alto: tesis · simulación |
|---|---|---|---|---|
| Presente (1981–2020) | 37,2 mm | 63 · **55** | 1,24 km² | 9 · **6** |
| CMIP5 RCP 4.5 · 2031–2060 | 42,4 mm (+14 %) | 63 · **59** | 1,43 km² | 9 · **6** |
| CMIP5 RCP 4.5 · 2071–2100 | 42,6 mm (+14 %) | 63 · **61** | 1,47 km² | 9 · **6** |
| CMIP5 RCP 8.5 · 2031–2060 | 45,7 mm (+23 %) | 76 · **65** | 1,54 km² | 11 · **6** |
| CMIP5 RCP 8.5 · 2071–2100 | 63,6 mm (+71 %) | 203 · **88** | 1,96 km² | 15 · **8** |
| CMIP6 SSP2-4.5 · 2031–2060 | 41,4 mm (+11 %) | 63 · **58** | 1,38 km² | 9 · **6** |
| CMIP6 SSP2-4.5 · 2071–2100 | 50,2 mm (+35 %) | 77 · **69** | 1,64 km² | 11 · **6** |
| CMIP6 SSP5-8.5 · 2031–2060 | 41,5 mm (+12 %) | 63 · **58** | 1,40 km² | 9 · **6** |
| CMIP6 SSP5-8.5 · 2071–2100 | 50,7 mm (+36 %) | 78 · **72** | 1,67 km² | 11 · **6** |

«Unidades en riesgo alto» incluye las de riesgo alto y muy alto. Un punto crítico cuenta en la simulación si tiene al menos 0,20 m de agua a 30 m o menos.

- **Aumento.** La simulación se calibró solo con el presente, y aun así reproduce el aumento de unidades en riesgo alto de los escenarios con más lluvia: +14 frente a +14 en SSP2-4.5 2071–2100 y +17 frente a +15 en SSP5-8.5 2071–2100. El número absoluto queda entre 2 y 11 unidades por debajo de la tesis.
- **Excepción: CMIP5 RCP 8.5 2071–2100.** La tesis salta a 203 unidades y a 97 % de la ciudad en peligro alto. La simulación sube a 88 unidades y a 1,96 km² inundados (+58 %). El salto de la tesis es el de un factor de lluvia clasificado, que eleva de clase a toda la ciudad. La simulación concentra el aumento en el cauce, sus riberas y las calles bajas.
- **Profundidad.** El área inundada crece casi en proporción a la lluvia (+11 % a +58 %), y el agua profunda (más de 50 cm) unas dos veces más rápido (+26 % a +143 %).
- **Puntos críticos.** PC-2 a PC-6, PC-14 y PC-15 no llegan a peligro alto en ningún escenario: tienen menos de 0,20 m. Es probable que dependan del drenaje o de obras que no están en el plano; son los primeros que conviene verificar en campo.
- **Terreno corregido.** El cauce es continuo y el terreno no tiene depresiones cerradas, y los patios desaguan a la calle. El agua atrapada en pozos sin salida bajó de 273 000 a 22 000 m³ en el presente; lo que queda está en tramos de calle encerrados por edificaciones.

El método, la calibración, la discusión y las limitaciones están en `docs/metodologia_inundaciones.md`.

## Capas para SIG (QGIS, ArcGIS)

| Archivo | Contenido |
|---|---|
| `datos/inundacion/unidades_riesgo.geojson` | 887 unidades de C-04, con vulnerabilidad, riesgo de la tesis, riesgo simulado y tirante P90 por escenario |
| `datos/inundacion/puntos_criticos.geojson` | 15 puntos críticos, con tirante y velocidad máximos por escenario |
| `datos/inundacion/tirante_max_<código>.tif` | Tirante máximo simulado (m), 10 m, EPSG:32718 |
| `datos/inundacion/peligro_tesis_presente_cuenca.tif` | Peligro del presente (C-03) en toda la cuenca, EPSG:32718 |
| `datos/inundacion/resumen_escenarios.csv` | Tesis y simulación por escenario |
| `datos/inundacion/calibracion.csv` | Corridas de calibración |
| `datos/plano/` | Capas del Plano Total 2025: manzanas, vías, curvas de nivel y MDE de 5 m |

Los GeoJSON están en WGS84 (EPSG:4326). Los TIF están en UTM 18S, en el marco del Plano Total 2025. Los códigos de escenario son:

| Código | Escenario |
|---|---|
| `PRES` | Presente (1981–2020) |
| `QM1`, `QM2` | CMIP5 RCP 4.5 (2031–2060 y 2071–2100) |
| `QA1`, `QA2` | CMIP5 RCP 8.5 (2031–2060 y 2071–2100) |
| `SM1`, `SM2` | CMIP6 SSP2-4.5 (2031–2060 y 2071–2100) |
| `SA1`, `SA2` | CMIP6 SSP5-8.5 (2031–2060 y 2071–2100) |

## Estructura

```
Tarma_ciudad_3D.html                 modelo de susceptibilidad a inundaciones (un solo archivo)
datos/inundacion/                    capas SIG y tablas de la simulación y de la tesis
datos/plano/                         capas del Plano Total 2025 (base del modelo)
docs/metodologia_inundaciones.md     método, calibración, resultados y limitaciones (para la tesis y el artículo)
docs/capturas/                       imágenes del modelo
fuente/inundacion/                   código e insumos para repetir la simulación y regenerar el HTML
fuente/                              procesamiento de la ciudad base y de los planos del PDU
```

## Versión anterior (Jr. Chanchamayo)

El modelo detallado del Jr. Chanchamayo y del punto crítico T01 (lotes, fachadas, sección C3 y lámina de agua por el método racional) se retiró porque ya no forma parte de la investigación. Sigue en el historial de git: `git checkout ea45e99 -- Tarma_ciudad_3D.html datos docs herramientas`.
