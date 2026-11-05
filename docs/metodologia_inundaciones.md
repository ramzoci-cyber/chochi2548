# Susceptibilidad a inundaciones de la ciudad de Tarma: modelo 3D, simulación 2D y calibración con la tesis

Este documento explica cómo se construyó la versión de inundaciones del modelo 3D de Tarma. Cubre la extracción de los mapas de la tesis, la simulación hidráulica 2D por escenario, su calibración contra el mapa de riesgo de la tesis, los resultados y sus límites. Acompaña a la tesis de Ramos Chagua y López Silva (UCSS) y al artículo *Influencia espacio-temporal de las lluvias extremas proyectadas con CMIP5 y CMIP6 en el peligro hidrológico de la ciudad de Tarma*.

**Resumen.**

- **Qué es.** Una simulación 2D de la tormenta de diseño de 25 años (24 h) sobre una malla de 10 m de la ciudad, con el terreno de las curvas del plano, las edificaciones como obstáculos y los patios desaguando a la calle.
- **Escenarios.** Corre los 9 escenarios de la tesis: el presente y CMIP5/CMIP6, con emisiones moderadas y altas, en 2031–2060 y 2071–2100.
- **Calibración.** Con el escenario presente, a la escala de manzana, contra el cuadro C-04.
- **Concordancia.** κ = 0,49; κ ponderado = 0,62; 70,5 % de acuerdo en 4 clases. Es la misma concordancia que logra el propio mapa de peligro C-03 de la tesis pasado por la matriz de riesgo (κ = 0,49 a 0,60).
- **Puntos críticos.** La simulación marca 6 de los 15 puntos críticos en peligro alto; la tesis, 9.

## 1. Cambio de enfoque y limpieza del modelo

La investigación dejó de centrarse en el punto crítico T01 del Jr. Chanchamayo y pasó a un mapa de susceptibilidad a inundaciones de toda la ciudad.

**Qué se retiró del HTML y del repositorio:**

- el corredor del Jr. Chanchamayo modelado lote por lote: lotes, fachadas, mobiliario, vehículos, negocios y recorrido virtual;
- la microcuenca y el eje de T01;
- la lámina de agua por el método racional;
- las fichas de sección vial y la capa «Propuesta PDU».

Todo eso sigue disponible en el historial de git (commit `ea45e99`).

**Qué se conserva**, porque es la base física del modelo de inundación:

- el terreno de las curvas del Plano Total 2025;
- las 1 238 manzanas y las calles del plano, con veredas y sardineles;
- los edificios recortados a las manzanas;
- la Plaza de Armas, la Catedral y el Estadio como referencias.

### 1.1 Base del modelo (planos del PDU, 2025)

- **Marco.** Todo el modelo está en el marco del Plano Total 2025 (WGS84 UTM 18S, como el AutoCAD). El marco local del visor es x = E − 424 400 y z = 8 738 400 − N.
- **Alineación.** Las capas satelitales (OSM, Microsoft, Google y Sentinel-2) estaban desplazadas respecto al plano: en mediana, 1,25 m al oeste y 5,5 m al norte. Se corrigieron con un campo de desplazamiento suave.
- **Terreno.** Es un MDE de 5 m. En el casco urbano, hasta 60 m de las manzanas, sale de las curvas de nivel del plano por interpolación armónica; afuera, del GLO-30 + 10,2 m. Para la simulación se promedia a 10 m.
- **Datum vertical.** Las curvas están unos 10,2 m más arriba que el GLO-30: en la Plaza de Armas, 3 066,2 m frente a 3 056,7 m. Probablemente es un datum vertical distinto, que no cambia las pendientes.
- **Manzanas y calles.** Las 1 238 manzanas salen de la capa `manzana ok` del plano. Las calzadas tienen el ancho medido entre manzanas, y los edificios están recortados a las manzanas.

## 2. Insumos de la tesis

