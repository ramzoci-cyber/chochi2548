# Modelado 3D detallado del Jr. Chanchamayo (Tarma): método, fuentes y limitaciones

Este documento explica cómo se construyó el tramo detallado del Jr. Chanchamayo en `Tarma_ciudad_3D.html`, para citarlo o adaptarlo en el capítulo de metodología o en un anexo de la tesis.

**Actualización con los planos del PDU (2025).** El modelo se ajustó después a tres planos en AutoCAD: las láminas 25 (Sistema vial) y 26 (Vías locales) de la propuesta JLORE y el Plano Total 2025 modificado. Con ellos se ajustaron:

- el marco de coordenadas;
- las cotas del terreno;
- las líneas de propiedad y los anchos de todas las calles;
- la sección propuesta del jirón.

Ese trabajo está en la sección 7. Las secciones 1 a 6 describen la primera versión y llevan anotados los valores que cambiaron.

## 1. Alcance

- **Tramo:** el Jr. Chanchamayo completo según OpenStreetMap. Mide 779,5 m entre el cruce Jr. Lima / Jr. 2 de Mayo (esquina NE de la Plaza de Armas) y la unión con la Av. Manuel Odría y la Av. Francisco de Paula Otero (frente al Estadio Unión Tarma).
- **Cuadras:** 7, más la prolongación al norte del Jr. Leonardo Alvariño. La numeración municipal crece hacia la plaza: los números 100 están al norte y los 700 junto a la plaza. Los impares quedan al lado este/sureste y los pares al oeste/noroeste. Se dedujo de 12 direcciones de negocios del jirón.
- **Cruces (12):** Jr. 2 de Mayo y Jr. Lima, Jr. Ucayali, pasaje s/n, Jr. Huánuco, Jr. Amazonas, Jr. Francisco Mendizábal, Jr. Huancavelica, Av. Bermúdez, Jr. San Juan, Jr. Ayacucho, Jr. Leonardo Alvariño, y Av. Manuel Odría con Av. F. de Paula Otero. Tres de ellos tienen semáforo en OSM: Huánuco, Mendizábal y Odría.
- **Punto crítico T01:** está a 730,9 m del inicio del eje, en la estación medida desde la plaza (732,2 m en la primera versión). La microcuenca de la tesis, que drena a T01, tiene 0,395 km². Con el eje reajustado a los planos, el jirón mide 778,2 m.

## 2. Fuentes de datos

| Fuente | Contenido usado | Resolución / fecha | Licencia |
|---|---|---|---|
| OpenStreetMap vía Overture Maps (release 2026-09-23.1) | Eje del jirón, calles transversales, semáforos, plaza, catedral, estadio, cancha, pista, río | Vectorial | ODbL |
| Google Open Buildings 2.5D Temporal v1 | Presencia y altura de edificaciones (bandas `building_presence` y `building_height`) | 0,5 m de píxel (resolución efectiva ~4 m), 2023 | CC BY 4.0 |
| Microsoft ML / Google Open Buildings (vía Overture) | Bordes de huellas, usados como pistas de linderos | Vectorial | ODbL / CC BY 4.0 |
| Overture Places (Meta, Microsoft) | Negocios con dirección en el Jr. Chanchamayo | Puntual, ubicación aproximada | CDLA-Permissive-2.0 |
| Modelo original del autor | Terreno (Copernicus GLO-30), textura (Sentinel-2), ciudad base, microcuenca, eje, T01, red D8 | 10 m / 5 m | según cada fuente |
| PDU de Tarma (Municipalidad Provincial de Tarma), láminas 25 y 26, propuesta JLORE 2025 | Secciones viales típicas (C1–C8, B1–B4, E1 y vías locales de 4 a 16 m), cortes de sección y anchos propuestos | AutoCAD 2018, escala 1/7 500 | del autor de los planos |
| Plano Total 2025, modificado por JLORE (setiembre) | Manzanas, curvas de nivel cada 5 m, nombres de calles, equipamientos | AutoCAD 2018, WGS 84 / UTM 18S | del autor de los planos |

