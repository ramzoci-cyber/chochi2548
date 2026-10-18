# Modelado 3D detallado del Jr. Chanchamayo (Tarma): método, fuentes y limitaciones

Este documento explica cómo se construyó el tramo detallado del Jr. Chanchamayo en `Tarma_ciudad_3D.html`, para citarlo o adaptarlo en el capítulo de metodología o en un anexo de la tesis.

## 1. Alcance

- **Tramo:** el Jr. Chanchamayo completo según OpenStreetMap. Mide 779,5 m entre el cruce Jr. Lima / Jr. 2 de Mayo (esquina NE de la Plaza de Armas) y la unión con la Av. Manuel Odría y la Av. Francisco de Paula Otero (frente al Estadio Unión Tarma).
- **Cuadras:** 7, más la prolongación al norte del Jr. Leonardo Alvariño. La numeración municipal crece hacia la plaza: los números 100 están al norte y los 700 junto a la plaza. Los impares quedan al lado este/sureste y los pares al oeste/noroeste. Se dedujo de 12 direcciones de negocios del jirón.
- **Cruces (12):** Jr. 2 de Mayo y Jr. Lima, Jr. Ucayali, pasaje s/n, Jr. Huánuco, Jr. Amazonas, Jr. Francisco Mendizábal, Jr. Huancavelica, Av. Bermúdez, Jr. San Juan, Jr. Ayacucho, Jr. Leonardo Alvariño, y Av. Manuel Odría con Av. F. de Paula Otero. Tres de ellos tienen semáforo en OSM: Huánuco, Mendizábal y Odría.
- **Punto crítico T01:** está a 732,2 m del inicio del eje, en la estación medida desde la plaza. La microcuenca de la tesis, que drena a T01, tiene 0,395 km².

## 2. Fuentes de datos

| Fuente | Contenido usado | Resolución / fecha | Licencia |
|---|---|---|---|
| OpenStreetMap vía Overture Maps (release 2026-09-23.1) | Eje del jirón, calles transversales, semáforos, plaza, catedral, estadio, cancha, pista, río | Vectorial | ODbL |
| Google Open Buildings 2.5D Temporal v1 | Presencia y altura de edificaciones (bandas `building_presence` y `building_height`) | 0,5 m de píxel (resolución efectiva ~4 m), 2023 | CC BY 4.0 |
| Microsoft ML / Google Open Buildings (vía Overture) | Bordes de huellas, usados como pistas de linderos | Vectorial | ODbL / CC BY 4.0 |
| Overture Places (Meta, Microsoft) | Negocios con dirección en el Jr. Chanchamayo | Puntual, ubicación aproximada | CDLA-Permissive-2.0 |
| Modelo original del autor | Terreno (Copernicus GLO-30), textura (Sentinel-2), ciudad base, microcuenca, eje, T01, red D8 | 10 m / 5 m | según cada fuente |

No se usaron imágenes de Google Street View ni de Google Maps. La red del entorno de trabajo las bloqueaba. Además, los términos de Google Maps Platform (sección 3.2.3) prohíben crear modelos 3D o digitalizar edificaciones a partir de Street View o de imágenes satelitales de Google.

## 3. Procesamiento

### 3.1 Marco de referencia
Se usó WGS 84 / UTM 18S (EPSG:32718) y coordenadas locales del modelo: x = E − 424 400 y z = 8 738 400 − N, en metros, con z positivo hacia el sur.

### 3.2 Corrección de alineación
El ráster de Google y la cartografía OSM/Microsoft no coincidían. Las vías de OSM caían sobre edificaciones del ráster. El desplazamiento se estimó buscando, en una grilla de ±12 m, el que minimiza la presencia media de edificación sobre 37 411 puntos de vías. Resultó de **5,0 m al este y 2,5 m al sur**: la presencia media sobre las vías bajó de 0,46 a 0,014 en el Jr. Chanchamayo. Las huellas de Microsoft y Google son coherentes con OSM, así que se corrigió el ráster y se dejó todo en el marco OSM del modelo original.

### 3.3 Eje y líneas de edificación
1. El eje OSM se densificó cada 0,5 m.
2. En cada estación se trazaron rayos perpendiculares a ambos lados hasta encontrar el primer píxel edificado (presencia > 0,5 y altura > 2 m).
3. El eje se recentró dos veces con el punto medio entre fachadas, solo donde el ancho estaba entre 5 y 13,5 m y lejos de los cruces. Luego se suavizó con un filtro gaussiano. El desplazamiento medio fue de 1,0 m.
4. La **línea de propiedad** de cada cara de manzana se tomó como el percentil 30 móvil (ventana de ±16 m) de la distancia a la primera edificación. Así, una casa con retiro no "mueve" la línea. Después se suavizó.
5. **Ancho fachada a fachada:** mediana de 8,5 m (percentil 10: 7,3 m; percentil 90: 15,9 m).

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
- **Perfil:** de 3 056,9 a 3 042,7 m s. n. m., con pendiente media de 1,81 %. La diferencia máxima con el DEM es de 0,93 m.
- El terreno del modelo se asentó bajo la calle: 0,32 m por debajo de la rasante hasta 9 m del borde, con transición en los 13 m siguientes. La plaza y el estadio se nivelaron como plataformas.

### 3.8 Sección y mobiliario
- **Sección de la calle:** veredas de 0,9 a 1,8 m (15 % del ancho total), calzada de hasta 8,6 m, bombeo del 2 %, sardinel de 0,17 m y vereda con pendiente del 1,5 % hacia la calle.
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
- **Actualización del modelo.** Tras editar el CSV, ejecutar `python herramientas/actualizar_lotes.py`. Para cambios de sección o de perfil, editar los datos de `fuente/data/chanchamayo.json` y regenerar con `fuente/scripts/build.py`.
