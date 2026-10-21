# Gobierno y calidad del dato --- MetroBus

## 1. Objetivo y alcance

Este documento define las reglas básicas de gobierno, calidad y uso
analítico de los datos del proyecto MetroBus. El alcance comprende las
nueve tablas del modelo: seis dimensiones (`dim_depot`, `dim_linea`,
`dim_parada`, `dim_tarifa`, `dim_vehiculo`, `dim_conductor`) y tres
tablas de hechos (`fact_viajes`, `fact_incidencias`,
`fact_mantenimiento`).

La arquitectura mantiene los CSV originales en `data/raw` sin
modificarlos. El proceso ETL extrae los datos, aplica de forma
reproducible las reglas de limpieza y validación definidas en
`src/metrobus/transform.py` y carga el resultado en PostgreSQL.
PostgreSQL constituye la capa persistente de datos preparados para SQL y
Power BI.

### Principios de gobierno

-   Trazabilidad: toda corrección debe poder relacionarse con un
    problema detectado durante el EDA.
-   Reproducibilidad: las transformaciones se realizan mediante
    código, no editando manualmente los CSV.
-   Conservación del dato original: los archivos RAW permanecen
    inmutables.
-   Integridad: se validan claves primarias, claves foráneas, rangos
    y restricciones antes de utilizar los datos analíticamente.
-   Imputación con evidencia: un valor nulo solo se reconstruye
    cuando existe información suficiente. Si no puede recuperarse de
    forma fiable, se conserva como `NULL`.
-   Outlier no implica error: un valor extremo estadístico se
    modifica únicamente cuando existe evidencia de que viola una regla
    de negocio o representa un error de captura.

La metodología aplicada es:

Problema detectado → investigar patrón/causa → comprobar si puede recuperarse → decidir → justificar → validar

------------------------------------------------------------------------

## 2. Diccionario de datos

### 2.1 `dim_depot`

Catálogo de depósitos operativos de MetroBus.

  -----------------------------------------------------------------------
  Campo                   Tipo                    Descripción
  ----------------------- ----------------------- -----------------------
  `depot_id`              INTEGER, PK             Identificador único del
                                                   depósito.

  `nombre`                VARCHAR                 Nombre del depósito.

  `barrio`                VARCHAR                 Barrio donde se
                                                  encuentra.

  `latitud`               NUMERIC                 Latitud geográfica
                                                  válida entre -90 y 90.

  `longitud`              NUMERIC                 Longitud geográfica
                                                  válida entre -180 y
                                                  180.

  `capacidad_vehiculos`   INTEGER                 Capacidad de vehículos
                                                  del depósito.
  -----------------------------------------------------------------------

### 2.2 `dim_linea`

Catálogo de líneas de autobús.

  -----------------------------------------------------------------------
  Campo                   Tipo                    Descripción
  ----------------------- ----------------------- -----------------------
  `linea_id`              INTEGER, PK             Identificador único de
                                                  línea.

  `codigo`                VARCHAR                 Código operativo de la
                                                  línea.

  `nombre`                VARCHAR                 Nombre de la línea.

  `tipo`                  VARCHAR                 Tipo de línea o
                                                  servicio.

  `km_recorrido`          NUMERIC                 Longitud programada del
                                                  recorrido en
                                                  kilómetros.

  `n_paradas`             INTEGER                 Número de paradas de la
                                                  línea.

  `frecuencia_min`        INTEGER                 Frecuencia programada
                                                  en minutos.
  -----------------------------------------------------------------------

### 2.3 `dim_parada`