No se usaron imágenes de Google Street View ni de Google Maps. La red del entorno de trabajo las bloqueaba. Además, los términos de Google Maps Platform (sección 3.2.3) prohíben crear modelos 3D o digitalizar edificaciones a partir de Street View o de imágenes satelitales de Google.

## 3. Procesamiento

### 3.1 Marco de referencia
Se usó WGS 84 / UTM 18S (EPSG:32718) y coordenadas locales del modelo: x = E − 424 400 y z = 8 738 400 − N, en metros, con z positivo hacia el sur. **Desde la actualización de 2025 todo el modelo está en el marco del Plano Total 2025** (sección 7.2). Las coordenadas exportadas coinciden con las del AutoCAD.

### 3.2 Corrección de alineación
El ráster de Google y la cartografía OSM/Microsoft no coincidían. Las vías de OSM caían sobre edificaciones del ráster. El desplazamiento se estimó buscando, en una grilla de ±12 m, el que minimiza la presencia media de edificación sobre 37 411 puntos de vías. Resultó de **5,0 m al este y 2,5 m al sur**: la presencia media sobre las vías bajó de 0,46 a 0,014 en el Jr. Chanchamayo. Las huellas de Microsoft y Google son coherentes con OSM, así que se corrigió el ráster y se dejó todo en el marco OSM del modelo original.

### 3.3 Eje y líneas de edificación
1. El eje OSM se densificó cada 0,5 m.
2. En cada estación se trazaron rayos perpendiculares a ambos lados hasta encontrar el primer píxel edificado (presencia > 0,5 y altura > 2 m).
3. El eje se recentró dos veces con el punto medio entre fachadas, solo donde el ancho estaba entre 5 y 13,5 m y lejos de los cruces. Luego se suavizó con un filtro gaussiano. El desplazamiento medio fue de 1,0 m.
4. La **línea de propiedad** de cada cara de manzana se tomó como el percentil 30 móvil (ventana de ±16 m) de la distancia a la primera edificación. Así, una casa con retiro no "mueve" la línea. Después se suavizó.
5. **Ancho fachada a fachada:** mediana de 8,5 m (percentil 10: 7,3 m; percentil 90: 15,9 m). En la versión con los planos, las líneas de propiedad salen del contorno de manzana del plano. El ancho medido así es: mediana 8,43 m, percentil 10 de 7,09 m y percentil 90 de 15,65 m (sección 7.7).

### 3.4 Lotes
- **Perfil de alturas:** en cada cara de manzana se midió la altura mediana del ráster entre 0,5 y 5 m detrás de la fachada, cada 0,5 m.
- **Segmentación:** el perfil se partió en lotes por programación dinámica. Se minimizó la suma de cuadrados de cada tramo más una penalidad de 20 por lote, con frentes de 4,5 a 18 m. Donde el borde de una huella de Microsoft o Google cruza la fachada, la penalidad del corte baja en 7, porque es probable que sea un lindero.
- **Clasificación:** un tramo con menos del 45 % de frente edificado se modeló como **cerco**, es decir, muro, portón o reja de un terreno sin edificar o un patio. Si la edificación está a más de 2 m de la línea de propiedad, se modeló un **retiro** con cerco y jardín.
- **Profundidad:** es la mediana, entre varios rayos, de la distancia hasta el primer vacío de 2,5 m (patio), limitada a 5–30 m. Si la altura cambia más de 2,2 m hacia el fondo, se crea un **volumen posterior** con su propia altura (30 lotes).
- **Resultado:** 101 lotes, con 1 119 m de frente edificado, y 26 cercos que suman 197 m. El frente mediano es de 10,5 m. La altura mediana es de 6,0 m (percentil 10: 4,0 m; percentil 90: 9,5 m; máximo 18,2 m).
- **Pisos:** `round((altura − 0,6) / 2,75)`. Quedaron 23 lotes de 1 piso, 48 de 2, 21 de 3, 7 de 4 y 2 de 5–6.
- **Exclusiones:** se excluyeron los volúmenes que corresponden a la tribuna del estadio, que se modela aparte.

### 3.5 Fachadas (atributos representativos)
Estos atributos se asignaron con reglas y un generador aleatorio con semilla fija, de modo que son reproducibles. Son editables en el CSV.

