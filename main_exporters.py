import argparse
import sys
import os

# Asegurar que el root del proyecto esté en path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.infraestructura.persistence.json_exporter import JsonExporter
from src.infraestructura.persistence.csv_exporter import CsvExporter
from src.infraestructura.persistence.toml_exporter import TomlExporter
from src.infraestructura.persistence.toon_exporter import ToonExporter

EXPORTERS = {
    "csv": CsvExporter,
    "toml": TomlExporter,
    "toon": ToonExporter
}

def main():
    parser = argparse.ArgumentParser(description="Herramienta de Exportación Multi-Formato (RPA Reclutamiento)")
    
    parser.add_argument("input_file", help="Ruta al archivo origen (ej: data/candidatos.jsonl)")
    parser.add_argument("format", choices=EXPORTERS.keys(), help="Formato de salida deseado")
    parser.add_argument("--output", "-o", help="Ruta de salida opcional (por defecto usa el nombre del input)")

    args = parser.parse_args()

    # 1. Validar Input
    if not os.path.exists(args.input_file):
        print(f"Error: El archivo '{args.input_file}' no existe.")
        sys.exit(1)

    # 2. Cargar Datos (Usando JsonExporter existente)
    print(f"--- Cargando datos de: {args.input_file} ---")
    json_loader = JsonExporter()
    try:
        # Detectar si es jsonl o json normal (simple check por extensión)
        if args.input_file.endswith(".jsonl"):
            data = json_loader.load_jsonl(args.input_file)
        else:
            # Fallback a load normal (aunque JsonExporter.load es para listas JSON array)
            data = json_loader.load(args.input_file)
            
        print(f"Registros cargados: {len(data)}")
        
        if not data:
            print("Advertencia: No hay datos para exportar.")
            sys.exit(0)

    except Exception as e:
        print(f"Error cargando datos: {e}")
        sys.exit(1)

    # 3. Exportar
    try:
        exporter_cls = EXPORTERS[args.format]
        exporter = exporter_cls()
        
        # Determinar output filename
        if args.output:
            output_file = args.output
        else:
            base_name = os.path.splitext(args.input_file)[0]
            output_file = f"{base_name}.{args.format}"

        print(f"--- Exportando a {args.format.upper()} ---")
        exporter.export(data, output_file)
        
        print(f"¡Éxito! Archivo guardado en: {output_file}")
        
    except Exception as e:
        print(f"Error durante la exportación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
