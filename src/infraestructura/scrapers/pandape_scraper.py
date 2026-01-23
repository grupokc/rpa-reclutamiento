import time
from playwright.sync_api import sync_playwright
from src.domain.interfaces import BaseScraper
from src.domain.models import CandidateSchema
from src.infraestructura.logging import Logger, ConsoleLogHandler

class PandapeScraper(BaseScraper):
    def __init__(self):
        self.logger = Logger(handlers=[ConsoleLogHandler()])

    def extract(self, keyword: str) -> list[CandidateSchema]:
        formatted_keyword = keyword.replace(" ", "%20")
        url = "https://ats.pandape.com/Company/Dashboard"
        self.logger.info(
            "extract", 
            f"Iniciando extracción en Pandape: {keyword}", 
            metadata={"url": url}
        )

        extracted_data = [] # TODO: Implementar extracción de datos
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            try:
                page.goto(url)
                time.sleep(5)
                self.logger.info(
                    "extract",
                    "Página cargada exitosamente."
                )
            except Exception as e:
                self.logger.error(
                    "extract", f"Error: {e}"
                )
            finally:
                browser.close()
                self.logger.info(
                    "extract", 
                    "Navegador cerrado."
                )

        return extracted_data
