import toml
import os
from typing import List, Dict, Any
from src.domain.models import CandidateSchema

class TomlExporter:
    """
    Exportador de candidatos a formato TOML.
    
    LIMITACIÓN: TOML no está diseñado para datasets masivos (60k+ objetos en un array).
    Se recomienda usar solo para exportaciones pequeñas o configuración.
    """

    def export(self, data: List[CandidateSchema | dict], filename: str) -> None:
        if not data:
            return

        # Asegurar directorio
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        try:
            # 1. Convertir lista de modelos a diccionarios
            candidates_dict_list = []
            for item in data:
                if hasattr(item, "model_dump"):
                    # Excluir None para limpieza, aunque TOML lo soporta (como vacío u omitido)
                    dump = item.model_dump(exclude_none=True)
                else:
                    # Limpiar Nones manualmente si es dict
                    dump = {k: v for k, v in item.items() if v is not None}
                
                candidates_dict_list.append(dump)

            # 2. Estructura raíz
            # TOML requiere un objeto raíz (tabla).
            toml_structure = {"candidates": candidates_dict_list}

            # 3. Escribir
            with open(filename, "w", encoding="utf-8") as f:
                toml.dump(toml_structure, f)
                
        except Exception as e:
            # Capturar errores comunes de serialización
            print(f"Error exportando TOML: {e}")
            raise
