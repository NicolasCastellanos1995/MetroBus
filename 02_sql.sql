-- Hice tambien un jupyter que se conecta a mi bbdd para verificar con los datos limpios.


-- 1 Cuales son los vehículos más caros de mantener?


SELECT
    v.vehiculo_id,
    v.modelo,
    ROUND(SUM(m.coste_eur)::numeric, 2) AS coste_total_mantenimiento
FROM fact_mantenimiento m
JOIN dim_vehiculo v
    ON m.vehiculo_id = v.vehiculo_id
GROUP BY
    v.vehiculo_id,
    v.modelo
ORDER BY coste_total_mantenimiento DESC
LIMIT 15;


-- 2 Cuales son los vehículos que más mantenimientos necesitan?


SELECT
    v.vehiculo_id,
    v.modelo,
    COUNT(m.mantenimiento_id) AS numero_mantenimientos
FROM fact_mantenimiento m
JOIN dim_vehiculo v
    ON m.vehiculo_id = v.vehiculo_id
GROUP BY
    v.vehiculo_id,
    v.modelo
ORDER BY numero_mantenimientos DESC
LIMIT 15;


-- 3 Cual es la antigüedad media del personal?


SELECT
    ROUND(AVG(antiguedad_anos)::numeric, 2) AS antiguedad_media_anos
FROM dim_conductor;


-- 4 Cuantos viajes realiza un conductor al año?


SELECT
    EXTRACT(YEAR FROM v.fecha)::int AS anio,
    c.conductor_id,
    c.nombre,
    COUNT(DISTINCT v.viaje_id) AS total_viajes
FROM fact_viajes v
JOIN dim_conductor c
    ON v.conductor_id = c.conductor_id
GROUP BY
    EXTRACT(YEAR FROM v.fecha),
    c.conductor_id,
    c.nombre
ORDER BY
    anio,
    total_viajes DESC;


-- 5 Que tasa de incidencias tiene cada conductor por cada 100 viajes?

WITH viajes_por_conductor AS (
    SELECT
        EXTRACT(YEAR FROM fecha)::int AS anio,
        conductor_id,
        COUNT(DISTINCT viaje_id) AS total_viajes
    FROM fact_viajes
    GROUP BY EXTRACT(YEAR FROM fecha), conductor_id
),
incidencias_por_conductor AS (
    SELECT
        EXTRACT(YEAR FROM fecha)::int AS anio,
        conductor_id,
        COUNT(DISTINCT incidencia_id) AS total_incidencias
    FROM fact_incidencias
    GROUP BY EXTRACT(YEAR FROM fecha), conductor_id
)
SELECT
    v.anio,
    c.conductor_id,
    c.nombre,
    v.total_viajes,
    COALESCE(i.total_incidencias, 0) AS total_incidencias,
    ROUND(
        100.0 * COALESCE(i.total_incidencias, 0)
        / NULLIF(v.total_viajes, 0),
        2
    ) AS incidencias_por_100_viajes
FROM viajes_por_conductor v
JOIN dim_conductor c
    ON v.conductor_id = c.conductor_id
LEFT JOIN incidencias_por_conductor i
    ON i.anio = v.anio
    AND i.conductor_id = v.conductor_id
ORDER BY
    v.anio,
    incidencias_por_100_viajes DESC;


-- 6 Cual es el retraso medio de salida por línea?


SELECT
    l.linea_id,
    l.codigo,
    ROUND(AVG(GREATEST(v.retraso_salida_min, 0))::numeric, 2)
        AS retraso_medio_min_por_viaje,
    ROUND(
        100.0 * AVG((v.retraso_salida_min <= 5)::int)::numeric,
        2
    ) AS puntualidad_pct
FROM fact_viajes v
JOIN dim_linea l
    ON v.linea_id = l.linea_id
GROUP BY
    l.linea_id,
    l.codigo
ORDER BY retraso_medio_min_por_viaje DESC;


-- 7 Cuales son los tipos de incidentes más frecuentes?

SELECT
    tipo_incidencia,
    COUNT(*) AS total_incidencias
FROM fact_incidencias
GROUP BY tipo_incidencia
ORDER BY total_incidencias DESC;


-- 8 Cuales son las paradas de origen con mayor retraso medio de salida?

SELECT
    p.parada_id,
    p.nombre_parada,
    COUNT(DISTINCT v.viaje_id) AS total_viajes,
    ROUND(AVG(GREATEST(v.retraso_salida_min, 0))::numeric, 2)
        AS retraso_medio_min_por_viaje,
    ROUND(
        100.0 * AVG((v.retraso_salida_min <= 5)::int)::numeric,
        2
    ) AS puntualidad_pct
FROM fact_viajes v
JOIN dim_parada p
    ON v.parada_origen_id = p.parada_id
GROUP BY
    p.parada_id,
    p.nombre_parada
ORDER BY retraso_medio_min_por_viaje DESC
LIMIT 15;


-- 9 Cuantos días pasa cada vehículo al año en mantenimiento, incluyendo
--    los vehículos sin intervenciones (2025 es un periodo parcial)?


WITH periodos AS (
    SELECT
        EXTRACT(YEAR FROM fecha_entrada)::int AS anio,
        MIN(fecha_entrada) AS inicio_periodo,
        MAX(fecha_entrada) AS fin_periodo
    FROM fact_mantenimiento
    GROUP BY EXTRACT(YEAR FROM fecha_entrada)
),
dias_por_vehiculo AS (
    SELECT
        p.anio,
        p.inicio_periodo,
        p.fin_periodo,
        v.vehiculo_id,
        COALESCE(SUM(m.dias_fuera_servicio), 0) AS dias_mantenimiento
    FROM periodos p
    CROSS JOIN dim_vehiculo v
    LEFT JOIN fact_mantenimiento m
        ON m.vehiculo_id = v.vehiculo_id
        AND EXTRACT(YEAR FROM m.fecha_entrada)::int = p.anio
    GROUP BY p.anio, p.inicio_periodo, p.fin_periodo, v.vehiculo_id
)
SELECT
    d.anio,
    MIN(d.inicio_periodo) AS primera_fecha_mantenimiento,
    MAX(d.fin_periodo) AS ultima_fecha_mantenimiento,
    COUNT(*) AS vehiculos_incluidos,
    ROUND(AVG(dias_mantenimiento)::numeric, 2)
        AS promedio_dias_mantenimiento_por_vehiculo
FROM dias_por_vehiculo d
GROUP BY d.anio
ORDER BY d.anio;


-- 10 Cuantos pasajeros lleva cada línea en cada viaje en promedio?


SELECT
    l.linea_id,
    l.codigo,
    COUNT(DISTINCT v.viaje_id) AS total_viajes,
    ROUND(AVG(v.pasajeros_subidos)::numeric, 2)
        AS pasajeros_promedio_por_viaje
FROM fact_viajes v
JOIN dim_linea l
    ON v.linea_id = l.linea_id
GROUP BY
    l.linea_id,
    l.codigo
ORDER BY pasajeros_promedio_por_viaje DESC;