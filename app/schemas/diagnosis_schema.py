from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DiagnosisBase(BaseModel):
    tipo: str | None = Field(default=None, max_length=255)
    nivel: int | None = Field(default=None, ge=0)
    nomurl: str | None = Field(default=None, max_length=255)

    @field_validator("tipo", "nomurl")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class DiagnosisCreate(DiagnosisBase):
    codigo: str = Field(min_length=1, max_length=50)
    titulo: str = Field(min_length=1, max_length=255)
    activo: bool = True


class DiagnosisUpdate(DiagnosisBase):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    activo: bool | None = None


class DiagnosisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_diag: int
    codigo: str
    diag_nombre: str
    tipo: str | None = None
    nivel: int | None = None
    nomurl: str | None = None
    activo: bool | None = None
    usu_creacion: int | None = None
    usu_creacion_nombre: str | None = None
    fec_creacion: datetime | None = None
    usu_actualizacion: int | None = None
    usu_actualizacion_nombre: str | None = None
    fec_actualizacion: datetime | None = None
