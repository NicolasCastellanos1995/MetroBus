-- MetroBus: esquema PostgreSQL definitivo.
-- La creación es idempotente y no elimina datos existentes.

CREATE TABLE IF NOT EXISTS dim_depot (
    depot_id INTEGER PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    barrio VARCHAR(100) NOT NULL,
    latitud NUMERIC(9,6) NOT NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud NUMERIC(9,6) NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    capacidad_vehiculos INTEGER NOT NULL CHECK (capacidad_vehiculos >= 0)
);

CREATE TABLE IF NOT EXISTS dim_linea (
    linea_id INTEGER PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    km_recorrido NUMERIC(8,2) NOT NULL CHECK (km_recorrido > 0),
    n_paradas INTEGER NOT NULL CHECK (n_paradas > 0),
    frecuencia_min INTEGER NOT NULL CHECK (frecuencia_min > 0)
);

CREATE TABLE IF NOT EXISTS dim_parada (
    parada_id INTEGER PRIMARY KEY,
    nombre_parada VARCHAR(150) NOT NULL,
    barrio VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    latitud NUMERIC(9,6) NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud NUMERIC(9,6) NULL CHECK (longitud BETWEEN -180 AND 180),
    accesible_silla BOOLEAN NULL,
    marquesina BOOLEAN NOT NULL,
    panel_informacion BOOLEAN NOT NULL,
    activa BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_tarifa (
    tarifa_id INTEGER PRIMARY KEY,
    tipo_titulo VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    precio_eur NUMERIC(8,2) NOT NULL CHECK (precio_eur >= 0),
    es_abono BOOLEAN NOT NULL,
    bonificado BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_vehiculo (
    vehiculo_id INTEGER PRIMARY KEY,
    matricula VARCHAR(30) NOT NULL UNIQUE,
    modelo VARCHAR(100) NOT NULL,
    combustible VARCHAR(20) NOT NULL CHECK (combustible IN ('Diesel','Electrico','Hibrido')),
    capacidad_sentados INTEGER NOT NULL CHECK (capacidad_sentados > 0),
    capacidad_total INTEGER NOT NULL CHECK (capacidad_total >= capacidad_sentados),
    anno_fabricacion INTEGER NOT NULL CHECK (anno_fabricacion >= 1900),
    anno_incorporacion INTEGER NOT NULL,
    km_totales NUMERIC(12,2) NOT NULL CHECK (km_totales >= 0),
    depot_id INTEGER NOT NULL REFERENCES dim_depot(depot_id),
    emisiones_co2_gkm NUMERIC(8,2) NOT NULL CHECK (emisiones_co2_gkm >= 0),
    en_servicio BOOLEAN NOT NULL,
    CHECK (anno_fabricacion <= anno_incorporacion)
);

CREATE TABLE IF NOT EXISTS dim_conductor (
    conductor_id INTEGER PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    anno_incorporacion INTEGER NOT NULL,
    antiguedad_anos NUMERIC(5,1) NOT NULL CHECK (antiguedad_anos >= 0),
    turno_habitual VARCHAR(80) NOT NULL,
    depot_id INTEGER NOT NULL REFERENCES dim_depot(depot_id),
    formacion VARCHAR(100) NOT NULL,
    licencia_tipo VARCHAR(30) NOT NULL,
    activo BOOLEAN NOT NULL,
    ausencias_2024 INTEGER NOT NULL CHECK (ausencias_2024 >= 0)
);

CREATE TABLE IF NOT EXISTS fact_viajes (
    viaje_id INTEGER PRIMARY KEY,
    linea_id INTEGER NOT NULL REFERENCES dim_linea(linea_id),
    vehiculo_id INTEGER NOT NULL REFERENCES dim_vehiculo(vehiculo_id),
    conductor_id INTEGER NOT NULL REFERENCES dim_conductor(conductor_id),
    parada_origen_id INTEGER NOT NULL REFERENCES dim_parada(parada_id),
    parada_destino_id INTEGER NOT NULL REFERENCES dim_parada(parada_id),
    fecha DATE NOT NULL,
    anno INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    dia_semana VARCHAR(20) NOT NULL,
    es_festivo BOOLEAN NOT NULL,
    franja_horaria VARCHAR(50) NOT NULL,
    hora_salida_prog TIME NOT NULL,
    hora_salida_real TIME NOT NULL,
    hora_llegada_real TIME NOT NULL,
    retraso_salida_min INTEGER NOT NULL,
    duracion_real_min INTEGER NOT NULL CHECK (duracion_real_min > 0),
    pasajeros_subidos INTEGER NOT NULL CHECK (pasajeros_subidos >= 0),
    ocupacion_pct NUMERIC(7,4) NOT NULL CHECK (ocupacion_pct BETWEEN 0 AND 1),
    km_programados NUMERIC(8,2) NOT NULL CHECK (km_programados >= 0),
    km_recorridos NUMERIC(8,2) NOT NULL CHECK (km_recorridos >= 0),
    viaje_completado BOOLEAN NOT NULL,
    consumo NUMERIC(10,4) NOT NULL CHECK (consumo >= 0),
    tarifa_predominante_id INTEGER NOT NULL REFERENCES dim_tarifa(tarifa_id)
);

CREATE TABLE IF NOT EXISTS fact_incidencias (
    incidencia_id INTEGER PRIMARY KEY,
    viaje_id INTEGER NOT NULL REFERENCES fact_viajes(viaje_id),
    vehiculo_id INTEGER NOT NULL REFERENCES dim_vehiculo(vehiculo_id),
    conductor_id INTEGER NOT NULL REFERENCES dim_conductor(conductor_id),
    linea_id INTEGER NOT NULL REFERENCES dim_linea(linea_id),
    fecha DATE NOT NULL,
    anno INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    hora_incidencia TIME NOT NULL,
    tipo_incidencia VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    severidad VARCHAR(30) NOT NULL,
    requiere_retirada BOOLEAN NOT NULL,
    duracion_resolucion_min INTEGER NOT NULL CHECK (duracion_resolucion_min >= 0),
    vehiculo_sustituto BOOLEAN NOT NULL,
    coste_estimado_eur NUMERIC(12,2) NOT NULL CHECK (coste_estimado_eur >= 0)
);

CREATE TABLE IF NOT EXISTS fact_mantenimiento (
    mantenimiento_id INTEGER PRIMARY KEY,
    vehiculo_id INTEGER NOT NULL REFERENCES dim_vehiculo(vehiculo_id),
    depot_id INTEGER NOT NULL REFERENCES dim_depot(depot_id),
    fecha_entrada DATE NOT NULL,
    fecha_salida DATE NOT NULL,
    anno INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    tipo_mantenimiento VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    es_correctivo BOOLEAN NOT NULL,
    dias_fuera_servicio INTEGER NOT NULL CHECK (dias_fuera_servicio >= 0),
    km_en_revision NUMERIC(12,2) NOT NULL CHECK (km_en_revision >= 0),
    coste_eur NUMERIC(12,2) NOT NULL CHECK (coste_eur >= 0),
    proveedor VARCHAR(120) NOT NULL,
    garantia_meses INTEGER NOT NULL CHECK (garantia_meses >= 0),
    CHECK (fecha_salida >= fecha_entrada)
);

CREATE INDEX IF NOT EXISTS idx_viajes_fecha ON fact_viajes(fecha);
CREATE INDEX IF NOT EXISTS idx_viajes_linea ON fact_viajes(linea_id);
CREATE INDEX IF NOT EXISTS idx_viajes_vehiculo ON fact_viajes(vehiculo_id);
CREATE INDEX IF NOT EXISTS idx_incidencias_tipo ON fact_incidencias(tipo_incidencia);
CREATE INDEX IF NOT EXISTS idx_incidencias_fecha ON fact_incidencias(fecha);
CREATE INDEX IF NOT EXISTS idx_mantenimiento_vehiculo ON fact_mantenimiento(vehiculo_id);
CREATE INDEX IF NOT EXISTS idx_mantenimiento_fecha ON fact_mantenimiento(fecha_entrada);