| Cuadro | Contenido | Uso en el modelo |
|---|---|---|
| C-01 | Lluvia de diseño de 25 años (P24) por escenario, en isoyetas | Lluvia de cada escenario sobre la ciudad y sobre cada cuenca aportante |
| C-02 | Cambio porcentual de la lluvia respecto al presente | Referencia; la lluvia de cada escenario sale de C-01 |
| C-03 | Peligro hidrológico (4 clases) en la cuenca y la ciudad, 9 escenarios | Referencia de la calibración a escala de celda; capa del visor |
| C-04 | Riesgo por manzana (y celdas de 1 ha) en 9 escenarios, vulnerabilidad y 15 puntos críticos | Unidades de análisis, referencia principal de la calibración, capa del visor |
| P-01 | Isoyetas del presente | Referencia; la lluvia del presente sale de C-01 |
| Artículo | Método y tabla de resultados por escenario | Valores de control: P24 en la Plaza, % de ciudad y cuenca en peligro alto, unidades, edificaciones, servicios y puntos críticos |

**Método de la tesis, en resumen:**

- **Lluvia.** PISCOp v3.0 corregido, ajuste GEV con forma común y factores de cambio de NEX-GDDP (CMIP5, 7 modelos) y NEX-GDDP-CMIP6 (12 modelos). La IDF del presente es I = 205,39·T^0,1296 / d^0,75.
- **Peligro.** H = 0,5·D + 0,5·Σ wᵢ·Cᵢ, donde D es el factor desencadenante (la lluvia). Los factores condicionantes y sus pesos son la acumulación de flujo (0,471), la distancia a cauces (0,284), la pendiente (0,171) y la cobertura (0,074); la relación de consistencia es 0,019.
- **Riesgo.** Riesgo = peligro × vulnerabilidad. La vulnerabilidad se mide como exposición: edificaciones, fracción construida y servicios esenciales.

## 3. Extracción y georreferenciación de los mapas de la tesis

### 3.1 Cuadro C-04 (riesgo por manzana)

**Extracción.** Los 10 paneles del cuadro son dibujos vectoriales: el presente, la vulnerabilidad y los 8 escenarios futuros. Cada manzana es un polígono relleno con el color de su clase: bajo `#A9D18E`, medio `#FFE699`, alto `#F4B183` y muy alto `#C00000`. Se leyeron con `pdfplumber` y salieron **887 unidades**: 573 manzanas y 314 celdas de 1 ha en la periferia. Cada unidad tiene su vulnerabilidad y su clase de riesgo en los 9 mapas.

**Georreferencia.** El punto de partida fue la estrella de la Plaza de Armas. Después se hizo un ajuste fino (ICP de semejanza) de los centroides contra las manzanas del Plano Total 2025, y al final un ajuste a la grilla de 100 m de las celdas de 1 ha.

**Control.** El mapa extraído tiene 65 unidades en riesgo alto o muy alto en el presente; la tabla del artículo dice 63. En RCP 8.5 2071–2100 tiene 206; la tabla dice 203.

**Puntos críticos.** Los 15 puntos críticos se ubicaron con los marcadores del mapa.

### 3.2 Cuadros C-03 (peligro) y C-01 (lluvia)

**Extracción.** Estos paneles son imágenes rasterizadas dentro del PDF. Se extrajeron con `pdfimages`, con su máscara de transparencia. Cada color se llevó a su clase (C-03) o a la marca de clase de la isoyeta (C-01: 38, 42, … 74 mm).

**Georreferencia.** Se ajustó el contorno del «área urbana evaluada» contra la unión de las unidades de C-04 ya georreferenciadas. La escala ajustada, 141,1 m por punto del PDF, coincide con la escala nominal 1:400 000 de los cuadros. El mismo ajuste sirve para C-01 y C-03.

**Malla.** El peligro se remuestreó a la malla de 10 m del modelo.

**Controles:**

- **Cuenca.** El porcentaje de la cuenca en peligro alto o muy alto coincide con la tabla del artículo.
- **Ciudad.** En el mapa extraído, la ciudad tiene entre 14,6 % y 14,8 % en peligro alto o muy alto, mientras que la tabla del artículo da 21,6 %. Ninguna definición razonable del área urbana (unidades de C-04, manzanas o contorno urbano) reproduce el 21,6 %. Conviene revisar en el SIG de la tesis con qué polígono se calculó ese porcentaje.
- **Lluvia.** La P24 que se lee en la Plaza en C-01 (38 mm en el presente, 62 mm en RCP 8.5 2071–2100) concuerda con la tabla (37,2 y 63,6 mm). En la simulación se usa el valor de la tabla y se reparte en el espacio con el mapa.

## 4. Hidrología de entrada

