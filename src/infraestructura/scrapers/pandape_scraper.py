import time
from playwright.sync_api import sync_playwright
from src.domain.interfaces import BaseScraper
from src.domain.models import CandidateSchema
from src.infraestructura.logging import Logger, ConsoleLogHandler
import os
from dotenv import load_dotenv

load_dotenv()

class PandapeScraper(BaseScraper):
    """
    Implementación concreta del scraper para Pandape usando Playwright
    """
    SELECTORS = {
        "login": {
            "username": '//*[@id="Username"]',
            "password": '//*[@id="Password"]',
            "submit": '//*[@id="btLogin"]'
        }
    }

    def __init__(self):
        self.logger = Logger(handlers=[ConsoleLogHandler()])

    def _login(self, page):
        """
        Realiza el login en Pandape y maneja OTP si es necesario
        """
        try:
            self.logger.info("login", "Iniciando login en Pandape...")
            # Detectar si hay campos de usuario/pass
            if page.locator(self.SELECTORS["login"]["username"]).is_visible():
                username = os.getenv("PANDAPE_USERNAME", "")
                password = os.getenv("PANDAPE_PASSWORD", "")

                page.fill(self.SELECTORS["login"]["username"], username)
                time.sleep(1)
                page.fill(self.SELECTORS["login"]["password"], password)
                time.sleep(1)
                page.click(self.SELECTORS["login"]["submit"])
                self.logger.info("login", "Credenciales enviadas.")

                # Esperar OTP
                self._waiting_for_otp(page)
            else:
                 self.logger.info("login", "No se detectó formulario de login (¿Sesión activa?).")

        except Exception as e:
            self.logger.error("login", f"Error durante el login: {e}")

    def _waiting_for_otp(self, page):
        """
        Espera a que el usuario ingrese el OTP manualmente
        """
        self.logger.info("login", "Esperando validación de OTP o acceso al Dashboard...")
        try:
            # Esperar hasta 120 segundos a que la URL cambie al Dashboard
            # Esto indica que el usuario ingresó el OTP correctamente (o no fue necesario)
            page.wait_for_url("**/Company/Dashboard", timeout=120000)
            self.logger.info("login", "Acceso al Dashboard confirmado.")
        except Exception as e:
             self.logger.warning("login", "Tiempo de espera agotado o no se detectó el Dashboard. Continuando...")

    def _logout(self, page):
        """
        Cierra sesión en el scraper
        """
        print("Por ahora un print para simular cierre de sesión y no falle el scraper")


    def extract(
        self, 
        keyword: str,
        location: str | None = None,
        limit: int = 100
    ) -> list[CandidateSchema]:
        formatted_keyword = keyword.replace(" ", "%20")
        url = "https://ats.pandape.com/Company/Dashboard"
        self.logger.info(
            "extract", 
            f"Iniciando extracción en Pandape: {keyword} en {location or 'todo México'}", 
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
                self._login(page)
                self.logger.info(
                    "extract",
                    "Login exitoso."
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
