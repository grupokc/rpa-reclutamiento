import sys
import os

# Agregar el directorio raíz del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.application.services import CandidateSearchService
from src.infraestructura.persistence.json_exporter import JsonExporter
from src.infraestructura.scrapers.occ_scraper import OCCScraper
from src.infraestructura.scrapers.pandape_scraper import PandapeScraper

def main():
    print("=== Automatizador de Reclutamiento ===")
    
    keyword = input("Ingresa el puesto o palabra clave: ")
    
    if not keyword:
        print("Debes ingresar una palabra clave.")
        return

    exporter = JsonExporter()
    service = CandidateSearchService(exporter)
    
    # Agregar scrapers
    service.add_scraper(OCCScraper())
    service.add_scraper(PandapeScraper())
    
    try:
        results = service.search_candidates(keyword)
        
        if results:
            print(f"\n✅ Se encontraron {len(results)} candidatos.")
            
            # Mostrar resultados
            for i, candidate in enumerate(results, 1):
                print(f"\n--- Candidato {i} ---")
                print(f"Nombre: {candidate.name}")
                print(f"Email: {candidate.email}")
                print(f"Teléfono: {candidate.phone}")
                print(f"Fuente: {candidate.source}")
                print(f"URL: {candidate.url}")
                print(f"Fecha de extracción: {candidate.extracted_at}")
            
            # Exportar a JSON
            filename = f"candidatos_{keyword.replace(' ', '_')}.json"
            exporter.save(results, filename)
            print(f"\n💾 Datos guardados en: {filename}")
        else:
            print("\nNo se encontraron candidatos.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
