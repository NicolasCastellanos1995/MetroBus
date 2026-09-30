import pandas as pd
from .config import RAW_DIR

FILES = [
    "dim_tarifa.csv", "dim_vehiculo.csv", "fact_incidencias.csv",
    "fact_mantenimiento.csv", "dim_parada.csv", "dim_linea.csv",
    "dim_depot.csv", "dim_conductor.csv", "fact_viajes.csv",
]

def extract_all():
    data = {}
    for filename in FILES:
        path = RAW_DIR / filename
        if not path.exists() or path.stat().st_size == 0:
            raise FileNotFoundError(
                f"Falta el CSV real o está vacío: {path}. "
                "Copia los CSV originales dentro de data/raw/."
            )
        data[path.stem] = pd.read_csv(path)
    return data
