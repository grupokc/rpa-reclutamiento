import time
import math
from playwright.sync_api import sync_playwright
from src.domain.interfaces import BaseScraper
from src.domain.models import CandidateSchema, Experience
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
            "submit": '//*[@id="btLogin"]',
            "allowCookiesModal": '//*[@id="AllowCookiesModal"]',
            "allowCookiesButton" : '//*[@id="AllowCookiesButton"]'
        },
        "search": {
            "next_page": '//*[@id="CandidateFilters"]/div/div[2]/div[3]/div[3]/a[2]'
        },
        "extract": {
            "noResultadosDropdown": '//*[@id="CandidateFilters"]/div/div[2]/div[3]/div[2]',
            "option100": '//*[@id="CandidateFilters"]/div/div[2]/div[3]/div[2]/div/a[4]',
            "inputKeyword": '//*[@id="txtCandidatesSearch"]',
            "estadoDropdown": '//*[@id="DivFiltersList"]/div[6]/div[1]/a'            
        },
        "menu": {
            "userMenu": '//*[@id="userMenu"]',
            "logout": '//*[@id="logout"]'
        },
        "candidate_card": {
            "card_container": "div.card:has(.candidate-info)",
            "name": ".candidate-name",
            "job": ".candidate-job",
            "link_primary": "a.js_lnkCandidateDetail", 
            "link_secondary": "a.candidate-name",
            "location": ".candidate-job + div > span:first-child",
            "last_updated": "span:has-text('Última actualización')",
            # Selectores ocultos en popover
            "experience_list": ".popover-custom .box-container div:has-text('Todas las experiencias') + ul li",
            "education_list": ".popover-custom .box-container div:has-text('Todas las formaciones') + ul li"
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

                if page.locator(self.SELECTORS["login"]["allowCookiesModal"]).is_visible():
                    page.click(self.SELECTORS["login"]["allowCookiesButton"])
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
            # Esperar hasta 240 segundos a que la URL cambie al Dashboard
            # Esto indica que el usuario ingresó el OTP correctamente (o no fue necesario)
            # Ya que el OTP tarda en llegar al correo
            page.wait_for_url("**/Company/Dashboard", timeout=240000)
            self.logger.info("login", "Acceso al Dashboard confirmado.")
        except Exception as e:
             self.logger.warning("login", "Tiempo de espera agotado o no se detectó el Dashboard. Continuando...")

    def _logout(self, page):
        """
        Cierra sesión en el scraper
        """
        try:
            page.goto(os.getenv("PANDAPE_LOGOUT_URL"))
            self.logger.info("logout", "Sesión cerrada exitosamente.")
        except Exception as e: self.logger.error("logout", f"Error durante el cierre de sesión: {e}") 
        
    def _extract_candidates(self, page): 
        """
        Extrae los candidatos de la página actual
        """
        try:
            candidates = []
        except:
            pass



    def _obtain_html(self, page, filename="debug_pandape.html") -> str:
        """
        Obtiene el HTML actual de la página y lo guarda en el root
        """
        try:
            content = page.content()
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.info("debug", f"HTML guardado en {filename}")
            return content
        except Exception as e:
            self.logger.error("debug", f"Error al obtener HTML: {e}")
            return ""


    def test_login(self):
        """
        Método para probar el login visualmente (debug)
        """
        url = os.getenv("PANDAPE_URL")
        self.logger.info("debug", "Iniciando prueba de login en Pandape...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(url)
                self._login(page)
                self.logger.info("debug", "Prueba finalizada. El navegador se cerrará en 10 segundos.")

                time.sleep(10)
            except Exception as e:
                self.logger.error("debug", f"Error en prueba de login: {e}")
                time.sleep(5)
            finally:
                browser.close()

    def _search_candidates(self, page, keyword, location, limit):
        try:
            # 1. Configurar cantidad de resultados
            page.click(self.SELECTORS["extract"]["noResultadosDropdown"])
            self.logger.info("search_candidates", "Dropdown de resultados abierto.")
            time.sleep(1)
            page.click(self.SELECTORS["extract"]["option100"])
            self.logger.info("search_candidates", "Opción de 100 resultados seleccionada.")
            time.sleep(2) # Esperar recarga

            # 2. Seleccionar ubicación si se especifica
            if location:
                self.logger.info("search_candidates", f"Intentando seleccionar ubicación: {location}")
                
                # Expandir filtro de 'Estado' si es necesario
                # El botón es: a[href="#filterLocations2"]
                toggle_btn = page.locator('a[href="#filterLocations2"]')
                
                # Verificar si está colapsado (tiene clase 'collapsed')
                if "collapsed" in toggle_btn.get_attribute("class"):
                    toggle_btn.click()
                    self.logger.info("search_candidates", "Filtro de Estado expandido.")
                    time.sleep(1)
                
                # Buscar el checkbox con el texto de la ubicación                
                # Mapeo de ubicaciones a VALUES (más robusto que texto)
                loc_map = {
                    "CDMX": "139_10",       # Ciudad de México DF - México
                    "Edo Mex": "139_16",    # Estado de México - México
                    "Nuevo León": "139_20", # Nuevo León - México
                    "Querétaro": "139_23",  # Querétaro - México
                    "Oaxaca": "139_21"      # Oaxaca - México
                }
                
                loc_value = loc_map.get(location)
                
                if loc_value:
                    # Selector por value
                    target_selector = f"input[value='{loc_value}'] + span.custom-control-label"
                    target_element = page.locator(target_selector)
                    
                    # Verificar si está visible. Si no, intentar "Mostrar todo"
                    # El elemento puede estar visible pero oculto por scroll, o oculto por display:none.
                    # is_visible() retorna true solo si es visible Y visible en viewport? No, solo visible.
                    # Mas bien, si está en 'display: none' parent, is_visible es False.
                    
                    if not target_element.is_visible():
                        self.logger.info("search_candidates", f"Elemento para '{location}' no visible inicialmente. Buscando botón 'Mostrar todo'...")
                        show_all_btn = page.locator('#filterLocations2 .js_showFilters')
                        
                        if show_all_btn.is_visible():
                             try:
                                show_all_btn.scroll_into_view_if_needed()
                                show_all_btn.click()
                                self.logger.info("search_candidates", "Botón 'Mostrar todo' clickeado. Esperando actualización del DOM...")
                                time.sleep(2) # Dar tiempo a que renderice
                             except Exception as e:
                                 self.logger.warning("search_candidates", f"No se pudo clickear 'Mostrar todo': {e}")
                        else:
                            self.logger.warning("search_candidates", "Botón 'Mostrar todo' no encontrado o no visible.")

                    # Refrescar el locator por si acaso (aunque son lazos, a veces ayuda mentalmente asegurar que buscamos de nuevo)
                    target_element = page.locator(target_selector)

                    # Intentar esperar a que aparezca si fue oculto
                    try:
                        target_element.wait_for(state="attached", timeout=5000)
                    except:
                        pass # Si falla, seguimos al intento de JS

                    # Scroll para asegurar que sea visible
                    try:
                        target_element.scroll_into_view_if_needed()
                        time.sleep(0.5)
                    except Exception as e:
                        self.logger.warning("search_candidates", f"No se pudo hacer scroll al elemento: {e}")

                    if target_element.is_visible():
                        target_element.click()
                        self.logger.info("search_candidates", f"Ubicación '{location}' (Value: {loc_value}) seleccionada.")
                        time.sleep(3) 
                    else:
                         # Intentar JS si elemento visual falla por solapamiento o display no estandar
                        self.logger.warning("search_candidates", f"Elemento visual para {location} no visible, intentando JS click.")
                        target_element.evaluate("el => el.click()")
                        self.logger.info("search_candidates", f"Ubicación '{location}' (Value: {loc_value}) seleccionada (JS).")
                        time.sleep(3)
                else:
                    self.logger.warning("search_candidates", f"Ubicación '{location}' no mapeada a un ID de Pandape.")


            # 3. Ingresar Keyword
            page.fill(self.SELECTORS["extract"]["inputKeyword"], keyword)
            self.logger.info("search_candidates", f"Keyword '{keyword}' ingresada.")
            time.sleep(1)
            page.press(self.SELECTORS["extract"]["inputKeyword"], "Enter") # Presionar enter para buscar
            self.logger.info("search_candidates", "Keyword ingresada y búsqueda iniciada.")
            
            time.sleep(5) # Esperar resultados
        
        except Exception as e:
            self.logger.error("search_candidates", f"Error: {e}")

    def _extract_candidates(self, page, default_location=None):
        """
        Extrae la información de los candidatos de la lista de resultados.
        Retorna una lista de diccionarios con los datos.
        """
        candidates_data = []
        try:
            # Selector general para tarjetas.
            # Pandape puede usar 'div.card' para cada item.
            cards = page.locator(self.SELECTORS["candidate_card"]["card_container"])
            count = cards.count()
            self.logger.info("extract_candidates", f"Encontradas {count} posibles tarjetas de candidatos.")
            
            for i in range(count):
                try:
                    card = cards.nth(i)
                    
                    # Nombre
                    name_el = card.locator(self.SELECTORS["candidate_card"]["name"])
                    name = name_el.inner_text().strip() if name_el.count() > 0 else "Nombre no encontrado"
                    
                    # Puesto / Titular
                    job_el = card.locator(self.SELECTORS["candidate_card"]["job"])
                    job = job_el.inner_text().strip() if job_el.count() > 0 else "Puesto no encontrado"
                    
                    # Url del perfil
                    # Buscar el primer enlace que parezca ir al detalle
                    url_el = card.locator(self.SELECTORS["candidate_card"]["link_primary"])
                    # Si no hay directo, quizás el nombre es el link
                    if url_el.count() == 0:
                         url_el = card.locator(self.SELECTORS["candidate_card"]["link_secondary"])
                    
                    url = "URL no encontrada"
                    if url_el.count() > 0:
                        href = url_el.first.get_attribute("href")
                        if href:
                            # Asegurar URL absoluta si es relativa
                            if href.startswith("/"):
                                url = f"https://ats.pandape.com{href}" # Ajustar dominio si es necesario
                            else:
                                url = href

                    # Ubicación (suele estar en un span o div secundario)
                    # No tenemos clase exacta, buscamos texto genérico o iconos
                    # A veces es .candidate-location
                    loc_el = card.locator(self.SELECTORS["candidate_card"]["location"])
                    if loc_el.count() > 0:
                        location = loc_el.inner_text().strip() 
                    else:
                        # Fallback al location search parameter si no se encuentra en la tarjeta
                        location = default_location if default_location else "Ubicación no encontrada"
                    
                    # ID Extraction
                    # Try to get from data-id attribute on the contact button or row
                    cand_id = None
                    try:
                        # Sometimes the card is wrapped in a div with data-id
                        # But here 'card' is likely the inner container.
                        # Let's check for the contact button which has data-id
                        contact_btn = card.locator(".js_ViewContact")
                        if contact_btn.count() > 0:
                            cand_id = contact_btn.first.get_attribute("data-id")
                    except:
                        pass

                    # Fallback to URL parsing if data-id not found
                    if not cand_id:
                        if "/Detail/" in url:
                            cand_id = url.split("/Detail/")[-1].split("?")[0]
                        elif "/candidate/" in url.lower():
                            cand_id = url.split("/candidate/")[-1].split("?")[0]
                    
                    # Detectar si es tarjeta de Computrabajo (Ct)
                    is_ct = "/CandidateCt/" in url or job == "Puesto no encontrado"
                    
                    # Inicializar variables dependientes del tipo de tarjeta
                    experience_list = []
                    education_str = "Sin educación detallada"

                    if is_ct:
                        if job == "Puesto no encontrado":
                            job = name # El encabezado suele ser el puesto/título
                            name = "Candidato Computrabajo" # Nombre genérico u oculto

                        edu_ct_el = card.locator(".candidate-info > div:nth-child(2)")
                        if edu_ct_el.count() > 0:
                             education_str = edu_ct_el.inner_text().strip().replace("\n", " ")

                    else:
                        experience_list = []
                        exp_items = card.locator(self.SELECTORS["candidate_card"]["experience_list"])
                        count_exp = exp_items.count()
                        for j in range(count_exp):
                            try:
                                item = exp_items.nth(j)
                                # Intentar separar Puesto (span) de Empresa (texto fuera del span)
                                pos_span = item.locator("span")
                                position_exp = pos_span.inner_text().strip() if pos_span.count() > 0 else "Sin puesto"
                                
                                # Texto completo
                                full_text = item.text_content().strip()
                                # Remover el texto del puesto para dejar la empresa
                                company_exp = full_text.replace(position_exp, "").strip()
                                
                                experience_list.append(Experience(
                                    position=position_exp,
                                    company=company_exp
                                ))
                            except:
                                continue

                        education_list = []
                        edu_items = card.locator(self.SELECTORS["candidate_card"]["education_list"])
                        count_edu = edu_items.count()
                        for k in range(count_edu):
                            try:
                                item_text = edu_items.nth(k).text_content().strip()
                                if item_text:
                                    education_list.append(item_text)
                            except:
                                continue
                        
                        if education_list:
                            education_str = "\n".join(education_list)

                    # Última actualización
                    last_updated_text = "Pendiente"
                    try:
                        last_updated_el = card.locator("text=/Última actualización:/i")
                        
                        if last_updated_el.count() > 0:
                            raw_text = last_updated_el.first.inner_text().strip()
                            # Extraer lo que está después de los dos puntos
                            if ":" in raw_text:
                                last_updated_text = raw_text.split(":", 1)[1].strip()
                            else:
                                last_updated_text = raw_text.replace("Última actualización", "").strip()
                    except Exception as e:
                        self.logger.warning("extract_candidates", f"No se pudo extraer fecha actualización: {e}")

                    candidate = CandidateSchema(
                        id=cand_id,
                        name=name,
                        position=job,
                        location=location,
                        url=url,
                        experience=experience_list,
                        education=education_str,
                        # Campos adicionales
                        last_updated=last_updated_text,
                        salary="Pendiente" 
                    )
                    candidates_data.append(candidate)
                    self.logger.info("extract_candidates", f"Candidato extraído: {name} - {job}")

                except Exception as e_card:
                     self.logger.warning("extract_candidates", f"Error extrayendo tarjeta {i}: {e_card}")

        except Exception as e:
            self.logger.error("extract_candidates", f"Error crítico: {e}")
            
        return candidates_data

    def _change_page(self, page):
        try:
            next_button = page.locator(self.SELECTORS["search"]["next_page"])
            if next_button.is_visible():
                next_button.click()
                self.logger.info("extract", "Página siguiente.")
                return True
            else:
                self.logger.info("extract", f"No se encontró la el botón de siguiente página.")
                return False
        except Exception as e:
            self.logger.error("change_page", f"Error cambiando de página: {e}")
            return False

    def _get_candidate_html(self, page, url: str) -> str | None:
        try:
            if not url:
                self.logger.warning("extract_detail", "URL de candidato inválida o vacía")
                return None
            
            self.logger.info("extract_datail", f"Navegando al perfil: {url}")
            page.goto(url)

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception as e:
                self.logger.error("extract_detail", f"Error cargando perfil: {e}")

            html_content = page.content()
            self.logger.info(
                "extract_detail",
                "HTML del perfil obtenido exitosamente"
            )

            # self._obtain_html(page)
            return html_content

        except Exception as e:
            self.logger.error("extract_detail", f"Error al obtener HTML del candidato: {e}")
            return None
                

    def _parse_candidate_detail(self, html_content: str) -> dict:
        """
        Parsea el HTML del detalle del candidato para extraer info completa.
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {
            "experience": [],
            "education": [],
            "skills": [],
            "email": None,
            "phone": None,
            "salary": None
        }

        try:
            # --- NOMBRE ---
            # Intentar extraer el nombre real del encabezado
            name_container = soup.select_one('#divCandidateName .font-3xxl')
            if name_container:
                name_text = name_container.get_text(strip=True)
                if name_text:
                    data["name"] = name_text

            # --- EXPERIENCIA ---
            exp_container = soup.find('div', id='ResumeExperiences')
            if exp_container:
                # Buscar filas de experiencia
                rows = exp_container.find_all('div', class_='row')
                for row in rows:
                    try:
                        # --- Extraer Fechas ---
                        col_date = row.find('div', class_='col-3')
                        start_date = None
                        end_date = None
                        
                        if col_date:
                            # Buscar el div con lh-180 que tiene las fechas
                            date_div = col_date.find('div', class_='lh-180')
                            if date_div:
                                date_text = date_div.get_text(separator="|", strip=True) # Usar separador para dividir mejor
                                # Esperamos algo como "Sep. 2020 -|Sep. 2024"
                                parts = date_text.split('-')
                                if len(parts) >= 1:
                                    start_date = parts[0].replace("|", "").strip()
                                if len(parts) >= 2:
                                    end_date = parts[1].replace("|", "").strip()

                        # --- Extraer Detalle ---
                        col_detail = row.find('div', class_='col-9') or row.find('div', class_='col-7') # A veces es col-7
                        
                        position = None
                        company = None
                        description = None

                        if col_detail:
                            # Título (Position)
                            title_el = col_detail.find('strong')
                            if title_el:
                                position = title_el.get_text(strip=True)
                            
                            # Empresa (Company)
                            # Intentar buscar el span dentro del div siguiente al título
                            # Estructura observada:
                            # <div><strong>Position</strong></div>
                            # <div><span>Company</span></div>
                            # <div class="c-md text-italic"><p>Description</p></div>
                            
                            # Buscar todos los divs directos
                            detail_divs = col_detail.find_all('div', recursive=False)
                            
                            # El segundo div suele tener la empresa
                            if len(detail_divs) > 1:
                                company_el = detail_divs[1].find('span')
                                if company_el:
                                    company = company_el.get_text(strip=True)
                                else:
                                    # Fallback: texto limpio del segundo div
                                    company = detail_divs[1].get_text(strip=True)

                            # Descripción
                            # Buscar clase específica .text-break-word o el div italico
                            desc_el = col_detail.find('p', class_='text-break-word')
                            if desc_el:
                                description = desc_el.get_text(strip=True)
                            
                            data["experience"].append(Experience(
                                position=position,
                                company=company,
                                start_date=start_date,
                                end_date=end_date,
                                description=description
                            ))
                    except Exception as ex_row:
                        self.logger.warning("parse_detail", f"Error parseando fila de experiencia: {ex_row}")
                        continue

            # --- EDUCACIÓN ---
            # El ID suele ser ResumeStudies o buscar por header
            edu_container = soup.find('div', id='ResumeStudies')
            if not edu_container:
                 # Fallback: buscar contenedor que tenga header "Educación"
                 headers = soup.find_all(string=re.compile("Educación", re.IGNORECASE))
                 for h in headers:
                     parent = h.find_parent('div', class_='resume-item')
                     if parent:
                         edu_container = parent
                         break
            
            if edu_container:
                rows = edu_container.find_all('div', class_='row')
                for row in rows:
                    try:
                        text = row.get_text(separator=" ", strip=True)
                        if text:
                            data["education"].append(text)
                    except:
                        continue

            # --- SKILLS ---
            skills_container = soup.find('div', id='ResumeSkills')
            if skills_container:
                tags = skills_container.find_all('div', class_='custom-tag')
                for tag in tags:
                    data["skills"].append(tag.get_text(strip=True))

            # --- CONTACTO (Email/Teléfono) ---
            # Buscar en todo el documento patrones de email si no hay selectores claros
            # El dump mostró "Email" 4 veces, quizás está en un bloque oculto o visible
            # Intentar buscar mailto
            if not data["email"]:
                mailto = soup.select_one('a[href^="mailto:"]')
                if mailto:
                    data["email"] = mailto.get_text(strip=True)

            # --- SALARIO ---
            salary_container = soup.find('div', id='Salary')
            if salary_container:
                # El salario está en col-9
                # <div> $ <span>7,500</span> (Mensual bruto) </div>
                col_9 = salary_container.find('div', class_='col-9')
                if col_9:
                     data["salary"] = col_9.get_text(separator=" ", strip=True)
            
        except Exception as e:
            self.logger.error("parse_detail", f"Error parseando detalle: {e}")

        return data

    def _enrich_candidates(self, page, candidates_data):
        enriched_candidates = []

        try:
            total = len(candidates_data)
            self.logger.info("enrich", f"Iniciando enriquecimiento de {total} candidatos.")

            for i, card in enumerate(candidates_data):
                self.logger.info("enrich", f"Procesando {i+1}/{total}: {card.name}")

                try:
                    self._obtain_html(page)
                    if "/CandidateCt/" in card.url or not card.experience:
                        html = self._get_candidate_html(page, card.url)

                        if html:
                            detail_data = self._parse_candidate_detail(html)
                            
                            # Preparar diccionario de actualizaciones
                            update_data = {}
                            
                            # Actualizar nombre si se extrajo y es diferente
                            if detail_data.get("name") and detail_data["name"] != card.name:
                                update_data["name"] = detail_data["name"]

                            if detail_data["experience"]:
                                update_data["experience"] = detail_data["experience"]
                                
                                try:
                                    latest_exp = detail_data["experience"][0]
                                    if latest_exp.position:
                                        curr_pos = latest_exp.position.strip()
                                        if curr_pos and len(curr_pos) > 2:
                                            update_data["position"] = curr_pos
                                except:
                                    pass
                            
                            if detail_data["education"]:
                                update_data["education"] = "\n".join(detail_data["education"])

                            if detail_data["skills"]:
                                update_data["skills"] = detail_data["skills"]

                            if detail_data["email"]:
                                update_data["email"] = detail_data["email"]

                            if detail_data["salary"]:
                                update_data["salary"] = detail_data["salary"]

                            # Crear nueva instancia con los datos actualizados si hubo cambios
                            if update_data:
                                card = card.model_copy(update=update_data)
                    
                    enriched_candidates.append(card)

                except Exception as e:
                    self.logger.error("enrich", f"Error enriqueciendo candidato {i+1}/{total}: {e}")
                    enriched_candidates.append(card) # Agregar sin cambios en caso de error

            return enriched_candidates
        except Exception as e:
            self.logger.error("enrich", f"Error enriqueciendo candidatos: {e}")
            return candidates_data
        

    def extract(
        self, 
        keyword: str,
        location: str | None = None,
        limit: int = 100
    ) -> list[CandidateSchema]:
        formatted_keyword = keyword.replace(" ", "%20")
        url = os.getenv("PANDAPE_URL")
        self.logger.info(
            "extract", 
            f"Iniciando extracción en Pandape: {keyword} en {location or 'todo México'}", 
            metadata={"url": url}
        )

        extracted_data = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            try:
                self.logger.info(
                    "extract",
                    "Abriendo navegador..."
                )
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
                time.sleep(2)
                cadidates_url = os.getenv("PANDAPE_COMPUTRABAJO_URL")
                self.logger.info(
                    "extract",
                    f"Navegando a URL de candidatos: {cadidates_url}"
                )
                page.goto(cadidates_url)        
                time.sleep(3)
                max_pages = math.ceil(limit / 100)

                self._search_candidates(page, keyword, location, limit)
                self.logger.info(
                    "extract",
                    "Búsqueda exitosa."
                )

                for i in range(1, max_pages + 1):
                    try:
                        self.logger.info(
                            "extract",
                            f"Extrayendo página {i} de {max_pages}"
                        )
                        # Pass the 'location' variable (from method arg) as the default_location
                        candidates = self._extract_candidates(page, default_location=location)
                        self.logger.info(
                            "extract",
                            f"Extracción exitosa. Candidatos encontrados en página {i}: {len(candidates)}"
                        )

                        extracted_data.extend(candidates)

                        if len(extracted_data) >= limit:
                            break

                        if not self._has_next_page(page):
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
                        "Iniciando fase de enriquecimiento de perfiles..."
                    )
                    extracted_data = self._enrich_candidates(page, extracted_data)

                    self.logger.info(
                        "extract",
                        "Enriquecimiento completado"
                    )

                self.logger.info(
                    "extract",
                    "Página de candidatos cargada exitosamente."
                )

            except Exception as e:
                self.logger.error(
                    "extract", f"Error: {e}"
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
