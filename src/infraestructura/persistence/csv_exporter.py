import csv
import os
from datetime import datetime
from typing import List, Dict, Any

from src.domain.models import CandidateSchema, Experience

class CsvExporter:
    """
    Exportador de candidatos a formato CSV optimizado para lectura en Excel/Sheets.
    Implementa la estrategia de 'Aplanamiento Híbrido':
    - Campos planos directos.
    - Skills concatenados.
    - Experiencia: 
        - Última experiencia en columnas dedicadas (para filtrado rápido).
        - Historial completo en columna de texto resumen.
    """

    def export(self, data: List[CandidateSchema | dict], filename: str) -> None:
        if not data:
            return

        # Asegurar directorio
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Definir encabezados
        headers = [
            "id", "name", 
            "headline_position", 
            "specialty", 
            "email", "phone", "location", "salary", 
            "url", "last_updated", 
            # Campos derivados de Experiencia (Lo más reciente)
            "latest_position", "latest_company", "latest_start_date", "latest_end_date",
            # Campos complejos aplanados
            "education", "skills", "experience_summary_text"
        ]

        try:
            # Usar utf-8-sig para que Excel reconozca acentos automáticamente
            with open(filename, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                for item in data:
                    row = self._flatten_candidate(item)
                    writer.writerow(row)
                    
        except Exception as e:
            print(f"Error exportando CSV: {e}")
            raise

    def _flatten_candidate(self, item: CandidateSchema | dict) -> Dict[str, Any]:
        """Convierte un objeto CandidateSchema o dict en un dict plano para CSV"""
        
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
            # Asumimos que la lista viene ordenada o que el primero es el actual/último
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
                
                # Formato rico: "Puesto en Empresa (Fechas) [Desc: ...]"
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
            "headline_position": candidate.get("position"), # Mapeo explícito
            "specialty": candidate.get("specialty"),       # Mapeo explícito
            "email": candidate.get("email"),
            "phone": candidate.get("phone"),
            "location": candidate.get("location"),
            "salary": candidate.get("salary"),
            "url": candidate.get("url"),
            "last_updated": candidate.get("last_updated"),
            
            # Exp Reciente
            **latest_exp,
            
            # Aplanados
            "education": candidate.get("education"),
            "skills": skills_str,
            "experience_summary_text": " || ".join(msg_summary)
        }
        
        return row
