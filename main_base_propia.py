from src.infraestructura.scrapers.pandape_base_propia_scraper import PandapeBasePropiaScraper
from src.infraestructura.persistence.json_exporter import JsonExporter
from src.domain.models import CandidateSchema
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
    
    # --- Configuración para Extracción Masiva (60k) ---
    queue_file = "data/cola_pendientes.jsonl"
    final_file = "data/candidatos_completos.jsonl"
    
    TARGET_LIMIT = 200 
    
    print(f"--- FASE 1: COSECHA (Harvester) ---")
    print(f"Meta: {TARGET_LIMIT} candidatos en cola.")
    
    # Cargar cola existente para ver cuánto falta
    current_queue = exporter.load_jsonl(queue_file)
    queue_ids = {item["id"] for item in current_queue if "id" in item}
    print(f"En cola actualmente: {len(queue_ids)}")
    
    if len(queue_ids) < TARGET_LIMIT:
        print("Iniciando recolección de URLs...")
        scraper.harvest_candidates(
            queue_file=queue_file, 
            limit=TARGET_LIMIT - len(queue_ids), # Solo lo que falta
            ignore_ids=queue_ids # Para no repetir cosecha
        )
    else:
        print("Meta de cosecha alcanzada. Saltando a procesamiento.")

    print(f"\n--- FASE 2: PROCESAMIENTO (Worker) ---")
    scraper.process_queue(
        queue_file=queue_file,
        final_file=final_file,
        batch_size=50
    )
    
    print("\n" + "="*50)
    print(f"Proceso masivo finalizado.")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
        

