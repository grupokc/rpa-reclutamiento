import sys
import os
import asyncio
import platform
import streamlit as st

# Fix para asyncio en Windows con Streamlit + Playwright
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Agregar el directorio raíz del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
from src.application.services import CandidateSearchService
from src.infraestructura.persistence.json_exporter import JsonExporter
from src.infraestructura.scrapers.occ_scraper import OCCScraper
from src.infraestructura.scrapers.pandape_scraper import PandapeScraper
# Agregar los demás scrapers

def main():
    st.set_page_config(page_title="Job Scraper", page_icon="🕵️", layout="wide")
    
    st.title("🕵️ Automatizador de Reclutamiento")
    st.markdown("Herramienta para extración de candidatos de múltiples sitios web.")

    st.sidebar.header("Configuración")

    use_occ = st.sidebar.checkbox("OCC", value=True)
    use_pandape = st.sidebar.checkbox("Pandape", value=False)
    
    st.sidebar.checkbox("LinkedIn", value=False, disabled=True, help="Implementación en progreso")
    st.sidebar.checkbox("Computrabajo", value=False, disabled=True, help="Implementación en progreso")
    st.sidebar.checkbox("Indeed", value=False, disabled=True, help="Implementación en progreso")

    st.markdown("### Filtros de Búsqueda")
    location_option = st.radio(
        "Selecciona la ubicación",
        ("Todo México (sin filtro)", "CDMX", "Edo Mex", "Nuevo León", "Oaxaca", "Querétaro"),
        horizontal=True
    )
    
    location_param = None if "Todo México" in location_option else location_option

    col1, col2 = st.columns([1, 3])
    
    with col1:
        limit = st.number_input(
            "Registros deseados",
            min_value=1,
            max_value=1000,
            value=100,
            step=10,
            help="El sistema intentará obtener esta cantidad de registros. Si hay menos disponibles, traerá los que encuentre."
        )

    with col2:
        keyword = st.text_input(
            "Puesto o palabra clave",
            placeholder="Ej. Desarrollador Python"
        )

    search_btn = st.button("Buscar Candidatos", type="primary")

    if search_btn and keyword:
        if not (use_occ or use_pandape):
            st.warning("Por favor, selecciona al menos un sitio web.")
            return

        with st.spinner(f"Ejecutando buscador para '{keyword}' ..."):
            exporter = JsonExporter()
            service = CandidateSearchService(exporter)

            if use_occ:
                service.add_scraper(OCCScraper())
            if use_pandape:
                service.add_scraper(PandapeScraper())
            # Agregar más servicios
            
            try:
                results = service.search_candidates(keyword, location_param, limit)

                if results:
                    st.success(f"✅ Se encontraron {len(results)} candidatos.")

                    df = pd.DataFrame([c.model_dump() for c in results])
                    st.dataframe(df, width="stretch")

                    json_str = df.to_json(
                        orient="records", 
                        indent=4, 
                        force_ascii=False
                    )

                    st.download_button(
                        label="📥 Descargar JSON",
                        data=json_str,
                        file_name=f"candidatos_{keyword.replace(' ', '_')}.json",
                        mime="application/json"
                    )
                else:
                    st.info("No se encontraron candidatos con los criterios de búsqueda.")
            except Exception as e:
                st.error(f"Error al buscar candidatos: {e}")

if __name__ == "__main__":
    main()              