**Cuenca.** Se delimitó la cuenca del río Tarma hasta la ciudad con Copernicus GLO-30, igual que la tesis, con estos pasos:

1. relleno de depresiones (priority-flood);
2. direcciones D8;
3. acumulación de flujo.

La salida está en E 424 805, N 8 741 945 y da **419,37 km²**, frente a 419,66 km² en la tesis.

**Dominio y aportes.** El dominio 2D mide 5,2 × 8 km y está centrado en la ciudad. Los cauces que entran por su borde tienen 10 cuencas aportantes, de 1,2 a 215,5 km².

**Lluvia efectiva.** Se calculó con SCS-CN (AMC II, grupo hidrológico C). El CN sale de la cobertura ESA WorldCover 2021, a 10 m:

| Cobertura | CN |
|---|---|
| Árboles | 73 |
| Arbustos | 77 |
| Pastos | 79 |
| Cultivos | 85 |
| Construido | 92 |
| Suelo desnudo | 91 |
| Agua | 100 |
| Humedal | 95 |

Dentro de la ciudad, la fracción de techos y calzadas toma CN 98.

**Hietograma.** Son bloques alternos de 10 minutos con la forma de la IDF de la tesis, escalados a la P24 de cada escenario. En cada cuenca aportante, la lluvia es la del mapa C-01 en esa cuenca, escalada por la razón tabla/mapa en la Plaza.

**Hidrogramas de entrada.** Se usó el hidrograma unitario adimensional del SCS, con tp = D/2 + 0,6·tc, el tc de Kirpich y un caudal base de 0,01 m³/s/km². Los caudales pico de los dos aportes mayores son:

| Escenario | Aporte oeste (215,5 km²) | Aporte sur (116,1 km²) |
|---|---|---|
| Presente | 86 m³/s | 77 m³/s |
| CMIP6 SSP5-8.5 2071–2100 | 221 m³/s | 196 m³/s |
| CMIP5 RCP 8.5 2071–2100 | 379 m³/s | 322 m³/s |

## 5. Modelo hidráulico 2D

**Esquema.** Se usó el esquema inercial local (Bates et al., 2010; de Almeida et al., 2012) en una malla de 10 m de 520 × 800 celdas, en el marco del Plano Total 2025 (UTM 18S). Está programado en Python con numba, en paralelo.

**Terreno.** Es el MDE de las curvas del plano. La Plaza de Armas y el Estadio están nivelados.

**Rugosidad de Manning:**

- calzadas: 0,016;
- coberturas de WorldCover: 0,035 a 0,10;
- cauce: 0,035;
- celdas con edificaciones: rugosidad equivalente que crece con la fracción construida, hasta 0,10.

**Edificaciones.** Las celdas con más de la mitad construida se elevan 3 m y actúan como obstáculos: el agua corre por las calles.

**Patios sin bolsones.** Al elevar las edificaciones, los techos siguen la pendiente del terreno, y los patios y espacios libres rodeados de construcción quedaban como pozos sin salida. El agua de toda la manzana corría hacia el patio más bajo y se acumulaba ahí, a veces con más de 2 m.

La corrección rellena esas celdas libres hasta su nivel de rebalse:

- solo en las celdas que no son calle ni cauce;
- solo en la parte de la depresión que crean las edificaciones, comparando con el terreno sin ellas;
- con la vecindad de 4 celdas del esquema numérico.

Así el agua de techos y patios sale a la calle, como en la realidad por el zaguán o el desagüe de la vivienda. Se elevaron 2 043 celdas, 0,43 m en promedio. Las depresiones del propio terreno y los badenes de las calles no se tocan, porque el agua que se junta en una calle es parte del peligro.

**Cauce.** Las celdas del río se profundizan 1,0 m, porque el MDE no representa la sección del cauce.

**Condiciones de borde.** Los bordes son abiertos, con tirante normal y pendiente 0,01. Los hidrogramas entran en parches de 3 × 3 celdas.

**Estabilidad.** Δt ≤ 2 s, con CFL α = 0,7. Hay un límite de Froude (Fr ≤ 1) y un limitador de volumen saliente por celda.

**Ventana de cálculo.** Se simulan las horas 6 a 18 de la tormenta de 24 h; el pico de intensidad está a las 12 h. Se guardan el tirante y la velocidad máximos, la hora del máximo y una instantánea cada 15 minutos.