Catálogo de paradas de la red.

  -----------------------------------------------------------------------
  Campo                   Tipo                    Descripción
  ----------------------- ----------------------- -----------------------
  `parada_id`             INTEGER, PK             Identificador único de
                                                  parada.

  `nombre_parada`         VARCHAR                 Nombre de la parada.

  `barrio`                VARCHAR                 Barrio de ubicación.

  `tipo`                  VARCHAR                 Tipo de parada.

  `latitud`               NUMERIC, NULL permitido Latitud. Los valores
                                                  desconocidos o
                                                  inválidos se conservan
                                                  como NULL.

  `longitud`              NUMERIC, NULL permitido Longitud. Los valores
                                                  desconocidos o
                                                  inválidos se conservan
                                                  como NULL.

  `accesible_silla`       BOOLEAN, NULL permitido Indica accesibilidad
                                                  para silla de ruedas;
                                                  NULL significa
                                                  desconocido.

  `marquesina`            BOOLEAN                 Indica si dispone de
                                                  marquesina.

  `panel_informacion`     BOOLEAN                 Indica si dispone de
                                                  panel informativo.

  `activa`                BOOLEAN                 Indica si la parada
                                                  está activa.
  -----------------------------------------------------------------------

### 2.4 `dim_tarifa`

Catálogo de títulos y tarifas.

  Campo           Tipo          Descripción
  --------------- ------------- -----------------------------------------
  `tarifa_id`     INTEGER, PK   Identificador único de tarifa.
  `tipo_titulo`   VARCHAR       Tipo de título de transporte.
  `categoria`     VARCHAR       Categoría tarifaria.
  `precio_eur`    NUMERIC       Precio unitario de referencia en euros.
  `es_abono`      BOOLEAN       Indica si el título es un abono.
  `bonificado`    BOOLEAN       Indica si la tarifa está bonificada.

### 2.5 `dim_vehiculo`

Maestro de vehículos de la flota.

  -----------------------------------------------------------------------
  Campo                   Tipo                    Descripción
  ----------------------- ----------------------- -----------------------
  `vehiculo_id`           INTEGER, PK             Identificador único del
                                                  vehículo.

  `matricula`             VARCHAR, UNIQUE         Matrícula del vehículo.

  `modelo`                VARCHAR                 Modelo del vehículo.

  `combustible`           VARCHAR                 Tecnología: Diesel,
                                                  Electrico o Hibrido.

  `capacidad_sentados`    INTEGER                 Número de plazas
                                                  sentadas.

  `capacidad_total`       INTEGER                 Capacidad total del
                                                  vehículo.

  `anno_fabricacion`      INTEGER                 Año de fabricación.

  `anno_incorporacion`    INTEGER                 Año de incorporación a
                                                  la flota.

  `km_totales`            NUMERIC                 Kilómetros acumulados
                                                  registrados.

  `depot_id`              INTEGER, FK             Depósito asignado.

  `emisiones_co2_gkm`     NUMERIC                 Emisiones de CO₂ en
                                                  g/km registradas en el
                                                  dataset.

  `en_servicio`           BOOLEAN                 Estado de servicio del
                                                  vehículo.
  -----------------------------------------------------------------------

### 2.6 `dim_conductor`

Maestro de conductores.

  -----------------------------------------------------------------------
  Campo                   Tipo                    Descripción
  ----------------------- ----------------------- -----------------------
  `conductor_id`          INTEGER, PK             Identificador único del
                                                  conductor.

  `nombre`                VARCHAR                 Nombre del conductor.

  `anno_incorporacion`    INTEGER                 Año de incorporación.

  `antiguedad_anos`       NUMERIC                 Antigüedad en años,
                                                  referenciada al año
                                                  2024.

  `turno_habitual`        VARCHAR                 Turno habitual
                                                  registrado.

  `depot_id`              INTEGER, FK             Depósito asociado.

  `formacion`             VARCHAR                 Formación registrada.

  `licencia_tipo`         VARCHAR                 Tipo de licencia.

  `activo`                BOOLEAN                 Indica si el conductor
                                                  está activo.

  `ausencias_2024`        INTEGER                 Ausencias registradas
                                                  para 2024.
  -----------------------------------------------------------------------

### 2.7 `fact_viajes`

