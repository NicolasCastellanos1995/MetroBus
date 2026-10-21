## monitorizo cambios en los csv originales, en caso de cambios relanzo pipeline 

from __future__ import annotations

from threading import Event
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import RAW_DIR
from metrobus.pipeline import main


class CSVChangeHandler(FileSystemEventHandler):
    """Marca cambios CSV para procesarlos tras una pausa de escritura."""

    def __init__(self):
        self.change_detected = Event()

    def on_modified(self, event):
        self._mark_change(event, event.src_path)

    def on_created(self, event):
        self._mark_change(event, event.src_path)

    def on_deleted(self, event):
        self._mark_change(event, event.src_path)

    def on_moved(self, event):
        self._mark_change(event, event.dest_path)

    def _mark_change(self, event, path):
        if event.is_directory or Path(path).suffix.lower() != ".csv":
            return

        self.change_detected.set()


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
            if not handler.change_detected.wait(timeout=1):
                continue

            # Espera a que terminen los guardados consecutivos antes de
            # volver a cargar todos los CSV.
            handler.change_detected.clear()
            while handler.change_detected.wait(timeout=2):
                handler.change_detected.clear()

            print("\nCambio detectado en data/raw.")
            print("Ejecutando pipeline...\n")

            try:
                main()
                print("\nPipeline actualizado correctamente.")
            except Exception as exc:
                print(f"\nERROR durante el pipeline: {exc}")

    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main_watch()