**Costo.** Cada escenario tarda unos 3 minutos en 4 núcleos.

## 6. Calibración (escenario presente)

### 6.1 Cómo se comparó

**Escala de manzana (referencia principal).** Para cada unidad de C-04 se calcula el P90 del tirante máximo dentro de la unidad, con un borde de 10 m para incluir la calle. Ese valor pasa a una clase de peligro con tres umbrales de tirante. La clase, combinada con la vulnerabilidad de la tesis, da un riesgo con la matriz que reproduce C-04:

| Peligro \ Vulnerabilidad | Baja | Media | Alta | Muy alta |
|---|---|---|---|---|
| Bajo | bajo | medio | medio | alto |
| Medio | bajo | medio | medio | alto |
| Alto | medio | medio | alto | alto |
| Muy alto | medio | alto | alto | muy alto |

El riesgo simulado se compara con el de C-04 mediante:

- κ de Cohen en 4 clases;
- κ con pesos cuadráticos;
- κ en 2 clases (alto o muy alto frente al resto).

**Escala de celda.** La clase simulada, agregada a unos 30 m, se compara con C-03.

**Puntos críticos.** Se cuentan los puntos con peligro simulado alto o muy alto en un radio de 30 m.

### 6.2 Corridas

Se probaron 9 combinaciones de parámetros:

- ajuste del CN: 0, +6 y +11;
- profundidad del cauce: 0,5, 1,0 y 1,5 m;
- rugosidad de bloque: 0,10 y 0,20;
- edificaciones como obstáculos: no, o sí con +3 m.

Para cada corrida se buscaron los umbrales que mejor reproducen C-04.

| Corrida | ΔCN | Cauce (m) | n de bloque | Edificaciones | Umbrales (m) | κ 4 clases | κ ponderado | κ 2 clases | Unidades en riesgo alto (sim / mapa C-04) | Puntos críticos ≥ 10 cm / ≥ 30 cm | κ celdas (C-03) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `base` | +0 | 1,5 | 0,20 | no | 0,05 · 0,15 · 1,50 | 0,482 | 0,622 | 0,624 | 64 / 65 | 6 / 3 | — |
| `c0_p0.5` | +0 | 0,5 | 0,20 | no | 0,05 · 0,20 · 1,50 | 0,486 | 0,621 | 0,653 | 59 / 65 | 6 / 3 | 0,167 |
| `c0_p1.5` | +0 | 1,5 | 0,20 | no | 0,05 · 0,15 · 1,50 | 0,482 | 0,622 | 0,624 | 64 / 65 | 6 / 3 | 0,157 |
| `c6_p0.5` | +6 | 0,5 | 0,20 | no | 0,05 · 0,10 · 1,50 | 0,470 | 0,611 | 0,629 | 66 / 65 | 9 / 6 | 0,156 |
| `c6_p1.5` | +6 | 1,5 | 0,20 | no | 0,05 · 0,10 · 2,00 | 0,475 | 0,610 | 0,641 | 61 / 65 | 8 / 6 | 0,155 |
| `c11_p0.5` | +11 | 0,5 | 0,20 | no | 0,05 · 0,10 · 2,00 | 0,472 | 0,609 | 0,652 | 62 / 65 | 12 / 6 | 0,166 |
| `c11_p1.5` | +11 | 1,5 | 0,20 | no | 0,05 · 0,75 · 2,00 | 0,462 | 0,609 | 0,607 | 64 / 65 | 12 / 6 | 0,165 |
| `b3_c0` | +0 | 1,0 | 0,10 | +3 m | 0,05 · 0,20 · 2,00 | 0,488 | 0,620 | 0,653 | 59 / 65 | 9 / 4 | 0,163 |
| `b3_c6` | +6 | 1,0 | 0,10 | +3 m | 0,05 · 0,75 · 2,00 | 0,465 | 0,612 | 0,590 | 64 / 65 | 10 / 7 | 0,160 |
| `b3p_c0` | +0 | 1,0 | 0,10 | +3 m | 0,05 · 0,30 · 1,50 | 0,472 | 0,615 | 0,618 | 65 / 65 | 6 / 3 | 0,158 |

La última columna es el κ en 2 clases frente a C-03, con los umbrales que mejor reproducen C-03 a escala de celda; la corrida `base` no se evaluó a esa escala. `b3p_c0` es `b3_c0` con la corrección de patios.

