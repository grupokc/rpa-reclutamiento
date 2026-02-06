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
    def extract(self, limit: int = 100, ignore_ids: set = None, on_page_callback: callable = None) -> list[CandidateSchema]:
        """
        Extracción específica para Base Propia.
        Args:
            limit: Límite de candidatos a extraer.
            ignore_ids: Set de IDs (o URLs) a ignorar porque ya existen.
            on_page_callback: Función a ejecutar tras procesar una página (recibe lista actual).
        """
        extracted_data = []
        ignore_ids = ignore_ids or set()
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            try:
                base_url = os.getenv("PANDAPE_URL")
                self.logger.info("extract", "Abriendo navegador...")
                page.goto(base_url)
                time.sleep(5)
                self.logger.info("extract", "Página cargada exitosamente.")
                
                self._login(page)
                self.logger.info("extract", "Login exitoso.")
                time.sleep(2)
                
                # Navegar a la URL específica de Base Propia
                candidates_url = os.getenv("PANDAPE_CANDIDATES_URL") 
                if not candidates_url:
                     self.logger.error("extract", "PANDAPE_CANDIDATES_URL no definida.")
                     return []

                page.goto(candidates_url)
                time.sleep(2)

                page.click(self.SELECTORS["extract"]["noResultadosDropdown"])
                self.logger.info("extract", "Dropdown de resultados abierto.")
                time.sleep(1)
                page.click(self.SELECTORS["extract"]["option100"])
                self.logger.info("extract", "Opción 100 resultados seleccionada.")
                time.sleep(5)
                
                # Asegurar carga inicial
                # self._obtain_html(page)
                
                # TODO: Implementar lógica para separar los candidatos en chunks 
                # pandapé solo permite ver 10000 candidatos a la vez

                for i in range(3):
                    try:
                        self.logger.info("extract", f"Procesando página {i+1}...")
                        
                        candidates = self._extract_candidates(page)
                        self.logger.info("extract", f"Candidatos encontrados en página: {len(candidates)}")
                        
                        # --- DEDUPLICACIÓN ---
                        new_candidates = []
                        for c in candidates:
                            # Usamos ID como identificador único
                            c_id = c.id
                            if c_id and c_id not in ignore_ids:
                                new_candidates.append(c)
                                ignore_ids.add(c_id) # Agregamos al set para no repetirlo
                            elif not c_id:
                                # Fallback por si acaso viene vacío
                                self.logger.warning("extract", f"Candidato sin ID encontrado: {c.name}")
                                new_candidates.append(c) 
                            else:
                                self.logger.debug("extract", f"Saltando candidato duplicado ID {c_id}: {c.name}")
                        
                        self.logger.info("extract", f"Nuevos candidatos a procesar: {len(new_candidates)}")

                        if new_candidates:
                            # Enriquecer solo los nuevos
                            self.logger.info("extract", "Enriqueciendo datos...")
                            enriched = self._enrich_candidates(page, new_candidates)
                            extracted_data.extend(enriched)
                            self.logger.info("extract", "Enriquecimiento completado.")
                            
                            # --- CALLBACK DE GUARDADO ---
                            if on_page_callback:
                                self.logger.info("extract", "Ejecutando guardado incremental...")
                                try:
                                    on_page_callback(extracted_data)
                                except Exception as cb_err:
                                    self.logger.error("extract", f"Error en callback de guardado: {cb_err}")

                        # Verificar paginación
                        if not self._has_next_page(page):
                            self.logger.info("extract", "No hay más páginas disponibles.")
                            break

                        self._change_page(page)
                        time.sleep(3) # Espera para cambiar de página
                        
                    except Exception as e:
                        self.logger.error("extract", f"Error en loop de páginas: {e}")
                        break

            except Exception as e:
                self.logger.error("extract", f"Error general: {e}")
            finally:
                self._logout(page)
                self.logger.info("extract", "Logout exitoso.")
                browser.close()
                self.logger.info("extract", "Navegador cerrado.")
                return extracted_data
            
    def harvest_candidates(self, queue_file: str, limit: int = 60000, ignore_ids: set = None) -> None:
        """
        FASE 1: COSECHA (Harvester)
        Recorre la paginación rápidamente y guarda perfiles básicos en una cola JSONL.
        """
        from src.infraestructura.persistence.json_exporter import JsonExporter
        exporter = JsonExporter()
        ignore_ids = ignore_ids or set()
        
        self.logger.info("harvest", f"Iniciando cosecha. Meta: {limit} candidatos.")

        loc_map = {
            "Aguascalientes": "139_2",
            "Baja California": "139_3",
            "Baja California Sur": "139_4",
            "Campeche": "139_5",
            "Coahuila": "139_6",
            "Colima": "139_7",
            "Chiapas": "139_8",
            "Chihuahua": "139_9",
            "Durango": "139_11",
            "Guanajuato": "139_12",
            "Guerrero": "139_13",
            "Hidalgo": "139_14",
            "Jalisco": "139_15",
            "Estado de México": "139_16",
            "Michoacán": "139_17",
            "Morelos": "139_18",
            "Nayarit": "139_19",
            "Nuevo León": "139_20",
            "Oaxaca": "139_21",
            "Puebla": "139_22",
            "Querétaro": "139_23",
            "Quintana Roo": "139_24",
            "San Luis Potosí": "139_25",
            "Sinaloa": "139_26",
            "Sonora": "139_27",
            "Tabasco": "139_28",
            "Tamaulipas": "139_29",
            "Tlaxcala": "139_30",
            "Veracruz": "139_31",
            "Yucatán": "139_32",
            "Zacatecas": "139_33",
            "CDMX": "139_10",
            "Ciudad de México": "139_10",
        }
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            try:
                base_url = os.getenv("PANDAPE_URL")
                candidates_url = os.getenv("PANDAPE_CANDIDATES_URL")
                
                # Login y Navegación inicial
                page.goto(base_url)
                self._login(page)
                page.goto(candidates_url)
                
                total_collected = 0
                
                # Iterar por cada estado
                for state_name, state_value in loc_map.items():
                    try:
                        self.logger.info("harvest", f"--- Procesando estado: {state_name} ({state_value}) ---")
                        
                        # 0. Limpiar filtros previos (recargar página de candidatos)
                        page.goto(candidates_url)
                        time.sleep(2)
                        
                        # 1. Configurar vista 100
                        try:
                            page.click(self.SELECTORS["extract"]["noResultadosDropdown"])
                            time.sleep(1)
                            page.click(self.SELECTORS["extract"]["option100"])
                            time.sleep(3)
                        except:
                            self.logger.warning("harvest", "No se pudo configurar vista 100 (quizás ya estaba o cambió el DOM).")

                        # 2. Seleccionar Estado
                        # Expandir acordeón si es necesario
                        toggle_btn = page.locator('a[href="#filterLocations2"]')
                        if toggle_btn.count() > 0 and "collapsed" in toggle_btn.get_attribute("class"):
                            toggle_btn.click()
                            time.sleep(1)
                            
                        # Buscar input por value
                        target_selector = f"input[value='{state_value}'] + span.custom-control-label"
                        target_element = page.locator(target_selector)
                        
                        if not target_element.is_visible():
                            # Intentar mostrar todo
                            show_all_btn = page.locator('#filterLocations2 .js_showFilters')
                            if show_all_btn.is_visible():
                                show_all_btn.click()
                                time.sleep(2)
                        
                        # Intentar click con JS si sigue oculto
                        if target_element.count() > 0:
                            target_element.first.scroll_into_view_if_needed()
                            if target_element.is_visible():
                                target_element.click()
                            else:
                                target_element.evaluate("el => el.click()")
                            time.sleep(3) # Esperar recarga por filtro
                        else:
                            self.logger.warning("harvest", f"No se encontró selector para {state_name}. Saltando...")
                            continue

                        # 3. Loop de Paginación para este estado
                        state_collected = 0
                        
                        while state_collected < limit: # Usamos el limit como 'limit per state' aquí? O global?
                            # El usuario dijo: "obtener la cantidad especificada en TARGET_LIMIT por cada estado"
                            
                            self.logger.info("harvest", f"[{state_name}] Procesando página... (Llevamos {state_collected})")
                            
                            # Extraer
                            raw_candidates = self._extract_candidates(page)
                            
                            # Filtrar y Guardar
                            new_items = []
                            for c in raw_candidates:
                                if c.id and c.id not in ignore_ids:
                                    new_items.append(c)
                                    ignore_ids.add(c.id)
                            
                            if new_items:
                                exporter.append_jsonl(new_items, queue_file)
                                state_collected += len(new_items)
                                total_collected += len(new_items)
                                self.logger.info("harvest", f"[{state_name}] +{len(new_items)} agregados a cola.")
                            else:
                                self.logger.info("harvest", f"[{state_name}] Página sin nuevos.")

                            # Checar límite por estado
                            if state_collected >= limit:
                                self.logger.info("harvest", f"[{state_name}] Meta por estado alcanzada ({limit}).")
                                break

                            # Paginación
                            if not self._has_next_page(page):
                                self.logger.info("harvest", f"[{state_name}] Fin de paginación.")
                                break
                            
                            if not self._change_page(page):
                                break
                            time.sleep(1)

                    except Exception as e_state:
                        self.logger.error("harvest", f"Error procesando estado {state_name}: {e_state}")
                        continue
                
                self.logger.info("harvest", f"Cosecha total finalizada. Total global: {total_collected}")

            except Exception as e:
                self.logger.error("harvest", f"Error en cosecha: {e}")
            finally:
                browser.close()

    def process_queue(self, queue_file: str, final_file: str, batch_size: int = 50) -> None:
        """
        FASE 2: PROCESAMIENTO (Worker)
        Lee de la cola JSONL, visita perfiles y guarda en DB final JSONL.
        """
        from src.infraestructura.persistence.json_exporter import JsonExporter
        exporter = JsonExporter()
        
        # 1. Cargar estado actual
        queue_data = exporter.load_jsonl(queue_file)
        final_data = exporter.load_jsonl(final_file)
        
        if not queue_data:
            self.logger.warning("process_queue", "Cola vacía. Nada que procesar.")
            return

        # IDs ya procesados
        processed_ids = {item.get("id") for item in final_data if item.get("id")}
        
        # Items pendientes (convertir dicts a Schemas si es necesario, pero aquí usaremos dicts/schemas mix)
        # Usamos CandidateSchema para aprovechar el metodo model_copy luego
        pending_items = []
        for q in queue_data:
            if q.get("id") not in processed_ids:
                pending_items.append(CandidateSchema(**q))
        
        total_pending = len(pending_items)
        self.logger.info("process_queue", f"Iniciando procesamiento. Pendientes: {total_pending} de {len(queue_data)} totales en cola.")
        
        if total_pending == 0:
            return

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            
            try:
                # Login necesario para ver detalles
                base_url = os.getenv("PANDAPE_URL")
                page.goto(base_url)
                self._login(page)
                
                current_batch = []
                
                for i, candidate in enumerate(pending_items):
                    self.logger.info("process_queue", f"Procesando {i+1}/{total_pending}: {candidate.name}")
                    
                    # Enriquecimiento individual (usamos _enrich_candidates que acepta lista, le pasamos lista de 1)
                    # OJO: _enrich_candidates navega. Es lo que queremos.
                    enriched_list = self._enrich_candidates(page, [candidate])
                    
                    if enriched_list:
                        cand = enriched_list[0]
                        # --- VALIDACIÓN ESTRICTA ---
                        # Solo guardamos si realmente se enriqueció (tiene experiencia, skills o email)
                        has_exp = cid_has_data = len(cand.experience) > 0
                        has_skills = cand.skills is not None and len(cand.skills) > 0
                        has_contact = cand.email is not None or cand.phone is not None
                        
                        if has_exp or has_skills or has_contact:
                            current_batch.append(cand)
                        else:
                            self.logger.warning("process_queue", f"Candidato {cand.name} (ID: {cand.id}) NO se enriqueció correctamente. Se omite.")
                    
                    # Guardado por lotes
                    if len(current_batch) >= batch_size:
                        exporter.append_jsonl(current_batch, final_file)
                        self.logger.info("process_queue", f"Lote de {len(current_batch)} guardado en final.")
                        current_batch = [] # Liberar memoria
                        
                # Guardar remanente
                if current_batch:
                    exporter.append_jsonl(current_batch, final_file)
                    self.logger.info("process_queue", f"Lote final de {len(current_batch)} guardado.")
                    
            except Exception as e:
                self.logger.error("process_queue", f"Error en procesamiento: {e}")
            finally:
                browser.close()