- **Tipología.** Las opciones son *adobe y teja* (tradicional, con balcón de madera), *ladrillo caravista* con pórticos de concreto y *tarrajeo pintado*. Adobe solo aplica a lotes de hasta 2 pisos, con probabilidad 0,42 cerca de la plaza (estación < 290 m), 0,28 en el centro y 0,20 al norte, más 0,15 si el techo se ve rojizo en Sentinel-2. Resultado: 25 de adobe, 29 de ladrillo y 47 de tarrajeo.
- **Uso.** Comercio en el primer piso con probabilidad 0,65 al sur de la estación 480 m y 0,45 al norte, y siempre en los lotes con negocio identificado. Resultado: 62 de comercio y 39 de vivienda.
- **Otros elementos.** Volado de 0,7 m sobre la vereda, balcón, último piso en obra con fierros de espera, tanque de agua, techo (losa 68, teja 25, calamina 8) y colores de una paleta local.
- **Vanos.** El frente se divide en tramos de unos 3,3 m. En el primer piso van puerta, portón, cochera o tiendas con cortina metálica (cerrada, abierta o a media altura). En los pisos altos van ventanas con marco, alféizar y derrame de 14 cm. Los letreros genéricos no llevan texto, para no inventar negocios.

### 3.6 Numeración y negocios
- **Numeración:** dentro de cada cuadra se interpola linealmente, de X00 a X99, con paridad por lado. Es **aproximada**.
- **Negocios:** los 12 negocios se ubicaron según su número de puerta. Si las coordenadas de Overture Places estaban a menos de 35 m de esa posición, se promediaron ambas. Son: Trattoria Tarma (698), Mavys Beauty Studio (676), Recepciones Cruz (663), Notaría Paulo Vivas Sierra (617), Decor Muebles 3D (545), Salón de Belleza Hilda (532), Ministerio Público (512, esquina con Jr. Amazonas), Paradise Suite Hotel (484), Plaza Seiko (460–470), Power Gym (463), Boticas Econophar (343) y Restaurante Marcelita 2 (228).

### 3.7 Perfil longitudinal y terreno
- El GLO-30 es un modelo digital de superficie con ruido en zona urbana. Por eso el perfil del eje se obtuvo con una regresión isotónica no creciente hacia el norte, un suavizado gaussiano (σ = 12 m) y una pendiente mínima de 0,2 %.
- **Perfil (primera versión, GLO-30):** de 3 056,9 a 3 042,7 m s. n. m., con pendiente media de 1,81 %. La diferencia máxima con el DEM es de 0,93 m.
- **Perfil con las curvas del plano (versión actual):** de 3 065,43 a 3 053,92 m s. n. m. La caída es de 11,52 m y la pendiente media de 1,48 %. La diferencia máxima con el MDE del plano es de 0,42 m. Se usó el mismo método: regresión isotónica, suavizado (σ = 10 m) y pendiente mínima de 0,2 %. Cerca de la cuadra 2 el terreno del plano no baja, así que el perfil queda en la pendiente mínima. Por eso ahí el tirante es mayor.
- El terreno del modelo se asentó bajo la calle: 0,32 m por debajo de la rasante hasta 9 m del borde, con transición en los 13 m siguientes. La plaza y el estadio se nivelaron como plataformas.

### 3.8 Sección y mobiliario
- **Sección de la calle:** veredas de 0,9 a 1,8 m (15 % del ancho total), calzada de hasta 8,6 m, bombeo del 2 %, sardinel de 0,17 m y vereda con pendiente del 1,5 % hacia la calle. Las líneas de propiedad salen del plano; el reparto entre vereda y calzada sigue siendo un supuesto.
- **Postes:** cada 28–36 m, alternando lado, evitando los cruces y con transformador en el 12 % de ellos.
- **Buzones:** en cada cruce y cada 55 m.
- **Sumideros:** a ±7,5 m de cada cruce, en ambos lados.
- **Vehículos:** estacionados, el 85 % al lado derecho en el sentido plaza → estadio.

**Todo esto es representativo.** Conviene reemplazarlo por el catastro de servicios (Electrocentro, EPS) o por el levantamiento propio.

## 4. Lámina de agua (ilustrativa)

