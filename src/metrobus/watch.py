## monitorizo cambios en los csv originales, en caso de cambios relanzo pipeline 

from __future__ import annotations

import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from metrobus.pipeline import main


RAW_DIR = Path("/app/data/raw")


class CSVChangeHandler(FileSystemEventHandler):
    """Ejecuta el pipeline cuando cambia un CSV."""

    def __init__(self):
        self.last_run = 0.0

    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        if path.suffix.lower() != ".csv":
            return

        # Evita varias ejecuciones consecutivas por el mismo guardado.
        now = time.time()

        if now - self.last_run < 2:
            return

        self.last_run = now

        print(f"\nCambio detectado: {path.name}")
        print("Ejecutando pipeline...\n")

        try:
            main()
            print("\nPipeline actualizado correctamente.")
        except Exception as exc:
            print(f"\nERROR durante el pipeline: {exc}")


def main_watch():
    print("=" * 60)
    print("MetroBus ETL Watcher")
    print("=" * 60)

    # Primera carga al arrancar.
    print("\nEjecutando carga inicial...\n")
    main()

    print("\nEsperando cambios en data/raw...")
    print("Modifica cualquier CSV para relanzar el ETL.\n")

    handler = CSVChangeHandler()

    observer = Observer()

    observer.schedule(
        handler,
        str(RAW_DIR),
        recursive=False,
    )

    observer.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main_watch()