Tabla de hechos principal. Cada fila representa un viaje.

  --------------------------------------------------------------------------
  Campo                      Tipo                    Descripción
  -------------------------- ----------------------- -----------------------
  `viaje_id`                 INTEGER, PK             Identificador único del
                                                     viaje.

  `linea_id`                 INTEGER, FK             Línea del viaje.

  `vehiculo_id`              INTEGER, FK             Vehículo utilizado.

  `conductor_id`             INTEGER, FK             Conductor asignado.

  `parada_origen_id`         INTEGER, FK             Parada de origen.

  `parada_destino_id`        INTEGER, FK             Parada de destino.

  `fecha`                    DATE                    Fecha del viaje.

  `anno`                     INTEGER                 Año.

  `mes`                      INTEGER                 Mes, entre 1 y 12.

  `dia_semana`               VARCHAR                 Día de la semana.

  `es_festivo`               BOOLEAN                 Indica si la fecha es
                                                     festiva.

  `franja_horaria`           VARCHAR                 Franja horaria del
                                                     viaje.

  `hora_salida_prog`         TIME                    Hora programada de
                                                     salida.

  `hora_salida_real`         TIME                    Hora real de salida.

  `hora_llegada_real`        TIME                    Hora real de llegada.

  `retraso_salida_min`       INTEGER                 Diferencia en minutos
                                                     entre salida programada
                                                     y real; valores
                                                     negativos pequeños
                                                     representan salida
                                                     anticipada.

  `duracion_real_min`        INTEGER                 Duración real del viaje
                                                     en minutos.

  `pasajeros_subidos`        INTEGER                 Número de pasajeros
                                                     registrados.

  `ocupacion_pct`            NUMERIC                 Ocupación expresada
                                                     entre 0 y 1.

  `km_programados`           NUMERIC                 Kilómetros programados.

  `km_recorridos`            NUMERIC                 Kilómetros realmente
                                                     recorridos.

  `viaje_completado`         BOOLEAN                 Indica si el viaje se
                                                     completó.

  `consumo`                  NUMERIC                 Consumo registrado;
                                                     debe analizarse
                                                     segmentado por
                                                     tecnología de
                                                     combustible.

  `tarifa_predominante_id`   INTEGER, FK             Tarifa predominante del
                                                     viaje. No representa la
                                                     tarifa individual de
                                                     cada pasajero.
  --------------------------------------------------------------------------

### 2.8 `fact_incidencias`

Cada fila representa una incidencia vinculada a un viaje.

  ---------------------------------------------------------------------------
  Campo                       Tipo                    Descripción
  --------------------------- ----------------------- -----------------------
  `incidencia_id`             INTEGER, PK             Identificador único de
                                                      incidencia.

  `viaje_id`                  INTEGER, FK             Viaje asociado.

  `vehiculo_id`               INTEGER, FK             Vehículo asociado.

  `conductor_id`              INTEGER, FK             Conductor asociado.

  `linea_id`                  INTEGER, FK             Línea asociada.

  `fecha`                     DATE                    Fecha de la incidencia.

  `anno`                      INTEGER                 Año.

  `mes`                       INTEGER                 Mes.

  `hora_incidencia`           TIME                    Hora de la incidencia.

  `tipo_incidencia`           VARCHAR                 Tipo concreto de
                                                      incidencia.

  `categoria`                 VARCHAR                 Categoría de la
                                                      incidencia.

  `severidad`                 VARCHAR                 Nivel de severidad
                                                      registrado.

  `requiere_retirada`         BOOLEAN                 Indica si requiere
                                                      retirada del vehículo.

  `duracion_resolucion_min`   INTEGER                 Tiempo de resolución en
                                                      minutos.

  `vehiculo_sustituto`        BOOLEAN                 Indica si se utilizó
                                                      vehículo sustituto.

  `coste_estimado_eur`        NUMERIC                 Coste estimado asociado
                                                      a la incidencia.
  ---------------------------------------------------------------------------

### 2.9 `fact_mantenimiento`

