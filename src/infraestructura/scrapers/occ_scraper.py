import os
import time
import math
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.domain.interfaces import BaseScraper
from src.domain.models import CandidateSchema, Experience
from src.infraestructura.logging import Logger, ConsoleLogHandler
from src.infraestructura.persistence.json_exporter import JsonExporter
import json

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
        },
        "popup": {
            "cerrar_popup": '//*[@id="results-page"]/div/div[1]/div[3]/div/div[2]/div[1]/div[1]/div/svg'
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
                    # Como es tarjeta, ponemos todo en position o description
                    experience.append(Experience(position=text))
            
            education = None
            if experience:
                education_obj = experience.pop()
                education = education_obj.position if education_obj else None

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


    def _parse_candidate_html(self, html_content: str) -> dict:
        """
        Parsea el HTML del perfil para extraer datos detallados.
        Prioriza la extracción de __NEXT_DATA__ (JSON) para mayor robustez.
        """
        extracted_data = {
            "name": None,
            "position": None,
            "salary": None,
            "specialty": None,
            "email": None,
            "phone": None,
            "skills": [],
            "experience": [],
            "last_updated": None
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Estrategia 1: __NEXT_DATA__ json
            next_data_script = soup.find("script", {"id": "__NEXT_DATA__"})
            if next_data_script:
                try:
                    data = json.loads(next_data_script.string)
                    # resume suele estar en props -> initialState -> resume -> resume
                    initial_state = data.get("props", {}).get("initialState", {})
                    resume_data = initial_state.get("resume", {}).get("resume", {})
                    
                    if resume_data:
                        # Extraer Datos Básicos
                        first_name = resume_data.get("name", "")
                        last_name = resume_data.get("surname", "")
                        if first_name or last_name:
                            extracted_data["name"] = f"{first_name} {last_name}".strip()
                        
                        extracted_data["position"] = resume_data.get("jobTitle")
                        extracted_data["position"] = resume_data.get("jobTitle")
                        extracted_data["salary"] = resume_data.get("salary") # A veces es un objeto o string
                        extracted_data["last_updated"] = resume_data.get("videoCvUpdateDate") or resume_data.get("updatedAt")

                        # Extraer habilidades
                        abilities = resume_data.get("abilities", [])
                        if abilities:
                            extracted_data["skills"] = [ab.get("description", "") for ab in abilities]
                            
                        # Extraer experiencia
                        experiences = resume_data.get("professionalexperiences", [])
                        if experiences:
                            exp_list = []
                            for exp in experiences:
                                start_date = exp.get("startDate", "")
                                end_date = exp.get("endDate", "") or "Actual"
                                
                                # Intentar formatear fechas (suelen venir como YYYY-MM-DD o YYYY-MM)
                                # Para simplificar, las dejamos tal cual o como las entrega el JSON
                                
                                exp_obj = Experience(
                                    position=exp.get("jobTitle", ""),
                                    company=exp.get("company", ""),
                                    start_date=start_date,
                                    end_date=end_date,
                                    description=exp.get("description", "")
                                )
                                exp_list.append(exp_obj)
                            extracted_data["experience"] = exp_list
                        
                        # Extraer Área de Especialidad
                        # A veces está en 'experienceAreas' o similar
                        areas = resume_data.get("experienceAreas", [])
                        if areas and len(areas) > 0:
                             # Tomamos la primera o concatenamos
                             extracted_data["specialty"] = areas[0].get("description", "")

                except Exception as e:
                    self.logger.warning("extract_detail", f"Error parseando __NEXT_DATA__: {e}")
            
            # ... (código existente de nombre, email, telefono, salario) ...

            # DOM Fallback para Experience
            if not extracted_data["experience"]:
                 # Buscar header "Experiencia laboral"
                 exp_header = soup.find(lambda tag: tag.name == "p" and "Experiencia laboral" in tag.get_text())
                 if exp_header:
                     # El contenedor está típicamente en un div hermano del padre o abuelo del header
                     # Basado en lo visto: header en div.c012217 -> div.c0117.c0126.c011001
                     # El contenido está en el siguiente div hermano: div.c0117.c0121
                     
                     # Subimos hasta encontrar el contenedor de la sección
                     section_container = exp_header.find_parent("div", class_=lambda x: x and "c011001" in x)
                     if section_container:
                         content_container = section_container.find_next_sibling("div")
                         if content_container:
                             # Cada item de experiencia es un div hijo directo
                             # Estructura observada: div > p(titulo), p(fechas), p(desc)
                             # A veces hay un div wrapper intermedio: container > div > div(item)
                             items = content_container.find_all("div", recursive=False)
                             
                             # Si detectamos que hay un wrapper único (un solo hijo que tiene hijos divs)
                             if len(items) == 1 and items[0].find_all("div", recursive=False):
                                 items = items[0].find_all("div", recursive=False)

                             exp_list_dom = []
                             for item in items:
                                 ps = item.find_all("p")
                                 if len(ps) >= 2:
                                     # Asumimos orden: 1. Titulo/Empresa, 2. Fechas, 3. Descripcion
                                     title_company = ps[0].get_text(strip=True)
                                     dates = ps[1].get_text(strip=True)
                                     desc = ps[2].get_text(strip=True) if len(ps) > 2 else ""
                                     
                                     # Intentar separar Titulo de Empresa si es posible (e.g. "Vendedora en GNP")
                                     parts = title_company.split(" en ", 1)
                                     if len(parts) == 2:
                                         pos = parts[0]
                                         comp = parts[1]
                                     else:
                                         pos = title_company
                                         comp = None
                                     
                                     # Separar fechas
                                     d_parts = dates.split("-")
                                     start = d_parts[0].strip() if len(d_parts) > 0 else None
                                     end = d_parts[1].strip() if len(d_parts) > 1 else None
                                     
                                     exp_list_dom.append(Experience(
                                         position=pos,
                                         company=comp,
                                         start_date=start,
                                         end_date=end,
                                         description=desc
                                     ))
                             if exp_list_dom:
                                 extracted_data["experience"] = exp_list_dom

            # Estrategia 2: DOM selectors (Backup y complemento)
            
            # Nombre H2
            if not extracted_data["name"]:
                h2_name = soup.find("h2")
                if h2_name:
                   extracted_data["name"] = h2_name.get_text(strip=True)

            # Email y Teléfono
            email_tag = soup.select_one('[data-testid="contact-email__data-cv"]')
            if email_tag:
                extracted_data["email"] = email_tag.get_text(strip=True)
                
            phone_tag = soup.select_one('[data-testid="contact-phone__data-cv"]')
            if phone_tag:
                extracted_data["phone"] = phone_tag.get_text(strip=True)
                
            # Salario si no vino en JSON (buscar texto "$")
            if not extracted_data["salary"]:
                 # Buscar el texto "Salario deseado"
                 salary_header = soup.find(lambda tag: tag.name == "p" and "Salario deseado" in tag.get_text())
                 if salary_header:
                     # Estructura: <div class="c0117..."><p>Salario deseado</p></div><div><p>$11,000</p></div>
                     # El header debe tener un padre que es hermano del div que contiene el valor
                     header_container = salary_header.find_parent("div", class_=lambda x: x and "c0117" in x)
                     if header_container:
                         # A veces necesitamos subir uno más
                         if not header_container.find_next_sibling("div"):
                              header_container = header_container.parent
                         
                         next_div = header_container.find_next_sibling("div")
                         if next_div:
                             salary_val = next_div.get_text(strip=True)
                             extracted_data["salary"] = salary_val

            # --- DOM Fallback para Skills y Especialidad ---
            # Si el JSON falló o vino vacío, buscamos por texto en el HTML
            if not extracted_data["skills"]:
                # Buscar el texto "Habilidad"
                habilidad_header = soup.find(lambda tag: tag.name == "p" and "Habilidad" in tag.get_text())
                if habilidad_header:
                    # El contenedor de etiquetas suele estar en un div hermano o cercano
                    # Subimos al contenedor de la sección y buscamos el siguiente contenedor
                    # Estructura observada:
                    # <div class="header">...<p>Habilidad</p>...</div>
                    # <div class="content"><label><p>Skill 1</p></label>...</div>
                    
                    # Intentamos buscar el siguiente div hermano del abuelo/padre
                    section_container = habilidad_header.find_parent("div", class_=lambda x: x and "c0117" in x)
                    if section_container:
                        next_div = section_container.find_next_sibling("div")
                        if next_div:
                            skills_tags = next_div.find_all("label")
                            extracted_data["skills"] = [s.get_text(strip=True) for s in skills_tags if s.get_text(strip=True)]

            if not extracted_data["specialty"]:
                # Buscar el texto "Área de especialidad"
                specialty_header = soup.find(lambda tag: tag.name == "p" and "Área de especialidad" in tag.get_text())
                if specialty_header:
                     section_container = specialty_header.find_parent("div", class_=lambda x: x and "c0117" in x)
                     if section_container:
                        next_div = section_container.find_next_sibling("div")
                        if next_div:
                            # Puede haber varias, tomamos todas concatenadas o la primera
                            specialty_tags = next_div.find_all("label")
                            specs = [s.get_text(strip=True) for s in specialty_tags if s.get_text(strip=True)]
                            if specs:
                                extracted_data["specialty"] = ", ".join(specs)

            if not extracted_data["last_updated"]:
                # Buscar texto "CV: ... - Última actividad ..." o "Actualizado ..."
                # Iteramos sobre todos los P para mayor seguridad (evitar problemas de 'string=' exacto)
                all_ps = soup.find_all("p")
                for p in all_ps:
                    # Normalizamos el texto (reemplazar saltos de línea por espacios y quitar espacios extra)
                    raw_text = p.get_text(" ", strip=True) 
                    clean_text = " ".join(raw_text.split())
                    
                    if "CV:" in clean_text and "-" in clean_text:
                        # La estructura es "CV: XXXXX - Texto de fecha"
                        parts = clean_text.split("-")
                        # Tomamos la última parte
                        candidate_last_part = parts[-1].strip()
                        # Validamos que parezca una fecha o texto de actividad
                        if len(candidate_last_part) > 2: # Mínimo algo de texto
                             extracted_data["last_updated"] = candidate_last_part
                             self.logger.info("extract_detail", f"Fecha última actividad extraída (DOM): {candidate_last_part}")
                             break

        except Exception as e:
            self.logger.error("extract_detail", f"Error general parseando HTML: {e}")
            
        return extracted_data

    def enrich_candidates(self, page, candidates: list[CandidateSchema]) -> list[CandidateSchema]:
        """
        Recibe una lista de candidatos, navega a sus URLs y completa la información.
        Usa la página (sesión) ya abierta.
        """
        enriched_list = []
        
        try:
            total = len(candidates)
            self.logger.info("enrich", f"Iniciando enriquecimiento de {total} candidatos...")

            for i, cand in enumerate(candidates):
                self.logger.info("enrich", f"Procesando {i+1}/{total}: {cand.name}")
                
                try:
                    html = self._get_candidate_html(page, cand.url)
                    if html:
                        details = self._parse_candidate_html(html)
                        
                        # Lógica de actualización:
                        # - Si encontramos nombre real, reemplazamos (incluso si no era confidencial, mejor el del perfil)
                        new_name = details.get("name")
                        if not new_name:
                             new_name = cand.name
                        
                        # - Email, Phone, Salary, Specialty
                        # - Skills y Experience (merge o replace? Replace con la data detallada es mejor)
                        
                        updated_cand = cand.model_copy(update={
                            "name": new_name,
                            "position": details.get("position") or cand.position,
                            "salary": details.get("salary") or cand.salary,
                            "specialty": details.get("specialty") or cand.specialty,
                            "email": details.get("email") or cand.email,
                            "phone": details.get("phone") or cand.phone,
                            "skills": details.get("skills") or cand.skills,
                            "experience": details.get("experience") or cand.experience,
                            "last_updated": details.get("last_updated") or cand.last_updated
                        })
                        enriched_list.append(updated_cand)
                        self.logger.info("enrich", f"Datos enriquecidos para {new_name}")
                    else:
                        enriched_list.append(cand) 
                        
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error("enrich", f"Error procesando {cand.id}: {e}")
                    enriched_list.append(cand)
                    
        except Exception as e:
            self.logger.error("enrich", f"Error global en enriquecimiento: {e}")
            return candidates 
            
        return enriched_list
    
    def _get_candidate_html(self, page, url: str) -> str | None:
        """
        Navega a la URL del candidato y obtiene el HTML completo de la página.
        """
        try:
            if not url:
                self.logger.warning("extract_detail", "URL de candidato inválida o vacía.")
                return None

            self.logger.info("extract_detail", f"Navegando al perfil: {url}")
            page.goto(url)
            
            # Esperar a que cargue el contenido principal
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                self.logger.warning("extract_detail", "Timeout esperando networkidle, intentando extraer HTML de todos modos.")

            html_content = page.content()
            self.logger.info("extract_detail", "HTML del perfil obtenido exitosamente.")
            
            return html_content

        except Exception as e:
            self.logger.error("extract_detail", f"Error al obtener HTML del candidato: {e}")
            return None
    
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
        location: str | None = None,
        limit: int = 100
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
                
                # Calcular páginas necesarias (50 por página)
                max_pages = math.ceil(limit / 50)
                self.logger.info("extract", f"Se extraerán hasta {limit} registros (aprox. {max_pages} páginas).")

                # Definir nombre de archivo único
                loc_str = location.replace(' ', '_') if location else "Todo_Mexico"
                file_name = f"data/candidates_occ_{keyword.replace(' ', '_')}_{loc_str}.json"
                exporter = JsonExporter()

                for i in range(1, max_pages + 1):
                    try:
                        self.logger.info("extract", f"Extrayendo página {i} de {max_pages}")
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
                            
                            # Guardado parcial
                            exporter.save(extracted_data, file_name)
                        else:
                             self.logger.info("extract", "No se encontraron candidatos nuevos en esta página.")


                        time.sleep(2)
                        
                        if not self._change_page(page):
                            break

                    except Exception as e:
                        self.logger.error("extract", f"Error al extraer candidatos: {e}")

            # --- Enriquecimiento al finalizar la paginación ---
                if extracted_data:
                    self.logger.info("extract", "Iniciando fase de enriquecimiento de perfiles...")
                    extracted_data = self.enrich_candidates(page, extracted_data)
                    
                    # Guardado final (Sobreescribe con datos enriquecidos)
                    exporter.save(extracted_data, file_name)
                    self.logger.info("extract", "Enriquecimiento completado y guardado.")
                
                

            except Exception as e:
                self.logger.error("extract", f"Error durante la navegación: {e}")
            finally:
                self._logout(page) # Cierra sesión sin importar si hubo errores
                time.sleep(2)
                browser.close()
                self.logger.info("extract", "Navegador cerrado.")

        return extracted_data
        