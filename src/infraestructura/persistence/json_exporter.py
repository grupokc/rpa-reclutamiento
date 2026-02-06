import json
import os

from src.domain.interfaces import DataExporter
from src.domain.models import CandidateSchema
from src.infraestructura.logging import Logger, ConsoleLogHandler


class JsonExporter(DataExporter):
    def __init__(self):
        self.logger = Logger(handlers=[ConsoleLogHandler()])

    def save(self, data: list[CandidateSchema], filename: str) -> None:
        self.logger.info(
            "save",
            f"Guardando {len(data)} registros en {filename}..."
        )
        try:
            data_dicts = [candidate.model_dump() for candidate in data]
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data_dicts, f, indent=4, ensure_ascii=False)
            self.logger.info(
                "save",
                "Guardado exitoso."
            )
        except Exception as e:
            self.logger.error(
                "save",
                f"Error al guardar JSON: {e}"
            )
            raise

    def load(self, filename: str) -> list[dict]:
        """Carga datos de un archivo JSON existente."""
        if not os.path.exists(filename):
            return []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error("load", f"Error cargando JSON {filename}: {e}")
            return []

    def append_jsonl(self, data: list[CandidateSchema | dict], filename: str) -> None:
        """
        Agrega datos a un archivo JSONL (JSON Lines).
        Cada línea es un objeto JSON independiente.
        Ideal para grandes volúmenes de datos.
        """
        if not data:
            return

        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "a", encoding="utf-8") as f:
                for item in data:
                    # Soportar tanto objetos Pydantic como dicts
                    if hasattr(item, "model_dump"):
                        line = item.model_dump()
                    else:
                        line = item
                    
                    f.write(json.dumps(line, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error("append_jsonl", f"Error escribiendo en {filename}: {e}")
            raise

    def load_jsonl(self, filename: str) -> list[dict]:
        """
        Carga todos los registros de un archivo JSONL.
        """
        if not os.path.exists(filename):
            return []
        
        results = []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except json.JSONDecodeError:
                            self.logger.warning("load_jsonl", f"Error de parseo en línea {i+1} de {filename}")
            return results
        except Exception as e:
            self.logger.error("load_jsonl", f"Error leyendo {filename}: {e}")
            return []
