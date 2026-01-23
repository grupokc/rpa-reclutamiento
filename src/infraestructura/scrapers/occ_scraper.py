import time
from playwright.sync_api import sync_playwright
from src.domain.interfaces import BaseScraper
from src.domain.models import CandidateSchema
from src.infraestructura.logging import Logger, ConsoleLogHandler


class OCCScraper(BaseScraper):
    """
    Implementación concreta del scraper para OCC usando Playwright
    """
    def __init__(self):
        self.logger = Logger(handlers=[ConsoleLogHandler()])

    def extract(self, keyword: str) -> list[CandidateSchema]:
        """
        Abre el navegador, navega a la búsqueda y cierra.
        Retorna una lista vacía por ahora
        """
        fromated_keyword = keyword.replace(" ","-")
        url = "https://www.occ.com.mx/empresas/"

        self.logger.info("extract", f"Iniciando extracción para: {keyword}", metadata={"url": url})

        extracted_data = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            try:
                self.logger.info("extract", "Navegador iniciado, accediendo a URL...")
                page.goto(url)

                time.sleep(5)

                self.logger.info("extract", "Página cargada exitosamente.")

            except Exception as e:
                self.logger.error("extract", f"Error durante la navegación: {e}")
            finally:
                browser.close()
                self.logger.info("extract", "Navegador cerrado.")

        return extracted_data