Cada fila representa una intervención de mantenimiento.

  -----------------------------------------------------------------------
  Campo                   Tipo                    Descripción
  ----------------------- ----------------------- -----------------------
  `mantenimiento_id`      INTEGER, PK             Identificador único de
                                                  intervención.

  `vehiculo_id`           INTEGER, FK             Vehículo intervenido.

  `depot_id`              INTEGER, FK             Depósito asociado.

  `fecha_entrada`         DATE                    Fecha de entrada a
                                                  mantenimiento.

  `fecha_salida`          DATE                    Fecha de salida.

  `anno`                  INTEGER                 Año.

  `mes`                   INTEGER                 Mes.

  `tipo_mantenimiento`    VARCHAR                 Tipo concreto de
                                                  mantenimiento.

  `categoria`             VARCHAR                 Categoría: Preventivo,
                                                  Correctivo, Legal o
                                                  Estetico.

  `es_correctivo`         BOOLEAN                 Indica si la
                                                  intervención es
                                                  correctiva.

  `dias_fuera_servicio`   INTEGER                 Días fuera de servicio.

  `km_en_revision`        NUMERIC                 Kilometraje registrado
                                                  en la revisión.

  `coste_eur`             NUMERIC                 Coste de la
                                                  intervención en euros.

  `proveedor`             VARCHAR                 Proveedor del
                                                  mantenimiento.

  `garantia_meses`        INTEGER                 Garantía asociada en
                                                  meses.
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 3. Data Quality Log

  --------------------------------------------------------------------------------------------------------------------------------
  \#             Tabla / campo                      Problema          Decisión aplicada                          Justificación /
                                                    detectado                                                    validación
  -------------- ---------------------------------- ----------------- ------------------------------------------ -----------------
  1              `dim_vehiculo.combustible`         Un nulo y         Imputar el vehículo afectado como `Diesel` El mismo modelo
                                                    variantes de      y normalizar a Diesel/Electrico/Hibrido.   del vehículo
                                                    capitalización.                                              afectado aparece
                                                                                                                 de forma
                                                                                                                 consistente como
                                                                                                                 Diesel.

  2              `fact_mantenimiento.categoria`     15 valores nulos. Reconstruir la categoría a partir de       Existe
                                                                      `tipo_mantenimiento`.                      correspondencia
                                                                                                                 determinista
                                                                                                                 entre tipo y
                                                                                                                 categoría:
                                                                                                                 Preventivo,
                                                                                                                 Correctivo, Legal
                                                                                                                 o Estetico.

  3              `dim_conductor.antiguedad_anos`    Un valor nulo.    Calcular `2024 - anno_incorporacion`.      El dataset se
                                                                                                                 referencia a
                                                                                                                 2024; para
                                                                                                                 incorporación
                                                                                                                 2015 el resultado
                                                                                                                 es 9 años.

  4              `dim_parada.latitud/longitud`      Coordenadas       Sustituir coordenadas fuera de rango por   Eliminar la
                                                    imposibles y una  `NULL`; no eliminar la parada.             dimensión
                                                    latitud ausente.                                             generaría
                                                                                                                 referencias
                                                                                                                 huérfanas. Los
                                                                                                                 mapas excluyen
                                                                                                                 registros sin
                                                                                                                 coordenadas
                                                                                                                 válidas.

  5              `dim_parada.accesible_silla`       Valor nulo sin    Mantener `NULL`.                           No existe otra
                                                    evidencia para                                               variable que
                                                    reconstruirlo.                                               permita inferir
                                                                                                                 accesibilidad de
                                                                                                                 forma fiable.

  6              `fact_viajes.consumo`              1.065 valores     Imputar mediante media del mismo           Mantiene contexto
                                                    nulos,            `vehiculo_id` + `linea_id` cuando existe   tecnológico y
                                                    concentrados en   historial conocido.                        operativo; no se
                                                    vehículos                                                    utiliza una media
                                                    eléctricos.                                                  global.

  7              `fact_viajes.pasajeros_subidos`    40 valores nulos. Reconstruir como                           Existe una
                                                                      `round(ocupacion_pct × capacidad_total)`   relación directa
                                                                      cuando ambos datos están disponibles.      entre ocupación y
                                                                                                                 capacidad del
                                                                                                                 vehículo.

  8              Todas las tablas / PK              Riesgo de         Validar PK nulas, PK duplicadas y filas    Resultado
                                                    duplicados o      completamente duplicadas.                  validado: 0 PK
                                                    claves nulas.                                                nulas, 0 PK
                                                                                                                 duplicadas y 0
                                                                                                                 duplicados
                                                                                                                 completos.

  9              `dim_vehiculo.anno_fabricacion`    Valor 2099 en un  Sustituir por la moda válida del mismo     2099 viola la
                                                    vehículo          modelo y año de incorporación: 2023.       coherencia
                                                    incorporado en                                               temporal
                                                    2024.                                                        fabricación ≤
                                                                                                                 incorporación.

  10             `dim_vehiculo.km_totales`          Valor negativo    Reconstruir con la suma de `km_recorridos` Un kilometraje
                                                    (-500).           observados para el vehículo: 16.584,13 km. negativo es
                                                                                                                 imposible. El
                                                                                                                 valor
                                                                                                                 reconstruido se
                                                                                                                 interpreta como
                                                                                                                 km observados en
                                                                                                                 los viajes
                                                                                                                 disponibles, no
                                                                                                                 como odómetro
                                                                                                                 histórico
                                                                                                                 completo.

  11             `fact_viajes.retraso_salida_min`   Valor anómalo     Recalcular el retraso desde hora           Tras la
                                                    -99.              programada y hora real, contemplando       corrección el
                                                                      cambio de día.                             rango es -3 a 50
                                                                                                                 min y no quedan
                                                                                                                 discrepancias con
                                                                                                                 el cálculo
                                                                                                                 temporal.

  12             `fact_mantenimiento.coste_eur`     Costes negativos. Aplicar valor absoluto a los registros     Se interpretan
                                                                      afectados.                                 como errores de
                                                                                                                 signo; el coste
                                                                                                                 económico de la
                                                                                                                 intervención no
                                                                                                                 puede ser
                                                                                                                 negativo en este
                                                                                                                 modelo.

  13             Valores extremos                   IQR detecta       Conservar cuando son compatibles con       Un outlier
                                                    extremos en       capacidad y contexto operativo.            estadístico no es
                                                    pasajeros,                                                   automáticamente
                                                    retrasos,                                                    un error. Solo se
                                                    incidencias,                                                 corrigen valores
                                                    costes y días                                                con evidencia de
                                                    fuera de                                                     invalidez.
                                                    servicio.                                                    
  ---------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------