### 6.3 Resultado

**Parámetros elegidos (corrida `b3p_c0`):**

- CN de la tabla, sin ajuste;
- cauce de 1,0 m;
- edificaciones como obstáculos de 3 m;
- rugosidad de bloque de 0,10;
- patios sin bolsones (ver sección 5).

Las corridas logran un acuerdo parecido con C-04 (κ entre 0,46 y 0,49), así que la elección se basó en el realismo físico. Entre las corridas sin corrección de patios, `b3_c0` tenía el κ más alto en 4 clases (0,49) y en 2 clases (0,65), y es una de las dos que representan las edificaciones como obstáculos. La versión final `b3p_c0` es la misma corrida con los patios corregidos.

Con los umbrales finales, `b3p_c0` da:

| Métrica | Valor |
|---|---|
| κ en 4 clases | 0,486 |
| κ ponderado | 0,618 |
| κ en 2 clases | 0,653 |
| Acuerdo | 70,5 % |
| Unidades en riesgo alto | 59 (65 en el mapa) |
| Puntos críticos en peligro alto | 6 |

**Efecto de la corrección de patios.** El acuerdo casi no cambia (κ 0,488 → 0,486), porque los bolsones eran celdas sueltas dentro de las manzanas. Sí cambian algunos puntos críticos:

| Punto | Antes | Después |
|---|---|---|
| PC-14 | 0,32 m | 0,05 m |
| PC-13 | 0,16 m | 0,06 m |
| PC-7 | 0,13 m | 0,09 m |

Su agua venía de un patio vecino sin salida. Por eso la simulación marca ahora 6 puntos críticos en peligro alto en el presente, en vez de 7.

En la tabla, el primer umbral aparece en 0,05 m porque la búsqueda no lo distingue (ver abajo). Para `b3p_c0` la búsqueda propone 0,30 m como segundo umbral, pero se mantuvo 0,20 m (la altura del sardinel): el κ es casi el mismo y el número de unidades en riesgo alto queda más cerca del mapa.

**Umbrales de peligro por tirante máximo:**

| Clase | Tirante máximo |
|---|---|
| Bajo | menos de 0,10 m |
| Medio | de 0,10 a 0,20 m |
| Alto | de 0,20 a 2,0 m |
| Muy alto | 2,0 m o más |

El umbral de 0,20 m corresponde a la altura de un sardinel: el agua que lo supera entra a las viviendas. El umbral bajo/medio no cambia el riesgo, porque la matriz trata igual el peligro bajo y el medio, así que se fijó en 10 cm, el encharcamiento perceptible.

**Techo de la comparación.** Si en lugar de la simulación se usa el propio mapa de peligro C-03 de la tesis, agregado por manzana y pasado por la misma matriz, el riesgo resultante coincide con C-04 con κ = 0,49 (máximo por unidad) a 0,60 (P90). La simulación llega al mismo nivel que el insumo original de la tesis. El techo no es 1 porque C-04 no sale solo de C-03 y de la vulnerabilidad que se pudo leer en el mapa.

**Escala de celda.** El acuerdo con C-03 es bajo en todas las corridas (κ en 2 clases ≈ 0,16). Es esperable: C-03 es un índice multicriterio a ~30 m que marca como peligrosas zonas amplias cercanas a los cauces y de alta acumulación, mientras que la simulación concentra el agua en las calles y los cauces.

## 7. Resultados por escenario

Los 9 escenarios se corrieron con los mismos parámetros calibrados y la corrección de patios. Solo cambian la lluvia y, con ella, los hidrogramas de entrada.