- **Caudal:** Q(s) = C · i · A(s) / 3,6·10⁶ [m³/s], con C = 0,75, i en mm/h (el control "Lluvia") y A(s) en m².
- **Área aportante A(s):** es el área de la microcuenca de la tesis (0,395 km²) repartida a lo largo del eje. Cada celda de 5 m se asigna a la estación del eje donde se proyecta, hasta T01.
- **Tirante:** en cada estación, cada 2 m, el nivel de agua h se obtiene por bisección hasta cumplir la ecuación de Manning, Q = (1/n) · A_m · R^(2/3) · S^(1/2). Se usa n = 0,016, la sección real (veredas, sardineles, cunetas y bombeo) y S como la pendiente del perfil suavizado en ±12 m, con mínimo 0,5 %. Si el tirante supera 17 cm, el agua sube a las veredas.
- **Caudales de referencia en T01:**

  | Intensidad | Caudal |
  |---|---|
  | 20 mm/h | 1,65 m³/s |
  | 40 mm/h | 3,29 m³/s |
  | 60 mm/h | 4,94 m³/s |
  | 90 mm/h | 7,41 m³/s |
  | 120 mm/h | 9,87 m³/s |

- **Sección actual frente a la sección C3 propuesta (PDU).** El visor calcula el tirante con las dos secciones. La C3 tiene 10,50 m entre líneas de propiedad: vereda 1,20, cuneta 0,40, vía rodada 7,30, cuneta 0,40 y vereda 1,20, con el mismo bombeo y el mismo sardinel. El caudal es el mismo en ambos casos (Q = C·i·A). El panel muestra la sección actual en azul y la C3 en naranja.

  | Intensidad | Q en T01 | Tirante en T01, actual | Tirante en T01, C3 | Máximo aguas arriba, actual | Máximo aguas arriba, C3 |
  |---|---|---|---|---|---|
  | 30 mm/h | 2,46 m³/s | 22,7 cm | 20,8 cm | 28,8 cm (est. 592) | 24,4 cm |
  | 60 mm/h | 4,91 m³/s | 28,7 cm | 27,7 cm | 40,1 cm (est. 592) | 33,3 cm |
  | 90 mm/h | 7,37 m³/s | 33,0 cm | 33,4 cm | 49,2 cm (est. 598) | 40,4 cm |
  | 120 mm/h | 9,82 m³/s | 36,8 cm | 38,3 cm | 57,2 cm (est. 598) | 46,7 cm |

  - **En T01 la C3 casi no cambia el tirante.** Hoy el jirón ya es más ancho que 10,50 m ahí: unos 15,8 m entre líneas, porque el lado este da al área del mercado y del estadio.
  - **En la cuadra 2 la C3 sí lo baja.** Ese tramo mide 7,0 m entre líneas y tiene pendiente mínima. El tirante máximo baja entre 15 % y 18 %.

- **Limitaciones:**
  - Supone flujo uniforme y que toda la escorrentía va por el jirón (sin red de alcantarillado pluvial).
  - No calcula tiempo de concentración ni tránsito de caudales: la subida y bajada de la lámina es solo visual.
  - El coeficiente C y la rugosidad n no están calibrados.

  La lámina sirve para comunicar resultados, no para obtenerlos. Para la tesis conviene ingresar en el visor las intensidades de diseño de las curvas IDF proyectadas con CMIP5 y contrastarlas con un modelo hidráulico (SWMM / HEC-RAS, según la norma OS.060).

## 5. Validación pendiente y limitaciones

1. **Ráster de alturas:** el producto de Google es un modelo con error propio, del orden de 1–2 m en altura según sus autores, y con bordes suavizados. Los edificios muy pequeños o muy bajos pueden faltar.
2. **Fachadas:** colores, materiales, vanos, balcones, usos y numeración son **estimados**. Ningún lote se verificó en campo.
3. **Mobiliario y servicios:** la posición de postes, buzones, sumideros y vehículos es esquemática.
4. **Sección de la calle:** el ancho de veredas y la altura de sardineles son supuestos.
5. **Pavimento:** se usó pavimento rígido (losas de concreto) en todo el jirón; OSM solo indica "paved" en el tramo norte.
6. **Hitos:** la catedral y el estadio se modelaron con sus huellas OSM y descripciones públicas: catedral neoclásica de 1954, de cruz latina, con dos torres y relojes; estadio de unas 9 100 personas. Los detalles arquitectónicos son aproximados.

