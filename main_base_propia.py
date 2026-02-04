from src.infraestructura.scrapers.pandape_base_propia_scraper import PandapeBasePropiaScraper
from src.infraestructura.persistence.json_exporter import JsonExporter
import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print("Iniciando Scraper de Base Propia...")
    
    # Validar variables de entorno requeridas
    required_vars = ["PANDAPE_USERNAME", "PANDAPE_PASSWORD", "PANDAPE_URL", "PANDAPE_CANDIDATES_URL", "PANDAPE_LOGOUT_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"Error: Faltan variables de entorno: {', '.join(missing)}")
        return

    scraper = PandapeBasePropiaScraper()
    exporter = JsonExporter()
    
    try:
        candidates = scraper.extract(limit=100)
        
        print("\n" + "="*50)
        print(f"Proceso finalizado.")
        print(f"Total candidatos extraídos: {len(candidates)}")
        print("="*50 + "\n")
        
        if candidates:
            output_file = "data/candidatos_BasePropia.json"
            exporter.save(candidates, output_file)
            print(f"Resultados guardados en: {output_file}")
        
        for c in candidates:
            print(f"- {c.name} ({c.position})")
            if c.email:
                print(f"  Email: {c.email}")
            print(f"  Exp: {len(c.experience) if c.experience else 0} items")
            
    except Exception as e:
        print(f"Error crítico durante la ejecución: {e}")

if __name__ == "__main__":
    main()
