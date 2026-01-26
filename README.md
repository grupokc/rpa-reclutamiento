# 🕵️ Automatizador de Reclutamiento (Job Scraper)

Herramienta construida con **Clean Architecture** para la extracción automatizada de candidatos de portales de empleo como OCC Mundial y Pandape.

## 🚀 Stack Tecnológico

*   **Lenguaje**: Python 3.12+
*   **Gestor de Paquetes**: `uv`
*   **Validación de Datos**: Pydantic
*   **Motor de Scraping**: Playwright
*   **Interfaz de Usuario**: Streamlit
*   **Arquitectura**: Clean Architecture (Domain, Application, Infrastructure, UI)

## 📂 Estructura del Proyecto

```text
src/
├── domain/           # Modelos (CandidateSchema) e Interfaces (BaseScraper)
├── application/      # Lógica de negocio (CandidateSearchService)
├── infraestructura/  # Implementación técnica (Scrapers, Logger, Exporters)
└── ui/               # Interfaz gráfica (Streamlit)
```

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

## 📝 Notas
*   Los resultados se guardan automáticamente en la carpeta `data/` en formato JSON.
*   Asegúrate de no abusar de las peticiones para evitar bloqueos por parte de los portales.
