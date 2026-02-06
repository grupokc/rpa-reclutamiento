import csv
import os
import io
from typing import List, Dict, Any
from src.domain.models import CandidateSchema

class ToonExporter:
    """
    Exportador de candidatos a formato TOON (Token-Oriented Object Notation).
    Formato experimental para minimizar tokens:
    candidates[N]{key1,key2...}:
    val1,val2...
    """

    def export(self, data: List[CandidateSchema | dict], filename: str) -> None:
        if not data:
            return

        # Asegurar directorio
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        try:
            # 1. Aplanar datos (Reutilizando lógica híbrida)
            flattened_data = [self._flatten_candidate(item) for item in data]
            
            if not flattened_data:
                return

            # Obtenemos las claves del primer elemento como esquema
            keys = list(flattened_data[0].keys())
            
            # 2. Generar Cabecera TOON
            # Formato: candidates[N]{k1,k2,k3}:
            header = f"candidates[{len(data)}]{{{','.join(keys)}}}:"

            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                f.write(header + "\n")
                
                # 3. Streaming de filas (usando csv.writer para manejar escaping de comas)
                # TOON normalmente evita comillas, pero para robustness con texto libre
                # usaremos el comportamiento estándar de CSV para las filas, que es compatible.
                writer = csv.writer(f)
                
                for row_dict in flattened_data:
                    # Asegurar orden de valores según keys
                    values = [row_dict.get(k, "") for k in keys]
                    writer.writerow(values)
                    
        except Exception as e:
            print(f"Error exportando TOON: {e}")
            raise

    def _flatten_candidate(self, item: CandidateSchema | dict) -> Dict[str, Any]:
        """Convierte un objeto CandidateSchema o dict en un dict plano (Lógica idéntica a CSV)"""
        
        # 1. Normalizar a objeto si es dict (o acceder como dict)
        if isinstance(item, dict):
            # Si es dict crudo, extraer campos con .get()
            candidate = item
            experience_list = candidate.get("experience", [])
            skills_list = candidate.get("skills", [])
        else:
            # Si es Pydantic
            candidate = item.model_dump()
            experience_list = item.experience or []
            skills_list = item.skills or []

        # 2. Procesar Experiencia (Estrategia B)
        latest_exp = {}
        msg_summary = []

        # Si hay experiencias, tomamos la primera como la más reciente
        if experience_list:
            curr = experience_list[0]
            
            # Manejo si es objeto o dict
            if isinstance(curr, dict):
                pos = curr.get("position", "")
                comp = curr.get("company", "")
                start = curr.get("start_date", "")
                end = curr.get("end_date", "")
                desc = curr.get("description", "")
            else:
                pos = curr.position
                comp = curr.company
                start = curr.start_date
                end = curr.end_date
                desc = curr.description

            latest_exp = {
                "latest_position": pos,
                "latest_company": comp,
                "latest_start_date": start,
                "latest_end_date": end
            }

            # Construir resumen de historial COMPLETO
            for exp in experience_list:
                if isinstance(exp, dict):
                    p, c, s, e, d = exp.get("position"), exp.get("company"), exp.get("start_date"), exp.get("end_date"), exp.get("description")
                else:
                    p, c, s, e, d = exp.position, exp.company, exp.start_date, exp.end_date, exp.description
                
                entry = f"{p} en {c} ({s} - {e})"
                if d:
                    entry += f" [Desc: {d}]"
                
                msg_summary.append(entry)
        else:
            latest_exp = {
                "latest_position": "", "latest_company": "", 
                "latest_start_date": "", "latest_end_date": ""
            }

        # 3. Procesar Skills
        skills_str = " | ".join(skills_list) if skills_list else ""

        # 4. Construir fila final
        row = {
            "id": candidate.get("id"),
            "name": candidate.get("name"),
            "headline_position": candidate.get("position"),
            "specialty": candidate.get("specialty"),
            "email": candidate.get("email"),
            "phone": candidate.get("phone"),
            "location": candidate.get("location"),
            "salary": candidate.get("salary"),
            "url": candidate.get("url"),
            "last_updated": candidate.get("last_updated"),
            **latest_exp,
            "education": candidate.get("education"),
            "skills": skills_str,
            "experience_summary_text": " || ".join(msg_summary)
        }
        
        return row