## 4. Definición formal de KPIs

### KPI 1 --- Total de pasajeros

**Objetivo:** medir el volumen total de demanda transportada.

**Fórmula:**\
`Total Pasajeros = SUM(fact_viajes[pasajeros_subidos])`

**Unidad:** pasajeros.\
**Granularidad:** periodo, línea, vehículo u otros filtros del modelo.

### KPI 2 --- Total de viajes

**Objetivo:** medir el volumen de servicios registrados.

**Fórmula:**\
`Total Viajes = DISTINCTCOUNT(fact_viajes[viaje_id])`

**Unidad:** viajes.

### KPI 3 --- Porcentaje de puntualidad

**Objetivo:** medir la proporción de viajes cuya salida se produce con
un retraso máximo de 5 minutos.

**Fórmula:**\
`Viajes puntuales / Total viajes × 100`

Se considera puntual un viaje con `retraso_salida_min <= 5`. Las salidas
anticipadas de pocos minutos (-1, -2, -3) se consideran puntuales.

**Unidad:** porcentaje.

### KPI 4 --- Retraso medio de salida

**Objetivo:** medir el retraso promedio respecto a la hora programada.

**Fórmula:**\
`AVG(GREATEST(fact_viajes[retraso_salida_min], 0))`

**Unidad:** minutos.

El promedio se calcula sobre todos los viajes; las salidas anticipadas y
puntuales aportan cero minutos, por lo que no compensan retrasos de otros
viajes. La puntualidad se mide por separado con el umbral definido en el
KPI 3.

### KPI 5 --- Total de incidencias

**Objetivo:** medir el volumen de incidencias operativas registradas.

**Fórmula:**\
`DISTINCTCOUNT(fact_incidencias[incidencia_id])`

**Unidad:** incidencias.

### KPI 6 --- Incidencias por 1.000 viajes

**Objetivo:** normalizar el número de incidencias respecto al volumen de
operación.

**Fórmula:**\
`Total Incidencias × 1.000 / Total Viajes`

