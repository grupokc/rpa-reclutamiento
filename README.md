# 🕵️ Automatizador de Reclutamiento (Job Scraper)

Herramienta construida con **Clean Architecture** para la extracción automatizada de candidatos de portales de empleo como OCC Mundial y Pandape.

## 🚀 Stack Tecnológico

*   **Lenguaje**: Python 3.12+
*   **Gestor de Paquetes**: `uv`
*   **Validación de Datos**: Pydantic
*   **Motor de Scraping**: Playwright
*   **Interfaz de Usuario**: Streamlit
*   **Arquitectura**: Clean Architecture (Domain, Application, Infrastructure, UI)

### 📂 Arquitectura del Proyecto (Clean Architecture)
El proyecto sigue una arquitectura en capas para garantizar la escalabilidad y mantenibilidad:

```text
src/
├── domain/                  # Capa de Dominio (Reglas de Negocio)
│   ├── models.py            # Entidades de datos (CandidateSchema, JobPost)
│   └── interfaces.py        # Contratos / Interfaces (BaseScraper, DataExporter)
│
├── application/             # Capa de Aplicación (Casos de Uso)
│   └── services.py          # Servicios orquestadores (CandidateSearchService)
│
├── infraestructura/         # Capa de Infraestructura (Implementaciones)
│   ├── scrapers/            # Adaptadores de Scraping
│   │   ├── occ_scraper.py   # Implementación para OCC
│   │   ├── pandape_scraper.py # Base para Pandape
│   │   └── pandape_base_propia_scraper.py # Scraper especializado (Harvest/Process)
│   ├── persistence/         # Adaptadores de Persistencia
│   │   ├── json_exporter.py # Exportación a JSONL
│   │   ├── csv_exporter.py  # Exportación a CSV (Hybrid Flattening)
│   │   ├── toml_exporter.py # Exportación a TOML
│   │   └── toon_exporter.py # Exportación a TOON
│   └── logging.py           # Configuración centralizada de logs
│
├── ui/                      # Capa de Interfaz
│   └── app.py               # Aplicación Web con Streamlit
│
├── main.py                  # Entry point (CLI Básico)
├── main_base_propia.py      # Entry point (Extracción Masiva)
├── main_exporters.py        # Entry point (Conversión de Formatos)
├── .env                     # Variables de entorno (Credenciales)
└── pyproject.toml           # Definición de dependencias
```

### Descripción de Componentes

*   **Domain**: Define *qué* hace el sistema. Contiene los modelos de datos (`models.py`) que representan a los candidatos y las interfaces (`interfaces.py`) que dictan cómo deben comportarse los scrapers y exportadores, sin preocuparse de la implementación.
*   **Application**: Define *cómo* se coordinan las tareas. `services.py` contiene la lógica principal (e.g., `CandidateSearchService`) que utiliza las interfaces del dominio para ejecutar la búsqueda, extracción y guardado de datos.
*   **Infrastructure**: Contiene los detalles técnicos. Aquí viven los scrapers reales (`occ_scraper.py`, `pandape_scraper.py`) que interactúan con los sitios web usando Playwright, y los exportadores (`json_exporter.py`, `csv_exporter.py`, etc.) que escriben en disco en varios formatos.
*   **UI**: La interfaz de usuario. `app.py` utiliza los servicios de la capa de aplicación para mostrar resultados al usuario final.

## 🛠️ Instalación

Este proyecto utiliza `uv` para la gestión de dependencias.

1.  **Clonar el repositorio**:
    ```bash
    git clone <url-del-repo>
    cd Automatizador_reclutamiento
    ```

2.  **Instalar dependencias**:
    ```bash
    uv sync
    ```

3.  **Instalar navegadores de Playwright**:
    ```bash
    uv run playwright install chromium
    ```

3.  **Configuración de Variables de Entorno**:
    Copia el archivo de ejemplo y configura tus credenciales:
    ```bash
    cp .env.example .env
    ```
    Edita `.env` con tus usuarios y contraseñas de OCC/Pandape.

## ▶️ Ejecución

Puedes ejecutar la herramienta de dos formas:

### 1. Interfaz Gráfica (Recomendado)
Inicia la aplicación web con Streamlit:
```bash
uv run streamlit run src/ui/app.py
```

### 2. Línea de Comandos (CLI)
Ejecuta el script principal para una búsqueda rápida en terminal:
```bash
uv run python main.py
```

### 3. Extracción Masiva (Base Propia Pandape)
Script especializado para extraer grandes volúmenes (60k+) en dos fases:
1.  **Cosecha (Harvest)**: Recolecta IDs rápidamente por estado.
2.  **Procesamiento (Worker)**: Enriquece los perfiles uno a uno.

```bash
uv run main_base_propia.py
```

### 4. Herramientas de Exportación
Convierte tus archivos JSONL recolectados a otros formatos (CSV, TOML, TOON):

```bash
# Sintaxis: uv run main_exporters.py <input_file> <format>
uv run main_exporters.py data/candidatos_completos.jsonl csv
uv run main_exporters.py data/candidatos_completos.jsonl toon
```
**Formatos soportados:** `csv`, `toml`, `toon`.

## 📝 Notas
*   Los resultados se guardan automáticamente en la carpeta `data/` en formato JSON.
*   Asegúrate de no abusar de las peticiones para evitar bloqueos por parte de los portales.