## 6. Levantamiento de campo recomendado

Para pasar de "representativo" a "verificado":

- **Recorrido a pie con fichas.** Llenar `datos/lotes_jr_chanchamayo.csv` lote por lote: pisos, material, uso, color, techo y N° de puerta. Tomar fotos propias, georreferenciadas.
- **Sección transversal cada 50 m y en T01.** Medir con wincha o láser el ancho de calzada y de veredas y la altura de sardineles. Ubicar cunetas, sumideros y buzones (tapas y rejillas).
- **Pendiente longitudinal.** Medir con nivel o con GNSS diferencial en puntos de control. Esto es lo que más mejora la hidráulica.
- **Marcas de agua y testimonios.** Registrar los niveles alcanzados en eventos pasados cerca de T01 para calibrar.
- **Actualización del modelo.** Tras editar el CSV, ejecutar `python herramientas/actualizar_lotes.py`. Para cambios de sección o de perfil, editar los datos de `fuente/plan/chanchamayo.json` y regenerar con `fuente/scripts/build.py`.
- **BM de control.** Ubicar un BM del IGN o de la municipalidad y medir su cota. Así se confirma el datum vertical de los planos (sección 7.2).

## 7. Planos del PDU y propuesta vial (actualización 2025)

### 7.1 Archivos y conversión
- **Planos recibidos (AutoCAD 2018, formato AC1032, en metros):**
  - `25_Sistema_vial_Tarma_-_Propuesta_JLORE.dwg` (lámina 25);
  - `26_Vias_Locales_Tarma_-_Propuesta_JLORE.dwg` (lámina 26);
  - `Plano_Total_2025_-_Modificado_JLORE_-_SEPT_-_copia.dwg`.
- **Escala y coordenadas.** Escala 1/7 500. Están en WGS 84 / UTM 18S: las grillas rotuladas como «E 421729» coinciden con OpenStreetMap con un error de pocos metros.
- **Conversión.** Se convirtieron a DXF con LibreDWG 0.7.17 (WebAssembly, `fuente/dwg/convertir.mjs`) y se leyeron con ezdxf 1.4.5. Cerca de la mitad de las curvas de nivel estaban guardadas en planos verticales (OCS). Se pasaron al sistema universal (WCS) antes de usarlas.
- **Capas usadas:**
  - `manzana ok`: 4 533 entidades;
  - `CONT-MNR`, curvas cada 5 m: 146 978 entidades;
  - `CONT-MJR`, curvas cada 25 m: 36 926 entidades;
  - `SECCIONES` de la lámina 25: 457 etiquetas y 337 líneas de corte;
  - `Secciones Viales Nuevas` de la lámina 26: 451 cotas de ancho;
  - `Calles`, para los nombres;
  - `E.MERCADO`, `E.EDUCACION`, `E.RECREACION.` y otras de equipamientos, para los linderos.
- **Capas excluidas.** Las de propietarios (`TEXTO PROPIEDADES`, certificados de catastro, `ZONA 2`) tienen nombres de personas. No se usaron ni se publican.

### 7.2 Georreferencia
- **Horizontal.** Las capas del modelo vienen de imágenes satelitales: OSM, huellas de Microsoft y Google, y la textura. Estas capas están desplazadas respecto al plano.
  - **Método.** El desplazamiento se midió en 99 ventanas de 450 m. Se buscó el que deja más superficie de edificios dentro de las manzanas del plano y más ejes OSM fuera de ellas.
  - **Resultado.** La mediana es de **1,25 m al oeste y 5,5 m al norte**. Varía entre −4 y +7 m en E y entre +1 y +11 m en N, con los valores más altos al norte de la ciudad.
  - **Aplicación.** Se ajustó un campo suave (thin-plate spline con suavizado; residuo RMS de 1,0 m en E y 0,7 m en N). Con él se movieron al marco del plano todas las capas del modelo: textura, edificios, vías, ríos, árboles, postes, microcuenca, eje, T01, hitos y el corredor del jirón.
