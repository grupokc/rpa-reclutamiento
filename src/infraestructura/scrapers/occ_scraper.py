import time
from playwright.sync_api import sync_playwright
from src.domain.interfaces import BaseScraper
from src.domain.models import CandidateSchema
from src.infraestructura.logging import Logger, ConsoleLogHandler


class OCCScraper(BaseScraper):
    """
    Implementación concreta del scraper para OCC usando Playwright
    """
    SELECTORS = {
        "login": {
            "iniciar_sesion": '//*[@id="login-link"]/span',
            "username": '//*[@id="inputID_identifier"]',
            "password": '//*[@id="inputID_password"]',
            "button": '//*[@id="inputID_method"]'
        },
    }

    def __init__(self):
        self.logger = Logger(handlers=[ConsoleLogHandler()])

    def _login(self) -> None:
        """
        Realiza el login en OCC
        """
        pass # TODO: Implementar login

    def extract(
        self, 
        keyword: str,
        location: str | None = None
    ) -> list[CandidateSchema]:
        """
        Abre el navegador, navega a la búsqueda y cierra.
        Retorna una lista vacía por ahora
        """
        fromated_keyword = keyword.replace(" ","%20")
        url = "https://www.occ.com.mx/empresas/"

        location_slugs = {
            "CDMX": "LOC-21957",
            "Edo Mex": "LOC-60991", 
            "Nuevo León": "LOC-83091",
            "Oaxaca": "LOC-87725",
            "Querétaro": "LOC-99788"
        }

        if location and location in location_slugs:
            slug = location_slugs[location]
            url = f"https://{url}/talento/resultados?facets={slug}&from=search&q={fromated_keyword}"
        

        self.logger.info(
            "extract", 
            f"Iniciando extracción para: {keyword} en {location or 'todo México'}", 
            metadata={"url": url}
        )

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