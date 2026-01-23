from typing import List
from src.domain.interfaces import BaseScraper, DataExporter
from src.domain.models import CandidateSchema
from src.infraestructura.logging import Logger, ConsoleLogHandler


class CandidateSearchService:
    """
    Servicio de aplicación que orquesta el proceso de búsqueda de candidatos
    """
    def __init__(self, exporter: DataExporter):
        self.scrapers: List[BaseScraper] = []
        self.exporter = exporter
        self.logger = Logger(handlers=[ConsoleLogHandler()])

    def add_scraper(self, scraper: BaseScraper):
        """
        Registra un scraper para ser usado en la búsqueda
        """
        self.scrapers.append(scraper)
        self.logger.info(
            "Service",
            f"Scraper registrado: {scraper.__class__.__name__}"
        )

    def search_candidates(self, keyword: str) -> List[CandidateSchema]:
        """
        Ejecuta la búsqueda de candidatos en todos los scrapers registrados,
        agrega los resultados y los mantiene
        """
        self.logger.info(
            "Service",
            f"Iniciando búsqueda para: '{keyword}'"
        )
        all_candidates: List[CandidateSchema] = []

        for scraper in self.scrapers:
            try:
                self.logger.info(
                    "Service",
                    f"Ejecutando: {scraper.__class__.__name__}..."
                )
                results = scraper.extract(keyword)
                all_candidates.extend(results)
                self.logger.info(
                    "Service",
                    f"{scraper.__class__.__name__} encontró {len(results)} candidatos."
                )
            except Exception as e:
                self.logger.error(
                    "Service",
                    f"Error en {scraper.__class__.__name__}: {e}"
                )

        self.logger.info(
            "Service",
            f"Total de candidatos encontrados: {len(all_candidates)}"
        )

        if all_candidates:
            filename = f"data/candidates_{keyword.replace(' ', '_')}.json"
            try:
                self.exporter.save(all_candidates, filename)
                self.logger.info(
                    "Service",
                    f"Resultados guardados exitosamente en: {filename}"
                )
            except Exception as e:
                self.logger.error(
                    "Service",
                    f"Fallo al guardar resultados: {e}"
                )
            
        return all_candidates
