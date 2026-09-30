from .extract import extract_all
from .transform import transform_all
from .load import load_all


def main():
    print("1/3 Extrayendo CSV...")
    raw = extract_all()
    print("2/3 Transformando...")
    clean = transform_all(raw)
    print("3/3 Cargando PostgreSQL...")
    load_all(clean)
    print("Pipeline terminado.")


if __name__ == "__main__":
    main()
