from pathlib import Path

from sqlalchemy import URL, create_engine, text

from .config import DB_CONFIG, ROOT_DIR

LOAD_ORDER = [
    "dim_depot", "dim_linea", "dim_parada", "dim_tarifa",
    "dim_vehiculo", "dim_conductor", "fact_viajes",
    "fact_incidencias", "fact_mantenimiento",
]


def get_engine():
    c = DB_CONFIG
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=c["user"],
        password=c["password"],
        host=c["host"],
        port=c["port"],
        database=c["database"],
    )
    return create_engine(url)


def create_schema(engine=None):
    """Crea tablas, PK, FK, CHECK e índices a partir de sql/schema.sql."""
    engine = engine or get_engine()
    schema_path = Path(ROOT_DIR) / "sql" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            cur.execute(sql)
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()


def load_all(data, create_schema_if_missing=True):
    """Reemplaza el dataset en una transacción, respetando las relaciones."""
    missing = set(LOAD_ORDER) - set(data)
    if missing:
        raise KeyError(f"Faltan tablas para cargar: {sorted(missing)}")

    empty = [table_name for table_name in LOAD_ORDER if data[table_name].empty]
    if empty:
        raise ValueError(
            f"No se reemplaza la carga con tablas vacías: {sorted(empty)}"
        )

    engine = get_engine()
    if create_schema_if_missing:
        create_schema(engine)

    with engine.begin() as conn:
        # Delete child tables first. A failed load rolls back both deletes
        # and inserts, leaving the previously loaded dataset available.
        for table_name in reversed(LOAD_ORDER):
            conn.execute(text(f'DELETE FROM "{table_name}"'))

        for table_name in LOAD_ORDER:
            df = data[table_name]
            df.to_sql(
                table_name,
                conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
            )
            print(f"Cargada {table_name}: {len(df):,} filas")

        # Validación simple post-carga.
        for table_name in LOAD_ORDER:
            db_count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()
            expected = len(data[table_name])
            if db_count != expected:
                raise RuntimeError(
                    f"Conteo incorrecto en {table_name}: PostgreSQL={db_count}, esperado={expected}"
                )