- **Vertical.** Las curvas del plano están en promedio **10,2 m más arriba** que el Copernicus GLO-30 (geoide EGM2008). En la Plaza de Armas, el plano da 3 066,2 m y el GLO-30, 3 056,7 m. Lo más probable es un datum vertical distinto, por ejemplo alturas elipsoidales o un BM local. El modelo adopta las cotas del plano y sube el resto del terreno 10,2 m para mantener la continuidad. Para la hidráulica importan las pendientes, que no dependen de esa constante. Conviene confirmar el datum con un BM del IGN (sección 6).

### 7.3 Terreno con las curvas del plano
- **Rasterizado.** Las curvas se rasterizaron a 5 m: 87 244 celdas con curva.
- **Curvas descartadas (3 139 celdas).** Se descartaron las que no eran coherentes:
  - desvío de más de 40 m respecto al desfase típico; por ejemplo, un grupo de curvas de 3 040 a 3 060 m dibujado sobre una ladera de 3 350 m;
  - desvío de más de 22 m respecto a la mediana local en 150 m;
  - celdas donde se amontonan curvas que difieren más de 12 m.
- **Dónde manda el plano.** Las curvas se usan hasta 60 m de las manzanas. Hacia las laderas, el plano difiere del GLO-30 entre −40 y −60 m. Por eso fuera del casco se usa el GLO-30 + 10,2 m, con una transición armónica de unos 200 m y un suavizado leve que evita facetas.
- **Interpolación.** Se usó residuo armónico. En cada celda con curva se calcula r = z_curva − tendencia, donde la tendencia es el GLO-30 suavizado con σ = 20 m. El residuo se interpola resolviendo la ecuación de Laplace. El terreno final es la tendencia más el residuo. Dentro del casco urbano respeta las curvas sin error (0,000 m).
- **Malla del modelo.** La malla de 10 m del modelo es el promedio 2×2 del MDE de 5 m.
- **Red D8.** Se recalculó la red de escurrimiento D8 de 5 m sobre el terreno final. Se usó un relleno de depresiones (priority-flood) y se marcaron como calles y ríos las calzadas del plano y los cauces.
- **Exportación.** `datos/plano/mde_plano_5m.tif`.

### 7.4 Manzanas
- **Contornos abiertos.** Los contornos de la capa `manzana ok` son polilíneas abiertas que casi se tocan. Se cerraron en tres pasos:
  1. se agruparon extremos a menos de 0,6 m;
  2. se prolongaron extremos libres hasta la línea vecina, a menos de 1,2 m;
  3. se unieron pares de extremos libres a menos de 3 m.
- **Polígonos.** Luego se poligonizó y se unieron las caras contiguas. Resultado: **1 238 manzanas, 263,6 ha**.
- **Manzanas sin cerrar.** Algunas tienen huecos más grandes y no se cerraron. Por eso los anchos de calle se miden contra las líneas del plano y no contra los polígonos.
- **En el visor.** Al hacer clic en una manzana se ven su área, su perímetro y la cota de cada lado. Los lados salen del contorno simplificado con tolerancia de 1,5 m y uniendo tramos casi alineados.

### 7.5 Anchos de vía actuales
- **Medición.** Sobre los ejes OSM, ya en el marco del plano, se trazaron rayos perpendiculares cada 2 m hasta la primera línea de manzana de cada lado, con un máximo de 30 m.
- **Resultado.** 783 tramos tienen ancho medido (77,3 km). La mediana es de 8,6 m; el percentil 10, 4,8 m; el percentil 90, 23,7 m. Los valores altos corresponden a plazas y espacios abiertos.
- **Calzadas en el modelo.** Ocupan el ancho medido menos las veredas.
- **Veredas en toda la ciudad.** Se modelaron a lo largo de las líneas de manzana con un ancho representativo según el ancho de la calle:
  - sin vereda si la calle mide menos de 5 m;
  - 0,9 m hasta 7 m;
  - 1,2 m hasta 9 m;
  - 1,5 m hasta 12 m;
  - 1,8 m hasta 16 m;
  - 2,2 m en calles más anchas.

  Este ancho de vereda es un supuesto, no una medida del plano.
