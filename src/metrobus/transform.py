"""Transformaciones reproducibles justificadas por el EDA de MetroBus."""

from __future__ import annotations

import numpy as np
import pandas as pd


REFERENCE_YEAR = 2024


PKS = {
    "dim_tarifa": "tarifa_id",
    "dim_vehiculo": "vehiculo_id",
    "fact_incidencias": "incidencia_id",
    "fact_mantenimiento": "mantenimiento_id",
    "dim_parada": "parada_id",
    "dim_linea": "linea_id",
    "dim_depot": "depot_id",
    "dim_conductor": "conductor_id",
    "fact_viajes": "viaje_id",
}


RELACIONES = [
    ("dim_vehiculo", "depot_id", "dim_depot", "depot_id"),
    ("dim_conductor", "depot_id", "dim_depot", "depot_id"),
    ("fact_viajes", "linea_id", "dim_linea", "linea_id"),
    ("fact_viajes", "vehiculo_id", "dim_vehiculo", "vehiculo_id"),
    ("fact_viajes", "conductor_id", "dim_conductor", "conductor_id"),
    ("fact_viajes", "parada_origen_id", "dim_parada", "parada_id"),
    ("fact_viajes", "parada_destino_id", "dim_parada", "parada_id"),
    ("fact_viajes", "tarifa_predominante_id", "dim_tarifa", "tarifa_id"),
    ("fact_incidencias", "viaje_id", "fact_viajes", "viaje_id"),
    ("fact_incidencias", "vehiculo_id", "dim_vehiculo", "vehiculo_id"),
    ("fact_incidencias", "conductor_id", "dim_conductor", "conductor_id"),
    ("fact_incidencias", "linea_id", "dim_linea", "linea_id"),
    ("fact_mantenimiento", "vehiculo_id", "dim_vehiculo", "vehiculo_id"),
    ("fact_mantenimiento", "depot_id", "dim_depot", "depot_id"),
]


def _mode_or_nan(s: pd.Series):
    """Devuelve la moda de una serie o NaN si no existen valores válidos."""
    m = s.dropna().mode()
    return m.iloc[0] if not m.empty else np.nan


def _minutes_between(
    programada: pd.Series,
    real: pd.Series,
) -> pd.Series:
    """
    Calcula real - programada en minutos.

    Corrige los cruces de medianoche para evitar diferencias artificiales
    cercanas a +/- 24 horas.
    """
    p = pd.to_timedelta(
        programada.astype("string") + ":00",
        errors="coerce",
    )

    r = pd.to_timedelta(
        real.astype("string") + ":00",
        errors="coerce",
    )

    diff = (r - p).dt.total_seconds() / 60

    # Corrección de cruces de medianoche.
    diff = diff.where(diff <= 720, diff - 1440)
    diff = diff.where(diff >= -720, diff + 1440)

    return diff


def _to_date_time_types(
    dfs: dict[str, pd.DataFrame],
) -> None:
    """Convierte fechas y horas a tipos compatibles con PostgreSQL."""

    date_columns = {
        "fact_viajes": ["fecha"],
        "fact_incidencias": ["fecha"],
        "fact_mantenimiento": ["fecha_entrada", "fecha_salida"],
    }

    for table, cols in date_columns.items():
        for col in cols:
            dfs[table][col] = pd.to_datetime(
                dfs[table][col],
                errors="raise",
            ).dt.date

    time_columns = {
        "fact_viajes": [
            "hora_salida_prog",
            "hora_salida_real",
            "hora_llegada_real",
        ],
        "fact_incidencias": ["hora_incidencia"],
    }

    for table, cols in time_columns.items():
        for col in cols:
            dfs[table][col] = pd.to_datetime(
                dfs[table][col],
                format="%H:%M",
                errors="raise",
            ).dt.time


