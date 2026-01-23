from abc import ABC, abstractmethod
from .models import CandidateSchema


class BaseScraper(ABC):
    """
    Contrato (Interfaz) para los scrapers
    Define los métodos obligatorios que deben implementar
    La capa de infraestructura implementará estos métodos
    """
    @abstractmethod
    def extract(self, keyword: str) -> list[CandidateSchema]:
        """
        Extrae una lista de candidatos basada en palabras clave
        """
        pass


class DataExporter(ABC):
    """
    Contrato (Interfaz) para la persistencia de datos
    Define los métodos obligatorios que deben implementar
    """
    @abstractmethod
    def save(self, data: list[CandidateSchema], filename: str) -> None:
        """
        Guarda los datos extraidos en el fomrto o medio especificado
        """
        pass
