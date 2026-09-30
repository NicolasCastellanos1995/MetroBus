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


-- 5 Cuantos incidentes tiene un conductor al año?


SELECT
    EXTRACT(YEAR FROM i.fecha)::int AS anio,
    c.conductor_id,
    c.nombre,
    COUNT(DISTINCT i.incidencia_id) AS total_incidencias
FROM fact_incidencias i
JOIN dim_conductor c
    ON i.conductor_id = c.conductor_id
GROUP BY
    EXTRACT(YEAR FROM i.fecha),
    c.conductor_id,
    c.nombre
ORDER BY
    anio,
    total_incidencias DESC;


-- 6 Cual es el retraso medio de salida por línea?


SELECT
    l.linea_id,
    l.codigo,
    ROUND(AVG(v.retraso_salida_min)::numeric, 2) AS retraso_medio_min
FROM fact_viajes v
JOIN dim_linea l
    ON v.linea_id = l.linea_id
GROUP BY
    l.linea_id,
    l.codigo
ORDER BY retraso_medio_min DESC;


-- 7 Cuales son los tipos de incidentes más frecuentes?

SELECT
    tipo_incidencia,
    COUNT(*) AS total_incidencias
FROM fact_incidencias
GROUP BY tipo_incidencia
ORDER BY total_incidencias DESC;


-- 8  Cuales son las paradas de bus con mayor retraso?

SELECT
    p.parada_id,
    p.nombre_parada,
    COUNT(DISTINCT v.viaje_id) AS total_viajes,
    ROUND(AVG(v.retraso_salida_min)::numeric, 2) AS retraso_medio_min
FROM fact_viajes v
JOIN dim_parada p
    ON v.parada_origen_id = p.parada_id
GROUP BY
    p.parada_id,
    p.nombre_parada
ORDER BY retraso_medio_min DESC
LIMIT 15;


-- 9 Cuantos días pasa al año en mantenimiento un vehículo en promedio?


WITH dias_por_vehiculo AS (
    SELECT
        EXTRACT(YEAR FROM fecha_entrada)::int AS anio,
        vehiculo_id,
        SUM(dias_fuera_servicio) AS dias_mantenimiento
    FROM fact_mantenimiento
    GROUP BY
        EXTRACT(YEAR FROM fecha_entrada),
        vehiculo_id
)

SELECT
    anio,
    ROUND(AVG(dias_mantenimiento)::numeric, 2)
        AS promedio_dias_mantenimiento_por_vehiculo
FROM dias_por_vehiculo
GROUP BY anio
ORDER BY anio;


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