- **Edificios.** Los edificios de la ciudad se recortaron al contorno de las manzanas. De 10 153 huellas quedaron 9 795: se recortaron 2 890 y se quitaron 259 que invadían la calzada.

### 7.6 Propuesta vial (láminas 25 y 26)
**Secciones típicas** (anchos en m; LP = línea de propiedad):

| Sección | Total | Componentes |
|---|---|---|
| C1 | 9,30 | canal 4,00 · vía rodada 3,95 · cuneta 0,35 · vereda 1,00 |
| C2 | 24,00 | vereda 1,50 · berma 1,50 · vía rodada 6,00 · separador 6,00 · vía rodada 6,00 · berma 1,50 · vereda 1,50 |
| **C3** | **10,50** | **vereda 1,20 · cuneta 0,40 · vía rodada 7,30 · cuneta 0,40 · vereda 1,20** |
| C3′ (Jr. Lima) | 10,50 | voladizo 1,45 · peatonal 9,05 |
| C4 | 8,00 | vereda 1,20 · cuneta 0,40 · vía rodada 4,80 · cuneta 0,40 · vereda 1,20 |
| C5 | 12,00 | vereda 1,20 · cuneta 0,40 · jardín 1,00 · vía rodada 6,80 · jardín 1,00 · cuneta 0,40 · vereda 1,20 |
| C6 | 14,00 | vereda 1,80 · cuneta 0,40 · estac./jardín 1,20 · vía rodada 7,20 · estac./jardín 1,20 · cuneta 0,40 · vereda 1,80 |
| C7 | 9,40 | vereda 1,20 · cuneta 0,30 · vía rodada 6,40 · cuneta 0,30 · vereda 1,20 |
| C8 (Av. José Gálvez) | 17,00 | vereda 1,20 · jardín 1,00 · vía rodada 4,80 · canal 3,00 · vía rodada 4,80 · jardín 1,00 · vereda 1,20 |
| B1 | 14,00 | vereda 1,50 · cuneta 0,30 · estac./jardín 1,60 · vía rodada 7,20 · estac./jardín 1,60 · cuneta 0,30 · vereda 1,50 |
| B2 | 25,00 | vereda 1,20 · jardín 1,90 · cuneta 0,35 · vía rodada 7,20 · cuneta 0,35 · separador 3,00 · cuneta 0,35 · vía rodada 7,20 · cuneta 0,35 · jardín 1,90 · vereda 1,20 |
| B3 | 12,00 | vereda 1,20 · cuneta 0,30 · vía rodada 9,00 · cuneta 0,30 · vereda 1,20 |
| B4 (Av. Manuel A. Odría) | 25,00 | vereda 2,20 · cuneta 0,50 · estac./jardín 1,75 · vía rodada 6,60 · separador 2,90 · vía rodada 6,60 · estac./jardín 1,75 · cuneta 0,50 · vereda 2,20 |
| E1 (Vía de Evitamiento) | 32,40 | 3,70 · 12,50 · 12,50 · 3,70 |
| Locales (lámina 26) | 4 a 16 | 4 y 5 m: vereda, jardín y vereda (pasajes). 6, 7, 8 y 9 m: vereda, cuneta 0,40, vía rodada, cuneta y vereda. 10, 12, 14 y 16 m: con estacionamiento o jardín (detalle en `datos/plano/secciones_viales.csv`) |

**Asignación de las secciones a las calles:**
- **Lámina 25 (sistema vial).** Cada línea de corte (290 sin duplicados) se emparejó con su etiqueta y con el eje que cruza: 239 cortes asignados. La sección se extendió a los tramos del mismo jirón a menos de 450 m. Así, **331 tramos** quedaron con sección.
- **Lámina 26 (vías locales).** Cada cota de ancho da dos valores: lo que mide el dibujo, que es el ancho actual, y el texto, que es el ancho propuesto. De 444 cotas válidas, 217 cruzan un eje existente. Las demás corresponden a «vías propuestas en expansión urbana» que todavía no existen. Al extender por nombre a menos de 220 m, **595 tramos** quedaron con ancho propuesto.
- **Resultado.** **231 tramos** requieren ensanche. Si el ensanche se reparte por igual a ambos lados del centro actual, las franjas de lotes afectadas suman unas **4,05 ha** en toda la ciudad.
- **En el visor.** Esto se ve con el botón «Propuesta PDU». Es ilustrativo: las láminas no dicen de qué lado se ensancha cada vía, salvo la nota de la C8.

