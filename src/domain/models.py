from pydantic import BaseModel, ConfigDict, Field

class Experience(BaseModel):
    position: str | None = None
    company: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None

class CandidateSchema(BaseModel):
    """
    Modelo de dominio que representa a un candidato extraído de una página web.
    Configuración inmutable.
    """
    model_config = ConfigDict(frozen=True)

    id: str | None = Field(default=None, description="Identificador único del candidato")
    name: str = Field(..., description="Nombre del candidato")
    position: str = Field(..., description="Puesto o cargo")
    skills: list[str] | None = Field(default=None, description="Lista de habilidades (opcional)")
    experience: list[Experience] | None = Field(default=None, description="Lista de experiencia laboral detallada (opcional)")
    education: str | None = Field(default=None, description="Formación profesional (opcional)")
    location: str | None = Field(default=None, description="Ubicación (opcional)")
    email: str | None = Field(default=None, description="Email del candidato")
    phone: str | None = Field(default=None, description="Teléfono del candidato")
    salary: str | None = Field(default=None, description="Salario deseado (opcional)")
    specialty: str | None = Field(default=None, description="Área de especialización (opcional)")
    last_updated: str | None = Field(default=None, description="Fecha o texto de última actualización del perfil")
    url: str = Field(..., description="URL del perfil")