| Escenario | P24 en la Plaza | Tesis: ciudad en peligro alto | Unidades en riesgo alto: tesis (tabla / mapa) · simulación | κ por unidad | Puntos críticos en peligro alto: tesis · simulación | Área urbana > 10 cm | Área > 50 cm | Edificaciones con > 30 cm |
|---|---|---|---|---|---|---|---|---|
| Presente (1981–2020) | 37,2 mm | 21,6 % | 63 / 65 · **59** | 0,49 | 9 · **6** | 1,37 km² | 0,71 km² | 2 194 |
| CMIP5 RCP 4.5 · 2031–2060 | 42,4 mm (+14 %) | 23,4 % | 63 / 65 · **65** | 0,47 | 9 · **6** | 1,52 km² | 0,91 km² | 2 470 |
| CMIP5 RCP 4.5 · 2071–2100 | 42,6 mm (+14 %) | 24,1 % | 63 / 65 · **68** | 0,46 | 9 · **6** | 1,55 km² | 0,96 km² | 2 527 |
| CMIP5 RCP 8.5 · 2031–2060 | 45,7 mm (+23 %) | 39,1 % | 76 / 78 · **68** | 0,37 | 11 · **6** | 1,61 km² | 1,03 km² | 2 619 |
| CMIP5 RCP 8.5 · 2071–2100 | 63,6 mm (+71 %) | 97,3 % | 203 / 206 · **92** | 0,04 | 15 · **8** | 2,00 km² | 1,45 km² | 3 189 |
| CMIP6 SSP2-4.5 · 2031–2060 | 41,4 mm (+11 %) | 22,6 % | 63 / 65 · **61** | 0,48 | 9 · **6** | 1,48 km² | 0,84 km² | 2 393 |
| CMIP6 SSP2-4.5 · 2071–2100 | 50,2 mm (+35 %) | 46,3 % | 77 / 79 · **72** | 0,36 | 11 · **6** | 1,70 km² | 1,14 km² | 2 741 |
| CMIP6 SSP5-8.5 · 2031–2060 | 41,5 mm (+12 %) | 23,0 % | 63 / 65 · **63** | 0,47 | 9 · **6** | 1,49 km² | 0,87 km² | 2 420 |
| CMIP6 SSP5-8.5 · 2071–2100 | 50,7 mm (+36 %) | 48,3 % | 78 / 80 · **75** | 0,35 | 11 · **6** | 1,73 km² | 1,18 km² | 2 799 |

En la tabla, «unidades en riesgo alto» incluye las de riesgo alto y muy alto, y los puntos críticos de la simulación son los que tienen al menos 0,20 m a 30 m o menos. Las edificaciones de la simulación son las que tienen más de 30 cm de agua al pie. La tesis cuenta, en cambio, las edificaciones de las unidades en riesgo alto (2 606 en el presente), así que esa columna solo indica el orden de magnitud.

### 7.1 Lectura de los resultados

**1. La simulación responde de forma gradual, y crece más la profundidad que la extensión.**

| Escenarios | Aumento de la lluvia | Área urbana con más de 10 cm | Área con más de 50 cm |
|---|---|---|---|
| Presente | — | 1,37 km² | 0,71 km² |
| RCP 4.5 (ambos periodos) y CMIP6 2031–2060 | +11 % a +14 % | +8 % a +13 % | +19 % a +36 % |
| CMIP5 RCP 8.5 2031–2060 | +23 % | +17 % | +46 % |
| CMIP6 de 2071–2100 | +35 % a +36 % | +24 % a +27 % | +61 % a +66 % |
| CMIP5 RCP 8.5 2071–2100 | +71 % | +46 % | +105 % |

Más lluvia hace más profundas, sobre todo, las zonas que ya se inundan: el cauce y sus riberas, y las calles bajas.

**2. El número de unidades en riesgo alto y su aumento coinciden con la tesis en 7 de los 9 escenarios.**

| Escenario | Tesis (tabla) | Simulación | Aumento respecto al presente (tesis · simulación) |
|---|---|---|---|
| Presente | 63 | 59 | — |
| CMIP5 RCP 4.5 2031–2060 | 63 | 65 | 0 · +6 |
| CMIP5 RCP 4.5 2071–2100 | 63 | 68 | 0 · +9 |
| CMIP5 RCP 8.5 2031–2060 | 76 | 68 | +13 · +9 |
| CMIP5 RCP 8.5 2071–2100 | 203 | 92 | +140 · +33 |
| CMIP6 SSP2-4.5 2031–2060 | 63 | 61 | 0 · +2 |
| CMIP6 SSP2-4.5 2071–2100 | 77 | 72 | +14 · +13 |
| CMIP6 SSP5-8.5 2031–2060 | 63 | 63 | 0 · +4 |
| CMIP6 SSP5-8.5 2071–2100 | 78 | 75 | +15 · +16 |

