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