def validate_all(
    dfs: dict[str, pd.DataFrame],
) -> None:
    """
    Valida las reglas esenciales del dataset limpio.

    Si alguna regla crítica falla, el ETL se detiene antes de cargar
    información inconsistente en PostgreSQL.
    """
    errors: list[str] = []

    # ---------------------------------------------------------
    # 1. Integridad de claves primarias
    # ---------------------------------------------------------

    for table, pk in PKS.items():

        if dfs[table][pk].isna().any():
            errors.append(
                f"{table}.{pk}: PK con nulos"
            )

        if dfs[table][pk].duplicated().any():
            errors.append(
                f"{table}.{pk}: PK duplicada"
            )

    # ---------------------------------------------------------
    # 2. Integridad referencial
    # ---------------------------------------------------------

    for child, fk, parent, pk in RELACIONES:

        bad = (
            dfs[child][fk].notna()
            & ~dfs[child][fk].isin(dfs[parent][pk])
        )

        if bad.any():
            errors.append(
                f"{child}.{fk}: {int(bad.sum())} FK huérfanas"
            )

    # ---------------------------------------------------------
    # 3. Vehículos
    # ---------------------------------------------------------

    v = dfs["dim_vehiculo"]

    if v["combustible"].isna().any():
        errors.append(
            "dim_vehiculo.combustible: quedan nulos"
        )

    invalid_vehicle_year = (
        v["anno_fabricacion"].notna()
        & v["anno_incorporacion"].notna()
        & (
            v["anno_fabricacion"]
            > v["anno_incorporacion"]
        )
    )

    if invalid_vehicle_year.any():
        errors.append(
            "dim_vehiculo: fabricación posterior a incorporación"
        )

    if (v["km_totales"] < 0).any():
        errors.append(
            "dim_vehiculo.km_totales: quedan negativos"
        )

    # ---------------------------------------------------------
    # 4. Paradas
    # ---------------------------------------------------------

    p = dfs["dim_parada"]

    bad_lat = (
        p["latitud"].notna()
        & ~p["latitud"].between(-90, 90)
    )

    bad_lon = (
        p["longitud"].notna()
        & ~p["longitud"].between(-180, 180)
    )

    if bad_lat.any() or bad_lon.any():
        errors.append(
            "dim_parada: coordenadas fuera de rango"
        )

    # ---------------------------------------------------------
    # 5. Mantenimiento
    # ---------------------------------------------------------

    m = dfs["fact_mantenimiento"]

    if m["categoria"].isna().any():
        errors.append(
            "fact_mantenimiento.categoria: quedan nulos"
        )

    if (m["coste_eur"] < 0).any():
        errors.append(
            "fact_mantenimiento.coste_eur: quedan negativos"
        )

    # ---------------------------------------------------------
    # 6. Viajes
    # ---------------------------------------------------------

    x = dfs["fact_viajes"]

    if x["pasajeros_subidos"].isna().any():
        errors.append(
            "fact_viajes.pasajeros_subidos: quedan nulos"
        )

    if x["consumo"].isna().any():
        errors.append(
            "fact_viajes.consumo: quedan nulos"
        )

    # ---------------------------------------------------------
    # Resultado
    # ---------------------------------------------------------

    if errors:
        raise ValueError(
            "Validación ETL fallida:\n- "
            + "\n- ".join(errors)
        )