- **Coincidencia.** En 7 de los 9 escenarios la diferencia con la tabla de la tesis es de 5 unidades o menos. La simulación se calibró solo con el presente, y aun así reproduce el aumento de los dos escenarios CMIP6 de 2071–2100: +13 frente a +14 y +16 frente a +15.
- **CMIP5 RCP 8.5 2031–2060.** Queda 8 unidades por debajo.
- **Concordancia por unidad.** Lo que coincide es el total y su aumento, no siempre las mismas manzanas: la concordancia por unidad baja de 0,49 en el presente a 0,35–0,48 en los escenarios futuros.

**3. El salto de CMIP5 RCP 8.5 2071–2100.** La tesis pasa a 97,3 % de la ciudad en peligro alto y a 203 unidades en riesgo alto. Frente al presente, en el mapa C-04 cambian de clase 495 de las 887 unidades, y 141 entran en riesgo alto. En la simulación cambian 70 y entran 33. El patrón de la tesis es el de un factor desencadenante clasificado: la lluvia (D) pesa el 50 % del índice de peligro, y cuando la P24 cruza el límite de una clase sube un nivel en toda la ciudad, sin importar el relieve. La simulación concentra el aumento donde el agua se acumula.

Para el artículo hay dos opciones:

- presentar el escenario extremo con este contraste físico;
- normalizar D de forma continua en lugar de clasificarlo.

**4. Los escenarios moderados también cambian.** Con +11 % a +14 % de lluvia (RCP 4.5 y los CMIP6 de 2031–2060), los mapas de la tesis casi no cambian: suben de clase entre 0 y 5 unidades. En la simulación suben entre 8 y 23 unidades, y entre 2 y 9 entran en riesgo alto. Es la diferencia entre una respuesta continua y una por clases.

**5. Puntos críticos:**

- **PC-1, PC-8 y PC-9.** Están en la llanura del río y superan 2 m en todos los escenarios.
- **PC-10, PC-11 y PC-12.** Tienen 0,28–0,29 m en el presente y llegan a 0,62–0,78 m en RCP 8.5 2071–2100.
- **PC-7 y PC-13.** Solo pasan de 0,20 m en RCP 8.5 2071–2100 (0,26 y 0,24 m).
- **PC-2, PC-3, PC-4, PC-5, PC-14 y PC-15.** Quedan por debajo de 0,20 m en todos los escenarios.
- **PC-6.** Queda seco (0,01 m).

En estos siete últimos puntos, la inundación que registra el plan municipal probablemente depende de algo que el modelo no representa: el drenaje colapsado, una alcantarilla o un canal que no está en el plano, o escorrentía muy local. Son los primeros puntos que conviene verificar en campo.

Con la corrección de patios, PC-14 y PC-13 perdieron el agua que les llegaba de un patio vecino sin salida: en el presente, PC-14 bajó de 0,32 a 0,05 m.

**6. Dónde está el agua profunda.** En el presente:

- el 81 % del área urbana con más de 1 m de agua está a menos de 150 m del cauce;
- en las calles a más de 150 m del cauce, el tirante máximo tiene una mediana de 1 cm y un P90 de 21 cm.

Las 28 zonas con más de 1 m lejos del río son calles inundadas y los lotes conectados a ellas, depresiones del terreno del plano o surcos de escurrimiento en campo abierto. Antes de la corrección de patios había además 149 bolsones aislados con más de 30 cm dentro de las manzanas; ahora quedan 16, con 0,6 ha en total.

## 8. Uso del visor (`Tarma_ciudad_3D.html`)

- **Escenario y capa.** Elige el escenario y la capa:
  - inundación simulada en el tiempo;
  - tirante máximo;
  - peligro de la tesis (C-03);
  - riesgo de la tesis (C-04);
  - peligro simulado;
  - riesgo simulado;
  - vulnerabilidad.
- **Simular tormenta.** Reproduce la tormenta de 10:00 a 17:00. El gráfico muestra la lluvia cada 10 minutos y el área urbana inundada.
- **Fichas.** Clic en una manzana: riesgo de la tesis, vulnerabilidad, tirante simulado y riesgo simulado en los 9 escenarios. Clic en un punto crítico (PC-n): tirante y velocidad máximos. Clic en una calle: tirante, velocidad, hora del máximo y ancho de la calle según el plano.
- **Edificios por riesgo.** Tiñe cada edificio con el riesgo de su manzana.