### 7.7 Jr. Chanchamayo reajustado
- **Sección propuesta.** La lámina 25 asigna al jirón la **sección C3 (10,50 m)**, con tres cortes a lo largo de él.
- **Eje y fachadas.**
  - El eje se movió al marco del plano y se recentró entre las líneas de manzana. El desplazamiento medio fue de 0,8 m y la longitud quedó en 778,2 m.
  - Las fachadas salen de las líneas del plano, incluidos los linderos de equipamientos, en el 89 % del lado este y el 97 % del lado oeste. El resto usa la línea de la primera versión: frente al estadio, el plano no tiene manzana cerrada.
- **Ancho actual entre líneas de propiedad:** mediana 8,43 m, percentil 10 de 7,09 m y percentil 90 de 15,65 m.
  - El 75 % de las estaciones mide menos de 10,50 m.
  - El 36 % mide menos de 8 m.
- **Linderos.** 38 linderos entre lotes se movieron hasta 2,5 m para coincidir con los quiebres del contorno de manzana. Esos quiebres marcan cambios de línea de fachada entre lotes vecinos.
- **Afectación de la C3.** Afectaría a **86 de los 101 lotes**: mediana de 1,27 m y máximo de 2,79 m de frente. Suman 964 m de fachada y unos 1 236 m².
- **En el visor.** Al hacer clic sobre la calzada del jirón se ve, en cada estación:
  - la cota y la pendiente;
  - el ancho actual;
  - la sección C3 dibujada;
  - la afectación por lado;
  - el área aportante.

  La ficha de cada lote muestra su línea de propiedad y la afectación.

### 7.8 Archivos exportados (`datos/plano/`)
| Archivo | Contenido |
|---|---|
| `manzanas_plano.geojson` | 1 238 manzanas (WGS 84), con área, perímetro y lados |
| `vias_plano.geojson` | Ejes de calles (OSM en el marco del plano) con ancho actual, mínimo, máximo, ancho propuesto, sección y fuente |
| `cotas_vias_locales.geojson` | Cotas de ancho de la lámina 26: medida del dibujo y ancho propuesto |
| `secciones_viales.csv` | Secciones típicas con sus componentes |
| `perfil_jr_chanchamayo.csv` | Perfil cada 2 m: cota de calzada y terreno, líneas de propiedad, ancho, afectación C3 y área aportante |
| `mde_plano_5m.tif` | MDE de 5 m (EPSG:32718) con las curvas del plano |
| `curvas_nivel_plano.zip` | Shapefile de curvas cada 5 m y 25 m (EPSG:32718) |

`datos/lotes_jr_chanchamayo.csv` añade dos columnas: `linea_propiedad_m` y `afectacion_C3_m`.

### 7.9 Limitaciones de esta etapa
1. **Ejes de las calles.** Son de OSM, no del plano. El ancho se mide perpendicular a ese eje y puede sobrestimarse donde el eje cruza oblicuo. En plazas y ensanches el ancho no es una sección de calle.
2. **Asignación de secciones.** Las secciones y anchos propuestos que se extendieron a tramos vecinos (columna `asignada_por_vecino`) deben revisarse en la lámina cuando el tramo sea importante para la tesis.
3. **Veredas.** Las veredas de la ciudad, fuera del jirón, son representativas. El plano no las acota.
4. **Datum vertical.** No está verificado (sección 7.2). Las pendientes, que son lo que usa la hidráulica, no dependen de esa constante.
5. **Laderas.** En las laderas altas y fuera del casco urbano el terreno es el GLO-30 corregido, no el plano.
6. **Desplazamiento.** El campo de desplazamiento corrige la posición de las capas satelitales. Las huellas de edificios siguen siendo las de Microsoft y Google, recortadas a las manzanas del plano.
