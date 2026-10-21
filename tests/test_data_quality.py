import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))

from metrobus.extract import extract_all
from metrobus.load import LOAD_ORDER, load_all
from metrobus.transform import transform_all, validate_all


class DataQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean = transform_all(extract_all())

    def copy_clean_data(self):
        return {
            table: frame.copy(deep=True)
            for table, frame in self.clean.items()
        }

    def test_current_dataset_passes_quality_validation(self):
        validate_all(self.copy_clean_data())

    def test_incident_attributes_match_associated_trip(self):
        data = self.copy_clean_data()
        incident = data["fact_incidencias"].iloc[0]
        other_vehicle = next(
            vehicle_id
            for vehicle_id in data["dim_vehiculo"]["vehiculo_id"]
            if vehicle_id != incident["vehiculo_id"]
        )
        data["fact_incidencias"].loc[0, "vehiculo_id"] = other_vehicle

        with self.assertRaisesRegex(ValueError, "no coincide con el viaje"):
            validate_all(data)

    def test_calendar_attributes_match_date(self):
        data = self.copy_clean_data()
        current_month = int(data["fact_viajes"].loc[0, "mes"])
        data["fact_viajes"].loc[0, "mes"] = current_month % 12 + 1

        with self.assertRaisesRegex(ValueError, "anno/mes no coincide"):
            validate_all(data)

    def test_maintenance_days_match_date_range(self):
        data = self.copy_clean_data()
        data["fact_mantenimiento"].loc[0, "dias_fuera_servicio"] += 1

        with self.assertRaisesRegex(ValueError, "dias_fuera_servicio"):
            validate_all(data)

    def test_empty_table_cannot_replace_loaded_data(self):
        data = {
            table: pd.DataFrame({"value": [1]})
            for table in LOAD_ORDER
        }
        data["fact_viajes"] = pd.DataFrame()

        with self.assertRaisesRegex(ValueError, "tablas vacías"):
            load_all(data)


if __name__ == "__main__":
    unittest.main()