## 9. Archivos exportados (`datos/inundacion/`)

| Archivo | Contenido |
|---|---|
| `unidades_riesgo.geojson` | 887 unidades de C-04 (WGS84). Atributos: vulnerabilidad, y por escenario el riesgo de la tesis, el riesgo simulado y el P90 del tirante |
| `puntos_criticos.geojson` | 15 puntos críticos, con tirante y velocidad máximos simulados por escenario |
| `tirante_max_<código>.tif` | Tirante máximo simulado (m), malla de 10 m, EPSG:32718 (marco del Plano Total 2025) |
| `peligro_tesis_presente_cuenca.tif` | Peligro del presente (C-03) georreferenciado en toda la cuenca (~34 m; marco OSM, a unos 5 m del marco del plano) |
| `resumen_escenarios.csv` | Lluvia, valores de la tesis y de la simulación por escenario |
| `calibracion.csv` | Corridas de calibración y su acuerdo con C-04 |

Los códigos de escenario son:

| Código | Escenario |
|---|---|
| `PRES` | Presente (1981–2020) |
| `QM1`, `QM2` | CMIP5 RCP 4.5 (2031–2060 y 2071–2100) |
| `QA1`, `QA2` | CMIP5 RCP 8.5 (2031–2060 y 2071–2100) |
| `SM1`, `SM2` | CMIP6 SSP2-4.5 (2031–2060 y 2071–2100) |
| `SA1`, `SA2` | CMIP6 SSP5-8.5 (2031–2060 y 2071–2100) |

## 10. Limitaciones

**Drenaje.** No se modela el drenaje pluvial (sumideros y colectores). El tirante simulado es el de escorrentía superficial sin drenaje. Si la red funciona, sobreestima en las calles con sumideros. Si se obstruye con sedimentos, es realista.

**Terreno:**

- El MDE interpolado de las curvas del plano no resuelve el bombeo de las calzadas ni la altura de los sardineles. Entre curvas, la interpolación puede dejar depresiones cerradas de 1–2 m junto al río (ver 7.1, punto 6).
- La sección del cauce se representa con una profundización uniforme de 1,0 m. Para precisar los desbordes del río hacen falta secciones topográficas del cauce.
- Las curvas del plano están unos 10 m más arriba que el GLO-30. Parece un datum vertical distinto: no afecta a las pendientes ni al tirante, pero conviene confirmarlo con un BM del IGN.

**Edificaciones.** Están representadas como bloques de 10 m. No se modelan muros, puertas ni el ingreso de agua a las viviendas. Los patios encerrados por los bloques se rellenan hasta su nivel de rebalse (sección 5), así que el agua que llega a un patio se considera desaguada a la calle. Un patio solo se inunda si se inunda la calle de la que recibe agua.

**Depresiones del terreno.** Los badenes de las calles y las depresiones cerradas del MDE del plano se conservan. Algunas pueden ser artefactos de la interpolación entre curvas, sobre todo en campo abierto en los extremos norte y sur del dominio, donde quedan charcos aislados de 1 a 3 m. Conviene verificarlas con topografía o en campo.

**Lluvia:**

- La lluvia es la de diseño de 25 años, en un hietograma de bloques alternos con el pico a las 12 h. Una tormenta convectiva corta e intensa puede producir tirantes mayores en las calles aunque deje menos volumen.
- Las pérdidas se calculan con SCS-CN con humedad antecedente normal (AMC II). Con suelo saturado (AMC III), la escorrentía crece mucho, sobre todo en las cuencas aportantes.

**Flujos de detritos.** No se simulan los huaycos ni el transporte de sedimentos. En las quebradas laterales, el peligro real puede ser mayor que el que indica el tirante de agua clara.

**Umbrales.** Los umbrales de peligro están calibrados con la clasificación de la tesis; no son una norma.

**Discrepancia en el porcentaje urbano.** El 21,6 % de ciudad en peligro alto del artículo no se reproduce con el mapa extraído (14,6 %). La comparación porcentual entre la tesis y la simulación se hace sobre la misma área: las unidades de C-04.

**Escenarios futuros.** Solo cambia la lluvia. No hay crecimiento urbano ni cambio de cobertura.

## 11. Reproducir

El código, los insumos procesados y los pasos están en `fuente/inundacion/README.md`.