**Unidad:** incidencias por 1.000 viajes.

### KPI 7 --- Coste de mantenimiento

**Objetivo:** medir el coste económico total de las intervenciones de
mantenimiento.

**Fórmula:**\
`SUM(fact_mantenimiento[coste_eur])`

**Unidad:** euros.

### KPI 8 --- Días fuera de servicio

**Objetivo:** medir el impacto del mantenimiento sobre la disponibilidad
de la flota.

**Fórmula:**\
`SUM(fact_mantenimiento[dias_fuera_servicio])`

**Unidad:** días.

### KPI complementario --- Ingresos estimados

**Objetivo:** obtener una aproximación analítica del valor económico
asociado a los viajes.

**Fórmula conceptual:**\
`SUM(pasajeros_subidos × precio de la tarifa predominante del viaje)`

**Unidad:** euros estimados.

**Limitación:** `tarifa_predominante_id` identifica únicamente la tarifa
predominante de cada viaje. No existe información de la tarifa
individual utilizada por cada pasajero. Por ello este indicador debe
denominarse **Ingresos estimados** y no facturación o ingresos reales.

------------------------------------------------------------------------

## 5. Trazabilidad y responsabilidades

Para este proyecto académico, la responsabilidad del dato se organiza
por capa:

  -----------------------------------------------------------------------
  Capa                                Función
  ----------------------------------- -----------------------------------
  `data/raw`                          Fuente original. No se modifica.

  `01_eda.ipynb`                      Perfilado, detección de anomalías y
                                      justificación de decisiones.

  `src/metrobus/transform.py`         Implementación reproducible de las
                                      reglas de limpieza y validación.

  `sql/schema.sql`                    Contrato estructural: tipos, PK,
                                      FK, restricciones e índices.

  PostgreSQL                          Persistencia de los datos
                                      preparados para consumo analítico.

  `02_sql.sql`                        Consultas y validaciones de
                                      negocio.

  Power BI                            Modelo semántico, KPIs y
                                      visualización.

  `03_gobierno.md`                    Documentación de definiciones,
                                      reglas y decisiones de calidad.
  -----------------------------------------------------------------------


## 6. Limitaciones de uso

Los resultados deben interpretarse dentro del alcance del dataset
disponible. No deben inferirse relaciones causales únicamente a partir
de asociaciones descriptivas.

El consumo debe compararse teniendo en cuenta la tecnología de
combustible, ya que las magnitudes no son necesariamente comparables
entre Diesel, Electrico e Hibrido.

Las coordenadas desconocidas se mantienen como `NULL`, por lo que las
visualizaciones geográficas pueden contener menos paradas que el modelo
completo.

Los ingresos calculados a partir de la tarifa predominante son
estimaciones y no representan transacciones individuales ni facturación
contable real.

Los viajes abarcan 2022--2024, mientras que mantenimiento incluye 47
intervenciones registradas en 2025. Ese último año es parcial y no debe
compararse con años completos como si tuviera la misma exposición.
El promedio anual de días fuera de servicio incluye todos los vehículos
de la dimensión, asignando cero a los que no tuvieron intervenciones ese
año. El modelo no conserva altas/bajas históricas de la flota, por lo que
el denominador no representa una flota activa historizada.
Asimismo, el coste de mantenimiento por kilómetro es descriptivo: no
ajusta por antigüedad, intensidad de uso ni mezcla de intervenciones, por
lo que no demuestra por sí solo una diferencia de eficiencia entre
tecnologías.


## 7. Criterio de aceptación de calidad

El dataset se considera preparado para análisis cuando:

-   las claves primarias son únicas y no nulas;
-   no existen relaciones huérfanas en las FK definidas;
-   las restricciones de rango y dominio se cumplen;
-   las anomalías corregibles han sido tratadas mediante reglas
    reproducibles;
-   los valores desconocidos sin evidencia suficiente se mantienen
    explícitamente como `NULL`;
-   los valores extremos válidos se conservan;
-   PostgreSQL acepta la carga conforme a `sql/schema.sql`;
-   las definiciones de KPI utilizadas en SQL y Power BI mantienen el
    mismo significado de negocio.
