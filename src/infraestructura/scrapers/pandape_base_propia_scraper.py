from playwright.sync_api import sync_playwright
import time
import os
from src.infraestructura.scrapers.pandape_scraper import PandapeScraper
from src.domain.models import CandidateSchema

class PandapeBasePropiaScraper(PandapeScraper):
    """
    Scraper especializado para extraer candidatos de la 'Base Propia' en Pandape.
    Hereda la autenticación y lógica base de PandapeScraper.
    """    
    def extract(self, limit: int = 100) -> list[CandidateSchema]:
        """
        Extracción específica para Base Propia.
        """
        extracted_data = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            try:
                base_url = os.getenv("PANDAPE_URL")
                self.logger.info("extract", "Abriendo navegador...")
                page.goto(base_url)
                time.sleep(5)
                self.logger.info(
                    "extract",
                    "Página cargada exitosamente."
                )
                self._login(page)
                self.logger.info(
                    "extract",
                    "Login exitoso."
                )
                time.sleep(2)
                
                # Navegar a la URL específica de Base Propia
                candidates_url = os.getenv("PANDAPE_CANDIDATES_URL") 
                # Si no está definida, usar un fallback o error
                if not candidates_url:
                     self.logger.error("extract", "PANDAPE_CANDIDATES_URL no definida.")
                     return []

                page.goto(candidates_url)
                time.sleep(2)

                page.click(self.SELECTORS["extract"]["noResultadosDropdown"])
                self.logger.info(
                    "extract",
                    "Dropdown de resultados abierto."
                )
                time.sleep(1)
                page.click(self.SELECTORS["extract"]["option100"])
                self.logger.info(
                    "extract",
                    "Opción 100 resultados seleccionada."
                )
                time.sleep(2)
                self._obtain_html(page)
                
                # TODO: Implementar lógica para separar los candidatos en chunks 
                # pandapé solo permite ver 10000 candidatos

                for i in range(3):
                    try:
                        self.logger.info(
                            "extract",
                            f"Extrayendo candidatos de la página {page.url}"
                        )
                        
                        candidates = self._extract_candidates(page)
                        self.logger.info(
                            "extract",
                            f"Extracción exitosa. Candidatos encontrado: {len(candidates)}"
                        )
                        extracted_data.extend(candidates)

                        if not self._has_next_page(page):
                            self.logger.info(
                                "extract",
                                "No hay más páginas."
                            )
                            break

                        self._change_page(page)
                        time.sleep(2)
                        self.logger.info(
                            "extract",
                            "Cambio de página exitoso."
                        )

                    except Exception as e:
                        self.logger.error(
                            "extract",
                            f"Error al extraer candidatos: {e}"
                        )

                if extracted_data:
                    self.logger.info(
                        "extract",
                        "Iniciando fase de enriquecimiento de datos..."
                    )
                    extracted_data = self._enrich_candidates(page, extracted_data)
                    self.logger.info(
                        "extract",
                        "Enriquecimiento de datos exitoso."
                    )
                    
                    # TODO: Guardar datos (el scraper base no guarda, retorna lista)

                self.logger.info(
                    "extract",
                    "Página de candidatos extraída exitosamente."
                )

            except Exception as e:
                self.logger.error(
                    "extract",
                    f"Error general: {e}"
                )
            finally:
                self._logout(page)
                self.logger.info(
                    "extract",
                    "Logout exitoso."
                )
                browser.close()
                self.logger.info(
                    "extract",
                    "Navegador cerrado."
                )
                return extracted_data
