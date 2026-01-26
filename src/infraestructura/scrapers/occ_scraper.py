import os
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.domain.interfaces import BaseScraper
from src.domain.models import CandidateSchema
from src.infraestructura.logging import Logger, ConsoleLogHandler
from src.infraestructura.persistence.json_exporter import JsonExporter

# Cargar variables de entorno
load_dotenv()


class OCCScraper(BaseScraper):
    """
    Implementación concreta del scraper para OCC usando Playwright
    """
    SELECTORS = {
        "login": {
            "iniciar_sesion_link": '//*[@id="homehirers_inicio_signup"]',
            "username_input": 'input[data-testid="login__user"]', 
            "password_input": 'input[data-testid="login__password"]',
            "login_button": '//*[@id="login_creacioncuenta_iniciasesion"]'
        },
        "search": {
            "talento_link": 'text=Talento',
            "location_selector": '#Searchpage_Estado',
            "keyword_input": '//*[@id="Searchpage_Puesto"]',
            "search_button": 'button[data-testid="form__submit"]',
            "candidate_number_50": '//*[@id="Resultpage_Resultados50"]',
            "next_page": '//*[@id="Resultpage_PaginadorPaginaSiguiente"]'
        },
        "logout": {
            "menu_usuario": 'text=Sistemas',
            "cerrar_sesion": 'text=Cerrar sesión'
        }
    }

    def __init__(self):
        self.logger = Logger(handlers=[ConsoleLogHandler()])

    def _login(self, page) -> None:
        """
        Realiza el login en OCC usando credenciales del .env
        """
        username = os.getenv("OCC_USERNAME")
        password = os.getenv("OCC_PASSWORD")

        if not username or not password:
            self.logger.warning("login", "Credenciales de OCC no encontradas en .env. Saltando login.")
            return

        try:
            self.logger.info("login", "Iniciando proceso de login...")
            
            # Click en 'Iniciar sesión'
            if page.locator(self.SELECTORS["login"]["iniciar_sesion_link"]).is_visible():
                page.click(self.SELECTORS["login"]["iniciar_sesion_link"])
                self.logger.info("login", "Click en 'Iniciar sesión'")
                time.sleep(2)

                # Ingresar usuario
                page.fill(self.SELECTORS["login"]["username_input"], username)
                self.logger.info("login", "Usuario ingresado")
                time.sleep(2)
                
                # Ingresar contraseña
                page.fill(self.SELECTORS["login"]["password_input"], password)
                self.logger.info("login", "Contraseña ingresada")
                time.sleep(2)

                # Click en botón entrar
                page.click(self.SELECTORS["login"]["login_button"])
                self.logger.info("login", "Enviando formulario...")
                
                # Esperar navegación o carga post-login
                # page.wait_for_load_state("networkidle") # Causaba timeout
                page.wait_for_selector(self.SELECTORS["logout"]["menu_usuario"], timeout=20000)
                self.logger.info("login", "Login completado (Menu usuario visible)")
            else:
                 self.logger.warning("login", "Botón de inicio de sesión no encontrado.")

        except Exception as e:
            self.logger.error("login", f"Error durante el login: {e}")

    def _logout(self, page) -> None:
        """
        Cierra la sesión en OCC
        """
        try:
            self.logger.info("logout", "Iniciando logout.")
            
            # click en menú de usuario
            page.wait_for_selector(self.SELECTORS["logout"]["menu_usuario"], timeout=5000)
            page.click(self.SELECTORS["logout"]["menu_usuario"])
            self.logger.info("logout", "Click en menú de usuario")
            time.sleep(2)

            # click en cerrar sesión
            page.wait_for_selector(self.SELECTORS["logout"]["cerrar_sesion"], timeout=5000)
            page.click(self.SELECTORS["logout"]["cerrar_sesion"])
            self.logger.info("logout", "Click en cerrar sesión")
            time.sleep(2)

            self.logger.info("logout", "Logout completado exitosamente")
        except Exception as e:
            self.logger.error("logout", f"Error durante el logout: {e}")


    def _search(self, page, keyword: str, location: str | None, location_slugs: dict) -> None:
        """
        Navega a la URL de búsqueda y aplica filtros si es necesario
        """
        page.click(self.SELECTORS["search"]["talento_link"])
        self.logger.info("search", "Click en 'Talento'")
        time.sleep(2)

        # Aplicar filtro de ubicación si es necesario
        if location and location in location_slugs:
            slug = location_slugs[location]
            selector = self.SELECTORS["search"]["location_selector"]

            if page.locator(selector).is_visible():
                self.logger.info("search", f"Seleccionando ubicación: {location} ({slug})")
                page.select_option(selector, value=slug)
                time.sleep(3)  # Esperar recarga de resultados
            else:
                self.logger.warning("search", "Selector de ubicación no encontrado, confiando en URL.")

        # Aplicar palabras clave
        if keyword:
            try:
                page.fill(self.SELECTORS["search"]["keyword_input"], keyword)
                self.logger.info("search", f"Palabras clave ingresadas: {keyword}")
                time.sleep(2)
            except Exception as e:
                self.logger.error("search", f"Error al ingresar palabras clave: {e}")

        try:
            page.click(self.SELECTORS["search"]["search_button"])
            self.logger.info("search", "Click en 'Buscar talento'")
            time.sleep(2)
        except Exception as e:
            self.logger.error("search", f"Error al buscar talento: {e}")

        self.logger.info("search", "Página cargada exitosamente.")

        try:
            self.logger.info("search", "Cambiando a 50 resultados por página.")
            page.wait_for_selector(self.SELECTORS["search"]["candidate_number_50"], timeout=10000)
            page.click(self.SELECTORS["search"]["candidate_number_50"])
            self.logger.info("search", "50 resultados por página seleccionados exitosamente.")
            time.sleep(2)
        except Exception as e:
            self.logger.error("search", f"Error al cargar resultados: {e}")

    def _extract_card_details(self, card) -> CandidateSchema:
        """
        Extrae los detalles de una tarjeta de candidato usando selectores robustos
        basados en la estructura SVG e iconos.
        """
        try:
            # 1. URL e ID
            href = card.get("href", "")
            full_url = f"https://www.occ.com.mx{href}" if href.startswith("/") else href

            id = card.get("id", "").split("|")[-1]
            
            # 2. Contenedor principal de datos (segunda columna)
            content_col = card.select_one("div > div:nth-of-type(2)")
            if not content_col:
                return None

            # 3. Título (Primer párrafo de la columna de contenido)
            title = "Sin título"
            title_tag = content_col.find("p")
            if title_tag:
                title = title_tag.get_text(strip=True)

            # 4. Ubicación (Buscar icono #atomic__location)
            location = None
            loc_icon = content_col.select_one("svg.atomic__location")
            if loc_icon:
                # El <p> hermano del <svg> contenedor
                loc_node = loc_icon.find_next_sibling("p")
                if loc_node:
                    location = loc_node.get_text(strip=True)

            # 5. Experiencia y Educación
            # Estrategia: Buscar divs que contengan dos <p>, uno para rol y otro para fecha
            experience = []
            # Saltamos los primeros divs (header y metadata) y buscamos los siguientes
            info_blocks = content_col.find_all("div", recursive=False)[2:] 
            for block in info_blocks:
                ps = block.find_all("p")
                if len(ps) >= 1:
                    text = " - ".join([p.get_text(strip=True) for p in ps])
                    experience.append(text)
            
            education = None
            if experience:
                education = experience.pop()

            # 6. Salario (Opcional, basado en icono #atomic__cash)
            # salary = ... (Podemos añadirlo si se requiere)

            return CandidateSchema(
                id=id,
                name="Confidencial", # El nombre suele estar oculto en la vista de lista
                position=title,
                url=full_url,
                location=location,
                company=None, 
                skills=[], # No visibles en el snippet
                experience=experience,
                education=education
            )

        except Exception as e:
            self.logger.error("extract", f"Error al extraer detalles de tarjeta: {e}")
            return None

    def _extract_candidates(self, page):
        """
        Extrae los candidatos de la página actual
        """
        try:
            candidates = []
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # Encontrar links de candidatos según patrón de URL visto en screenshot
            cards = soup.select("a[href*='/empresas/candidatos/cv/']")
            self.logger.info("extract", f"Se encontraron {len(cards)} tarjetas en esta página.")

            for card in cards:
                candidato = self._extract_card_details(card)
                candidates.append(candidato)

        except Exception as e:
            self.logger.error("extract", f"Error al extraer candidatos: {e}")

        return candidates
    
    def _change_page(self, page) -> bool:
        """
        Cambia a la siguiente página. Retorna True si tuvo éxito, False si no hay más páginas.
        """
        try:
            next_button = page.locator(self.SELECTORS["search"]["next_page"])
            if next_button.is_visible(timeout=5000):
                next_button.click()
                self.logger.info("extract", "Página siguiente.")
                return True
            else:
                self.logger.info("extract", "No se encontró el botón de siguiente página. Fin de la paginación.")
                return False
        except Exception as e:
            self.logger.error("extract", f"Error al cambiar de página: {e}")
            return False

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
                self.logger.info("extract", "Navegador iniciado, accediendo a URL base...")
                # Primero vamos a la home o url base para loguearnos si es necesario
                page.goto(url)
                
                # Ejecutar Login
                self._login(page)
                
                # Ejecutar Búsqueda y Filtros
                self._search(page, keyword, location, location_slugs)

                time.sleep(2)

                seen_ids = set()

                for i in range(1, 11): # Intentar hasta 10 páginas
                    try:
                        self.logger.info("extract", f"Extrayendo página {i}")
                        time.sleep(2)
                        
                        candidates = self._extract_candidates(page)
                        
                        # Filtrar duplicados
                        new_candidates = []
                        for cand in candidates:
                            if cand.id and cand.id not in seen_ids:
                                seen_ids.add(cand.id)
                                new_candidates.append(cand)

                        if new_candidates:
                            extracted_data.extend(new_candidates)
                            self.logger.info("extract", f"Agregados {len(new_candidates)} candidatos nuevos. Total: {len(extracted_data)}")
                            
                            exporter = JsonExporter()
                            exporter.save(extracted_data, f"data/candidates_occ_{keyword.replace(' ','_')}_{location.replace(' ','_')}.json")
                        else:
                             self.logger.info("extract", "No se encontraron candidatos nuevos en esta página.")


                        time.sleep(2)
                        
                        if not self._change_page(page):
                            break

                    except Exception as e:
                        self.logger.error("extract", f"Error al extraer candidatos: {e}")
                
                

            except Exception as e:
                self.logger.error("extract", f"Error durante la navegación: {e}")
            finally:
                self._logout(page) # Cierra sesión sin importar si hubo errores
                time.sleep(2)
                browser.close()
                self.logger.info("extract", "Navegador cerrado.")

        return extracted_data