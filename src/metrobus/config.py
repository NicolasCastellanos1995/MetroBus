from pathlib import Path
import os
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
RAW_DIR = ROOT_DIR / "data" / "raw"

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "metrobus"),
    "user": os.getenv("POSTGRES_USER", "metrobus"),
    "password": os.getenv("POSTGRES_PASSWORD", "metrobus"),
}