def transform_all(
    data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """
    Aplica únicamente transformaciones justificadas durante el EDA.

    Los DataFrames originales no se modifican.
    """

    # Copia profunda para preservar los datos RAW.
    dfs = {
        name: df.copy(deep=True)
        for name, df in data.items()
    }

    # =========================================================
    # 1. DIM_VEHICULO
    # =========================================================

    v = dfs["dim_vehiculo"]

    # ---------------------------------------------------------
    # Combustible
    # ---------------------------------------------------------

    fuel_map = {
        "diesel": "Diesel",
        "electrico": "Electrico",
        "hibrido": "Hibrido",
    }

    v["combustible"] = (
        v["combustible"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map(fuel_map)
    )

    # Los nulos se reconstruyen usando la moda del mismo modelo.
    model_fuel = (
        v.groupby("modelo")["combustible"]
        .transform(_mode_or_nan)
    )

    v["combustible"] = (
        v["combustible"]
        .fillna(model_fuel)
    )

    # ---------------------------------------------------------
    # Año de fabricación
    # ---------------------------------------------------------

    invalid_year = (
        v["anno_fabricacion"].isna()
        | (v["anno_fabricacion"] < 1900)
        | (
            v["anno_fabricacion"]
            > v["anno_incorporacion"]
        )
    )

    valid = v.loc[~invalid_year]

    ref_year = (
        valid
        .groupby(
            ["modelo", "anno_incorporacion"]
        )["anno_fabricacion"]
        .agg(_mode_or_nan)
    )

    for idx in v.index[invalid_year]:

        key = (
            v.at[idx, "modelo"],
            v.at[idx, "anno_incorporacion"],
        )

        if (
            key not in ref_year.index
            or pd.isna(ref_year.loc[key])
        ):
            raise ValueError(
                "No se puede reconstruir "
                "anno_fabricacion para "
                f"vehiculo_id={v.at[idx, 'vehiculo_id']}"
            )

        v.at[idx, "anno_fabricacion"] = int(
            ref_year.loc[key]
        )

    # ---------------------------------------------------------
    # Kilómetros totales
    # ---------------------------------------------------------

    # IMPORTANTE:
    # km_totales puede recibir valores decimales al reconstruirse
    # desde fact_viajes. Lo convertimos a float ANTES de asignar
    # valores como 16584.13.
    #
    # Esto elimina el FutureWarning de pandas.
    v["km_totales"] = pd.to_numeric(
        v["km_totales"],
        errors="coerce",
    ).astype("float64")

    x = dfs["fact_viajes"]

    x["km_recorridos"] = pd.to_numeric(
        x["km_recorridos"],
        errors="coerce",
    )

    km_obs = (
        x.groupby("vehiculo_id")["km_recorridos"]
        .sum(min_count=1)
    )

    invalid_km = (
        v["km_totales"].notna()
        & (v["km_totales"] < 0)
    )

    for idx in v.index[invalid_km]:

        vid = v.at[idx, "vehiculo_id"]

        if (
            vid not in km_obs.index
            or pd.isna(km_obs.loc[vid])
        ):
            raise ValueError(
                "No se puede reconstruir "
                f"km_totales para vehiculo_id={vid}"
            )

        v.at[idx, "km_totales"] = round(
            float(km_obs.loc[vid]),
            2,
        )

    # =========================================================
    # 2. DIM_CONDUCTOR
    # =========================================================

    c = dfs["dim_conductor"]

    missing_tenure = (
        c["antiguedad_anos"].isna()
    )

    c.loc[
        missing_tenure,
        "antiguedad_anos",
    ] = (
        REFERENCE_YEAR
        - c.loc[
            missing_tenure,
            "anno_incorporacion",
        ]
    )

    # =========================================================
    # 3. DIM_PARADA
    # =========================================================

    p = dfs["dim_parada"]

    # Coordenadas imposibles se convierten en NULL.
    # La parada NO se elimina para preservar integridad
    # referencial con fact_viajes.

    invalid_lat = (
        p["latitud"].notna()
        & ~p["latitud"].between(-90, 90)
    )

    p.loc[
        invalid_lat,
        "latitud",
    ] = np.nan

    invalid_lon = (
        p["longitud"].notna()
        & ~p["longitud"].between(-180, 180)
    )

    p.loc[
        invalid_lon,
        "longitud",
    ] = np.nan

    # accesible_silla desconocido se mantiene como NULL.
    # No existe evidencia suficiente para imputarlo.

    # =========================================================
    # 4. FACT_MANTENIMIENTO
    # =========================================================

    m = dfs["fact_mantenimiento"]

    # ---------------------------------------------------------
    # Categoría
    # ---------------------------------------------------------

    known = m.loc[
        m["categoria"].notna(),
        [
            "tipo_mantenimiento",
            "categoria",
        ],
    ]

    cardinality = (
        known
        .groupby("tipo_mantenimiento")["categoria"]
        .nunique()
    )

    ambiguous = cardinality[
        cardinality > 1
    ]

    if not ambiguous.empty:
        raise ValueError(
            "Tipos de mantenimiento con "
            "categoría ambigua: "
            f"{ambiguous.index.tolist()}"
        )

    cat_map = (
        known
        .drop_duplicates("tipo_mantenimiento")
        .set_index("tipo_mantenimiento")["categoria"]
    )

    m["categoria"] = (
        m["categoria"]
        .fillna(
            m["tipo_mantenimiento"].map(cat_map)
        )
    )

    # ---------------------------------------------------------
    # Coste
    # ---------------------------------------------------------

    m["coste_eur"] = pd.to_numeric(
        m["coste_eur"],
        errors="coerce",
    ).abs()

    # =========================================================
    # 5. FACT_VIAJES
    # =========================================================

    # ---------------------------------------------------------
    # Retraso de salida
    # ---------------------------------------------------------

    recalculated_delay = _minutes_between(
        x["hora_salida_prog"],
        x["hora_salida_real"],
    )

    valid_delay = recalculated_delay.notna()

    x.loc[
        valid_delay,
        "retraso_salida_min",
    ] = (
        recalculated_delay.loc[valid_delay]
        .round()
        .astype(int)
    )

    # ---------------------------------------------------------
    # Consumo
    # ---------------------------------------------------------

    x["consumo"] = pd.to_numeric(
        x["consumo"],
        errors="coerce",
    )

    # Imputación utilizando únicamente el mismo vehículo
    # y la misma línea.
    consumption_mean = (
        x.groupby(
            ["vehiculo_id", "linea_id"]
        )["consumo"]
        .transform("mean")
    )

    missing_consumption = (
        x["consumo"].isna()
        & consumption_mean.notna()
    )

    x.loc[
        missing_consumption,
        "consumo",
    ] = consumption_mean.loc[
        missing_consumption
    ]

    # ---------------------------------------------------------
    # Pasajeros subidos
    # ---------------------------------------------------------

    # El EDA verificó que:
    #
    # pasajeros_subidos ≈ ocupacion_pct * capacidad_total
    #
    # Por tanto podemos reconstruir los valores ausentes.

    capacity = (
        v.set_index("vehiculo_id")[
            "capacidad_total"
        ]
    )

    missing_passengers = (
        x["pasajeros_subidos"].isna()
    )

    reconstructed = (
        x.loc[
            missing_passengers,
            "ocupacion_pct",
        ]
        * x.loc[
            missing_passengers,
            "vehiculo_id",
        ].map(capacity)
    ).round()

    x.loc[
        missing_passengers,
        "pasajeros_subidos",
    ] = reconstructed

    x["pasajeros_subidos"] = (
        x["pasajeros_subidos"]
        .astype("Int64")
    )

    # =========================================================
    # 6. VALIDACIÓN
    # =========================================================

    # Las validaciones se ejecutan ANTES de cargar PostgreSQL.
    validate_all(dfs)

    # =========================================================
    # 7. TIPOS SQL
    # =========================================================

    _to_date_time_types(dfs)

    return dfs