from pydantic import BaseModel, ConfigDict, Field

class CandidateSchema(BaseModel):
    """
    Modelo de dominio que representa a un candidato extraído de una página web.
    Configuración inmutable.
    """
    model_config = ConfigDict(frozen=True)

    id: str | None = Field(default=None, description="Identificador único del candidato")
    name: str = Field(..., description="Nombre del candidato")
    position: str = Field(..., description="Puesto o cargo")
    company: str | None = Field(default=None, description="Empresa (opcional)")
    skills: list[str] | None = Field(default=None, description="Lista de habilidades (opcional)")
    experience: list[str] | None = Field(default=None, description="Lista de experiencia laboral (opcional)")
    education: str | None = Field(default=None, description="Formación profesional (opcional)")
    location: str | None = Field(default=None, description="Ubicación (opcional)")
    contact_info: str | None = Field(default=None, description="Información de contacto (opcional)")
    url: str = Field(..., description="URL del perfil")